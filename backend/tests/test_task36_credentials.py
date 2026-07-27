import importlib
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
ADMIN_HEADERS = {"X-Admin-Token": "safehome-local-admin-token"}


def _fresh_app(tmp_path, monkeypatch):
    sys.path.insert(0, str(BACKEND))
    for name in list(sys.modules):
        if name in {"app", "config", "database", "models"} or name.startswith("routes.") or name.startswith("services."):
            sys.modules.pop(name, None)
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "task36-credentials.sqlite3"))
    monkeypatch.setenv("CONTENT_DIR", str(ROOT / "content"))
    return importlib.import_module("app").app


def _temporary_account_payload(**overrides):
    payload = {
        "username": "safehome_researcher_01",
        "password": "Temporary-Researcher-Password-123!",
        "role": "researcher",
        "nickname": "任务36研究者",
        "temporary_credential": True,
        "credential_receipt_id": "credential_receipt_test_f01",
        "credential_expires_at": (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat(),
    }
    payload.update(overrides)
    return payload


def test_temporary_account_requires_password_change_before_research_access(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    created = client.post("/api/auth/admin-create-account", headers=ADMIN_HEADERS, json=_temporary_account_payload())

    assert created.status_code == 201
    login = client.post(
        "/api/auth/login",
        json={"username": "safehome_researcher_01", "password": "Temporary-Researcher-Password-123!"},
    )
    assert login.status_code == 200
    login_data = login.get_json()["data"]
    assert login_data["user"]["must_change_password"] is True
    blocked = client.get(
        "/api/research/participants",
        headers={"Authorization": f"Bearer {login_data['token']}"},
    )
    assert blocked.status_code == 403
    assert blocked.get_json()["error"]["code"] == "password_change_required"


def test_first_password_change_revokes_old_token_and_unlocks_research_access(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    client.post("/api/auth/admin-create-account", headers=ADMIN_HEADERS, json=_temporary_account_payload())
    login_data = client.post(
        "/api/auth/login",
        json={"username": "safehome_researcher_01", "password": "Temporary-Researcher-Password-123!"},
    ).get_json()["data"]
    old_headers = {"Authorization": f"Bearer {login_data['token']}"}

    changed = client.post(
        "/api/auth/change-password",
        headers=old_headers,
        json={
            "current_password": "Temporary-Researcher-Password-123!",
            "new_password": "Permanent-Researcher-Password-456!",
        },
    )

    assert changed.status_code == 200
    changed_data = changed.get_json()["data"]
    assert changed_data["user"]["must_change_password"] is False
    assert changed_data["sessions_revoked"] is True
    assert client.get("/api/auth/me", headers=old_headers).status_code == 401
    new_headers = {"Authorization": f"Bearer {changed_data['token']}"}
    assert client.get("/api/research/participants", headers=new_headers).status_code == 200
    assert client.post(
        "/api/auth/login",
        json={"username": "safehome_researcher_01", "password": "Temporary-Researcher-Password-123!"},
    ).status_code == 401


def test_expired_temporary_credential_is_rejected_without_creating_account(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    expired = client.post(
        "/api/auth/admin-create-account",
        headers=ADMIN_HEADERS,
        json=_temporary_account_payload(
            credential_expires_at=(datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat()
        ),
    )

    assert expired.status_code == 400
    assert expired.get_json()["error"]["code"] == "temporary_credential_expired"
    assert client.post(
        "/api/auth/login",
        json={"username": "safehome_researcher_01", "password": "Temporary-Researcher-Password-123!"},
    ).status_code == 401


def test_prepared_credential_that_expires_before_login_is_blocked(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    assert client.post(
        "/api/auth/admin-create-account", headers=ADMIN_HEADERS, json=_temporary_account_payload()
    ).status_code == 201
    with app.app_context():
        database = importlib.import_module("database")
        with database.get_connection() as conn:
            conn.execute(
                "UPDATE users SET credential_expires_at = ? WHERE username = ?",
                ((datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat(), "safehome_researcher_01"),
            )
            conn.commit()

    login = client.post(
        "/api/auth/login",
        json={"username": "safehome_researcher_01", "password": "Temporary-Researcher-Password-123!"},
    )

    assert login.status_code == 403
    assert login.get_json()["error"]["code"] == "temporary_credential_expired"


def test_repeated_login_failures_lock_account_until_admin_unlocks_it(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    assert client.post(
        "/api/auth/admin-create-account",
        headers=ADMIN_HEADERS,
        json=_temporary_account_payload(temporary_credential=False, credential_receipt_id=None, credential_expires_at=None),
    ).status_code == 201

    failures = [
        client.post(
            "/api/auth/login",
            json={"username": "safehome_researcher_01", "password": f"wrong-password-{index}"},
        )
        for index in range(5)
    ]
    assert [item.status_code for item in failures[:4]] == [401, 401, 401, 401]
    assert failures[-1].status_code == 423
    assert failures[-1].get_json()["error"]["code"] == "account_locked"
    still_locked = client.post(
        "/api/auth/login",
        json={"username": "safehome_researcher_01", "password": "Temporary-Researcher-Password-123!"},
    )
    assert still_locked.status_code == 423

    unlocked = client.post(
        "/api/auth/admin-accounts/safehome_researcher_01/unlock",
        headers=ADMIN_HEADERS,
    )
    assert unlocked.status_code == 200
    assert unlocked.get_json()["data"]["failed_login_count"] == 0
    assert client.post(
        "/api/auth/login",
        json={"username": "safehome_researcher_01", "password": "Temporary-Researcher-Password-123!"},
    ).status_code == 200


def test_reapplying_same_receipt_is_idempotent_but_different_create_receipt_conflicts(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    payload = _temporary_account_payload()
    first = client.post("/api/auth/admin-create-account", headers=ADMIN_HEADERS, json=payload)
    repeated = client.post("/api/auth/admin-create-account", headers=ADMIN_HEADERS, json=payload)
    conflicting = client.post(
        "/api/auth/admin-create-account",
        headers=ADMIN_HEADERS,
        json=_temporary_account_payload(credential_receipt_id="credential_receipt_other_f01"),
    )

    assert first.status_code == 201
    assert repeated.status_code == 200
    assert repeated.get_json()["data"]["already_applied"] is True
    assert conflicting.status_code == 409
    assert conflicting.get_json()["error"]["code"] == "username_exists"


def test_explicit_rotation_revokes_old_password_and_token_without_changing_role(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    original = _temporary_account_payload(
        temporary_credential=False,
        credential_receipt_id=None,
        credential_expires_at=None,
    )
    assert client.post("/api/auth/admin-create-account", headers=ADMIN_HEADERS, json=original).status_code == 201
    old_login = client.post(
        "/api/auth/login",
        json={"username": original["username"], "password": original["password"]},
    ).get_json()["data"]

    wrong_role = client.post(
        "/api/auth/admin-create-account",
        headers=ADMIN_HEADERS,
        json=_temporary_account_payload(
            password="Rotated-Supervisor-Password-456!",
            role="supervisor",
            rotate_existing=True,
            credential_receipt_id="credential_receipt_wrong_role",
        ),
    )
    assert wrong_role.status_code == 409
    assert wrong_role.get_json()["error"]["code"] == "role_change_forbidden"

    rotated_payload = _temporary_account_payload(
        password="Rotated-Researcher-Password-456!",
        rotate_existing=True,
        credential_receipt_id="credential_receipt_rotate_f01",
    )
    rotated = client.post("/api/auth/admin-create-account", headers=ADMIN_HEADERS, json=rotated_payload)
    assert rotated.status_code == 200
    assert rotated.get_json()["data"]["credentials_rotated"] is True
    assert client.get(
        "/api/auth/me", headers={"Authorization": f"Bearer {old_login['token']}"}
    ).status_code == 401
    assert client.post(
        "/api/auth/login",
        json={"username": original["username"], "password": original["password"]},
    ).status_code == 401
    new_login = client.post(
        "/api/auth/login",
        json={"username": original["username"], "password": rotated_payload["password"]},
    )
    assert new_login.status_code == 200
    assert new_login.get_json()["data"]["user"]["role"] == "researcher"
    assert new_login.get_json()["data"]["user"]["must_change_password"] is True


def test_rotate_requires_existing_account(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    rotated = app.test_client().post(
        "/api/auth/admin-create-account",
        headers=ADMIN_HEADERS,
        json=_temporary_account_payload(rotate_existing=True),
    )
    assert rotated.status_code == 404
    assert rotated.get_json()["error"]["code"] == "account_not_found"


def test_temporary_credential_requires_strong_password_and_unique_receipt(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    weak = client.post(
        "/api/auth/admin-create-account",
        headers=ADMIN_HEADERS,
        json=_temporary_account_payload(password="weakpass"),
    )
    assert weak.status_code == 400
    assert weak.get_json()["error"]["code"] == "validation_error"

    first = client.post(
        "/api/auth/admin-create-account", headers=ADMIN_HEADERS, json=_temporary_account_payload()
    )
    reused = client.post(
        "/api/auth/admin-create-account",
        headers=ADMIN_HEADERS,
        json=_temporary_account_payload(username="safehome_supervisor_01", role="supervisor"),
    )
    assert first.status_code == 201
    assert reused.status_code == 409
    assert reused.get_json()["error"]["code"] == "credential_receipt_reused"


def test_admin_can_verify_and_revoke_account_without_receiving_credentials(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    payload = _temporary_account_payload(
        temporary_credential=False,
        credential_receipt_id=None,
        credential_expires_at=None,
    )
    client.post("/api/auth/admin-create-account", headers=ADMIN_HEADERS, json=payload)
    login = client.post(
        "/api/auth/login", json={"username": payload["username"], "password": payload["password"]}
    ).get_json()["data"]

    verified = client.get(f"/api/auth/admin-accounts/{payload['username']}", headers=ADMIN_HEADERS)
    assert verified.status_code == 200
    verification = verified.get_json()["data"]
    assert verification["username"] == payload["username"]
    assert verification["role"] == "researcher"
    assert verification["password_configured"] is True
    assert "password" not in verification
    assert "password_hash" not in verification
    assert "credential_receipt_id" not in verification

    revoked = client.post(f"/api/auth/admin-accounts/{payload['username']}/revoke", headers=ADMIN_HEADERS)
    assert revoked.status_code == 200
    assert revoked.get_json()["data"]["status"] == "disabled"
    assert revoked.get_json()["data"]["tokens_revoked"] is True
    assert client.get(
        "/api/auth/me", headers={"Authorization": f"Bearer {login['token']}"}
    ).status_code in {401, 403}


def test_credential_lifecycle_schema_is_migrated_and_receipt_is_unique(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    with app.app_context():
        database = importlib.import_module("database")
        assert database.CURRENT_SCHEMA_VERSION == "2026_07_27_033"
        with database.get_connection() as conn:
            columns = {row["name"] for row in database.list_database_columns(conn, "users")}
            indexes = {
                row["name"]
                for row in conn.execute("PRAGMA index_list(users)").fetchall()
            }

    assert {
        "must_change_password",
        "credential_receipt_id",
        "credential_expires_at",
        "password_changed_at",
        "failed_login_count",
        "last_failed_login_at",
        "locked_until",
    }.issubset(columns)
    assert "idx_users_credential_receipt_unique" in indexes


def test_web_login_forces_temporary_account_to_change_password_before_navigation():
    page = (ROOT / "apps/web/src/pages/LoginPage.tsx").read_text(encoding="utf-8")
    api = (ROOT / "apps/web/src/services/safehomeApi.ts").read_text(encoding="utf-8")
    constants = (ROOT / "shared/constants/api.ts").read_text(encoding="utf-8")

    assert "must_change_password" in page
    assert "safeHomeApi.changePassword" in page
    assert "首次登录，请先设置新密码" in page
    assert "async changePassword" in api
    assert 'authChangePassword: "/api/auth/change-password"' in constants


def test_miniprogram_login_forces_temporary_account_to_change_password_before_navigation():
    page_js = (ROOT / "apps/miniprogram/pages/login/index.js").read_text(encoding="utf-8")
    page_wxml = (ROOT / "apps/miniprogram/pages/login/index.wxml").read_text(encoding="utf-8")
    api = (ROOT / "apps/miniprogram/services/api.js").read_text(encoding="utf-8")

    assert "must_change_password" in page_js
    assert "api.changePassword" in page_js
    assert "首次登录，请先设置新密码" in page_wxml
    assert "changePassword(data)" in api
    assert 'authChangePassword: "/api/auth/change-password"' in api
    assert 'backendCode !== "invalid_credentials"' in api


def test_credential_audit_and_security_events_do_not_store_plaintext_secrets(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    temporary_password = "Temporary-Researcher-Password-123!"
    permanent_password = "Permanent-Researcher-Password-456!"
    receipt_id = "credential_receipt_redaction_f01"
    payload = _temporary_account_payload(
        password=temporary_password,
        credential_receipt_id=receipt_id,
    )
    client.post("/api/auth/admin-create-account", headers=ADMIN_HEADERS, json=payload)
    login_data = client.post(
        "/api/auth/login", json={"username": payload["username"], "password": temporary_password}
    ).get_json()["data"]
    client.post(
        "/api/auth/change-password",
        headers={"Authorization": f"Bearer {login_data['token']}"},
        json={"current_password": temporary_password, "new_password": permanent_password},
    )
    client.post(
        "/api/auth/login", json={"username": payload["username"], "password": "known-wrong-password"}
    )

    with app.app_context():
        database = importlib.import_module("database")
        with database.get_connection() as conn:
            audit_rows = [dict(row) for row in conn.execute("SELECT * FROM audit_logs").fetchall()]
            security_rows = [dict(row) for row in conn.execute("SELECT * FROM security_events").fetchall()]
    serialized = str(audit_rows + security_rows)
    assert temporary_password not in serialized
    assert permanent_password not in serialized
    assert "known-wrong-password" not in serialized
    assert receipt_id not in serialized
