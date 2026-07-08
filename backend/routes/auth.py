"""Formal pilot username/password and WeChat auth endpoints."""

import hashlib
import json
import os
from urllib.parse import urlencode
from urllib.request import urlopen

from flask import Blueprint, request
from werkzeug.security import check_password_hash, generate_password_hash

from config import Config
from database import ensure_user, get_connection, new_id, now_iso, row_to_dict
from routes.auth_utils import PUBLIC_REGISTER_ROLES, AuthError, auth_error_response, generate_auth_token, require_login
from routes.utils import fail, ok, require_admin_token

bp = Blueprint("auth", __name__, url_prefix="/api/auth")


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
        with urlopen(f"https://api.weixin.qq.com/sns/jscode2session?{query}", timeout=8) as response:
            payload = json.loads(response.read().decode("utf-8"))
        if payload.get("errcode"):
            raise ValueError(payload.get("errmsg") or "微信登录校验失败")
        if not payload.get("openid"):
            raise ValueError("微信登录没有返回 openid")
        return payload
    if Config.APP_ENV == "production":
        raise ValueError("生产环境缺少 WECHAT_APPID 或 WECHAT_SECRET")
    digest = hashlib.sha256(code.encode("utf-8")).hexdigest()[:24]
    return {"openid": f"dev_openid_{digest}", "session_key": None, "dev_fallback": True}


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
            return fail("username_exists", "该用户名已被使用", status=400)
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
        conn.commit()
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()

    user = _public_user(row_to_dict(row))
    return ok({"token": generate_auth_token(user), "user": user}, status=201)


@bp.post("/login")
def login():
    payload = request.get_json(silent=True) or {}
    username = str(payload.get("username") or "").strip()
    password = str(payload.get("password") or "")
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        if row is None or not row["password_hash"] or not check_password_hash(row["password_hash"], password):
            return fail("invalid_credentials", "用户名或密码不正确", status=401)
        if row["status"] and row["status"] != "active":
            return fail("account_inactive", "账号暂不可用", status=403)
        timestamp = now_iso()
        conn.execute("UPDATE users SET last_login_at = ?, updated_at = ? WHERE id = ?", (timestamp, timestamp, row["id"]))
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
    if not code:
        return fail("validation_error", "缺少微信登录 code", status=400)

    try:
        session = _wechat_session_from_code(code)
    except ValueError as exc:
        return fail("wechat_login_failed", str(exc), status=400)

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
        conn.commit()
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()

    user = _public_user(row_to_dict(row))
    return ok({"token": generate_auth_token(user), "user": user, "dev_fallback": bool(session.get("dev_fallback"))})


@bp.post("/bind-phone")
def bind_phone():
    """Bind a WeChat-authorized phone number when platform config is available.

    The pilot build intentionally does not fake phone authorization. Mini
    Program getPhoneNumber returns a short-lived code that must be exchanged
    through WeChat's API with real AppID/AppSecret and permissions.
    """

    try:
        actor = require_login(allow_legacy_admin=False)
    except AuthError as exc:
        return auth_error_response(exc)

    payload = request.get_json(silent=True) or {}
    code = str(payload.get("code") or "").strip()
    if not code:
        return fail("validation_error", "缺少手机号授权 code", status=400)

    appid = os.environ.get("WECHAT_APPID", "").strip()
    secret = os.environ.get("WECHAT_SECRET", "").strip()
    if not appid or not secret:
        return fail(
            "wechat_phone_config_missing",
            "缺少 WECHAT_APPID/WECHAT_SECRET 或小程序手机号授权配置，不能伪造手机号绑定。",
            status=400,
        )

    # Keep the endpoint explicit and safe until access_token management is added.
    return fail(
        "wechat_phone_not_configured",
        "手机号授权接口骨架已存在，但尚未配置微信 access_token 交换流程。",
        status=400,
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
            return fail("username_exists", "该用户名已被使用", status=400)
        ensure_user(conn, user_id, nickname)
        conn.execute(
            """
            UPDATE users
            SET username = ?, phone_or_email = ?, password_hash = ?,
                anonymous_id = ?, role = ?, source = 'admin_created',
                status = 'active', updated_at = ?
            WHERE id = ?
            """,
            (username, None, generate_password_hash(password), anonymous_id, role, timestamp, user_id),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()

    user = _public_user(row_to_dict(row))
    return ok({"user": user}, status=201)


@bp.post("/logout")
def logout():
    return ok({"message": "已退出。请在前端清除本地登录状态。"})


@bp.get("/me")
def me():
    try:
        actor = require_login(allow_legacy_admin=False)
    except AuthError as exc:
        return auth_error_response(exc)
    return ok({"user": _public_user(actor["user"])})
