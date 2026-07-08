import importlib
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = PROJECT_ROOT / "backend"


def _fresh_app(tmp_path, monkeypatch):
    sys.path.insert(0, str(BACKEND_ROOT))
    for name in list(sys.modules):
        if name in {"app", "config", "database", "models"} or name.startswith("routes.") or name.startswith("services."):
            sys.modules.pop(name, None)
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "safehome-test.sqlite3"))
    monkeypatch.setenv("CONTENT_DIR", str(PROJECT_ROOT / "content"))
    module = importlib.import_module("app")
    return module.app


def _wechat_login(client, code: str):
    response = client.post("/api/auth/wechat-login", json={"code": code, "nickname": code})
    assert response.status_code == 200
    data = response.get_json()["data"]
    return data["user"]["id"], data["token"]


def test_emotion_thermometer_day_returns_sorted_records_and_summary(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    user_id, token = _wechat_login(client, "t8-thermo")

    for level, created_at in [(7, "2026-07-01T09:10:00+00:00"), (3, "2026-07-01T08:10:00+00:00")]:
        response = client.post(
            "/api/emotion-thermometer",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "intensity_level": level,
                "brief_text": "一次温度记录",
                "created_at": created_at,
            },
        )
        assert response.status_code == 201

    response = client.get(
        f"/api/emotion-thermometer/day?user_id={user_id}&date=2026-07-01",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.get_json()["data"]
    assert [item["intensity_level"] for item in data["items"]] == [3, 7]
    assert data["summary"]["count"] == 2
    assert data["summary"]["min"] == 3
    assert data["summary"]["max"] == 7
    assert data["summary"]["avg"] == 5.0
    assert data["summary"]["valence_avg"] is None
    assert data["summary"]["arousal_avg"] is None
    assert data["summary"]["control_avg"] is None
    assert "诊断" in data["boundary_notice"]


def test_programs_endpoints_return_pilot_programs(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()

    list_response = client.get("/api/programs")
    assert list_response.status_code == 200
    items = list_response.get_json()["data"]["items"]
    ids = {item["id"] for item in items}
    assert "self_compassion_exam_anxiety" in ids
    assert "academic_pressure_sleep_health" in ids

    detail_response = client.get("/api/programs/self_compassion_exam_anxiety")
    assert detail_response.status_code == 200
    program = detail_response.get_json()["data"]["program"]
    assert program["review_status"] == "pilot_draft"
    assert len(program["sessions"]) >= 3
    assert "不构成诊断" in program["boundary_notice"]


def test_training_plan_prompts_when_no_assessment(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    _user_id, token = _wechat_login(client, "no-assessment-user")

    response = client.get("/api/training-plan", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    data = response.get_json()["data"]
    assert data["has_assessment"] is False
    assert data["plan_items"] == []
    assert data["next_action"]["url"] == "/pages/assessment/index"


def test_training_plan_uses_latest_assessment_recommendation(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    user_id, token = _wechat_login(client, "training-plan-user")

    create_response = client.post(
        "/api/assessment-results",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "worksheet_id": "student_profile_v1",
            "answers": [
                {"question_id": "test_anxiety", "prompt": "考试紧张", "value": "5", "score": 5},
                {"question_id": "iu_total", "prompt": "不确定", "value": "5", "score": 5},
            ],
        },
    )
    assert create_response.status_code == 201

    response = client.get(
        f"/api/training-plan?user_id={user_id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.get_json()["data"]
    assert data["has_assessment"] is True
    assert data["plan_items"]
    assert data["plan_items"][0]["cards"]
    assert "不构成" in data["boundary_notice"]
