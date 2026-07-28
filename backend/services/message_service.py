"""Deep message domain service; HTTP adapters only resolve actors and inputs."""

from database import get_connection, new_id, now_iso, row_to_dict, rows_to_dicts, write_audit_log
from services.relationship_pilot_common import RelationshipPilotError, ensure_researcher_assignment
from services.risk_service import check_text_risk


PUBLIC_FIELDS = {
    "id", "user_id", "message_type", "title", "body", "source_type", "source_id",
    "sender_role", "status", "created_at", "read_at", "delivery_id", "delivery_version", "withdrawn_at",
}


class MessageServiceError(ValueError):
    def __init__(self, code: str, message: str, status: int) -> None:
        super().__init__(message)
        self.code = code
        self.status = status


def public_message(item: dict) -> dict:
    result = {key: value for key, value in item.items() if key in PUBLIC_FIELDS}
    result["is_unread"] = result.get("status") == "unread"
    result["is_withdrawn"] = result.get("status") == "withdrawn"
    if item.get("already_sent"):
        result["already_sent"] = True
    return result


def create_message(
    conn,
    user_id: str,
    title: str,
    body: str | None = None,
    message_type: str = "system",
    source_type: str | None = None,
    source_id: str | None = None,
    sender_id: str | None = None,
    sender_role: str | None = None,
    idempotency_key: str | None = None,
    delivery_id: str | None = None,
    delivery_version: int | None = None,
) -> dict:
    message_id = new_id("msg")
    timestamp = now_iso()
    conn.execute(
        """
        INSERT INTO messages (
            id, user_id, sender_id, sender_role, message_type, title, body,
            source_type, source_id, idempotency_key, status, created_at, read_at
            , delivery_id, delivery_version, withdrawn_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'unread', ?, NULL, ?, ?, NULL)
        """,
        (message_id, user_id, sender_id, sender_role, message_type, title, body, source_type, source_id, idempotency_key, timestamp, delivery_id, delivery_version),
    )
    row = conn.execute("SELECT * FROM messages WHERE id = ?", (message_id,)).fetchone()
    return row_to_dict(row) or {"id": message_id, "user_id": user_id}


def list_user_messages(user_id: str, *, page: int, page_size: int, status: str = "", message_type: str = "") -> dict:
    offset = (page - 1) * page_size
    where = ["user_id = ?"]
    params: list = [user_id]
    if status in {"unread", "read"}:
        where.append("status = ?")
        params.append(status)
    if message_type:
        where.append("message_type = ?")
        params.append(message_type[:80])
    with get_connection() as conn:
        total_row = conn.execute(f"SELECT COUNT(*) AS count FROM messages WHERE {' AND '.join(where)}", params).fetchone()
        rows = conn.execute(
            f"SELECT * FROM messages WHERE {' AND '.join(where)} ORDER BY created_at DESC LIMIT ? OFFSET ?",
            [*params, page_size, offset],
        ).fetchall()
        unread_row = conn.execute("SELECT COUNT(*) AS count FROM messages WHERE user_id = ? AND status = 'unread'", (user_id,)).fetchone()
    items = [public_message(item) for item in rows_to_dicts(rows)]
    total = int(total_row["count"] if total_row else 0)
    return {"items": items, "count": len(items), "total": total, "page": page, "page_size": page_size, "has_more": offset + len(items) < total, "unread_count": int(unread_row["count"] if unread_row else 0)}


def send_message_to_participant(actor: dict, payload: dict, idempotency_key: str) -> tuple[dict, int]:
    enrollment_id = str(payload.get("enrollment_id") or "").strip()
    title = str(payload.get("title") or "").strip()
    body = str(payload.get("body") or "").strip()
    message_type = str(payload.get("message_type") or "researcher_message").strip()
    if not enrollment_id:
        raise MessageServiceError("validation_error", "请选择关系试点参与者。", 400)
    if not title or len(title) > 60:
        raise MessageServiceError("validation_error", "消息标题需为1至60个字符。", 400)
    if not body or len(body) > 2000:
        raise MessageServiceError("validation_error", "消息正文需为1至2000个字符。", 400)
    if message_type not in {"researcher_message", "relationship_stage_feedback"}:
        raise MessageServiceError("validation_error", "消息类型不受支持。", 400)
    if len(idempotency_key) > 120:
        raise MessageServiceError("validation_error", "幂等键过长。", 400)
    risk = check_text_risk([title, body], source="researcher_message")
    if risk.get("risk_level") == "high" and actor.get("role") == "researcher":
        raise MessageServiceError("message_requires_supervisor_review", "消息包含需要督导复核的高风险表述，请先由督导确认。", 409)
    with get_connection() as conn:
        enrollment = conn.execute("SELECT * FROM relationship_pilot_enrollments WHERE id = ?", (enrollment_id,)).fetchone()
        if not enrollment:
            raise MessageServiceError("not_found", "没有找到对应参与者档案。", 404)
        enrollment = row_to_dict(enrollment)
        if enrollment.get("status") != "enrolled":
            raise MessageServiceError("enrollment_not_active", "该参与者当前不在项目中，不能继续发送消息。", 409)
        try:
            enrollment = ensure_researcher_assignment(conn, actor, enrollment)
        except RelationshipPilotError as exc:
            raise MessageServiceError(exc.code, exc.message, exc.status) from exc
        if idempotency_key:
            existing = conn.execute("SELECT * FROM messages WHERE sender_id = ? AND idempotency_key = ?", (actor["id"], idempotency_key)).fetchone()
            if existing:
                item = row_to_dict(existing)
                expected = {"user_id": enrollment["user_id"], "source_type": "relationship_pilot_enrollment", "source_id": enrollment_id, "title": title, "body": body, "message_type": message_type}
                if any(str(item.get(key) or "") != str(value or "") for key, value in expected.items()):
                    raise MessageServiceError("idempotency_conflict", "该幂等键已用于另一条消息，请更换后重试。", 409)
                item["already_sent"] = True
                return public_message(item), 200
        from services.publication_gate_service import (
            PublicationGateError,
            assert_candidate_approved,
            evaluate_candidate,
            mark_published,
        )

        try:
            candidate = evaluate_candidate(
                conn,
                actor,
                channel="researcher_message",
                subject_type="relationship_pilot_enrollment",
                subject_id=enrollment_id,
                recipient_user_id=str(enrollment["user_id"]),
                content={"title": title, "body": body},
                source_refs=[f"relationship_pilot_enrollment:{enrollment_id}"],
                idempotency_key=f"researcher-message:{idempotency_key}",
                context={
                    "permission_granted": True,
                    "consent_active": enrollment.get("status") == "enrolled",
                    "recipient_matches_scope": True,
                    "source_authorized": True,
                    "language_checked": True,
                    "responsible_role": str(actor.get("role") or ""),
                    "publisher_id": str(actor["id"]),
                    "author_id": str(actor["id"]),
                    "reviewer_id": "",
                    "human_reviewed": False,
                    "risk_level": str(risk.get("risk_level") or "low"),
                    "high_risk_reviewed": False,
                    "ordinary_training_path": False,
                    "multi_party": False,
                },
            )
            assert_candidate_approved(candidate)
        except PublicationGateError as exc:
            conn.commit()
            raise MessageServiceError(exc.code, exc.message, exc.status) from exc
        message = create_message(conn, enrollment["user_id"], title, body, message_type, "relationship_pilot_enrollment", enrollment_id, sender_id=str(actor["id"]), sender_role=str(actor.get("role") or "researcher"), idempotency_key=idempotency_key or None)
        mark_published(conn, candidate["id"], actor)
        write_audit_log(conn, "researcher_message_sent", actor["id"], "message", message["id"], {"enrollment_id": enrollment_id, "recipient_user_id": enrollment["user_id"], "message_type": message_type, "risk_level": risk.get("risk_level")})
        conn.commit()
    return public_message(message), 201


def mark_all_read(user_id: str) -> dict:
    with get_connection() as conn:
        cursor = conn.execute("UPDATE messages SET status = 'read', read_at = COALESCE(read_at, ?) WHERE user_id = ? AND status = 'unread'", (now_iso(), user_id))
        conn.commit()
    return {"updated_count": int(cursor.rowcount or 0), "status": "read"}


def get_user_message(user_id: str, message_id: str, *, mark_read: bool = True) -> dict:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM messages WHERE id = ? AND user_id = ?", (message_id, user_id)).fetchone()
        if row is None:
            raise MessageServiceError("not_found", "没有找到这条消息。", 404)
        if mark_read and row["status"] == "unread":
            conn.execute("UPDATE messages SET status = 'read', read_at = ? WHERE id = ?", (now_iso(), message_id))
            conn.commit()
            row = conn.execute("SELECT * FROM messages WHERE id = ? AND user_id = ?", (message_id, user_id)).fetchone()
    return public_message(row_to_dict(row))


def mark_one_read(user_id: str, message_id: str) -> dict:
    get_user_message(user_id, message_id, mark_read=False)
    with get_connection() as conn:
        conn.execute(
            "UPDATE messages SET status = 'read', read_at = COALESCE(read_at, ?) WHERE id = ? AND user_id = ? AND status = 'unread'",
            (now_iso(), message_id, user_id),
        )
        conn.commit()
        row = conn.execute("SELECT status, read_at, withdrawn_at FROM messages WHERE id = ? AND user_id = ?", (message_id, user_id)).fetchone()
    return {"id": message_id, "status": row["status"], "read_at": row["read_at"], "withdrawn_at": row["withdrawn_at"]}
