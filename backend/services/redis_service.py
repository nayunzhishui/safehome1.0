"""Optional Redis cache/coordination layer.

Redis is never a source of truth for consent, risk review, assessment results or
other participant records.  All helpers fail soft unless the caller explicitly
chooses to block on Redis availability.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import threading
import time
from typing import Any


_LOCK = threading.Lock()
_CLIENT = None
_LAST_ERROR: str | None = None


def _bool(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _int(name: str, default: int, minimum: int, maximum: int) -> int:
    try:
        value = int(os.environ.get(name, str(default)))
    except (TypeError, ValueError):
        value = default
    return max(minimum, min(value, maximum))


def settings() -> dict[str, Any]:
    url = os.environ.get("REDIS_URL", "").strip()
    return {
        "enabled": bool(url) and _bool("REDIS_ENABLED", default=True),
        "url_configured": bool(url),
        "namespace": os.environ.get("REDIS_NAMESPACE", "safehome").strip() or "safehome",
        "socket_connect_timeout_seconds": _int("REDIS_CONNECT_TIMEOUT_SECONDS", 2, 1, 30),
        "socket_timeout_seconds": _int("REDIS_SOCKET_TIMEOUT_SECONDS", 2, 1, 30),
        "default_cache_ttl_seconds": _int("REDIS_CACHE_TTL_SECONDS", 300, 5, 86400),
    }


def _key(value: str) -> str:
    namespace = settings()["namespace"]
    return f"{namespace}:{value}"


def hash_component(value: str, *, salt: str = "safehome") -> str:
    return hashlib.sha256(f"{salt}:{value}".encode("utf-8")).hexdigest()[:24]


def get_client():
    global _CLIENT, _LAST_ERROR
    if not settings()["enabled"]:
        return None
    if _CLIENT is not None:
        return _CLIENT
    with _LOCK:
        if _CLIENT is not None:
            return _CLIENT
        try:
            import redis

            cfg = settings()
            _CLIENT = redis.Redis.from_url(
                os.environ["REDIS_URL"],
                decode_responses=True,
                socket_connect_timeout=cfg["socket_connect_timeout_seconds"],
                socket_timeout=cfg["socket_timeout_seconds"],
                health_check_interval=30,
                retry_on_timeout=True,
            )
            _CLIENT.ping()
            _LAST_ERROR = None
        except Exception as exc:
            _CLIENT = None
            _LAST_ERROR = exc.__class__.__name__
    return _CLIENT


def health() -> dict[str, Any]:
    client = get_client()
    if client is None:
        return {
            "enabled": settings()["enabled"],
            "ok": not settings()["enabled"],
            "status": "disabled" if not settings()["enabled"] else "unavailable",
            "error_class": _LAST_ERROR,
        }
    started = time.perf_counter()
    try:
        client.ping()
        latency = round((time.perf_counter() - started) * 1000, 2)
        return {"enabled": True, "ok": True, "status": "ready", "latency_ms": latency}
    except Exception as exc:
        return {"enabled": True, "ok": False, "status": "unavailable", "error_class": exc.__class__.__name__}


def get_json(key: str) -> Any | None:
    client = get_client()
    if client is None:
        return None
    try:
        raw = client.get(_key(key))
        return json.loads(raw) if raw else None
    except Exception:
        return None


def set_json(key: str, value: Any, ttl_seconds: int | None = None) -> bool:
    client = get_client()
    if client is None:
        return False
    ttl = ttl_seconds or settings()["default_cache_ttl_seconds"]
    try:
        client.set(_key(key), json.dumps(value, ensure_ascii=False, separators=(",", ":")), ex=max(1, int(ttl)))
        return True
    except Exception:
        return False


def delete(key: str) -> bool:
    client = get_client()
    if client is None:
        return False
    try:
        client.delete(_key(key))
        return True
    except Exception:
        return False


def acquire_once(key: str, ttl_seconds: int = 300) -> bool | None:
    """Return True when acquired, False when already present, None if Redis unavailable."""
    client = get_client()
    if client is None:
        return None
    try:
        return bool(client.set(_key(key), "1", ex=max(1, int(ttl_seconds)), nx=True))
    except Exception:
        return None


def rate_limit(
    key: str,
    *,
    limit: int,
    window_seconds: int,
    unavailable_policy: str = "allow",
) -> dict[str, Any]:
    """Apply a fixed-window limit with an explicit Redis failure policy.

    ``deny_if_enabled`` permits intentional local disablement but blocks when a
    configured Redis instance is unavailable. ``deny`` is used by production
    authentication and other abuse-sensitive paths.
    """
    if unavailable_policy not in {"allow", "deny", "deny_if_enabled"}:
        raise ValueError("unsupported Redis unavailable policy")
    client = get_client()
    limit = max(1, int(limit))
    window_seconds = max(1, int(window_seconds))
    now = int(time.time())
    bucket = now // window_seconds
    redis_key = _key(f"ratelimit:{key}:{bucket}")
    retry_after = max(1, (bucket + 1) * window_seconds - now)
    if client is None:
        redis_enabled = bool(settings().get("enabled"))
        allowed = unavailable_policy == "allow" or (
            unavailable_policy == "deny_if_enabled" and not redis_enabled
        )
        return {
            "available": False,
            "allowed": allowed,
            "limit": limit,
            "remaining": limit,
            "retry_after": retry_after,
            "reason": "redis_disabled" if not redis_enabled else "redis_unavailable",
        }
    try:
        pipe = client.pipeline(transaction=True)
        pipe.incr(redis_key)
        pipe.expire(redis_key, window_seconds + 2)
        count, _ = pipe.execute()
        count = int(count)
        return {
            "available": True,
            "allowed": count <= limit,
            "limit": limit,
            "remaining": max(0, limit - count),
            "retry_after": retry_after,
            "reason": "allowed" if count <= limit else "rate_limited",
        }
    except Exception:
        allowed = unavailable_policy == "allow"
        return {
            "available": False,
            "allowed": allowed,
            "limit": limit,
            "remaining": limit,
            "retry_after": retry_after,
            "reason": "redis_unavailable",
        }
