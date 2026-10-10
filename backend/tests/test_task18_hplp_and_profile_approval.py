import json
from pathlib import Path

from services.assessment_execution_service import execute_assessment
from services.assessment_profile_service import model_artifact_hash_is_valid


ROOT = Path(__file__).resolve().parents[2]


def load_content(name: str):
    return json.loads((ROOT / "content" / name).read_text(encoding="utf-8"))


def test_hplp_uses_canonical_40_item_six_dimension_mean_scoring():
    worksheet = next(
        item
        for item in load_content("assessment_worksheets.json")["worksheets"]
        if item["id"] == "hplp_c_health_promoting_lifestyle"
    )
    assert worksheet["review_status"] == "production_approved"
    assert worksheet["enabled_for_user"] is True
    assert len(worksheet["questions"]) == 40
    assert [item["code"] for item in worksheet["dimensions"]] == [
        "NUTRITION",
        "HEALTH_RESPONSIBILITY",
        "PHYSICAL_ACTIVITY",
        "SPIRITUAL_GROWTH",
        "INTERPERSONAL_RELATIONS",
        "STRESS_MANAGEMENT",
    ]
    assert sum(len(item["item_ids"]) for item in worksheet["dimensions"]) == 40

    answers = [
        {"question_id": question["id"], "value": "4"}
        for question in worksheet["questions"]
    ]
    result = execute_assessment(worksheet, answers)
    assert result.total_score is None
    dimensions = {item["key"]: item["score"] for item in result.scores["dimensions"]}
    assert dimensions == {
        "NUTRITION": 4,
        "HEALTH_RESPONSIBILITY": 4,
        "PHYSICAL_ACTIVITY": 4,
        "SPIRITUAL_GROWTH": 4,
        "INTERPERSONAL_RELATIONS": 4,
        "STRESS_MANAGEMENT": 4,
        "HPLP_TOTAL": 4,
    }


def test_all_implemented_worksheets_have_project_owner_production_approval():
    worksheets = load_content("assessment_worksheets.json")["worksheets"]
    catalog = {item["id"]: item for item in load_content("scales_catalog.json")["scales"]}
    for worksheet in worksheets:
        assert worksheet["review_status"] == "production_approved"
        assert worksheet["enabled_for_user"] is True
        assert worksheet["approval"]["evidence_path"].endswith("量表正式开放负责人批准记录_20261008.md")
        assert (ROOT / worksheet["approval"]["evidence_path"]).is_file()
        # The earlier pilot approval stays on record as provenance of the formal release.
        assert worksheet["_meta"]["release_20261008"]["previous_review_status"] == "pilot_approved"
        if worksheet["id"] in catalog:
            assert catalog[worksheet["id"]]["review_status"] == "production_approved"
            assert catalog[worksheet["id"]]["enabled"] is True


def test_profile_models_are_linked_and_hplp_duplicate_is_not_runtime_candidate():
    models = {
        path.name: json.loads(path.read_text(encoding="utf-8"))
        for path in (ROOT / "content" / "profiles").glob("*.json")
    }
    for name, model in models.items():
        assert model_artifact_hash_is_valid(model), name
        if name == "profile_007_9b08783201.json":
            assert model["admission_status"] == "deprecated"
            assert model["worksheet_id"] is None
            assert model["replacement_model_id"] == models["profile_005_e6d75f52a4.json"]["model_id"]
        else:
            assert model["admission_status"] == "pilot_approved"
            assert model["interpretation_approval_status"] == "pilot_approved"
            assert model["worksheet_id"] == model["scale_id"]
            assert model["worksheet_link_status"] == "confirmed"

    hplp = models["profile_005_e6d75f52a4.json"]
    assert len({feature["worksheet_question_id"] for feature in hplp["features"]}) == hplp["n_features"]
    assert all(feature["worksheet_question_id"].startswith("HPLP") for feature in hplp["features"])


def test_hplp_follows_chinese_revision_factor_key_and_forty_item_composite():
    """曹文君等(2016)表1与本地hplp.sps：营养6题、健康责任11题；综合观察为40题均分。"""
    worksheet = next(
        item
        for item in load_content("assessment_worksheets.json")["worksheets"]
        if item["id"] == "hplp_c_health_promoting_lifestyle"
    )
    dims = {item["code"]: item["item_ids"] for item in worksheet["dimensions"]}
    assert dims["NUTRITION"] == ["HPLP12", "HPLP18", "HPLP23", "HPLP30", "HPLP35", "HPLP39"]
    assert dims["HEALTH_RESPONSIBILITY"] == [
        "HPLP01", "HPLP02", "HPLP06", "HPLP07", "HPLP13", "HPLP19",
        "HPLP24", "HPLP28", "HPLP31", "HPLP36", "HPLP40",
    ]
    prompts = {item["id"]: item["prompt"] for item in worksheet["questions"]}
    assert prompts["HPLP19"].startswith("当不信任卫生专业人士的建议时去寻求第二人的建议")
    assert prompts["HPLP26"].startswith("用特殊方式缓解压力")
    assert prompts["HPLP38"].startswith("自我安静、避免疲劳")

    nutrition = set(dims["NUTRITION"])
    answers = [
        {"question_id": question["id"], "value": "4" if question["id"] in nutrition else "1"}
        for question in worksheet["questions"]
    ]
    result = execute_assessment(worksheet, answers)
    scores = {item["key"]: item for item in result.scores["dimensions"]}
    assert scores["NUTRITION"]["score"] == 4  # the former 8-item key gave 3.25
    assert scores["HEALTH_RESPONSIBILITY"]["score"] == 1
    assert scores["HPLP_TOTAL"]["score"] == 1.45  # (6 * 4 + 34 * 1) / 40
    assert scores["HPLP_TOTAL"]["item_count"] == 40
