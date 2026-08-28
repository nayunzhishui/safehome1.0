"""RC0810-F01 build profile contract verifier.

This is a definition and static-integrity check. It never builds, deploys, or
loads secrets. Production profiles remain ineligible until external gates pass.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG_ROOT = ROOT / "config" / "rc0810"
PROFILE_FILE = "build_profiles.json"
INVENTORY_FILE = "environment_inventory.json"
MATRIX_FILE = "capability_matrix.json"
POPULATION_FILE = "release_population_and_client_contract.json"
SCHEMA_FILE = "build_profile.schema.json"
EXPECTED_ARTIFACTS = {
    "development_miniprogram",
    "validation_miniprogram",
    "production_participant_miniprogram",
    "validation_backend",
    "production_backend",
}
PROFILE_KEYS = {
    "profile_id",
    "artifact_class",
    "target_environment",
    "production_gate_eligible",
    "capabilities",
    "references",
    "required_inputs",
    "blocked_by",
}
CAPABILITY_KEYS = {
    "debug_pages",
    "showcase",
    "research_workbench",
    "ai_sandbox",
    "real_ai_provider",
    "production_writes",
    "privacy_execution",
    "platform_send",
    "local_http",
}
SOURCE_CAPABILITY_RE = re.compile(r"^\s*([A-Z][A-Z0-9_]+)\s*=.*os\.environ\.get\(", re.MULTILINE)


def _read(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    # Repository text artifacts may be checked out with CRLF on Windows or LF
    # in CI.  Bind the inventory to stable content bytes, not checkout style.
    raw = path.read_bytes()
    normalized = raw.replace(b"\\r\\n", b"\\n").replace(b"\\r", b"\\n")
    return hashlib.sha256(normalized).hexdigest()


def _canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def _error(errors: list[str], value: str) -> None:
    if value not in errors:
        errors.append(value)


def _check_object_keys(value: Any, allowed: set[str], label: str, errors: list[str]) -> None:
    if not isinstance(value, dict):
        _error(errors, f"not_object:{label}")
        return
    for key in value:
        if key not in allowed:
            _error(errors, f"unknown_field:{label}:{key}")


def _source_flags(root: Path) -> set[str]:
    text = (root / "backend" / "config.py").read_text(encoding="utf-8")
    tree = ast.parse(text)
    names: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if not (
            isinstance(node.func, ast.Attribute)
            and node.func.attr == "get"
            and isinstance(node.func.value, ast.Attribute)
            and node.func.value.attr == "environ"
            and isinstance(node.func.value.value, ast.Name)
            and node.func.value.value.id == "os"
            and node.args
            and isinstance(node.args[0], ast.Constant)
            and isinstance(node.args[0].value, str)
        ):
            continue
        env_name = node.args[0].value
        if env_name.endswith(("_ENABLED", "_ALLOWED", "_FROZEN", "_UNLOCKED", "_APPROVED", "_ENFORCED", "_HEADERS", "_SQLITE")):
            names.add(env_name)
    return {
        name
        for name in names
    }


def _schema_contract(config_root: Path, errors: list[str]) -> None:
    schema = _read(config_root / SCHEMA_FILE)
    if schema.get("$id") != "safehome.rc0810.build-profile.v1":
        _error(errors, "schema_id_mismatch")
    if schema.get("additionalProperties") is not False:
        _error(errors, "schema_not_strict")
    profiles = _read(config_root / PROFILE_FILE)
    _check_object_keys(
        profiles,
        {"schema", "schema_version", "decision_status", "environments", "artifact_profiles", "source_contract", "non_go_reasons"},
        "build_profiles",
        errors,
    )
    for field in ("schema", "schema_version", "decision_status", "environments", "artifact_profiles", "source_contract", "non_go_reasons"):
        if field not in profiles:
            _error(errors, f"missing_field:build_profiles:{field}")


def _verify_inventory(config_root: Path, root: Path, errors: list[str]) -> tuple[bool, int]:
    inventory = _read(config_root / INVENTORY_FILE)
    _check_object_keys(inventory, {"schema", "schema_version", "inventory_status", "sensitive_values_included", "sources", "environment_variable_classes", "current_fact_findings"}, "environment_inventory", errors)
    if inventory.get("sensitive_values_included") is not False:
        _error(errors, "inventory_contains_sensitive_values")
    sources = inventory.get("sources", [])
    for item in sources:
        path = root / item.get("path", "")
        if not path.is_file():
            _error(errors, f"source_missing:{item.get('path')}")
            continue
        if item.get("sha256") != _sha256(path):
            _error(errors, f"source_hash_mismatch:{item.get('path')}")
        if not item.get("layer") or not item.get("classification"):
            _error(errors, f"source_metadata_missing:{item.get('path')}")
    return not any(item.startswith(("source_missing:", "source_hash_mismatch:")) for item in errors), len(sources)


def _verify_profiles(config_root: Path, errors: list[str]) -> list[dict[str, Any]]:
    profiles = _read(config_root / PROFILE_FILE)
    if profiles.get("schema") != "safehome.rc0810.build-profiles.v1":
        _error(errors, "profile_schema_mismatch")
    artifacts = profiles.get("artifact_profiles", [])
    if {item.get("profile_id") for item in artifacts} != EXPECTED_ARTIFACTS:
        _error(errors, "artifact_profile_set_mismatch")
    for item in artifacts:
        profile_id = item.get("profile_id", "unknown")
        _check_object_keys(item, PROFILE_KEYS, f"artifact:{profile_id}", errors)
        if item.get("target_environment") not in {"development", "validation", "production"}:
            _error(errors, f"unknown_target_environment:{profile_id}:{item.get('target_environment')}")
        caps = item.get("capabilities", {})
        if set(caps) != CAPABILITY_KEYS:
            _error(errors, f"capability_set_mismatch:{profile_id}")
        if item.get("target_environment") == "production":
            if item.get("production_gate_eligible") is not False:
                _error(errors, f"production_gate_open:{profile_id}")
            if any(caps.values()):
                _error(errors, f"production_capability_open:{profile_id}")
            refs = item.get("references", {})
            forbidden = ("validation", "development", "127.0.0.1", "localhost", "local-http")
            for key, value in refs.items():
                if value and any(token in str(value).lower() for token in forbidden):
                    _error(errors, f"production_cross_reference:{profile_id}:{key}")
    return artifacts


def _verify_capabilities(config_root: Path, root: Path, errors: list[str]) -> int:
    matrix = _read(config_root / MATRIX_FILE)
    _check_object_keys(matrix, {"schema", "schema_version", "source", "production_policy", "flags"}, "capability_matrix", errors)
    expected = _source_flags(root)
    actual = {item.get("name") for item in matrix.get("flags", [])}
    if expected != actual:
        _error(errors, "capability_flag_inventory_mismatch")
    for item in matrix.get("flags", []):
        if set(item) != {"name", "default", "production", "owner", "rollback"}:
            _error(errors, f"capability_metadata_incomplete:{item.get('name')}")
        if not item.get("owner") or not item.get("rollback"):
            _error(errors, f"capability_owner_or_rollback_missing:{item.get('name')}")
        if item.get("name") != "CONTENT_GOVERNANCE_ENFORCED" and item.get("production") is not False:
            _error(errors, f"production_capability_not_closed:{item.get('name')}")
    return len(actual)


def _verify_population(config_root: Path, errors: list[str]) -> None:
    contract = _read(config_root / POPULATION_FILE)
    _check_object_keys(contract, {"schema", "schema_version", "release_population_manifest", "client_compatibility"}, "population_client", errors)
    population = contract.get("release_population_manifest", {})
    if population.get("status") != "pending_external" or population.get("production_gate_eligible") is not False:
        _error(errors, "population_gate_not_pending")
    if population.get("max_users") != 0 or population.get("max_organizations") != 0 or population.get("regions") != []:
        _error(errors, "population_not_empty_fail_closed")
    if set(population.get("expansion_invalidates", [])) != {"security", "privacy", "real_device", "release_review"}:
        _error(errors, "population_invalidation_set_mismatch")
    client = contract.get("client_compatibility", {})
    if client.get("minimum_protocol_version") != 1 or client.get("maximum_protocol_version") != 1:
        _error(errors, "client_protocol_range_invalid")
    if client.get("unknown_protocol_action") != "safe_reject" or client.get("old_client_action") != "require_upgrade":
        _error(errors, "client_compatibility_not_fail_closed")


def population_expanded(current: dict[str, Any], candidate: dict[str, Any]) -> bool:
    keys = ("age_scope", "risk_scope", "invite_mode", "relationship_mode", "max_users", "max_organizations", "regions", "inclusion_rules")
    return any(current.get(key) != candidate.get(key) for key in keys)


def negotiate_client(version: str, protocol: int, config_root: Path = DEFAULT_CONFIG_ROOT) -> dict[str, Any]:
    contract = _read(config_root / POPULATION_FILE)["client_compatibility"]
    if protocol < contract["minimum_protocol_version"] or protocol > contract["maximum_protocol_version"]:
        return {"action": contract["unknown_protocol_action"], "protocol": protocol, "reason": "unknown_protocol"}
    if tuple(int(part) for part in version.split(".")[:2]) < (1, 0):
        return {"action": contract["old_client_action"], "protocol": protocol, "reason": "client_version_too_old"}
    return {"action": contract["compatible_action"], "protocol": protocol, "reason": None}


def _git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def build_summary(profile_id: str, build_time: str, config_root: Path = DEFAULT_CONFIG_ROOT, root: Path = ROOT) -> dict[str, Any]:
    profiles = _read(config_root / PROFILE_FILE)
    profile = next(item for item in profiles["artifact_profiles"] if item["profile_id"] == profile_id)
    matrix = _read(config_root / MATRIX_FILE)
    capability_digest = hashlib.sha256(_canonical(matrix["flags"])).hexdigest()
    stable_material = {"profile": profile, "schema_version": profiles["schema_version"], "capability_digest": capability_digest}
    return {
        "profile_id": profile_id,
        "schema_version": profiles["schema_version"],
        "environment": profile["target_environment"],
        "commit": _git("rev-parse", "HEAD"),
        "source_tree": _git("rev-parse", "HEAD^{tree}"),
        "build_time": build_time,
        "capability_digest": capability_digest,
        "artifact_digest": hashlib.sha256(_canonical(stable_material)).hexdigest(),
    }


def verify(config_root: Path = DEFAULT_CONFIG_ROOT, root: Path = ROOT) -> dict[str, Any]:
    errors: list[str] = []
    _schema_contract(config_root, errors)
    inventory_ok, source_count = _verify_inventory(config_root, root, errors)
    artifacts = _verify_profiles(config_root, errors)
    capability_count = _verify_capabilities(config_root, root, errors)
    _verify_population(config_root, errors)
    summary = {
        "artifact_profiles": sorted(item.get("profile_id") for item in artifacts),
        "source_inventory_verified": inventory_ok,
        "source_count": source_count,
        "capability_flags_verified": "capability_flag_inventory_mismatch" not in errors,
        "capability_flag_count": capability_count,
        "production_gate_eligible": False,
        "status": "definition_ready" if not errors else "invalid",
    }
    return {"valid": not errors, "errors": errors, "summary": summary}


def _self_check(config_root: Path, root: Path) -> dict[str, Any]:
    result = verify(config_root, root)
    checks = {
        "default_contract": result["valid"],
        "production_fail_closed": result["summary"]["production_gate_eligible"] is False,
        "stable_digest": build_summary("validation_backend", "a", config_root, root)["artifact_digest"] == build_summary("validation_backend", "b", config_root, root)["artifact_digest"],
    }
    return {"valid": result["valid"] and all(checks.values()), "checks": checks, "errors": result["errors"]}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-check", action="store_true")
    args = parser.parse_args()
    payload = _self_check(DEFAULT_CONFIG_ROOT, ROOT) if args.self_check else verify(DEFAULT_CONFIG_ROOT, ROOT)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
