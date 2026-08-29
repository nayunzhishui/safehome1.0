from __future__ import annotations

import copy
import importlib.util
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CONFIG_ROOT = ROOT / "config" / "rc0810"
SCRIPT = ROOT / "scripts" / "verify_rc0810_f01_profiles.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("verify_rc0810_f01_profiles", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _copy_contracts(tmp_path: Path) -> Path:
    target = tmp_path / "contracts"
    target.mkdir()
    for name in (
        "build_profile.schema.json",
        "build_profiles.json",
        "capability_matrix.json",
        "environment_inventory.json",
        "release_population_and_client_contract.json",
    ):
        (target / name).write_bytes((CONFIG_ROOT / name).read_bytes())
    return target


def _mutate(path: Path, callback) -> None:
    payload = json.loads(path.read_text(encoding="utf-8"))
    callback(payload)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def test_f01_contract_files_and_five_artifacts_exist():
    module = _load_module()
    result = module.verify(CONFIG_ROOT, ROOT)
    assert result["valid"], result["errors"]
    assert set(result["summary"]["artifact_profiles"]) == {
        "development_miniprogram",
        "validation_miniprogram",
        "production_participant_miniprogram",
        "validation_backend",
        "production_backend",
    }


def test_f01_inventory_hashes_current_sources():
    result = _load_module().verify(CONFIG_ROOT, ROOT)
    assert result["summary"]["source_inventory_verified"] is True
    assert result["summary"]["source_count"] >= 10


def test_f01_unknown_profile_field_is_rejected(tmp_path: Path):
    contracts = _copy_contracts(tmp_path)
    _mutate(contracts / "build_profiles.json", lambda p: p.update({"typo_field": True}))
    result = _load_module().verify(contracts, ROOT)
    assert "unknown_field:build_profiles:typo_field" in result["errors"]


def test_f01_missing_required_field_is_rejected(tmp_path: Path):
    contracts = _copy_contracts(tmp_path)
    _mutate(contracts / "build_profiles.json", lambda p: p.pop("schema_version"))
    result = _load_module().verify(contracts, ROOT)
    assert "missing_field:build_profiles:schema_version" in result["errors"]


def test_f01_unknown_environment_is_rejected(tmp_path: Path):
    contracts = _copy_contracts(tmp_path)
    _mutate(
        contracts / "build_profiles.json",
        lambda p: p["artifact_profiles"][0].update({"target_environment": "prodution"}),
    )
    result = _load_module().verify(contracts, ROOT)
    assert "unknown_target_environment:development_miniprogram:prodution" in result["errors"]


def test_f01_production_profiles_are_fail_closed():
    profiles = json.loads((CONFIG_ROOT / "build_profiles.json").read_text(encoding="utf-8"))
    for profile in profiles["artifact_profiles"]:
        if profile["target_environment"] == "production":
            assert profile["production_gate_eligible"] is False
            assert not any(profile["capabilities"].values())


def test_f01_production_rejects_nonproduction_reference(tmp_path: Path):
    contracts = _copy_contracts(tmp_path)
    _mutate(
        contracts / "build_profiles.json",
        lambda p: p["artifact_profiles"][2]["references"].update(
            {"cloud_env_id": "validation-safehome", "api_base_url": "http://127.0.0.1:5000"}
        ),
    )
    result = _load_module().verify(contracts, ROOT)
    assert any(error.startswith("production_cross_reference:") for error in result["errors"])


def test_f01_artifact_digest_is_stable_across_build_time():
    module = _load_module()
    first = module.build_summary("validation_backend", "2026-08-11T00:00:00Z", CONFIG_ROOT, ROOT)
    second = module.build_summary("validation_backend", "2026-08-11T00:01:00Z", CONFIG_ROOT, ROOT)
    assert first["artifact_digest"] == second["artifact_digest"]
    assert first["build_time"] != second["build_time"]


def test_f01_build_summary_binds_commit_tree_and_contract():
    summary = _load_module().build_summary(
        "development_miniprogram", "2026-08-11T00:00:00Z", CONFIG_ROOT, ROOT
    )
    assert summary["profile_id"] == "development_miniprogram"
    assert summary["schema_version"] == "1.0.0"
    assert len(summary["commit"]) == 40
    assert len(summary["source_tree"]) == 40
    assert len(summary["capability_digest"]) == 64
    assert len(summary["artifact_digest"]) == 64


def test_f01_capability_matrix_covers_backend_boolean_flags():
    result = _load_module().verify(CONFIG_ROOT, ROOT)
    assert result["summary"]["capability_flags_verified"] is True
    assert result["summary"]["capability_flag_count"] >= 20


def test_f01_every_capability_has_default_production_owner_and_rollback():
    matrix = json.loads((CONFIG_ROOT / "capability_matrix.json").read_text(encoding="utf-8"))
    for entry in matrix["flags"]:
        assert set(entry) == {"name", "default", "production", "owner", "rollback"}
        assert entry["owner"]
        assert entry["rollback"]


def test_f01_release_population_is_pending_and_fail_closed():
    contract = json.loads(
        (CONFIG_ROOT / "release_population_and_client_contract.json").read_text(encoding="utf-8")
    )
    population = contract["release_population_manifest"]
    assert population["status"] == "pending_external"
    assert population["production_gate_eligible"] is False
    assert population["max_users"] == 0
    assert population["max_organizations"] == 0
    assert population["regions"] == []


def test_f01_population_expansion_invalidates_evidence():
    module = _load_module()
    contract = json.loads(
        (CONFIG_ROOT / "release_population_and_client_contract.json").read_text(encoding="utf-8")
    )
    current = contract["release_population_manifest"]
    expanded = copy.deepcopy(current)
    expanded["max_users"] = 1
    assert module.population_expanded(current, expanded) is True
    assert set(current["expansion_invalidates"]) >= {"security", "privacy", "real_device", "release_review"}


def test_f01_client_negotiation_allows_compatible_and_rejects_incompatible():
    module = _load_module()
    assert module.negotiate_client("1.0.0", 1, CONFIG_ROOT) == {
        "action": "allow_validation_only",
        "protocol": 1,
        "reason": None,
    }
    assert module.negotiate_client("0.9.0", 1, CONFIG_ROOT)["action"] == "require_upgrade"
    assert module.negotiate_client("1.0.0", 0, CONFIG_ROOT)["action"] == "safe_reject"
    assert module.negotiate_client("1.0.0", 99, CONFIG_ROOT)["action"] == "safe_reject"


def test_f01_source_drift_is_rejected(tmp_path: Path):
    contracts = _copy_contracts(tmp_path)
    _mutate(
        contracts / "environment_inventory.json",
        lambda p: p["sources"][0].update({"sha256": "0" * 64}),
    )
    result = _load_module().verify(contracts, ROOT)
    assert any(error.startswith("source_hash_mismatch:") for error in result["errors"])


def test_f01_production_dockerfile_remains_gate_ineligible():
    inventory = json.loads((CONFIG_ROOT / "environment_inventory.json").read_text(encoding="utf-8"))
    docker = next(item for item in inventory["sources"] if item["path"] == "Dockerfile")
    assert docker["classification"] == "production_backend_definition_fail_closed"
    assert docker["production_eligible"] is False


def test_f01_cross_layer_sources_are_explicit_and_hashed():
    inventory = json.loads((CONFIG_ROOT / "environment_inventory.json").read_text(encoding="utf-8"))
    layers = {item["layer"] for item in inventory["sources"]}
    assert {"backend", "deployment", "miniprogram", "web", "shared", "docs"} <= layers
    assert all(len(item["sha256"]) == 64 for item in inventory["sources"])


def test_f01_cli_default_and_self_check_pass():
    default = subprocess.run([sys.executable, str(SCRIPT)], cwd=ROOT, capture_output=True, text=True)
    self_check = subprocess.run(
        [sys.executable, str(SCRIPT), "--self-check"], cwd=ROOT, capture_output=True, text=True
    )
    assert default.returncode == 0, default.stdout + default.stderr
    assert self_check.returncode == 0, self_check.stdout + self_check.stderr
