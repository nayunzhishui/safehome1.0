import importlib
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"


def _fresh_app(tmp_path, monkeypatch):
    sys.path.insert(0, str(BACKEND))
    for name in list(sys.modules):
        if name in {"app", "config", "database", "models"} or name.startswith("routes.") or name.startswith("services."):
            sys.modules.pop(name, None)
    monkeypatch.setenv("APP_ENV", "pilot")
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "minor-input-types.sqlite3"))
    monkeypatch.setenv("CONTENT_DIR", str(ROOT / "content"))
    monkeypatch.setenv("DB_PROVIDER", "sqlite")
    monkeypatch.setenv("SECRET_KEY", "minor-input-types-secret-key-long-enough")
    monkeypatch.setenv("ADMIN_EXPORT_TOKEN", "legacy-admin-token")
    monkeypatch.delenv("LEGACY_ADMIN_TOKEN_ENABLED", raising=False)
    return importlib.import_module("app").app


def _register(client, username, role):
    response = client.post(
        "/api/auth/register",
        json={
            "username": username,
            "password": "StrongPass123!",
            "role": role,
            "nickname": username,
        },
    )
    assert response.status_code == 201, response.get_json()
    return response.get_json()["data"]


def _headers(token):
    return {"Authorization": f"Bearer {token}"}


def test_guardian_consent_rejects_string_boolean(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    parent = _register(client, "boolean-parent", "parent")
    student = _register(client, "boolean-student", "student")

    response = client.post(
        "/api/minor-safeguards/guardian-consent",
        headers=_headers(parent["token"]),
        json={"child_user_id": student["user"]["id"], "agreed": "false"},
    )

    assert response.status_code == 400
    assert response.get_json()["error"]["code"] == "invalid_boolean"
    assert response.get_json()["error"]["details"]["field"] == "agreed"


def test_child_assent_rejects_string_booleans(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    student = _register(client, "boolean-child", "student")
    headers = _headers(student["token"])

    assented = client.post(
        "/api/minor-safeguards/child-assent",
        headers=headers,
        json={"assented": "false"},
    )
    withdraw = client.post(
        "/api/minor-safeguards/child-assent",
        headers=headers,
        json={"withdraw": "false"},
    )

    assert assented.status_code == 400
    assert assented.get_json()["error"]["code"] == "invalid_boolean"
    assert assented.get_json()["error"]["details"]["field"] == "assented"
    assert withdraw.status_code == 400
    assert withdraw.get_json()["error"]["code"] == "invalid_boolean"
    assert withdraw.get_json()["error"]["details"]["field"] == "withdraw"
