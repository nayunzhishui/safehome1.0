import importlib.util
import json
import sys
from pathlib import Path
import pytest
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))
from services.assessment_execution_service import execute_assessment
from routes.assessments import _db_row_to_worksheet

spec = importlib.util.spec_from_file_location("launch_worksheet_import", ROOT / "backend/scripts/import_worksheets_to_db.py")
importer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(importer)
WORKSHEETS = json.loads((ROOT / "content/assessment_worksheets.json").read_text(encoding="utf-8"))["worksheets"]

def _answers(w, high=False):
    return [{"question_id": q["id"], "value": q["options"][-1 if high else 0]["value"] if q.get("options") else "合成记录"}
            for q in w["questions"]]

@pytest.mark.parametrize("high", [False, True])
def test_rfq_formula_dimensions_count_six_items(high):
    w = next(w for w in WORKSHEETS if w["id"] == "rfq8_reflective_functioning")
    result = execute_assessment(w, _answers(w, high))
    assert {d["key"]: d["item_count"] for d in result.scores["dimensions"]} == {"RFQC": 6, "RFQU": 6}

@pytest.mark.parametrize("worksheet_id", ["emotion_regulation_erq", "parent_reflective_functioning_prfq"])
def test_subscale_only_sources_do_not_invent_a_global_total(worksheet_id):
    w = next(w for w in WORKSHEETS if w["id"] == worksheet_id)
    result = execute_assessment(w, _answers(w))
    assert result.total_score is None
    assert result.scores["dimensions"]

@pytest.mark.parametrize("w", WORKSHEETS, ids=lambda w:w["id"])
def test_database_roundtrip_preserves_scoring_metadata(w):
    row = importer.worksheet_to_row(w, "synthetic-checkpoint")
    restored = _db_row_to_worksheet(row)
    source = execute_assessment(w, _answers(w))
    stored = execute_assessment(restored, _answers(w))
    assert source.total_score == stored.total_score
    assert source.scores == stored.scores

def test_privacy_is_readable_in_app_and_explicit_about_pending_fields():
    policy = (ROOT / "content/privacy.md").read_text(encoding="utf-8")
    snapshot = json.loads((ROOT / "apps/miniprogram/utils/privacy-policy.json").read_text(encoding="utf-8"))
    source = (ROOT / "apps/miniprogram/pages/settings-detail/index.js").read_text(encoding="utf-8")
    assert "privacy: privacyPolicy" in source
    assert "正式文本以 content/privacy.md" not in source
    assert snapshot["status"] == "draft"
    assert "人工支持" in policy and "手机号登录" in policy
    assert any("待填写：" in text for section in snapshot["sections"] for text in section["items"])
