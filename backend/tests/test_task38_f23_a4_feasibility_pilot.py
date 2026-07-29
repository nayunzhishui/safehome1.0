import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
REGISTRY = ROOT / "content" / "therapeutic_assessment_pilot_evidence_registry.json"


def test_a4_metrics_answer_safe_implementation_only():
    payload = json.loads(REGISTRY.read_text(encoding="utf-8"))
    stage = next(item for item in payload["stages"] if item["id"] == "A4")
    assert {item["id"] for item in stage["metrics"]} == {
        "completion_rate",
        "time_to_first_review",
        "revision_rate",
        "queue_load",
        "refusal_or_withdrawal",
        "negative_events",
        "severe_issues",
        "stop_count",
    }
    for metric in stage["metrics"]:
        assert metric["denominator"]
        assert metric["timepoint"]
        assert metric["missing_data"]
    assert stage["purpose"] == "safe_implementation_feasibility_only"
    assert stage["efficacy_claim_allowed"] is False
    assert stage["treatment_effect_estimation_allowed"] is False
    assert stage["symptom_change_claim_allowed"] is False


def test_a4_entry_stop_and_human_release_gates_remain_closed():
    payload = json.loads(REGISTRY.read_text(encoding="utf-8"))
    stage = next(item for item in payload["stages"] if item["id"] == "A4")
    assert stage["entry_dependencies"] == ["A3_formative_pilot_complete", "A3_severe_issues_closed"]
    assert {
        "serious_harm_or_safety_signal",
        "unresolved_severe_issue",
        "privacy_or_security_incident",
        "role_or_object_scope_violation",
        "queue_without_qualified_duty",
    } == set(stage["stop_reasons"])
    assert stage["severe_issue_blocks_release"] is True
    assert stage["synthetic_or_automation_may_sign"] is False
    assert stage["feasibility_pilot_complete"] is False
    assert stage["production_release_approved"] is False
