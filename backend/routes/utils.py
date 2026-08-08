"""Small response and parsing helpers for route modules."""

import os

from flask import current_app, g, has_request_context, jsonify, request


def ok(data=None, status: int = 200):
    request_id = getattr(g, "request_id", None) if has_request_context() else None
    return jsonify({"ok": True, "data": data if data is not None else {}, "request_id": request_id}), status


def fail(code: str, message: str, status: int = 400, details: dict | list | None = None):
    request_id = getattr(g, "request_id", None) if has_request_context() else None
    error = {"code": code, "message": message}
    if details is not None:
        error["details"] = details
    return jsonify({"ok": False, "error": error, "request_id": request_id}), status


def _legacy_admin_token_enabled() -> bool:
    configured = os.environ.get("LEGACY_ADMIN_TOKEN_ENABLED")
    if configured is not None:
        return configured.strip().lower() in {"1", "true", "yes"}
    return str(current_app.config.get("APP_ENV", "development")).lower() in {"development", "testing"}


def require_admin_token() -> str:
    if not _legacy_admin_token_enabled():
        raise ValueError("当前环境已停用 X-Admin-Token，请使用具名后台账号登录")
    admin_token = current_app.config.get("ADMIN_EXPORT_TOKEN")
    request_token = request.headers.get("X-Admin-Token", "")
    if not admin_token or request_token != admin_token:
        raise ValueError("后台操作需要有效的 X-Admin-Token")
    return "admin-token"


def admin_token_error_response(exc: ValueError):
    return fail("unauthorized", str(exc), status=401)


def get_request_user_id() -> str | None:
    """Development-only compatibility accessor for pre-auth endpoints."""
    if str(current_app.config.get("APP_ENV", "development")).lower() != "development":
        return None
    payload = None
    if request.method in {"POST", "PUT", "PATCH"}:
        payload = request.get_json(silent=True) or {}
    user_id = request.args.get("user_id") or request.headers.get("X-User-Id") or (payload or {}).get("user_id")
    return str(user_id) if user_id else None


def require_admin_or_owner(record_user_id: str | None) -> str:
    from routes.auth_utils import AuthError, get_current_actor

    try:
        actor = get_current_actor(allow_legacy_admin=True)
    except AuthError as exc:
        raise ValueError(str(exc)) from exc
    if actor is not None:
        if actor.get("role") in {"admin", "supervisor", "researcher"}:
            return str(actor["id"])
        if record_user_id and str(actor.get("id")) == str(record_user_id):
            return str(actor["id"])
        raise ValueError("只能访问自己的数据")

    if str(current_app.config.get("APP_ENV", "development")).lower() != "development":
        raise ValueError("需要先登录")
    request_user_id = get_request_user_id()
    if record_user_id and request_user_id and str(record_user_id) == str(request_user_id):
        return str(request_user_id)
    raise ValueError("需要登录；匿名 user_id 兼容仅允许本地开发环境")


def auth_error_response(exc: ValueError):
    return fail("unauthorized", str(exc), status=401)


def require_fields(payload: dict, fields: list[str]) -> list[str]:
    return [field for field in fields if payload.get(field) in (None, "")]


def require_user_id(payload: dict) -> str:
    """Compatibility wrapper; authenticated actor remains authoritative."""
    from routes.auth_utils import AuthError, resolve_actor_user_id

    try:
        return resolve_actor_user_id(payload=payload, allow_dev_fallback=True)
    except AuthError as exc:
        raise ValueError(str(exc)) from exc


def resolve_user_id_for_query(user_id: str | None) -> str:
    from routes.auth_utils import AuthError, resolve_actor_user_id

    try:
        return resolve_actor_user_id(
            requested_user_id=user_id,
            allow_legacy_admin=True,
            allow_dev_fallback=True,
        )
    except AuthError as exc:
        raise ValueError(str(exc)) from exc


def parse_int(value, default: int | None = None) -> int | None:
    if value in (None, ""):
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def parse_bool(value, default: bool = False) -> bool:
    if value in (None, ""):
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y", "完成", "是"}
