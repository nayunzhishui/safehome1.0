"""Governed, withdrawable knowledge indexing and local RAG retrieval."""

from __future__ import annotations

import hashlib
import json
import math
import re
from collections import Counter
from datetime import datetime, timezone
from urllib.parse import urlparse

from database import (
    get_connection,
    json_dumps,
    json_loads,
    new_id,
    now_iso,
    row_to_dict,
    rows_to_dicts,
    write_audit_log,
)


ALLOWED_CONTENT_TYPES = {
    "training_card",
    "course",
    "faq",
    "consent_text",
    "privacy_text",
}
ALLOWED_RIGHTS = {
    "owned",
    "licensed",
    "public_domain",
    "permission_recorded",
}
REQUIRED_DISCIPLINES = {"research", "psychology", "ethics", "content"}
RETRIEVAL_METHODS = {"bm25", "vector", "hybrid"}
ALLOWED_AUDIENCES = {
    "all",
    "participant",
    "parent",
    "student",
    "researcher",
    "supervisor",
    "admin",
}
VECTOR_DIMENSIONS = 96
MAX_QUERY_LENGTH = 500
MAX_CHUNK_LENGTH = 520
CHUNK_OVERLAP = 60
CONTENT_KEYS_FORBIDDEN_IN_CANDIDATE = {
    "body",
    "content",
    "content_text",
    "html",
    "page_html",
    "raw_text",
    "source_text",
    "text",
}


class KnowledgeError(ValueError):
    def __init__(
        self,
        code: str,
        message: str,
        status: int = 400,
        details: dict | None = None,
    ):
        super().__init__(message)
        self.code = code
        self.status = status
        self.details = details or {}


def _canonical(value) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def _hash(value) -> str:
    text = value if isinstance(value, str) else _canonical(value)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _parse_time(value) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _terms(text: str) -> list[str]:
    normalized = re.sub(r"\s+", " ", str(text or "").lower()).strip()
    latin = re.findall(r"[a-z0-9_]{2,}", normalized)
    chinese_runs = re.findall(r"[\u4e00-\u9fff]+", normalized)
    chinese: list[str] = []
    for run in chinese_runs:
        if len(run) == 1:
            chinese.append(run)
        else:
            chinese.extend(run[index : index + 2] for index in range(len(run) - 1))
    return latin + chinese


def _vector(terms: list[str]) -> list[float]:
    values = [0.0] * VECTOR_DIMENSIONS
    for term, count in Counter(terms).items():
        digest = hashlib.sha256(term.encode("utf-8")).digest()
        index = int.from_bytes(digest[:4], "big") % VECTOR_DIMENSIONS
        sign = 1.0 if digest[4] % 2 == 0 else -1.0
        values[index] += sign * (1.0 + math.log(max(1, count)))
    norm = math.sqrt(sum(value * value for value in values))
    if norm:
        values = [round(value / norm, 8) for value in values]
    return values


def _cosine(left: list[float], right: list[float]) -> float:
    if not left or not right or len(left) != len(right):
        return 0.0
    return max(0.0, sum(a * b for a, b in zip(left, right)))


def _audiences(value) -> list[str]:
    if isinstance(value, list):
        items = value
    else:
        items = re.split(r"[,，|/]", str(value or "all"))
    normalized = []
    for item in items:
        audience = str(item).strip().lower()
        if audience in ALLOWED_AUDIENCES and audience not in normalized:
            normalized.append(audience)
    return normalized or ["all"]


def _split_text(text: str) -> list[str]:
    compact = re.sub(r"\s+", " ", str(text or "")).strip()
    if not compact:
        return []
    if len(compact) <= MAX_CHUNK_LENGTH:
        return [compact]
    chunks = []
    start = 0
    while start < len(compact):
        end = min(len(compact), start + MAX_CHUNK_LENGTH)
        if end < len(compact):
            boundary = max(
                compact.rfind("。", start, end),
                compact.rfind("；", start, end),
                compact.rfind("，", start, end),
                compact.rfind(" ", start, end),
            )
            if boundary > start + MAX_CHUNK_LENGTH // 2:
                end = boundary + 1
        chunks.append(compact[start:end].strip())
        if end >= len(compact):
            break
        start = max(start + 1, end - CHUNK_OVERLAP)
    return [item for item in chunks if item]


def _payload_sections(payload) -> list[tuple[str, str, str]]:
    sections: list[tuple[str, str, str]] = []

    def visit(value, location: str, heading: str = "", depth: int = 0):
        if depth > 5:
            return
        if isinstance(value, str):
            for part_index, part in enumerate(_split_text(value)):
                suffix = f"#{part_index + 1}" if len(value) > MAX_CHUNK_LENGTH else ""
                sections.append((f"{location}{suffix}", heading, part))
            return
        if isinstance(value, (int, float, bool)):
            sections.append((location, heading, str(value)))
            return
        if isinstance(value, list):
            for index, item in enumerate(value[:100]):
                visit(item, f"{location}[{index}]", heading, depth + 1)
            return
        if isinstance(value, dict):
            local_heading = str(
                value.get("title")
                or value.get("display_name")
                or value.get("label")
                or heading
                or ""
            ).strip()
            preferred = (
                "title",
                "purpose",
                "core_concept",
                "summary",
                "description",
                "body",
                "steps",
                "sections",
                "safety_notes",
                "boundary_notice",
            )
            visited = set()
            for key in preferred:
                if key in value:
                    visited.add(key)
                    visit(
                        value[key],
                        f"{location}.{key}" if location else key,
                        local_heading,
                        depth + 1,
                    )
            for key in sorted(value):
                if key in visited or key in {"id", "tags", "audience"}:
                    continue
                item = value[key]
                if isinstance(item, (dict, list, str)):
                    visit(
                        item,
                        f"{location}.{key}" if location else key,
                        local_heading,
                        depth + 1,
                    )

    visit(payload, "")
    deduplicated = []
    seen = set()
    for location, heading, text in sections:
        digest = _hash(text)
        if digest in seen:
            continue
        seen.add(digest)
        deduplicated.append((location.lstrip(".") or "body", heading, text))
    return deduplicated


def _eligibility(row: dict, review_disciplines: set[str]) -> tuple[bool, str]:
    if row["content_type"] not in ALLOWED_CONTENT_TYPES:
        return False, "content_type_not_allowed"
    if row["status"] != "published" or row["release_status"] != "active":
        return False, "not_active_published"
    metadata = json_loads(row["metadata_json"], {})
    if str(metadata.get("copyright_status") or "") not in ALLOWED_RIGHTS:
        return False, "rights_not_approved"
    if not str(metadata.get("source") or "").strip():
        return False, "source_missing"
    if not str(metadata.get("source_version") or "").strip():
        return False, "source_version_missing"
    if not REQUIRED_DISCIPLINES.issubset(review_disciplines):
        return False, "professional_reviews_incomplete"
    current = datetime.now(timezone.utc)
    valid_from = _parse_time(metadata.get("valid_from"))
    expires_at = _parse_time(metadata.get("expires_at"))
    if metadata.get("valid_from") and valid_from is None:
        return False, "valid_from_invalid"
    if metadata.get("expires_at") and expires_at is None:
        return False, "expires_at_invalid"
    if valid_from and current < valid_from:
        return False, "not_yet_valid"
    if expires_at and current >= expires_at:
        return False, "expired"
    return True, "approved"


def _load_governed_rows(conn) -> list[dict]:
    rows = conn.execute(
        """
        SELECT v.id, v.content_type, v.item_id, v.version, v.payload_json,
               v.payload_hash, v.metadata_json, v.status,
               r.id AS release_id, r.package_json,
               r.status AS release_status
        FROM content_governance_versions v
        LEFT JOIN content_governance_releases r
          ON r.version_id = v.id
         AND r.status = 'active'
        WHERE v.status = 'published'
        ORDER BY v.updated_at DESC
        """
    ).fetchall()
    return [row_to_dict(row) for row in rows]


def sync_approved_knowledge(actor: dict | None = None) -> dict:
    """Rebuild the active index from content already approved and released."""
    timestamp = now_iso()
    indexed = 0
    rejected = 0
    active_ids: set[str] = set()
    rejection_reasons: Counter = Counter()
    with get_connection() as conn:
        governed_rows = _load_governed_rows(conn)
        existing = {
            row["version_id"]: row_to_dict(row)
            for row in conn.execute(
                "SELECT * FROM ai_knowledge_documents"
            ).fetchall()
        }
        for row in governed_rows:
            reviews = {
                review["discipline"]
                for review in conn.execute(
                    """
                    SELECT discipline
                    FROM content_governance_reviews
                    WHERE version_id = ? AND decision = 'approved'
                    """,
                    (row["id"],),
                ).fetchall()
            }
            eligible, reason = _eligibility(row, reviews)
            if not eligible:
                rejected += 1
                rejection_reasons[reason] += 1
                continue
            metadata = json_loads(row["metadata_json"], {})
            payload = json_loads(row["payload_json"], {})
            package = json_loads(row["package_json"], {})
            version_id = row["id"]
            document = existing.get(version_id)
            document_id = (
                document["id"]
                if document
                else "aikd-" + hashlib.sha256(version_id.encode()).hexdigest()[:24]
            )
            values = {
                "release_id": row["release_id"],
                "content_type": row["content_type"],
                "item_id": row["item_id"],
                "document_version": row["version"],
                "source_ref": str(metadata.get("source")).strip(),
                "source_version": str(metadata.get("source_version")).strip(),
                "rights_status": str(metadata.get("copyright_status")).strip(),
                "valid_from": metadata.get("valid_from"),
                "expires_at": metadata.get("expires_at"),
                "audiences_json": json_dumps(_audiences(metadata.get("audience"))),
                "payload_hash": row["payload_hash"],
                "package_hash": package.get("package_hash"),
            }
            if document:
                conn.execute(
                    """
                    UPDATE ai_knowledge_documents
                    SET release_id = ?, content_type = ?, item_id = ?,
                        document_version = ?, source_ref = ?,
                        source_version = ?, rights_status = ?,
                        review_status = 'approved', valid_from = ?,
                        expires_at = ?, audiences_json = ?, status = 'active',
                        payload_hash = ?, package_hash = ?, indexed_at = ?,
                        withdrawn_at = NULL, updated_at = ?
                    WHERE id = ?
                    """,
                    (
                        values["release_id"],
                        values["content_type"],
                        values["item_id"],
                        values["document_version"],
                        values["source_ref"],
                        values["source_version"],
                        values["rights_status"],
                        values["valid_from"],
                        values["expires_at"],
                        values["audiences_json"],
                        values["payload_hash"],
                        values["package_hash"],
                        timestamp,
                        timestamp,
                        document_id,
                    ),
                )
            else:
                conn.execute(
                    """
                    INSERT INTO ai_knowledge_documents
                    (id, version_id, release_id, content_type, item_id,
                     document_version, source_ref, source_version,
                     rights_status, review_status, valid_from, expires_at,
                     audiences_json, status, payload_hash, package_hash,
                     indexed_at, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'approved', ?, ?, ?,
                            'active', ?, ?, ?, ?, ?)
                    """,
                    (
                        document_id,
                        version_id,
                        values["release_id"],
                        values["content_type"],
                        values["item_id"],
                        values["document_version"],
                        values["source_ref"],
                        values["source_version"],
                        values["rights_status"],
                        values["valid_from"],
                        values["expires_at"],
                        values["audiences_json"],
                        values["payload_hash"],
                        values["package_hash"],
                        timestamp,
                        timestamp,
                        timestamp,
                    ),
                )
            conn.execute(
                "DELETE FROM ai_knowledge_chunks WHERE document_id = ?",
                (document_id,),
            )
            sections = _payload_sections(payload)
            for ordinal, (location, heading, text) in enumerate(sections):
                lexical_terms = _terms(f"{heading} {text}")
                chunk_id = (
                    "aikc-"
                    + hashlib.sha256(
                        f"{version_id}:{ordinal}:{_hash(text)}".encode()
                    ).hexdigest()[:24]
                )
                conn.execute(
                    """
                    INSERT INTO ai_knowledge_chunks
                    (id, document_id, ordinal, location, heading, content_text,
                     content_hash, token_count, lexical_terms_json, vector_json,
                     created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        chunk_id,
                        document_id,
                        ordinal,
                        location,
                        heading or None,
                        text,
                        _hash(text),
                        len(lexical_terms),
                        json_dumps(lexical_terms),
                        json_dumps(_vector(lexical_terms)),
                        timestamp,
                        timestamp,
                    ),
                )
            active_ids.add(version_id)
            indexed += 1

        for version_id, document in existing.items():
            if version_id in active_ids:
                continue
            expiry = _parse_time(document.get("expires_at"))
            status = (
                "expired"
                if expiry and datetime.now(timezone.utc) >= expiry
                else "withdrawn"
            )
            conn.execute(
                """
                UPDATE ai_knowledge_documents
                SET status = ?, withdrawn_at = COALESCE(withdrawn_at, ?),
                    updated_at = ?
                WHERE id = ? AND status = 'active'
                """,
                (status, timestamp, timestamp, document["id"]),
            )
        if actor:
            write_audit_log(
                conn,
                "ai_knowledge_index_rebuilt",
                actor["id"],
                "ai_knowledge_index",
                "approved",
                {
                    "indexed_documents": indexed,
                    "rejected_documents": rejected,
                    "rejection_reasons": dict(rejection_reasons),
                    "candidate_content_ingested": False,
                    "human_release_approval": False,
                },
            )
        conn.commit()
        active_count = conn.execute(
            """
            SELECT COUNT(*) AS count
            FROM ai_knowledge_documents
            WHERE status = 'active'
            """
        ).fetchone()["count"]
        chunk_count = conn.execute(
            """
            SELECT COUNT(*) AS count
            FROM ai_knowledge_chunks c
            JOIN ai_knowledge_documents d ON d.id = c.document_id
            WHERE d.status = 'active'
            """
        ).fetchone()["count"]
    return {
        "indexed_documents": indexed,
        "active_documents": active_count,
        "active_chunks": chunk_count,
        "rejected_documents": rejected,
        "rejection_reasons": dict(rejection_reasons),
        "only_governed_releases": True,
        "candidate_content_ingested": False,
        "human_release_approval": False,
    }


def _active_rows(audience: str) -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT c.*, d.version_id, d.release_id, d.content_type, d.item_id,
                   d.document_version, d.source_ref, d.source_version,
                   d.rights_status, d.review_status, d.valid_from,
                   d.expires_at, d.audiences_json, d.payload_hash,
                   d.package_hash
            FROM ai_knowledge_chunks c
            JOIN ai_knowledge_documents d ON d.id = c.document_id
            JOIN content_governance_versions v
              ON v.id = d.version_id AND v.status = 'published'
            JOIN content_governance_releases r
              ON r.id = d.release_id AND r.status = 'active'
            WHERE d.status = 'active'
            ORDER BY d.updated_at DESC, c.ordinal
            """
        ).fetchall()
    result = []
    for row in rows:
        item = row_to_dict(row)
        audiences = json_loads(item["audiences_json"], ["all"])
        if "all" not in audiences and audience not in audiences:
            continue
        item["audiences"] = audiences
        item["terms"] = json_loads(item["lexical_terms_json"], [])
        item["vector"] = json_loads(item["vector_json"], [])
        result.append(item)
    return result


def _knowledge_snapshot(rows: list[dict]) -> str:
    return _hash(
        sorted(
            {
                (
                    item["version_id"],
                    item["release_id"],
                    item["payload_hash"],
                    item["content_hash"],
                )
                for item in rows
            }
        )
    )


def retrieve_published_content(
    query: str,
    limit: int = 4,
    *,
    method: str = "hybrid",
    audience: str = "researcher",
) -> dict:
    query = str(query or "").strip()
    method = str(method or "hybrid").strip().lower()
    audience = str(audience or "researcher").strip().lower()
    if not query:
        raise KnowledgeError("knowledge_query_required", "query不能为空")
    if len(query) > MAX_QUERY_LENGTH:
        raise KnowledgeError(
            "knowledge_query_too_long",
            f"query不能超过{MAX_QUERY_LENGTH}个字符",
        )
    if method not in RETRIEVAL_METHODS:
        raise KnowledgeError(
            "knowledge_method_invalid",
            "method仅支持bm25、vector或hybrid",
        )
    if audience not in ALLOWED_AUDIENCES:
        raise KnowledgeError("knowledge_audience_invalid", "适用人群不受支持")
    limit = max(1, min(int(limit or 4), 8))

    sync_approved_knowledge()
    rows = _active_rows(audience)
    query_terms = _terms(query)
    snapshot_hash = _knowledge_snapshot(rows)
    if not rows or not query_terms:
        return {
            "citations": [],
            "knowledge_snapshot_hash": snapshot_hash,
            "only_published": True,
            "retrieval_method": method,
            "evidence_status": "insufficient",
            "audience": audience,
        }

    document_count = len(rows)
    average_length = (
        sum(max(1, len(item["terms"])) for item in rows) / document_count
    )
    document_frequency = Counter()
    for term in set(query_terms):
        document_frequency[term] = sum(
            1 for item in rows if term in set(item["terms"])
        )
    query_vector = _vector(query_terms)
    scored = []
    for item in rows:
        term_counts = Counter(item["terms"])
        length = max(1, len(item["terms"]))
        bm25 = 0.0
        for term in query_terms:
            frequency = term_counts.get(term, 0)
            if not frequency:
                continue
            df = document_frequency.get(term, 0)
            inverse = math.log(
                1 + (document_count - df + 0.5) / (df + 0.5)
            )
            denominator = frequency + 1.2 * (
                1 - 0.75 + 0.75 * length / max(1.0, average_length)
            )
            bm25 += inverse * (frequency * 2.2) / denominator
        vector_score = _cosine(query_vector, item["vector"])
        exact_overlap = len(set(query_terms) & set(item["terms"]))
        if exact_overlap == 0:
            continue
        heading_overlap = len(
            set(query_terms) & set(_terms(item.get("heading") or ""))
        ) / max(1, len(set(query_terms)))
        scored.append(
            {
                "item": item,
                "bm25": bm25,
                "vector": vector_score,
                "rerank": min(1.0, heading_overlap + 0.05),
            }
        )
    if not scored:
        return {
            "citations": [],
            "knowledge_snapshot_hash": snapshot_hash,
            "only_published": True,
            "retrieval_method": method,
            "evidence_status": "insufficient",
            "audience": audience,
        }
    max_bm25 = max(item["bm25"] for item in scored) or 1.0
    for item in scored:
        bm25_normalized = item["bm25"] / max_bm25
        if method == "bm25":
            base = bm25_normalized
        elif method == "vector":
            base = item["vector"]
        else:
            base = 0.6 * bm25_normalized + 0.4 * item["vector"]
        item["final"] = base + 0.15 * item["rerank"]
    scored.sort(
        key=lambda item: (
            item["final"],
            item["bm25"],
            item["item"]["content_hash"],
        ),
        reverse=True,
    )

    citations = []
    seen_documents = set()
    for score in scored:
        item = score["item"]
        if item["document_id"] in seen_documents:
            continue
        seen_documents.add(item["document_id"])
        citations.append(
            {
                "content_id": item["item_id"],
                "content_type": item["content_type"],
                "version_id": item["version_id"],
                "content_version": item["document_version"],
                "release_id": item["release_id"],
                "payload_hash": item["payload_hash"],
                "governance_status": "published",
                "document_id": item["document_id"],
                "chunk_id": item["id"],
                "location": item["location"],
                "title": item.get("heading") or item["item_id"],
                "excerpt": item["content_text"][:360],
                "source_ref": item["source_ref"],
                "source_version": item["source_version"],
                "rights_status": item["rights_status"],
                "review_status": item["review_status"],
                "valid_from": item.get("valid_from"),
                "expires_at": item.get("expires_at"),
                "audiences": item["audiences"],
                "package_hash": item.get("package_hash"),
                "retrieval_method": method,
                "scores": {
                    "bm25": round(score["bm25"], 6),
                    "vector": round(score["vector"], 6),
                    "rerank": round(score["rerank"], 6),
                    "final": round(score["final"], 6),
                },
            }
        )
        if len(citations) >= limit:
            break
    return {
        "citations": citations,
        "knowledge_snapshot_hash": snapshot_hash,
        "only_published": True,
        "retrieval_method": method,
        "evidence_status": "sufficient" if citations else "insufficient",
        "audience": audience,
    }


def list_knowledge() -> dict:
    sync_approved_knowledge()
    with get_connection() as conn:
        documents = rows_to_dicts(
            conn.execute(
                """
                SELECT d.*, COUNT(c.id) AS chunk_count
                FROM ai_knowledge_documents d
                LEFT JOIN ai_knowledge_chunks c ON c.document_id = d.id
                GROUP BY d.id
                ORDER BY d.updated_at DESC
                """
            ).fetchall()
        )
        candidates = rows_to_dicts(
            conn.execute(
                """
                SELECT id, source_url, title, source_hash, rights_status,
                       review_status, status, recorded_by, created_at,
                       updated_at
                FROM ai_knowledge_candidates
                ORDER BY created_at DESC
                LIMIT 200
                """
            ).fetchall()
        )
    for document in documents:
        document["audiences"] = json_loads(
            document.pop("audiences_json"), ["all"]
        )
    for candidate in candidates:
        candidate["indexed"] = False
    return {
        "documents": documents,
        "candidates": candidates,
        "candidate_content_stored": False,
        "web_candidate_auto_approval": False,
    }


def register_public_candidate(
    actor: dict,
    payload: dict,
    idempotency_key: str,
) -> dict:
    forbidden = sorted(CONTENT_KEYS_FORBIDDEN_IN_CANDIDATE & set(payload))
    if forbidden:
        raise KnowledgeError(
            "knowledge_candidate_content_forbidden",
            "公开网页候选只登记元数据，不接收正文",
            details={"forbidden_fields": forbidden},
        )
    source_url = str(payload.get("source_url") or "").strip()
    title = str(payload.get("title") or "").strip()
    source_hash = str(payload.get("source_hash") or "").strip().lower()
    idempotency_key = str(idempotency_key or "").strip()
    parsed = urlparse(source_url)
    if parsed.scheme != "https" or not parsed.netloc:
        raise KnowledgeError(
            "knowledge_candidate_url_invalid", "source_url必须是HTTPS地址"
        )
    if not title or len(title) > 200:
        raise KnowledgeError(
            "knowledge_candidate_title_invalid", "title为必填且不超过200字符"
        )
    if not re.fullmatch(r"[0-9a-f]{64}", source_hash):
        raise KnowledgeError(
            "knowledge_candidate_hash_invalid",
            "source_hash必须是64位SHA-256",
        )
    if not idempotency_key or len(idempotency_key) > 120:
        raise KnowledgeError(
            "idempotency_key_required", "需要有效的Idempotency-Key"
        )
    timestamp = now_iso()
    with get_connection() as conn:
        existing = conn.execute(
            """
            SELECT * FROM ai_knowledge_candidates
            WHERE recorded_by = ? AND idempotency_key = ?
            """,
            (actor["id"], idempotency_key),
        ).fetchone()
        if existing:
            result = row_to_dict(existing)
            result["indexed"] = False
            result["idempotent"] = True
            return result
        candidate_id = new_id("aikq")
        conn.execute(
            """
            INSERT INTO ai_knowledge_candidates
            (id, source_url, title, source_hash, rights_status, review_status,
             status, recorded_by, idempotency_key, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, 'not_reviewed', 'quarantined', ?, ?, ?, ?)
            """,
            (
                candidate_id,
                source_url,
                title,
                source_hash,
                str(payload.get("rights_status") or "unverified"),
                actor["id"],
                idempotency_key,
                timestamp,
                timestamp,
            ),
        )
        write_audit_log(
            conn,
            "ai_knowledge_candidate_quarantined",
            actor["id"],
            "ai_knowledge_candidate",
            candidate_id,
            {
                "source_hash": source_hash,
                "content_stored": False,
                "indexed": False,
                "auto_approved": False,
            },
        )
        conn.commit()
        result = row_to_dict(
            conn.execute(
                "SELECT * FROM ai_knowledge_candidates WHERE id = ?",
                (candidate_id,),
            ).fetchone()
        )
    result["indexed"] = False
    result["idempotent"] = False
    return result


def run_retrieval_evaluation(actor: dict, payload: dict) -> dict:
    cases = payload.get("cases")
    if not isinstance(cases, list) or not cases or len(cases) > 100:
        raise KnowledgeError(
            "knowledge_evaluation_cases_invalid",
            "cases必须包含1至100个固定评测案例",
        )
    suite_version = str(payload.get("suite_version") or "").strip()
    if not suite_version or len(suite_version) > 100:
        raise KnowledgeError(
            "knowledge_evaluation_version_invalid",
            "suite_version为必填且不超过100字符",
        )
    method = str(payload.get("method") or "hybrid").strip().lower()
    if method not in RETRIEVAL_METHODS:
        raise KnowledgeError(
            "knowledge_method_invalid",
            "method仅支持bm25、vector或hybrid",
        )
    results = []
    positive_scores = []
    citation_scores = []
    no_evidence_scores = []
    snapshot_hash = _hash([])
    for index, case in enumerate(cases):
        query = str(case.get("query") or "").strip()
        expected = {
            str(item)
            for item in (case.get("expected_content_ids") or [])
            if str(item)
        }
        retrieval = retrieve_published_content(
            query,
            method=method,
            audience="researcher",
        )
        snapshot_hash = retrieval["knowledge_snapshot_hash"]
        actual = {
            str(item["content_id"]) for item in retrieval["citations"]
        }
        if expected:
            recall = len(expected & actual) / len(expected)
            positive_scores.append(recall)
            citation_correct = all(
                item["content_id"] in expected
                and item.get("chunk_id")
                and item.get("location")
                and item.get("source_ref")
                for item in retrieval["citations"]
            )
            citation_scores.append(1.0 if citation_correct else 0.0)
            passed = recall == 1.0 and citation_correct
        else:
            no_evidence = not retrieval["citations"]
            no_evidence_scores.append(1.0 if no_evidence else 0.0)
            passed = no_evidence
        results.append(
            {
                "case_id": str(case.get("id") or f"case-{index + 1}"),
                "expected_content_ids": sorted(expected),
                "actual_content_ids": sorted(actual),
                "citation_locations": [
                    item.get("location") for item in retrieval["citations"]
                ],
                "passed": bool(passed),
            }
        )

    def average(values: list[float]) -> float:
        return round(sum(values) / len(values), 6) if values else 1.0

    metrics = {
        "recall_at_k": average(positive_scores),
        "citation_accuracy": average(citation_scores),
        "no_evidence_accuracy": average(no_evidence_scores),
        "case_pass_rate": round(
            sum(1 for item in results if item["passed"]) / len(results), 6
        ),
    }
    passed = all(value == 1.0 for value in metrics.values())
    status = (
        "engineering_threshold_passed"
        if passed
        else "engineering_threshold_failed"
    )
    run_id = new_id("aikev")
    timestamp = now_iso()
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO ai_knowledge_evaluation_runs
            (id, suite_version, retrieval_method, metrics_json, result_json,
             knowledge_snapshot_hash, status, created_by, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                suite_version,
                method,
                json_dumps(metrics),
                json_dumps(results),
                snapshot_hash,
                status,
                actor["id"],
                timestamp,
            ),
        )
        write_audit_log(
            conn,
            "ai_knowledge_retrieval_evaluated",
            actor["id"],
            "ai_knowledge_evaluation",
            run_id,
            {
                "suite_version": suite_version,
                "retrieval_method": method,
                "metrics": metrics,
                "human_release_approval": False,
                "raw_queries_logged": False,
            },
        )
        conn.commit()
    return {
        "id": run_id,
        "suite_version": suite_version,
        "retrieval_method": method,
        "metrics": metrics,
        "results": results,
        "knowledge_snapshot_hash": snapshot_hash,
        "status": status,
        "created_by": actor["id"],
        "created_at": timestamp,
        "human_release_approval": False,
    }
