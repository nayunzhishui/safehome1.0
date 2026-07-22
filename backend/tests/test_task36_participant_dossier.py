import importlib
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = PROJECT_ROOT / "backend"
ADMIN_HEADERS = {"X-Admin-Token": "safehome-local-admin-token"}


def _fresh_app(tmp_path, monkeypatch):
    sys.path.insert(0, str(BACKEND_ROOT))
    for name in list(sys.modules):
        if name in {"app", "config", "database", "models"} or name.startswith("routes.") or name.startswith("services."):
            sys.modules.pop(name, None)
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "safehome-test.sqlite3"))
    monkeypatch.setenv("CONTENT_DIR", str(PROJECT_ROOT / "content"))
    return importlib.import_module("app").app


def _login(client, code):
    data = client.post("/api/auth/wechat-login", json={"code": code, "nickname": "很长的参与者昵称用于检查布局"}).get_json()["data"]
    return data["user"]["id"], {"Authorization": f"Bearer {data['token']}"}


def test_lazy_dossier_paginates_filters_and_audits_sensitive_modules(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    user_id, headers = _login(client, "task36-f05-user")
    for index in range(3):
        assert client.post("/api/diaries", headers=headers, json={
            "scene": "沟通" if index < 2 else "学习",
            "event_description": f"第{index + 1}条较长但可按需读取的记录",
            "parent_emotion": "担心",
        }).status_code == 201

    summary = client.get(f"/api/research/participants/{user_id}", headers=ADMIN_HEADERS)
    assert summary.status_code == 200
    payload = summary.get_json()["data"]
    assert isinstance(payload["modules"], list)
    assert "event_description" not in str(payload)
    assert payload["participant"]["anonymous_id"].startswith("anon_")

    first = client.get(f"/api/research/participants/{user_id}/modules/diaries?page=1&page_size=2&type=%E6%B2%9F%E9%80%9A", headers=ADMIN_HEADERS)
    assert first.status_code == 200
    page = first.get_json()["data"]
    assert page["count"] == 2
    assert page["total"] == 2
    assert page["has_more"] is False
    assert page["timezone"] == "Asia/Shanghai"
    assert all(item["scene"] == "沟通" for item in page["items"])

    assert client.get(f"/api/research/participants/{user_id}/modules/unknown", headers=ADMIN_HEADERS).status_code == 400
    assert client.get(f"/api/research/participants/{user_id}/modules/diaries?page=0", headers=ADMIN_HEADERS).status_code == 400
    assert client.get("/api/research/participants/not-authorized/modules/diaries", headers=ADMIN_HEADERS).status_code == 404

    with app.app_context():
        database = importlib.import_module("database")
        with database.get_connection() as conn:
            audit = conn.execute("SELECT metadata_json FROM audit_logs WHERE action = 'research_participant_sensitive_module_viewed' ORDER BY created_at DESC LIMIT 1").fetchone()
            assert audit is not None
            assert "event_description" not in audit["metadata_json"]


def test_deleted_participant_and_revoked_consent_are_not_readable(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    user_id, _headers = _login(client, "task36-f05-withdrawn")
    database = importlib.import_module("database")
    with app.app_context():
        with database.get_connection() as conn:
            conn.execute("UPDATE users SET status = 'deleted' WHERE id = ?", (user_id,))
            conn.commit()
    assert client.get(f"/api/research/participants/{user_id}", headers=ADMIN_HEADERS).status_code == 404
    assert client.get(f"/api/research/participants/{user_id}/modules/timeline", headers=ADMIN_HEADERS).status_code == 404


def test_web_shared_and_miniprogram_use_the_same_lazy_module_contract():
    shared = (PROJECT_ROOT / "shared" / "types" / "api.ts").read_text(encoding="utf-8")
    web_api = (PROJECT_ROOT / "apps" / "web" / "src" / "services" / "safehomeApi.ts").read_text(encoding="utf-8")
    web_page = (PROJECT_ROOT / "apps" / "web" / "src" / "pages" / "ResearchDashboard.tsx").read_text(encoding="utf-8")
    mini_api = (PROJECT_ROOT / "apps" / "miniprogram" / "services" / "api.js").read_text(encoding="utf-8")
    mini_page = (PROJECT_ROOT / "apps" / "miniprogram" / "pages" / "researcher-dashboard" / "index.js").read_text(encoding="utf-8")
    mini_view = (PROJECT_ROOT / "apps" / "miniprogram" / "pages" / "researcher-dashboard" / "index.wxml").read_text(encoding="utf-8")

    for module_key in ("assessments", "measurements", "diaries", "training", "stage_reports", "relationship_pilot", "project_tests", "messages", "human_support", "timeline"):
        assert f'"{module_key}"' in shared
    assert "getResearchParticipantModule" in web_api and "getResearchParticipantModule" in mini_api
    assert "loadParticipantModule" in web_page and "loadParticipantModule" in mini_page
    assert "选择一个标签后才会读取详情" in web_page
    assert "选择标签后才读取详情" in mini_view
