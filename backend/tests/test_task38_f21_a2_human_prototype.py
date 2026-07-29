import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REGISTRY = ROOT / "content" / "therapeutic_assessment_pilot_evidence_registry.json"


def test_a2_sequence_scope_supervision_and_human_only_feedback():
    payload = json.loads(REGISTRY.read_text(encoding="utf-8"))
    stage = next(item for item in payload["stages"] if item["id"] == "A2")
    assert stage["sequence"] == [
        "synthetic_cases",
        "expert_role_rehearsal",
        "small_real_low_risk_adult_sample",
        "case_by_case_supervision",
        "error_harm_revision_review",
    ]
    assert all(stage["allowed_scope"].values())
    assert stage["case_supervision_required"] is True
    assert stage["system_may_generate_h"] is False
    assert stage["system_may_publish_feedback"] is False
    assert stage["real_cases_completed"] is False
    assert stage["human_supervision_complete"] is False
    assert {"version_history", "error_or_negative_event", "revision_decision"} <= set(stage["case_evidence_fields"])
