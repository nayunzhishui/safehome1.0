import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / "scripts" / "run_tasks_37_38.py"
SOURCE_GENERATOR = ROOT / "scripts" / "generate_task38_source_registry.py"
REGISTRY = ROOT / "config" / "task37_38_registry.json"
FOUNDATION = ROOT / "config" / "task37_38_foundation.json"
SOURCE_REGISTRY = ROOT / "content" / "task38_source_registry.json"


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def _expected_scope():
    return [
        *[f"T37-P{number:02d}" for number in range(5)],
        *[f"T38-F{number:02d}" for number in range(26)],
        *[f"T37-A{number:02d}" for number in range(1, 8)],
        *[f"T37-B{number:02d}" for number in range(1, 6)],
        *[f"T37-C{number:02d}" for number in range(1, 11)],
        *[f"T37-R{number:02d}" for number in range(1, 5)],
    ]


def test_registry_covers_all_tasks_and_has_an_acyclic_dependency_graph():
    runner = _load_module(RUNNER, "tasks37_38_runner")
    payload = runner.load_registry()
    assert set(payload["scope"]) == set(_expected_scope())
    assert len(payload["scope"]) == 57
    assert [task["id"] for task in payload["tasks"]] == payload["execution_order"]
    assert runner.topological_order(payload) == payload["execution_order"]
    assert payload["tasks"][0]["id"] == "T37-P00"
    assert payload["tasks"][1]["id"] == "T38-F00"


def test_owner_decisions_open_participant_entry_without_faking_professional_service():
    payload = json.loads(REGISTRY.read_text(encoding="utf-8"))
    decisions = payload["owner_decisions"]
    assert decisions["participant_ai_entry"]["development_open"] is True
    assert decisions["participant_ai_entry"]["production_max_service_level_without_humans"] == "L0"
    assert decisions["participant_ai_entry"]["pretend_human_review_allowed"] is False
    assert decisions["individual_risk"]["mode"] == "shadow_human_review_signal"
    assert decisions["individual_risk"]["automatic_action_allowed"] is False
    assert decisions["training_consent"]["default_selected"] is False
    assert decisions["training_consent"]["refusal_blocks_basic_service"] is False
    assert decisions["simulated_roles"]["count_as_human_signoff"] is False


def test_production_automation_is_conditional_and_never_accepts_simulated_signoff():
    payload = json.loads(REGISTRY.read_text(encoding="utf-8"))
    policy = payload["policy"]
    assert policy["production_automation_authorized"] is True
    assert policy["production_automation_requires_backup_restore_canary_kill_switch"] is True
    assert policy["simulated_agent_may_sign_external_gate"] is False
    assert policy["dirty_worktree_policy"] == "observe_only_never_revert"
    assert policy["secret_values_may_be_recorded"] is False
    assert policy["temporary_showcase_bypass_counts_as_formal_permission_evidence"] is False


def test_foundation_freezes_schema_commit_and_core_asset_fingerprints():
    payload = json.loads(FOUNDATION.read_text(encoding="utf-8"))
    assert payload["schema"] == "safehome.tasks37_38.foundation.v1"
    assert payload["database"]["schema_version"] == "2026_07_27_030"
    assert len(payload["git"]["head"]) == 40
    assert payload["git"]["dirty_worktree_policy"] == "observe_only_never_revert"
    assert len(payload["assets"]) >= 12
    for asset in payload["assets"]:
        assert len(asset["sha256"]) == 64
        assert asset["bytes"] > 0
        assert (ROOT / asset["path"]).is_file()
    assert payload["current_capabilities"]["affective_computing"] == "rules_and_synthetic_only"
    assert payload["current_capabilities"]["social_network_analysis"] == "synthetic_group_descriptive_only"
    assert payload["current_capabilities"]["ai_provider"] == "fake_only"


def test_source_registry_contains_all_108_frozen_documents_with_provenance():
    payload = json.loads(SOURCE_REGISTRY.read_text(encoding="utf-8"))
    assert payload["schema"] == "safehome.task38.source-registry.v1"
    assert payload["source_count"] == 108
    assert payload["extension_counts"] == {".docx": 77, ".html": 4, ".json": 2, ".md": 25}
    assert len(payload["sources"]) == 108
    assert len({source["id"] for source in payload["sources"]}) == 108
    assert len({source["sha256"] for source in payload["sources"]}) == 108
    assert any(source["source_role"] == "therapeutic_assessment_translation_source" for source in payload["sources"])
    assert any(source["source_role"] == "engineering_reference" for source in payload["sources"])
    for source in payload["sources"]:
        assert len(source["sha256"]) == 64
        assert source["bytes"] > 0
        assert source["evidence_tier"] in {
            "method_translation_source",
            "engineering_reference",
            "project_learning_record",
        }
        assert source["product_rule_authority"] in {
            "source_or_expert_review_required",
            "engineering_reference_not_clinical_evidence",
        }


def test_source_registry_check_is_portable_without_external_source_files():
    completed = subprocess.run(
        [sys.executable, str(SOURCE_GENERATOR), "--check"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    payload = json.loads(completed.stdout)
    assert payload["valid"] is True
    assert payload["source_count"] == 108
    assert payload["external_files_reverified"] in {True, False}


def test_agent_and_rag_seams_are_separate_and_non_authoritative():
    agent_contract = (ROOT / "agents" / "task37_38" / "README.md").read_text(encoding="utf-8")
    rag_contract = (ROOT / "rag" / "task37_38" / "README.md").read_text(encoding="utf-8")
    assert "不能替代真人" in agent_contract
    assert "count_as_human_signoff = false" in agent_contract
    assert "候选隔离" in rag_contract
    assert "不得自动进入生产索引" in rag_contract


def test_runner_report_and_dry_run_use_only_ignored_recoverable_state():
    runner = _load_module(RUNNER, "tasks37_38_runner_report")
    registry = runner.load_registry()
    report = runner.report(registry)
    assert report["tasks_total"] == 57
    completed = sum(1 for task in registry["tasks"] if task["engineering_complete"])
    expected_next = next(
        (task_id for task_id in registry["execution_order"] if not next(task for task in registry["tasks"] if task["id"] == task_id)["engineering_complete"]),
        None,
    )
    assert report["tasks_engineering_complete"] == completed
    assert report["next_automatable_task"] == expected_next
    assert report["human_external_signoff_complete"] is False
    assert report["production_release_approved"] is False

    state_path = ROOT / ".codex_tmp" / "task37_38_state.json"
    previous = state_path.read_bytes() if state_path.exists() else None
    try:
        completed = subprocess.run(
            [sys.executable, str(RUNNER), "verify", "--task", "T37-P00", "--dry-run"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
    finally:
        if previous is None:
            state_path.unlink(missing_ok=True)
        else:
            state_path.write_bytes(previous)
    assert completed.returncode == 0, completed.stderr
    result = json.loads(completed.stdout)
    assert result["status"] == "dry_run"
    assert result["production_mutations_executed"] is False
    assert result["external_signoffs_executed"] is False
    ignored = subprocess.run(
        ["git", "check-ignore", ".codex_tmp/task37_38_state.json"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert ignored.returncode == 0


def test_runner_rejects_dependency_cycles_and_command_drift(tmp_path, monkeypatch):
    runner = _load_module(RUNNER, "tasks37_38_runner_failures")
    payload = json.loads(REGISTRY.read_text(encoding="utf-8"))
    payload["tasks"][0]["dependencies"] = ["T37-R04"]
    invalid = tmp_path / "invalid-registry.json"
    invalid.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    monkeypatch.setattr(runner, "REGISTRY_PATH", invalid)
    with pytest.raises(runner.RegistryError, match="依赖"):
        runner.load_registry()

    specs = [{"cwd": ".", "command": ["python", "first.py"]}]
    record = {
        "command_digest": runner.command_digest(specs),
        "outcomes": [{"command": ["python", "first.py"], "returncode": 0}],
    }
    with pytest.raises(runner.RegistryError, match="不能resume"):
        runner.resume_point(record, [{"cwd": ".", "command": ["python", "changed.py"]}])
