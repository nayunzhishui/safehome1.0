"""Verify the live F06 route/object inventory and retired authorization shortcuts."""

from __future__ import annotations

import argparse
import importlib
import json
import os
import re
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
INVENTORY_PATH = ROOT / "config" / "rc0810" / "object_authorization_inventory.json"
API_CONTRACT_PATH = ROOT / "shared" / "contracts" / "api-contract.json"
TARGET_NAMES = {"user_id", "participant_user_id", "subject_id", "record_id", "job_id"}


def _live_routes() -> list[dict]:
    temp_dir = tempfile.TemporaryDirectory(
        prefix="safehome-f06-inventory-", ignore_cleanup_errors=True
    )
    os.environ["APP_ENV"] = "testing"
    os.environ["DATABASE_PATH"] = str(Path(temp_dir.name) / "inventory.sqlite3")
    os.environ["CONTENT_DIR"] = str(ROOT / "content")
    os.environ["DATABASE_DATA_WATERMARK"] = "local_fake_only"
    if str(BACKEND) not in sys.path:
        sys.path.insert(0, str(BACKEND))
    for name in list(sys.modules):
        if name in {"app", "config", "database", "models"} or name.startswith(("routes.", "services.")):
            sys.modules.pop(name, None)
    app = importlib.import_module("app").app
    rows = []
    for rule in app.url_map.iter_rules():
        if not str(rule.rule).startswith("/api/"):
            continue
        variables = sorted(str(item) for item in rule.arguments)
        if not variables:
            continue
        rows.append(
            {
                "route": str(rule.rule),
                "methods": sorted(method for method in rule.methods if method not in {"HEAD", "OPTIONS"}),
                "parameters": variables,
            }
        )
    return sorted(rows, key=lambda item: (item["route"], item["methods"]))


def _parameter_hits() -> list[dict]:
    pattern = re.compile(r"(?:request\.(?:args|form)\.get|payload\.get)\(\s*[\"']([^\"']+)[\"']")
    rows = []
    for path in sorted((BACKEND / "routes").glob("*.py")):
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            for match in pattern.finditer(line):
                name = match.group(1)
                if name in TARGET_NAMES:
                    rows.append(
                        {
                            "file": path.relative_to(ROOT).as_posix(),
                            "line": line_number,
                            "parameter": name,
                        }
                    )
    return rows


def _retired_shortcut_errors() -> list[str]:
    checks = {
        "backend/routes/admin.py": ['require_role("admin", "researcher", allow_legacy_admin=True)'],
        "backend/services/relationship_pilot_common.py": ["legacy-auto-", "claim_enrollment(actor"],
        "backend/services/therapeutic_assessment_service.py": ['role in {"admin", "supervisor"}'],
    }
    errors = []
    for relative, forbidden in checks.items():
        text = (ROOT / relative).read_text(encoding="utf-8")
        for token in forbidden:
            if token in text:
                errors.append(f"retired shortcut remains: {relative}: {token}")
    helper_text = (ROOT / "backend" / "routes" / "utils.py").read_text(encoding="utf-8")
    if "require_participant_scope" not in helper_text:
        errors.append("require_admin_or_owner is not bound to participant scope")
    stale_call = re.compile(r"_assert_(?:read|researcher)\(actor\s*,")
    for path in sorted((BACKEND / "services").glob("therapeutic_assessment_*.py")):
        if stale_call.search(path.read_text(encoding="utf-8")):
            errors.append(
                f"therapeutic case authorization call does not share its service connection: "
                f"{path.relative_to(ROOT).as_posix()}"
            )
    return errors


def _contract_scope_errors() -> list[str]:
    payload = json.loads(API_CONTRACT_PATH.read_text(encoding="utf-8"))
    scopes = {
        (item["path"], item["method"]): item.get("object_scope")
        for item in payload.get("endpoints", [])
    }
    expected = {
        ("/api/therapeutic-assessment/cases/<case_id>", "GET"):
            "participant_owner_or_assigned_researcher_or_claimed_queue_or_supervision_chain_or_admin",
        ("/api/therapeutic-assessment/method-library", "GET"):
            "module_resource_role_or_owner_scope_without_therapeutic_case_claim",
        ("/api/therapeutic-assessment/data-items/<item_id>", "GET"):
            "data_controller_or_provider_or_explicit_allowed_viewer_with_dynamic_consent",
        ("/api/therapeutic-assessment/data-items/<item_id>/consent", "PATCH"):
            "data_subject_or_involved_participant_consent_control",
        ("/api/research/access/assignments", "POST"):
            "admin_managed_versioned_assignment_lifecycle",
        ("/api/research/analysis/jobs/<job_id>", "GET"):
            "analysis_job_or_artifact_bound_to_authorized_snapshot_or_admin_operation",
    }
    return [
        f"API object_scope mismatch: {method} {path}: {scopes.get((path, method))!r}"
        for (path, method), value in expected.items()
        if scopes.get((path, method)) != value
    ]


def verify(write: bool = False) -> dict:
    inventory = json.loads(INVENTORY_PATH.read_text(encoding="utf-8"))
    live_routes = _live_routes()
    parameter_hits = _parameter_hits()
    if write:
        inventory["discovered_routes"] = live_routes
        inventory["source_parameter_hits"] = parameter_hits
        INVENTORY_PATH.write_text(
            json.dumps(inventory, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    errors = _retired_shortcut_errors() + _contract_scope_errors()
    if inventory.get("discovered_routes") != live_routes:
        errors.append("live Flask route inventory changed; run verifier with --write and review")
    if inventory.get("source_parameter_hits") != parameter_hits:
        errors.append("route target-parameter inventory changed; run verifier with --write and review")
    object_types = {item.get("object_type") for item in inventory.get("objects", [])}
    required = {
        "participant_user",
        "message",
        "relationship_enrollment",
        "therapeutic_case",
        "therapeutic_data_item",
        "research_analysis",
        "export",
    }
    if not required <= object_types:
        errors.append("object authorization model is incomplete")
    return {
        "schema": "safehome.rc0810.f06-authorization-verification.v1",
        "ok": not errors,
        "route_count": len(live_routes),
        "parameter_hit_count": len(parameter_hits),
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    result = verify(write=args.write)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
