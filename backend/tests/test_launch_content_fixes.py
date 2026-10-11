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


def test_legacy_import_refuses_production_before_initialization(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setattr(importer, "init_db", lambda: pytest.fail("must not initialize production"))
    with pytest.raises(RuntimeError, match="生产"):
        importer.import_worksheets()


def test_import_plan_only_reads_definitions_and_rejects_unknown_selection():
    w = WORKSHEETS[0]
    stored = importer.worksheet_to_row(w, "synthetic-time")
    stored["instructions"] = "old instructions"
    class ReadOnlyConnection:
        def execute(self, sql, args):
            assert sql.lstrip().startswith("SELECT") and "assessment_worksheets" in sql
            self.row = stored if args[0] == stored["id"] else None
            return self
        def fetchone(self): return self.row
    plan = importer.plan_worksheet_sync(ReadOnlyConnection(), [w], [w["id"]])
    assert plan == [{"id": w["id"], "action": "updated", "changed_fields": ["instructions"]}]
    with pytest.raises(ValueError, match="unknown"):
        importer.plan_worksheet_sync(ReadOnlyConnection(), [w], ["missing"])


def test_launch_report_is_read_only_and_privacy_snapshot_is_synchronized(monkeypatch):
    spec = importlib.util.spec_from_file_location("launch_readiness_test", ROOT / "scripts/check_launch_readiness.py")
    checker = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(checker)
    import database
    monkeypatch.setattr(database, "get_connection", lambda *a, **k: pytest.fail("source report must not access a database"))
    result = checker.report()
    assert result["status"] == "pending_required_evidence"
    assert result["privacy_pending_fields"]
    assert result["privacy_copy_synchronized"]
    assert result["summary"]["worksheets"]["total"] == len(WORKSHEETS)
    assert "TEMPORARY_*" in result["note"]


def test_privacy_parser_preserves_headings_and_does_not_grant_approval():
    spec = importlib.util.spec_from_file_location("launch_privacy_test", ROOT / "scripts/check_launch_readiness.py")
    checker = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(checker)
    parsed = checker.privacy_notice("# 标题\n版本：test-v1\n## 用途\n- 说明\n")
    assert parsed["version"] == "test-v1" and parsed["status"] == "text_complete"
    assert parsed["sections"][-1] == {"title": "用途", "items": ["说明"]}
    assert "approved" not in parsed.values()
