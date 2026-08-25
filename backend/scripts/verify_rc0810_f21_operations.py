"""Verify the RC0810-F21 operations and recovery policy."""

from __future__ import annotations

import argparse
import json
import sys
from copy import deepcopy
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from services.operations_reliability_service import load_operations_policy, run_isolated_drills  # noqa: E402


REQUIRED_P0 = {
    "psychological_content_misdelivery", "cross_object_disclosure", "deletion_failure",
    "high_risk_feedback_error", "external_message_misdelivery",
}
REQUIRED_COSTS = {
    "cloudbase_requests", "mysql_storage", "logs", "backups", "external_messages",
    "production_ai", "human_review",
}


def validate(policy: dict) -> list[str]:
    errors = []
    health = policy.get("health_contract") or {}
    if health.get("public_fields") != ["ok", "service", "version"]:
        errors.append("public_health_not_minimal")
    if set(health.get("protected_components") or []) != {"database", "redis", "queues", "content", "scheduler", "deployment"}:
        errors.append("protected_health_components_incomplete")
    if health.get("forwarded_headers_trusted") is not False:
        errors.append("forwarded_headers_must_not_be_trusted")
    alerts = policy.get("alerts") or []
    required_alert_fields = {"id", "level", "threshold", "duration", "notify", "silence", "recovery"}
    if not alerts or any(not required_alert_fields.issubset(item) for item in alerts):
        errors.append("alert_contract_incomplete")
    if set((policy.get("rollback_runbooks") or {}).keys()) != {"code_version", "database_migration", "content_artifact"}:
        errors.append("rollback_runbooks_incomplete")
    p0 = policy.get("incident_record", {}).get("p0_categories") or []
    if {item.get("id") for item in p0} != REQUIRED_P0 or any(not {"stop", "notify", "repair", "reconcile"}.issubset(item) for item in p0):
        errors.append("p0_incident_categories_incomplete")
    drills = run_isolated_drills(policy)
    if not drills["ok"] or len(drills["results"]) != 5:
        errors.append("isolated_drills_failed")
    costs = policy.get("cost_quota") or []
    if {item.get("resource") for item in costs} != REQUIRED_COSTS or any(item.get("warn_at") != 0.8 or not item.get("owner") for item in costs):
        errors.append("cost_quota_incomplete")
    continuity = policy.get("account_continuity") or []
    if not continuity or any(item.get("minimum_admins", 0) < 2 or item.get("single_person_dependency") is not False for item in continuity):
        errors.append("account_continuity_single_person_risk")
    if policy.get("external_gates") != {
        "operations_owner": "pending_external",
        "test_cloud_observation": "pending_external",
        "account_recovery_drill": "pending_external",
    } or policy.get("production_gate_eligible") is not False:
        errors.append("external_gate_or_production_state_invalid")
    return errors


def verify() -> dict:
    policy = load_operations_policy()
    errors = validate(policy)
    return {
        "ok": not errors,
        "policy_version": policy.get("version"),
        "sli_count": len(policy.get("sli_slo") or []),
        "alert_count": len(policy.get("alerts") or []),
        "drill_count": len(policy.get("isolated_drills") or []),
        "p0_category_count": len(policy.get("incident_record", {}).get("p0_categories") or []),
        "production_gate_eligible": policy.get("production_gate_eligible"),
        "errors": errors,
    }


def self_check() -> dict:
    broken = deepcopy(load_operations_policy())
    broken["incident_record"]["p0_categories"] = broken["incident_record"]["p0_categories"][:-1]
    errors = validate(broken)
    return {"ok": "p0_incident_categories_incomplete" in errors, "detected_errors": errors}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-check", action="store_true")
    args = parser.parse_args()
    result = self_check() if args.self_check else verify()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
