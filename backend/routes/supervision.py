"""Human supervision request endpoints."""

from datetime import datetime, timedelta, timezone

from flask import Blueprint, request

from database import ensure_user, get_connection, json_dumps, new_id, now_iso, row_to_dict, write_audit_log
from routes.auth_utils import AuthError, auth_error_response, require_role, resolve_actor_user_id
from routes.utils import fail, ok, require_fields
from services.input_validation_service import InputValidationError, bounded_text, validate_supervision_payload
from services.message_service import create_message
from services.risk_review_service import create_risk_review_record
from services.risk_service import check_text_risk
from services.schema_migration_service import apply_pending_schema_migrations

bp = Blueprint("supervision", __name__, url_prefix="/api/supervision")

SUPERVISION_TARGET_MINUTES = {
    "urgent_human_review": 15,
    "human_review": 240,
    "standard": 1440,
}
SUPERVISION_STATUSES = {"pending", "acknowledged", "in_review", "replied", "resolved", "transferred", "closed"}


def _due_at(route: str, timestamp: str) -> str:
    minutes = SUPERVISION_TARGET_MINUTES.get(route, 1440)
    parsed = datetime.fromisoformat(timestamp)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return (parsed + timedelta(minutes=minutes)).isoformat()


def _priority(route: str) -> str:
    if route == "urgent_human_review":
        return "urgent"
    if route == "human_review":
        return "high"
    return "normal"


def _mask_contact(value: str | None) -> str | None:
    text = str(value or "").strip()
    if not text:
        return None
    if "@" in text:
        local, _, domain = text.partition("@")
        return f"{local[:1]}***@{domain}" if domain else "***"
    digits = "".join(char for char in text if char.isdigit())
    if len(digits) >= 7:
        return f"{digits[:3]}****{digits[-4:]}"
    return text[:1] + "***"


def _public_item(row: dict, *, include_contact: bool = False) -> dict:
    item = dict(row)
    contact = item.pop("contact", None)
    item["contact_masked"] = _mask_contact(contact)
    if include_contact:
        item["contact"] = contact
    item["sla_notice"] = "响应时间是内部服务目标，不是紧急服务承诺；如存在现实危险，请优先联系现实中的可信成年人、专业机构或当地紧急服务。"
    return item


def _event(conn, request_id: str, actor_id: str, actor_role: str, action: str, from_status: str | None, to_status: str, metadata: dict | None = None) -> None:
    conn.execute(
        """
        INSERT INTO supervision_request_events (
            id, request_id, actor_id, actor_role, action,
            from_status, to_status, metadata_json, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            new_id("supervision_event"),
            request_id,
            actor_id,
            actor_role,
            action,
            from_status,
            to_status,
            json_dumps(metadata or {}),
            now_iso(),
        ),
    )


def _reviewer_actor():
    try:
        return require_role("admin", "supervisor", allow_legacy_admin=True), None
    except AuthError as exc:
        return None, auth_error_response(exc)


@bp.post("")
def create_supervision_request():
    raw_payload = request.get_json(silent=True) or {}
    missing = require_fields(raw_payload, ["message"])
    if missing:
        return fail("missing_fields", f"缺少必填字段：{', '.join(missing)}")
    try:
        payload = validate_supervision_payload(raw_payload)
    except InputValidationError as exc:
        return fail(exc.code, exc.message, status=400, details={"field": exc.field})

    try:
        user_id = resolve_actor_user_id(payload=payload)
    except AuthError as exc:
        return auth_error_response(exc)
    timestamp = now_iso()
    request_id = new_id("supervision")
    submission_id = str(request.headers.get("Idempotency-Key") or payload.get("client_submission_id") or "").strip()
    if len(submission_id) > 120:
        return fail("validation_error", "提交标识不能超过120个字符。", status=400)
    source_type = str(payload.get("source_type") or "").strip()
    source_id = str(payload.get("source_id") or payload.get("diary_id") or "").strip()
    source_title = str(payload.get("source_title") or "").strip()[:120]
    if source_type not in {"", "diary", "assessment"}:
        return fail("invalid_source_type", "关联记录类型不受支持。", status=400)

    risk_result = check_text_risk([payload.get("message"), payload.get("risk_hint")], source="supervision")
    safety_route = str(risk_result.get("safety_route") or "standard")
    stored_risk_level = str(risk_result.get("risk_level") or payload.get("risk_level") or "low")
    priority = _priority(safety_route)
    due_at = _due_at(safety_route, timestamp)

    with get_connection() as conn:
        apply_pending_schema_migrations(conn)
        ensure_user(conn, user_id, payload.get("nickname"))
        if submission_id:
            existing = conn.execute(
                "SELECT * FROM supervision_requests WHERE user_id = ? AND client_submission_id = ?",
                (user_id, submission_id),
            ).fetchone()
            if existing is not None:
                same_payload = (
                    existing["message"] == payload["message"]
                    and (existing["source_type"] or "") == source_type
                    and (existing["source_id"] or "") == source_id
                    and existing["contact"] == payload.get("contact")
                    and existing["risk_hint"] == payload.get("risk_hint")
                    and (not source_title or existing["source_title"] == source_title)
                )
                if not same_payload:
                    return fail("idempotency_conflict", "该提交标识已用于另一份人工支持请求。", status=409)
                item = _public_item(row_to_dict(existing))
                item["risk"] = risk_result
                item["boundary_notice"] = risk_result.get("boundary_notice")
                return ok(item)
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
                message, contact, risk_hint, risk_level, status, client_submission_id,
                priority, due_at, last_actor_id, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?, ?, ?, ?, ?)
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
                submission_id or None,
                priority,
                due_at,
                user_id,
                timestamp,
            ),
        )
        _event(
            conn,
            request_id,
            user_id,
            "participant",
            "created",
            None,
            "pending",
            {"priority": priority, "due_at": due_at, "safety_route": safety_route},
        )
        create_risk_review_record(conn, user_id, "supervision", request_id, risk_result)
        write_audit_log(
            conn,
            action="supervision_requested",
            actor_id=user_id,
            target_type="supervision_request",
            target_id=request_id,
            metadata={"priority": priority, "due_at": due_at, "safety_route": safety_route},
        )
        conn.commit()
        row = conn.execute("SELECT * FROM supervision_requests WHERE id = ?", (request_id,)).fetchone()

    item = _public_item(row_to_dict(row))
    item["risk"] = risk_result
    item["boundary_notice"] = risk_result.get("boundary_notice")
    return ok(item, status=201)


@bp.get("/<request_id>")
def get_supervision_request(request_id: str):
    try:
        actor_user_id = resolve_actor_user_id()
    except AuthError as exc:
        return auth_error_response(exc)
    with get_connection() as conn:
        apply_pending_schema_migrations(conn)
        row = conn.execute("SELECT * FROM supervision_requests WHERE id = ?", (request_id,)).fetchone()
        if row is None:
            return fail("not_found", "没有找到对应督导请求。", status=404)
        item = row_to_dict(row)
        if str(item["user_id"]) != str(actor_user_id):
            return fail("forbidden", "只能查看自己的人工支持请求。", status=403)
    return ok(_public_item(item))


@bp.get("/<request_id>/reviewer")
def get_supervision_request_for_reviewer(request_id: str):
    actor, error = _reviewer_actor()
    if error:
        return error
    with get_connection() as conn:
        apply_pending_schema_migrations(conn)
        row = conn.execute("SELECT * FROM supervision_requests WHERE id = ?", (request_id,)).fetchone()
        if row is None:
            return fail("not_found", "没有找到对应督导请求。", status=404)
        write_audit_log(
            conn,
            action="supervision_sensitive_contact_viewed",
            actor_id=str(actor["id"]),
            target_type="supervision_request",
            target_id=request_id,
            metadata={"actor_role": actor.get("role"), "contact_present": bool(row["contact"])},
        )
        conn.commit()
    return ok(_public_item(row_to_dict(row), include_contact=True))


@bp.post("/<request_id>/acknowledge")
def acknowledge_supervision_request(request_id: str):
    actor, error = _reviewer_actor()
    if error:
        return error
    timestamp = now_iso()
    with get_connection() as conn:
        apply_pending_schema_migrations(conn)
        row = conn.execute("SELECT * FROM supervision_requests WHERE id = ?", (request_id,)).fetchone()
        if row is None:
            return fail("not_found", "没有找到对应督导请求。", status=404)
        before = row_to_dict(row)
        if before["status"] in {"resolved", "closed"}:
            return fail("invalid_status_transition", "已结束的人工支持请求不能重新确认接单。", status=409)
        conn.execute(
            """
            UPDATE supervision_requests
            SET status = 'acknowledged', acknowledged_at = ?, acknowledged_by = ?,
                last_actor_id = ?
            WHERE id = ?
            """,
            (timestamp, str(actor["id"]), str(actor["id"]), request_id),
        )
        _event(conn, request_id, str(actor["id"]), str(actor.get("role") or "supervisor"), "acknowledged", before["status"], "acknowledged")
        write_audit_log(conn, "supervision_acknowledged", str(actor["id"]), "supervision_request", request_id, {"previous_status": before["status"]})
        conn.commit()
        updated = conn.execute("SELECT * FROM supervision_requests WHERE id = ?", (request_id,)).fetchone()
    return ok(_public_item(row_to_dict(updated), include_contact=True))


@bp.post("/<request_id>/reply")
def reply_supervision_request(request_id: str):
    actor, error = _reviewer_actor()
    if error:
        return error

    payload = request.get_json(silent=True) or {}
    try:
        reply = bounded_text(
            payload.get("supervisor_reply") or payload.get("reply"),
            "supervisor_reply",
            allow_none=False,
        )
    except InputValidationError as exc:
        return fail(exc.code, exc.message, status=400, details={"field": exc.field})

    timestamp = now_iso()
    with get_connection() as conn:
        apply_pending_schema_migrations(conn)
        row = conn.execute("SELECT * FROM supervision_requests WHERE id = ?", (request_id,)).fetchone()
        if row is None:
            return fail("not_found", "没有找到对应督导请求。", status=404)
        before = row_to_dict(row)
        if before["status"] in {"resolved", "closed"}:
            return fail("invalid_status_transition", "已结束的人工支持请求不能继续回复。", status=409)
        conn.execute(
            """
            UPDATE supervision_requests
            SET supervisor_reply = ?, status = 'replied', replied_at = ?, last_actor_id = ?
            WHERE id = ?
            """,
            (reply, timestamp, str(actor["id"]), request_id),
        )
        _event(conn, request_id, str(actor["id"]), str(actor.get("role") or "supervisor"), "replied", before["status"], "replied")
        create_message(
            conn,
            user_id=row["user_id"],
            message_type="supervision_feedback",
            title="老师补充反馈已更新",
            body="你提交的人工支持请求已有补充反馈，可以到消息里查看。这里不替代紧急帮助。",
            source_type="supervision",
            source_id=request_id,
        )
        write_audit_log(conn, "supervision_replied", str(actor["id"]), "supervision_request", request_id, {"previous_status": before["status"]})
        conn.commit()
        updated = conn.execute("SELECT * FROM supervision_requests WHERE id = ?", (request_id,)).fetchone()

    return ok(_public_item(row_to_dict(updated), include_contact=True))


@bp.post("/<request_id>/resolve")
def resolve_supervision_request(request_id: str):
    actor, error = _reviewer_actor()
    if error:
        return error
    payload = request.get_json(silent=True) or {}
    resolution_code = str(payload.get("resolution_code") or "support_completed").strip()[:80]
    if not resolution_code:
        return fail("validation_error", "resolution_code 不能为空。", status=400)
    timestamp = now_iso()
    with get_connection() as conn:
        apply_pending_schema_migrations(conn)
        row = conn.execute("SELECT * FROM supervision_requests WHERE id = ?", (request_id,)).fetchone()
        if row is None:
            return fail("not_found", "没有找到对应督导请求。", status=404)
        before = row_to_dict(row)
        if before["status"] == "closed":
            return fail("invalid_status_transition", "请求已经关闭。", status=409)
        conn.execute(
            """
            UPDATE supervision_requests
            SET status = 'resolved', resolved_at = ?, resolved_by = ?,
                resolution_code = ?, last_actor_id = ?
            WHERE id = ?
            """,
            (timestamp, str(actor["id"]), resolution_code, str(actor["id"]), request_id),
        )
        _event(conn, request_id, str(actor["id"]), str(actor.get("role") or "supervisor"), "resolved", before["status"], "resolved", {"resolution_code": resolution_code})
        write_audit_log(conn, "supervision_resolved", str(actor["id"]), "supervision_request", request_id, {"resolution_code": resolution_code})
        conn.commit()
        updated = conn.execute("SELECT * FROM supervision_requests WHERE id = ?", (request_id,)).fetchone()
    return ok(_public_item(row_to_dict(updated), include_contact=True))
