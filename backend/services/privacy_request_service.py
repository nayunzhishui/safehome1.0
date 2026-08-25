"""State transitions and audit history for privacy requests."""

from __future__ import annotations

import hashlib
import hmac
import json

from flask import current_app

from database import get_connection, json_dumps, json_loads, new_id, now_iso, row_to_dict, rows_to_dicts, write_audit_log
from services.consent_service import (
    append_consent_event,
    is_verified_participant_event,
    latest_consent_event,
)


PRIVACY_REQUEST_STATUSES = {"pending", "processing", "completed", "rejected", "cancelled"}
PRIVACY_HANDLING_SCOPES = {
    "account_identity",
    "participant_records",
    "feedback_and_training",
    "messages_and_notifications",
    "relationship_pilot",
    "research_outputs",
    "therapeutic_assessment",
}
REVIEW_ACTIONS = {"start_processing", "reject", "return_to_pending"}
RESEARCH_CONSENT_TYPES = {"anonymous_research", "research_authorization"}
CONSENT_TYPES_FOR_STATUS = ["user_agreement", "privacy_policy", "non_diagnostic_notice", "anonymous_research", "research_authorization"]

SCOPE_TABLES = {
    "account_identity": (
        "consent_record_annotations",
        "consent_records",
        "family_links",
        "data_claims",
        "ai_capability_decisions",
    ),
    "participant_records": (
        "goals", "emotion_diaries", "emotion_thermometer", "assessment_results",
        "student_profiles", "student_profile_followups", "student_sandplay_entries",
        "parent_assessment_submissions", "parent_report_actions", "risk_review_records",
    ),
    "feedback_and_training": (
        "feedback_results", "feedback_ledger", "feedback_ledger_actions", "recommendation_snapshots",
        "checkins", "weekly_reports", "supervision_requests",
    ),
    "messages_and_notifications": (
        "messages", "notification_preferences", "notification_deliveries",
        "ai_qa_feedback", "ai_qa_messages", "ai_qa_safety_events",
        "ai_qa_provider_events", "ai_qa_sessions",
    ),
    "relationship_pilot": (
        "relationship_pilot_enrollments", "relationship_screening_reports", "relationship_pilot_tasks",
        "relationship_research_notes", "relationship_narratives", "relationship_longitudinal_entries",
        "relationship_hypothesis_feedback",
    ),
    "research_outputs": ("records", "profile_reviews"),
    "therapeutic_assessment": (
        "publication_gate_checks",
        "publication_candidate_events",
        "publication_candidates",
        "therapeutic_assessment_data_consents",
        "therapeutic_assessment_participant_draft_events",
        "therapeutic_assessment_researcher_workbench_draft_events",
        "therapeutic_assessment_quality_events",
        "therapeutic_assessment_queue_events",
        "therapeutic_assessment_feedback_deliveries",
        "therapeutic_assessment_feedback_responses",
        "therapeutic_assessment_evidence_items",
        "therapeutic_assessment_data_items",
        "therapeutic_assessment_participant_drafts",
        "therapeutic_assessment_responsibility_chains",
        "therapeutic_assessment_safety_events",
        "therapeutic_assessment_researcher_workbench_drafts",
        "therapeutic_assessment_quality_reviews",
        "therapeutic_assessment_quality_incidents",
        "therapeutic_assessment_work_queue",
        "therapeutic_assessment_feedback_versions",
        "therapeutic_assessment_events",
        "therapeutic_assessment_actions",
        "therapeutic_assessment_cases",
    ),
}

DIRECT_USER_TABLES = {
    "consent_records", "goals", "emotion_diaries", "emotion_thermometer", "assessment_results",
    "student_profiles", "student_profile_followups", "student_sandplay_entries",
    "parent_assessment_submissions", "risk_review_records", "feedback_results", "feedback_ledger",
    "feedback_ledger_actions", "recommendation_snapshots",
    "checkins", "weekly_reports", "supervision_requests", "messages", "notification_preferences",
    "notification_deliveries", "relationship_pilot_enrollments", "relationship_screening_reports",
    "relationship_pilot_tasks", "relationship_narratives", "relationship_longitudinal_entries",
    "relationship_hypothesis_feedback", "records", "ai_qa_feedback", "ai_qa_messages",
    "ai_qa_safety_events", "ai_qa_provider_events", "ai_qa_sessions",
}


class PrivacyRequestError(ValueError):
    def __init__(self, code: str, message: str, status: int) -> None:
        super().__init__(message)
        self.code = code
        self.status = status


def _latest_consent_status(conn, user_id: str, consent_type: str) -> dict:
    latest = latest_consent_event(conn, user_id, consent_type)
    verified = is_verified_participant_event(latest, user_id)
    agreed = bool(latest and latest.get("agreed") and verified)
    return {
        "user_id": user_id,
        "consent_type": consent_type,
        "agreed": agreed,
        "verification_status": "verified_participant" if verified else (
            "provenance_unknown" if latest else "not_recorded"
        ),
        "consent_version": latest.get("consent_version") if latest else None,
        "purpose": latest.get("purpose") if latest else None,
        "processor": latest.get("processor") if latest else None,
        "source": latest.get("source") if latest else None,
        "event_type": latest.get("event_type") if latest else None,
        "current_record_id": latest.get("id") if latest else None,
        "agreed_at": latest.get("agreed_at") if agreed else None,
        "revoked_at": latest.get("revoked_at") if latest else None,
        "created_at": latest.get("created_at") if latest else None,
    }


def get_participant_consent_status(user_id: str) -> dict:
    with get_connection() as conn:
        items = [_latest_consent_status(conn, user_id, consent_type) for consent_type in CONSENT_TYPES_FOR_STATUS]
    return {"user_id": user_id, "items": items}


def revoke_research_consent(user_id: str, actor: dict, payload: dict, *, default_version: str) -> dict:
    consent_type = str(payload.get("consent_type") or "anonymous_research").strip()
    if consent_type not in RESEARCH_CONSENT_TYPES:
        raise PrivacyRequestError("validation_error", "当前仅支持撤回匿名研究授权", 400)
    reason = str(payload.get("reason") or "用户主动撤回").strip()[:300]
    with get_connection() as conn:
        item, _created = append_consent_event(
            conn,
            actor_id=str(actor["id"]),
            subject_id=user_id,
            consent_type=consent_type,
            consent_version=str(payload.get("consent_version") or default_version),
            agreed=False,
            purpose=payload.get("purpose"),
            processor=str(payload.get("processor") or "safehome"),
            text_hash=payload.get("text_hash"),
            source="participant_self",
            reason=reason,
            expected_latest_id=payload.get("expected_latest_id"),
            require_latest_guard=False,
        )
        for table in ["student_profiles", "student_profile_followups", "student_sandplay_entries", "parent_assessment_submissions", "records"]:
            conn.execute(f"UPDATE {table} SET export_allowed = 0 WHERE user_id = ?", (user_id,))
        write_audit_log(conn, "privacy_revoke_consent", actor["id"], "consent", consent_type, {"route": "/api/privacy/revoke-consent", "reason_length": len(reason), "new_research_processing_blocked": True})
        conn.commit()
    return {
        "user_id": user_id,
        "consent_type": consent_type,
        "agreed": False,
        "revoked_at": item.get("revoked_at"),
        "record_id": item.get("id"),
    }


def create_participant_delete_request(user_id: str, actor: dict, reason: str) -> tuple[dict, int]:
    timestamp = now_iso()
    with get_connection() as conn:
        existing = conn.execute("SELECT id, user_id, request_type, status, created_at, updated_at FROM privacy_requests WHERE user_id = ? AND request_type = 'delete_my_data' AND status IN ('pending', 'processing') ORDER BY created_at DESC LIMIT 1", (user_id,)).fetchone()
        if existing is not None:
            item = row_to_dict(existing)
            item["already_active"] = True
            return item, 200
        request_id = new_id("privacy")
        conn.execute("INSERT INTO privacy_requests (id, user_id, request_type, reason, status, handled_by, handled_note, created_at, updated_at) VALUES (?, ?, 'delete_my_data', ?, 'pending', NULL, NULL, ?, ?)", (request_id, user_id, reason or None, timestamp, timestamp))
        write_audit_log(conn, "privacy_delete_request", actor["id"], "privacy_request", request_id, {"route": "/api/privacy/delete-my-data", "reason_length": len(reason)})
        conn.commit()
        row = conn.execute("SELECT * FROM privacy_requests WHERE id = ?", (request_id,)).fetchone()
    return row_to_dict(row), 201


def list_participant_requests(user_id: str, *, page: int, page_size: int) -> dict:
    offset = (page - 1) * page_size
    with get_connection() as conn:
        total_row = conn.execute("SELECT COUNT(*) AS count FROM privacy_requests WHERE user_id = ?", (user_id,)).fetchone()
        rows = conn.execute("SELECT id, user_id, request_type, status, participant_notice, execution_proof_hash, created_at, updated_at FROM privacy_requests WHERE user_id = ? ORDER BY created_at DESC LIMIT ? OFFSET ?", (user_id, page_size, offset)).fetchall()
    total = int(total_row["count"] if total_row else 0)
    items = rows_to_dicts(rows)
    return {"items": items, "page": page, "page_size": page_size, "total": total, "has_more": offset + len(items) < total}


def revoked_research_user_ids(conn) -> set[str]:
    rows = conn.execute("SELECT * FROM consent_records WHERE consent_type IN (?, ?) ORDER BY user_id ASC, consent_type ASC, event_version DESC, created_at DESC, id DESC", ("anonymous_research", "research_authorization")).fetchall()
    latest_by_key: dict[tuple[str, str], dict] = {}
    for row in rows:
        item = row_to_dict(row)
        latest_by_key.setdefault((item["user_id"], item["consent_type"]), item)
    return {
        user_id
        for (user_id, _), item in latest_by_key.items()
        if not item.get("agreed") or not is_verified_participant_event(item, user_id)
    }


def research_revoked_filter(conn, column: str = "user_id") -> tuple[str, list[str]]:
    revoked_ids = sorted(revoked_research_user_ids(conn))
    if not revoked_ids:
        return "", []
    placeholders = ",".join("?" for _ in revoked_ids)
    return f"{column} NOT IN ({placeholders})", revoked_ids


def export_participant_privacy_summary(user_id: str) -> dict:
    def count_for_user(conn, table: str) -> int:
        row = conn.execute(f"SELECT COUNT(*) AS count FROM {table} WHERE user_id = ?", (user_id,)).fetchone()
        return int(row["count"]) if row else 0

    with get_connection() as conn:
        privacy_rows = conn.execute("SELECT id, request_type, status, created_at, updated_at FROM privacy_requests WHERE user_id = ? ORDER BY created_at DESC", (user_id,)).fetchall()
        consent_rows = rows_to_dicts(
            conn.execute(
                """
                SELECT * FROM consent_records
                WHERE COALESCE(subject_id, user_id) = ?
                ORDER BY created_at DESC, id DESC
                """,
                (user_id,),
            ).fetchall()
        )
        annotations = rows_to_dicts(
            conn.execute(
                "SELECT * FROM consent_record_annotations WHERE subject_id = ? ORDER BY created_at DESC, id DESC",
                (user_id,),
            ).fetchall()
        )
        annotations_by_record: dict[str, list[dict]] = {}
        for annotation in annotations:
            annotations_by_record.setdefault(annotation["consent_record_id"], []).append(annotation)
        for consent in consent_rows:
            consent["annotations"] = annotations_by_record.get(consent["id"], [])
        return {
            "user_id": user_id,
            "counts": {
                "goals": count_for_user(conn, "goals"),
                "diaries": count_for_user(conn, "emotion_diaries"),
                "feedback": count_for_user(conn, "feedback_results"),
                "checkins": count_for_user(conn, "checkins"),
                "profiles": count_for_user(conn, "student_profiles"),
                "parent_assessments": count_for_user(conn, "parent_assessment_submissions"),
                "supervision": count_for_user(conn, "supervision_requests"),
                "ai_qa_sessions": count_for_user(conn, "ai_qa_sessions"),
                "ai_capability_decisions": _count(
                    conn,
                    "SELECT COUNT(*) AS count FROM ai_capability_decisions WHERE actor_id = ?",
                    (user_id,),
                ),
            },
            "consent_status": [_latest_consent_status(conn, user_id, consent_type) for consent_type in CONSENT_TYPES_FOR_STATUS],
            "consent_history": consent_rows,
            "privacy_requests": rows_to_dicts(privacy_rows),
            "boundary_notice": "该摘要不包含自由文本原文、联系方式、后台审计 metadata 或风险处置私密备注。",
        }


def participant_view(item: dict, *, already_processed: bool = False) -> dict:
    return {
        "id": item["id"],
        "user_id": item["user_id"],
        "request_type": item["request_type"],
        "status": item["status"],
        "created_at": item["created_at"],
        "updated_at": item["updated_at"],
        "participant_notice": item.get("participant_notice"),
        "execution_proof_hash": item.get("execution_proof_hash"),
        "already_processed": already_processed,
    }


def _idempotent_replay(conn, request_id: str, actor_id: str, action: str, idempotency_key: str) -> dict | None:
    row = conn.execute(
        "SELECT * FROM privacy_request_actions WHERE actor_id = ? AND idempotency_key = ?",
        (actor_id, idempotency_key),
    ).fetchone()
    if row is None:
        return None
    existing = row_to_dict(row)
    if existing["request_id"] != request_id or existing["action"] != action:
        raise PrivacyRequestError("idempotency_conflict", "该幂等键已用于其他隐私操作。", 409)
    current = conn.execute("SELECT * FROM privacy_requests WHERE id = ?", (request_id,)).fetchone()
    if current is None:
        raise PrivacyRequestError("not_found", "没有找到该隐私申请。", 404)
    return row_to_dict(current)


def cancel_participant_request(request_id: str, actor: dict, idempotency_key: str, note: str) -> dict:
    if not idempotency_key:
        raise PrivacyRequestError("validation_error", "取消申请需要提供 Idempotency-Key。", 400)
    actor_id = str(actor["id"])
    timestamp = now_iso()
    with get_connection() as conn:
        replay = _idempotent_replay(conn, request_id, actor_id, "participant_cancel", idempotency_key)
        if replay is not None:
            return participant_view(replay, already_processed=True)

        row = conn.execute(
            "SELECT * FROM privacy_requests WHERE id = ? AND user_id = ?",
            (request_id, actor_id),
        ).fetchone()
        if row is None:
            raise PrivacyRequestError("not_found", "没有找到可取消的隐私申请。", 404)
        item = row_to_dict(row)
        if item["status"] != "pending":
            raise PrivacyRequestError("invalid_transition", "只有待处理的申请可以由参与者取消。", 409)

        cursor = conn.execute(
            """
            UPDATE privacy_requests
            SET status = 'cancelled', decision = 'cancelled_by_participant',
                handled_at = ?, updated_at = ?, version = version + 1
            WHERE id = ? AND user_id = ? AND status = 'pending' AND version = ?
            """,
            (timestamp, timestamp, request_id, actor_id, int(item.get("version") or 0)),
        )
        if cursor.rowcount != 1:
            raise PrivacyRequestError("state_conflict", "申请状态刚刚发生变化，请刷新后重试。", 409)
        conn.execute(
            """
            INSERT INTO privacy_request_actions (
                id, request_id, actor_id, actor_role, action, from_status, to_status,
                scope_json, note, idempotency_key, created_at
            ) VALUES (?, ?, ?, ?, 'participant_cancel', 'pending', 'cancelled', '[]', ?, ?, ?)
            """,
            (new_id("privacy_action"), request_id, actor_id, str(actor.get("role") or "participant"), note or None, idempotency_key, timestamp),
        )
        write_audit_log(
            conn,
            "privacy_request_cancelled",
            actor_id,
            "privacy_request",
            request_id,
            {"from_status": "pending", "to_status": "cancelled", "note_length": len(note)},
        )
        conn.commit()
        updated = conn.execute("SELECT * FROM privacy_requests WHERE id = ?", (request_id,)).fetchone()
    return participant_view(row_to_dict(updated))


def appeal_participant_request(request_id: str, actor: dict, idempotency_key: str, reason: str) -> dict:
    if not idempotency_key:
        raise PrivacyRequestError("validation_error", "重新提交需要提供 Idempotency-Key。", 400)
    if not reason or len(reason) > 500:
        raise PrivacyRequestError("validation_error", "请填写不超过500字的补充说明。", 400)
    actor_id = str(actor["id"])
    timestamp = now_iso()
    with get_connection() as conn:
        replay = _idempotent_replay(conn, request_id, actor_id, "participant_appeal", idempotency_key)
        if replay is not None:
            return participant_view(replay, already_processed=True)
        row = conn.execute(
            "SELECT * FROM privacy_requests WHERE id = ? AND user_id = ?", (request_id, actor_id)
        ).fetchone()
        if row is None:
            raise PrivacyRequestError("not_found", "没有找到可重新提交的隐私申请。", 404)
        item = row_to_dict(row)
        if item["status"] != "rejected":
            raise PrivacyRequestError("invalid_transition", "只有已退回的申请可以补充说明后重新提交。", 409)
        cursor = conn.execute(
            """
            UPDATE privacy_requests
            SET status = 'pending', reason = ?, handled_by = NULL, handled_note = NULL,
                handling_scope_json = '[]', decision = NULL, processing_started_at = NULL,
                handled_at = NULL, participant_notice = NULL, updated_at = ?, version = version + 1
            WHERE id = ? AND user_id = ? AND status = 'rejected' AND version = ?
            """,
            (reason, timestamp, request_id, actor_id, int(item.get("version") or 0)),
        )
        if cursor.rowcount != 1:
            raise PrivacyRequestError("state_conflict", "申请状态刚刚发生变化，请刷新后重试。", 409)
        conn.execute(
            """
            INSERT INTO privacy_request_actions (
                id, request_id, actor_id, actor_role, action, from_status, to_status,
                scope_json, note, idempotency_key, created_at
            ) VALUES (?, ?, ?, ?, 'participant_appeal', 'rejected', 'pending', '[]', ?, ?, ?)
            """,
            (new_id("privacy_action"), request_id, actor_id, str(actor.get("role") or "participant"), reason, idempotency_key, timestamp),
        )
        write_audit_log(conn, "privacy_request_appealed", actor_id, "privacy_request", request_id, {"reason_length": len(reason)})
        conn.commit()
        updated = conn.execute("SELECT * FROM privacy_requests WHERE id = ?", (request_id,)).fetchone()
    return participant_view(row_to_dict(updated))


def list_reviewer_requests(actor: dict, *, status: str, page: int, page_size: int) -> dict:
    if status and status not in PRIVACY_REQUEST_STATUSES:
        raise PrivacyRequestError("validation_error", "不支持的隐私申请状态。", 400)
    offset = (page - 1) * page_size
    where = "WHERE status = ?" if status else ""
    params: list[object] = [status] if status else []
    with get_connection() as conn:
        total_row = conn.execute(
            f"SELECT COUNT(*) AS count FROM privacy_requests {where}",
            tuple(params),
        ).fetchone()
        rows = conn.execute(
            f"""
            SELECT id, user_id, request_type, status, handled_by,
                   processing_started_at, handled_at, created_at, updated_at, version
            FROM privacy_requests
            {where}
            ORDER BY CASE status WHEN 'pending' THEN 0 WHEN 'processing' THEN 1 ELSE 2 END,
                     created_at ASC, id ASC
            LIMIT ? OFFSET ?
            """,
            tuple([*params, page_size, offset]),
        ).fetchall()
        write_audit_log(
            conn,
            "privacy_request_queue_viewed",
            str(actor["id"]),
            "privacy_request_queue",
            status or "all",
            {"page": page, "page_size": page_size, "result_count": len(rows)},
        )
        conn.commit()
    total = int(total_row["count"] if total_row else 0)
    return {
        "items": rows_to_dicts(rows),
        "page": page,
        "page_size": page_size,
        "total": total,
        "has_more": offset + len(rows) < total,
        "boundary_notice": "列表只展示申请状态和处理标识；申请原因与内部备注需进入详情并记录审计后查看。",
    }


def get_reviewer_request(request_id: str, actor: dict) -> dict:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM privacy_requests WHERE id = ?", (request_id,)).fetchone()
        if row is None:
            raise PrivacyRequestError("not_found", "没有找到该隐私申请。", 404)
        actions = conn.execute(
            """
            SELECT id, actor_id, actor_role, action, from_status, to_status,
                   scope_json, note, created_at
            FROM privacy_request_actions
            WHERE request_id = ?
            ORDER BY created_at ASC, id ASC
            """,
            (request_id,),
        ).fetchall()
        approvals = conn.execute(
            "SELECT actor_id, actor_role, scope_hash, policy_version, decision, created_at FROM privacy_request_approvals WHERE request_id = ? ORDER BY created_at, id",
            (request_id,),
        ).fetchall()
        executions = conn.execute(
            "SELECT id, actor_id, environment, mode, policy_version, scope_hash, status, proof_hash, started_at, completed_at FROM privacy_request_executions WHERE request_id = ? ORDER BY started_at, id",
            (request_id,),
        ).fetchall()
        write_audit_log(
            conn,
            "privacy_request_detail_viewed",
            str(actor["id"]),
            "privacy_request",
            request_id,
            {"status": row["status"], "reason_present": bool(row["reason"])},
        )
        conn.commit()
    request_item = row_to_dict(row)
    request_item["handling_scope"] = json_loads(request_item.pop("handling_scope_json", None), [])
    action_items = rows_to_dicts(actions)
    for action in action_items:
        action["scope"] = json_loads(action.pop("scope_json", None), [])
    return {
        "request": request_item,
        "actions": action_items,
        "approvals": rows_to_dicts(approvals),
        "executions": rows_to_dicts(executions),
        "allowed_scopes": sorted(PRIVACY_HANDLING_SCOPES),
        "boundary_notice": "申请原因和处理备注仅用于受控隐私处理，不得复制到普通研究记录或导出文件。",
    }


def _validate_scope(scope: object, *, required: bool) -> list[str]:
    if not isinstance(scope, list):
        if required:
            raise PrivacyRequestError("validation_error", "处理范围必须是数组。", 400)
        return []
    normalized = list(dict.fromkeys(str(item).strip() for item in scope if str(item).strip()))
    invalid = [item for item in normalized if item not in PRIVACY_HANDLING_SCOPES]
    if invalid:
        raise PrivacyRequestError("validation_error", f"包含不支持的处理范围：{invalid[0]}。", 400)
    if required and not normalized:
        raise PrivacyRequestError("validation_error", "开始处理前必须选择至少一个处理范围。", 400)
    return normalized


def transition_reviewer_request(
    request_id: str,
    actor: dict,
    *,
    action: str,
    scope: object,
    note: str,
    idempotency_key: str,
) -> dict:
    if action not in REVIEW_ACTIONS:
        if action == "mark_completed":
            raise PrivacyRequestError("execution_required", "删除申请只能由T24-03受控执行器完成。", 409)
        raise PrivacyRequestError("validation_error", "不支持的处理动作。", 400)
    if not idempotency_key:
        raise PrivacyRequestError("validation_error", "处理申请需要提供 Idempotency-Key。", 400)
    if len(note) > 1000:
        raise PrivacyRequestError("validation_error", "处理备注不能超过1000字。", 400)
    if action in {"reject", "return_to_pending"} and not note:
        raise PrivacyRequestError("validation_error", "该处理动作必须填写备注。", 400)
    normalized_scope = _validate_scope(scope, required=action == "start_processing")
    actor_id = str(actor["id"])
    actor_role = str(actor.get("role") or "")
    timestamp = now_iso()

    with get_connection() as conn:
        replay = _idempotent_replay(conn, request_id, actor_id, action, idempotency_key)
        if replay is not None:
            result = get_reviewer_request(request_id, actor)
            result["already_processed"] = True
            return result

        row = conn.execute("SELECT * FROM privacy_requests WHERE id = ?", (request_id,)).fetchone()
        if row is None:
            raise PrivacyRequestError("not_found", "没有找到该隐私申请。", 404)
        item = row_to_dict(row)
        from_status = str(item["status"])
        handled_by = str(item.get("handled_by") or "")
        if from_status == "processing" and handled_by and handled_by != actor_id and actor_role != "admin":
            raise PrivacyRequestError("processing_conflict", "该申请已由其他处理人领取。", 409)

        transition = {
            "start_processing": ({"pending"}, "processing"),
            "reject": ({"pending", "processing"}, "rejected"),
            "return_to_pending": ({"processing"}, "pending"),
        }[action]
        allowed_from, to_status = transition
        if from_status not in allowed_from:
            raise PrivacyRequestError("invalid_transition", f"申请当前为{from_status}，不能执行该操作。", 409)

        stored_scope = normalized_scope or json_loads(item.get("handling_scope_json"), [])
        next_handled_by = actor_id if to_status in {"processing", "rejected"} else None
        next_processing_started = timestamp if action == "start_processing" else item.get("processing_started_at")
        next_handled_at = timestamp if to_status == "rejected" else None
        decision = "rejected" if to_status == "rejected" else None
        participant_notice = "当前申请暂不能继续处理。你可以补充说明后重新提交；如需帮助，可联系项目支持人员。" if to_status == "rejected" else None
        cursor = conn.execute(
            """
            UPDATE privacy_requests
            SET status = ?, handled_by = ?, handled_note = ?, handling_scope_json = ?,
                decision = ?, processing_started_at = ?, handled_at = ?, participant_notice = ?,
                updated_at = ?, version = version + 1
            WHERE id = ? AND status = ? AND version = ?
            """,
            (
                to_status,
                next_handled_by,
                note or None,
                json_dumps(stored_scope),
                decision,
                next_processing_started,
                next_handled_at,
                participant_notice,
                timestamp,
                request_id,
                from_status,
                int(item.get("version") or 0),
            ),
        )
        if cursor.rowcount != 1:
            raise PrivacyRequestError("state_conflict", "申请状态刚刚发生变化，请刷新后重试。", 409)
        conn.execute(
            """
            INSERT INTO privacy_request_actions (
                id, request_id, actor_id, actor_role, action, from_status, to_status,
                scope_json, note, idempotency_key, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                new_id("privacy_action"),
                request_id,
                actor_id,
                actor_role,
                action,
                from_status,
                to_status,
                json_dumps(stored_scope),
                note or None,
                idempotency_key,
                timestamp,
            ),
        )
        write_audit_log(
            conn,
            "privacy_request_transitioned",
            actor_id,
            "privacy_request",
            request_id,
            {
                "action": action,
                "from_status": from_status,
                "to_status": to_status,
                "scope": stored_scope,
                "note_length": len(note),
            },
        )
        conn.commit()
    return get_reviewer_request(request_id, actor)


def _load_policy() -> dict:
    path = current_app.config["CONTENT_DIR"] / "privacy_retention_policy.json"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PrivacyRequestError("policy_unavailable", "隐私保存策略不可用，执行已停止。", 503) from exc
    if not payload.get("policy_version") or not isinstance(payload.get("retained_categories"), list):
        raise PrivacyRequestError("policy_invalid", "隐私保存策略缺少必要字段，执行已停止。", 503)
    return payload


def _stable_hash(payload: object) -> str:
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _count(conn, sql: str, params: tuple) -> int:
    row = conn.execute(sql, params).fetchone()
    return int(row["count"] if row else 0)


def _table_count(conn, table: str, user_id: str) -> int:
    if table == "ai_capability_decisions":
        return _count(
            conn,
            "SELECT COUNT(*) AS count FROM ai_capability_decisions WHERE actor_id = ?",
            (user_id,),
        )
    if table in DIRECT_USER_TABLES:
        return _count(conn, f"SELECT COUNT(*) AS count FROM {table} WHERE user_id = ?", (user_id,))
    if table == "family_links":
        return _count(conn, "SELECT COUNT(*) AS count FROM family_links WHERE parent_user_id = ? OR student_user_id = ?", (user_id, user_id))
    if table == "data_claims":
        return _count(conn, "SELECT COUNT(*) AS count FROM data_claims WHERE target_user_id = ?", (user_id,))
    if table == "consent_record_annotations":
        return _count(conn, "SELECT COUNT(*) AS count FROM consent_record_annotations WHERE subject_id = ?", (user_id,))
    if table == "parent_report_actions":
        return _count(conn, "SELECT COUNT(*) AS count FROM parent_report_actions WHERE submission_id IN (SELECT id FROM parent_assessment_submissions WHERE user_id = ?)", (user_id,))
    if table == "profile_reviews":
        return _count(conn, "SELECT COUNT(*) AS count FROM profile_reviews WHERE profile_id IN (SELECT id FROM student_profiles WHERE user_id = ?)", (user_id,))
    if table == "relationship_research_notes":
        return _count(conn, "SELECT COUNT(*) AS count FROM relationship_research_notes WHERE enrollment_id IN (SELECT id FROM relationship_pilot_enrollments WHERE user_id = ?)", (user_id,))
    case_linked_tables = {
        "therapeutic_assessment_feedback_versions",
        "therapeutic_assessment_feedback_deliveries",
        "therapeutic_assessment_feedback_responses",
        "therapeutic_assessment_evidence_items",
        "therapeutic_assessment_data_items",
        "therapeutic_assessment_participant_drafts",
        "therapeutic_assessment_responsibility_chains",
        "therapeutic_assessment_safety_events",
        "therapeutic_assessment_researcher_workbench_drafts",
        "therapeutic_assessment_quality_reviews",
        "therapeutic_assessment_quality_incidents",
        "therapeutic_assessment_work_queue",
        "therapeutic_assessment_events",
    }
    if table in case_linked_tables:
        return _count(
            conn,
            f"SELECT COUNT(*) AS count FROM {table} WHERE case_id IN (SELECT id FROM therapeutic_assessment_cases WHERE participant_user_id = ?)",
            (user_id,),
        )
    if table == "therapeutic_assessment_data_consents":
        return _count(
            conn,
            "SELECT COUNT(*) AS count FROM therapeutic_assessment_data_consents WHERE data_item_id IN (SELECT id FROM therapeutic_assessment_data_items WHERE case_id IN (SELECT id FROM therapeutic_assessment_cases WHERE participant_user_id = ?))",
            (user_id,),
        )
    if table == "therapeutic_assessment_participant_draft_events":
        return _count(
            conn,
            "SELECT COUNT(*) AS count FROM therapeutic_assessment_participant_draft_events WHERE draft_id IN (SELECT id FROM therapeutic_assessment_participant_drafts WHERE case_id IN (SELECT id FROM therapeutic_assessment_cases WHERE participant_user_id = ?))",
            (user_id,),
        )
    if table == "therapeutic_assessment_researcher_workbench_draft_events":
        return _count(
            conn,
            "SELECT COUNT(*) AS count FROM therapeutic_assessment_researcher_workbench_draft_events WHERE draft_id IN (SELECT id FROM therapeutic_assessment_researcher_workbench_drafts WHERE case_id IN (SELECT id FROM therapeutic_assessment_cases WHERE participant_user_id = ?))",
            (user_id,),
        )
    if table == "therapeutic_assessment_queue_events":
        return _count(
            conn,
            "SELECT COUNT(*) AS count FROM therapeutic_assessment_queue_events WHERE queue_item_id IN (SELECT id FROM therapeutic_assessment_work_queue WHERE case_id IN (SELECT id FROM therapeutic_assessment_cases WHERE participant_user_id = ?))",
            (user_id,),
        )
    if table == "therapeutic_assessment_quality_events":
        return _count(
            conn,
            """
            SELECT COUNT(*) AS count FROM therapeutic_assessment_quality_events
            WHERE (entity_type = 'quality_review' AND entity_id IN (
                SELECT id FROM therapeutic_assessment_quality_reviews
                WHERE case_id IN (SELECT id FROM therapeutic_assessment_cases WHERE participant_user_id = ?)
            )) OR (entity_type = 'quality_incident' AND entity_id IN (
                SELECT id FROM therapeutic_assessment_quality_incidents
                WHERE case_id IN (SELECT id FROM therapeutic_assessment_cases WHERE participant_user_id = ?)
            ))
            """,
            (user_id, user_id),
        )
    if table == "publication_candidates":
        return _count(
            conn,
            "SELECT COUNT(*) AS count FROM publication_candidates WHERE channel = 'therapeutic_feedback' AND subject_id IN (SELECT id FROM therapeutic_assessment_feedback_versions WHERE case_id IN (SELECT id FROM therapeutic_assessment_cases WHERE participant_user_id = ?))",
            (user_id,),
        )
    if table in {"publication_gate_checks", "publication_candidate_events"}:
        return _count(
            conn,
            f"SELECT COUNT(*) AS count FROM {table} WHERE candidate_id IN (SELECT id FROM publication_candidates WHERE channel = 'therapeutic_feedback' AND subject_id IN (SELECT id FROM therapeutic_assessment_feedback_versions WHERE case_id IN (SELECT id FROM therapeutic_assessment_cases WHERE participant_user_id = ?)))",
            (user_id,),
        )
    if table in {"therapeutic_assessment_actions", "therapeutic_assessment_cases"}:
        return _count(
            conn,
            f"SELECT COUNT(*) AS count FROM {table} WHERE participant_user_id = ?",
            (user_id,),
        )
    return 0


def preview_privacy_request(request_id: str, actor: dict) -> dict:
    policy = _load_policy()
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM privacy_requests WHERE id = ?", (request_id,)).fetchone()
        if row is None:
            raise PrivacyRequestError("not_found", "没有找到该隐私申请。", 404)
        item = row_to_dict(row)
        if item["status"] != "processing":
            raise PrivacyRequestError("invalid_transition", "只有处理中申请可以生成执行预览。", 409)
        if item.get("handled_by") != actor["id"] and actor.get("role") != "admin":
            raise PrivacyRequestError("processing_conflict", "该申请由其他处理人负责。", 409)
        scopes = _validate_scope(json_loads(item.get("handling_scope_json"), []), required=True)
        modules = []
        for scope in scopes:
            tables = [{"table": table, "count": _table_count(conn, table, item["user_id"])} for table in SCOPE_TABLES[scope]]
            modules.append({
                "scope": scope,
                "label": policy.get("scope_labels", {}).get(scope, scope),
                "method": "delete_or_anonymize_by_whitelist",
                "count": sum(entry["count"] for entry in tables),
                "tables": tables,
            })
        users_count = _count(conn, "SELECT COUNT(*) AS count FROM users WHERE id = ?", (item["user_id"],)) if "account_identity" in scopes else 0
        if users_count:
            modules[scopes.index("account_identity")]["tables"].append({"table": "users", "count": users_count})
            modules[scopes.index("account_identity")]["count"] += users_count
        preview = {
            "request_id": request_id,
            "request_version": int(item.get("version") or 0),
            "policy_version": policy["policy_version"],
            "policy_approval_status": policy.get("approval_status"),
            "scope": scopes,
            "modules": modules,
            "total_affected": sum(module["count"] for module in modules),
            "retained_categories": policy["retained_categories"],
            "external_surfaces": [
                {"surface": "application_cache", "status": "not_present_in_current_architecture"},
                {"surface": "search_index", "status": "not_present_in_current_architecture"},
                {"surface": "offline_exports", "status": "blocked_by_consent_and_export_flags"},
                {"surface": "backups", "status": "retention_confirmation_required", "rule": policy.get("backup_policy", {}).get("rule")},
            ],
            "irreversible_notice": "正式执行会删除或匿名化白名单内数据；事务失败将整笔回滚，但已完成执行不能由页面撤销。",
        }
        preview["scope_hash"] = _stable_hash({"policy_version": preview["policy_version"], "scope": scopes, "modules": modules})
        write_audit_log(conn, "privacy_request_previewed", str(actor["id"]), "privacy_request", request_id, {"scope_hash": preview["scope_hash"], "total_affected": preview["total_affected"]})
        conn.commit()
    return preview


def approve_privacy_execution(request_id: str, actor: dict, scope_hash: str, policy_version: str, idempotency_key: str) -> dict:
    if not idempotency_key or not scope_hash or not policy_version:
        raise PrivacyRequestError("validation_error", "批准需要幂等键、策略版本和范围哈希。", 400)
    preview = preview_privacy_request(request_id, actor)
    if preview["scope_hash"] != scope_hash or preview["policy_version"] != policy_version:
        raise PrivacyRequestError("preview_changed", "范围或策略已经变化，请重新预览。", 409)
    timestamp = now_iso()
    with get_connection() as conn:
        existing = conn.execute("SELECT * FROM privacy_request_approvals WHERE actor_id = ? AND idempotency_key = ?", (actor["id"], idempotency_key)).fetchone()
        if existing is not None:
            item = row_to_dict(existing)
            if item["request_id"] != request_id or item["scope_hash"] != scope_hash:
                raise PrivacyRequestError("idempotency_conflict", "该幂等键已用于其他批准。", 409)
            item["already_processed"] = True
            return item
        approval_id = new_id("privacy_approval")
        try:
            conn.execute(
                "INSERT INTO privacy_request_approvals (id, request_id, actor_id, actor_role, scope_hash, policy_version, decision, idempotency_key, created_at) VALUES (?, ?, ?, ?, ?, ?, 'approved', ?, ?)",
                (approval_id, request_id, actor["id"], actor.get("role"), scope_hash, policy_version, idempotency_key, timestamp),
            )
        except Exception as exc:
            raise PrivacyRequestError("approval_conflict", "同一人员不能对同一范围重复批准。", 409) from exc
        write_audit_log(conn, "privacy_execution_approved", str(actor["id"]), "privacy_request", request_id, {"scope_hash": scope_hash, "policy_version": policy_version})
        conn.commit()
        row = conn.execute("SELECT * FROM privacy_request_approvals WHERE id = ?", (approval_id,)).fetchone()
    return row_to_dict(row)


def _delete_table_rows(
    conn, table: str, user_id: str, replacement_user_id: str | None = None
) -> int:
    if table == "ai_capability_decisions":
        return conn.execute(
            "UPDATE ai_capability_decisions SET actor_id = ? WHERE actor_id = ?",
            (replacement_user_id, user_id),
        ).rowcount
    if table in DIRECT_USER_TABLES:
        return conn.execute(f"DELETE FROM {table} WHERE user_id = ?", (user_id,)).rowcount
    if table == "family_links":
        return conn.execute("DELETE FROM family_links WHERE parent_user_id = ? OR student_user_id = ?", (user_id, user_id)).rowcount
    if table == "data_claims":
        return conn.execute("DELETE FROM data_claims WHERE target_user_id = ?", (user_id,)).rowcount
    if table == "consent_record_annotations":
        return conn.execute("DELETE FROM consent_record_annotations WHERE subject_id = ?", (user_id,)).rowcount
    if table == "parent_report_actions":
        return conn.execute("DELETE FROM parent_report_actions WHERE submission_id IN (SELECT id FROM parent_assessment_submissions WHERE user_id = ?)", (user_id,)).rowcount
    if table == "profile_reviews":
        return conn.execute("DELETE FROM profile_reviews WHERE profile_id IN (SELECT id FROM student_profiles WHERE user_id = ?)", (user_id,)).rowcount
    if table == "relationship_research_notes":
        return conn.execute("DELETE FROM relationship_research_notes WHERE enrollment_id IN (SELECT id FROM relationship_pilot_enrollments WHERE user_id = ?)", (user_id,)).rowcount
    case_linked_tables = {
        "therapeutic_assessment_feedback_versions",
        "therapeutic_assessment_feedback_deliveries",
        "therapeutic_assessment_feedback_responses",
        "therapeutic_assessment_evidence_items",
        "therapeutic_assessment_data_items",
        "therapeutic_assessment_participant_drafts",
        "therapeutic_assessment_responsibility_chains",
        "therapeutic_assessment_safety_events",
        "therapeutic_assessment_researcher_workbench_drafts",
        "therapeutic_assessment_quality_reviews",
        "therapeutic_assessment_quality_incidents",
        "therapeutic_assessment_work_queue",
        "therapeutic_assessment_events",
    }
    if table in case_linked_tables:
        return conn.execute(
            f"DELETE FROM {table} WHERE case_id IN (SELECT id FROM therapeutic_assessment_cases WHERE participant_user_id = ?)",
            (user_id,),
        ).rowcount
    if table == "therapeutic_assessment_data_consents":
        return conn.execute(
            "DELETE FROM therapeutic_assessment_data_consents WHERE data_item_id IN (SELECT id FROM therapeutic_assessment_data_items WHERE case_id IN (SELECT id FROM therapeutic_assessment_cases WHERE participant_user_id = ?))",
            (user_id,),
        ).rowcount
    if table == "therapeutic_assessment_participant_draft_events":
        return conn.execute(
            "DELETE FROM therapeutic_assessment_participant_draft_events WHERE draft_id IN (SELECT id FROM therapeutic_assessment_participant_drafts WHERE case_id IN (SELECT id FROM therapeutic_assessment_cases WHERE participant_user_id = ?))",
            (user_id,),
        ).rowcount
    if table == "therapeutic_assessment_researcher_workbench_draft_events":
        return conn.execute(
            "DELETE FROM therapeutic_assessment_researcher_workbench_draft_events WHERE draft_id IN (SELECT id FROM therapeutic_assessment_researcher_workbench_drafts WHERE case_id IN (SELECT id FROM therapeutic_assessment_cases WHERE participant_user_id = ?))",
            (user_id,),
        ).rowcount
    if table == "therapeutic_assessment_queue_events":
        return conn.execute(
            "DELETE FROM therapeutic_assessment_queue_events WHERE queue_item_id IN (SELECT id FROM therapeutic_assessment_work_queue WHERE case_id IN (SELECT id FROM therapeutic_assessment_cases WHERE participant_user_id = ?))",
            (user_id,),
        ).rowcount
    if table == "therapeutic_assessment_quality_events":
        return conn.execute(
            """
            DELETE FROM therapeutic_assessment_quality_events
            WHERE (entity_type = 'quality_review' AND entity_id IN (
                SELECT id FROM therapeutic_assessment_quality_reviews
                WHERE case_id IN (SELECT id FROM therapeutic_assessment_cases WHERE participant_user_id = ?)
            )) OR (entity_type = 'quality_incident' AND entity_id IN (
                SELECT id FROM therapeutic_assessment_quality_incidents
                WHERE case_id IN (SELECT id FROM therapeutic_assessment_cases WHERE participant_user_id = ?)
            ))
            """,
            (user_id, user_id),
        ).rowcount
    if table == "publication_candidates":
        return conn.execute(
            "DELETE FROM publication_candidates WHERE channel = 'therapeutic_feedback' AND subject_id IN (SELECT id FROM therapeutic_assessment_feedback_versions WHERE case_id IN (SELECT id FROM therapeutic_assessment_cases WHERE participant_user_id = ?))",
            (user_id,),
        ).rowcount
    if table in {"publication_gate_checks", "publication_candidate_events"}:
        return conn.execute(
            f"DELETE FROM {table} WHERE candidate_id IN (SELECT id FROM publication_candidates WHERE channel = 'therapeutic_feedback' AND subject_id IN (SELECT id FROM therapeutic_assessment_feedback_versions WHERE case_id IN (SELECT id FROM therapeutic_assessment_cases WHERE participant_user_id = ?)))",
            (user_id,),
        ).rowcount
    if table in {"therapeutic_assessment_actions", "therapeutic_assessment_cases"}:
        return conn.execute(
            f"DELETE FROM {table} WHERE participant_user_id = ?",
            (user_id,),
        ).rowcount
    return 0


def _verify_deleted_scope(conn, user_id: str, scopes: list[str], preview: dict, deleted: dict) -> dict:
    expected = {
        entry["table"]: int(entry["count"])
        for module in preview.get("modules", [])
        for entry in module.get("tables", [])
        if entry.get("table") != "users"
    }
    checks = []
    for table in dict.fromkeys(table for scope in scopes for table in SCOPE_TABLES[scope]):
        post_count = _table_count(conn, table, user_id)
        expected_count = expected.get(table, 0)
        deleted_count = int(deleted.get(table, 0))
        checks.append(
            {
                "table": table,
                "expected_count": expected_count,
                "deleted_count": deleted_count,
                "post_count": post_count,
                "passed": post_count == 0 and deleted_count == expected_count,
            }
        )
    if "account_identity" in scopes:
        user = conn.execute(
            "SELECT status, username, phone_or_email, password_hash, wechat_openid, phone_hash, avatar_url FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
        checks.append(
            {
                "table": "users_identity",
                "expected_count": 1,
                "deleted_count": int(deleted.get("users_anonymized", 0)),
                "post_count": 0 if user and user["status"] == "deleted" and not any(user[key] for key in ("username", "phone_or_email", "password_hash", "wechat_openid", "phone_hash", "avatar_url")) else 1,
                "passed": bool(user and user["status"] == "deleted" and not any(user[key] for key in ("username", "phone_or_email", "password_hash", "wechat_openid", "phone_hash", "avatar_url"))),
            }
        )
    return {
        "status": "verified" if all(item["passed"] for item in checks) else "failed",
        "checks": checks,
        "all_queries_zero_or_anonymized": all(item["passed"] for item in checks),
        "new_export_blocked": True,
        "offline_and_ai_participant_text_allowed": False,
        "backup_erasure_status": "human_policy_pending",
    }


def _execution_gate(conn, request_id: str, preview: dict) -> None:
    if not current_app.config.get("PRIVACY_EXECUTION_ENABLED", False):
        raise PrivacyRequestError("execution_disabled", "真实执行开关未开启；当前只允许预览和 dry-run。", 503)
    env = str(current_app.config.get("APP_ENV", "development")).lower()
    if not current_app.config.get("PRIVACY_RETENTION_POLICY_APPROVED", False):
        raise PrivacyRequestError("policy_not_approved", "数据保存矩阵尚未由负责人确认。", 409)
    if env == "production":
        if preview.get("policy_approval_status") != "approved":
            raise PrivacyRequestError("policy_not_approved", "源控数据保存策略尚未记录负责人批准。", 409)
        if not current_app.config.get("PRIVACY_PRODUCTION_EXECUTION_ENABLED", False):
            raise PrivacyRequestError("production_execution_disabled", "生产执行开关未开启。", 503)
        rows = conn.execute("SELECT actor_id, actor_role FROM privacy_request_approvals WHERE request_id = ? AND scope_hash = ? AND policy_version = ? AND decision = 'approved'", (request_id, preview["scope_hash"], preview["policy_version"])).fetchall()
        distinct = {row["actor_id"] for row in rows}
        if len(distinct) < 2 or not any(row["actor_role"] == "admin" for row in rows):
            raise PrivacyRequestError("dual_approval_required", "生产执行需要两名不同人员批准，且至少一名为管理员。", 409)


def execute_privacy_request(request_id: str, actor: dict, *, dry_run: bool, idempotency_key: str, expected_version: int | None) -> dict:
    if not idempotency_key:
        raise PrivacyRequestError("validation_error", "执行需要 Idempotency-Key。", 400)
    mode = "dry_run" if dry_run else "execute"
    with get_connection() as conn:
        replay = conn.execute("SELECT * FROM privacy_request_executions WHERE actor_id = ? AND idempotency_key = ?", (actor["id"], idempotency_key)).fetchone()
    if replay is not None:
        item = row_to_dict(replay)
        if item["request_id"] != request_id or item["mode"] != mode:
            raise PrivacyRequestError("idempotency_conflict", "该幂等键已用于其他执行。", 409)
        result = json_loads(item.pop("result_json", None), {})
        item.pop("preview_json", None)
        return {"execution": item, "result": result, "already_processed": True}
    preview = preview_privacy_request(request_id, actor)
    if expected_version is not None and expected_version != preview["request_version"]:
        raise PrivacyRequestError("state_conflict", "申请版本已经变化，请重新预览。", 409)
    timestamp = now_iso()
    with get_connection() as conn:
        replay = conn.execute("SELECT * FROM privacy_request_executions WHERE actor_id = ? AND idempotency_key = ?", (actor["id"], idempotency_key)).fetchone()
        if replay is not None:
            item = row_to_dict(replay)
            if item["request_id"] != request_id or item["mode"] != mode:
                raise PrivacyRequestError("idempotency_conflict", "该幂等键已用于其他执行。", 409)
            return {"execution": item, "result": json_loads(item.get("result_json"), {}), "already_processed": True}
        row = conn.execute("SELECT * FROM privacy_requests WHERE id = ?", (request_id,)).fetchone()
        if row is None or row["status"] != "processing":
            raise PrivacyRequestError("invalid_transition", "申请状态已经变化，请重新加载。", 409)
        if row["handled_by"] != actor["id"] and actor.get("role") != "admin":
            raise PrivacyRequestError("processing_conflict", "该申请由其他处理人负责。", 409)
        if not dry_run:
            _execution_gate(conn, request_id, preview)
        execution_id = new_id("privacy_execution")
        conn.execute(
            "INSERT INTO privacy_request_executions (id, request_id, actor_id, environment, mode, policy_version, scope_hash, preview_json, result_json, status, idempotency_key, started_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, '{}', 'running', ?, ?)",
            (execution_id, request_id, actor["id"], str(current_app.config.get("APP_ENV", "development")), mode, preview["policy_version"], preview["scope_hash"], json_dumps(preview), idempotency_key, timestamp),
        )
        if dry_run:
            result = {"mode": mode, "deleted": {}, "total_deleted": 0, "would_affect": preview["total_affected"], "external_surfaces": preview["external_surfaces"]}
        else:
            user_id = row["user_id"]
            scopes = preview["scope"]
            deleted: dict[str, int] = {}
            replacement = f"deleted_{_stable_hash({'request_id': request_id, 'user_id': user_id})[:16]}"
            ordered_tables = [
                "parent_report_actions", "profile_reviews", "relationship_research_notes",
                *[table for scope in scopes for table in SCOPE_TABLES[scope] if table not in {"parent_report_actions", "profile_reviews", "relationship_research_notes"}],
            ]
            for table in dict.fromkeys(ordered_tables):
                deleted[table] = _delete_table_rows(
                    conn, table, user_id, replacement
                )
            if "account_identity" in scopes:
                conn.execute("UPDATE users SET nickname = '已删除用户', username = NULL, phone_or_email = NULL, password_hash = NULL, anonymous_id = ?, wechat_openid = NULL, phone_hash = NULL, avatar_url = NULL, status = 'deleted', updated_at = ? WHERE id = ?", (replacement, timestamp, user_id))
                deleted["users_anonymized"] = 1
                conn.execute("UPDATE audit_logs SET actor_id = ? WHERE actor_id = ?", (replacement, user_id))
                conn.execute("UPDATE audit_logs SET target_id = ?, metadata_json = '{\"privacy_redacted\":true}' WHERE target_id = ?", (replacement, user_id))
                conn.execute("UPDATE privacy_request_actions SET actor_id = ?, note = NULL WHERE request_id = ? AND actor_id = ?", (replacement, request_id, user_id))
            subject_hash = hmac.new(str(current_app.config.get("PRIVACY_TOMBSTONE_SECRET", "")).encode(), user_id.encode(), hashlib.sha256).hexdigest()
            verification = _verify_deleted_scope(conn, user_id, scopes, preview, deleted)
            if verification["status"] != "verified":
                raise PrivacyRequestError("deletion_verification_failed", "删除后核验未通过，本次事务已回滚。", 409)
            verification_id = new_id("privacy_verification")
            conn.execute(
                """INSERT INTO privacy_deletion_verifications
                   (id, request_id, execution_id, subject_hash, scope_hash,
                    verification_json, status, verified_at)
                   VALUES (?, ?, ?, ?, ?, ?, 'verified', ?)""",
                (verification_id, request_id, execution_id, subject_hash, preview["scope_hash"], json_dumps(verification), timestamp),
            )
            result = {"mode": mode, "deleted": deleted, "total_deleted": sum(deleted.values()), "replacement_user_id": replacement, "verification_id": verification_id, "verification_status": "verified", "external_surfaces": preview["external_surfaces"]}
            proof_hash = _stable_hash({"request_id": request_id, "policy_version": preview["policy_version"], "scope_hash": preview["scope_hash"], "result": result, "completed_at": timestamp})
            conn.execute("INSERT INTO privacy_deletion_tombstones (id, request_id, subject_hash, replacement_user_id, policy_version, scope_json, proof_hash, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (new_id("privacy_tombstone"), request_id, subject_hash, replacement, preview["policy_version"], json_dumps(scopes), proof_hash, timestamp))
            request_user_id = replacement if "account_identity" in scopes else user_id
            completion = conn.execute("UPDATE privacy_requests SET user_id = ?, reason = NULL, handled_note = NULL, participant_notice = '申请已完成。系统仅保留最小审计证明，不保留申请原因或业务原文。', status = 'completed', decision = 'executed', handled_at = ?, policy_version = ?, execution_proof_hash = ?, updated_at = ?, version = version + 1 WHERE id = ? AND status = 'processing' AND version = ?", (request_user_id, timestamp, preview["policy_version"], proof_hash, timestamp, request_id, preview["request_version"]))
            if completion.rowcount != 1:
                raise PrivacyRequestError("state_conflict", "完成前申请状态发生变化，执行已回滚。", 409)
        proof_hash = None if dry_run else proof_hash
        completed_at = now_iso()
        conn.execute("UPDATE privacy_request_executions SET result_json = ?, proof_hash = ?, status = 'completed', completed_at = ? WHERE id = ?", (json_dumps(result), proof_hash, completed_at, execution_id))
        write_audit_log(conn, "privacy_request_dry_run" if dry_run else "privacy_request_executed", str(actor["id"]), "privacy_request", request_id, {"scope_hash": preview["scope_hash"], "policy_version": preview["policy_version"], "proof_hash": proof_hash, "total": result.get("total_deleted", 0)})
        conn.commit()
        execution = conn.execute("SELECT * FROM privacy_request_executions WHERE id = ?", (execution_id,)).fetchone()
    item = row_to_dict(execution)
    item.pop("preview_json", None)
    item.pop("result_json", None)
    return {"execution": item, "result": result, "already_processed": False}


def get_deletion_verification(request_id: str, actor: dict) -> dict:
    with get_connection() as conn:
        request_row = conn.execute("SELECT id, handled_by, status FROM privacy_requests WHERE id = ?", (request_id,)).fetchone()
        if request_row is None:
            raise PrivacyRequestError("not_found", "没有找到该隐私申请。", 404)
        if actor.get("role") != "admin" and request_row["handled_by"] != actor.get("id"):
            raise PrivacyRequestError("forbidden", "只能核对自己负责的隐私申请。", 403)
        row = conn.execute(
            "SELECT * FROM privacy_deletion_verifications WHERE request_id = ? ORDER BY verified_at DESC LIMIT 1",
            (request_id,),
        ).fetchone()
    if row is None:
        raise PrivacyRequestError("not_found", "该申请尚无删除核验证据。", 404)
    item = row_to_dict(row)
    item["verification"] = json_loads(item.pop("verification_json", None), {})
    item.pop("subject_hash", None)
    return item
