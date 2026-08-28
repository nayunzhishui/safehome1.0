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
    monkeypatch.setenv("APP_ENV", "testing")
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "minor-sensitive-writes.sqlite3"))
    monkeypatch.setenv("CONTENT_DIR", str(ROOT / "content"))
    monkeypatch.setenv("DB_PROVIDER", "sqlite")
    monkeypatch.setenv("SECRET_KEY", "minor-sensitive-write-secret-key-long-enough")
    monkeypatch.setenv("ADMIN_EXPORT_TOKEN", "legacy-admin-token")
    monkeypatch.setenv("LEGACY_ADMIN_TOKEN_ENABLED", "0")
    app = importlib.import_module("app").app
    safeguard_service = importlib.import_module("services.participant_safeguard_service")
    monkeypatch.setattr(safeguard_service.Config, "MINOR_SAFEGUARDS_ENFORCED", True, raising=False)
    return app


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


def _diary_payload():
    return {
        "scene": "学习安排",
        "event_description": "记录一次普通学习事件。",
        "parent_emotion": "平静",
    }


def test_age_confirmation_gates_diary_and_profile_writes(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    student = _register(client, "sensitive-write-student", "student")
    headers = _headers(student["token"])

    blocked_diary = client.post("/api/diaries", headers=headers, json=_diary_payload())
    blocked_profile = client.post("/api/profile", headers=headers, json={})

    assert blocked_diary.status_code == 403
    assert blocked_diary.get_json()["error"]["code"] == "age_verification_required"
    assert blocked_profile.status_code == 403
    assert blocked_profile.get_json()["error"]["code"] == "age_verification_required"

    age = client.post(
        "/api/minor-safeguards/age-confirmation",
        headers=headers,
        json={"age_band": "14_or_over"},
    )
    assert age.status_code == 200

    allowed_diary = client.post("/api/diaries", headers=headers, json=_diary_payload())
    profile_reaches_own_validation = client.post("/api/profile", headers=headers, json={})

    assert allowed_diary.status_code == 201
    assert profile_reaches_own_validation.status_code == 400
    assert profile_reaches_own_validation.get_json()["error"]["code"] == "missing_profile_scores"


def test_under14_withdrawal_reblocks_sensitive_writes(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    parent = _register(client, "withdraw-parent", "parent")
    student = _register(client, "withdraw-student", "student")
    parent_headers = _headers(parent["token"])
    student_headers = _headers(student["token"])

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
        json={"child_user_id": student["user"]["id"], "agreed": True},
    )
    assert consent.status_code == 200

    assent = client.post(
        "/api/minor-safeguards/child-assent",
        headers=student_headers,
        json={"assented": True},
    )
    assert assent.status_code == 200
    assert assent.get_json()["data"]["status"] == "active"

    allowed = client.post("/api/diaries", headers=student_headers, json=_diary_payload())
    assert allowed.status_code == 201

    withdrawn = client.post(
        "/api/minor-safeguards/child-assent",
        headers=student_headers,
        json={"withdraw": True},
    )
    assert withdrawn.status_code == 200
    assert withdrawn.get_json()["data"]["status"] == "blocked_withdrawn_or_refused"

    blocked = client.post("/api/diaries", headers=student_headers, json=_diary_payload())
    assert blocked.status_code == 403
    assert blocked.get_json()["error"]["code"] == "blocked_withdrawn_or_refused"
