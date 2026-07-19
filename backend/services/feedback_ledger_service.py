"""Append-only participant evaluations for feedback and recommendations."""

from __future__ import annotations

from dataclasses import dataclass

from database import get_connection, new_id, now_iso, row_to_dict, rows_to_dicts, write_audit_log


EVALUATIONS = {"matches", "partly_matches", "does_not_match", "uncomfortable"}
SOURCE_TABLES = {
    "instant_feedback": ("feedback_results", "user_id"),
    "stage_report": ("relationship_screening_reports", "user_id"),
    "message": ("messages", "user_id"),
}


@dataclass
class FeedbackLedgerError(Exception):
    code: str
    message: str
    status: int = 400

    def __str__(self) -> str:
        return self.message


def _public(item: dict, *, include_reason: bool = True) -> dict:
    fields = {
        "id",
        "user_id",
        "source_type",
        "source_id",
        "content_version",
        "evaluation",
        "reason_code",
        "review_status",
        "status",
        "created_at",
        "updated_at",
    }
    if include_reason:
        fields.add("reason_text")
    result = {key: item.get(key) for key in fields}
    result["requires_human_review"] = item.get("evaluation") == "uncomfortable"
    result["stop_reinforcement"] = item.get("evaluation") in {"does_not_match", "uncomfortable"}
    if item.get("already_recorded"):
        result["already_recorded"] = True
    return result


def _ensure_source_owner(conn, user_id: str, source_type: str, source_id: str) -> None:
    if source_type == "training_recommendation":
        row = conn.execute("SELECT id FROM training_cards WHERE id = ? AND enabled = 1", (source_id,)).fetchone()
    else:
        table_info = SOURCE_TABLES.get(source_type)
        if table_info is None:
            raise FeedbackLedgerError("validation_error", "不支持的反馈来源。")
        table, owner_column = table_info
        row = conn.execute(
            f"SELECT id FROM {table} WHERE id = ? AND {owner_column} = ?",
            (source_id, user_id),
        ).fetchone()
    if row is None:
        raise FeedbackLedgerError("not_found", "没有找到可评价的内容。", status=404)


def create_feedback_entry(user_id: str, payload: dict, idempotency_key: str = "") -> tuple[dict, int]:
    source_type = str(payload.get("source_type") or "").strip()
    source_id = str(payload.get("source_id") or "").strip()
    content_version = str(payload.get("content_version") or "").strip()
    evaluation = str(payload.get("evaluation") or "").strip()
    reason_code = str(payload.get("reason_code") or "").strip()
    reason_text = str(payload.get("reason_text") or "").strip()
    idempotency_key = str(idempotency_key or payload.get("idempotency_key") or "").strip()

    if not source_id or len(source_id) > 160:
        raise FeedbackLedgerError("validation_error", "缺少有效的评价来源。")
    if not content_version or len(content_version) > 120:
        raise FeedbackLedgerError("validation_error", "缺少有效的内容版本。")
    if evaluation not in EVALUATIONS:
        raise FeedbackLedgerError("validation_error", "请选择符合、部分符合、不符合或让我不舒服。")
    if len(reason_code) > 80 or len(reason_text) > 500 or len(idempotency_key) > 120:
        raise FeedbackLedgerError("validation_error", "评价补充内容过长。")

    timestamp = now_iso()
    with get_connection() as conn:
        _ensure_source_owner(conn, user_id, source_type, source_id)
        if idempotency_key:
            existing = conn.execute(
                "SELECT * FROM feedback_ledger WHERE user_id = ? AND idempotency_key = ?",
                (user_id, idempotency_key),
            ).fetchone()
            if existing:
                item = row_to_dict(existing)
                expected = {
                    "source_type": source_type,
                    "source_id": source_id,
                    "content_version": content_version,
                    "evaluation": evaluation,
                    "reason_code": reason_code or None,
                    "reason_text": reason_text or None,
                }
                if any(str(item.get(key) or "") != str(value or "") for key, value in expected.items()):
                    raise FeedbackLedgerError("idempotency_conflict", "该幂等键已用于另一条评价。", status=409)
                item["already_recorded"] = True
                return _public(item), 200

        conn.execute(
            """
            UPDATE feedback_ledger
            SET status = 'superseded', updated_at = ?
            WHERE user_id = ? AND source_type = ? AND source_id = ? AND status = 'active'
            """,
            (timestamp, user_id, source_type, source_id),
        )
        entry_id = new_id("feedback-ledger")
        review_status = "pending_review" if evaluation == "uncomfortable" else "recorded"
        conn.execute(
            """
            INSERT INTO feedback_ledger (
                id, user_id, source_type, source_id, content_version, evaluation,
                reason_code, reason_text, review_status, status, idempotency_key,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'active', ?, ?, ?)
            """,
            (
                entry_id,
                user_id,
                source_type,
                source_id,
                content_version,
                evaluation,
                reason_code or None,
                reason_text or None,
                review_status,
                idempotency_key or None,
                timestamp,
                timestamp,
            ),
        )
        write_audit_log(
            conn,
            "participant_feedback_evaluated",
            user_id,
            "feedback_ledger",
            entry_id,
            {
                "source_type": source_type,
                "source_id": source_id,
                "evaluation": evaluation,
                "requires_human_review": evaluation == "uncomfortable",
            },
        )
        conn.commit()
        item = row_to_dict(conn.execute("SELECT * FROM feedback_ledger WHERE id = ?", (entry_id,)).fetchone())
    return _public(item), 201


def list_feedback_entries(user_id: str, source_type: str = "", source_id: str = "") -> list[dict]:
    where = ["user_id = ?"]
    params: list = [user_id]
    if source_type:
        where.append("source_type = ?")
        params.append(source_type)
    if source_id:
        where.append("source_id = ?")
        params.append(source_id)
    with get_connection() as conn:
        rows = conn.execute(
            f"SELECT * FROM feedback_ledger WHERE {' AND '.join(where)} ORDER BY created_at DESC",
            params,
        ).fetchall()
    return [_public(item) for item in rows_to_dicts(rows)]


def researcher_feedback_summary(actor: dict, user_id: str) -> dict:
    if not user_id:
        raise FeedbackLedgerError("validation_error", "请指定参与者 user_id。")
    with get_connection() as conn:
        if actor.get("role") == "researcher":
            assigned = conn.execute(
                """
                SELECT id FROM relationship_pilot_enrollments
                WHERE user_id = ? AND assigned_researcher_id = ? AND status = 'enrolled'
                LIMIT 1
                """,
                (user_id, actor.get("id")),
            ).fetchone()
            if assigned is None:
                raise FeedbackLedgerError("forbidden", "只能查看已分配参与者的评价摘要。", status=403)
        rows = rows_to_dicts(
            conn.execute(
                "SELECT source_type, evaluation, review_status FROM feedback_ledger WHERE user_id = ? AND status = 'active'",
                (user_id,),
            ).fetchall()
        )
        legacy_checkins = rows_to_dicts(
            conn.execute(
                """
                SELECT helpfulness_rating AS evaluation, COUNT(*) AS count
                FROM checkins WHERE user_id = ? AND helpfulness_rating IS NOT NULL
                GROUP BY helpfulness_rating
                """,
                (user_id,),
            ).fetchall()
        )
        legacy_hypotheses = rows_to_dicts(
            conn.execute(
                """
                SELECT response AS evaluation, COUNT(*) AS count
                FROM relationship_hypothesis_feedback WHERE user_id = ?
                GROUP BY response
                """,
                (user_id,),
            ).fetchall()
        )

    evaluation_counts = {value: 0 for value in sorted(EVALUATIONS)}
    source_counts: dict[str, int] = {}
    pending_review_count = 0
    for row in rows:
        evaluation_counts[row["evaluation"]] = evaluation_counts.get(row["evaluation"], 0) + 1
        source_counts[row["source_type"]] = source_counts.get(row["source_type"], 0) + 1
        if row["review_status"] == "pending_review":
            pending_review_count += 1
    return {
        "user_id": user_id,
        "evaluation_counts": evaluation_counts,
        "source_counts": source_counts,
        "pending_review_count": pending_review_count,
        "legacy_sources": {
            "checkins": legacy_checkins,
            "relationship_hypotheses": legacy_hypotheses,
        },
        "boundary_notice": "摘要只用于共同修订反馈与练习建议，不用于诊断或风险推断。",
    }
