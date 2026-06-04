"""Small response and parsing helpers for route modules."""

from flask import current_app, jsonify, request

from config import Config


def ok(data=None, status: int = 200):
    return jsonify({"ok": True, "data": data if data is not None else {}}), status


def fail(code: str, message: str, status: int = 400):
    return jsonify({"ok": False, "error": {"code": code, "message": message}}), status


def require_admin_token() -> str:
    admin_token = current_app.config.get("ADMIN_EXPORT_TOKEN")
    request_token = request.headers.get("X-Admin-Token", "")
    if not admin_token or request_token != admin_token:
        raise ValueError("后台操作需要有效的 X-Admin-Token")
    return "admin-token"


def admin_token_error_response(exc: ValueError):
    return fail("unauthorized", str(exc), status=401)


def require_fields(payload: dict, fields: list[str]) -> list[str]:
    return [field for field in fields if payload.get(field) in (None, "")]


def require_user_id(payload: dict) -> str:
    user_id = payload.get("user_id")
    if user_id:
        return str(user_id)
    if str(Config.APP_ENV).lower() == "development":
        return "demo-parent"
    raise ValueError("正式环境必须提供匿名 user_id")


def resolve_user_id_for_query(user_id: str | None) -> str:
    if user_id:
        return str(user_id)
    if str(Config.APP_ENV).lower() == "development":
        return "demo-parent"
    raise ValueError("正式环境查询必须提供匿名 user_id")


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
