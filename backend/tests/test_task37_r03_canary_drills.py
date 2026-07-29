import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
REGISTRY = ROOT / "content" / "task37_release_execution_registry.json"
SCRIPT = ROOT / "backend" / "scripts" / "task37_r03_canary_drills.py"


def _module():
    spec = importlib.util.spec_from_file_location("task37_r03_canary_drills", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_r03_registry_covers_canary_shadow_load_and_eight_incidents():
    payload = json.loads(REGISTRY.read_text(encoding="utf-8"))
    stage = next(item for item in payload["stages"] if item["id"] == "R03")
    assert stage["canary_steps_percent"] == [1, 5, 10]
    assert stage["shadow_comparison"]["required"] is True
    assert stage["shadow_comparison"]["participant_visible"] is False
    assert stage["shadow_comparison"]["raw_text_in_evidence"] is False
    assert {item["id"] for item in stage["drill_scenarios"]} == {
        "service_overload",
        "provider_failure",
        "model_drift",
        "duty_interruption",
        "participant_withdrawal",
        "privacy_incident",
        "object_scope_violation",
        "unsafe_output",
    }


def test_r03_synthetic_rehearsal_passes_without_claiming_real_canary():
    result = _module().rehearse()
    assert result["ok"] is True
    assert result["load_passed"] is True
    assert len(result["drills"]) == 8
    assert all(item["passed"] for item in result["drills"])
    assert all(item["contains_real_participant_data"] is False for item in result["drills"])
    assert result["shadow"]["participant_visible"] is False
    assert len(result["shadow"]["sha256"]) == 64
    assert result["real_canary_execution_complete"] is False
    assert result["real_incident_drills_complete"] is False
    assert result["production_traffic_used"] is False
    assert result["production_release_approved"] is False


def test_r03_simulation_cannot_sign_or_own_incident():
    payload = json.loads(REGISTRY.read_text(encoding="utf-8"))
    stage = next(item for item in payload["stages"] if item["id"] == "R03")
    assert stage["synthetic_drill_may_sign"] is False
    assert stage["simulated_agent_may_be_incident_owner"] is False
    assert {"human_owner_decision", "kill_switch_verified"} <= set(stage["canary_promotion_requires"])
    assert {
        "incident_owner_reference",
        "independent_verifier_reference",
        "kill_switch_result",
        "recovery_result",
    } <= set(stage["required_evidence_fields"])
