"""Formal pilot username/password and WeChat auth endpoints."""

import hashlib
import hmac
import json
import os
import re
import time
from pathlib import Path
from urllib.parse import urlencode
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from flask import Blueprint, current_app, request
from werkzeug.security import check_password_hash, generate_password_hash

from config import Config
from database import ensure_user, get_connection, new_id, now_iso, row_to_dict, write_audit_log
from routes.auth_utils import PUBLIC_REGISTER_ROLES, AuthError, auth_error_response, generate_auth_token, get_current_actor, require_login
from routes.utils import fail, ok, require_admin_token
from services.data_claim_service import claim_preview, claim_records, register_claim_candidate
from services.security_control_service import record_security_event

bp = Blueprint("auth", __name__, url_prefix="/api/auth")
CLOUDBASE_ACCESS_TOKEN_PATH = "/.tencentcloudbase/wx/cloudbase_access_token"
_WECHAT_ACCESS_TOKEN_CACHE: dict[str, float | str] = {"appid": "", "token": "", "expires_at": 0.0}
_CLOUDBASE_OPENID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{6,128}$")


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
    }


def _trusted_cloudbase_openid() -> str | None:
    """Read the identity header injected by WeChat CloudBase callContainer.

    This path is disabled by default. Deployments behind CloudBase callContainer
    must opt in explicitly after confirming that public traffic cannot bypass
    the trusted gateway.
    """

    if not current_app.config.get("TRUST_CLOUDBASE_IDENTITY_HEADERS", False):
        return None
    openid = str(request.headers.get("X-WX-OPENID") or "").strip()
    source = str(request.headers.get("X-WX-SOURCE") or "").strip()
    if source != "wx-cloudbase" or not _CLOUDBASE_OPENID_PATTERN.fullmatch(openid):
        return None
    return openid


def _read_json_response(response) -> dict:
    return json.loads(response.read().decode("utf-8"))


def _wechat_session_from_code(code: str) -> dict:
    appid = os.environ.get("WECHAT_APPID", "").strip()
    secret = os.environ.get("WECHAT_SECRET", "").strip()
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
            with urlopen(f"https://api.weixin.qq.com/sns/jscode2session?{query}", timeout=8) as response:
                payload = _read_json_response(response)
        except (HTTPError, URLError, OSError, json.JSONDecodeError) as exc:
            raise WechatAuthError("wechat_service_unavailable", "微信服务暂时没有响应，请稍后重试。", 502) from exc
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
    token_path = Path(os.environ.get("CLOUDBASE_ACCESS_TOKEN_PATH", CLOUDBASE_ACCESS_TOKEN_PATH))
    try:
        token = token_path.read_text(encoding="utf-8").strip()
    except OSError:
        return None
    return token or None


def _standard_wechat_access_token() -> str | None:
    appid = os.environ.get("WECHAT_APPID", "").strip()
    secret = os.environ.get("WECHAT_SECRET", "").strip()
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
        with urlopen(f"https://api.weixin.qq.com/cgi-bin/token?{query}", timeout=8) as response:
            payload = _read_json_response(response)
    except (HTTPError, URLError, OSError, json.JSONDecodeError) as exc:
        raise WechatAuthError("wechat_service_unavailable", "微信服务暂时没有响应，请稍后重试。", 502) from exc
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
        raise WechatAuthError("wechat_service_unavailable", "微信服务暂时没有响应，请稍后重试。", 502) from exc
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


@bp.get("/capabilities")
def auth_capabilities():
    """Expose login readiness without returning credentials or identity values."""
    standard_wechat_configured = bool(
        os.environ.get("WECHAT_APPID", "").strip()
        and os.environ.get("WECHAT_SECRET", "").strip()
    )
    cloudbase_identity_available = _trusted_cloudbase_openid() is not None
    cloudbase_phone_token_available = _cloudbase_access_token() is not None
    return ok(
        {
            "account_password": {"available": True},
            "wechat_login": {
                "available": bool(cloudbase_identity_available or standard_wechat_configured),
                "mode": (
                    "cloudbase_identity"
                    if cloudbase_identity_available
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
        if row is None or not row["password_hash"] or not check_password_hash(row["password_hash"], password):
            record_security_event(
                "login_failed",
                "medium",
                target_type="credential_hash",
                target_id=hashlib.sha256(username.encode("utf-8")).hexdigest()[:16] if username else None,
                metadata={"source": "password", "failure_count": 1},
            )
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
        timestamp = now_iso()
        conn.execute(
            "UPDATE users SET anonymous_id = COALESCE(?, anonymous_id), last_login_at = ?, updated_at = ? WHERE id = ?",
            (anonymous_id, timestamp, timestamp, row["id"]),
        )
        register_claim_candidate(conn, row["id"], anonymous_id)
        conn.commit()
        row = conn.execute("SELECT * FROM users WHERE id = ?", (row["id"],)).fetchone()

    user = _public_user(row_to_dict(row))
    return ok({"token": generate_auth_token(user), "user": user})


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
            user_id = row["id"]
            if row["status"] and row["status"] != "active":
                return fail("account_inactive", "账号暂不可用", status=403)
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
        conn.commit()
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()

    user = _public_user(row_to_dict(row))
    return ok(
        {
            "token": generate_auth_token(user),
            "user": user,
            "dev_fallback": bool(session.get("dev_fallback")),
            "identity_source": session.get("identity_source") or "jscode2session",
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
        if phone_row is not None and openid_row is not None and phone_row["id"] != openid_row["id"]:
            return fail("phone_account_conflict", "该手机号已关联其他账号，请使用原账号登录。", status=409)

        row = phone_row or openid_row
        if row is None:
            user_id = new_id("user")
            ensure_user(conn, user_id, "微信用户")
        else:
            user_id = row["id"]
            if row["status"] and row["status"] != "active":
                return fail("account_inactive", "账号暂不可用", status=403)

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
        conn.commit()
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()

    user = _public_user(row_to_dict(row))
    return ok(
        {
            "token": generate_auth_token(user),
            "user": user,
            "phone_bound": True,
            "phone_masked": _mask_phone(phone_number),
        }
    )


@bp.post("/bind-phone")
def bind_phone():
    """Bind a WeChat-authorized phone number without storing the raw number."""

    try:
        actor = require_login(allow_legacy_admin=False)
    except AuthError as exc:
        return auth_error_response(exc)

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

    if len(username) < 3:
        return fail("validation_error", "用户名至少需要 3 个字符", status=400)
    if len(password) < 8:
        return fail("validation_error", "密码至少需要 8 个字符", status=400)
    if role not in {"admin", "researcher", "supervisor", "parent", "student"}:
        return fail("validation_error", "不支持该角色", status=400)

    timestamp = now_iso()
    user_id = new_id("user")
    with get_connection() as conn:
        existing = conn.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
        if existing:
            if not rotate_existing:
                return fail("username_exists", "该用户名已被使用", status=409)
            user_id = existing["id"]
        else:
            ensure_user(conn, user_id, nickname)
        conn.execute(
            """
            UPDATE users
            SET username = ?, phone_or_email = ?, password_hash = ?,
                anonymous_id = ?, role = ?, source = 'admin_created',
                status = 'active', status_reason = NULL,
                auth_epoch = auth_epoch + ?, updated_at = ?
            WHERE id = ?
            """,
            (username, None, generate_password_hash(password), anonymous_id, role, 1 if existing else 0, timestamp, user_id),
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


@bp.post("/logout")
def logout():
    try:
        actor = get_current_actor(allow_legacy_admin=False)
    except AuthError as exc:
        return auth_error_response(exc)
    if actor is None:
        return ok({"message": "本地登录状态可以清除；当前请求没有可撤销的服务端令牌。", "tokens_revoked": False})
    timestamp = now_iso()
    with get_connection() as conn:
        conn.execute(
            "UPDATE users SET auth_epoch = auth_epoch + 1, updated_at = ? WHERE id = ?",
            (timestamp, actor["id"]),
        )
        write_audit_log(conn, "auth_sessions_revoked", actor["id"], "user", actor["id"], {"scope": "all_tokens"})
        conn.commit()
    return ok({"message": "已安全退出，当前账号的既有登录令牌已失效。"})


@bp.get("/me")
def me():
    try:
        actor = require_login(allow_legacy_admin=False)
    except AuthError as exc:
        return auth_error_response(exc)
    return ok({"user": _public_user(actor["user"])})


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
        preview = claim_preview(conn, actor["id"])
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
    try:
        with get_connection() as conn:
            result = claim_records(conn, actor["id"], claim_id)
            conn.commit()
    except LookupError as exc:
        return fail("not_found", str(exc), status=404)
    except ValueError as exc:
        return fail("claim_unavailable", str(exc), status=409)
    return ok(result)
