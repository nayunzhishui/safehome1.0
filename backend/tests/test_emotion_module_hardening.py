"""情感计算模块硬化回归：聚合出口值约束、独立隐私门和否定附加信号。"""

import importlib.util
import json
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))


def test_assert_safe_shape_rejects_long_string_and_deep_nesting():
    from services.research_analysis_service import ResearchAnalysisError, _assert_safe_shape

    _assert_safe_shape({"coverage_rate": 0.9, "result": {"nodes": [{"display_name": "情绪", "degree": 3}]}})

    with pytest.raises(ResearchAnalysisError):
        _assert_safe_shape({"result": {"note": "原" * 300}})

    deep = current = {}
    for _ in range(12):
        current["child"] = {}
        current = current["child"]
    with pytest.raises(ResearchAnalysisError):
        _assert_safe_shape({"result": deep})


def test_independent_privacy_gate_blocks_forbidden_keys_and_long_text():
    from services.text_analysis_service import _independent_privacy_gate

    assert _independent_privacy_gate({"coverage_rate": 0.9, "emotion_categories": [["anxiety", 3]]})
    assert not _independent_privacy_gate({"raw_text": "孩子今天……"})
    assert not _independent_privacy_gate({"records": [{"text": "x"}]})
    assert not _independent_privacy_gate({"summary": "字" * 2500})


def test_negation_produces_additive_signal_without_flipping_valence():
    spec = importlib.util.spec_from_file_location(
        "analyze_text_sources_hardening",
        ROOT / "analysis" / "text_analysis" / "analyze_text_sources.py",
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    record = {
        "source": "synthetic.text",
        "source_type": "user_text",
        "text": "我不生气",
        "sentiment_ok": True,
        "network_ok": True,
    }
    summary = module.analyze_records([record])["sentiment_summary"]
    assert summary["negated_match_count"] == 1
    assert summary["intensity_signal_score"] == 0
    assert summary["negated_polarity_signal"] > 0
    assert summary["effective_coverage_rate"] >= summary["coverage_rate"]


def test_expanded_lexicon_covers_more_everyday_words():
    payload = json.loads(
        (ROOT / "analysis" / "text_analysis" / "dictionaries" / "emotion_terms.json").read_text(encoding="utf-8")
    )
    words = {term["word"] for term in payload["terms"]}
    assert len(words) >= 60
    assert {"忐忑", "自责", "欣慰", "撑不住"} <= words
