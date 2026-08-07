"""Embedding adapter used by the governed RAG v2 pipeline.

Default mode is deterministic local hashing, so tests and offline research never
require an external provider.  An OpenAI-compatible embeddings endpoint can be
opted in explicitly for approved internal knowledge only.
"""

from __future__ import annotations

import json
import math
import os
import urllib.error
import urllib.request
from typing import Iterable


class EmbeddingError(RuntimeError):
    pass


def _provider() -> str:
    return os.environ.get("RAG_EMBEDDING_PROVIDER", "hash").strip().lower() or "hash"


def embedding_model() -> str:
    if _provider() == "hash":
        return "safehome-hash-96-v1"
    return os.environ.get("RAG_EMBEDDING_MODEL", "").strip() or "unconfigured"


def _normalize(values: list[float]) -> list[float]:
    if not values:
        raise EmbeddingError("embedding为空")
    if any(not math.isfinite(float(value)) for value in values):
        raise EmbeddingError("embedding包含非有限数值")
    norm = math.sqrt(sum(float(value) * float(value) for value in values))
    if not norm:
        raise EmbeddingError("embedding范数为0")
    return [float(value) / norm for value in values]


def _hash_embedding(text: str) -> list[float]:
    # Reuse the existing deterministic vectorizer to preserve offline parity.
    from services.ai_qa_retrieval_service import _terms, _vector

    return [float(value) for value in _vector(_terms(text))]


def _openai_compatible_embeddings(texts: list[str]) -> list[list[float]]:
    base_url = os.environ.get("RAG_EMBEDDING_BASE_URL", "").strip().rstrip("/")
    api_key = os.environ.get("RAG_EMBEDDING_API_KEY", "").strip()
    model = os.environ.get("RAG_EMBEDDING_MODEL", "").strip()
    if not base_url or not api_key or not model:
        raise EmbeddingError("外部embedding需要RAG_EMBEDDING_BASE_URL/API_KEY/MODEL")
    timeout = max(1.0, min(float(os.environ.get("RAG_EMBEDDING_TIMEOUT_SECONDS", "10")), 60.0))
    body = json.dumps({"model": model, "input": texts}, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        f"{base_url}/embeddings",
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise EmbeddingError(f"embedding供应商调用失败:{exc.__class__.__name__}") from exc
    data = payload.get("data") if isinstance(payload, dict) else None
    if not isinstance(data, list) or len(data) != len(texts):
        raise EmbeddingError("embedding供应商返回数量不匹配")
    ordered = sorted(data, key=lambda item: int(item.get("index", 0)))
    vectors = []
    for item in ordered:
        values = item.get("embedding") if isinstance(item, dict) else None
        if not isinstance(values, list):
            raise EmbeddingError("embedding供应商返回格式无效")
        vectors.append(_normalize([float(value) for value in values]))
    dimensions = {len(item) for item in vectors}
    if len(dimensions) != 1:
        raise EmbeddingError("embedding维度不一致")
    return vectors


def embed_texts(texts: Iterable[str]) -> list[list[float]]:
    normalized = [str(text or "").strip() for text in texts]
    if not normalized or any(not text for text in normalized):
        raise EmbeddingError("embedding输入不能为空")
    provider = _provider()
    if provider == "hash":
        return [_hash_embedding(text) for text in normalized]
    if provider == "openai_compatible":
        return _openai_compatible_embeddings(normalized)
    raise EmbeddingError("RAG_EMBEDDING_PROVIDER仅支持hash或openai_compatible")


def embed_text(text: str) -> list[float]:
    return embed_texts([text])[0]


def public_status() -> dict:
    provider = _provider()
    return {
        "provider": provider,
        "model": embedding_model(),
        "external": provider != "hash",
        "api_key_configured": bool(os.environ.get("RAG_EMBEDDING_API_KEY", "").strip()) if provider != "hash" else False,
        "raw_participant_indexing_allowed": False,
    }
