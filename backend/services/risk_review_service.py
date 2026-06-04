"""Helpers for creating and updating risk review records."""

import sqlite3

from database import json_dumps, new_id, now_iso, row_to_dict, rows_to_dicts, write_audit_log

REVIEWABLE_RISK_LEVELS = {"medium", "high"}
REVIEW_STATUSES = {"pending", "reviewed", "follow_up_needed", "transferred", "closed"}


def should_create_risk_review(risk_result: dict | None) -> bool:
    if not risk_result:
        return False
    risk_level = risk_result.get("risk_level", "low")
    return risk_level in REVIEWABLE_RISK_LEVELS or bool(risk_result.get("requires_review"))


def create_risk_review_record(
    conn: sqlite3.Connection,
    user_id: str,
    source_type: str,
    source_id: str,
    risk_result: dict | None,
) -> dict | None:
    """Create a pending review record for medium/high risk routing."""

    if not should_create_risk_review(risk_result):
        return None

    timestamp = now_iso()
    review_id = new_id("risk_review")
    matched_categories = risk_result.get("matched_categories", []) if risk_result else []
    conn.execute(
        """
        INSERT INTO risk_review_records (
            id, user_id, source_type, source_id, risk_level,
            matched_categories_json, review_status, created_at, updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, 'pending', ?, ?)
        """,
        (
            review_id,
            user_id,
            source_type,
            source_id,
            risk_result.get("risk_level", "low") if risk_result else "low",
            json_dumps(matched_categories),
            timestamp,
            timestamp,
        ),
    )
    row = conn.execute("SELECT * FROM risk_review_records WHERE id = ?", (review_id,)).fetchone()
    return row_to_dict(row)


def list_risk_review_records(conn: sqlite3.Connection, status: str | None = None, limit: int = 50) -> dict:
    where_sql = ""
    params: list = []
    if status:
        where_sql = "WHERE review_status = ?"
        params.append(status)
    params.append(limit)
    rows = conn.execute(
        f"""
        SELECT * FROM risk_review_records
        {where_sql}
        ORDER BY created_at DESC
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
    review_note: str | None = None,
    action_taken: str | None = None,
    closed_reason: str | None = None,
) -> dict | None:
    if review_status not in REVIEW_STATUSES:
        raise ValueError("review_status 不在支持范围内")

    timestamp = now_iso()
    conn.execute(
        """
        UPDATE risk_review_records
        SET reviewer_id = ?, review_status = ?, review_note = ?,
            action_taken = ?, closed_reason = ?,
            reviewed_at = ?, updated_at = ?
        WHERE id = ?
        """,
        (reviewer_id, review_status, review_note, action_taken, closed_reason, timestamp, timestamp, review_id),
    )
    row = conn.execute("SELECT * FROM risk_review_records WHERE id = ?", (review_id,)).fetchone()
    if row is None:
        return None

    write_audit_log(
        conn,
        action="review_risk",
        actor_id=reviewer_id,
        target_type="risk_review",
        target_id=review_id,
        metadata={
            "review_status": review_status,
            "source_type": row["source_type"],
            "source_id": row["source_id"],
            "risk_level": row["risk_level"],
            "action_taken": action_taken,
            "closed_reason": closed_reason,
        },
    )
    return row_to_dict(row)
