import importlib
import sys
from datetime import date
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
    return importlib.import_module("app").app


def _wechat_login(client, code: str):
    response = client.post("/api/auth/wechat-login", json={"code": code, "nickname": code})
    assert response.status_code == 200
    payload = response.get_json()["data"]
    return payload["user"]["id"], payload["token"]


def _headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _create_assessment(client, token: str):
    response = client.post(
        "/api/assessment-results",
        headers=_headers(token),
        json={
            "worksheet_id": "student_profile_v1",
            "answers": [
                {"question_id": question_id, "value": "5"}
                for question_id in ["test_anxiety", "iu_score", "fear_score", "self_compassion"]
            ],
        },
    )
    assert response.status_code == 201


def _save_assignment(client, token: str, status: str = "active"):
    response = client.post(
        "/api/training-plan/assignment",
        headers=_headers(token),
        json={
            "phase": "practice",
            "cadence": "daily",
            "status": status,
            "start_date": date.today().isoformat(),
            "goal_text": "",
        },
    )
    assert response.status_code == 200


def test_journey_starts_with_assessment_for_new_participant(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    user_id, token = _wechat_login(client, "journey-new")

    response = client.get("/api/journey/today", headers=_headers(token))

    assert response.status_code == 200
    data = response.get_json()["data"]
    assert data["user_id"] == user_id
    assert data["state"] == "ready"
    assert data["primary_action"]["type"] == "start_assessment"
    assert data["primary_action"]["url"] == "/pages/assessment/index"
    assert "不构成" in data["boundary_notice"]


def test_journey_prioritizes_latest_unread_message_without_body(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    user_id, token = _wechat_login(client, "journey-message")
    with app.app_context():
        from database import get_connection
        from services.message_service import create_message

        with get_connection() as conn:
            message = create_message(
                conn,
                user_id,
                "阶段性反馈已更新",
                "这段正文不应出现在首页契约。",
                "relationship_stage_feedback",
                "relationship_report",
                "report-1",
                sender_id="researcher-1",
                sender_role="researcher",
            )
            conn.commit()

    response = client.get("/api/journey/today", headers=_headers(token))

    assert response.status_code == 200
    data = response.get_json()["data"]
    assert data["primary_action"]["type"] == "read_feedback"
    assert data["primary_action"]["source_id"] == message["id"]
    assert message["id"] in data["primary_action"]["url"]
    assert "body" not in data["primary_action"]
    assert "这段正文" not in response.get_data(as_text=True)


def test_journey_reports_paused_training_without_recommending_a_card(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    _user_id, token = _wechat_login(client, "journey-paused")
    _create_assessment(client, token)
    _save_assignment(client, token, status="paused")

    data = client.get("/api/journey/today", headers=_headers(token)).get_json()["data"]

    assert data["state"] == "paused"
    assert data["primary_action"]["type"] == "training_paused"
    assert data["primary_action"]["url"] == "/pages/personalized-plan/index"
    assert "card_id" not in data["primary_action"]


def test_journey_uses_existing_schedule_for_due_training(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    _user_id, token = _wechat_login(client, "journey-due")
    _create_assessment(client, token)
    _save_assignment(client, token)

    data = client.get("/api/journey/today", headers=_headers(token)).get_json()["data"]

    assert data["primary_action"]["type"] == "practice_due"
    assert data["primary_action"]["url"] == "/pages/personalized-plan/index"
    assert data["primary_action"]["source_type"] == "training_plan_assignment"


def test_journey_marks_today_completed_after_checkin(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    _user_id, token = _wechat_login(client, "journey-completed")
    _create_assessment(client, token)
    _save_assignment(client, token)
    checkin = client.post(
        "/api/checkins",
        headers=_headers(token),
        json={"card_id": "three_second_pause", "status": "completed"},
    )
    assert checkin.status_code == 201

    data = client.get("/api/journey/today", headers=_headers(token)).get_json()["data"]

    assert data["state"] == "completed"
    assert data["primary_action"]["type"] == "today_completed"
    assert data["primary_action"]["url"] == "/pages/weekly-report/index"


def test_journey_rejects_cross_user_query(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    _user_id, token = _wechat_login(client, "journey-owner")
    other_id, _other_token = _wechat_login(client, "journey-other")
    assert _user_id != other_id

    response = client.get(f"/api/journey/today?user_id={other_id}", headers=_headers(token))

    assert response.status_code == 403
    assert response.get_json()["error"]["code"] == "forbidden"
