"""Human-gated pilot evidence packages for Task38 F19-F23."""

from __future__ import annotations

import hashlib
import json

from flask import current_app

from database import get_connection, write_audit_log
from services.therapeutic_assessment_service import FORMAL_ROLES, TherapeuticAssessmentError


def _registry() -> dict:
    path = current_app.config["CONTENT_DIR"] / "therapeutic_assessment_pilot_evidence_registry.json"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise TherapeuticAssessmentError("pilot_evidence_unavailable", "试点证据模板暂时不可读取", 503) from exc
    if payload.get("schema") != "safehome.therapeutic-assessment.pilot-evidence.v1":
        raise TherapeuticAssessmentError("pilot_evidence_invalid", "试点证据模板版本不兼容", 503)
    return payload


def build_package(actor: dict, stage_id: str) -> dict:
    if str(actor.get("role") or "") not in FORMAL_ROLES:
        raise TherapeuticAssessmentError("pilot_evidence_forbidden", "试点证据包仅向正式研究角色开放", 403)
    payload = _registry()
    stage = next((item for item in payload["stages"] if item.get("id") == stage_id), None)
    if stage is None:
        raise TherapeuticAssessmentError("pilot_stage_not_found", "未找到对应试点阶段", 404)
    package = {
        "schema": "safehome.therapeutic-assessment.pilot-evidence-package.v1",
        "registry_version": payload["version"],
        "stage": stage,
        "human_reviews": [],
        "unresolved_critical_issues": [],
        "human_signoff_complete": False,
        "simulated_signoffs_counted": False,
        "production_release_approved": False,
        "boundary_notice": payload["boundary_notice"],
    }
    canonical = json.dumps(package, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    package["sha256"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    with get_connection() as conn:
        write_audit_log(
            conn, "therapeutic_assessment_pilot_evidence_built", str(actor["id"]),
            "therapeutic_assessment_pilot_stage", stage_id,
            {"human_signoff_complete": False, "simulated_signoffs_counted": False, "sha256": package["sha256"]},
        )
        conn.commit()
    return package
