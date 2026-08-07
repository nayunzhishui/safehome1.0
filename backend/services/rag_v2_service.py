"""Governed RAG v2 retrieval: BM25 + vector + RRF + deterministic rerank.

This pipeline reads only the already-approved knowledge index.  It does not
crawl the web, index participant text, or auto-approve candidate content.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
from collections import Counter
from typing import Any

from services import ai_qa_retrieval_service as legacy
from services.embedding_service import EmbeddingError, embed_text, embedding_model, public_status as embedding_status
from services.redis_service import get_json, set_json


def _int(name: str, default: int, minimum: int, maximum: int) -> int:
    try:
        value = int(os.environ.get(name, str(default)))
    except (TypeError, ValueError):
        value = default
    return max(minimum, min(value, maximum))


def settings() -> dict[str, Any]:
    return {
        "lexical_top_k": _int("RAG_LEXICAL_TOP_K", 20, 1, 100),
        "vector_top_k": _int("RAG_VECTOR_TOP_K", 30, 1, 100),
        "final_context_k": _int("RAG_FINAL_CONTEXT_K", 6, 1, 12),
        "rrf_k": _int("RAG_RRF_K", 60, 1, 1000),
        "cache_ttl_seconds": _int("RAG_CACHE_TTL_SECONDS", 300, 5, 3600),
        "max_chunks_per_document": _int("RAG_MAX_CHUNKS_PER_DOCUMENT", 1, 1, 3),
    }


def _cosine(left: list[float], right: list[float]) -> float:
    if not left or not right or len(left) != len(right):
        return 0.0
    left_norm = math.sqrt(sum(float(value) ** 2 for value in left))
    right_norm = math.sqrt(sum(float(value) ** 2 for value in right))
    if not left_norm or not right_norm:
        return 0.0
    return max(-1.0, min(1.0, sum(float(a) * float(b) for a, b in zip(left, right)) / (left_norm * right_norm)))


def _bm25_scores(rows: list[dict], query_terms: list[str]) -> dict[str, float]:
    if not rows or not query_terms:
        return {}
    average_length = sum(max(1, len(item["terms"])) for item in rows) / len(rows)
    document_frequency = Counter()
    for term in set(query_terms):
        document_frequency[term] = sum(1 for item in rows if term in set(item["terms"]))
    scores: dict[str, float] = {}
    for item in rows:
        term_counts = Counter(item["terms"])
        length = max(1, len(item["terms"]))
        score = 0.0
        for term in query_terms:
            frequency = term_counts.get(term, 0)
            if not frequency:
                continue
            df = document_frequency.get(term, 0)
            inverse = math.log(1 + (len(rows) - df + 0.5) / (df + 0.5))
            denominator = frequency + 1.2 * (1 - 0.75 + 0.75 * length / max(1.0, average_length))
            score += inverse * (frequency * 2.2) / denominator
        if score > 0:
            scores[item["id"]] = score
    return scores


def _stored_embedding(item: dict) -> list[float] | None:
    raw = item.get("embedding_json")
    if raw:
        try:
            values = json.loads(raw) if isinstance(raw, str) else raw
            if isinstance(values, list) and values:
                return [float(value) for value in values]
        except (TypeError, ValueError, json.JSONDecodeError):
            return None
    values = item.get("vector")
    return [float(value) for value in values] if isinstance(values, list) and values else None


def _query_vector(query: str, rows: list[dict]) -> tuple[list[float], str, bool]:
    has_external_embeddings = any(str(item.get("embedding_model") or "").strip() for item in rows)
    if has_external_embeddings:
        try:
            return embed_text(query), embedding_model(), False
        except EmbeddingError:
            pass
    terms = legacy._terms(query)
    return [float(value) for value in legacy._vector(terms)], "safehome-hash-96-v1", True


def _rerank(query: str, query_terms: list[str], item: dict) -> float:
    heading = str(item.get("heading") or "")
    content = str(item.get("content_text") or "")
    heading_terms = set(legacy._terms(heading))
    query_set = set(query_terms)
    heading_overlap = len(query_set & heading_terms) / max(1, len(query_set))
    phrase_bonus = 0.25 if query and query.lower() in content.lower() else 0.0
    source_bonus = 0.05 if str(item.get("review_status") or "") == "approved" else 0.0
    return min(1.0, heading_overlap * 0.7 + phrase_bonus + source_bonus)


def _cache_key(query: str, audience: str, snapshot_hash: str, limit: int) -> str:
    digest = hashlib.sha256(f"{query}|{audience}|{snapshot_hash}|{limit}|rag-v2".encode("utf-8")).hexdigest()
    return f"rag:v2:{digest}"


def retrieve_published_content_v2(
    query: str,
    limit: int = 4,
    *,
    method: str = "hybrid",
    audience: str = "researcher",
) -> dict:
    query = str(query or "").strip()
    audience = str(audience or "researcher").strip().lower()
    method = str(method or "hybrid").strip().lower()
    if not query:
        raise legacy.KnowledgeError("knowledge_query_required", "query不能为空")
    if len(query) > legacy.MAX_QUERY_LENGTH:
        raise legacy.KnowledgeError("knowledge_query_too_long", f"query不能超过{legacy.MAX_QUERY_LENGTH}个字符")
    if audience not in legacy.ALLOWED_AUDIENCES:
        raise legacy.KnowledgeError("knowledge_audience_invalid", "适用人群不受支持")
    if method not in {"bm25", "vector", "hybrid", "rrf"}:
        raise legacy.KnowledgeError("knowledge_method_invalid", "method仅支持bm25、vector、hybrid或rrf")

    cfg = settings()
    limit = max(1, min(int(limit or cfg["final_context_k"]), cfg["final_context_k"]))
    legacy.sync_approved_knowledge()
    rows = legacy._active_rows(audience)
    query_terms = legacy._terms(query)
    snapshot_hash = legacy._knowledge_snapshot(rows)
    cache_key = _cache_key(query, audience, snapshot_hash, limit)
    cached = get_json(cache_key)
    if isinstance(cached, dict):
        cached["cache"] = "redis_hit"
        return cached
    if not rows or not query_terms:
        return {
            "citations": [],
            "knowledge_snapshot_hash": snapshot_hash,
            "only_published": True,
            "retrieval_method": "rag_v2_rrf",
            "evidence_status": "insufficient",
            "audience": audience,
            "cache": "miss",
        }

    by_id = {item["id"]: item for item in rows}
    bm25 = _bm25_scores(rows, query_terms)
    lexical_rank = sorted(bm25, key=lambda item_id: (bm25[item_id], item_id), reverse=True)[: cfg["lexical_top_k"]]

    query_vector, query_model, embedding_fallback = _query_vector(query, rows)
    vector_scores = {}
    for item in rows:
        vector = _stored_embedding(item)
        score = _cosine(query_vector, vector or [])
        if score > 0:
            vector_scores[item["id"]] = score
    vector_rank = sorted(vector_scores, key=lambda item_id: (vector_scores[item_id], item_id), reverse=True)[: cfg["vector_top_k"]]

    if method == "bm25":
        candidate_ids = lexical_rank
    elif method == "vector":
        candidate_ids = vector_rank
    else:
        candidate_ids = list(dict.fromkeys(lexical_rank + vector_rank))

    lexical_position = {item_id: index + 1 for index, item_id in enumerate(lexical_rank)}
    vector_position = {item_id: index + 1 for index, item_id in enumerate(vector_rank)}
    scored = []
    for item_id in candidate_ids:
        item = by_id[item_id]
        rrf = 0.0
        if item_id in lexical_position:
            rrf += 1.0 / (cfg["rrf_k"] + lexical_position[item_id])
        if item_id in vector_position:
            rrf += 1.0 / (cfg["rrf_k"] + vector_position[item_id])
        rerank = _rerank(query, query_terms, item)
        if method == "bm25":
            final = bm25.get(item_id, 0.0) + 0.1 * rerank
        elif method == "vector":
            final = vector_scores.get(item_id, 0.0) + 0.1 * rerank
        else:
            final = rrf + 0.005 * rerank
        scored.append((final, rrf, rerank, item_id))
    scored.sort(reverse=True)

    citations = []
    document_counts: Counter = Counter()
    for final, rrf, rerank, item_id in scored:
        item = by_id[item_id]
        if document_counts[item["document_id"]] >= cfg["max_chunks_per_document"]:
            continue
        document_counts[item["document_id"]] += 1
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
                "excerpt": str(item["content_text"])[:360],
                "source_ref": item["source_ref"],
                "source_version": item["source_version"],
                "rights_status": item["rights_status"],
                "review_status": item["review_status"],
                "valid_from": item.get("valid_from"),
                "expires_at": item.get("expires_at"),
                "audiences": item["audiences"],
                "package_hash": item.get("package_hash"),
                "retrieval_method": "rag_v2_rrf",
                "embedding_model": item.get("embedding_model") or query_model,
                "scores": {
                    "bm25": round(bm25.get(item_id, 0.0), 6),
                    "vector": round(vector_scores.get(item_id, 0.0), 6),
                    "rrf": round(rrf, 8),
                    "rerank": round(rerank, 6),
                    "final": round(final, 8),
                },
            }
        )
        if len(citations) >= limit:
            break

    result = {
        "citations": citations,
        "knowledge_snapshot_hash": snapshot_hash,
        "only_published": True,
        "retrieval_method": "rag_v2_rrf",
        "requested_method": method,
        "evidence_status": "sufficient" if citations else "insufficient",
        "audience": audience,
        "embedding": {**embedding_status(), "query_model": query_model, "fallback_used": embedding_fallback},
        "pipeline": cfg,
        "cache": "miss",
    }
    set_json(cache_key, result, cfg["cache_ttl_seconds"])
    return result


def install_rag_v2() -> dict:
    """Install the v2 function before app/routes import it by name."""
    legacy.retrieve_published_content = retrieve_published_content_v2
    return {"installed": True, "pipeline": "rag_v2_rrf", "settings": settings(), "embedding": embedding_status()}
