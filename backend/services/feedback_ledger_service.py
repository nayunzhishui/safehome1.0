"""Append-only participant evaluations for feedback and recommendations."""

from __future__ import annotations

from dataclasses import dataclass

from database import get_connection, new_id, now_iso, row_to_dict, rows_to_dicts, write_audit_log


EVALUATIONS = {"matches", "partly_matches", "does_not_match", "uncomfortable"}
LEDGER_ACTIONS = {"withdraw", "correct"}
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
        "supersedes_id",
        "participant_status",
        "withdrawn_at",
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


def _normalize_feedback_payload(payload: dict, *, source_type: str = "", source_id: str = "") -> dict:
    values = {
        "source_type": str(source_type or payload.get("source_type") or "").strip(),
        "source_id": str(source_id or payload.get("source_id") or "").strip(),
        "content_version": str(payload.get("content_version") or "").strip(),
        "evaluation": str(payload.get("evaluation") or "").strip(),
        "reason_code": str(payload.get("reason_code") or "").strip(),
        "reason_text": str(payload.get("reason_text") or "").strip(),
    }
    if not values["source_id"] or len(values["source_id"]) > 160:
        raise FeedbackLedgerError("validation_error", "缺少有效的评价来源。")
    if not values["content_version"] or len(values["content_version"]) > 120:
        raise FeedbackLedgerError("validation_error", "缺少有效的内容版本。")
    if values["evaluation"] not in EVALUATIONS:
        raise FeedbackLedgerError("validation_error", "请选择符合、部分符合、不符合或让我不舒服。")
    if len(values["reason_code"]) > 80 or len(values["reason_text"]) > 500:
        raise FeedbackLedgerError("validation_error", "评价补充内容过长。")
    return values


def _insert_feedback_entry(conn, user_id: str, values: dict, *, idempotency_key: str, supersedes_id: str | None = None) -> str:
    timestamp = now_iso()
    entry_id = new_id("feedback-ledger")
    review_status = "pending_review" if values["evaluation"] == "uncomfortable" else "recorded"
    conn.execute(
        """
        INSERT INTO feedback_ledger (
            id, user_id, source_type, source_id, content_version, evaluation,
            reason_code, reason_text, review_status, status, supersedes_id,
            participant_status, idempotency_key, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'active', ?, 'visible', ?, ?, ?)
        """,
        (
            entry_id,
            user_id,
            values["source_type"],
            values["source_id"],
            values["content_version"],
            values["evaluation"],
            values["reason_code"] or None,
            values["reason_text"] or None,
            review_status,
            supersedes_id,
            idempotency_key or None,
            timestamp,
            timestamp,
        ),
    )
    return entry_id


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
    values = _normalize_feedback_payload(payload)
    source_type = values["source_type"]
    source_id = values["source_id"]
    idempotency_key = str(idempotency_key or payload.get("idempotency_key") or "").strip()
    if len(idempotency_key) > 120:
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
                    "content_version": values["content_version"],
                    "evaluation": values["evaluation"],
                    "reason_code": values["reason_code"] or None,
                    "reason_text": values["reason_text"] or None,
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
        entry_id = _insert_feedback_entry(conn, user_id, values, idempotency_key=idempotency_key)
        write_audit_log(
            conn,
            "participant_feedback_evaluated",
            user_id,
            "feedback_ledger",
            entry_id,
            {
                "source_type": source_type,
                "source_id": source_id,
                "evaluation": values["evaluation"],
                "requires_human_review": values["evaluation"] == "uncomfortable",
            },
        )
        if values["evaluation"] == "uncomfortable":
            write_audit_log(
                conn,
                "product_event_feedback_discomfort_recorded",
                user_id,
                "product_event",
                entry_id,
                {"event_name": "feedback_discomfort_recorded", "source": "feedback_ledger", "status": "recorded"},
            )
            write_audit_log(
                conn,
                "product_event_human_support_escalated",
                user_id,
                "product_event",
                entry_id,
                {"event_name": "human_support_escalated", "source": "feedback_ledger", "status": "escalated"},
            )
        conn.commit()
        item = row_to_dict(conn.execute("SELECT * FROM feedback_ledger WHERE id = ?", (entry_id,)).fetchone())
    return _public(item), 201


def apply_feedback_action(user_id: str, entry_id: str, payload: dict, idempotency_key: str = "") -> tuple[dict, int]:
    action = str(payload.get("action") or "").strip()
    idempotency_key = str(idempotency_key or payload.get("idempotency_key") or "").strip()
    if action not in LEDGER_ACTIONS:
        raise FeedbackLedgerError("validation_error", "action 仅支持 withdraw 或 correct。")
    if not idempotency_key or len(idempotency_key) > 120:
        raise FeedbackLedgerError("validation_error", "撤回或修订必须提供有效幂等键。")

    with get_connection() as conn:
        existing_action = conn.execute(
            "SELECT * FROM feedback_ledger_actions WHERE user_id = ? AND idempotency_key = ?",
            (user_id, idempotency_key),
        ).fetchone()
        if existing_action:
            recorded = row_to_dict(existing_action)
            if recorded.get("entry_id") != entry_id or recorded.get("action") != action:
                raise FeedbackLedgerError("idempotency_conflict", "该幂等键已用于另一项评价操作。", status=409)
            target_id = recorded.get("replacement_entry_id") or entry_id
            item = row_to_dict(conn.execute("SELECT * FROM feedback_ledger WHERE id = ?", (target_id,)).fetchone())
            item["already_recorded"] = True
            return _public(item), 200

        row = conn.execute(
            "SELECT * FROM feedback_ledger WHERE id = ? AND user_id = ?",
            (entry_id, user_id),
        ).fetchone()
        if row is None:
            raise FeedbackLedgerError("not_found", "没有找到可操作的评价。", status=404)
        current = row_to_dict(row)
        if current.get("status") != "active" or current.get("participant_status") == "withdrawn":
            raise FeedbackLedgerError("state_conflict", "该评价已不是当前有效版本。", status=409)

        timestamp = now_iso()
        replacement_id = None
        to_status = "withdrawn"
        if action == "withdraw":
            conn.execute(
                """
                UPDATE feedback_ledger
                SET status = 'withdrawn', participant_status = 'withdrawn', withdrawn_at = ?, updated_at = ?
                WHERE id = ?
                """,
                (timestamp, timestamp, entry_id),
            )
        else:
            values = _normalize_feedback_payload(
                payload.get("replacement") if isinstance(payload.get("replacement"), dict) else payload,
                source_type=current["source_type"],
                source_id=current["source_id"],
            )
            conn.execute(
                "UPDATE feedback_ledger SET status = 'superseded', participant_status = 'corrected', updated_at = ? WHERE id = ?",
                (timestamp, entry_id),
            )
            replacement_id = _insert_feedback_entry(
                conn,
                user_id,
                values,
                idempotency_key=f"{idempotency_key}:replacement",
                supersedes_id=entry_id,
            )
            to_status = "corrected"

        action_id = new_id("feedback-action")
        conn.execute(
            """
            INSERT INTO feedback_ledger_actions (
                id, entry_id, user_id, action, from_status, to_status,
                replacement_entry_id, idempotency_key, created_at
            ) VALUES (?, ?, ?, ?, 'active', ?, ?, ?, ?)
            """,
            (action_id, entry_id, user_id, action, to_status, replacement_id, idempotency_key, timestamp),
        )
        write_audit_log(
            conn,
            f"participant_feedback_{action}",
            user_id,
            "feedback_ledger",
            entry_id,
            {"action_id": action_id, "replacement_entry_id": replacement_id, "participant_status": to_status},
        )
        conn.commit()
        target_id = replacement_id or entry_id
        item = row_to_dict(conn.execute("SELECT * FROM feedback_ledger WHERE id = ?", (target_id,)).fetchone())
    return _public(item), 200


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
