"""Deterministic Task 34 operations-governance acceptance audit."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from flask import Flask


ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

import scripts.generate_task34_operations_registry as generator  # noqa: E402
from config import Config  # noqa: E402
from services.artifact_integrity_service import artifact_sha256  # noqa: E402
from services.operations_governance_service import execute_fixed_replay  # noqa: E402


PATHS = {
    "registry": ROOT / "content/operations_capability_registry.json",
    "cards": ROOT / "content/operations_asset_cards.json",
    "manifest": ROOT / "content/operations_release_manifest.json",
    "contract": ROOT / "shared/contracts/api-contract.json",
}


def audit() -> dict:
    issues = []
    payloads = {name: json.loads(path.read_text(encoding="utf-8")) for name, path in PATHS.items()}
    registry = payloads["registry"]
    contract = payloads["contract"]
    cards = payloads["cards"]
    manifest = payloads["manifest"]

    operation_ids = {item["operation_id"] for item in contract["endpoints"]}
    covered = {operation_id for capability in registry.get("capabilities", []) for operation_id in capability.get("operation_ids", [])}
    if covered != operation_ids:
        issues.append({"code": "capability_operation_coverage", "missing": sorted(operation_ids - covered), "extra": sorted(covered - operation_ids)})
    required_capability_fields = {"intended_use", "owner", "dependencies", "data", "open_roles", "feature_flags", "version", "tests", "rollback", "governance_status"}
    for item in registry.get("capabilities", []):
        missing = sorted(required_capability_fields - set(item))
        if missing:
            issues.append({"code": "capability_metadata_incomplete", "id": item.get("id"), "missing": missing})

    required_card_fields = {"source", "license", "metrics", "bias", "failure_modes", "out_of_domain", "admission_criteria", "disable_criteria"}
    card_types = set()
    for item in cards.get("cards", []):
        card_types.add(item.get("card_type"))
        missing = sorted(required_card_fields - set(item))
        if missing:
            issues.append({"code": "asset_card_incomplete", "id": item.get("id"), "missing": missing})
    if not {"dataset", "rule", "model"} <= card_types:
        issues.append({"code": "asset_card_type_coverage", "types": sorted(card_types)})

    artifact_types = set()
    for artifact in manifest.get("artifacts", []):
        artifact_types.add(artifact.get("artifact_type"))
        path = ROOT / artifact.get("path", "")
        if not path.is_file() or artifact_sha256(path) != artifact.get("sha256"):
            issues.append({"code": "release_artifact_integrity", "path": artifact.get("path")})
    required_types = {"content", "rule", "model", "dictionary", "prompt", "knowledge_index"}
    if not required_types <= artifact_types:
        issues.append({"code": "release_artifact_type_coverage", "missing": sorted(required_types - artifact_types)})

    app = Flask("task34-audit")
    app.config["CONTENT_DIR"] = ROOT / "content"
    Config.CONTENT_DIR = ROOT / "content"
    with app.app_context():
        replay = execute_fixed_replay({"id": "task34-audit"})
    metrics = replay["metrics"]
    if metrics["failed"] or metrics["high_severity_regressions"]:
        issues.append({"code": "fixed_replay_failed", "metrics": metrics})

    if registry.get("production_release_approved") is not False:
        issues.append({"code": "production_gate_inferred"})
    if registry.get("temporary_showcase_exception", {}).get("formal_permission_acceptance") is not False:
        issues.append({"code": "temporary_showcase_used_for_formal_acceptance"})
    if registry.get("treatment_assessment", {}).get("real_participant_release_allowed") is not False:
        issues.append({"code": "treatment_assessment_real_release_inferred"})

    return {
        "ok": not issues,
        "registry_version": registry.get("version"),
        "contract_version": contract.get("version"),
        "capability_count": len(registry.get("capabilities", [])),
        "operation_count": len(operation_ids),
        "asset_card_count": len(cards.get("cards", [])),
        "artifact_count": len(manifest.get("artifacts", [])),
        "fixed_replay": metrics,
        "contains_real_participant_data": False,
        "production_release_approved": False,
        "issues": issues,
    }


def main() -> int:
    if generator.check() != 0:
        return 1
    result = audit()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
