"""User-facing in-app messages."""

from flask import Blueprint, request

from database import get_connection, now_iso, row_to_dict, rows_to_dicts
from routes.auth_utils import AuthError, auth_error_response, require_login
from routes.utils import fail, ok, parse_int, resolve_user_id_for_query

bp = Blueprint("messages", __name__, url_prefix="/api/messages")


def _expand_message(item: dict) -> dict:
    item["is_unread"] = item.get("status") == "unread"
    return item


def _resolve_message_user_id(requested_user_id: str | None = None) -> tuple[str | None, tuple | None]:
    try:
        actor = require_login(allow_legacy_admin=True)
    except AuthError as exc:
        return None, auth_error_response(exc)

    if actor["role"] in {"admin", "supervisor"}:
        try:
            return resolve_user_id_for_query(requested_user_id), None
        except ValueError as exc:
            return None, fail("validation_error", str(exc), status=400)

    actor_id = str(actor["id"])
    if requested_user_id and str(requested_user_id) != actor_id:
        return None, fail("forbidden", "只能查看自己的消息。", status=403)
    return actor_id, None


@bp.get("")
def list_messages():
    user_id, error = _resolve_message_user_id(request.args.get("user_id"))
    if error:
        return error
    limit = min(parse_int(request.args.get("limit"), 50), 100)
    status = str(request.args.get("status") or "").strip()
    where = ["user_id = ?"]
    params: list = [user_id]
    if status in {"unread", "read"}:
        where.append("status = ?")
        params.append(status)
    params.append(limit)
    with get_connection() as conn:
        rows = conn.execute(
            f"""
            SELECT * FROM messages
            WHERE {' AND '.join(where)}
            ORDER BY created_at DESC
            LIMIT ?
            """,
            params,
        ).fetchall()
        unread_row = conn.execute(
            "SELECT COUNT(*) AS count FROM messages WHERE user_id = ? AND status = 'unread'",
            (user_id,),
        ).fetchone()
    items = [_expand_message(item) for item in rows_to_dicts(rows)]
    return ok({"items": items, "count": len(items), "unread_count": int(unread_row["count"] if unread_row else 0)})


@bp.get("/<message_id>")
def get_message(message_id: str):
    user_id, error = _resolve_message_user_id(request.args.get("user_id"))
    if error:
        return error
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM messages WHERE id = ? AND user_id = ?", (message_id, user_id)).fetchone()
        if row is None:
            return fail("not_found", "没有找到这条消息。", status=404)
        if row["status"] != "read":
            conn.execute("UPDATE messages SET status = 'read', read_at = ? WHERE id = ?", (now_iso(), message_id))
            conn.commit()
            row = conn.execute("SELECT * FROM messages WHERE id = ? AND user_id = ?", (message_id, user_id)).fetchone()
    return ok(_expand_message(row_to_dict(row)))


@bp.post("/<message_id>/read")
def mark_message_read(message_id: str):
    payload = request.get_json(silent=True) or {}
    user_id, error = _resolve_message_user_id(payload.get("user_id") or request.args.get("user_id"))
    if error:
        return error
    with get_connection() as conn:
        row = conn.execute("SELECT id FROM messages WHERE id = ? AND user_id = ?", (message_id, user_id)).fetchone()
        if row is None:
            return fail("not_found", "没有找到这条消息。", status=404)
        conn.execute("UPDATE messages SET status = 'read', read_at = COALESCE(read_at, ?) WHERE id = ?", (now_iso(), message_id))
        conn.commit()
    return ok({"id": message_id, "status": "read"})
