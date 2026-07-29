import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REGISTRY = ROOT / "content" / "therapeutic_assessment_pilot_evidence_registry.json"


def test_a1_covers_three_questions_seven_domains_and_screen_level_records():
    payload = json.loads(REGISTRY.read_text(encoding="utf-8"))
    stage = next(item for item in payload["stages"] if item["id"] == "A1")
    assert len(stage["screen_prompts"]) == 3
    assert {"谁会看到", "拒绝"} <= {
        "谁会看到" if "谁会看到" in item else "拒绝"
        for item in stage["screen_prompts"][1:]
    }
    assert {
        "诊断感", "被迫感", "隐私理解", "按钮层级", "等待状态", "撤回理解", "风险提示"
    } == set(stage["coverage_domains"])
    assert len(stage["screen_inventory"]) >= 5
    assert "unresolved_disagreement" in stage["required_interview_fields"]
    assert stage["usability_is_efficacy_research"] is False
    assert stage["human_interviews_complete"] is False
