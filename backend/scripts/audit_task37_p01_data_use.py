"""Audit Task 37 P01 governance without touching databases or external systems."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from services.task37_data_use_service import DataUseDenied, authorize_data_use, load_governance


def main() -> int:
    governance = load_governance()
    failures: list[str] = []
    if set(governance["domains"]) != {"affective_computing", "group_sna", "controlled_ai"}:
        failures.append("domains")
    if set(governance["data_purposes"]) != {
        "service_delivery",
        "quality_evaluation",
        "model_training",
        "secondary_research",
    }:
        failures.append("data_purposes")
    try:
        authorize_data_use(
            {
                "domain": "controlled_ai",
                "purpose": "model_training",
                "source_kind": "participant_text",
                "contains_identifiable_data": False,
                "consent": {"agreed": False, "purpose": "model_training", "version": "audit"},
            }
        )
        failures.append("default_training_opt_in")
    except DataUseDenied as exc:
        if exc.code != "explicit_opt_in_required":
            failures.append("wrong_denial_code")

    result = {
        "task": "T37-P01",
        "status": "failed" if failures else "passed",
        "governance_version": governance["version"],
        "failures": failures,
        "production_mutation": False,
        "human_signoff": False,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
