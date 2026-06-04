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
    if app_env == "production":
        monkeypatch.setenv("ADMIN_EXPORT_TOKEN", "production-test-token")
    else:
        monkeypatch.delenv("ADMIN_EXPORT_TOKEN", raising=False)
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "safehome-test.sqlite3"))
    monkeypatch.setenv("CONTENT_DIR", str(PROJECT_ROOT / "content"))
    module = importlib.import_module("app")
    return module.app


def test_create_and_list_consent_records(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()

    create_response = client.post(
        "/api/consent",
        json={
            "user_id": "parent-consent",
            "consent_type": "user_agreement",
            "consent_version": "2026.06-consent-v1",
            "agreed": True,
        },
    )

    assert create_response.status_code == 201
    created = create_response.get_json()["data"]
    assert created["user_id"] == "parent-consent"
    assert created["consent_type"] == "user_agreement"
    assert created["consent_version"] == "2026.06-consent-v1"
    assert created["agreed"] == 1
    assert created["revoked_at"] is None

    list_response = client.get("/api/consent?user_id=parent-consent")
    assert list_response.status_code == 200
    listed = list_response.get_json()["data"]
    assert listed["count"] == 1
    assert listed["items"][0]["id"] == created["id"]


def test_research_authorization_can_be_declined(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()

    response = client.post(
        "/api/consent",
        json={
            "user_id": "parent-consent",
            "consent_type": "research_authorization",
            "agreed": False,
        },
    )

    assert response.status_code == 201
    data = response.get_json()["data"]
    assert data["agreed"] == 0
    assert data["consent_version"] == "2026.06-consent-v1"
    assert data["revoked_at"]


def test_invalid_consent_type_is_rejected(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()

    response = client.post(
        "/api/consent",
        json={
            "user_id": "parent-consent",
            "consent_type": "clinical_diagnosis",
            "agreed": True,
        },
    )

    assert response.status_code == 400
    assert response.get_json()["error"]["code"] == "validation_error"


def test_production_consent_requires_user_id(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch, app_env="production")
    client = app.test_client()

    response = client.post(
        "/api/consent",
        json={
            "consent_type": "privacy_policy",
            "agreed": True,
        },
    )

    assert response.status_code == 400
    assert response.get_json()["error"]["code"] == "validation_error"
