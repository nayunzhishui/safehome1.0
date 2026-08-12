from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "audit_participant_information_density.py"


def load_module():
    spec = importlib.util.spec_from_file_location("participant_density_audit", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


def test_literal_text_nodes_ignore_comments_and_runtime_values():
    audit = load_module()
    nodes = audit.literal_text_nodes('<!-- hidden --><text>保留 {{value}} 文案</text><section-title title="阶段反馈" /><view>{{only}}</view>')
    assert nodes == ["保留 文案", "阶段反馈"]


def test_function_baseline_protects_required_home_features():
    audit = load_module()
    baseline = audit.function_baseline("pages/home/index", audit.HOME_FEATURES, audit.HOME_BUTTONS)
    required = {"情绪天气", "测一测", "情绪日记", "今天的一小步", "三步开始", "支持性反馈", "训练中心", "人工支持", "最近记录", "阶段性反馈"}
    assert required.issubset(set(baseline["features"]))
    assert {"listDiaries", "getTodayJourney", "getProgressSummary"}.issubset(set(baseline["api_calls"]))
    assert "/pages/weekly-report/index" in baseline["navigation_targets"]
    assert {"openTodayAction", "retryTodayJourney", "openGettingStarted"}.issubset({item["handler"] for item in baseline["links"]})


def test_function_baseline_protects_assessment_result_actions_and_apis():
    audit = load_module()
    baseline = audit.function_baseline("pages/assessment-result/index", audit.RESULT_FEATURES, audit.RESULT_BUTTONS)
    assert {"getAssessmentResult", "getAssessment", "listCards", "getAssessmentProfilePosition"}.issubset(set(baseline["api_calls"]))
    assert any(item["handler"] == "openRecommendedCards" for item in baseline["buttons"])
    assert any(item["handler"] == "backToAssessment" for item in baseline["buttons"])


def test_scores_are_deterministic_and_bounded():
    audit = load_module()
    rows = [audit.page_metrics("pages/home/index"), audit.page_metrics("pages/assessment-result/index")]
    audit.add_scores(rows)
    assert all(0 <= row["density_score"] <= 100 for row in rows)
    assert audit.page_metrics("pages/home/index") == audit.page_metrics("pages/home/index")
