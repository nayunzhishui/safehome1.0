"""Participant draft synchronization for the eight-step assessment flow."""

from __future__ import annotations

from datetime import datetime

from database import get_connection, json_dumps, json_loads, new_id, now_iso, row_to_dict, write_audit_log
from services.therapeutic_assessment_service import (
    TherapeuticAssessmentError,
    _assert_participant,
    _case_row,
    _idempotency,
)


STEP_IDS = {
    "boundary",
    "issue",
    "recent_event",
    "resources",
    "sharing",
    "summary",
    "feedback_check",
    "action_review",
}
STATUSES = {"active", "completed", "discarded"}


def _validate_payload(value, depth: int = 0):
    if depth > 4:
        raise TherapeuticAssessmentError("validation_error", "草稿结构过深。")
    if value is None or isinstance(value, (bool, int, float)):
        return value
    if isinstance(value, str):
        if len(value) > 4000:
            raise TherapeuticAssessmentError("validation_error", "单项草稿不能超过4000字。")
        return value
    if isinstance(value, list):
        if len(value) > 30:
            raise TherapeuticAssessmentError("validation_error", "草稿列表条目过多。")
        return [_validate_payload(item, depth + 1) for item in value]
    if isinstance(value, dict):
        if len(value) > 30:
            raise TherapeuticAssessmentError("validation_error", "草稿字段过多。")
        result = {}
        for key, item in value.items():
            key_text = str(key)
            if len(key_text) > 80 or key_text.startswith("_"):
                raise TherapeuticAssessmentError("validation_error", "草稿字段名称无效。")
            result[key_text] = _validate_payload(item, depth + 1)
        return result
    raise TherapeuticAssessmentError("validation_error", "草稿包含不支持的数据类型。")


def _present(row: dict) -> dict:
    item = dict(row)
    item["payload"] = json_loads(item.pop("payload_json", None), {})
    item.pop("idempotency_key", None)
    return item


def get_draft(actor: dict, case_id: str, step_id: str) -> dict:
    if step_id not in STEP_IDS:
        raise TherapeuticAssessmentError("validation_error", "未知的参与者流程步骤。")
    with get_connection() as conn:
        case = _case_row(conn, case_id)
        _assert_participant(actor, case)
        row = conn.execute(
            """SELECT * FROM therapeutic_assessment_participant_drafts
            WHERE case_id = ? AND participant_user_id = ? AND step_id = ?""",
            (case_id, str(actor["id"]), step_id),
        ).fetchone()
        write_audit_log(
            conn,
            "therapeutic_assessment_draft_viewed",
            str(actor["id"]),
            "therapeutic_assessment_case",
            case_id,
            {"step_id": step_id, "exists": row is not None},
        )
        conn.commit()
        if row is None:
            return {
                "case_id": case_id,
                "participant_user_id": str(actor["id"]),
                "step_id": step_id,
                "payload": {},
                "status": "active",
                "version": 0,
                "updated_at": None,
            }
        return _present(row_to_dict(row))


def save_draft(actor: dict, case_id: str, step_id: str, payload: dict, idempotency_key: str) -> dict:
    if step_id not in STEP_IDS:
        raise TherapeuticAssessmentError("validation_error", "未知的参与者流程步骤。")
    key = _idempotency(idempotency_key)
    expected = payload.get("expected_version")
    status = str(payload.get("status") or "active")
    values = payload.get("payload", {})
    client_updated_at = str(payload.get("client_updated_at") or "").strip()[:64] or None
    if not isinstance(expected, int) or expected < 0 or status not in STATUSES or not isinstance(values, dict):
        raise TherapeuticAssessmentError("validation_error", "草稿版本、状态或内容无效。")
    if client_updated_at:
        try:
            datetime.fromisoformat(client_updated_at.replace("Z", "+00:00"))
        except ValueError as exc:
            raise TherapeuticAssessmentError("validation_error", "客户端更新时间格式无效。") from exc
    clean = _validate_payload(values)
    timestamp = now_iso()
    actor_id = str(actor["id"])
    with get_connection() as conn:
        case = _case_row(conn, case_id)
        _assert_participant(actor, case)
        if case["status"] == "withdrawn" or case["consent_status"] == "withdrawn":
            raise TherapeuticAssessmentError("withdrawn", "本次协作已撤回，草稿不能继续同步。", 409)
        replay = conn.execute(
            """SELECT d.* FROM therapeutic_assessment_participant_draft_events e
            JOIN therapeutic_assessment_participant_drafts d ON d.id = e.draft_id
            WHERE e.participant_user_id = ? AND e.idempotency_key = ?""",
            (actor_id, key),
        ).fetchone()
        if replay is not None:
            if str(replay["case_id"]) != case_id or str(replay["step_id"]) != step_id:
                raise TherapeuticAssessmentError("idempotency_conflict", "该提交标识已用于其它草稿。", 409)
            return _present(row_to_dict(replay))
        current = conn.execute(
            """SELECT * FROM therapeutic_assessment_participant_drafts
            WHERE case_id = ? AND participant_user_id = ? AND step_id = ?""",
            (case_id, actor_id, step_id),
        ).fetchone()
        current_version = int(current["version"]) if current is not None else 0
        if current_version != expected:
            raise TherapeuticAssessmentError(
                "version_conflict",
                "另一台设备已更新这份草稿，请先重新读取。",
                409,
                details={"current_version": current_version},
            )
        if current is None:
            draft_id = new_id("ta_draft")
            conn.execute(
                """INSERT INTO therapeutic_assessment_participant_drafts
                (id, case_id, participant_user_id, step_id, payload_json, client_updated_at,
                 status, version, idempotency_key, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?, ?, ?)""",
                (draft_id, case_id, actor_id, step_id, json_dumps(clean), client_updated_at, status, key, timestamp, timestamp),
            )
        else:
            draft_id = str(current["id"])
            cursor = conn.execute(
                """UPDATE therapeutic_assessment_participant_drafts
                SET payload_json = ?, client_updated_at = ?, status = ?, version = version + 1,
                    idempotency_key = ?, updated_at = ?
                WHERE id = ? AND version = ?""",
                (json_dumps(clean), client_updated_at, status, key, timestamp, draft_id, expected),
            )
            if cursor.rowcount != 1:
                raise TherapeuticAssessmentError("version_conflict", "草稿已更新，请重新读取。", 409)
        result_version = current_version + 1
        conn.execute(
            """INSERT INTO therapeutic_assessment_participant_draft_events
            (id, draft_id, participant_user_id, action, result_version, idempotency_key, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (new_id("ta_draft_event"), draft_id, actor_id, status, result_version, key, timestamp),
        )
        write_audit_log(
            conn,
            "therapeutic_assessment_draft_saved",
            actor_id,
            "therapeutic_assessment_case",
            case_id,
            {"step_id": step_id, "status": status},
        )
        conn.commit()
        return _present(row_to_dict(conn.execute(
            "SELECT * FROM therapeutic_assessment_participant_drafts WHERE id = ?",
            (draft_id,),
        ).fetchone()))
