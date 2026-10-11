import importlib
import json
import os
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = PROJECT_ROOT / "backend"
WORKSHEETS = json.loads((PROJECT_ROOT / "content" / "assessment_worksheets.json").read_text(encoding="utf-8"))["worksheets"]
GUIDES = json.loads((PROJECT_ROOT / "content" / "assessment_dimension_guides.json").read_text(encoding="utf-8"))


def _fresh_app(tmp_path):
    sys.path.insert(0, str(BACKEND_ROOT))
    for name in list(sys.modules):
        if name in {"app", "config", "database", "models"} or name.startswith("routes.") or name.startswith("services."):
            sys.modules.pop(name, None)
    os.environ["DATABASE_PATH"] = str(tmp_path / "safehome-test.sqlite3")
    os.environ["CONTENT_DIR"] = str(PROJECT_ROOT / "content")
    return importlib.import_module("app").app


def _worksheet(worksheet_id):
    return next(item for item in WORKSHEETS if item["id"] == worksheet_id)


def _codes(worksheet):
    derived = worksheet.get("derived_dimensions") or (worksheet.get("_meta") or {}).get("derived_dimensions") or []
    return [item["code"] for item in worksheet.get("dimensions", [])] + [item["code"] for item in derived]


def test_every_scored_dimension_has_a_definition_and_two_end_hints():
    for worksheet in WORKSHEETS:
        entries = GUIDES["worksheets"][worksheet["id"]]
        assert set(entries) == set(_codes(worksheet)), worksheet["id"]
        for code, entry in entries.items():
            assert entry["definition"] and entry["hints"]["low"] and entry["hints"]["high"], (worksheet["id"], code)
            assert set(entry.get("cutoffs", {})) <= {"low_below", "high_at_least"}, (worksheet["id"], code)
    assert GUIDES["approval"]["status"] == "owner_authorized_without_item_review"


def test_threshold_bounds_match_the_stored_score_range(tmp_path):
    _fresh_app(tmp_path)
    from services.assessment_execution_service import _score_range, dimension_score_bounds, score_answers

    for worksheet in WORKSHEETS:
        answers = [
            {"question_id": question["id"], "score": question["options"][0]["score"]}
            for question in worksheet.get("questions", [])
            if question.get("options")
        ]
        scores, _total = score_answers(worksheet, answers)
        bounds = dimension_score_bounds(worksheet)
        for dimension in scores.get("dimensions", []):
            assert _score_range(bounds.get(dimension["key"])) == dimension.get("score_range"), (worksheet["id"], dimension["key"])


@pytest.mark.parametrize(
    ("worksheet_id", "code", "score", "band", "basis"),
    [
        ("gad7_anxiety", "TOTAL", 4, "low", "cutoffs"),
        ("gad7_anxiety", "TOTAL", 5, "middle", "cutoffs"),
        ("gad7_anxiety", "TOTAL", 9, "middle", "cutoffs"),
        ("gad7_anxiety", "TOTAL", 10, "high", "cutoffs"),
        ("who5_wellbeing", "WELLBEING", 12, "low", "cutoffs"),
        ("who5_wellbeing", "WELLBEING", 13, "high", "cutoffs"),
        ("self_compassion_scs_cn", "SCS_SK", 2.59, "low", "scale_midpoint"),
        ("self_compassion_scs_cn", "SCS_SK", 2.6, "middle", "scale_midpoint"),
        ("self_compassion_scs_cn", "SCS_SK", 3.4, "middle", "scale_midpoint"),
        ("self_compassion_scs_cn", "SCS_SK", 3.41, "high", "scale_midpoint"),
        ("relationship_initiation_intention_action", "BI", 2.9, "low", "norm"),
        ("relationship_initiation_intention_action", "BI", 3.3, "middle", "norm"),
        ("relationship_initiation_intention_action", "BI", 3.75, "high", "norm"),
        # Raw 1-9 answers compared with norms mapped back from the 1-5 model scale.
        ("regulatory_focus_relationship_18", "PROM", 6.0, "low", "norm"),
        ("regulatory_focus_relationship_18", "PROM", 6.6, "middle", "norm"),
        ("regulatory_focus_relationship_18", "PROM", 7.3, "high", "norm"),
    ],
)
def test_bands_follow_cutoffs_then_norms_then_the_middle_zone(tmp_path, worksheet_id, code, score, band, basis):
    _fresh_app(tmp_path)
    from services.assessment_dimension_guide_service import classify

    guide = GUIDES["worksheets"][worksheet_id][code]
    assert classify(_worksheet(worksheet_id), code, score, guide) == (band, basis)


def test_training_rules_use_the_same_thresholds(tmp_path):
    _fresh_app(tmp_path)
    from services import training_recommendation_service as service

    scs = _worksheet("self_compassion_scs_cn")
    assert service._threshold_from_worksheet("SCS_SK", scs, scs["id"]) == {"support_below": 2.6, "high_above": 3.4}
    initiation = _worksheet("relationship_initiation_intention_action")
    assert service._threshold_from_worksheet("BI", initiation, initiation["id"]) == {"support_below": 2.9796, "high_above": 3.6996}
    # A score just under the scale midpoint is now "middle", so the low-band card rule stays quiet.
    condition = {"worksheet_id": scs["id"], "dimension": "SCS_SK", "level": "needs_support"}
    assert service._evaluate_condition(condition, {"SCS_SK": 2.8}, None, scs, scs["id"]) is False
    assert service._evaluate_condition(condition, {"SCS_SK": 2.4}, None, scs, scs["id"]) is True


def test_result_api_returns_definition_band_and_hint(tmp_path):
    app = _fresh_app(tmp_path)
    client = app.test_client()
    login = client.post("/api/auth/wechat-login", json={"code": "guide-synthetic", "nickname": "guide-synthetic"})
    token = login.get_json()["data"]["token"]
    worksheet = _worksheet("self_compassion_scs_cn")
    created = client.post(
        "/api/assessment-results",
        headers={"Authorization": f"Bearer {token}"},
        json={"worksheet_id": worksheet["id"], "answers": [
            {"question_id": question["id"], "value": question["options"][0]["value"]} for question in worksheet["questions"]
        ]},
    )
    assert created.status_code == 201
    result_id = created.get_json()["data"]["id"]
    response = client.get(f"/api/assessment-results/{result_id}", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    guides = response.get_json()["data"]["dimension_guides"]
    items = {item["key"]: item for item in guides["items"]}
    assert set(items) == set(_codes(worksheet))
    assert guides["boundary"] and guides["version"] == GUIDES["version"]
    kind = items["SCS_SK"]
    assert kind["band"] == "low" and kind["band_label"] == "这次偏低"
    assert kind["hint"] == GUIDES["worksheets"][worksheet["id"]]["SCS_SK"]["hints"]["low"]
    assert kind["definition"].startswith("遇到困难时")
    assert items["SCS_TOTAL"]["composite"] is True
    for item in items.values():
        assert item["band"] in {"low", "middle", "high"}
        assert item["hint"]
        if item["band"] == "middle":
            assert item["band_label"] is None and item["hint"] == GUIDES["middle_hint"]
