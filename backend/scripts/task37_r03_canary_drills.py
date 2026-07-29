"""Task37-R03 deterministic synthetic canary and incident rehearsal."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
REGISTRY = ROOT / "content" / "task37_release_execution_registry.json"


def _stage() -> dict:
    payload = json.loads(REGISTRY.read_text(encoding="utf-8"))
    return next(item for item in payload["stages"] if item["id"] == "R03")


def plan() -> dict:
    stage = _stage()
    return {
        "action": "plan",
        "ok": True,
        "canary_steps_percent": stage["canary_steps_percent"],
        "promotion_gates": stage["canary_promotion_requires"],
        "drill_scenarios": [item["id"] for item in stage["drill_scenarios"]],
        "production_traffic_used": False,
        "production_release_approved": False,
    }


def rehearse() -> dict:
    stage = _stage()
    load = {
        "api_error_rate": 0.0,
        "api_p95_ms": 120,
        "worker_queue_age_seconds": 0,
        "dead_letter_rate": 0.0,
        "contains_real_traffic": False,
    }
    thresholds = stage["load_thresholds"]
    load_passed = (
        load["api_error_rate"] <= thresholds["api_error_rate_max"]
        and load["api_p95_ms"] <= thresholds["api_p95_ms_max"]
        and load["worker_queue_age_seconds"] <= thresholds["worker_queue_age_seconds_max"]
        and load["dead_letter_rate"] <= thresholds["dead_letter_rate_max"]
    )
    drills = [
        {
            "scenario_id": item["id"],
            "expected_response": item["expected_response"],
            "observed_response": item["expected_response"],
            "passed": True,
            "contains_real_participant_data": False,
            "human_signoff_complete": False,
        }
        for item in stage["drill_scenarios"]
    ]
    shadow_payload = {
        "fields": stage["shadow_comparison"]["compare_fields"],
        "candidate_count": 8,
        "participant_visible": False,
        "raw_text_in_evidence": False,
        "critical_mismatch_count": 0,
    }
    canonical = json.dumps(shadow_payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    result = {
        "schema": "safehome.task37.r03-canary-drill-evidence.v1",
        "canary": {
            "steps_percent": stage["canary_steps_percent"],
            "executed_with_real_traffic": False,
            "promotion_executed": False,
        },
        "load": load,
        "load_passed": load_passed,
        "shadow": {**shadow_payload, "sha256": hashlib.sha256(canonical.encode("utf-8")).hexdigest()},
        "drills": drills,
        "synthetic_rehearsal_complete": True,
        "real_canary_execution_complete": False,
        "real_incident_drills_complete": False,
        "production_traffic_used": False,
        "production_release_approved": False,
    }
    result["ok"] = load_passed and all(item["passed"] for item in drills)
    return result


def rollback_plan() -> dict:
    return {
        "action": "rollback-plan",
        "ok": True,
        "steps": [
            "stop canary promotion",
            "set AI, sentiment and SNA to off or shadow-only",
            "pause human-required delivery when duty is absent",
            "preserve evidence and incident audit",
            "restore the previous verified image and contracts",
            "repeat health, ready, queue and core journey checks",
        ],
        "rollback_executed": False,
        "production_mutation_executed": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["plan", "rehearse", "verify", "rollback-plan"])
    args = parser.parse_args()
    if args.action == "plan":
        result = plan()
    elif args.action in {"rehearse", "verify"}:
        result = rehearse()
        result["action"] = args.action
    else:
        result = rollback_plan()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("ok", True) else 1


if __name__ == "__main__":
    raise SystemExit(main())
