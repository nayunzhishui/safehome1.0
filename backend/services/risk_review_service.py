"""Helpers for creating and updating risk review records."""

import sqlite3
from datetime import datetime, timedelta, timezone

from database import json_dumps, new_id, now_iso, row_to_dict, rows_to_dicts, write_audit_log
from services.schema_migration_service import apply_pending_schema_migrations

REVIEWABLE_RISK_LEVELS = {"medium", "high"}
REVIEW_STATUSES = {
    "pending",
    "priority_review",
    "reviewed",
    "follow_up_needed",
    "transferred",
    "closed",
}
REVIEW_SLA_MINUTES = {
    "urgent_human_review": 15,
    "human_review": 240,
}


def should_create_risk_review(risk_result: dict | None) -> bool:
    if not risk_result:
        return False
    risk_level = risk_result.get("risk_level", "low")
    return risk_level in REVIEWABLE_RISK_LEVELS or bool(risk_result.get("requires_review"))


def _deadline(route: str, timestamp: str) -> str | None:
    minutes = REVIEW_SLA_MINUTES.get(route)
    if not minutes:
        return None
    try:
        parsed = datetime.fromisoformat(timestamp)
    except ValueError:
        parsed = datetime.now(timezone.utc)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return (parsed + timedelta(minutes=minutes)).isoformat()


def _route(risk_result: dict | None) -> str:
    if not risk_result:
        return "standard"
    configured = str(risk_result.get("safety_route") or "").strip()
    if configured in {"standard", "human_review", "urgent_human_review"}:
        return configured
    return "urgent_human_review" if risk_result.get("risk_level") == "high" else "human_review"


def create_risk_review_record(
    conn: sqlite3.Connection,
    user_id: str,
    source_type: str,
    source_id: str,
    risk_result: dict | None,
) -> dict | None:
    """Create a pending review record for safety routing.

    `risk_level` is retained for backward compatibility.  Operational decisions
    use `safety_route`, which makes clear that this queue is not a clinical
    probability classification.
    """

    if not should_create_risk_review(risk_result):
        return None

    apply_pending_schema_migrations(conn)
    timestamp = now_iso()
    review_id = new_id("risk_review")
    matched_categories = risk_result.get("matched_categories", []) if risk_result else []
    safety_route = _route(risk_result)
    priority = "urgent" if safety_route == "urgent_human_review" else "high" if safety_route == "human_review" else "normal"
    review_status = "priority_review" if safety_route == "urgent_human_review" else "pending"
    due_at = _deadline(safety_route, timestamp)
    conn.execute(
        """
        INSERT INTO risk_review_records (
            id, user_id, source_type, source_id, risk_level,
            matched_categories_json, review_status, safety_route, priority,
            due_at, review_version, created_at, updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?)
        """,
        (
            review_id,
            user_id,
            source_type,
            source_id,
            risk_result.get("risk_level", "low") if risk_result else "low",
            json_dumps(matched_categories),
            review_status,
            safety_route,
            priority,
            due_at,
            timestamp,
            timestamp,
        ),
    )
    write_audit_log(
        conn,
        action="risk_review_created",
        actor_id="system",
        target_type="risk_review",
        target_id=review_id,
        metadata={
            "source_type": source_type,
            "source_id": source_id,
            "safety_route": safety_route,
            "priority": priority,
            "due_at": due_at,
        },
    )
    row = conn.execute("SELECT * FROM risk_review_records WHERE id = ?", (review_id,)).fetchone()
    return row_to_dict(row)


def list_risk_review_records(conn, status: str | None = None, limit: int = 50) -> dict:
    apply_pending_schema_migrations(conn)
    where_sql = ""
    params: list = []
    if status:
        if status not in REVIEW_STATUSES:
            raise ValueError("review_status 不在支持范围内")
        where_sql = "WHERE review_status = ?"
        params.append(status)
    params.append(max(1, min(int(limit or 50), 200)))
    rows = conn.execute(
        f"""
        SELECT * FROM risk_review_records
        {where_sql}
        ORDER BY
            CASE priority WHEN 'urgent' THEN 0 WHEN 'high' THEN 1 ELSE 2 END,
            CASE WHEN due_at IS NULL THEN 1 ELSE 0 END,
            due_at ASC,
            created_at ASC
        LIMIT ?
        """,
        params,
    ).fetchall()
    return {"items": rows_to_dicts(rows), "count": len(rows)}


def update_risk_review_record(
    conn: sqlite3.Connection,
    review_id: str,
    reviewer_id: str,
    review_status: str,
    reviewer_role: str = "supervisor",
    review_note: str | None = None,
    action_taken: str | None = None,
    closed_reason: str | None = None,
) -> dict | None:
    apply_pending_schema_migrations(conn)
    if review_status not in REVIEW_STATUSES:
        raise ValueError("review_status 不在支持范围内")

    existing = conn.execute("SELECT * FROM risk_review_records WHERE id = ?", (review_id,)).fetchone()
    if existing is None:
        return None
    existing_dict = row_to_dict(existing)
    if existing_dict.get("review_status") == "closed" and review_status != "closed":
        raise ValueError("已关闭的安全复核不能直接重新打开；如需重启请创建新的人工复核记录")

    timestamp = now_iso()
    escalated_at = existing_dict.get("escalated_at")
    if review_status in {"follow_up_needed", "transferred"} and not escalated_at:
        escalated_at = timestamp

    cursor = conn.execute(
        """
        UPDATE risk_review_records
        SET reviewer_id = ?, last_actor_id = ?, review_status = ?, review_note = ?,
            action_taken = ?, closed_reason = ?, escalated_at = ?,
            reviewed_at = ?, review_version = review_version + 1, updated_at = ?
        WHERE id = ? AND review_version = ?
        """,
        (
            reviewer_id,
            reviewer_id,
            review_status,
            review_note,
            action_taken,
            closed_reason,
            escalated_at,
            timestamp,
            timestamp,
            review_id,
            int(existing_dict.get("review_version") or 0),
        ),
    )
    if getattr(cursor, "rowcount", 1) != 1:
        raise ValueError("复核记录已被其他人员更新，请刷新后重试")

    row = conn.execute("SELECT * FROM risk_review_records WHERE id = ?", (review_id,)).fetchone()
    if row is None:
        return None
    row_dict = row_to_dict(row)

    # Non-repudiation: actor_id is always the authenticated reviewer supplied by
    # the route, never a free-form metadata field from the request body.
    write_audit_log(
        conn,
        action="review_risk",
        actor_id=reviewer_id,
        target_type="risk_review",
        target_id=review_id,
        metadata={
            "actor_role": reviewer_role,
            "review_status": review_status,
            "source_type": row_dict["source_type"],
            "source_id": row_dict["source_id"],
            "risk_level": row_dict["risk_level"],
            "safety_route": row_dict.get("safety_route"),
            "action_taken": action_taken,
            "closed_reason": closed_reason,
            "review_version": row_dict.get("review_version"),
        },
    )
    return row_dict
