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
    monkeypatch.delenv("DB_PROVIDER", raising=False)
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "safehome-test.sqlite3"))
    monkeypatch.setenv("CONTENT_DIR", str(PROJECT_ROOT / "content"))
    module = importlib.import_module("app")
    return module.app


def _register(client, username: str, role: str) -> tuple[str, str]:
    response = client.post(
        "/api/auth/register",
        json={"username": username, "password": "password123", "role": role},
    )
    assert response.status_code == 201
    data = response.get_json()["data"]
    return data["user"]["id"], data["token"]


def test_parent_creates_expiring_bind_code_and_student_binds(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    _, parent_token = _register(client, "family-parent", "parent")
    student_id, student_token = _register(client, "family-student", "student")

    create = client.post(
        "/api/family/create-bind-code",
        headers={"Authorization": f"Bearer {parent_token}"},
        json={"relation_label": "家长"},
    )
    assert create.status_code == 200
    created = create.get_json()["data"]
    assert len(created["bind_code"]) == 10
    assert created["expires_at"]
    assert created["max_attempts"] == 5

    bind = client.post(
        "/api/family/bind-student",
        headers={"Authorization": f"Bearer {student_token}"},
        json={"bind_code": created["bind_code"]},
    )
    assert bind.status_code == 200
    data = bind.get_json()["data"]
    assert data["student_user_id"] == student_id
    assert data["status"] == "consumed"
    assert data["attempt_count"] == 1


def test_expired_bind_code_uses_generic_unavailable_response(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    _, parent_token = _register(client, "expired-parent", "parent")
    _, student_token = _register(client, "expired-student", "student")

    create = client.post("/api/family/create-bind-code", headers={"Authorization": f"Bearer {parent_token}"})
    created = create.get_json()["data"]
    bind_code = created["bind_code"]

    import database

    with database.get_connection() as conn:
        conn.execute(
            "UPDATE family_links SET expires_at = '2020-01-01T00:00:00+00:00' WHERE id = ?",
            (created["id"],),
        )
        conn.commit()

    bind = client.post(
        "/api/family/bind-student",
        headers={"Authorization": f"Bearer {student_token}"},
        json={"bind_code": bind_code},
    )
    assert bind.status_code == 400
    assert bind.get_json()["error"]["code"] == "bind_code_unavailable"


def test_bind_code_rate_limit_returns_429(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    _, parent_token = _register(client, "limited-parent", "parent")
    _, student_token = _register(client, "limited-student", "student")

    client.post("/api/family/create-bind-code", headers={"Authorization": f"Bearer {parent_token}"})

    headers = {"Authorization": f"Bearer {student_token}", "X-Device-Id": "family-limit-device"}
    responses = [
        client.post(
            "/api/family/bind-student",
            headers=headers,
            json={"bind_code": "9999999999"},
        )
        for _ in range(6)
    ]
    bind = responses[-1]
    assert bind.status_code == 429
    assert bind.get_json()["error"]["code"] == "family_binding_rate_limited"
