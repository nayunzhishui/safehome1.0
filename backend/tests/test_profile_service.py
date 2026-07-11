import importlib
import os
import sys
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = PROJECT_ROOT / "backend"


def _profile_service():
    sys.path.insert(0, str(BACKEND_ROOT))
    for name in list(sys.modules):
        if name in {"config"} or name.startswith("services."):
            sys.modules.pop(name, None)
    os.environ["CONTENT_DIR"] = str(PROJECT_ROOT / "content")
    return importlib.import_module("services.student_profile_model_service")


def test_profile_service_generates_normal_supportive_profile():
    service = _profile_service()

    result = service.generate_student_profile(
        {
            "scores": {
                "test_anxiety": 4.2,
                "iu_score": 4.1,
                "f_score": 2.8,
                "self_compassion": 2.7,
            },
            "free_text": "考试前会担心，但愿意先做一次情绪命名练习。",
        }
    )

    assert result["risk_level"] == "low"
    assert result["allow_auto_feedback"] is True
    assert result["profile_name"]
    assert result["boundary_notice"]
    assert result["recommended_card_ids"]


def test_profile_service_missing_scores_raises_input_error():
    service = _profile_service()

    with pytest.raises(service.ProfileInputError):
        service.generate_student_profile({"free_text": "只写了文字，没有分数。"})


def test_profile_service_high_risk_blocks_profile_cards():
    service = _profile_service()

    result = service.generate_student_profile(
        {
            "scores": {
                "test_anxiety": 4.2,
                "iu_score": 4.1,
                "f_score": 2.8,
                "self_compassion": 2.7,
            },
            "free_text": "我最近不想活，需要现实中的可信成年人帮助。",
        }
    )

    assert result["risk_level"] == "high"
    assert result["requires_review"] is True
    assert result["allow_auto_feedback"] is False
    assert result["recommended_card_ids"] == []
    assert result["profile_code"] == "requires_review"


def test_profile_service_low_confidence_is_visible_for_manual_review_queue():
    service = _profile_service()

    result = service.generate_student_profile(
        {
            "scores": {
                "test_anxiety": 2.0,
                "iu_score": 4.5,
                "self_compassion": 4.0,
                "erf_evaluation": 2.5,
                "erf_expression": 2.5,
                "erf_strategy_flex": 2.5,
                "f_score": 3.0,
            },
            "free_text": "最近有些压力，但没有危险想法。",
        }
    )

    assert result["risk_level"] == "low"
    assert result["confidence"] < 0.5
    assert result["profile_code"]


def test_profile_visuals_do_not_export_row_level_training_points():
    service = _profile_service()
    visuals = service.build_student_visuals(
        {"features": {"iu_total": 3, "erf_evaluation": 3, "erf_expression": 3, "erf_strategy_flex": 3, "self_compassion": 3, "test_anxiety": 3}},
        {"pc1": 0, "pc2": 0, "cluster_id": 1, "profile_code": "middle_uncertain", "confidence": 0.5},
    )

    assert visuals["pca"]["points"] == []
    assert visuals["pca"]["aggregate_centroids"]
