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
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "minor-consent-cycle.sqlite3"))
    monkeypatch.setenv("CONTENT_DIR", str(ROOT / "content"))
    monkeypatch.setenv("DB_PROVIDER", "sqlite")
    monkeypatch.setenv("SECRET_KEY", "minor-consent-cycle-secret-key-long-enough")
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


def test_guardian_reconsent_requires_fresh_child_assent(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    parent = _register(client, "cycle-parent", "parent")
    student = _register(client, "cycle-student", "student")
    parent_headers = _headers(parent["token"])
    student_headers = _headers(student["token"])
    child_id = student["user"]["id"]

    age = client.post(
        "/api/minor-safeguards/age-confirmation",
        headers=student_headers,
        json={"age_band": "under_14"},
    )
    assert age.status_code == 200

    bind_code_response = client.post(
        "/api/family/create-bind-code",
        headers=parent_headers,
        json={},
    )
    assert bind_code_response.status_code == 200
    bind_code = bind_code_response.get_json()["data"]["bind_code"]
    bound = client.post(
        "/api/family/bind-student",
        headers=student_headers,
        json={"bind_code": bind_code},
    )
    assert bound.status_code == 200

    consent = client.post(
        "/api/minor-safeguards/guardian-consent",
        headers=parent_headers,
        json={"child_user_id": child_id, "agreed": True},
    )
    assert consent.status_code == 200
    assent = client.post(
        "/api/minor-safeguards/child-assent",
        headers=student_headers,
        json={"assented": True},
    )
    assert assent.status_code == 200
    assert assent.get_json()["data"]["status"] == "active"

    guardian_withdraw = client.post(
        "/api/minor-safeguards/guardian-consent",
        headers=parent_headers,
        json={"child_user_id": child_id, "agreed": False},
    )
    assert guardian_withdraw.status_code == 200
    withdrawn_data = guardian_withdraw.get_json()["data"]
    assert withdrawn_data["status"] == "blocked_withdrawn_or_refused"
    assert withdrawn_data["child_assent_status"] == "pending"

    guardian_reconsent = client.post(
        "/api/minor-safeguards/guardian-consent",
        headers=parent_headers,
        json={"child_user_id": child_id, "agreed": True},
    )
    assert guardian_reconsent.status_code == 200
    reconsent_data = guardian_reconsent.get_json()["data"]
    assert reconsent_data["status"] == "child_assent_required"
    assert reconsent_data["child_assent_status"] == "pending"

    status = client.get(
        "/api/minor-safeguards/status",
        headers=student_headers,
    )
    assert status.status_code == 200
    assert status.get_json()["data"]["status"] == "child_assent_required"

    fresh_assent = client.post(
        "/api/minor-safeguards/child-assent",
        headers=student_headers,
        json={"assented": True},
    )
    assert fresh_assent.status_code == 200
    assert fresh_assent.get_json()["data"]["status"] == "active"
