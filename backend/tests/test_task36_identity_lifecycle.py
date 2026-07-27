import importlib
import hashlib
import os
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = PROJECT_ROOT / "backend"
ADMIN_HEADERS = {"X-Admin-Token": "safehome-local-admin-token"}


def _fresh_app(tmp_path, monkeypatch):
    sys.path.insert(0, str(BACKEND_ROOT))
    for name in list(sys.modules):
        if name in {"app", "config", "database", "models"} or name.startswith("routes.") or name.startswith("services."):
            sys.modules.pop(name, None)
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.delenv("ADMIN_EXPORT_TOKEN", raising=False)
    monkeypatch.delenv("WECHAT_APPID", raising=False)
    monkeypatch.delenv("WECHAT_SECRET", raising=False)
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "safehome-task36-f12.sqlite3"))
    monkeypatch.setenv("CONTENT_DIR", str(PROJECT_ROOT / "content"))
    return importlib.import_module("app").app


def _register(client, username, role="parent"):
    response = client.post(
        "/api/auth/register",
        json={"username": username, "password": "password-123", "role": role},
    )
    assert response.status_code == 201
    data = response.get_json()["data"]
    return data["user"], {"Authorization": f"Bearer {data['token']}"}


def _create_backend_identity(client, username, role, openid):
    created = client.post(
        "/api/auth/admin-create-account",
        headers=ADMIN_HEADERS,
        json={"username": username, "password": "password-123", "role": role},
    )
    assert created.status_code == 201
    database = importlib.import_module("database")
    with database.get_connection() as conn:
        conn.execute("UPDATE users SET wechat_openid = ? WHERE username = ?", (openid, username))
        conn.commit()


def _seed_goal(user_id, label):
    database = importlib.import_module("database")
    timestamp = database.now_iso()
    with database.get_connection() as conn:
        database.ensure_user(conn, user_id, label)
        goal_id = database.new_id("goal")
        conn.execute(
            """
            INSERT INTO goals (id, user_id, scene, smart_goal, motivation, start_date, status, created_at, updated_at)
            VALUES (?, ?, '沟通', ?, NULL, NULL, 'active', ?, ?)
            """,
            (goal_id, user_id, label, timestamp, timestamp),
        )
        conn.commit()
    return goal_id


def test_quick_login_never_inherits_backend_role(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    openid = f"dev_openid_{hashlib.sha256(b'backend-role-code').hexdigest()[:24]}"
    _create_backend_identity(client, "f12-researcher", "researcher", openid)

    response = client.post("/api/auth/wechat-login", json={"code": "backend-role-code"})

    assert response.status_code == 403
    body = response.get_json()
    assert body["error"]["code"] == "backend_role_quick_login_forbidden"
    assert not body.get("data", {}).get("token")


def test_phone_quick_login_never_inherits_backend_role(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    _create_backend_identity(client, "f12-phone-admin", "admin", "f12-unrelated-openid")
    auth_route = importlib.import_module("routes.auth")
    monkeypatch.setattr(
        auth_route,
        "_wechat_phone_from_code",
        lambda _code: {"phone_number": "13800001234", "pure_phone_number": "13800001234"},
    )
    with app.app_context():
        phone_hash = auth_route._phone_hash("13800001234")
    database = importlib.import_module("database")
    with database.get_connection() as conn:
        conn.execute("UPDATE users SET phone_hash = ? WHERE username = 'f12-phone-admin'", (phone_hash,))
        conn.commit()

    response = client.post("/api/auth/phone-login", json={"code": "phone-backend-role"})

    assert response.status_code == 403
    assert response.get_json()["error"]["code"] == "backend_role_quick_login_forbidden"


def test_identity_status_is_redacted_and_unbind_revokes_sessions_without_deleting_records(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    user, headers = _register(client, "f12-unbind")
    goal_id = _seed_goal(user["id"], "保留这条业务记录")
    database = importlib.import_module("database")
    with database.get_connection() as conn:
        conn.execute("UPDATE users SET wechat_openid = ? WHERE id = ?", ("f12-secret-openid", user["id"]))
        conn.commit()

    status = client.get("/api/auth/identity-status", headers=headers)
    assert status.status_code == 200
    status_data = status.get_json()["data"]
    assert status_data["identities"]["username"]["state"] == "bound_direct"
    assert status_data["identities"]["wechat"]["state"] == "bound_direct"
    assert "f12-secret-openid" not in str(status_data)

    unbound = client.post(
        "/api/auth/identity-unbind",
        headers=headers,
        json={"identity_type": "wechat", "confirm": True, "expected_auth_epoch": status_data["auth_epoch"]},
    )
    assert unbound.status_code == 200
    assert unbound.get_json()["data"]["sessions_revoked"] is True
    assert client.get("/api/auth/me", headers=headers).status_code == 401
    with database.get_connection() as conn:
        assert conn.execute("SELECT wechat_openid FROM users WHERE id = ?", (user["id"],)).fetchone()["wechat_openid"] is None
        assert conn.execute("SELECT COUNT(*) AS count FROM goals WHERE id = ?", (goal_id,)).fetchone()["count"] == 1


def test_unbind_rejects_removing_the_only_login_identity(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    login = client.post("/api/auth/wechat-login", json={"code": "sole-login-identity"})
    assert login.status_code == 200
    headers = {"Authorization": f"Bearer {login.get_json()['data']['token']}"}
    status = client.get("/api/auth/identity-status", headers=headers).get_json()["data"]

    response = client.post(
        "/api/auth/identity-unbind",
        headers=headers,
        json={"identity_type": "wechat", "confirm": True, "expected_auth_epoch": status["auth_epoch"]},
    )

    assert response.status_code == 409
    assert response.get_json()["error"]["code"] == "last_login_identity"


def test_claim_uses_version_and_idempotency_without_duplicate_audit(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    anonymous_id = "web_user_1760000001000_f12abc"
    _seed_goal(anonymous_id, "匿名记录")
    registered = client.post(
        "/api/auth/register",
        json={
            "username": "f12-claim",
            "password": "password-123",
            "role": "parent",
            "anonymous_id": anonymous_id,
        },
    ).get_json()["data"]
    headers = {
        "Authorization": f"Bearer {registered['token']}",
        "Idempotency-Key": "f12-claim-once",
    }
    preview = client.get("/api/auth/data-claim-preview", headers=headers).get_json()["data"]
    assert preview["version"] == 0

    payload = {"claim_id": preview["claim_id"], "confirm": True, "expected_version": preview["version"]}
    first = client.post("/api/auth/data-claim", headers=headers, json=payload)
    second = client.post("/api/auth/data-claim", headers=headers, json=payload)

    assert first.status_code == 200
    assert second.status_code == 200
    assert second.get_json()["data"]["already_completed"] is True
    database = importlib.import_module("database")
    with database.get_connection() as conn:
        claim = conn.execute("SELECT * FROM data_claims WHERE id = ?", (preview["claim_id"],)).fetchone()
        assert claim["status"] == "claimed"
        assert claim["idempotency_key"] == "f12-claim-once"
        assert int(claim["version"]) == 2
        audit_count = conn.execute(
            "SELECT COUNT(*) AS count FROM audit_logs WHERE action = 'anonymous_data_claimed'"
        ).fetchone()["count"]
        assert audit_count == 1


def test_account_merge_requires_confirmation_preserves_role_and_can_rollback(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    source, _source_headers = _register(client, "f12-source")
    target, _target_headers = _register(client, "f12-target", role="student")
    goal_id = _seed_goal(source["id"], "需要迁移的记录")

    candidate = client.post(
        "/api/auth/admin-account-merges",
        headers={**ADMIN_HEADERS, "Idempotency-Key": "f12-merge-candidate"},
        json={"source_user_id": source["id"], "target_user_id": target["id"], "reason_code": "identity_conflict"},
    )
    assert candidate.status_code == 201
    workflow = candidate.get_json()["data"]
    assert workflow["status"] == "candidate"

    blocked = client.post(
        f"/api/auth/admin-account-merges/{workflow['id']}/execute",
        headers=ADMIN_HEADERS,
        json={"expected_version": workflow["version"]},
    )
    assert blocked.status_code == 409

    confirmed = client.post(
        f"/api/auth/admin-account-merges/{workflow['id']}/confirm",
        headers=ADMIN_HEADERS,
        json={"confirm": True, "expected_version": workflow["version"]},
    ).get_json()["data"]
    executed = client.post(
        f"/api/auth/admin-account-merges/{workflow['id']}/execute",
        headers={**ADMIN_HEADERS, "Idempotency-Key": "f12-merge-execute"},
        json={"expected_version": confirmed["version"]},
    )
    assert executed.status_code == 200
    executed_data = executed.get_json()["data"]
    assert executed_data["status"] == "executed"

    database = importlib.import_module("database")
    with database.get_connection() as conn:
        assert conn.execute("SELECT user_id FROM goals WHERE id = ?", (goal_id,)).fetchone()["user_id"] == target["id"]
        assert conn.execute("SELECT role FROM users WHERE id = ?", (target["id"],)).fetchone()["role"] == "student"
        source_row = conn.execute("SELECT status, merged_into_user_id FROM users WHERE id = ?", (source["id"],)).fetchone()
        assert source_row["status"] == "merged"
        assert source_row["merged_into_user_id"] == target["id"]

    verified = client.post(
        f"/api/auth/admin-account-merges/{workflow['id']}/verify",
        headers=ADMIN_HEADERS,
        json={"expected_version": executed_data["version"]},
    ).get_json()["data"]
    rolled_back = client.post(
        f"/api/auth/admin-account-merges/{workflow['id']}/rollback",
        headers={**ADMIN_HEADERS, "Idempotency-Key": "f12-merge-rollback"},
        json={"confirm": True, "expected_version": verified["version"]},
    )
    assert rolled_back.status_code == 200
    assert rolled_back.get_json()["data"]["status"] == "rolled_back"
    with database.get_connection() as conn:
        assert conn.execute("SELECT user_id FROM goals WHERE id = ?", (goal_id,)).fetchone()["user_id"] == source["id"]
        source_row = conn.execute("SELECT status, merged_into_user_id FROM users WHERE id = ?", (source["id"],)).fetchone()
        assert source_row["status"] == "active"
        assert source_row["merged_into_user_id"] is None


def test_backend_roles_cannot_enter_account_merge_workflow(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    participant, _headers = _register(client, "f12-participant")
    _create_backend_identity(client, "f12-admin-source", "admin", "f12-admin-openid")
    database = importlib.import_module("database")
    with database.get_connection() as conn:
        backend = conn.execute("SELECT id FROM users WHERE username = 'f12-admin-source'").fetchone()

    response = client.post(
        "/api/auth/admin-account-merges",
        headers={**ADMIN_HEADERS, "Idempotency-Key": "f12-role-block"},
        json={"source_user_id": backend["id"], "target_user_id": participant["id"], "reason_code": "wrong_role"},
    )

    assert response.status_code == 409
    assert response.get_json()["error"]["code"] == "merge_role_forbidden"


def test_merge_rollback_rejects_claim_completed_after_merge(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    source, _source_headers = _register(client, "f12-claim-source")
    target, _target_headers = _register(client, "f12-claim-target")
    database = importlib.import_module("database")
    timestamp = database.now_iso()
    claim_id = database.new_id("claim")
    with database.get_connection() as conn:
        conn.execute(
            """
            INSERT INTO data_claims (
                id, anonymous_id, target_user_id, status, counts_json,
                claimed_at, created_at, updated_at, idempotency_key, version
            ) VALUES (?, ?, ?, 'available', '{}', NULL, ?, ?, NULL, 0)
            """,
            (claim_id, "web_user_1760000002000_f12abc", source["id"], timestamp, timestamp),
        )
        conn.commit()

    candidate = client.post(
        "/api/auth/admin-account-merges",
        headers={**ADMIN_HEADERS, "Idempotency-Key": "f12-claim-merge-candidate"},
        json={"source_user_id": source["id"], "target_user_id": target["id"], "reason_code": "identity_conflict"},
    ).get_json()["data"]
    confirmed = client.post(
        f"/api/auth/admin-account-merges/{candidate['id']}/confirm",
        headers=ADMIN_HEADERS,
        json={"confirm": True, "expected_version": candidate["version"]},
    ).get_json()["data"]
    executed = client.post(
        f"/api/auth/admin-account-merges/{candidate['id']}/execute",
        headers={**ADMIN_HEADERS, "Idempotency-Key": "f12-claim-merge-execute"},
        json={"expected_version": confirmed["version"]},
    ).get_json()["data"]
    with database.get_connection() as conn:
        conn.execute(
            "UPDATE data_claims SET status = 'claimed', version = version + 1 WHERE id = ?",
            (claim_id,),
        )
        conn.commit()

    response = client.post(
        f"/api/auth/admin-account-merges/{candidate['id']}/rollback",
        headers={**ADMIN_HEADERS, "Idempotency-Key": "f12-claim-merge-rollback"},
        json={"confirm": True, "expected_version": executed["version"]},
    )

    assert response.status_code == 409
    assert response.get_json()["error"]["code"] == "merge_rollback_conflict"
    with database.get_connection() as conn:
        claim = conn.execute(
            "SELECT target_user_id, status FROM data_claims WHERE id = ?",
            (claim_id,),
        ).fetchone()
        assert claim["target_user_id"] == target["id"]
        assert claim["status"] == "claimed"
        workflow = conn.execute(
            "SELECT status FROM identity_merge_workflows WHERE id = ?",
            (candidate["id"],),
        ).fetchone()
        assert workflow["status"] == "executed"


def test_identity_lifecycle_migration_is_additive_and_repeatable(tmp_path, monkeypatch):
    _fresh_app(tmp_path, monkeypatch)
    migration = importlib.import_module("scripts.migrate_task36_identity_claims")

    first = migration.inspect()
    migration.apply()
    second = migration.inspect()
    rollback = migration.rollback()

    assert first["ok"] is True
    assert second["ok"] is True
    assert second["schema_version"] == "2026_07_27_034"
    assert second["schema_name"] == "therapeutic_assessment_dynamic_consent"
    assert rollback["schema_preserved"] is True
    assert rollback["business_records_preserved"] is True
