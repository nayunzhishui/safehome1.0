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


def test_admin_create_account_requires_valid_admin_token(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()

    payload = {
        "username": "created-researcher",
        "password": "password123",
        "role": "researcher",
        "nickname": "研究员账号",
    }

    no_token = client.post("/api/auth/admin-create-account", json=payload)
    wrong_token = client.post("/api/auth/admin-create-account", json=payload, headers={"X-Admin-Token": "wrong-token"})
    ok_response = client.post(
        "/api/auth/admin-create-account",
        json=payload,
        headers={"X-Admin-Token": "safehome-local-admin-token"},
    )

    assert no_token.status_code == 401
    assert wrong_token.status_code == 401
    assert ok_response.status_code == 201
    body = ok_response.get_json()
    assert body["ok"] is True
    assert body["data"]["user"]["role"] == "researcher"
    assert "token" not in body["data"]


def test_admin_created_backend_account_can_login_with_role(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()

    create_response = client.post(
        "/api/auth/admin-create-account",
        json={
            "username": "created-supervisor",
            "password": "password123",
            "role": "supervisor",
            "nickname": "督导账号",
        },
        headers={"X-Admin-Token": "safehome-local-admin-token"},
    )
    assert create_response.status_code == 201

    login_response = client.post(
        "/api/auth/login",
        json={"username": "created-supervisor", "password": "password123"},
    )

    assert login_response.status_code == 200
    body = login_response.get_json()
    assert body["ok"] is True
    assert body["data"]["token"]
    assert body["data"]["user"]["role"] == "supervisor"


def test_admin_create_account_rejects_unknown_role(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()

    response = client.post(
        "/api/auth/admin-create-account",
        json={
            "username": "created-unknown",
            "password": "password123",
            "role": "owner",
        },
        headers={"X-Admin-Token": "safehome-local-admin-token"},
    )

    assert response.status_code == 400
    body = response.get_json()
    assert body["ok"] is False
    assert body["error"]["code"] == "validation_error"
