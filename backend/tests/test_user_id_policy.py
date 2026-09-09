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
    if app_env == "production":
        monkeypatch.setenv("DB_PROVIDER", "sqlite")
        monkeypatch.setenv("ALLOW_PRODUCTION_SQLITE", "1")
        monkeypatch.setenv("SECRET_KEY", "production-test-secret-key-32-chars")
    else:
        monkeypatch.delenv("DB_PROVIDER", raising=False)
        monkeypatch.delenv("ALLOW_PRODUCTION_SQLITE", raising=False)
        monkeypatch.delenv("SECRET_KEY", raising=False)
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


def test_non_development_rejects_missing_user_id_for_core_write_endpoints(tmp_path, monkeypatch):
    # Production requires an approved MySQL profile and cannot be booted on the
    # isolated SQLite fixture; testing keeps the same no-anonymous-identity
    # contract without attempting a production connection.
    app = _fresh_app(tmp_path, monkeypatch, "testing")
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
        assert response.status_code in {400, 401}, path
        assert body["error"]["code"] in {"validation_error", "unauthorized"}, path
        assert "匿名 user_id" in body["error"]["message"] or "登录" in body["error"]["message"] or "需要先登录" in body["error"]["message"], path


def test_non_development_rejects_missing_user_id_for_query_endpoints(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch, "testing")
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
        assert response.status_code in {400, 401}, path
        assert body["error"]["code"] in {"validation_error", "unauthorized"}, path
        assert "匿名 user_id" in body["error"]["message"] or "登录" in body["error"]["message"] or "需要先登录" in body["error"]["message"], path


def test_non_development_rejects_body_and_query_user_id_without_signed_actor(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch, "testing")
    client = app.test_client()

    responses = [
        client.post(
            "/api/goals",
            json={"user_id": "spoofed-user", "scene": "作业拖延", "smart_goal": "先记录一次"},
        ),
        client.get("/api/goals?user_id=spoofed-user"),
        client.post(
            "/api/consent",
            json={"user_id": "spoofed-user", "consent_type": "privacy_policy", "agreed": True},
        ),
    ]

    for response in responses:
        assert response.status_code in {400, 401}
        assert response.get_json()["error"]["code"] in {"validation_error", "unauthorized"}
        assert "登录" in response.get_json()["error"]["message"]
