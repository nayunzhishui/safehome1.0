"""Formal pilot username/password and WeChat auth endpoints."""

import hashlib
import hmac
import json
import re
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from flask import Blueprint, current_app, request
from werkzeug.security import check_password_hash, generate_password_hash

from config import Config
from database import ensure_user, get_connection, new_id, now_iso, row_to_dict, write_audit_log
from routes.auth_utils import (
    PUBLIC_REGISTER_ROLES,
    AuthError,
    auth_error_response,
    generate_auth_token,
    get_current_actor,
    require_login,
    require_role,
)
from routes.utils import fail, ok, require_admin_token
from services.data_claim_service import claim_preview, claim_records, register_claim_candidate
from services.redis_service import hash_component as redis_hash_component, rate_limit as redis_rate_limit
from services.identity_lifecycle_service import (
    BACKEND_ROLES,
    PARTICIPANT_ROLES,
    IdentityLifecycleError,
    confirm_merge,
    create_merge_candidate,
    execute_merge,
    get_merge_workflow,
    identity_status,
    rollback_merge,
    unbind_identity,
    verify_merge,
)
from services.security_control_service import record_security_event

bp = Blueprint("auth", __name__, url_prefix="/api/auth")
CLOUDBASE_ACCESS_TOKEN_PATH = "/.tencentcloudbase/wx/cloudbase_access_token"
_WECHAT_ACCESS_TOKEN_CACHE: dict[str, float | str] = {"appid": "", "token": "", "expires_at": 0.0}
_CLOUDBASE_OPENID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{6,128}$")
_CLOUDBASE_MINIPROGRAM_SOURCES = {"wx_devtools", "wx_client"}
MAX_PASSWORD_FAILURES = 5
PASSWORD_LOCK_MINUTES = 15


class WechatAuthError(ValueError):
    def __init__(self, code: str, message: str, status: int = 400) -> None:
        super().__init__(message)
        self.code = code
        self.status = status


def _public_user(row: dict) -> dict:
    return {
        "id": row["id"],
        "username": row.get("username"),
        "role": row.get("role") or "parent",
        "nickname": row.get("nickname"),
        "anonymous_id": row.get("anonymous_id"),
        "avatar_url": row.get("avatar_url"),
        "status": row.get("status") or "active",
        "must_change_password": bool(row.get("must_change_password")),
        "auth_epoch": int(row.get("auth_epoch") or 0),
    }


def _apply_pending_logout(conn, row: dict, payload: dict) -> tuple[bool, bool]:
    if payload.get("revoke_previous_sessions") is not True:
        return False, False
    pending_user_id = str(payload.get("pending_logout_user_id") or "").strip()
    user_id = str(row["id"])
    if not pending_user_id or pending_user_id != user_id:
        return False, True

    current_epoch = int(row.get("auth_epoch") or 0)
    supplied_epoch = payload.get("pending_logout_auth_epoch")
    try:
        expected_epoch = int(supplied_epoch) if supplied_epoch is not None else current_epoch
    except (TypeError, ValueError):
        expected_epoch = current_epoch
    if current_epoch <= expected_epoch:
        timestamp = now_iso()
        cursor = conn.execute(
            """
            UPDATE users SET auth_epoch = auth_epoch + 1, updated_at = ?
            WHERE id = ? AND auth_epoch = ?
            """,
            (timestamp, user_id, current_epoch),
        )
        if cursor.rowcount == 1:
            write_audit_log(
                conn,
                "auth_pending_logout_resolved",
                user_id,
                "user",
                user_id,
                {"previous_auth_epoch": current_epoch, "token_material_received": False},
            )
    return True, False


def _participant_quick_login_row(conn, row):
    """Resolve only participant identities; never turn a quick login into a backend session."""

    if row is None:
        return None
    item = row_to_dict(row)
    if item.get("role") in BACKEND_ROLES:
        raise IdentityLifecycleError(
            "backend_role_quick_login_forbidden",
            "研究与管理账号只能使用后台账号方式登录。",
            403,
        )
    if item.get("status") == "merged" and item.get("merged_into_user_id"):
        target = conn.execute(
            "SELECT * FROM users WHERE id = ?",
            (item["merged_into_user_id"],),
        ).fetchone()
        if target is None:
            raise IdentityLifecycleError("merged_account_unavailable", "账号关联状态需要人工核对", 409)
        item = row_to_dict(target)
    if item.get("role") not in PARTICIPANT_ROLES:
        raise IdentityLifecycleError(
            "backend_role_quick_login_forbidden",
            "研究与管理账号只能使用后台账号方式登录。",
            403,
        )
    if item.get("status") != "active":
        raise IdentityLifecycleError("account_inactive", "账号暂不可用", 403)
    return item


def _identity_error_response(exc: IdentityLifecycleError):
    return fail(exc.code, str(exc), status=exc.status)


def _trusted_cloudbase_openid() -> str | None:
    """Read the identity header injected by WeChat CloudBase callContainer.

    This path is disabled by default. Deployments behind CloudBase callContainer
    must opt in explicitly after confirming that public traffic cannot bypass
    the trusted gateway.
    """

    openid = str(request.headers.get("X-WX-OPENID") or "").strip()
    source = str(request.headers.get("X-WX-SOURCE") or "").strip()
    request_appid = str(request.headers.get("X-WX-APPID") or "").strip()
    explicit_trust = bool(current_app.config.get("TRUST_CLOUDBASE_IDENTITY_HEADERS", False))

    if not explicit_trust:
        return None
    if not _CLOUDBASE_OPENID_PATTERN.fullmatch(openid):
        return None
    if source not in _CLOUDBASE_MINIPROGRAM_SOURCES:
        return None
    configured_appid = str(current_app.config.get("WECHAT_APPID") or "").strip()
    if configured_appid and (
        not request_appid or not hmac.compare_digest(configured_appid, request_appid)
    ):
        return None
    return openid


def _read_json_response(response) -> dict:
    return json.loads(response.read().decode("utf-8"))


def _log_wechat_transport_failure(operation: str, exc: Exception) -> None:
    """Log only transport metadata; never log URLs, codes, AppSecret or response bodies."""

    upstream_status = exc.code if isinstance(exc, HTTPError) else None
    reason = exc.reason if isinstance(exc, URLError) else None
    current_app.logger.warning(
        "wechat_transport_failure operation=%s kind=%s upstream_status=%s reason_type=%s",
        operation,
        type(exc).__name__,
        upstream_status,
        type(reason).__name__ if reason is not None else None,
    )


def _wechat_transport_error(operation: str, exc: Exception) -> WechatAuthError:
    _log_wechat_transport_failure(operation, exc)
    if isinstance(exc, HTTPError):
        return WechatAuthError(
            "wechat_upstream_http_error",
            "微信服务拒绝了服务器连接，请稍后重试或使用账号密码登录。",
            502,
        )
    if isinstance(exc, json.JSONDecodeError):
        return WechatAuthError(
            "wechat_upstream_invalid_response",
            "微信服务返回了无法识别的结果，请稍后重试或使用账号密码登录。",
            502,
        )
    return WechatAuthError(
        "wechat_network_unavailable",
        "服务器暂时无法连接微信服务，请稍后重试或使用账号密码登录。",
        502,
    )


def _wechat_session_from_code(code: str) -> dict:
    appid = str(current_app.config.get("WECHAT_APPID") or "").strip()
    secret = str(current_app.config.get("WECHAT_SECRET") or "").strip()
    if appid and secret:
        query = urlencode(
            {
                "appid": appid,
                "secret": secret,
                "js_code": code,
                "grant_type": "authorization_code",
            }
        )
        try:
            api_request = Request(
                f"https://api.weixin.qq.com/sns/jscode2session?{query}",
                headers={"Accept": "application/json", "User-Agent": "SafeHome-WeChat-Auth/1.0"},
            )
            with urlopen(api_request, timeout=8) as response:
                payload = _read_json_response(response)
        except (HTTPError, URLError, OSError, json.JSONDecodeError) as exc:
            raise _wechat_transport_error("jscode2session", exc) from exc
        if payload.get("errcode"):
            raise WechatAuthError("wechat_login_failed", "微信登录凭证已失效，请重新尝试。", 400)
        if not payload.get("openid"):
            raise WechatAuthError("wechat_login_failed", "微信登录暂未完成，请重新尝试。", 400)
        return {**payload, "identity_source": "jscode2session"}
    if Config.APP_ENV == "production":
        raise WechatAuthError(
            "wechat_login_config_missing",
            "微信登录暂不可用，请尝试手机号快捷登录或账号密码登录。",
            503,
        )
    digest = hashlib.sha256(code.encode("utf-8")).hexdigest()[:24]
    return {
        "openid": f"dev_openid_{digest}",
        "session_key": None,
        "dev_fallback": True,
        "identity_source": "development_fallback",
    }


def _cloudbase_access_token() -> str | None:
    token_path = Path(current_app.config.get("CLOUDBASE_ACCESS_TOKEN_PATH", CLOUDBASE_ACCESS_TOKEN_PATH))
    try:
        token = token_path.read_text(encoding="utf-8").strip()
    except OSError:
        return None
    return token or None


def _standard_wechat_access_token() -> str | None:
    appid = str(current_app.config.get("WECHAT_APPID") or "").strip()
    secret = str(current_app.config.get("WECHAT_SECRET") or "").strip()
    if not appid or not secret:
        return None

    now = time.time()
    if (
        _WECHAT_ACCESS_TOKEN_CACHE.get("appid") == appid
        and _WECHAT_ACCESS_TOKEN_CACHE.get("token")
        and float(_WECHAT_ACCESS_TOKEN_CACHE.get("expires_at") or 0) > now + 60
    ):
        return str(_WECHAT_ACCESS_TOKEN_CACHE["token"])

    query = urlencode({"grant_type": "client_credential", "appid": appid, "secret": secret})
    try:
        api_request = Request(
            f"https://api.weixin.qq.com/cgi-bin/token?{query}",
            headers={"Accept": "application/json", "User-Agent": "SafeHome-WeChat-Auth/1.0"},
        )
        with urlopen(api_request, timeout=8) as response:
            payload = _read_json_response(response)
    except (HTTPError, URLError, OSError, json.JSONDecodeError) as exc:
        raise _wechat_transport_error("access_token", exc) from exc
    token = str(payload.get("access_token") or "").strip()
    if not token:
        raise WechatAuthError("wechat_phone_config_invalid", "手机号快捷登录暂不可用，请使用其他登录方式。", 503)
    expires_in = max(int(payload.get("expires_in") or 7200), 300)
    _WECHAT_ACCESS_TOKEN_CACHE.update({"appid": appid, "token": token, "expires_at": now + expires_in})
    return token


def _wechat_api_credential() -> tuple[str, str]:
    cloudbase_token = _cloudbase_access_token()
    if cloudbase_token:
        return "cloudbase_access_token", cloudbase_token
    standard_token = _standard_wechat_access_token()
    if standard_token:
        return "access_token", standard_token
    raise WechatAuthError(
        "wechat_phone_config_missing",
        "手机号快捷登录尚未开通，请使用微信一键登录或账号密码登录。",
        503,
    )


def _normalize_phone_number(value: str) -> str:
    normalized = "".join(char for char in str(value or "") if char.isdigit())
    if normalized.startswith("86") and len(normalized) == 13:
        normalized = normalized[2:]
    if len(normalized) < 7 or len(normalized) > 15:
        raise WechatAuthError("wechat_phone_invalid", "微信没有返回有效手机号，请重新授权。", 400)
    return normalized


def _phone_hash(phone_number: str) -> str:
    key = str(current_app.config["SECRET_KEY"]).encode("utf-8")
    message = f"safehome-phone-v1:{phone_number}".encode("utf-8")
    return hmac.new(key, message, hashlib.sha256).hexdigest()


def _mask_phone(phone_number: str) -> str:
    if len(phone_number) < 7:
        return "****"
    return f"{phone_number[:3]}****{phone_number[-4:]}"


def _wechat_phone_from_code(code: str) -> dict:
    credential_name, credential = _wechat_api_credential()
    query = urlencode({credential_name: credential})
    request_body = json.dumps({"code": code}, ensure_ascii=False).encode("utf-8")
    api_request = Request(
        f"https://api.weixin.qq.com/wxa/business/getuserphonenumber?{query}",
        data=request_body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(api_request, timeout=8) as response:
            payload = _read_json_response(response)
    except (HTTPError, URLError, OSError, json.JSONDecodeError) as exc:
        raise _wechat_transport_error("getuserphonenumber", exc) from exc
    if payload.get("errcode") not in {None, 0}:
        raise WechatAuthError("wechat_phone_exchange_failed", "手机号授权已失效，请重新授权后再试。", 400)
    phone_info = payload.get("phone_info") or payload.get("phoneInfo") or {}
    phone_number = _normalize_phone_number(
        phone_info.get("purePhoneNumber") or phone_info.get("phoneNumber") or phone_info.get("pure_phone_number")
    )
    return {
        "phone_number": phone_number,
        "pure_phone_number": phone_number,
        "country_code": str(phone_info.get("countryCode") or phone_info.get("country_code") or ""),
    }


def _wechat_error_response(exc: WechatAuthError):
    current_app.logger.warning("wechat_auth_failed code=%s status=%s", exc.code, exc.status)
    return fail(exc.code, str(exc), status=exc.status)


def _parse_utc_timestamp(value: str) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(value)
    except (TypeError, ValueError):
        return None
    if parsed.tzinfo is None:
        return None
    return parsed.astimezone(timezone.utc)


@bp.get("/capabilities")
def auth_capabilities():
    """Expose login readiness without returning credentials or identity values."""
    standard_wechat_configured = bool(
        str(current_app.config.get("WECHAT_APPID") or "").strip()
        and str(current_app.config.get("WECHAT_SECRET") or "").strip()
    )
    cloudbase_identity_configured = bool(
        current_app.config.get("TRUST_CLOUDBASE_IDENTITY_HEADERS", False)
    )
    cloudbase_request_identity = _trusted_cloudbase_openid() is not None
    cloudbase_phone_token_available = _cloudbase_access_token() is not None
    return ok(
        {
            "account_password": {"available": True},
            "wechat_login": {
                "available": bool(cloudbase_request_identity or cloudbase_identity_configured or standard_wechat_configured),
                "mode": (
                    "cloudbase_identity"
                    if cloudbase_request_identity or cloudbase_identity_configured
                    else "jscode2session"
                    if standard_wechat_configured
                    else "not_configured"
                ),
            },
            "phone_login": {
                "available": bool(cloudbase_phone_token_available or standard_wechat_configured),
                "mode": (
                    "cloudbase_access_token"
                    if cloudbase_phone_token_available
                    else "wechat_access_token"
                    if standard_wechat_configured
                    else "not_configured"
                ),
            },
            "privacy_notice": "能力检查不返回 openid、手机号、令牌或密钥。",
        }
    )


@bp.post("/register")
def register():
    payload = request.get_json(silent=True) or {}
    username = str(payload.get("username") or "").strip()
    password = str(payload.get("password") or "")
    role = str(payload.get("role") or "parent").strip()
    nickname = str(payload.get("nickname") or "").strip() or None
    anonymous_id = str(payload.get("anonymous_id") or "").strip() or None
    phone_or_email = str(payload.get("phone_or_email") or "").strip() or None

    if len(username) < 3:
        return fail("validation_error", "用户名至少需要 3 个字符", status=400)
    if len(password) < 8:
        return fail("validation_error", "密码至少需要 8 个字符", status=400)
    if role not in PUBLIC_REGISTER_ROLES:
        return fail("validation_error", "公开注册仅支持家长或学生账号", status=400)

    timestamp = now_iso()
    user_id = new_id("user")
    with get_connection() as conn:
        existing = conn.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
        if existing:
            return fail("username_exists", "该用户名已被使用", status=409)
        ensure_user(conn, user_id, nickname)
        conn.execute(
            """
            UPDATE users
            SET username = ?, phone_or_email = ?, password_hash = ?,
                anonymous_id = ?, role = ?, source = 'web_auth',
                status = 'active', updated_at = ?
            WHERE id = ?
            """,
            (username, phone_or_email, generate_password_hash(password), anonymous_id, role, timestamp, user_id),
        )
        register_claim_candidate(conn, user_id, anonymous_id)
        conn.commit()
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()

    user = _public_user(row_to_dict(row))
    return ok({"token": generate_auth_token(user), "user": user}, status=201)


@bp.post("/login")
def login():
    payload = request.get_json(silent=True) or {}
    username = str(payload.get("username") or "").strip()
    password = str(payload.get("password") or "")
    anonymous_id = str(payload.get("anonymous_id") or "").strip() or None
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        now = datetime.now(timezone.utc)
        if row is not None and row["locked_until"]:
            locked_until = _parse_utc_timestamp(str(row["locked_until"]))
            if locked_until is not None and locked_until > now:
                return fail("account_locked", "登录失败次数过多，请稍后重试或联系管理员解锁", status=423)
            conn.execute(
                "UPDATE users SET failed_login_count = 0, last_failed_login_at = NULL, locked_until = NULL WHERE id = ?",
                (row["id"],),
            )
            conn.commit()
            row = conn.execute("SELECT * FROM users WHERE id = ?", (row["id"],)).fetchone()
        if row is None or not row["password_hash"] or not check_password_hash(row["password_hash"], password):
            locked = False
            failure_count = 1
            if row is not None:
                failure_count = int(row["failed_login_count"] or 0) + 1
                locked = failure_count >= MAX_PASSWORD_FAILURES
                lock_until = (now + timedelta(minutes=PASSWORD_LOCK_MINUTES)).isoformat() if locked else None
                conn.execute(
                    """
                    UPDATE users
                    SET failed_login_count = ?, last_failed_login_at = ?, locked_until = ?, updated_at = ?
                    WHERE id = ?
                    """,
                    (failure_count, now.isoformat(), lock_until, now.isoformat(), row["id"]),
                )
                conn.commit()
            record_security_event(
                "account_locked" if locked else "login_failed",
                "high" if locked else "medium",
                target_type="credential_hash",
                target_id=hashlib.sha256(username.encode("utf-8")).hexdigest()[:16] if username else None,
                metadata={"source": "password", "failure_count": failure_count},
            )
            if locked:
                return fail("account_locked", "登录失败次数过多，请稍后重试或联系管理员解锁", status=423)
            return fail("invalid_credentials", "用户名或密码不正确", status=401)
        if row["status"] and row["status"] != "active":
            record_security_event(
                "inactive_account_login_blocked",
                "high",
                target_type="user",
                target_id=row["id"],
                metadata={"source": "password", "status": row["status"]},
            )
            return fail("account_inactive", "账号暂不可用", status=403)
        if bool(row["must_change_password"]) and row["credential_expires_at"]:
            expires_at = _parse_utc_timestamp(str(row["credential_expires_at"]))
            if expires_at is None or expires_at <= datetime.now(timezone.utc):
                record_security_event(
                    "temporary_credential_expired",
                    "medium",
                    target_type="user",
                    target_id=row["id"],
                    metadata={"source": "password"},
                )
                return fail("temporary_credential_expired", "一次性密码已过期，请联系管理员重新生成", status=403)
        timestamp = now_iso()
        conn.execute(
            """
            UPDATE users
            SET anonymous_id = COALESCE(?, anonymous_id), last_login_at = ?, updated_at = ?,
                failed_login_count = 0, last_failed_login_at = NULL, locked_until = NULL
            WHERE id = ?
            """,
            (anonymous_id, timestamp, timestamp, row["id"]),
        )
        register_claim_candidate(conn, row["id"], anonymous_id)
        pending_logout_resolved, pending_logout_user_mismatch = _apply_pending_logout(
            conn, row_to_dict(row), payload
        )
        conn.commit()
        row = conn.execute("SELECT * FROM users WHERE id = ?", (row["id"],)).fetchone()

    user = _public_user(row_to_dict(row))
    return ok(
        {
            "token": generate_auth_token(user),
            "user": user,
            "pending_logout_resolved": pending_logout_resolved,
            "pending_logout_user_mismatch": pending_logout_user_mismatch,
        }
    )


@bp.post("/wechat-login")
def wechat_login():
    payload = request.get_json(silent=True) or {}
    code = str(payload.get("code") or "").strip()
    nickname = str(payload.get("nickname") or payload.get("nickName") or "").strip() or None
    avatar_url = str(payload.get("avatar_url") or payload.get("avatarUrl") or "").strip() or None
    anonymous_id = str(payload.get("anonymous_id") or "").strip() or None
    cloudbase_openid = _trusted_cloudbase_openid()
    if cloudbase_openid:
        session = {
            "openid": cloudbase_openid,
            "dev_fallback": False,
            "identity_source": "cloudbase_header",
        }
    else:
        if not code:
            return fail("validation_error", "缺少微信登录凭证", status=400)
        try:
            session = _wechat_session_from_code(code)
        except WechatAuthError as exc:
            return _wechat_error_response(exc)

    openid = session["openid"]
    timestamp = now_iso()
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM users WHERE wechat_openid = ?", (openid,)).fetchone()
        if row is None:
            user_id = new_id("user")
            ensure_user(conn, user_id, nickname)
            conn.execute(
                """
                UPDATE users
                SET wechat_openid = ?, avatar_url = ?, anonymous_id = ?,
                    role = 'parent', source = 'wechat', status = 'active',
                    last_login_at = ?, updated_at = ?
                WHERE id = ?
                """,
                (openid, avatar_url, anonymous_id, timestamp, timestamp, user_id),
            )
        else:
            try:
                participant = _participant_quick_login_row(conn, row)
            except IdentityLifecycleError as exc:
                return _identity_error_response(exc)
            user_id = participant["id"]
            conn.execute(
                """
                UPDATE users
                SET nickname = COALESCE(?, nickname),
                    avatar_url = COALESCE(?, avatar_url),
                    anonymous_id = COALESCE(?, anonymous_id),
                    last_login_at = ?, updated_at = ?
                WHERE id = ?
                """,
                (nickname, avatar_url, anonymous_id, timestamp, timestamp, user_id),
            )
        register_claim_candidate(conn, user_id, anonymous_id)
        current = row_to_dict(
            conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        )
        pending_logout_resolved, pending_logout_user_mismatch = _apply_pending_logout(
            conn, current, payload
        )
        conn.commit()
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()

    user = _public_user(row_to_dict(row))
    return ok(
        {
            "token": generate_auth_token(user),
            "user": user,
            "dev_fallback": bool(session.get("dev_fallback")),
            "identity_source": session.get("identity_source") or "jscode2session",
            "pending_logout_resolved": pending_logout_resolved,
            "pending_logout_user_mismatch": pending_logout_user_mismatch,
        }
    )


@bp.post("/phone-login")
def phone_login():
    payload = request.get_json(silent=True) or {}
    code = str(payload.get("code") or "").strip()
    anonymous_id = str(payload.get("anonymous_id") or "").strip() or None
    if not code:
        return fail("validation_error", "缺少手机号授权凭证", status=400)

    try:
        phone_info = _wechat_phone_from_code(code)
    except WechatAuthError as exc:
        return _wechat_error_response(exc)

    phone_number = _normalize_phone_number(phone_info.get("pure_phone_number") or phone_info.get("phone_number"))
    phone_hash = _phone_hash(phone_number)
    cloudbase_openid = _trusted_cloudbase_openid()
    timestamp = now_iso()
    with get_connection() as conn:
        phone_row = conn.execute("SELECT * FROM users WHERE phone_hash = ?", (phone_hash,)).fetchone()
        openid_row = (
            conn.execute("SELECT * FROM users WHERE wechat_openid = ?", (cloudbase_openid,)).fetchone()
            if cloudbase_openid
            else None
        )
        try:
            phone_participant = _participant_quick_login_row(conn, phone_row)
            openid_participant = _participant_quick_login_row(conn, openid_row)
        except IdentityLifecycleError as exc:
            return _identity_error_response(exc)
        if (
            phone_participant is not None
            and openid_participant is not None
            and phone_participant["id"] != openid_participant["id"]
        ):
            return fail("phone_account_conflict", "该手机号已关联其他账号，请使用原账号登录。", status=409)

        row = phone_participant or openid_participant
        if row is None:
            user_id = new_id("user")
            ensure_user(conn, user_id, "微信用户")
        else:
            user_id = row["id"]

        conn.execute(
            """
            UPDATE users
            SET phone_hash = ?, phone_verified_at = ?, phone_source = 'wechat_phone',
                wechat_openid = COALESCE(?, wechat_openid),
                anonymous_id = COALESCE(?, anonymous_id),
                role = COALESCE(role, 'parent'),
                source = CASE WHEN source IS NULL OR source = 'mvp' THEN 'wechat_phone' ELSE source END,
                status = 'active', last_login_at = ?, updated_at = ?
            WHERE id = ?
            """,
            (phone_hash, timestamp, cloudbase_openid, anonymous_id, timestamp, timestamp, user_id),
        )
        register_claim_candidate(conn, user_id, anonymous_id)
        current = row_to_dict(
            conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        )
        pending_logout_resolved, pending_logout_user_mismatch = _apply_pending_logout(
            conn, current, payload
        )
        conn.commit()
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()

    user = _public_user(row_to_dict(row))
    return ok(
        {
            "token": generate_auth_token(user),
            "user": user,
            "phone_bound": True,
            "phone_masked": _mask_phone(phone_number),
            "pending_logout_resolved": pending_logout_resolved,
            "pending_logout_user_mismatch": pending_logout_user_mismatch,
        }
    )


@bp.post("/bind-phone")
def bind_phone():
    """Bind a WeChat-authorized phone number without storing the raw number."""

    try:
        actor = require_login(allow_legacy_admin=False)
    except AuthError as exc:
        return auth_error_response(exc)
    if actor.get("role") not in PARTICIPANT_ROLES:
        return fail(
            "backend_role_quick_login_forbidden",
            "研究与管理账号不能绑定参与者快捷登录身份。",
            status=403,
        )

    payload = request.get_json(silent=True) or {}
    code = str(payload.get("code") or "").strip()
    if not code:
        return fail("validation_error", "缺少手机号授权 code", status=400)

    try:
        phone_info = _wechat_phone_from_code(code)
    except WechatAuthError as exc:
        return _wechat_error_response(exc)

    phone_number = _normalize_phone_number(phone_info.get("pure_phone_number") or phone_info.get("phone_number"))
    phone_hash = _phone_hash(phone_number)
    timestamp = now_iso()
    with get_connection() as conn:
        existing = conn.execute("SELECT id FROM users WHERE phone_hash = ?", (phone_hash,)).fetchone()
        if existing is not None and existing["id"] != actor["id"]:
            return fail("phone_account_conflict", "该手机号已关联其他账号，请使用原账号登录。", status=409)
        conn.execute(
            """
            UPDATE users
            SET phone_hash = ?, phone_verified_at = ?, phone_source = 'wechat_phone', updated_at = ?
            WHERE id = ?
            """,
            (phone_hash, timestamp, timestamp, actor["id"]),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM users WHERE id = ?", (actor["id"],)).fetchone()

    user = _public_user(row_to_dict(row))
    return ok(
        {
            "token": generate_auth_token(user),
            "user": user,
            "phone_bound": True,
            "phone_masked": _mask_phone(phone_number),
        }
    )


@bp.post("/admin-create-account")
def admin_create_account():
    """管理员用 X-Admin-Token 创建任意角色账号（研究者/督导/管理员等）。"""
    try:
        require_admin_token()
    except ValueError as exc:
        return fail("unauthorized", str(exc), status=401)

    payload = request.get_json(silent=True) or {}
    username = str(payload.get("username") or "").strip()
    password = str(payload.get("password") or "")
    role = str(payload.get("role") or "researcher").strip()
    nickname = str(payload.get("nickname") or "").strip() or None
    anonymous_id = str(payload.get("anonymous_id") or "").strip() or None
    rotate_existing = payload.get("rotate_existing") is True
    temporary_credential = payload.get("temporary_credential") is True
    credential_receipt_id = str(payload.get("credential_receipt_id") or "").strip() or None
    credential_expires_at = str(payload.get("credential_expires_at") or "").strip() or None
    target_environment = str(payload.get("target_environment") or "").strip()
    target_binding = payload.get("target_binding")

    if len(username) < 3:
        return fail("validation_error", "用户名至少需要 3 个字符", status=400)
    if len(password) < 8:
        return fail("validation_error", "密码至少需要 8 个字符", status=400)
    if role not in {"admin", "researcher", "supervisor", "parent", "student"}:
        return fail("validation_error", "不支持该角色", status=400)
    if temporary_credential and (not credential_receipt_id or not credential_expires_at):
        return fail("validation_error", "一次性凭据需要receipt ID和过期时间", status=400)
    if temporary_credential:
        app_environment = str(current_app.config.get("APP_ENV") or "development").lower()
        if not target_environment:
            if app_environment == "production":
                return fail("environment_binding_required", "云端一次性凭据需要目标环境绑定", status=400)
            target_environment = "local"
        if target_environment not in {"local", "test_cloud", "production"}:
            return fail("validation_error", "一次性凭据目标环境无效", status=400)
        if target_environment != "local":
            expected_target_environment = str(
                current_app.config.get("DEPLOYMENT_TARGET_ENVIRONMENT") or ""
            )
            expected_binding = {
                "cloud_env_id": str(current_app.config.get("DEPLOYMENT_CLOUDBASE_ENV_ID") or ""),
                "container_service": str(current_app.config.get("DEPLOYMENT_CLOUDBASE_SERVICE") or ""),
                "base_url": str(current_app.config.get("DEPLOYMENT_PUBLIC_BASE_URL") or "").rstrip("/"),
            }
            if not expected_target_environment or not all(expected_binding.values()):
                return fail(
                    "environment_binding_unconfigured",
                    "服务端未配置云环境身份，禁止应用云端一次性凭据",
                    status=503,
                )
            if target_environment != expected_target_environment:
                return fail(
                    "environment_binding_mismatch",
                    "一次性凭据环境类别与当前部署不一致",
                    status=409,
                )
            normalized_binding = dict(target_binding) if isinstance(target_binding, dict) else {}
            normalized_binding["base_url"] = str(normalized_binding.get("base_url") or "").rstrip("/")
            if normalized_binding != expected_binding:
                return fail(
                    "environment_binding_mismatch",
                    "一次性凭据目标与当前云环境不一致",
                    status=409,
                )
        password_error = _validate_new_password(password)
        if password_error:
            return fail("validation_error", password_error, status=400)
        expires_at = _parse_utc_timestamp(credential_expires_at)
        now = datetime.now(timezone.utc)
        if expires_at is None:
            return fail("validation_error", "一次性凭据过期时间必须包含有效时区", status=400)
        if expires_at <= now:
            return fail("temporary_credential_expired", "一次性凭据已过期，请重新生成", status=400)
        if expires_at > now + timedelta(hours=24, minutes=5):
            return fail("validation_error", "一次性凭据有效期不能超过24小时", status=400)

    timestamp = now_iso()
    user_id = new_id("user")
    with get_connection() as conn:
        receipt_owner = None
        if credential_receipt_id:
            receipt_owner = conn.execute(
                "SELECT username FROM users WHERE credential_receipt_id = ?",
                (credential_receipt_id,),
            ).fetchone()
        if receipt_owner is not None and str(receipt_owner["username"] or "") != username:
            return fail("credential_receipt_reused", "该一次性凭据回执已被使用", status=409)
        existing = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        if existing:
            if temporary_credential and credential_receipt_id and hmac.compare_digest(
                str(existing["credential_receipt_id"] or ""), credential_receipt_id
            ):
                existing_user = _public_user(row_to_dict(existing))
                return ok(
                    {
                        "user": existing_user,
                        "created": False,
                        "credentials_rotated": False,
                        "already_applied": True,
                    }
                )
            if not rotate_existing:
                return fail("username_exists", "该用户名已被使用", status=409)
            if str(existing["role"] or "") != role:
                return fail("role_change_forbidden", "凭据轮换不能同时修改账号角色", status=409)
            user_id = existing["id"]
        else:
            if rotate_existing:
                return fail("account_not_found", "待轮换账号不存在", status=404)
            ensure_user(conn, user_id, nickname)
        conn.execute(
            """
            UPDATE users
            SET username = ?, phone_or_email = ?, password_hash = ?,
                anonymous_id = ?, role = ?, source = 'admin_created',
                status = 'active', status_reason = NULL,
                auth_epoch = auth_epoch + ?,
                must_change_password = ?, credential_receipt_id = ?, credential_expires_at = ?,
                failed_login_count = 0, last_failed_login_at = NULL, locked_until = NULL,
                updated_at = ?
            WHERE id = ?
            """,
            (
                username,
                None,
                generate_password_hash(password),
                anonymous_id,
                role,
                1 if existing else 0,
                1 if temporary_credential else 0,
                credential_receipt_id,
                credential_expires_at,
                timestamp,
                user_id,
            ),
        )
        write_audit_log(
            conn,
            "account_credentials_rotated" if existing else "account_created",
            "admin-token",
            "user",
            user_id,
            {"role": role, "existing": bool(existing)},
        )
        conn.commit()
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()

    user = _public_user(row_to_dict(row))
    return ok({"user": user, "created": existing is None, "credentials_rotated": existing is not None}, status=201 if existing is None else 200)


def _validate_new_password(password: str) -> str | None:
    if len(password) < 12:
        return "新密码至少需要12个字符"
    categories = sum(
        bool(pattern.search(password))
        for pattern in (re.compile(r"[a-z]"), re.compile(r"[A-Z]"), re.compile(r"\d"), re.compile(r"[^A-Za-z0-9]"))
    )
    if categories < 3:
        return "新密码需要包含大小写字母、数字或符号中的至少三类"
    return None


@bp.post("/change-password")
def change_password():
    try:
        actor = require_login(allow_legacy_admin=False)
    except AuthError as exc:
        return auth_error_response(exc)

    payload = request.get_json(silent=True) or {}
    current_password = str(payload.get("current_password") or "")
    new_password = str(payload.get("new_password") or "")
    validation_error = _validate_new_password(new_password)
    if validation_error:
        return fail("validation_error", validation_error, status=400)
    if hmac.compare_digest(current_password, new_password):
        return fail("password_reuse_forbidden", "新密码不能与当前密码相同", status=409)

    timestamp = now_iso()
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (actor["id"],)).fetchone()
        if row is None or not row["password_hash"] or not check_password_hash(row["password_hash"], current_password):
            record_security_event(
                "password_change_failed",
                "medium",
                actor_id=actor["id"],
                target_type="user",
                target_id=actor["id"],
                metadata={"source": "password_change"},
            )
            return fail("invalid_credentials", "当前密码不正确", status=401)
        conn.execute(
            """
            UPDATE users
            SET password_hash = ?, must_change_password = 0,
                credential_receipt_id = NULL, credential_expires_at = NULL,
                password_changed_at = ?, failed_login_count = 0,
                last_failed_login_at = NULL, locked_until = NULL,
                auth_epoch = auth_epoch + 1, updated_at = ?
            WHERE id = ?
            """,
            (generate_password_hash(new_password), timestamp, timestamp, actor["id"]),
        )
        write_audit_log(
            conn,
            "account_password_changed",
            actor["id"],
            "user",
            actor["id"],
            {"sessions_revoked": True, "temporary_credential_cleared": True},
        )
        conn.commit()
        updated = row_to_dict(conn.execute("SELECT * FROM users WHERE id = ?", (actor["id"],)).fetchone())

    user = _public_user(updated)
    return ok({"token": generate_auth_token(updated), "user": user, "sessions_revoked": True})


@bp.post("/admin-accounts/<username>/unlock")
def admin_unlock_account(username: str):
    try:
        require_admin_token()
    except ValueError as exc:
        return fail("unauthorized", str(exc), status=401)
    normalized = str(username or "").strip()
    timestamp = now_iso()
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM users WHERE username = ?", (normalized,)).fetchone()
        if row is None:
            return fail("not_found", "没有找到该账号", status=404)
        conn.execute(
            """
            UPDATE users
            SET failed_login_count = 0, last_failed_login_at = NULL, locked_until = NULL, updated_at = ?
            WHERE id = ?
            """,
            (timestamp, row["id"]),
        )
        write_audit_log(
            conn,
            "account_login_unlocked",
            "admin-token",
            "user",
            row["id"],
            {"previous_failure_count": int(row["failed_login_count"] or 0)},
        )
        conn.commit()
    return ok({"username": normalized, "failed_login_count": 0, "locked": False})


def _admin_account_status(row: dict) -> dict:
    locked_until = _parse_utc_timestamp(str(row.get("locked_until") or ""))
    return {
        "username": row.get("username"),
        "role": row.get("role"),
        "status": row.get("status"),
        "last_login_at": row.get("last_login_at"),
        "password_configured": bool(row.get("password_hash")),
        "must_change_password": bool(row.get("must_change_password")),
        "credential_generation": int(row.get("auth_epoch") or 0),
        "temporary_credential_expires_at": row.get("credential_expires_at"),
        "failed_login_count": int(row.get("failed_login_count") or 0),
        "locked": bool(locked_until and locked_until > datetime.now(timezone.utc)),
        "locked_until": row.get("locked_until"),
    }


@bp.get("/admin-accounts/<username>")
def admin_verify_account(username: str):
    try:
        require_admin_token()
    except ValueError as exc:
        return fail("unauthorized", str(exc), status=401)
    normalized = str(username or "").strip()
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM users WHERE username = ?", (normalized,)).fetchone()
    if row is None:
        return fail("not_found", "没有找到该账号", status=404)
    return ok(_admin_account_status(row_to_dict(row)))


@bp.post("/admin-accounts/<username>/revoke")
def admin_revoke_account(username: str):
    try:
        require_admin_token()
    except ValueError as exc:
        return fail("unauthorized", str(exc), status=401)
    normalized = str(username or "").strip()
    timestamp = now_iso()
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM users WHERE username = ?", (normalized,)).fetchone()
        if row is None:
            return fail("not_found", "没有找到该账号", status=404)
        already_revoked = row["status"] == "disabled" and row["status_reason"] == "credential_revoked"
        if not already_revoked:
            conn.execute(
                """
                UPDATE users
                SET status = 'disabled', status_reason = 'credential_revoked',
                    must_change_password = 0, credential_receipt_id = NULL,
                    credential_expires_at = NULL, auth_epoch = auth_epoch + 1, updated_at = ?
                WHERE id = ?
                """,
                (timestamp, row["id"]),
            )
            write_audit_log(
                conn,
                "account_credentials_revoked",
                "admin-token",
                "user",
                row["id"],
                {"tokens_revoked": True},
            )
            conn.commit()
        updated = row_to_dict(conn.execute("SELECT * FROM users WHERE id = ?", (row["id"],)).fetchone())
    return ok({**_admin_account_status(updated), "tokens_revoked": True, "already_revoked": already_revoked})


@bp.post("/logout")
def logout():
    try:
        actor = get_current_actor(allow_legacy_admin=False)
    except AuthError:
        return ok(
            {
                "message": "本地登录状态可以清除；服务端令牌已失效或无法再次撤销。",
                "tokens_revoked": False,
                "already_inactive": True,
            }
        )
    if actor is None:
        return ok(
            {
                "message": "本地登录状态可以清除；当前请求没有可撤销的服务端令牌。",
                "tokens_revoked": False,
                "already_inactive": True,
            }
        )
    timestamp = now_iso()
    with get_connection() as conn:
        expected_epoch = int(actor.get("user", {}).get("auth_epoch") or 0)
        cursor = conn.execute(
            """
            UPDATE users SET auth_epoch = auth_epoch + 1, updated_at = ?
            WHERE id = ? AND auth_epoch = ?
            """,
            (timestamp, actor["id"], expected_epoch),
        )
        tokens_revoked = cursor.rowcount == 1
        if tokens_revoked:
            write_audit_log(
                conn,
                "auth_sessions_revoked",
                actor["id"],
                "user",
                actor["id"],
                {"scope": "all_tokens", "previous_auth_epoch": expected_epoch},
            )
        conn.commit()
    return ok(
        {
            "message": "已安全退出，当前账号的既有登录令牌已失效。",
            "tokens_revoked": tokens_revoked,
            "already_inactive": not tokens_revoked,
        }
    )


@bp.get("/me")
def me():
    try:
        actor = require_login(allow_legacy_admin=False)
    except AuthError as exc:
        return auth_error_response(exc)
    return ok({"user": _public_user(actor["user"])})


@bp.get("/identity-status")
def get_identity_status():
    try:
        actor = require_login(allow_legacy_admin=False)
    except AuthError as exc:
        return auth_error_response(exc)
    with get_connection() as conn:
        try:
            result = identity_status(conn, actor["id"])
        except IdentityLifecycleError as exc:
            return _identity_error_response(exc)
    return ok(result)


@bp.post("/identity-unbind")
def identity_unbind():
    try:
        actor = require_login(allow_legacy_admin=False)
    except AuthError as exc:
        return auth_error_response(exc)
    if actor.get("role") not in PARTICIPANT_ROLES:
        return fail("forbidden", "研究与管理账号不能从参与者端撤销登录绑定", status=403)
    payload = request.get_json(silent=True) or {}
    if payload.get("confirm") is not True:
        return fail("validation_error", "需要明确确认后才能撤销登录绑定", status=400)
    try:
        expected_auth_epoch = int(payload.get("expected_auth_epoch"))
    except (TypeError, ValueError):
        return fail("validation_error", "缺少有效的账号状态版本", status=400)
    try:
        with get_connection() as conn:
            result = unbind_identity(
                conn,
                actor["id"],
                str(payload.get("identity_type") or "").strip(),
                expected_auth_epoch,
            )
            conn.commit()
    except IdentityLifecycleError as exc:
        return _identity_error_response(exc)
    return ok(result)


@bp.post("/admin-account-merges")
def admin_create_account_merge():
    try:
        actor = require_role("admin")
    except AuthError as exc:
        return auth_error_response(exc)
    payload = request.get_json(silent=True) or {}
    idempotency_key = str(request.headers.get("Idempotency-Key") or "").strip()
    if not idempotency_key:
        return fail("idempotency_key_required", "创建账号合并候选需要幂等键", status=400)
    try:
        with get_connection() as conn:
            result, created = create_merge_candidate(
                conn,
                source_user_id=str(payload.get("source_user_id") or "").strip(),
                target_user_id=str(payload.get("target_user_id") or "").strip(),
                reason_code=str(payload.get("reason_code") or "identity_conflict").strip(),
                requested_by=actor["id"],
                idempotency_key=idempotency_key,
            )
            conn.commit()
    except IdentityLifecycleError as exc:
        return _identity_error_response(exc)
    return ok(result, status=201 if created else 200)


@bp.get("/admin-account-merges/<workflow_id>")
def admin_get_account_merge(workflow_id: str):
    try:
        require_role("admin")
        with get_connection() as conn:
            result = get_merge_workflow(conn, workflow_id)
    except AuthError as exc:
        return auth_error_response(exc)
    except IdentityLifecycleError as exc:
        return _identity_error_response(exc)
    return ok(result)


def _expected_merge_version(payload: dict) -> int:
    try:
        return int(payload.get("expected_version"))
    except (TypeError, ValueError) as exc:
        raise IdentityLifecycleError("validation_error", "缺少有效的合并流程版本", 400) from exc


@bp.post("/admin-account-merges/<workflow_id>/confirm")
def admin_confirm_account_merge(workflow_id: str):
    payload = request.get_json(silent=True) or {}
    if payload.get("confirm") is not True:
        return fail("validation_error", "需要人工明确确认后才能继续", status=400)
    try:
        actor = require_role("admin")
        with get_connection() as conn:
            result = confirm_merge(conn, workflow_id, actor["id"], _expected_merge_version(payload))
            conn.commit()
    except AuthError as exc:
        return auth_error_response(exc)
    except IdentityLifecycleError as exc:
        return _identity_error_response(exc)
    return ok(result)


@bp.post("/admin-account-merges/<workflow_id>/execute")
def admin_execute_account_merge(workflow_id: str):
    payload = request.get_json(silent=True) or {}
    idempotency_key = str(request.headers.get("Idempotency-Key") or f"execute:{workflow_id}").strip()
    try:
        actor = require_role("admin")
        with get_connection() as conn:
            result = execute_merge(
                conn,
                workflow_id,
                actor["id"],
                _expected_merge_version(payload),
                idempotency_key,
            )
            conn.commit()
    except AuthError as exc:
        return auth_error_response(exc)
    except IdentityLifecycleError as exc:
        return _identity_error_response(exc)
    except Exception:
        current_app.logger.exception("identity_merge_execute_failed workflow_id=%s", workflow_id)
        return fail("merge_execution_failed", "账号合并未完成，事务已回滚，可刷新后重试", status=409)
    return ok(result)


@bp.post("/admin-account-merges/<workflow_id>/verify")
def admin_verify_account_merge(workflow_id: str):
    payload = request.get_json(silent=True) or {}
    try:
        actor = require_role("admin")
        with get_connection() as conn:
            result = verify_merge(conn, workflow_id, actor["id"], _expected_merge_version(payload))
            conn.commit()
    except AuthError as exc:
        return auth_error_response(exc)
    except IdentityLifecycleError as exc:
        return _identity_error_response(exc)
    return ok(result)


@bp.post("/admin-account-merges/<workflow_id>/rollback")
def admin_rollback_account_merge(workflow_id: str):
    payload = request.get_json(silent=True) or {}
    if payload.get("confirm") is not True:
        return fail("validation_error", "需要人工明确确认后才能撤销合并", status=400)
    idempotency_key = str(request.headers.get("Idempotency-Key") or f"rollback:{workflow_id}").strip()
    try:
        actor = require_role("admin")
        with get_connection() as conn:
            result = rollback_merge(
                conn,
                workflow_id,
                actor["id"],
                _expected_merge_version(payload),
                idempotency_key,
            )
            conn.commit()
    except AuthError as exc:
        return auth_error_response(exc)
    except IdentityLifecycleError as exc:
        return _identity_error_response(exc)
    except Exception:
        current_app.logger.exception("identity_merge_rollback_failed workflow_id=%s", workflow_id)
        return fail("merge_rollback_failed", "账号合并撤销未完成，事务已回滚，可刷新后重试", status=409)
    return ok(result)


@bp.get("/data-claim-preview")
def data_claim_preview():
    try:
        actor = require_login(allow_legacy_admin=False)
    except AuthError as exc:
        return auth_error_response(exc)
    if actor.get("role") not in {"parent", "student", "user"}:
        return fail("forbidden", "研究与管理账号不参与试用记录合并", status=403)

    with get_connection() as conn:
        # Backfill accounts that recorded an anonymous ID before this feature existed.
        register_claim_candidate(conn, actor["id"], actor["user"].get("anonymous_id"))
        preview = claim_preview(
            conn,
            actor["id"],
            token_ttl_seconds=int(current_app.config.get("DATA_CLAIM_TOKEN_TTL_SECONDS", 900)),
        )
        conn.commit()
    return ok(preview)


@bp.post("/data-claim")
def data_claim():
    try:
        actor = require_login(allow_legacy_admin=False)
    except AuthError as exc:
        return auth_error_response(exc)
    if actor.get("role") not in {"parent", "student", "user"}:
        return fail("forbidden", "研究与管理账号不参与试用记录合并", status=403)

    payload = request.get_json(silent=True) or {}
    claim_id = str(payload.get("claim_id") or "").strip()
    if not claim_id or payload.get("confirm") is not True:
        return fail("validation_error", "需要明确确认后才能合并试用记录", status=400)
    expected_version = payload.get("expected_version")
    if expected_version is not None:
        try:
            expected_version = int(expected_version)
        except (TypeError, ValueError):
            return fail("validation_error", "认领状态版本无效", status=400)
    idempotency_key = str(request.headers.get("Idempotency-Key") or "").strip()
    if not idempotency_key:
        return fail("idempotency_key_required", "匿名认领必须提供 Idempotency-Key", status=400)
    production = str(current_app.config.get("APP_ENV") or "").lower() == "production"
    rate_decision = redis_rate_limit(
        "data-claim:"
        + redis_hash_component(f"{actor['id']}:{request.remote_addr or 'unknown'}", salt="data-claim"),
        limit=int(current_app.config.get("DATA_CLAIM_RATE_LIMIT_PER_MINUTE", 10)),
        window_seconds=60,
        unavailable_policy="deny" if production else "deny_if_enabled",
    )
    if not rate_decision["allowed"]:
        if not rate_decision["available"]:
            return fail("rate_limit_unavailable", "请求保护暂时不可用，请稍后再试", status=503)
        return fail("rate_limited", "认领尝试过于频繁，请稍后再试", status=429)
    try:
        with get_connection() as conn:
            result = claim_records(
                conn,
                actor["id"],
                claim_id,
                idempotency_key=idempotency_key,
                expected_version=expected_version,
                max_attempts=int(current_app.config.get("DATA_CLAIM_MAX_ATTEMPTS", 5)),
            )
            conn.commit()
    except LookupError as exc:
        return fail("not_found", str(exc), status=404)
    except ValueError as exc:
        return fail("claim_unavailable", str(exc), status=409)
    return ok(result)
