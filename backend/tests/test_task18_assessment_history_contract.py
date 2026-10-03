import importlib
import json
import os
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = PROJECT_ROOT / "backend"
MINIPROGRAM_ROOT = PROJECT_ROOT / "apps" / "miniprogram"


def _fresh_app(tmp_path):
    sys.path.insert(0, str(BACKEND_ROOT))
    for name in list(sys.modules):
        if name in {"app", "config", "database", "models"} or name.startswith("routes.") or name.startswith("services."):
            sys.modules.pop(name, None)
    os.environ["DATABASE_PATH"] = str(tmp_path / "safehome-test.sqlite3")
    os.environ["CONTENT_DIR"] = str(PROJECT_ROOT / "content")
    return importlib.import_module("app").app


def _wechat_login(client, code):
    response = client.post("/api/auth/wechat-login", json={"code": code, "nickname": code})
    assert response.status_code == 200
    data = response.get_json()["data"]
    return data["user"]["id"], data["token"]


def test_assessment_history_supports_stable_pagination_and_total(tmp_path):
    app = _fresh_app(tmp_path)
    client = app.test_client()
    user_id, token = _wechat_login(client, "task18-history")

    from database import get_connection, json_dumps

    with get_connection() as conn:
        for index in range(5):
            conn.execute(
                """
                INSERT INTO assessment_results (
                    id, user_id, worksheet_id, worksheet_title, category,
                    answers_json, scores_json, total_score, result_summary, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    f"task18-history-{index}",
                    user_id,
                    "student_profile_v1",
                    "学生支持性画像",
                    "学生自主量表",
                    json_dumps([]),
                    json_dumps({"dimensions": [{"key": "stress", "label": "压力线索", "score": index}]}),
                    index,
                    f"记录 {index}",
                    f"2026-07-0{index + 1}T08:00:00+00:00",
                ),
            )
        conn.commit()

    first = client.get(
        "/api/assessment-results?page=1&page_size=2",
        headers={"Authorization": f"Bearer {token}"},
    ).get_json()["data"]
    last = client.get(
        "/api/assessment-results?page=3&page_size=2",
        headers={"Authorization": f"Bearer {token}"},
    ).get_json()["data"]

    assert first["total"] == 5
    assert first["page"] == 1
    assert first["page_size"] == 2
    assert first["has_more"] is True
    assert [item["id"] for item in first["items"]] == ["task18-history-4", "task18-history-3"]
    assert last["has_more"] is False
    assert [item["id"] for item in last["items"]] == ["task18-history-0"]


def test_weekly_dimensions_keep_same_keys_separate_between_scales(tmp_path):
    _fresh_app(tmp_path)
    from database import json_dumps
    from services.report_service import _build_assessment_summary

    assessments = [
        {
            "worksheet_id": "scale_a",
            "worksheet_title": "量表甲",
            "scores_json": json_dumps({"dimensions": [{"key": "TOTAL", "label": "甲总分", "score": 3}]}),
            "created_at": "2026-07-07T08:00:00+00:00",
        },
        {
            "worksheet_id": "scale_b",
            "worksheet_title": "量表乙",
            "scores_json": json_dumps({"dimensions": [{"key": "TOTAL", "label": "乙总分", "score": 4}]}),
            "created_at": "2026-07-07T09:00:00+00:00",
        },
    ]

    summary = _build_assessment_summary(assessments)

    assert len(summary["dimension_summaries"]) == 2
    assert {(item["worksheet_id"], item["label"]) for item in summary["dimension_summaries"]} == {
        ("scale_a", "甲总分"),
        ("scale_b", "乙总分"),
    }


def test_miniprogram_uses_dedicated_history_page_and_grouped_weekly_dimensions():
    app_config = json.loads((MINIPROGRAM_ROOT / "app.json").read_text(encoding="utf-8"))
    profile_js = (MINIPROGRAM_ROOT / "pages" / "profile" / "index.js").read_text(encoding="utf-8")
    history_js = (MINIPROGRAM_ROOT / "pages" / "assessment-history" / "index.js").read_text(encoding="utf-8")
    weekly_wxml = (MINIPROGRAM_ROOT / "pages" / "weekly-report" / "index.wxml").read_text(encoding="utf-8")

    assert "pages/assessment-history/index" in app_config["pages"]
    assert 'url: "/pages/assessment-history/index"' in profile_js
    assert "page_size: PAGE_SIZE" in history_js
    assert "has_more" in history_js
    assert "group.worksheetTitle" in weekly_wxml
    assert "group.dimensions" in weekly_wxml


def test_cross_version_or_missing_provenance_does_not_generate_score_trend(tmp_path):
    _fresh_app(tmp_path)
    from database import json_dumps
    from services.report_service import _build_assessment_summary
    from services.progress_summary_service import _assessment_summary, _status
    def row(version, total, dimension):
        return {"worksheet_id": "synthetic-uwes", "worksheet_title": "合成问卷", "worksheet_version": version, "scoring_version": f"{version}::worksheet_server_score_v1", "raw_scale_json": json_dumps({"ranges": [{"min": 0, "max": 6}]}), "total_score": total, "scores_json": json_dumps({"dimensions": [{"key": "VIGOR", "score": dimension}]})}
    newer, older = row("v2", 5, 5), row("v1", 85, 30)
    weekly = _build_assessment_summary([newer, older])["dimension_summaries"][0]
    assert weekly["score_delta"] is None
    assert weekly["direction"] == "暂不比较"
    progress = _assessment_summary([newer, older])
    repeated = progress["repeated_worksheets"][0]
    assert repeated["score_delta"] is None
    assert repeated["dimension_trends"] == []
    assert not repeated["comparable"]
    assert _status(progress, {"completed_count": 1}, {"count": 0}) == "low_confidence"
    same = _assessment_summary([row("v2", 5, 5), row("v2", 4, 4)])["repeated_worksheets"][0]
    assert same["score_delta"] == 1
    assert same["dimension_trends"][0]["score_delta"] == 1
    newer.pop("worksheet_version")
    assert not _assessment_summary([newer, row("v2", 4, 4)])["repeated_worksheets"][0]["comparable"]
