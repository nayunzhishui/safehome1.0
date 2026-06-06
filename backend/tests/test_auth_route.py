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
    monkeypatch.delenv("ADMIN_EXPORT_TOKEN", raising=False)
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "safehome-test.sqlite3"))
    monkeypatch.setenv("CONTENT_DIR", str(PROJECT_ROOT / "content"))
    module = importlib.import_module("app")
    return module.app


def _register(client, username: str, role: str):
    return client.post(
        "/api/auth/register",
        json={
            "username": username,
            "password": "password123",
            "role": role,
            "nickname": "测试账号",
        },
    )


def test_public_register_allows_parent_and_student(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()

    for role in ["parent", "student"]:
        response = _register(client, f"{role}-user", role)

        assert response.status_code == 201
        body = response.get_json()
        assert body["ok"] is True
        assert body["data"]["token"]
        assert body["data"]["user"]["role"] == role


def test_public_register_rejects_backend_roles_without_token(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()

    for role in ["admin", "researcher", "supervisor"]:
        response = _register(client, f"{role}-user", role)

        assert response.status_code == 400
        body = response.get_json()
        assert body["ok"] is False
        assert body["error"]["code"] == "validation_error"
        assert "data" not in body or not body.get("data", {}).get("token")


def test_public_registered_accounts_cannot_access_admin_export(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()

    for role in ["parent", "student"]:
        register_response = _register(client, f"{role}-export-user", role)
        assert register_response.status_code == 201
        token = register_response.get_json()["data"]["token"]

        export_response = client.get("/api/admin/export?type=diaries", headers={"Authorization": f"Bearer {token}"})

        assert export_response.status_code == 403
