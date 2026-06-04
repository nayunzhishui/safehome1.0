import importlib
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = PROJECT_ROOT / "backend"


def _fresh_app(tmp_path, monkeypatch, app_env: str = "development"):
    sys.path.insert(0, str(BACKEND_ROOT))
    for name in list(sys.modules):
        if name in {"app", "config", "database", "models"} or name.startswith("routes.") or name.startswith("services."):
            sys.modules.pop(name, None)
    monkeypatch.setenv("APP_ENV", app_env)
    monkeypatch.setenv("ADMIN_EXPORT_TOKEN", "production-test-token")
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "safehome-test.sqlite3"))
    monkeypatch.setenv("CONTENT_DIR", str(PROJECT_ROOT / "content"))
    module = importlib.import_module("app")
    return module.app


def test_development_allows_demo_parent_for_write_endpoint(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch, "development")
    client = app.test_client()

    response = client.post("/api/goals", json={"scene": "作业拖延", "smart_goal": "先记录一次具体事件"})

    assert response.status_code == 201
    assert response.get_json()["data"]["user_id"] == "demo-parent"


def test_development_allows_demo_parent_for_query_endpoint(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch, "development")
    client = app.test_client()

    response = client.get("/api/goals")

    assert response.status_code == 200
    assert response.get_json()["data"]["items"] == []


def test_production_rejects_missing_user_id_for_core_write_endpoints(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch, "production")
    client = app.test_client()
    cases = [
        ("/api/goals", {"scene": "作业拖延", "smart_goal": "先记录一次具体事件"}),
        ("/api/diaries", {"scene": "作业拖延", "event_description": "孩子没有开始写作业", "parent_emotion": "着急"}),
        ("/api/feedback/generate", {"event_description": "孩子写作业拖延，我很着急"}),
        (
            "/api/profile",
            {"scores": {"test_anxiety": 4, "iu_score": 4, "f_score": 3, "self_compassion": 3}, "free_text": "最近压力有点大"},
        ),
        ("/api/checkins", {"card_id": "three_second_pause"}),
        ("/api/supervision", {"message": "想请老师补充看看这条记录。"}),
        ("/api/consent", {"consent_type": "privacy_policy", "agreed": True}),
        ("/api/assessment-results", {"worksheet_id": "student_profile_v1", "answers": []}),
        ("/api/parent-assessments", {"answers": {}}),
    ]

    for path, payload in cases:
        response = client.post(path, json=payload)
        body = response.get_json()
        assert response.status_code == 400, path
        assert body["error"]["code"] == "validation_error", path
        assert "匿名 user_id" in body["error"]["message"], path


def test_production_rejects_missing_user_id_for_query_endpoints(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch, "production")
    client = app.test_client()
    paths = [
        "/api/goals",
        "/api/diaries",
        "/api/checkins",
        "/api/weekly-report",
        "/api/assessment-results",
    ]

    for path in paths:
        response = client.get(path)
        body = response.get_json()
        assert response.status_code == 400, path
        assert body["error"]["code"] == "validation_error", path
        assert "匿名 user_id" in body["error"]["message"], path
