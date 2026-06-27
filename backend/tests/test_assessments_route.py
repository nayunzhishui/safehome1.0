import importlib
import os
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = PROJECT_ROOT / "backend"


def _fresh_app(tmp_path):
    sys.path.insert(0, str(BACKEND_ROOT))
    for name in list(sys.modules):
        if name in {"app", "config", "database", "models"} or name.startswith("routes.") or name.startswith("services."):
            sys.modules.pop(name, None)
    os.environ["DATABASE_PATH"] = str(tmp_path / "safehome-test.sqlite3")
    os.environ["CONTENT_DIR"] = str(PROJECT_ROOT / "content")
    module = importlib.import_module("app")
    return module.app


def test_disabled_assessment_detail_is_readable_but_submit_is_blocked(tmp_path):
    app = _fresh_app(tmp_path)
    client = app.test_client()

    detail_response = client.get("/api/assessments/worksheet_3_1_anxiety")
    assert detail_response.status_code == 200
    detail = detail_response.get_json()["data"]
    assert detail["enabled_for_user"] is False
    assert detail["review_status"] == "draft_only"
    assert detail["review_note"]

    submit_response = client.post(
        "/api/assessment-results",
        json={
            "user_id": "parent-disabled-check",
            "worksheet_id": "worksheet_3_1_anxiety",
            "answers": [{"question_id": "q1", "prompt": "测试题", "value": "1", "score": 1}],
        },
    )

    assert submit_response.status_code == 400
    body = submit_response.get_json()
    assert body["ok"] is False
    assert body["error"]["code"] == "assessment_not_enabled"

    from database import get_connection

    with get_connection() as conn:
        saved_count = conn.execute(
            "SELECT COUNT(*) FROM assessment_results WHERE worksheet_id = ?",
            ("worksheet_3_1_anxiety",),
        ).fetchone()[0]

    assert saved_count == 0


def test_enabled_student_profile_assessment_result_still_saves(tmp_path):
    app = _fresh_app(tmp_path)
    client = app.test_client()

    response = client.post(
        "/api/assessment-results",
        json={
            "user_id": "student-enabled-check",
            "worksheet_id": "student_profile_v1",
            "answers": [{"question_id": "test_anxiety", "prompt": "测试题", "value": "3", "score": 3}],
        },
    )

    assert response.status_code == 201
    data = response.get_json()["data"]
    assert data["worksheet_id"] == "student_profile_v1"
    assert data["total_score"] == 3


def test_assessment_detail_includes_training_recommendation_rules(tmp_path):
    app = _fresh_app(tmp_path)
    client = app.test_client()

    response = client.get("/api/assessments/student_profile_v1")

    assert response.status_code == 200
    data = response.get_json()["data"]
    rules = data["training_recommendation_rules"]
    assert len(rules) == 1
    assert rules[0]["rule_id"] == "student_profile_pressure_alert_basic_support"
    assert len(rules[0]["recommended_card_ids"]) <= 3
