"""User-facing in-app messages."""

from flask import Blueprint, request

from database import get_connection, now_iso, row_to_dict, rows_to_dicts, write_audit_log
from routes.auth_utils import AuthError, auth_error_response, require_login, require_role
from routes.utils import fail, ok, parse_int, resolve_user_id_for_query
from services.message_service import create_message
from services.risk_service import check_text_risk

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
    page = max(1, parse_int(request.args.get("page"), 1))
    page_size = max(1, min(parse_int(request.args.get("page_size") or request.args.get("limit"), 50), 100))
    offset = (page - 1) * page_size
    status = str(request.args.get("status") or "").strip()
    message_type = str(request.args.get("message_type") or "").strip()
    where = ["user_id = ?"]
    params: list = [user_id]
    if status in {"unread", "read"}:
        where.append("status = ?")
        params.append(status)
    if message_type:
        where.append("message_type = ?")
        params.append(message_type[:80])
    with get_connection() as conn:
        total_row = conn.execute(
            f"SELECT COUNT(*) AS count FROM messages WHERE {' AND '.join(where)}",
            params,
        ).fetchone()
        rows = conn.execute(
            f"""
            SELECT * FROM messages
            WHERE {' AND '.join(where)}
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
            """,
            [*params, page_size, offset],
        ).fetchall()
        unread_row = conn.execute(
            "SELECT COUNT(*) AS count FROM messages WHERE user_id = ? AND status = 'unread'",
            (user_id,),
        ).fetchone()
    items = [_expand_message(item) for item in rows_to_dicts(rows)]
    total = int(total_row["count"] if total_row else 0)
    return ok({"items": items, "count": len(items), "total": total, "page": page, "page_size": page_size, "has_more": offset + len(items) < total, "unread_count": int(unread_row["count"] if unread_row else 0)})


@bp.post("")
def send_researcher_message():
    try:
        actor = require_role("researcher", "supervisor", "admin", allow_legacy_admin=True)
    except AuthError as exc:
        return auth_error_response(exc)
    payload = request.get_json(silent=True) or {}
    enrollment_id = str(payload.get("enrollment_id") or "").strip()
    title = str(payload.get("title") or "").strip()
    body = str(payload.get("body") or "").strip()
    message_type = str(payload.get("message_type") or "researcher_message").strip()
    idempotency_key = str(request.headers.get("Idempotency-Key") or payload.get("idempotency_key") or "").strip()
    if not enrollment_id:
        return fail("validation_error", "请选择关系试点参与者。", status=400)
    if not title or len(title) > 60:
        return fail("validation_error", "消息标题需为1至60个字符。", status=400)
    if not body or len(body) > 2000:
        return fail("validation_error", "消息正文需为1至2000个字符。", status=400)
    if message_type not in {"researcher_message", "relationship_stage_feedback"}:
        return fail("validation_error", "消息类型不受支持。", status=400)
    if len(idempotency_key) > 120:
        return fail("validation_error", "幂等键过长。", status=400)
    risk = check_text_risk([title, body], source="researcher_message")
    if risk.get("risk_level") == "high" and actor.get("role") == "researcher":
        return fail("message_requires_supervisor_review", "消息包含需要督导复核的高风险表述，请先由督导确认。", status=409)
    with get_connection() as conn:
        enrollment = conn.execute("SELECT id, user_id FROM relationship_pilot_enrollments WHERE id = ?", (enrollment_id,)).fetchone()
        if not enrollment:
            return fail("not_found", "没有找到对应参与者档案。", status=404)
        if idempotency_key:
            existing = conn.execute("SELECT * FROM messages WHERE sender_id = ? AND idempotency_key = ?", (actor["id"], idempotency_key)).fetchone()
            if existing:
                item = _expand_message(row_to_dict(existing))
                item["already_sent"] = True
                return ok(item)
        message = create_message(
            conn,
            enrollment["user_id"],
            title,
            body,
            message_type,
            "relationship_pilot_enrollment",
            enrollment_id,
            sender_id=str(actor["id"]),
            sender_role=str(actor.get("role") or "researcher"),
            idempotency_key=idempotency_key or None,
        )
        write_audit_log(conn, "researcher_message_sent", actor["id"], "message", message["id"], {"enrollment_id": enrollment_id, "recipient_user_id": enrollment["user_id"], "message_type": message_type, "risk_level": risk.get("risk_level")})
        conn.commit()
    return ok(_expand_message(message), status=201)


@bp.post("/read-all")
def mark_all_messages_read():
    payload = request.get_json(silent=True) or {}
    user_id, error = _resolve_message_user_id(payload.get("user_id") or request.args.get("user_id"))
    if error:
        return error
    timestamp = now_iso()
    with get_connection() as conn:
        cursor = conn.execute("UPDATE messages SET status = 'read', read_at = COALESCE(read_at, ?) WHERE user_id = ? AND status = 'unread'", (timestamp, user_id))
        conn.commit()
    return ok({"updated_count": int(cursor.rowcount or 0), "status": "read"})


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
