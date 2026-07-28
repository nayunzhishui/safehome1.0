"""Read models and quality metrics for the collaborative feedback lifecycle."""

from __future__ import annotations

from flask import current_app

from database import get_connection, json_loads, row_to_dict, rows_to_dicts, write_audit_log
from services.therapeutic_assessment_service import (
    FORMAL_ROLES,
    TherapeuticAssessmentError,
    _assert_read,
    _case_row,
)


CORE_CONTINUITY = {
    "independent_routes": [
        "/api/goals",
        "/api/diaries",
        "/api/cards/recommend",
        "/api/checkins",
        "/api/weekly-report",
        "/api/messages",
    ],
    "boundary": "关闭协作式反馈生命周期只关闭本模块入口，不改变目标、日记、训练卡、打卡、周报和消息。",
}


def _enabled() -> bool:
    return bool(current_app.config.get("THERAPEUTIC_ASSESSMENT_LIFECYCLE_ENABLED", False))


def _feedback_item(row: dict) -> dict:
    item = dict(row)
    item["evidence"] = json_loads(item.pop("evidence_json", None), [])
    item.pop("participant_content", None)
    item.pop("observations_json", None)
    item.pop("alternatives_json", None)
    item.pop("human_discussion_json", None)
    return item


def _process_metrics(
    feedback: list[dict],
    deliveries: list[dict],
    responses: list[dict],
    actions: list[dict],
    events: list[dict],
) -> dict:
    revised = sum(1 for item in events if item["action"] == "feedback_revised")
    withdrawn = sum(1 for item in feedback if item["status"] == "withdrawn")
    completed_actions = sum(1 for item in actions if item["status"] == "completed")
    return {
        "feedback_version_count": len(feedback),
        "revision_count": revised,
        "withdrawn_feedback_count": withdrawn,
        "delivery_receipt_count": len(deliveries),
        "participant_response_count": len(responses),
        "action_selected_count": len(actions),
        "action_followup_count": completed_actions,
        "latest_event_at": events[-1]["created_at"] if events else None,
    }


def _implementation_metrics(
    deliveries: list[dict],
    feedback: list[dict],
    actions: list[dict],
) -> dict:
    active_sent = [item for item in feedback if item["status"] == "sent" and not item.get("withdrawn_at")]
    orphan_receipts = [
        item for item in deliveries
        if not any(feedback_item["id"] == item["feedback_id"] for feedback_item in feedback)
    ]
    return {
        "active_sent_feedback_count": len(active_sent),
        "delivery_attempt_count": len(deliveries),
        "withdrawal_propagation_ok": all(
            item["status"] == "withdrawn"
            for item in deliveries
            if any(
                feedback_item["id"] == item["feedback_id"]
                and feedback_item["status"] == "withdrawn"
                for feedback_item in feedback
            )
        ),
        "orphan_delivery_receipt_count": len(orphan_receipts),
        "versioned_action_count": sum(1 for item in actions if int(item.get("version") or 0) >= 1),
    }


def get_case_lifecycle(actor: dict, case_id: str) -> dict:
    with get_connection() as conn:
        case = _case_row(conn, case_id)
        _assert_read(actor, case)
        if not _enabled():
            return {
                "enabled": False,
                "case_id": case_id,
                "workflow_state": case["workflow_state"],
                "core_continuity": CORE_CONTINUITY,
            }

        feedback = rows_to_dicts(
            conn.execute(
                """
                SELECT id, case_id, version_no, author_id, source, status, feedback_layer,
                       recipient_user_id, letter_title, evidence_json, supersedes_feedback_id,
                       reviewed_by, reviewed_at, sent_at, withdrawn_at, withdrawal_reason,
                       lifecycle_version, created_at
                FROM therapeutic_assessment_feedback_versions
                WHERE case_id = ?
                ORDER BY version_no, created_at, id
                """,
                (case_id,),
            ).fetchall()
        )
        deliveries = rows_to_dicts(
            conn.execute(
                "SELECT * FROM therapeutic_assessment_feedback_deliveries WHERE case_id = ? ORDER BY sequence_no, created_at, id",
                (case_id,),
            ).fetchall()
        )
        responses = rows_to_dicts(
            conn.execute(
                "SELECT * FROM therapeutic_assessment_feedback_responses WHERE case_id = ? ORDER BY created_at, id",
                (case_id,),
            ).fetchall()
        )
        actions = rows_to_dicts(
            conn.execute(
                "SELECT * FROM therapeutic_assessment_actions WHERE case_id = ? ORDER BY created_at, id",
                (case_id,),
            ).fetchall()
        )
        events = rows_to_dicts(
            conn.execute(
                """
                SELECT id, action, actor_id, before_version, after_version,
                       metadata_json, idempotency_key, created_at
                FROM therapeutic_assessment_events
                WHERE case_id = ?
                ORDER BY created_at, id
                """,
                (case_id,),
            ).fetchall()
        )
        incidents = rows_to_dicts(
            conn.execute(
                """
                SELECT id, category, status, created_at, updated_at
                FROM therapeutic_assessment_quality_incidents
                WHERE case_id = ?
                ORDER BY created_at, id
                """,
                (case_id,),
            ).fetchall()
        )
        pending_privacy = conn.execute(
            """
            SELECT id, status, created_at
            FROM privacy_requests
            WHERE user_id = ? AND request_type = 'delete_my_data'
              AND status IN ('pending', 'processing')
            ORDER BY created_at DESC LIMIT 1
            """,
            (case["participant_user_id"],),
        ).fetchone()
        write_audit_log(
            conn,
            "therapeutic_assessment_lifecycle_viewed",
            str(actor["id"]),
            "therapeutic_assessment_case",
            case_id,
            {"workflow_state": case["workflow_state"], "event_count": len(events)},
        )
        conn.commit()

    for item in events:
        item["metadata"] = json_loads(item.pop("metadata_json", None), {})
    process_quality = _process_metrics(feedback, deliveries, responses, actions, events)
    implementation_quality = _implementation_metrics(deliveries, feedback, actions)
    harm_incidents = {
        "total": len(incidents),
        "open": sum(1 for item in incidents if item["status"] not in {"resolved", "closed"}),
        "resolved": sum(1 for item in incidents if item["status"] in {"resolved", "closed"}),
        "items": incidents,
        "boundary": "伤害事件单独统计，不与流程完成率或行动次数合并。",
    }
    return {
        "enabled": True,
        "case_id": case_id,
        "case_version": int(case["version"]),
        "workflow_state": case["workflow_state"],
        "hypothesis_state": case["hypothesis_state"],
        "safety_state": case["safety_state"],
        "feedback_versions": [_feedback_item(item) for item in feedback],
        "delivery_receipts": deliveries,
        "participant_responses": responses,
        "actions": actions,
        "events": events,
        "recovery": {
            "retryable_feedback_ids": [
                item["id"]
                for item in feedback
                if item["status"] == "sent" and not item.get("withdrawn_at")
            ],
            "withdrawal_propagation_ok": implementation_quality["withdrawal_propagation_ok"],
            "privacy_deletion_request": row_to_dict(pending_privacy),
        },
        "metrics": {
            "process_quality": process_quality,
            "implementation_quality": implementation_quality,
            "harm_incidents": harm_incidents,
        },
        "core_continuity": CORE_CONTINUITY,
        "boundary_notice": "流程指标描述服务过程，不代表疗效、诊断、关系质量或个体风险结论。",
    }


def get_lifecycle_metrics(actor: dict) -> dict:
    role = str(actor.get("role") or "")
    if role not in FORMAL_ROLES:
        raise TherapeuticAssessmentError("forbidden", "汇总指标仅向正式研究角色开放。", 403)
    scope_sql = ""
    params: tuple[object, ...] = ()
    if role == "researcher":
        scope_sql = "WHERE assigned_researcher_id = ?"
        params = (str(actor["id"]),)
    with get_connection() as conn:
        case_rows = rows_to_dicts(
            conn.execute(
                f"SELECT id, workflow_state FROM therapeutic_assessment_cases {scope_sql}",
                params,
            ).fetchall()
        )
        case_ids = [item["id"] for item in case_rows]
        if not case_ids:
            return {
                "enabled": _enabled(),
                "process_quality": {"case_count": 0},
                "implementation_quality": {"withdrawal_propagation_failures": 0},
                "harm_incidents": {"total": 0, "open": 0},
                "core_continuity": CORE_CONTINUITY,
            }
        placeholders = ",".join("?" for _ in case_ids)
        feedback = rows_to_dicts(
            conn.execute(
                f"SELECT id, case_id, status, withdrawn_at FROM therapeutic_assessment_feedback_versions WHERE case_id IN ({placeholders})",
                tuple(case_ids),
            ).fetchall()
        )
        deliveries = rows_to_dicts(
            conn.execute(
                f"SELECT feedback_id, status FROM therapeutic_assessment_feedback_deliveries WHERE case_id IN ({placeholders})",
                tuple(case_ids),
            ).fetchall()
        )
        incidents = rows_to_dicts(
            conn.execute(
                f"SELECT status FROM therapeutic_assessment_quality_incidents WHERE case_id IN ({placeholders})",
                tuple(case_ids),
            ).fetchall()
        )
        withdrawal_failures = sum(
            1
            for item in feedback
            if item["status"] == "withdrawn"
            and any(
                delivery["feedback_id"] == item["id"] and delivery["status"] != "withdrawn"
                for delivery in deliveries
            )
        )
        result = {
            "enabled": _enabled(),
            "process_quality": {
                "case_count": len(case_rows),
                "archived_case_count": sum(1 for item in case_rows if item["workflow_state"] == "archived"),
                "withdrawn_case_count": sum(1 for item in case_rows if item["workflow_state"] == "withdrawn"),
                "feedback_version_count": len(feedback),
                "delivery_receipt_count": len(deliveries),
            },
            "implementation_quality": {
                "withdrawal_propagation_failures": withdrawal_failures,
                "orphan_delivery_receipt_count": sum(
                    1
                    for delivery in deliveries
                    if not any(item["id"] == delivery["feedback_id"] for item in feedback)
                ),
            },
            "harm_incidents": {
                "total": len(incidents),
                "open": sum(1 for item in incidents if item["status"] not in {"resolved", "closed"}),
            },
            "core_continuity": CORE_CONTINUITY,
            "boundary_notice": "汇总只描述流程与实施质量；伤害事件独立呈现。",
        }
        write_audit_log(
            conn,
            "therapeutic_assessment_lifecycle_metrics_viewed",
            str(actor["id"]),
            "therapeutic_assessment_lifecycle",
            "aggregate",
            {"case_count": len(case_rows)},
        )
        conn.commit()
        return result
