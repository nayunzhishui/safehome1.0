"""Human supervision request endpoints."""

from flask import Blueprint, request

from database import ensure_user, get_connection, new_id, now_iso, row_to_dict
from routes.auth_utils import AuthError, auth_error_response, require_role, resolve_actor_user_id
from routes.utils import fail, ok, require_fields
from services.message_service import create_message
from services.risk_review_service import create_risk_review_record
from services.risk_service import check_text_risk

bp = Blueprint("supervision", __name__, url_prefix="/api/supervision")


@bp.post("")
def create_supervision_request():
    payload = request.get_json(silent=True) or {}
    missing = require_fields(payload, ["message"])
    if missing:
        return fail("missing_fields", f"缺少必填字段：{', '.join(missing)}")

    try:
        user_id = resolve_actor_user_id(payload=payload)
    except AuthError as exc:
        return auth_error_response(exc)
    timestamp = now_iso()
    request_id = new_id("supervision")
    source_type = str(payload.get("source_type") or "").strip()
    source_id = str(payload.get("source_id") or payload.get("diary_id") or "").strip()
    source_title = str(payload.get("source_title") or "").strip()[:120]
    if source_type not in {"", "diary", "assessment"}:
        return fail("invalid_source_type", "关联记录类型不受支持。", status=400)
    risk_result = check_text_risk([payload.get("message"), payload.get("risk_hint")], source="supervision")
    stored_risk_level = risk_result.get("risk_level", "low")
    if stored_risk_level == "low":
        stored_risk_level = payload.get("risk_level", "low")

    with get_connection() as conn:
        ensure_user(conn, user_id, payload.get("nickname"))
        if source_type == "diary":
            source_row = conn.execute(
                "SELECT id, scene FROM emotion_diaries WHERE id = ? AND user_id = ?",
                (source_id, user_id),
            ).fetchone()
            if source_row is None:
                return fail("source_not_found", "没有找到可关联的情绪日记。", status=404)
            source_title = source_title or f"情绪日记 · {source_row['scene'] or '具体事件'}"
        elif source_type == "assessment":
            source_row = conn.execute(
                "SELECT id, worksheet_title FROM assessment_results WHERE id = ? AND user_id = ?",
                (source_id, user_id),
            ).fetchone()
            if source_row is None:
                return fail("source_not_found", "没有找到可关联的测评记录。", status=404)
            source_title = source_title or f"测一测 · {source_row['worksheet_title'] or '支持性测评'}"
        conn.execute(
            """
            INSERT INTO supervision_requests (
                id, user_id, diary_id, source_type, source_id, source_title,
                message, contact, risk_hint, risk_level, status, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?)
            """,
            (
                request_id,
                user_id,
                source_id if source_type == "diary" else None,
                source_type or None,
                source_id or None,
                source_title or None,
                payload["message"],
                payload.get("contact"),
                payload.get("risk_hint"),
                stored_risk_level,
                timestamp,
            ),
        )
        create_risk_review_record(conn, user_id, "supervision", request_id, risk_result)
        conn.commit()
        row = conn.execute(
            "SELECT * FROM supervision_requests WHERE id = ?", (request_id,)
        ).fetchone()

    item = row_to_dict(row)
    item["risk"] = risk_result
    item["boundary_notice"] = risk_result.get("boundary_notice")
    return ok(item, status=201)


@bp.post("/<request_id>/reply")
def reply_supervision_request(request_id: str):
    try:
        actor = require_role("admin", "supervisor", allow_legacy_admin=True)
    except AuthError as exc:
        return auth_error_response(exc)

    payload = request.get_json(silent=True) or {}
    reply = str(payload.get("supervisor_reply") or payload.get("reply") or "").strip()
    if not reply:
        return fail("missing_fields", "请填写督导补充内容。", status=400)

    timestamp = now_iso()
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM supervision_requests WHERE id = ?", (request_id,)).fetchone()
        if row is None:
            return fail("not_found", "没有找到对应督导请求。", status=404)
        conn.execute(
            """
            UPDATE supervision_requests
            SET supervisor_reply = ?, status = 'replied', replied_at = ?
            WHERE id = ?
            """,
            (reply, timestamp, request_id),
        )
        create_message(
            conn,
            user_id=row["user_id"],
            message_type="supervision_feedback",
            title="老师补充反馈已更新",
            body="你提交的人工督导请求已有补充反馈，可以到消息里查看。这里不替代紧急帮助。",
            source_type="supervision",
            source_id=request_id,
        )
        conn.commit()
        updated = conn.execute("SELECT * FROM supervision_requests WHERE id = ?", (request_id,)).fetchone()

    item = row_to_dict(updated)
    item["actor_id"] = actor["id"]
    return ok(item)
