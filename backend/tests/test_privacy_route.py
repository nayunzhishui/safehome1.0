import importlib
import os
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = PROJECT_ROOT / "backend"
ADMIN_HEADERS = {"X-Admin-Token": "safehome-local-admin-token"}


def _fresh_app(tmp_path):
    sys.path.insert(0, str(BACKEND_ROOT))
    for name in list(sys.modules):
        if name in {"app", "config", "database", "models"} or name.startswith("routes.") or name.startswith("services."):
            sys.modules.pop(name, None)
    os.environ["DATABASE_PATH"] = str(tmp_path / "safehome-test.sqlite3")
    os.environ["CONTENT_DIR"] = str(PROJECT_ROOT / "content")
    os.environ.pop("APP_ENV", None)
    os.environ.pop("DB_PROVIDER", None)
    module = importlib.import_module("app")
    return module.app


def _fresh_production_app(tmp_path, monkeypatch):
    sys.path.insert(0, str(BACKEND_ROOT))
    for name in list(sys.modules):
        if name in {"app", "config", "database", "models"} or name.startswith("routes.") or name.startswith("services."):
            sys.modules.pop(name, None)
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("DB_PROVIDER", "sqlite")
    monkeypatch.setenv("ALLOW_PRODUCTION_SQLITE", "1")
    monkeypatch.setenv("ADMIN_EXPORT_TOKEN", "production-test-admin-token")
    monkeypatch.setenv("SECRET_KEY", "production-test-secret-key-32-chars")
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "safehome-production-test.sqlite3"))
    monkeypatch.setenv("CONTENT_DIR", str(PROJECT_ROOT / "content"))
    module = importlib.import_module("app")
    return module.app


def _register(client, username: str):
    response = client.post(
        "/api/auth/register",
        json={"username": username, "password": "password123", "role": "parent"},
    )
    assert response.status_code == 201
    data = response.get_json()["data"]
    return data["user"]["id"], data["token"]


def _wechat_login(client, code: str):
    response = client.post("/api/auth/wechat-login", json={"code": code, "nickname": code})
    assert response.status_code == 200
    data = response.get_json()["data"]
    return data["user"]["id"], data["token"]


def test_revoke_research_consent_writes_consent_and_audit(tmp_path):
    app = _fresh_app(tmp_path)
    client = app.test_client()

    response = client.post(
        "/api/privacy/revoke-consent",
        json={"user_id": "privacy-user", "consent_type": "anonymous_research", "reason": "用户主动撤回"},
    )

    assert response.status_code == 200
    data = response.get_json()["data"]
    assert data["agreed"] is False
    assert data["revoked_at"]

    import database

    with database.get_connection() as conn:
        consent = conn.execute("SELECT * FROM consent_records WHERE user_id = ?", ("privacy-user",)).fetchone()
        audit = conn.execute("SELECT * FROM audit_logs WHERE action = 'privacy_revoke_consent'").fetchone()

    assert consent["consent_type"] == "anonymous_research"
    assert consent["agreed"] == 0
    assert audit["actor_id"] == "privacy-user"


def test_delete_request_and_my_data_summary_avoid_raw_text(tmp_path):
    app = _fresh_app(tmp_path)
    client = app.test_client()
    user_id, token = _wechat_login(client, "privacy-summary-user")

    diary = client.post(
        "/api/diaries",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "user_id": user_id,
            "scene": "作业沟通",
            "event_description": "PRIVATE_RAW_EVENT",
            "parent_emotion": "着急",
        },
    )
    assert diary.status_code == 201

    delete_response = client.post(
        "/api/privacy/delete-my-data",
        json={"user_id": user_id, "reason": "希望删除试用数据"},
    )
    summary_response = client.get(f"/api/privacy/export-my-data?user_id={user_id}")

    assert delete_response.status_code == 201
    assert summary_response.status_code == 200
    data = summary_response.get_json()["data"]
    assert data["counts"]["diaries"] == 1
    assert data["privacy_requests"][0]["status"] == "pending"
    assert "PRIVATE_RAW_EVENT" not in str(data)


def test_revoked_research_consent_excludes_user_from_research_exports(tmp_path):
    app = _fresh_app(tmp_path)
    client = app.test_client()

    import database

    with database.get_connection() as conn:
        conn.execute(
            """
            INSERT INTO student_profiles (
                id, user_id, anonymous_id, assessment_result_id, round, source,
                scores_json, text_features_json, profile_code, profile_name,
                confidence, dimensions_json, recommended_task_ids_json,
                risk_level, requires_review, boundary_notice, rules_version,
                report_json, visuals_json, export_allowed, created_at, updated_at
            )
            VALUES (
                'profile_revoked_001', 'privacy-revoked-user', 'anon_revoked',
                NULL, 1, 'test', '{}', '{}', 'support_profile', '阶段性画像',
                0.8, '[]', '[]', 'low', 0, '边界提示', 'test',
                '{}', '{}', 1,
                '2026-06-06T00:00:00+00:00', '2026-06-06T00:00:00+00:00'
            )
            """
        )
        conn.execute(
            """
            INSERT INTO records (
                id, user_id, module_type, source_id, data_json,
                created_at, updated_at, export_allowed
            )
            VALUES (
                'record_revoked_001', 'privacy-revoked-user', 'student_profile',
                'profile_revoked_001',
                '{"anonymous_id":"anon_revoked","risk_level":"low","requires_review":false,"profile_code":"support_profile"}',
                '2026-06-06T00:00:00+00:00', '2026-06-06T00:00:00+00:00', 1
            )
            """
        )
        conn.commit()

    before = client.get("/api/admin/export?type=records&module_type=student_profile", headers=ADMIN_HEADERS)
    assert before.status_code == 200
    assert "anon_revoked" in before.get_data(as_text=True)

    revoke = client.post("/api/privacy/revoke-consent", json={"user_id": "privacy-revoked-user"})
    assert revoke.status_code == 200

    after = client.get("/api/admin/export?type=records&module_type=student_profile", headers=ADMIN_HEADERS)
    assert after.status_code == 200
    assert "anon_revoked" not in after.get_data(as_text=True)


def test_production_privacy_endpoints_require_login(tmp_path, monkeypatch):
    app = _fresh_production_app(tmp_path, monkeypatch)
    client = app.test_client()

    revoke = client.post("/api/privacy/revoke-consent", json={"user_id": "privacy-prod-user"})
    delete = client.post("/api/privacy/delete-my-data", json={"user_id": "privacy-prod-user"})
    summary = client.get("/api/privacy/export-my-data?user_id=privacy-prod-user")

    assert revoke.status_code == 401
    assert delete.status_code == 401
    assert summary.status_code == 401


def test_production_privacy_owner_can_operate_own_user_id(tmp_path, monkeypatch):
    app = _fresh_production_app(tmp_path, monkeypatch)
    client = app.test_client()
    user_id, token = _register(client, "privacy-owner")
    headers = {"Authorization": f"Bearer {token}"}

    revoke = client.post(
        "/api/privacy/revoke-consent",
        headers=headers,
        json={"user_id": user_id, "consent_type": "anonymous_research"},
    )
    delete = client.post("/api/privacy/delete-my-data", headers=headers, json={"user_id": user_id})
    summary = client.get(f"/api/privacy/export-my-data?user_id={user_id}", headers=headers)

    assert revoke.status_code == 200
    assert delete.status_code == 201
    assert summary.status_code == 200
    assert "boundary_notice" in summary.get_json()["data"]


def test_privacy_owner_mismatch_returns_403(tmp_path, monkeypatch):
    app = _fresh_production_app(tmp_path, monkeypatch)
    client = app.test_client()
    owner_id, token = _register(client, "privacy-owner-a")
    other_id, _ = _register(client, "privacy-owner-b")
    headers = {"Authorization": f"Bearer {token}"}

    revoke = client.post(
        "/api/privacy/revoke-consent",
        headers=headers,
        json={"user_id": other_id, "consent_type": "anonymous_research"},
    )
    delete = client.post("/api/privacy/delete-my-data", headers=headers, json={"user_id": other_id})
    summary = client.get(f"/api/privacy/export-my-data?user_id={other_id}", headers=headers)

    assert owner_id != other_id
    assert revoke.status_code == 403
    assert delete.status_code == 403
    assert summary.status_code == 403
