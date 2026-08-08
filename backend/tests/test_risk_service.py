import importlib
import os
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = PROJECT_ROOT / "backend"


def _risk_service():
    sys.path.insert(0, str(BACKEND_ROOT))
    for name in list(sys.modules):
        if name in {"config"} or name.startswith("services."):
            sys.modules.pop(name, None)
    os.environ["CONTENT_DIR"] = str(PROJECT_ROOT / "content")
    return importlib.import_module("services.risk_service")


def test_risk_service_high_blocks_auto_feedback_and_cards():
    risk_service = _risk_service()

    result = risk_service.check_text_risk("我不想活了，感觉活不下去。", source="test")

    assert result["source"] == "test"
    assert result["risk_level"] == "high"
    assert result["safety_route"] == "human_review"
    assert result["requires_review"] is True
    assert result["allow_auto_feedback"] is False
    assert result["allow_recommended_training_cards"] is False
    assert result["matched_categories"][0]["id"] == "self_harm"
    assert result["safe_response"]
    assert "不构成诊断" in result["boundary_notice"]


def test_risk_service_immediate_high_routes_urgently():
    risk_service = _risk_service()

    result = risk_service.check_text_risk("我现在不想活，已经计划今晚伤害自己。")

    assert result["risk_level"] == "high"
    assert result["safety_route"] == "urgent_human_review"
    assert result["allow_auto_feedback"] is False
    assert result["allow_recommended_training_cards"] is False


def test_risk_service_medium_allows_auto_feedback_but_requires_review():
    risk_service = _risk_service()

    result = risk_service.check_text_risk("最近连续失眠，觉得有点撑不住。")

    assert result["risk_level"] == "medium"
    assert result["safety_route"] == "human_review"
    assert result["requires_review"] is True
    assert result["allow_auto_feedback"] is True
    assert result["allow_recommended_training_cards"] is True
    assert result["export_raw_text_by_default"] is False


def test_risk_service_low_uses_default_boundary_response():
    risk_service = _risk_service()

    result = risk_service.check_text_risk("今天只是有点烦，想先记录一下。")

    assert result["risk_level"] == "low"
    assert result["safety_route"] == "standard"
    assert result["requires_review"] is False
    assert result["allow_auto_feedback"] is True
    assert result["allow_recommended_training_cards"] is True
    assert result["matched_categories"] == []
    assert result["safe_response"].startswith("当前文本未命中")


def test_risk_service_uses_highest_level_across_multiple_text_fields():
    risk_service = _risk_service()

    result = risk_service.check_text_risk(["最近连续失眠", "也出现过不想活的念头"])

    assert result["risk_level"] == "high"
    matched_ids = {item["id"] for item in result["matched_categories"]}
    assert {"extreme_distress", "self_harm"}.issubset(matched_ids)


def test_risk_service_context_downgrades_priority_but_never_discards_signal():
    risk_service = _risk_service()

    quoted = risk_service.check_text_risk("朋友说他不想活，我很担心他。")
    negated = risk_service.check_text_risk("我没有不想活，只是这次压力很大。")
    historical = risk_service.check_text_risk("以前曾经有过自残的念头，现在在回顾那段经历。")

    for result in (quoted, negated, historical):
        assert result["risk_level"] == "medium"
        assert result["safety_route"] == "human_review"
        assert result["requires_review"] is True
        assert result["matched_categories"]
        assert result["matched_categories"][0]["all_contextual"] is True


def test_risk_service_does_not_echo_free_text_context():
    risk_service = _risk_service()
    result = risk_service.check_text_risk("我现在不想活。")
    serialized = repr(result["matched_categories"])
    assert "我现在不想活" not in serialized
