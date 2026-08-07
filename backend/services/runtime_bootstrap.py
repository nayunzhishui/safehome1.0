"""Production runtime bootstrap kept separate from Flask domain code."""

from __future__ import annotations

import hashlib
import os
from typing import Any

from flask import g, jsonify, request
from werkzeug.middleware.proxy_fix import ProxyFix

from services.mysql_pool_runtime import install_mysql_pool, status as mysql_pool_status
from services.redis_service import health as redis_health, rate_limit


_PRE_APP_STATUS: dict[str, Any] = {}


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


def install_pre_app() -> dict[str, Any]:
    """Install adapters that must exist before app.py imports routes/services."""
    global _PRE_APP_STATUS
    mysql = install_mysql_pool()
    rag = {"installed": False, "reason": "disabled"}
    if _bool("RAG_V2_ENABLED", default=True):
        from services.rag_v2_service import install_rag_v2

        rag = install_rag_v2()
    _PRE_APP_STATUS = {"mysql_pool": mysql, "rag": rag}
    return dict(_PRE_APP_STATUS)


def _client_key(app) -> str:
    value = str(request.remote_addr or "unknown")
    secret = str(app.config.get("SECRET_KEY") or "safehome-runtime")
    return hashlib.sha256(f"{secret}:{value}".encode("utf-8")).hexdigest()[:24]


def _limit_for_path(path: str) -> tuple[str, int, int] | None:
    if path == "/api/auth/login":
        return "auth-login", _int("REDIS_LOGIN_RATE_LIMIT_PER_MINUTE", 20, 5, 300), 60
    if path.startswith("/api/ai-qa/") and path not in {"/api/ai-qa/config", "/api/ai-qa/use-cases"}:
        return "ai-qa", _int("REDIS_AI_RATE_LIMIT_PER_MINUTE", 60, 5, 600), 60
    return None


def configure_app(app) -> dict[str, Any]:
    """Apply infrastructure-only WSGI/runtime controls; no UI behavior lives here."""
    max_body = _int("MAX_REQUEST_BODY_BYTES", 1024 * 1024, 64 * 1024, 10 * 1024 * 1024)
    app.config["MAX_CONTENT_LENGTH"] = max_body

    proxy_hops = _int("TRUST_PROXY_HOPS", 0, 0, 4)
    if proxy_hops:
        app.wsgi_app = ProxyFix(
            app.wsgi_app,
            x_for=proxy_hops,
            x_proto=proxy_hops,
            x_host=proxy_hops,
            x_port=proxy_hops,
        )

    @app.before_request
    def distributed_runtime_rate_limit():
        if request.method == "OPTIONS":
            return None
        spec = _limit_for_path(request.path)
        if spec is None:
            return None
        bucket_name, limit, window = spec
        decision = rate_limit(f"{bucket_name}:{_client_key(app)}", limit=limit, window_seconds=window)
        g.redis_rate_limit = decision
        if decision["allowed"]:
            return None
        response = jsonify(
            {
                "ok": False,
                "error": {"code": "rate_limited", "message": "请求过于频繁，请稍后再试。"},
                "request_id": getattr(g, "request_id", None),
            }
        )
        response.status_code = 429
        response.headers["Retry-After"] = str(decision["retry_after"])
        return response

    @app.after_request
    def add_runtime_rate_headers(response):
        decision = getattr(g, "redis_rate_limit", None)
        if isinstance(decision, dict) and decision.get("available"):
            response.headers["X-RateLimit-Limit"] = str(decision["limit"])
            response.headers["X-RateLimit-Remaining"] = str(decision["remaining"])
        return response

    status = {
        "pre_app": dict(_PRE_APP_STATUS),
        "mysql_pool": mysql_pool_status(),
        "redis": redis_health(),
        "proxy_hops": proxy_hops,
        "max_request_body_bytes": max_body,
    }
    app.extensions["safehome_engineering_runtime"] = status
    return status
