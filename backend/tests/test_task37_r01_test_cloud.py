import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
REGISTRY = ROOT / "content" / "task37_release_execution_registry.json"
SCRIPT = ROOT / "backend" / "scripts" / "task37_r01_test_cloud.py"


def _module():
    spec = importlib.util.spec_from_file_location("task37_r01_test_cloud", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_r01_covers_health_worker_monitoring_replay_fault_and_fallback():
    payload = json.loads(REGISTRY.read_text(encoding="utf-8"))
    stage = next(item for item in payload["stages"] if item["id"] == "R01")
    assert {item["id"] for item in stage["probes"]} == {
        "health",
        "deep_health",
        "ready",
        "public_monitoring",
    }
    assert {
        "computation_worker_heartbeat",
        "job_idempotency",
        "dead_letter_recovery",
        "metrics_without_payload",
    } <= set(stage["worker_checks"])
    assert len(stage["synthetic_replay_suites"]) == 2
    assert {"network_timeout", "provider_failure", "duplicate_message"} <= set(stage["fault_scenarios"])
    assert all(stage["read_only_fallback"][key] is expected for key, expected in {
        "required": True,
        "disable_writes_first": True,
        "core_records_remain_readable": True,
        "participant_feedback_auto_publish": False,
        "production_promotion_allowed": False,
    }.items())


def test_r01_local_rehearsal_never_counts_as_cloud_or_production():
    state = _module().inspect()
    assert state["ok"] is True
    assert state["missing_artifacts"] == []
    assert state["test_cloud_execution_complete"] is False
    assert state["production_mutation_executed"] is False
    assert state["production_release_approved"] is False


def test_r01_required_evidence_has_commit_image_contract_and_operator():
    payload = json.loads(REGISTRY.read_text(encoding="utf-8"))
    stage = next(item for item in payload["stages"] if item["id"] == "R01")
    assert {
        "source_commit",
        "image_digest",
        "schema_version",
        "content_contract_hash",
        "probe_results",
        "worker_results",
        "monitoring_snapshot",
        "synthetic_replay_results",
        "fault_drill_results",
        "read_only_fallback_result",
        "operator_reference",
    } <= set(stage["required_evidence_fields"])
    assert stage["local_automation_is_test_cloud_evidence"] is False
    assert stage["test_cloud_execution_complete"] is False
