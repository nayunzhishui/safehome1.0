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
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "minor-profile-scope.sqlite3"))
    monkeypatch.setenv("CONTENT_DIR", str(ROOT / "content"))
    monkeypatch.setenv("DB_PROVIDER", "sqlite")
    monkeypatch.setenv("SECRET_KEY", "minor-profile-scope-secret-key-long-enough")
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


def _activate_under14(client, parent, student):
    parent_headers = _headers(parent["token"])
    student_headers = _headers(student["token"])
    child_id = student["user"]["id"]

    assert client.post(
        "/api/minor-safeguards/age-confirmation",
        headers=student_headers,
        json={"age_band": "under_14"},
    ).status_code == 200
    code_response = client.post(
        "/api/family/create-bind-code",
        headers=parent_headers,
        json={},
    )
    assert code_response.status_code == 200
    assert client.post(
        "/api/family/bind-student",
        headers=student_headers,
        json={"bind_code": code_response.get_json()["data"]["bind_code"]},
    ).status_code == 200
    assert client.post(
        "/api/minor-safeguards/guardian-consent",
        headers=parent_headers,
        json={"child_user_id": child_id, "agreed": True},
    ).status_code == 200
    assent = client.post(
        "/api/minor-safeguards/child-assent",
        headers=student_headers,
        json={"assented": True},
    )
    assert assent.status_code == 200
    assert assent.get_json()["data"]["status"] == "active"


def test_unrelated_user_cannot_infer_profile_minor_status(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    parent = _register(client, "scope-parent", "parent")
    child = _register(client, "scope-child", "student")
    outsider = _register(client, "scope-outsider", "student")
    child_headers = _headers(child["token"])
    outsider_headers = _headers(outsider["token"])

    _activate_under14(client, parent, child)
    assert client.post(
        "/api/minor-safeguards/age-confirmation",
        headers=outsider_headers,
        json={"age_band": "14_or_over"},
    ).status_code == 200

    profile = client.post(
        "/api/profile",
        headers=child_headers,
        json={
            "user_id": child["user"]["id"],
            "scores": {
                "test_anxiety": 4.2,
                "iu_score": 4.1,
                "f_score": 2.8,
                "self_compassion": 2.7,
            },
            "free_text": "记录一次普通支持性画像内容。",
        },
    )
    assert profile.status_code == 201, profile.get_json()
    profile_id = profile.get_json()["data"]["student_profile_id"]

    before = client.post(
        f"/api/profile-results/{profile_id}/followups",
        headers=outsider_headers,
        json={"round_no": 1, "text": "普通随访文本。"},
    )
    assert before.status_code == 404
    before_error = before.get_json()["error"]
    assert before_error["code"] == "not_found"
    assert "details" not in before_error

    withdrawn = client.post(
        "/api/minor-safeguards/child-assent",
        headers=child_headers,
        json={"withdraw": True},
    )
    assert withdrawn.status_code == 200

    after = client.post(
        f"/api/profile-results/{profile_id}/followups",
        headers=outsider_headers,
        json={"round_no": 1, "text": "普通随访文本。"},
    )
    assert after.status_code == before.status_code
    assert after.get_json()["error"] == before_error
