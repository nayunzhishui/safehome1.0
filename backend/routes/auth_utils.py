"""Signed-token auth helpers for the formal pilot account MVP."""

import os

from flask import current_app, request
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from config import Config
from database import get_connection, row_to_dict
from routes.utils import fail, require_admin_token

AUTH_TOKEN_MAX_AGE_SECONDS = 60 * 60 * 24 * 7
ALLOWED_ROLES = {"parent", "student", "researcher", "supervisor", "admin"}
PUBLIC_REGISTER_ROLES = {"parent", "student"}
# Formal researcher data never uses the generic showcase read bypass. The
# separate development exception below is limited to named research-platform
# namespaces and must be disabled before formal authorization acceptance.
SHOWCASE_READ_PATH_PREFIXES: tuple[str, ...] = ()
SHOWCASE_RESEARCHER_PLATFORM_PATH_PREFIXES = (
    "/api/research/",
    "/api/therapeutic-assessment/",
    "/api/ai-qa/",
    "/api/relationship-pilot/",
    "/api/text-analysis/",
    "/api/operations-governance/",
    "/api/reliability/",
    "/api/content-review/",
    "/api/security/",
    "/api/ux-governance/",
    "/api/risk-review/",
    "/api/supervision/",
)
SHOWCASE_RESEARCHER_PLATFORM_OPERATIONS = {
    # Researcher-to-participant messaging lives outside a research namespace.
    ("POST", "/api/messages"),
}
SHOWCASE_RESEARCHER_WORKSPACE_HEADER = "X-SafeHome-Researcher-Workspace"


class AuthError(ValueError):
    def __init__(self, message: str, status: int = 401, code: str | None = None, details: dict | None = None) -> None:
        super().__init__(message)
        self.status = status
        self.code = code
        self.details = details


def legacy_admin_token_enabled() -> bool:
    """Return whether the compatibility X-Admin-Token path is allowed.

    The old static token remains available for local/test migration work, but
    pilot and production converge on named authenticated actors by default.
    A deployment that still needs the compatibility path must opt in explicitly
    with LEGACY_ADMIN_TOKEN_ENABLED=1 and should treat that as temporary debt.
    """

    configured = os.environ.get("LEGACY_ADMIN_TOKEN_ENABLED")
    if configured is not None:
        return configured.strip().lower() in {"1", "true", "yes"}
    return str(Config.APP_ENV or "development").strip().lower() in {"development", "testing"}


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
        if not legacy_admin_token_enabled():
            raise AuthError(
                "当前环境已停用 X-Admin-Token，请使用具名后台账号登录。",
                status=401,
                code="legacy_admin_token_disabled",
            )
        try:
            require_admin_token()
        except ValueError as exc:
            raise AuthError("后台操作需要有效的 X-Admin-Token", status=401) from exc
        return {
            "id": "admin-token",
            "role": "admin",
            "source": "legacy_admin_token",
            "legacy_auth": True,
        }
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None
    token = auth_header.removeprefix("Bearer ").strip()
    if not token:
        return None
    user = verify_auth_token(token)
    if bool(user.get("must_change_password")) and request.path not in {
        "/api/auth/me",
        "/api/auth/change-password",
        "/api/auth/logout",
    }:
        raise AuthError("首次登录需要先修改一次性密码", status=403, code="password_change_required")
    return {
        "id": user["id"],
        "role": user.get("role") or "parent",
        "source": "auth_token",
        "legacy_auth": False,
        "user": user,
    }


def require_login(allow_legacy_admin: bool = True) -> dict:
    actor = get_current_actor(allow_legacy_admin=allow_legacy_admin)
    if actor is None:
        raise AuthError("需要先登录", status=401)
    return actor


def elevate_actor_for_showcase_researcher_platform(actor: dict) -> dict:
    """Temporarily elevate signed-in users for research-platform operations.

    This development exception covers reads and writes, including research
    permission configuration and module-specific release gates. It does not
    cover generic account administration or unrelated participant APIs.
    Downstream services still enforce payload, state-machine, evidence and
    ownership invariants. ``original_role`` prevents the elevation from being
    mistaken for guardian/minor authorization.
    """

    from services.showcase_access_service import allow_showcase_researcher_platform_full_access

    if (
        allow_showcase_researcher_platform_full_access()
        and request.headers.get(SHOWCASE_RESEARCHER_WORKSPACE_HEADER) == "1"
        and (
            request.path.startswith(SHOWCASE_RESEARCHER_PLATFORM_PATH_PREFIXES)
            or (request.method, request.path) in SHOWCASE_RESEARCHER_PLATFORM_OPERATIONS
        )
    ):
        return {
            **actor,
            "original_role": actor.get("original_role") or actor.get("role"),
            "role": "admin",
            "showcase_access": True,
            "showcase_full_access": True,
        }
    return actor


def require_role(*roles: str, allow_legacy_admin: bool = True) -> dict:
    actor = elevate_actor_for_showcase_researcher_platform(
        require_login(allow_legacy_admin=allow_legacy_admin)
    )
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


def require_capability(capability_id: str, allow_legacy_admin: bool = True) -> dict:
    """Authorize a versioned research capability on the server."""

    from services.research_access_service import ResearchAccessError, assert_capability

    actor = elevate_actor_for_showcase_researcher_platform(
        require_login(allow_legacy_admin=allow_legacy_admin)
    )
    try:
        assert_capability(actor, capability_id)
    except ResearchAccessError as exc:
        raise AuthError(exc.message, status=exc.status, code=exc.code, details=exc.details) from exc
    return actor


def resolve_actor_user_id(
    requested_user_id: str | None = None,
    payload: dict | None = None,
    allow_legacy_admin: bool = False,
    allow_dev_fallback: bool = False,
) -> str:
    """Resolve private-data ownership from the authenticated actor first.

    Participant request fields can no longer choose identity once a signed
    actor exists.  Explicit user_id is only a target selector for authorized
    backend roles.  Anonymous/user-id fallback is development-only legacy
    compatibility and must never become a pilot/production identity source.
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
    return fail(
        exc.code or code_by_status.get(exc.status, "auth_error"),
        str(exc),
        status=exc.status,
        details=exc.details,
    )


def route_actor(*roles: str):
    """Resolve a role-gated route actor and its Flask error response."""

    try:
        return require_role(*roles, allow_legacy_admin=True), None
    except AuthError as exc:
        return None, auth_error_response(exc)
