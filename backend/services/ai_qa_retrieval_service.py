"""Retrieve only active, published content-governance versions for AI QA."""

from __future__ import annotations

import hashlib
import json
import re

from database import get_connection, json_loads


ALLOWED_CONTENT_TYPES = {"training_card", "course", "faq", "consent_text", "privacy_text"}


def _canonical(value) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _tokens(text: str) -> set[str]:
    compact = re.sub(r"\s+", "", text.lower())
    latin = set(re.findall(r"[a-z0-9_]{2,}", compact))
    chinese = {compact[index : index + 2] for index in range(max(0, len(compact) - 1)) if "\u4e00" <= compact[index] <= "\u9fff"}
    return latin | chinese


def _payload_text(payload) -> tuple[str, str]:
    if isinstance(payload, str):
        return "边界说明", payload[:800]
    title = str(payload.get("title") or payload.get("display_name") or payload.get("label") or payload.get("id") or "已批准内容")
    parts = [payload.get("purpose"), payload.get("core_concept"), payload.get("body"), payload.get("boundary_notice")]
    for field in ("steps", "sections", "safety_notes"):
        value = payload.get(field)
        if isinstance(value, list):
            for item in value[:8]:
                if isinstance(item, dict):
                    parts.extend([item.get("title"), item.get("content"), item.get("description")])
                else:
                    parts.append(item)
    text = " ".join(str(item).strip() for item in parts if item)
    return title, text[:1200]


def retrieve_published_content(query: str, limit: int = 4) -> dict:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT v.id, v.content_type, v.item_id, v.version, v.payload_json, v.payload_hash,
                   r.id AS release_id, r.package_json
            FROM content_governance_versions v
            JOIN content_governance_releases r ON r.version_id = v.id AND r.status = 'active'
            WHERE v.status = 'published'
            ORDER BY r.created_at DESC
            """
        ).fetchall()
    query_tokens = _tokens(query)
    candidates = []
    for row in rows:
        if row["content_type"] not in ALLOWED_CONTENT_TYPES:
            continue
        payload = json_loads(row["payload_json"], {})
        title, text = _payload_text(payload)
        source_tokens = _tokens(f"{title} {text}")
        score = len(query_tokens & source_tokens)
        if score == 0 and query_tokens:
            continue
        package = json_loads(row["package_json"], {})
        candidates.append(
            (
                score,
                {
                    "content_id": row["item_id"],
                    "content_type": row["content_type"],
                    "version_id": row["id"],
                    "content_version": row["version"],
                    "release_id": row["release_id"],
                    "payload_hash": row["payload_hash"],
                    "governance_status": "published",
                    "title": title,
                    "excerpt": text[:360],
                    "package_hash": package.get("package_hash"),
                },
            )
        )
    candidates.sort(key=lambda item: (item[0], item[1]["content_id"]), reverse=True)
    citations = [item for _score, item in candidates[: max(1, min(limit, 8))]]
    snapshot_hash = hashlib.sha256(_canonical([{key: item.get(key) for key in ("version_id", "release_id", "payload_hash")} for item in citations]).encode("utf-8")).hexdigest()
    return {"citations": citations, "knowledge_snapshot_hash": snapshot_hash, "only_published": True}
