import importlib
import json
import shutil
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = PROJECT_ROOT / "backend"
CONTENT_ROOT = PROJECT_ROOT / "content"


def _builder():
    sys.path.insert(0, str(BACKEND_ROOT))
    return importlib.import_module("scripts.build_worksheets")


def _copy_content(target: Path) -> None:
    target.mkdir()
    for filename in [
        "assessment_worksheets.json",
        "scale_item_drafts.json",
        "scales_catalog.json",
    ]:
        shutil.copy(CONTENT_ROOT / filename, target / filename)


def test_build_worksheets_preserves_student_profile_and_is_idempotent(tmp_path):
    builder = _builder()
    content_dir = tmp_path / "content"
    _copy_content(content_dir)

    first = builder.build_worksheets(content_dir)["payload"]
    builder.write_json(content_dir / "assessment_worksheets.json", first)
    second = builder.build_worksheets(content_dir)["payload"]

    first_ids = [item["id"] for item in first["worksheets"]]
    second_ids = [item["id"] for item in second["worksheets"]]
    assert first_ids == second_ids

    student_profile = next(item for item in second["worksheets"] if item["id"] == "student_profile_v1")
    assert len(student_profile["questions"]) == 6
    assert student_profile["audience_class"] == "student"

    scs = next(item for item in second["worksheets"] if item["id"] == "self_compassion_scs_cn")
    assert len(scs["questions"]) == 26
    assert scs["enabled_for_user"] is True
    assert "不构成诊断" in scs["result_disclaimer"]


def test_build_worksheets_includes_all_scale_item_drafts(tmp_path):
    builder = _builder()
    content_dir = tmp_path / "content"
    _copy_content(content_dir)

    payload = builder.build_worksheets(content_dir)["payload"]
    draft_payload = json.loads((content_dir / "scale_item_drafts.json").read_text(encoding="utf-8"))
    worksheet_ids = {item["id"] for item in payload["worksheets"]}
    alias_map = builder.SCALE_WORKSHEET_ALIASES

    expected_ids = {
        alias_map.get(draft["scale_id"], draft["scale_id"])
        for draft in draft_payload["drafts"]
        if draft.get("items")
    }
    missing_ids = sorted(expected_ids - worksheet_ids)

    assert not missing_ids
    assert "emotion_regulation_erq" in worksheet_ids
    assert "emotion_regulation_erq_gross" not in worksheet_ids


def test_build_worksheets_prfq_options_reverse_and_mean_scoring(tmp_path):
    builder = _builder()
    content_dir = tmp_path / "content"
    _copy_content(content_dir)

    catalog_path = content_dir / "scales_catalog.json"
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    prfq = next(item for item in catalog["scales"] if item["id"] == "parent_reflective_functioning_prfq")
    prfq["enabled"] = True
    prfq["review_status"] = "pilot_review_required"
    prfq["boundary_notice"] = "本结果只用于自我观察，不构成诊断或筛查结论。"
    prfq["result_disclaimer"] = "本结果只用于自我观察，不构成诊断或筛查结论。"
    catalog_path.write_text(json.dumps(catalog, ensure_ascii=False), encoding="utf-8")

    payload = builder.build_worksheets(content_dir)["payload"]
    worksheet = next(item for item in payload["worksheets"] if item["id"] == "parent_reflective_functioning_prfq")
    questions = {item["id"]: item for item in worksheet["questions"]}

    assert len(questions["PRFQ01"]["options"]) == 7
    assert questions["PRFQ11"]["reverse_scored"] is True
    assert questions["PRFQ18"]["reverse_scored"] is True
    assert worksheet["dimension_score_method"] == "mean"
