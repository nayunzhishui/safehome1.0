import importlib
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"


def _fresh_app(tmp_path, monkeypatch, *, app_env="testing"):
    sys.path.insert(0, str(BACKEND))
    for name in list(sys.modules):
        if name in {"app", "config", "database", "models"} or name.startswith("routes.") or name.startswith("services."):
            sys.modules.pop(name, None)
    monkeypatch.setenv("APP_ENV", app_env)
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "participant-safeguards.sqlite3"))
    monkeypatch.setenv("CONTENT_DIR", str(ROOT / "content"))
    monkeypatch.setenv("DB_PROVIDER", "sqlite")
    if app_env == "production":
        monkeypatch.setenv("ALLOW_PRODUCTION_SQLITE", "1")
        monkeypatch.setenv("SECRET_KEY", "participant-safeguard-production-secret-key")
        monkeypatch.setenv("ADMIN_EXPORT_TOKEN", "production-legacy-token")
    return importlib.import_module("app").app


def _register(client, username: str, role: str):
    response = client.post(
        "/api/auth/register",
        json={
            "username": username,
            "password": "StrongPassword123!",
            "role": role,
            "nickname": username,
        },
    )
    assert response.status_code == 201
    data = response.get_json()["data"]
    return data["user"], data["token"]


def _diary_payload():
    return {
        "scene": "学习",
        "event_description": "今天记录一次普通情绪事件。",
        "parent_emotion": "紧张",
    }


def test_student_age_confirmation_is_required_before_ordinary_psychological_data(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    student, token = _register(client, "student-age-gate", "student")
    headers = {"Authorization": f"Bearer {token}"}

    blocked = client.post("/api/diaries", headers=headers, json=_diary_payload())
    assert blocked.status_code == 428
    assert blocked.get_json()["error"]["code"] == "participant_safeguard_required"
    assert blocked.get_json()["error"]["details"]["status"] == "age_confirmation_required"

    confirmed = client.post(
        "/api/consent/age-confirmation",
        headers=headers,
        json={"age_band": "14_or_older"},
    )
    assert confirmed.status_code == 201
    status = confirmed.get_json()["data"]["safeguard"]
    assert status["under_14"] is False
    assert status["processing_allowed"] is True
    assert status["exact_birth_date_collected"] is False

    allowed = client.post("/api/diaries", headers=headers, json=_diary_payload())
    assert allowed.status_code == 201
    assert allowed.get_json()["data"]["user_id"] == student["id"]


def test_under14_requires_active_guardian_consent_and_minor_assent(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    student, student_token = _register(client, "student-under14", "student")
    parent, parent_token = _register(client, "parent-under14", "parent")
    student_headers = {"Authorization": f"Bearer {student_token}"}
    parent_headers = {"Authorization": f"Bearer {parent_token}"}

    age = client.post(
        "/api/consent/age-confirmation",
        headers=student_headers,
        json={"age_band": "under_14"},
    )
    assert age.status_code == 201
    assert age.get_json()["data"]["safeguard"]["status"] == "guardian_link_required"

    blocked = client.post("/api/diaries", headers=student_headers, json=_diary_payload())
    assert blocked.status_code == 428

    bind = client.post("/api/family/create-bind-code", headers=parent_headers, json={"relation_label": "监护人"})
    assert bind.status_code == 200
    bind_code = bind.get_json()["data"]["bind_code"]
    linked = client.post("/api/family/bind-student", headers=student_headers, json={"bind_code": bind_code})
    assert linked.status_code == 200
    assert linked.get_json()["data"]["student_user_id"] == student["id"]
    assert linked.get_json()["data"]["parent_user_id"] == parent["id"]

    guardian = client.post(
        "/api/consent/guardian-sensitive-processing",
        headers=parent_headers,
        json={"child_user_id": student["id"], "agreed": True},
    )
    assert guardian.status_code == 201
    assert guardian.get_json()["data"]["safeguard"]["status"] == "minor_assent_required"

    assent = client.post(
        "/api/consent/minor-assent",
        headers=student_headers,
        json={"agreed": True},
    )
    assert assent.status_code == 201
    assert assent.get_json()["data"]["safeguard"]["status"] == "under14_safeguards_ready"
    assert assent.get_json()["data"]["safeguard"]["processing_allowed"] is True

    allowed = client.post("/api/diaries", headers=student_headers, json=_diary_payload())
    assert allowed.status_code == 201

    withdrawn = client.post(
        "/api/consent/guardian-sensitive-processing",
        headers=parent_headers,
        json={"child_user_id": student["id"], "agreed": False},
    )
    assert withdrawn.status_code == 201
    assert withdrawn.get_json()["data"]["safeguard"]["guardian_consent_active"] is False

    blocked_again = client.post("/api/diaries", headers=student_headers, json=_diary_payload())
    assert blocked_again.status_code == 428


def test_under14_safeguard_does_not_block_direct_help_routes(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    _, token = _register(client, "student-help-path", "student")
    headers = {"Authorization": f"Bearer {token}"}
    age = client.post(
        "/api/consent/age-confirmation",
        headers=headers,
        json={"age_band": "under_14"},
    )
    assert age.status_code == 201

    risk = client.post("/api/risk/check", headers=headers, json={"text": "我现在很难受"})
    assert risk.status_code != 428


def test_production_rejects_legacy_admin_token(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch, app_env="production")
    client = app.test_client()

    response = client.get(
        "/api/risk-review",
        headers={"X-Admin-Token": "production-legacy-token"},
    )
    assert response.status_code == 401
    assert response.get_json()["error"]["code"] == "legacy_admin_disabled"
