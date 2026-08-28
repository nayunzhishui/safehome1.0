"""Validate the F25-A WeChat platform acceptance definition contract."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from run_rc0810 import collect_git_snapshot, load_registry  # noqa: E402


BASELINE_PATH = ROOT / "docs" / "02_专项进度与验收" / "rc0810_f25a_platform_baseline_current.json"
BASELINE_RELATIVE = BASELINE_PATH.relative_to(ROOT).as_posix()
RELEASE_EVIDENCE_RELATIVES = (
    "docs/02_专项进度与验收/rc0810_f22a_security_baseline.json",
    "docs/02_专项进度与验收/rc0810_f22b_security_gate.json",
    "docs/02_专项进度与验收/rc0810_f25a_platform_baseline.json",
    BASELINE_RELATIVE,
    "docs/02_专项进度与验收/rc0810_f25b_evidence.json",
    "docs/02_专项进度与验收/rc0810_f26_final_rc.json",
    "docs/02_专项进度与验收/rc0810_f26_final_rc.md",
    "docs/02_专项进度与验收/rc0810_required_ci_evidence.json",
    "docs/02_专项进度与验收/rc0810_wave_c_review_packet.json",
    "docs/02_专项进度与验收/rc0810_wave_c_review_decision.json",
)
DEFINITIONS = (
    "config/rc0810/wechat_platform_acceptance.schema.json",
    "config/rc0810/wechat_platform_catalog.json",
    "config/rc0810/wechat_platform_capability_map.json",
    "config/rc0810/wechat_platform_zero_context_review.json",
    "config/rc0810/wechat_platform_review_freeze.json",
    "config/rc0810/wechat_platform_raci.json",
    "config/rc0810/wechat_platform_real_world_evidence.json",
)
ACCOUNT_SCENARIOS = [
    "wechat_one_tap_login", "phone_login", "account_login", "logout",
    "legacy_account", "locked_account", "multi_device_session",
]
MESSAGE_SCENARIOS = [
    "subscription_denied", "subscription_expired", "subscription_duplicate",
    "training_record", "historical_feedback", "researcher_feedback_message",
]
DEVICE_SCENARIOS = [
    "cold_start", "warm_start", "foreground_background", "weak_network",
    "offline_recovery", "large_font", "keyboard", "safe_area",
]
REQUIRED_ZERO_CONTEXT_OUTCOMES = [
    "login_without_help",
    "find_core_journey",
    "understand_non_diagnostic_boundary",
    "recover_from_failure",
]
EXPECTED_INVALIDATION_RULES = {
    "package_or_image": ["artifact", "device", "journey", "materials", "platform"],
    "cloudbase_target": ["platform", "journey", "device"],
    "privacy_text": ["privacy", "materials", "platform"],
    "base_library": ["devtools", "device", "journey"],
    "test_account_or_data": ["zero_context", "journey", "messages"],
}
PAGE_CLASSIFICATIONS = [
    "public_mapped",
    "internal_hidden",
    "test_only_disabled",
    "blocker_pending_mapping",
]


def strict_object(required: list[str], properties: dict[str, Any]) -> dict[str, Any]:
    return {
        "type": "object",
        "required": required,
        "properties": properties,
        "additionalProperties": False,
    }


STRING = {"type": "string", "minLength": 1}
NULLABLE_STRING = {"type": ["string", "null"]}
STRING_ARRAY = {"type": "array", "items": STRING}
DEFINITION_SCHEMAS: dict[str, dict[str, Any]] = {
    "catalog": strict_object(
        ["schema", "phase", "subtasks", "artifact_binding", "platform_checks", "account_scenarios", "message_scenarios", "devtools_checks", "device_slots", "journeys", "review_materials", "evidence_contract", "external_identities", "production_gate_eligible"],
        {
            "schema": STRING,
            "phase": {"const": "F25-A"},
            "subtasks": STRING_ARRAY,
            "artifact_binding": strict_object(
                ["miniprogram_package_sha256", "backend_image_digest", "cloudbase_config_sha256", "privacy_text_sha256", "base_library_version", "status"],
                {key: NULLABLE_STRING for key in ["miniprogram_package_sha256", "backend_image_digest", "cloudbase_config_sha256", "privacy_text_sha256", "base_library_version"]} | {"status": STRING},
            ),
            "platform_checks": {"type": "array", "items": strict_object(["id", "owner", "status"], {"id": STRING, "owner": STRING, "status": STRING})},
            "account_scenarios": STRING_ARRAY,
            "message_scenarios": STRING_ARRAY,
            "devtools_checks": STRING_ARRAY,
            "device_slots": {"type": "array", "items": strict_object(["platform", "device_id", "operator_id", "scenarios", "status"], {"platform": STRING, "device_id": NULLABLE_STRING, "operator_id": NULLABLE_STRING, "scenarios": STRING_ARRAY, "status": STRING})},
            "journeys": strict_object(["participant_core", "production_negative", "status"], {"participant_core": STRING_ARRAY, "production_negative": STRING_ARRAY, "status": STRING}),
            "review_materials": STRING_ARRAY,
            "evidence_contract": strict_object(["required_fields", "states", "automation_max_state"], {"required_fields": STRING_ARRAY, "states": STRING_ARRAY, "automation_max_state": STRING}),
            "external_identities": {"type": "array", "maxItems": 0},
            "production_gate_eligible": {"const": False},
        },
    ),
    "capability": strict_object(
        ["schema", "phase", "inventory_sources", "capabilities", "registered_page_inventory", "allowed_page_classifications", "unmapped_public_capability_policy", "production_gate_eligible"],
        {
            "schema": STRING,
            "phase": {"const": "F25-A"},
            "inventory_sources": strict_object(
                ["app_json", "api_client", "registered_pages_count", "registered_pages_sha256"],
                {
                    "app_json": strict_object(["path", "sha256"], {"path": STRING, "sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"}}),
                    "api_client": strict_object(["path", "sha256"], {"path": STRING, "sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"}}),
                    "registered_pages_count": {"type": "integer", "minimum": 1},
                    "registered_pages_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                },
            ),
            "capabilities": {"type": "array", "items": strict_object(["id", "pages", "apis", "data_domains", "service_category", "qualification", "privacy_declaration", "status"], {"id": STRING, "pages": STRING_ARRAY, "apis": STRING_ARRAY, "data_domains": STRING_ARRAY, "service_category": NULLABLE_STRING, "qualification": NULLABLE_STRING, "privacy_declaration": NULLABLE_STRING, "status": STRING})},
            "registered_page_inventory": {"type": "array", "items": strict_object(["page", "classification", "capability_id"], {"page": STRING, "classification": {"enum": PAGE_CLASSIFICATIONS}, "capability_id": NULLABLE_STRING})},
            "allowed_page_classifications": {"const": PAGE_CLASSIFICATIONS},
            "unmapped_public_capability_policy": {"const": "block_or_hide_before_review"},
            "production_gate_eligible": {"const": False},
        },
    ),
    "zero_context": strict_object(
        ["schema", "phase", "allowed_inputs", "forbidden_assistance", "required_outcomes", "reviewer_id", "status", "automation_may_approve"],
        {"schema": STRING, "phase": {"const": "F25-A"}, "allowed_inputs": STRING_ARRAY, "forbidden_assistance": STRING_ARRAY, "required_outcomes": STRING_ARRAY, "reviewer_id": {"type": "null"}, "status": {"const": "pending_external"}, "automation_may_approve": {"const": False}},
    ),
    "freeze": strict_object(
        ["schema", "phase", "frozen_inputs", "current_snapshot", "invalidation_rules", "status", "production_gate_eligible"],
        {"schema": STRING, "phase": {"const": "F25-A"}, "frozen_inputs": STRING_ARRAY, "current_snapshot": {"type": "null"}, "invalidation_rules": strict_object(list(EXPECTED_INVALIDATION_RULES), {key: STRING_ARRAY for key in EXPECTED_INVALIDATION_RULES}), "status": {"const": "pending_external"}, "production_gate_eligible": {"const": False}},
    ),
    "raci": strict_object(
        ["schema", "phase", "domains", "required_roles", "assignments", "automation_may_sign", "status", "production_gate_eligible"],
        {"schema": STRING, "phase": {"const": "F25-A"}, "domains": STRING_ARRAY, "required_roles": STRING_ARRAY, "assignments": {"type": "array", "maxItems": 0}, "automation_may_sign": {"const": False}, "status": {"const": "pending_external"}, "production_gate_eligible": {"const": False}},
    ),
    "real_world": strict_object(
        ["schema", "phase", "items", "allowed_terminal_states", "automation_may_approve", "production_gate_eligible"],
        {"schema": STRING, "phase": {"const": "F25-A"}, "items": {"type": "array", "items": strict_object(["id", "owner", "status"], {"id": STRING, "owner": {"type": "null"}, "status": {"const": "pending_external"}})}, "allowed_terminal_states": STRING_ARRAY, "automation_may_approve": {"const": False}, "production_gate_eligible": {"const": False}},
    ),
}


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def git(*args: str, env: dict[str, str] | None = None) -> bytes:
    completed = subprocess.run(
        ["git", *args], cwd=ROOT, env=env, capture_output=True, check=False
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.decode("utf-8", errors="replace"))
    return completed.stdout


def platform_source_snapshot() -> dict[str, str]:
    current = collect_git_snapshot(load_registry())["git"]
    with tempfile.TemporaryDirectory(prefix="rc0810-f25-index-") as directory:
        env = os.environ.copy()
        env["GIT_INDEX_FILE"] = str(Path(directory) / "index")
        git("read-tree", current["source_tree"], env=env)
        for relative in RELEASE_EVIDENCE_RELATIVES:
            subprocess.run(
                ["git", "update-index", "--force-remove", "--", relative],
                cwd=ROOT,
                env=env,
                capture_output=True,
                check=False,
            )
        source_tree = git("write-tree", env=env).decode("ascii").strip()
    manifest = git("ls-tree", "-r", "-z", source_tree)
    diff = git("diff-tree", "--binary", "--no-ext-diff", current["head_tree"], source_tree)
    return {
        "head": current["head"],
        "head_tree": current["head_tree"],
        "source_tree": source_tree,
        "dirty_diff_sha256": sha256_bytes(diff),
        "source_manifest_sha256": sha256_bytes(manifest),
    }


def definition_paths() -> dict[str, Path]:
    return {relative: ROOT / relative for relative in DEFINITIONS}


def load_definitions() -> dict[str, dict[str, Any]]:
    return {
        "baseline_schema": load_json(ROOT / DEFINITIONS[0]),
        "catalog": load_json(ROOT / DEFINITIONS[1]),
        "capability": load_json(ROOT / DEFINITIONS[2]),
        "zero_context": load_json(ROOT / DEFINITIONS[3]),
        "freeze": load_json(ROOT / DEFINITIONS[4]),
        "raci": load_json(ROOT / DEFINITIONS[5]),
        "real_world": load_json(ROOT / DEFINITIONS[6]),
    }


def _canonical_sha256(value: Any) -> str:
    return sha256_bytes(
        json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    )


def validate_semantics(definitions: dict[str, dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    catalog = definitions["catalog"]
    capability = definitions["capability"]
    zero_context = definitions["zero_context"]
    freeze = definitions["freeze"]
    raci = definitions["raci"]
    real_world = definitions["real_world"]

    try:
        Draft202012Validator.check_schema(definitions["baseline_schema"])
    except Exception as exc:  # pragma: no cover - exact jsonschema error is environment-specific
        errors.append(f"baseline_schema_definition_invalid:{exc}")
    if definitions["baseline_schema"].get("additionalProperties") is not False:
        errors.append("baseline_schema_must_reject_unknown_fields")
    for name, schema in DEFINITION_SCHEMAS.items():
        for problem in Draft202012Validator(schema).iter_errors(definitions[name]):
            location = "/".join(str(part) for part in problem.absolute_path) or "$"
            errors.append(f"{name}_schema:{location}:{problem.message}")

    if catalog.get("subtasks") != [f"F25.{index}" for index in range(1, 15)]:
        errors.append("subtask_catalog_incomplete")
    if catalog.get("production_gate_eligible") is not False:
        errors.append("catalog_production_gate_must_remain_closed")
    if catalog.get("external_identities") != []:
        errors.append("external_identity_must_remain_unassigned")
    expected_binding = {
        "miniprogram_package_sha256": None,
        "backend_image_digest": None,
        "cloudbase_config_sha256": None,
        "privacy_text_sha256": None,
        "base_library_version": None,
        "status": "pending_external",
    }
    if catalog.get("artifact_binding") != expected_binding:
        errors.append("artifact_binding_must_remain_pending")
    expected_platform_checks = {
        "appid_subject", "service_category", "interface_permissions", "legal_domains",
        "cloudbase_environment", "privacy_guideline", "filing_status", "qualification_materials",
    }
    platform_checks = catalog.get("platform_checks", [])
    platform_ids = [item.get("id") for item in platform_checks]
    if len(platform_ids) != len(set(platform_ids)):
        errors.append("platform_check_ids_must_be_unique")
    if set(platform_ids) != expected_platform_checks:
        errors.append("platform_check_catalog_incomplete")
    if any(item.get("status") != "pending_external" for item in platform_checks):
        errors.append("platform_check_must_remain_pending")
    if catalog.get("account_scenarios") != ACCOUNT_SCENARIOS:
        errors.append("account_scenario_catalog_incomplete")
    if catalog.get("message_scenarios") != MESSAGE_SCENARIOS:
        errors.append("message_scenario_catalog_incomplete")
    if catalog.get("devtools_checks") != ["compile", "subpackages", "package_size", "network", "base_library", "page_warnings"]:
        errors.append("devtools_catalog_incomplete")
    device_slots = catalog.get("device_slots", [])
    device_ids = [item.get("platform") for item in device_slots]
    if len(device_ids) != len(set(device_ids)):
        errors.append("device_platform_ids_must_be_unique")
    slots = {item.get("platform"): item for item in device_slots}
    if set(slots) != {"ios", "android"} or any(item.get("scenarios") != DEVICE_SCENARIOS for item in slots.values()):
        errors.append("device_scenario_catalog_incomplete")
    if any(item.get("status") != "pending_external" or item.get("device_id") or item.get("operator_id") for item in device_slots):
        errors.append("device_evidence_must_remain_pending")
    journeys = catalog.get("journeys", {})
    if journeys.get("participant_core") != ["goal", "diary", "feedback", "training", "checkin", "weekly_report", "supervision"] or journeys.get("production_negative") != ["internal_route_hidden", "temporary_privilege_disabled", "debug_entry_hidden"] or journeys.get("status") != "pending_external":
        errors.append("journey_catalog_incomplete")
    if catalog.get("review_materials") != ["review_notes", "test_account_guide", "feature_paths", "boundary_statement", "failure_recovery"]:
        errors.append("review_material_catalog_incomplete")
    evidence_contract = catalog.get("evidence_contract", {})
    if set(evidence_contract.get("required_fields", [])) != {"owner", "reviewer", "captured_at", "valid_until", "invalidation_conditions", "artifact_sha256", "request_id"} or evidence_contract.get("automation_max_state") != "evidence_ready" or evidence_contract.get("states") != ["pending_external", "evidence_ready", "human_verified", "platform_approved", "stale"]:
        errors.append("evidence_contract_incomplete")

    if capability.get("production_gate_eligible") is not False:
        errors.append("capability_production_gate_must_remain_closed")
    source = capability.get("inventory_sources", {})
    app_path = ROOT / "apps/miniprogram/app.json"
    api_path = ROOT / "apps/miniprogram/services/api.js"
    app_pages = load_json(app_path).get("pages", [])
    expected_sources = {
        "app_json": {"path": "apps/miniprogram/app.json", "sha256": sha256_file(app_path)},
        "api_client": {"path": "apps/miniprogram/services/api.js", "sha256": sha256_file(api_path)},
        "registered_pages_count": len(app_pages),
        "registered_pages_sha256": _canonical_sha256(app_pages),
    }
    if source != expected_sources:
        errors.append("capability_inventory_source_mismatch")
    capabilities = capability.get("capabilities", [])
    capability_ids = [item.get("id") for item in capabilities]
    if len(capability_ids) != len(set(capability_ids)):
        errors.append("capability_ids_must_be_unique")
    mapped_pages: dict[str, str] = {}
    api_text = api_path.read_text(encoding="utf-8")
    for item in capabilities:
        if item.get("status") != "blocking_pending_external" or not item.get("pages") or not item.get("apis") or not item.get("data_domains"):
            errors.append("capability_mapping_incomplete")
        if item.get("service_category") is not None or item.get("qualification") is not None or item.get("privacy_declaration") is not None:
            errors.append("capability_platform_claim_must_remain_pending")
        for page in item.get("pages", []):
            if page in mapped_pages:
                errors.append("capability_page_mapped_more_than_once")
            mapped_pages[page] = str(item.get("id"))
            if page not in app_pages:
                errors.append("capability_page_not_registered")
        for api in item.get("apis", []):
            if f'"{api}"' not in api_text:
                errors.append("capability_api_not_in_client_contract")
    inventory = capability.get("registered_page_inventory", [])
    inventory_pages = [item.get("page") for item in inventory]
    if inventory_pages != app_pages or len(inventory_pages) != len(set(inventory_pages)):
        errors.append("registered_page_inventory_incomplete")
    for item in inventory:
        classification = item.get("classification")
        page = item.get("page")
        if classification == "public_mapped":
            if mapped_pages.get(page) != item.get("capability_id"):
                errors.append("public_page_capability_binding_mismatch")
        elif classification == "blocker_pending_mapping":
            if item.get("capability_id") is not None or page in mapped_pages:
                errors.append("blocked_page_must_not_claim_mapping")
        else:
            # F25-A has no source proof that a registered route is removed or hidden.
            errors.append("hidden_or_test_page_requires_source_attestation")
    if set(mapped_pages) != {item.get("page") for item in inventory if item.get("classification") == "public_mapped"}:
        errors.append("capability_public_page_set_mismatch")
    if capability.get("allowed_page_classifications") != PAGE_CLASSIFICATIONS or capability.get("unmapped_public_capability_policy") != "block_or_hide_before_review":
        errors.append("capability_inventory_policy_incomplete")

    if zero_context.get("status") != "pending_external" or zero_context.get("automation_may_approve") is not False:
        errors.append("zero_context_review_must_remain_pending")
    if set(zero_context.get("allowed_inputs", [])) != {"submitted_materials", "test_account", "frozen_release_candidate"} or set(zero_context.get("forbidden_assistance", [])) != {"oral_supplement", "database_mutation", "temporary_privilege", "live_debugging", "out_of_band_instruction"} or zero_context.get("reviewer_id") is not None:
        errors.append("zero_context_contract_incomplete")
    if zero_context.get("required_outcomes") != REQUIRED_ZERO_CONTEXT_OUTCOMES:
        errors.append("zero_context_required_outcomes_incomplete")
    if freeze.get("current_snapshot") is not None or freeze.get("status") != "pending_external" or freeze.get("production_gate_eligible") is not False:
        errors.append("review_freeze_must_remain_pending")
    if set(freeze.get("frozen_inputs", [])) != {"backend_contract", "test_accounts", "test_data", "miniprogram_package", "backend_image", "cloudbase_target", "privacy_text", "base_library"}:
        errors.append("review_freeze_contract_incomplete")
    if freeze.get("invalidation_rules") != EXPECTED_INVALIDATION_RULES:
        errors.append("review_freeze_invalidation_targets_incomplete")
    if raci.get("assignments") != [] or raci.get("automation_may_sign") is not False or raci.get("production_gate_eligible") is not False:
        errors.append("raci_must_remain_unassigned")
    if set(raci.get("domains", [])) != {"filing_and_category", "privacy", "psychology_content", "deployment", "database", "ai_supplier", "device_acceptance", "incident_response"} or raci.get("required_roles") != ["responsible", "accountable", "consulted", "informed"]:
        errors.append("raci_contract_incomplete")
    real_items = real_world.get("items", [])
    real_ids = [item.get("id") for item in real_items]
    if len(real_ids) != len(set(real_ids)):
        errors.append("real_world_item_ids_must_be_unique")
    if any(item.get("status") != "pending_external" for item in real_items) or real_world.get("automation_may_approve") is not False or real_world.get("production_gate_eligible") is not False:
        errors.append("real_world_evidence_must_remain_pending")
    if set(real_ids) != {"core_funnel", "failure_recovery", "user_understanding_interview", "human_processing_capacity"} or any(item.get("owner") is not None for item in real_items) or real_world.get("allowed_terminal_states") != ["evidence_ready", "human_verified"]:
        errors.append("real_world_contract_incomplete")
    return errors


def status_summary(definitions: dict[str, dict[str, Any]] | None = None) -> dict[str, int]:
    definitions = definitions or load_definitions()
    catalog = definitions["catalog"]
    capability = definitions["capability"]
    raci = definitions["raci"]
    real_world = definitions["real_world"]
    return {
        "platform_checks_total": len(catalog["platform_checks"]),
        "platform_checks_pending": sum(item["status"] == "pending_external" for item in catalog["platform_checks"]),
        "device_slots_total": len(catalog["device_slots"]),
        "device_slots_pending": sum(item["status"] == "pending_external" for item in catalog["device_slots"]),
        "capabilities_total": len(capability["capabilities"]),
        "capabilities_blocking": sum(item["status"] == "blocking_pending_external" for item in capability["capabilities"]),
        "raci_domains_total": len(raci["domains"]),
        "raci_unassigned": len(raci["domains"]) - len(raci["assignments"]),
        "real_world_items_total": len(real_world["items"]),
        "real_world_items_pending": sum(item["status"] == "pending_external" for item in real_world["items"]),
    }


def build_baseline(definitions: dict[str, dict[str, Any]] | None = None) -> dict[str, Any]:
    definitions = definitions or load_definitions()
    return {
        "schema": "safehome.rc0810.wechat-platform-baseline.v1",
        "phase": "F25-A",
        "captured_at": datetime.now(timezone.utc).isoformat(),
        **platform_source_snapshot(),
        "definition_hashes": {
            relative: sha256_file(path) for relative, path in definition_paths().items()
        },
        "status_summary": status_summary(definitions),
        "production_gate_eligible": False,
        "status": "definition_ready",
    }


def validate_definition(baseline_path: Path = BASELINE_PATH) -> dict[str, Any]:
    errors: list[str] = []
    try:
        baseline = load_json(baseline_path)
        definitions = load_definitions()
        schema = definitions["baseline_schema"]
        catalog = definitions["catalog"]
        capability = definitions["capability"]
        zero_context = definitions["zero_context"]
        freeze = definitions["freeze"]
        raci = definitions["raci"]
        real_world = definitions["real_world"]
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        return {"valid": False, "status": "invalid", "phase": "F25-A", "production_gate_eligible": False, "errors": [f"definition_missing_or_invalid:{exc}"]}
    for problem in Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(baseline):
        errors.append(f"baseline_schema:{problem.message}")
    source = platform_source_snapshot()
    for field in ("head", "head_tree", "source_tree", "dirty_diff_sha256", "source_manifest_sha256"):
        if baseline.get(field) != source[field]:
            errors.append(f"{field}_mismatch")
    expected_hashes = {relative: sha256_file(path) for relative, path in definition_paths().items()}
    if baseline.get("definition_hashes") != expected_hashes:
        errors.append("definition_hash_mismatch")
    if baseline.get("status_summary") != status_summary():
        errors.append("status_summary_mismatch")
    errors.extend(validate_semantics(definitions))
    if catalog.get("subtasks") != [f"F25.{index}" for index in range(1, 15)]:
        errors.append("subtask_catalog_incomplete")
    if catalog.get("production_gate_eligible") is not False or baseline.get("production_gate_eligible") is not False:
        errors.append("production_gate_must_remain_closed")
    if catalog.get("external_identities") != []:
        errors.append("external_identity_must_remain_unassigned")
    expected_binding = {
        "miniprogram_package_sha256": None,
        "backend_image_digest": None,
        "cloudbase_config_sha256": None,
        "privacy_text_sha256": None,
        "base_library_version": None,
        "status": "pending_external",
    }
    if catalog.get("artifact_binding") != expected_binding:
        errors.append("artifact_binding_must_remain_pending")
    expected_platform_checks = {
        "appid_subject", "service_category", "interface_permissions", "legal_domains",
        "cloudbase_environment", "privacy_guideline", "filing_status", "qualification_materials",
    }
    if {item.get("id") for item in catalog.get("platform_checks", [])} != expected_platform_checks:
        errors.append("platform_check_catalog_incomplete")
    if any(item.get("status") != "pending_external" for item in catalog.get("platform_checks", [])):
        errors.append("platform_check_must_remain_pending")
    if catalog.get("account_scenarios") != ACCOUNT_SCENARIOS:
        errors.append("account_scenario_catalog_incomplete")
    if catalog.get("message_scenarios") != MESSAGE_SCENARIOS:
        errors.append("message_scenario_catalog_incomplete")
    if catalog.get("devtools_checks") != ["compile", "subpackages", "package_size", "network", "base_library", "page_warnings"]:
        errors.append("devtools_catalog_incomplete")
    slots = {item.get("platform"): item for item in catalog.get("device_slots", [])}
    if set(slots) != {"ios", "android"} or any(item.get("scenarios") != DEVICE_SCENARIOS for item in slots.values()):
        errors.append("device_scenario_catalog_incomplete")
    if any(item.get("status") != "pending_external" or item.get("device_id") or item.get("operator_id") for item in catalog.get("device_slots", [])):
        errors.append("device_evidence_must_remain_pending")
    journeys = catalog.get("journeys", {})
    if journeys.get("participant_core") != ["goal", "diary", "feedback", "training", "checkin", "weekly_report", "supervision"] or journeys.get("production_negative") != ["internal_route_hidden", "temporary_privilege_disabled", "debug_entry_hidden"] or journeys.get("status") != "pending_external":
        errors.append("journey_catalog_incomplete")
    if catalog.get("review_materials") != ["review_notes", "test_account_guide", "feature_paths", "boundary_statement", "failure_recovery"]:
        errors.append("review_material_catalog_incomplete")
    evidence_contract = catalog.get("evidence_contract", {})
    if set(evidence_contract.get("required_fields", [])) != {"owner", "reviewer", "captured_at", "valid_until", "invalidation_conditions", "artifact_sha256", "request_id"} or evidence_contract.get("automation_max_state") != "evidence_ready" or evidence_contract.get("states") != ["pending_external", "evidence_ready", "human_verified", "platform_approved", "stale"]:
        errors.append("evidence_contract_incomplete")
    if any(item.get("status") != "blocking_pending_external" for item in capability.get("capabilities", [])):
        errors.append("capability_mapping_must_block")
    expected_capabilities = {"account_access", "goal_setting", "emotion_diary", "supportive_feedback", "training_cards", "practice_checkin", "weekly_report", "human_supervision"}
    if {item.get("id") for item in capability.get("capabilities", [])} != expected_capabilities or any(not item.get("pages") or not item.get("apis") or not item.get("data_domains") or item.get("service_category") is not None or item.get("qualification") is not None or item.get("privacy_declaration") is not None for item in capability.get("capabilities", [])) or capability.get("unmapped_public_capability_policy") != "block_or_hide_before_review":
        errors.append("capability_mapping_incomplete")
    if zero_context.get("status") != "pending_external" or zero_context.get("automation_may_approve") is not False:
        errors.append("zero_context_review_must_remain_pending")
    if set(zero_context.get("allowed_inputs", [])) != {"submitted_materials", "test_account", "frozen_release_candidate"} or set(zero_context.get("forbidden_assistance", [])) != {"oral_supplement", "database_mutation", "temporary_privilege", "live_debugging", "out_of_band_instruction"} or zero_context.get("reviewer_id") is not None:
        errors.append("zero_context_contract_incomplete")
    if freeze.get("current_snapshot") is not None or freeze.get("status") != "pending_external":
        errors.append("review_freeze_must_remain_pending")
    if set(freeze.get("frozen_inputs", [])) != {"backend_contract", "test_accounts", "test_data", "miniprogram_package", "backend_image", "cloudbase_target", "privacy_text", "base_library"} or set(freeze.get("invalidation_rules", {})) != {"package_or_image", "cloudbase_target", "privacy_text", "base_library", "test_account_or_data"}:
        errors.append("review_freeze_contract_incomplete")
    if raci.get("assignments") != [] or raci.get("automation_may_sign") is not False:
        errors.append("raci_must_remain_unassigned")
    if set(raci.get("domains", [])) != {"filing_and_category", "privacy", "psychology_content", "deployment", "database", "ai_supplier", "device_acceptance", "incident_response"} or raci.get("required_roles") != ["responsible", "accountable", "consulted", "informed"]:
        errors.append("raci_contract_incomplete")
    if any(item.get("status") != "pending_external" for item in real_world.get("items", [])) or real_world.get("automation_may_approve") is not False:
        errors.append("real_world_evidence_must_remain_pending")
    if {item.get("id") for item in real_world.get("items", [])} != {"core_funnel", "failure_recovery", "user_understanding_interview", "human_processing_capacity"} or any(item.get("owner") is not None for item in real_world.get("items", [])) or real_world.get("allowed_terminal_states") != ["evidence_ready", "human_verified"]:
        errors.append("real_world_contract_incomplete")
    return {
        "valid": not errors,
        "status": "definition_ready" if not errors else "invalid",
        "phase": "F25-A",
        "source_tree": baseline.get("source_tree"),
        "status_summary": baseline.get("status_summary", {}),
        "production_gate_eligible": False,
        "errors": errors,
    }


def run_self_checks() -> dict[str, bool]:
    baseline = load_json(BASELINE_PATH)
    mutations = {}
    for name, field, value in (
        ("source_drift_rejected", "source_tree", "0" * 40),
        ("definition_drift_rejected", "definition_hashes", {}),
        ("summary_drift_rejected", "status_summary", {}),
    ):
        candidate = copy.deepcopy(baseline)
        candidate[field] = value
        with tempfile.TemporaryDirectory(prefix="rc0810-f25-self-check-") as directory:
            path = Path(directory) / "candidate.json"
            path.write_text(json.dumps(candidate), encoding="utf-8")
            mutations[name] = not validate_definition(path)["valid"]
    definitions = load_definitions()
    semantic_mutations: list[tuple[str, dict[str, dict[str, Any]]]] = []
    release = copy.deepcopy(definitions)
    release["capability"]["production_gate_eligible"] = True
    semantic_mutations.append(("release_flag_drift_rejected", release))
    outcomes = copy.deepcopy(definitions)
    outcomes["zero_context"]["required_outcomes"] = []
    semantic_mutations.append(("required_outcome_drift_rejected", outcomes))
    invalidation = copy.deepcopy(definitions)
    invalidation["freeze"]["invalidation_rules"]["cloudbase_target"] = []
    semantic_mutations.append(("invalidation_target_drift_rejected", invalidation))
    duplicate = copy.deepcopy(definitions)
    duplicate["catalog"]["platform_checks"].append(copy.deepcopy(duplicate["catalog"]["platform_checks"][0]))
    semantic_mutations.append(("duplicate_matrix_id_rejected", duplicate))
    unknown_state = copy.deepcopy(definitions)
    unknown_state["real_world"]["items"][0]["status"] = "machine_approved"
    semantic_mutations.append(("unknown_state_rejected", unknown_state))
    for name, candidate in semantic_mutations:
        mutations[name] = bool(validate_semantics(candidate))
    return mutations


def write_validated_baseline(
    target: Path = BASELINE_PATH,
    *,
    definitions: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    definitions = definitions or load_definitions()
    semantic_errors = validate_semantics(definitions)
    if semantic_errors:
        return {
            "valid": False,
            "status": "invalid",
            "phase": "F25-A",
            "production_gate_eligible": False,
            "errors": semantic_errors,
        }
    target = target.resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.is_relative_to(ROOT):
        temporary_parent = ROOT / ".codex_tmp" / "rc0810" / "f25-baseline-write"
        temporary_parent.mkdir(parents=True, exist_ok=True)
    else:
        temporary_parent = target.parent
    handle, raw_path = tempfile.mkstemp(prefix="candidate-", suffix=".json", dir=temporary_parent)
    os.close(handle)
    temporary_path = Path(raw_path)
    try:
        temporary_path.write_text(
            json.dumps(build_baseline(definitions), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        result = validate_definition(temporary_path)
        if not result["valid"]:
            return result
        os.replace(temporary_path, target)
        return validate_definition(target)
    finally:
        temporary_path.unlink(missing_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", type=Path, default=BASELINE_PATH)
    parser.add_argument("--write-baseline", action="store_true")
    parser.add_argument("--self-check", action="store_true")
    args = parser.parse_args()
    if args.write_baseline:
        result = write_validated_baseline(args.baseline)
    else:
        result = validate_definition(args.baseline)
    if args.self_check and result["valid"]:
        checks = run_self_checks()
        result["self_checks"] = checks
        result["valid"] = all(checks.values())
        result["status"] = "self_check_passed" if result["valid"] else "invalid"
        if not result["valid"]:
            result["errors"].append("self_check_failed")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
