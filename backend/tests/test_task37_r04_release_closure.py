import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
REGISTRY = ROOT / "content" / "task37_release_execution_registry.json"
SCRIPT = ROOT / "backend" / "scripts" / "task37_r04_release_closure.py"


def _module():
    spec = importlib.util.spec_from_file_location("task37_r04_release_closure", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_r04_builds_complete_model_prompt_knowledge_and_contract_fingerprint():
    result = _module().build()
    assert result["ok"] is True
    assert result["missing_artifacts"] == []
    assert len(result["artifacts"]) == 12
    assert all(len(item["sha256"]) == 64 and item["size_bytes"] > 0 for item in result["artifacts"])
    assert len(result["artifact_set_sha256"]) == 64
    assert result["production_release_executed"] is False
    assert result["production_release_approved"] is False


def test_r04_release_notes_observation_and_rollback_thresholds_are_complete():
    payload = json.loads(REGISTRY.read_text(encoding="utf-8"))
    stage = next(item for item in payload["stages"] if item["id"] == "R04")
    assert set(stage["release_note_sections"]) == {
        "engineering_changes",
        "features_kept_closed",
        "external_gates",
        "migration_and_rollback",
        "known_limitations",
        "observation_plan",
        "owner_decision",
    }
    assert [item["id"] for item in stage["observation_windows"]] == [
        "first_30m",
        "first_2h",
        "first_24h",
        "first_72h",
    ]
    threshold_metrics = {item["metric"] for item in stage["automatic_rollback_thresholds"]}
    assert {
        "health_ready",
        "api_error_rate",
        "api_p95_ms",
        "worker_queue_age",
        "critical_safety_miss",
        "object_scope_violation",
        "privacy_incident",
        "withdrawal_propagation_failure",
        "kill_switch_health",
    } == threshold_metrics


def test_r04_human_approval_and_post_release_observation_remain_pending():
    payload = json.loads(REGISTRY.read_text(encoding="utf-8"))
    stage = next(item for item in payload["stages"] if item["id"] == "R04")
    assert stage["owner_approval_required"] is True
    assert stage["owner_approval_complete"] is False
    assert stage["post_release_observation_complete"] is False
    assert stage["production_release_executed"] is False
    assert stage["production_release_approved"] is False
