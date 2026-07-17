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


def _wechat_login(client, code):
    response = client.post("/api/auth/wechat-login", json={"code": code, "nickname": code})
    assert response.status_code == 200
    data = response.get_json()["data"]
    return data["user"]["id"], data["token"]


def test_research_workspace_lists_and_reads_multi_module_participant(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    user_id, token = _wechat_login(client, "research-matrix-user")
    diary = client.post(
        "/api/diaries",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "scene": "亲子沟通",
            "event_description": "我先停下来听完，再说自己的担心。",
            "parent_emotion": "着急",
        },
    )
    assert diary.status_code == 201
    program = client.post(
        "/api/programs/self_compassion_exam_anxiety/entries",
        headers={"Authorization": f"Bearer {token}"},
        json={"session_no": 1, "reflection": "我愿意先完成一个小步骤。", "recommendation_source": "user_choice"},
    )
    assert program.status_code == 201

    matrix = client.get(f"/api/research/participants?q={user_id}", headers=ADMIN_HEADERS)
    assert matrix.status_code == 200
    data = matrix.get_json()["data"]
    assert data["count"] == 1
    assert data["items"][0]["user_id"] == user_id
    assert data["items"][0]["diary_count"] == 1
    assert data["items"][0]["program_count"] == 1

    dossier = client.get(f"/api/research/participants/{user_id}", headers=ADMIN_HEADERS)
    assert dossier.status_code == 200
    detail = dossier.get_json()["data"]
    assert detail["participant"]["user_id"] == user_id
    assert detail["modules"]["diaries"][0]["event_description"]
    assert detail["modules"]["program_entries"][0]["reflection"]
    assert "原始填写" in detail["boundary_notice"]


def test_research_workspace_requires_research_role(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    assert client.get("/api/research/participants").status_code == 401
