"""Versioned three-track state transitions for collaborative assessment."""

from __future__ import annotations

import json
from functools import lru_cache

from config import Config
from database import get_connection, json_loads, now_iso, row_to_dict, write_audit_log
from services.therapeutic_assessment_service import (
    REVIEW_ROLES,
    TherapeuticAssessmentError,
    _assert_participant,
    _assert_researcher,
    _case_row,
    _idempotency,
    _present_case,
    _event,
)


ALLOWED_PAYLOAD_KEYS = {"track", "target_state", "expected_version", "reason_code"}
PARTICIPANT_ROLES = {"parent", "student"}
PARTICIPANT_WORKFLOW_TARGETS = {
    "submitted",
    "revision_requested",
    "action_selected",
    "followup",
    "withdrawn",
}
PARTICIPANT_HYPOTHESIS_TARGETS = {"participant_checked", "revised", "withdrawn"}
REVIEW_ONLY_HYPOTHESIS_TARGETS = {"human_reviewed"}
REVIEW_ONLY_SAFETY_TARGETS = {"safety_path", "stabilized", "closed"}


@lru_cache(maxsize=1)
def _contract() -> dict:
    path = Config.CONTENT_DIR / "therapeutic_assessment_state_machine.json"
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value.get("tracks"), dict) or not isinstance(value.get("reason_codes"), list):
        raise RuntimeError("治疗性评估状态机配置不完整")
    return value


def _authorize(conn, actor: dict, case: dict, track: str, target: str) -> None:
    role = str(actor.get("role") or "")
    if role in PARTICIPANT_ROLES:
        _assert_participant(actor, case)
        allowed = (
            target in PARTICIPANT_WORKFLOW_TARGETS
            if track == "workflow"
            else target in PARTICIPANT_HYPOTHESIS_TARGETS
            if track == "hypothesis"
            else False
        )
        if not allowed:
            raise TherapeuticAssessmentError("forbidden", "该状态变化需要正式研究角色处理。", 403)
        return

    _assert_researcher(conn, actor, case)
    if track == "hypothesis" and target in REVIEW_ONLY_HYPOTHESIS_TARGETS and role not in REVIEW_ROLES:
        raise TherapeuticAssessmentError("forbidden", "该假设状态需要督导或管理员复核。", 403)
    if track == "safety" and target in REVIEW_ONLY_SAFETY_TARGETS and role not in REVIEW_ROLES:
        raise TherapeuticAssessmentError("forbidden", "该安全状态需要督导或管理员处理。", 403)


def _legacy_status(workflow_state: str, safety_state: str, current: str) -> str:
    if workflow_state == "withdrawn":
        return "withdrawn"
    if workflow_state == "participant_check":
        return "feedback_sent"
    if workflow_state == "archived":
        return "archived"
    if workflow_state == "not_applicable":
        return "not_applicable"
    if workflow_state == "safety_path" or safety_state == "safety_path":
        return "support_required"
    if current in {"withdrawn", "feedback_sent", "archived", "not_applicable", "support_required"}:
        return "open"
    return current or "open"


def transition_case(
    actor: dict,
    case_id: str,
    payload: dict,
    idempotency_key: str,
) -> dict:
    """Move one state track while enforcing scope, role, version and idempotency."""

    key = _idempotency(idempotency_key)
    unknown = set(payload) - ALLOWED_PAYLOAD_KEYS
    if unknown:
        raise TherapeuticAssessmentError(
            "validation_error",
            "状态变化包含未支持字段。",
            details={"unknown_fields": sorted(unknown)},
        )
    track = str(payload.get("track") or "").strip()
    target = str(payload.get("target_state") or "").strip()
    reason = str(payload.get("reason_code") or "").strip()
    expected = payload.get("expected_version")
    if not isinstance(expected, int) or isinstance(expected, bool) or expected < 1:
        raise TherapeuticAssessmentError("validation_error", "expected_version 必须是正整数。")

    contract = _contract()
    tracks = contract["tracks"]
    if track not in tracks:
        raise TherapeuticAssessmentError("validation_error", "不支持的状态轨道。")
    if reason not in set(contract["reason_codes"]):
        raise TherapeuticAssessmentError("validation_error", "不支持的状态变化原因。")
    definition = tracks[track]
    column = str(definition["column"])
    action = f"state_transition:{track}:{target}"
    timestamp = now_iso()

    with get_connection() as conn:
        case = _case_row(conn, case_id)
        role = str(actor.get("role") or "")
        if role in PARTICIPANT_ROLES:
            _assert_participant(actor, case)
        else:
            _assert_researcher(conn, actor, case)

        replay = conn.execute(
            """
            SELECT case_id, action, after_version, metadata_json
            FROM therapeutic_assessment_events
            WHERE actor_id = ? AND idempotency_key = ?
            """,
            (str(actor["id"]), key),
        ).fetchone()
        if replay is not None:
            replay_item = row_to_dict(replay)
            if replay_item["case_id"] != case_id or replay_item["action"] != action:
                raise TherapeuticAssessmentError(
                    "idempotency_conflict",
                    "该提交标识已用于其它操作。",
                    409,
                )
            return _present_case(conn, case, actor)

        if case.get("workflow_state") == "withdrawn":
            raise TherapeuticAssessmentError("withdrawn", "该协作记录已经撤回，不能继续变化。", 409)
        current_version = int(case.get("version") or 0)
        if expected != current_version:
            raise TherapeuticAssessmentError(
                "version_conflict",
                "记录已经更新，请刷新后重试。",
                409,
                {"expected_version": expected, "current_version": current_version},
            )
        current_state = str(case.get(column) or definition.get("initial") or "")
        allowed_targets = definition.get("transitions", {}).get(current_state)
        if allowed_targets is None or target not in allowed_targets:
            raise TherapeuticAssessmentError(
                "invalid_transition",
                "当前状态不能直接进入目标状态。",
                409,
                {"track": track, "current_state": current_state, "target_state": target},
            )
        _authorize(conn, actor, case, track, target)

        workflow_state = target if track == "workflow" else str(case["workflow_state"])
        safety_state = target if track == "safety" else str(case["safety_state"])
        next_version = current_version + 1
        legacy_status = _legacy_status(
            workflow_state,
            safety_state,
            str(case.get("status") or ""),
        )
        withdrawn_at = timestamp if workflow_state == "withdrawn" else case.get("withdrawn_at")
        consent_status = "withdrawn" if workflow_state == "withdrawn" else case.get("consent_status")
        cursor = conn.execute(
            f"""
            UPDATE therapeutic_assessment_cases
            SET {column} = ?, status = ?, consent_status = ?, withdrawn_at = ?,
                version = ?, updated_at = ?
            WHERE id = ? AND version = ?
            """,
            (
                target,
                legacy_status,
                consent_status,
                withdrawn_at,
                next_version,
                timestamp,
                case_id,
                current_version,
            ),
        )
        if cursor.rowcount != 1:
            raise TherapeuticAssessmentError(
                "version_conflict",
                "记录已经被其他操作更新，请刷新后重试。",
                409,
            )
        _event(
            conn,
            case_id,
            actor,
            action,
            key,
            current_version,
            next_version,
            {
                "track": track,
                "from": current_state,
                "to": target,
                "reason_code": reason,
                "contract_version": contract["version"],
                "actor_role": role,
            },
        )
        write_audit_log(
            conn,
            "therapeutic_assessment_state_transitioned",
            str(actor["id"]),
            "therapeutic_assessment_case",
            case_id,
            {
                "track": track,
                "from": current_state,
                "to": target,
                "reason_code": reason,
                "before_version": current_version,
                "after_version": next_version,
            },
        )
        conn.commit()
        return _present_case(conn, _case_row(conn, case_id), actor)
