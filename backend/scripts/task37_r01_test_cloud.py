"""Task37-R01 test-cloud evidence planning and local rehearsal."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
REGISTRY = ROOT / "content" / "task37_release_execution_registry.json"


def _stage() -> tuple[dict, dict]:
    payload = json.loads(REGISTRY.read_text(encoding="utf-8"))
    if payload.get("schema") != "safehome.task37.release-execution.v1":
        raise RuntimeError("release execution registry schema mismatch")
    stage = next(item for item in payload.get("stages") or [] if item.get("id") == "R01")
    return payload, stage


def inspect() -> dict:
    payload, stage = _stage()
    referenced = list(stage["deployment_artifacts"]) + list(stage["synthetic_replay_suites"])
    missing = [item for item in referenced if not (ROOT / item).exists()]
    canonical = json.dumps(stage, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return {
        "ok": not missing,
        "registry_version": payload["version"],
        "stage_id": stage["id"],
        "stage_sha256": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
        "missing_artifacts": missing,
        "probe_count": len(stage["probes"]),
        "worker_check_count": len(stage["worker_checks"]),
        "fault_scenario_count": len(stage["fault_scenarios"]),
        "test_cloud_execution_complete": False,
        "production_mutation_executed": False,
        "production_release_approved": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["plan", "exercise-local", "verify", "rollback-plan"])
    args = parser.parse_args()
    state = inspect()
    if args.action == "plan":
        result = {
            "action": "plan",
            **state,
            "next_action": "run in an isolated test-cloud environment and attach human-verifiable evidence",
        }
    elif args.action == "exercise-local":
        result = {
            "action": "exercise-local",
            **state,
            "local_rehearsal_complete": state["ok"],
            "counts_as_test_cloud_execution": False,
        }
    elif args.action == "rollback-plan":
        result = {
            "action": "rollback-plan",
            **state,
            "steps": [
                "disable test-cloud writes",
                "switch AI, sentiment and SNA to read-only or off",
                "preserve audit and evidence",
                "restore the previous verified test image",
                "repeat health, ready and synthetic replay checks",
            ],
            "rollback_executed": False,
        }
    else:
        result = {"action": "verify", **state}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if state["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
