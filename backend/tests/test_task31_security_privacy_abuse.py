import importlib
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"


def _fresh_app(tmp_path, monkeypatch, *, scan_enabled=True):
    sys.path.insert(0, str(BACKEND))
    for name in list(sys.modules):
        if name in {"app", "config", "database", "models"} or name.startswith("routes.") or name.startswith("services.") or name.startswith("scripts."):
            sys.modules.pop(name, None)
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "task31.sqlite3"))
    monkeypatch.setenv("CONTENT_DIR", str(ROOT / "content"))
    monkeypatch.setenv("SECURITY_SCAN_EXECUTION_ENABLED", "1" if scan_enabled else "0")
    monkeypatch.setenv("AI_QA_ENABLED", "0")
    monkeypatch.setenv("AI_QA_PROVIDER", "fake")
    return importlib.import_module("app").app


def _actors(app):
    specs = [("participant-a", "parent"), ("researcher-a", "researcher"), ("supervisor-a", "supervisor"), ("admin-a", "admin")]
    with app.app_context():
        database = importlib.import_module("database")
        auth = importlib.import_module("routes.auth_utils")
        with database.get_connection() as conn:
            now = database.now_iso()
            for actor_id, role in specs:
                conn.execute(
                    "INSERT INTO users (id, nickname, role, source, status, created_at, updated_at) VALUES (?, ?, ?, 'test', 'active', ?, ?)",
                    (actor_id, actor_id, role, now, now),
                )
            conn.commit()
        return {actor_id: {"Authorization": f"Bearer {auth.generate_auth_token({'id': actor_id, 'role': role})}"} for actor_id, role in specs}


def _login(client, code):
    response = client.post("/api/auth/wechat-login", json={"code": code, "nickname": code})
    assert response.status_code == 200
    return response.get_json()["data"]


def _headers(token, key=None):
    result = {"Authorization": f"Bearer {token}"}
    if key:
        result["Idempotency-Key"] = key
    return result


def _set_role(app, user_id, role):
    with app.app_context():
        database = importlib.import_module("database")
        with database.get_connection() as conn:
            conn.execute("UPDATE users SET role = ? WHERE id = ?", (role, user_id))
            conn.commit()


def test_public_status_is_minimal_and_workbench_is_role_restricted(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    headers = _actors(app)
    client = app.test_client()
    public = client.get("/api/security/public-status")
    participant = client.get("/api/security/workbench", headers=headers["participant-a"])
    internal = client.get("/api/security/workbench", headers=headers["researcher-a"])
    assert public.status_code == 200 and participant.status_code == 403 and internal.status_code == 200
    data = public.get_json()["data"]
    assert data["formal_permission_acceptance_passed"] is False
    assert data["temporary_showcase_exception_enabled"] is True
    assert data["participant_ai_enabled"] is False
    assert "asset_inventory" not in data and "events" not in data


def test_registry_covers_every_operation_and_keeps_showcase_as_blocker(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    headers = _actors(app)
    data = app.test_client().get("/api/security/workbench", headers=headers["admin-a"]).get_json()["data"]
    registry = data["registry"]
    matrix = registry["authorization_matrix"]
    contract_count = len(json.loads((ROOT / "shared/contracts/api-contract.json").read_text(encoding="utf-8"))["endpoints"])
    assert len(matrix) == registry["authorization_summary"]["operation_count"] == contract_count
    assert len({item["operation_id"] for item in matrix}) == contract_count
    assert all(set(item["allowed_roles"]).isdisjoint(item["denied_roles"]) for item in matrix)
    assert registry["authorization_summary"]["formal_permission_acceptance_passed"] is False
    assert registry["temporary_showcase_exception"]["accepted_for_formal_permission_testing"] is False


def test_security_scan_is_admin_only_redacted_and_audited(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    headers = _actors(app)
    client = app.test_client()
    denied = client.post("/api/security/scans", headers=headers["researcher-a"])
    result = client.post("/api/security/scans", headers=headers["admin-a"])
    assert denied.status_code == 403 and result.status_code == 200
    data = result.get_json()["data"]
    assert data["hard_checks_passed"] is True and data["blockers"] == []
    assert data["secret_values_returned"] is False and data["production_approval_inferred"] is False
    assert "network_dependency_advisories" in data["warnings"]
    with app.app_context():
        database = importlib.import_module("database")
        with database.get_connection() as conn:
            assert conn.execute("SELECT COUNT(*) AS count FROM security_control_runs").fetchone()["count"] == 1
            assert conn.execute("SELECT COUNT(*) AS count FROM audit_logs WHERE action = 'security_scan_run'").fetchone()["count"] == 1


def test_disabled_scan_remains_readable_but_cannot_run(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch, scan_enabled=False)
    headers = _actors(app)
    client = app.test_client()
    assert client.get("/api/security/workbench", headers=headers["admin-a"]).status_code == 200
    blocked = client.post("/api/security/scans", headers=headers["admin-a"])
    assert blocked.status_code == 503 and blocked.get_json()["error"]["code"] == "security_scan_disabled"


def test_logout_rotates_auth_epoch_and_invalidates_existing_token(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    account = client.post("/api/auth/register", json={"username": "logout-user", "password": "password123", "role": "parent"}).get_json()["data"]
    headers = _headers(account["token"])
    assert client.get("/api/auth/me", headers=headers).status_code == 200
    logout = client.post("/api/auth/logout", headers=headers)
    assert logout.status_code == 200 and logout.get_json()["data"]["message"]
    assert client.get("/api/auth/me", headers=headers).status_code == 401
    anonymous = client.post("/api/auth/logout")
    assert anonymous.status_code == 200 and anonymous.get_json()["data"]["tokens_revoked"] is False


def test_admin_account_disable_and_recovery_revoke_old_tokens(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    headers = _actors(app)
    client = app.test_client()
    denied = client.patch("/api/security/accounts/participant-a/status", headers=headers["supervisor-a"], json={"status": "disabled", "reason_code": "security_review"})
    disabled = client.patch("/api/security/accounts/participant-a/status", headers=headers["admin-a"], json={"status": "disabled", "reason_code": "security_review", "expected_auth_epoch": 0})
    assert denied.status_code == 403 and disabled.status_code == 200
    assert disabled.get_json()["data"]["tokens_revoked"] is True
    assert client.get("/api/auth/me", headers=headers["participant-a"]).status_code in {401, 403}
    repeated = client.patch("/api/security/accounts/participant-a/status", headers=headers["admin-a"], json={"status": "disabled", "reason_code": "security_review", "expected_auth_epoch": 1})
    assert repeated.status_code == 200 and repeated.get_json()["data"]["already_applied"] is True
    restored = client.patch("/api/security/accounts/participant-a/status", headers=headers["admin-a"], json={"status": "active", "reason_code": "account_recovery", "expected_auth_epoch": 1})
    assert restored.status_code == 200 and restored.get_json()["data"]["auth_epoch"] == 2


def test_security_event_resolution_is_admin_only_and_audited(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    headers = _actors(app)
    client = app.test_client()
    client.post("/api/auth/login", json={"username": "missing-user", "password": "wrong-password"})
    workbench = client.get("/api/security/workbench", headers=headers["admin-a"]).get_json()["data"]
    event = next(item for item in workbench["events"] if item["event_type"] == "login_failed")
    denied = client.post(f"/api/security/events/{event['id']}/resolve", headers=headers["researcher-a"])
    resolved = client.post(f"/api/security/events/{event['id']}/resolve", headers=headers["admin-a"])
    assert denied.status_code == 403 and resolved.status_code == 200
    assert resolved.get_json()["data"]["status"] == "resolved"


def test_csv_export_escapes_formula_cells_and_sets_safe_headers(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    headers = _actors(app)
    with app.app_context():
        database = importlib.import_module("database")
        with database.get_connection() as conn:
            now = database.now_iso()
            conn.execute("INSERT INTO goals (id, user_id, scene, smart_goal, status, created_at, updated_at) VALUES ('goal-injection', 'participant-a', '=HYPERLINK(\"https://bad\")', 'safe', 'active', ?, ?)", (now, now))
            conn.commit()
    response = app.test_client().get("/api/admin/export?type=goals", headers=headers["admin-a"])
    text = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "'=HYPERLINK" in text and "\n=HYPERLINK" not in text
    assert response.headers["Content-Disposition"] == "attachment; filename=safehome_goals.csv"
    assert response.headers["Cache-Control"] == "no-store" and response.headers["X-Content-Type-Options"] == "nosniff"


def test_api_security_headers_do_not_reflect_unapproved_origin(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    response = app.test_client().get("/healthz", headers={"Origin": "https://attacker.invalid"})
    assert "Access-Control-Allow-Origin" not in response.headers
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["Referrer-Policy"] == "no-referrer"
    assert response.headers["Permissions-Policy"] == "camera=(), microphone=(), geolocation=()"


def test_real_privacy_execution_records_zero_count_verification(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    app.config.update(PRIVACY_EXECUTION_ENABLED=True, PRIVACY_RETENTION_POLICY_APPROVED=True)
    client = app.test_client()
    owner = _login(client, "task31-delete-owner")
    admin = _login(client, "task31-delete-admin")
    _set_role(app, admin["user"]["id"], "admin")
    client.post("/api/diaries", headers=_headers(owner["token"]), json={"scene": "沟通", "event_description": "合成删除记录", "parent_emotion": "担心"})
    created = client.post("/api/privacy/delete-my-data", headers=_headers(owner["token"]), json={"reason": "合成删除测试"})
    request_id = created.get_json()["data"]["id"]
    claimed = client.post(f"/api/privacy/admin/requests/{request_id}/transition", headers=_headers(admin["token"], "claim-task31"), json={"action": "start_processing", "scope": ["participant_records"], "note": "合成核验"})
    version = claimed.get_json()["data"]["request"]["version"]
    executed = client.post(f"/api/privacy/admin/requests/{request_id}/execute", headers=_headers(admin["token"], "execute-task31"), json={"dry_run": False, "expected_version": version})
    assert executed.status_code == 200
    assert executed.get_json()["data"]["result"]["verification_status"] == "verified"
    proof = client.get(f"/api/privacy/admin/requests/{request_id}/verification", headers=_headers(admin["token"]))
    assert proof.status_code == 200
    proof_data = proof.get_json()["data"]
    assert proof_data["status"] == "verified" and proof_data["verification"]["all_queries_zero_or_anonymized"] is True
    assert "subject_hash" not in proof_data
