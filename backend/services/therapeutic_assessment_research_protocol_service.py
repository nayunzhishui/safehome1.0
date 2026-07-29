"""Pre-specified research protocol and minimum-necessary export for Task38-F18."""

from __future__ import annotations

import hashlib
import hmac
import json

from flask import current_app

from database import get_connection, rows_to_dicts, write_audit_log
from services.therapeutic_assessment_service import (
    FORMAL_ROLES,
    TherapeuticAssessmentError,
)


def _load() -> dict:
    path = current_app.config["CONTENT_DIR"] / "therapeutic_assessment_research_protocol.json"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise TherapeuticAssessmentError(
            "research_protocol_unavailable", "研究协议暂时不可读取", 503
        ) from exc
    if payload.get("schema") != "safehome.therapeutic-assessment.research-protocol.v1":
        raise TherapeuticAssessmentError(
            "research_protocol_invalid", "研究协议版本不兼容", 503
        )
    return payload


def _assert_formal(actor: dict) -> None:
    if str(actor.get("role") or "") not in FORMAL_ROLES:
        raise TherapeuticAssessmentError(
            "research_protocol_forbidden", "研究协议与导出仅向正式研究角色开放", 403
        )


def get_protocol(actor: dict) -> dict:
    _assert_formal(actor)
    payload = _load()
    with get_connection() as conn:
        write_audit_log(
            conn,
            "therapeutic_assessment_research_protocol_viewed",
            str(actor["id"]),
            "therapeutic_assessment_research_protocol",
            str(payload["version"]),
            {"production_release_approved": False},
        )
        conn.commit()
    return payload


def _case_key(case_id: str) -> str:
    secret = str(current_app.config["SECRET_KEY"]).encode("utf-8")
    digest = hmac.new(secret, case_id.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"ta_{digest[:20]}"


def preview_export(actor: dict, data: dict) -> dict:
    _assert_formal(actor)
    protocol = _load()
    purpose = str(data.get("purpose") or "").strip()
    allowed = set(protocol["export_policy"]["allowed_purposes"])
    if purpose not in allowed:
        raise TherapeuticAssessmentError(
            "research_export_purpose_invalid",
            "导出用途未获本研究协议允许",
            400,
            {"allowed_purposes": sorted(allowed)},
        )
    role = str(actor.get("role") or "")
    where = ""
    params: tuple[object, ...] = ()
    if role == "researcher":
        where = "WHERE c.assigned_researcher_id = ?"
        params = (str(actor["id"]),)
    with get_connection() as conn:
        rows = rows_to_dicts(
            conn.execute(
                f"""
                SELECT c.id, c.workflow_state, c.safety_state, c.readiness_level,
                       c.created_at, c.updated_at,
                       COUNT(DISTINCT f.id) AS feedback_version_count,
                       COUNT(DISTINCT r.id) AS participant_response_count,
                       COUNT(DISTINCT a.id) AS action_count,
                       COUNT(DISTINCT CASE
                           WHEN q.category IN (
                               'diagnostic_misunderstanding', 'shame_or_blame',
                               'conflict_escalation', 'unauthorized_sharing',
                               'irreversible_withdrawal_error', 'risk_human_chain_failure'
                           ) AND q.status NOT IN ('resolved', 'closed') THEN q.id END
                       ) AS serious_harm_open_count
                FROM therapeutic_assessment_cases c
                LEFT JOIN therapeutic_assessment_feedback_versions f ON f.case_id = c.id
                LEFT JOIN therapeutic_assessment_feedback_responses r ON r.case_id = c.id
                LEFT JOIN therapeutic_assessment_actions a ON a.case_id = c.id
                LEFT JOIN therapeutic_assessment_quality_incidents q ON q.case_id = c.id
                {where}
                GROUP BY c.id, c.workflow_state, c.safety_state, c.readiness_level,
                         c.created_at, c.updated_at
                ORDER BY c.created_at, c.id
                """,
                params,
            ).fetchall()
        )
        result_rows = [
            {
                "case_key": _case_key(str(row["id"])),
                "workflow_state": row["workflow_state"],
                "safety_state": row["safety_state"],
                "service_level": row["readiness_level"],
                "started_at": row["created_at"],
                "last_updated_at": row["updated_at"],
                "feedback_version_count": int(row["feedback_version_count"] or 0),
                "participant_response_count": int(row["participant_response_count"] or 0),
                "action_count": int(row["action_count"] or 0),
                "serious_harm_open_count": int(row["serious_harm_open_count"] or 0),
            }
            for row in rows
        ]
        write_audit_log(
            conn,
            "therapeutic_assessment_research_export_previewed",
            str(actor["id"]),
            "therapeutic_assessment_research_export",
            purpose,
            {
                "row_count": len(result_rows),
                "deidentified": True,
                "raw_text_included": False,
                "production_export_executed": False,
            },
        )
        conn.commit()
    return {
        "schema": "safehome.therapeutic-assessment.research-export.v1",
        "protocol_version": protocol["version"],
        "purpose": purpose,
        "count": len(result_rows),
        "rows": result_rows,
        "deidentified": True,
        "minimum_necessary": True,
        "raw_text_included": False,
        "harm_metrics_separate": True,
        "symptom_outcomes_role": protocol["symptom_scales"]["role"],
        "preview_only": True,
        "production_export_executed": False,
        "boundary_notice": protocol["boundary_notice"],
    }
