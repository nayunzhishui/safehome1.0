"""Signed-token auth helpers for the formal pilot account MVP."""

from functools import wraps
from typing import Callable

from flask import current_app, request
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from config import Config
from database import get_connection, row_to_dict
from routes.utils import fail, require_admin_token

AUTH_TOKEN_MAX_AGE_SECONDS = 60 * 60 * 24 * 7
ALLOWED_ROLES = {"parent", "student", "researcher", "supervisor", "admin"}
PUBLIC_REGISTER_ROLES = {"parent", "student"}
SHOWCASE_READ_PATH_PREFIXES = (
    "/api/relationship-pilot/researcher/dashboard",
    "/api/relationship-pilot/enrollments",
    "/api/relationship-pilot/reports/",
    "/api/relationship-pilot/narratives/",
    "/api/text-analysis/summary",
)


class AuthError(ValueError):
    def __init__(self, message: str, status: int = 401) -> None:
        super().__init__(message)
        self.status = status


def _serializer() -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(current_app.config["SECRET_KEY"], salt="safehome-auth-v1")


def generate_auth_token(user: dict) -> str:
    auth_epoch = user.get("auth_epoch")
    if auth_epoch is None:
        with get_connection() as conn:
            row = conn.execute("SELECT auth_epoch FROM users WHERE id = ?", (user["id"],)).fetchone()
        auth_epoch = int(row["auth_epoch"] or 0) if row is not None else 0
    return _serializer().dumps(
        {"user_id": user["id"], "role": user["role"], "auth_epoch": int(auth_epoch or 0)}
    )


def verify_auth_token(token: str) -> dict:
    try:
        payload = _serializer().loads(token, max_age=AUTH_TOKEN_MAX_AGE_SECONDS)
    except SignatureExpired as exc:
        raise AuthError("登录已过期，请重新登录", status=401) from exc
    except BadSignature as exc:
        raise AuthError("登录令牌无效", status=401) from exc
    user_id = payload.get("user_id")
    if not user_id:
        raise AuthError("登录令牌无效", status=401)
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    if row is None:
        raise AuthError("登录用户不存在或已停用", status=401)
    user = row_to_dict(row)
    if user.get("status") and user.get("status") != "active":
        raise AuthError("账号暂不可用", status=403)
    if int(payload.get("auth_epoch") or 0) != int(user.get("auth_epoch") or 0):
        raise AuthError("登录状态已更新，请重新登录", status=401)
    return user


def get_current_actor(allow_legacy_admin: bool = True) -> dict | None:
    if allow_legacy_admin and request.headers.get("X-Admin-Token"):
        try:
            require_admin_token()
        except ValueError as exc:
            raise AuthError("后台操作需要有效的 X-Admin-Token", status=401) from exc
        return {"id": "admin-token", "role": "admin", "source": "legacy_admin_token"}
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None
    token = auth_header.removeprefix("Bearer ").strip()
    if not token:
        return None
    user = verify_auth_token(token)
    return {"id": user["id"], "role": user.get("role") or "parent", "source": "auth_token", "user": user}


def require_login(allow_legacy_admin: bool = True) -> dict:
    actor = get_current_actor(allow_legacy_admin=allow_legacy_admin)
    if actor is None:
        raise AuthError("需要先登录", status=401)
    return actor


def require_role(*roles: str, allow_legacy_admin: bool = True) -> dict:
    actor = require_login(allow_legacy_admin=allow_legacy_admin)
    if actor["role"] not in roles:
        from services.showcase_access_service import allow_showcase_read_bypass

        if (
            request.method in {"GET", "HEAD", "OPTIONS"}
            and allow_showcase_read_bypass()
            and request.path.startswith(SHOWCASE_READ_PATH_PREFIXES)
        ):
            return {**actor, "showcase_access": True}
        raise AuthError("当前角色没有权限访问该接口", status=403)
    return actor


def resolve_actor_user_id(
    requested_user_id: str | None = None,
    payload: dict | None = None,
    allow_legacy_admin: bool = False,
    allow_dev_fallback: bool = False,
) -> str:
    """Resolve private-data ownership from the signed token before request data.

    Normal users can only act as themselves. Admin, supervisor and researcher
    actors may target an explicit user_id for review/debug workflows.
    """

    payload_user_id = (payload or {}).get("user_id")
    explicit_user_id = requested_user_id or payload_user_id
    actor = get_current_actor(allow_legacy_admin=allow_legacy_admin)
    if actor:
        role = actor.get("role")
        if role in {"admin", "supervisor", "researcher"}:
            if explicit_user_id:
                return str(explicit_user_id)
            if actor.get("source") == "legacy_admin_token":
                raise AuthError("后台查询需要指定 user_id", status=400)
        return str(actor["id"])

    if allow_dev_fallback and str(Config.APP_ENV).lower() == "development":
        return str(explicit_user_id or "demo-parent")

    raise AuthError("需要先登录", status=401)


def auth_error_response(exc: AuthError):
    code_by_status = {
        400: "validation_error",
        401: "unauthorized",
        403: "forbidden",
    }
    return fail(code_by_status.get(exc.status, "auth_error"), str(exc), status=exc.status)


def role_required(*roles: str, allow_legacy_admin: bool = True):
    def decorator(fn: Callable):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            try:
                require_role(*roles, allow_legacy_admin=allow_legacy_admin)
            except AuthError as exc:
                return auth_error_response(exc)
            return fn(*args, **kwargs)

        return wrapper

    return decorator
