"""Formal pilot username/password auth endpoints."""

from flask import Blueprint, request
from werkzeug.security import check_password_hash, generate_password_hash

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
        "status": row.get("status") or "active",
    }


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
