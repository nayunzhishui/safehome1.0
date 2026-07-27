import importlib
import json
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
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "safehome-test.sqlite3"))
    monkeypatch.setenv("CONTENT_DIR", str(PROJECT_ROOT / "content"))
    monkeypatch.delenv("PRIVACY_EXECUTION_ENABLED", raising=False)
    monkeypatch.delenv("PRIVACY_RETENTION_POLICY_APPROVED", raising=False)
    return importlib.import_module("app").app


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
        from database import get_connection

        with get_connection() as conn:
            conn.execute("UPDATE users SET role = ? WHERE id = ?", (role, user_id))
            conn.commit()


def _claim(client, owner, reviewer, scopes):
    created = client.post("/api/privacy/delete-my-data", headers=_headers(owner["token"]), json={"reason": "停止使用"})
    request_id = created.get_json()["data"]["id"]
    claimed = client.post(
        f"/api/privacy/admin/requests/{request_id}/transition",
        headers=_headers(reviewer["token"], f"claim-{request_id}"),
        json={"action": "start_processing", "scope": scopes, "note": "核对保存范围"},
    )
    assert claimed.status_code == 200
    return request_id, claimed.get_json()["data"]["request"]["version"]


def test_preview_and_dry_run_are_whitelisted_audited_and_non_mutating(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    owner = _login(client, "privacy-preview-owner")
    supervisor = _login(client, "privacy-preview-supervisor")
    _set_role(app, supervisor["user"]["id"], "supervisor")
    client.post(
        "/api/diaries",
        headers=_headers(owner["token"]),
        json={"scene": "沟通", "event_description": "只用于本测试", "parent_emotion": "担心"},
    )
    request_id, version = _claim(client, owner, supervisor, ["participant_records"])

    preview = client.get(f"/api/privacy/admin/requests/{request_id}/preview", headers=_headers(supervisor["token"]))
    disabled = client.post(
        f"/api/privacy/admin/requests/{request_id}/execute",
        headers=_headers(supervisor["token"], "execute-disabled"),
        json={"dry_run": False, "expected_version": version},
    )
    dry_run = client.post(
        f"/api/privacy/admin/requests/{request_id}/execute",
        headers=_headers(supervisor["token"], "execute-dry-run"),
        json={"dry_run": True, "expected_version": version},
    )

    assert preview.status_code == 200
    preview_data = preview.get_json()["data"]
    assert preview_data["total_affected"] >= 1
    assert preview_data["scope_hash"] and preview_data["retained_categories"]
    assert {item["surface"] for item in preview_data["external_surfaces"]} == {
        "application_cache", "search_index", "offline_exports", "backups"
    }
    assert disabled.status_code == 503
    assert disabled.get_json()["error"]["code"] == "execution_disabled"
    assert dry_run.status_code == 200
    assert dry_run.get_json()["data"]["result"]["would_affect"] >= 1
    with app.app_context():
        from database import get_connection

        with get_connection() as conn:
            assert conn.execute("SELECT COUNT(*) AS count FROM emotion_diaries WHERE user_id = ?", (owner["user"]["id"],)).fetchone()["count"] == 1
            assert conn.execute("SELECT COUNT(*) AS count FROM privacy_request_executions WHERE mode = 'dry_run'").fetchone()["count"] == 1


def test_enabled_execution_deletes_selected_data_and_keeps_minimal_proof(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    app.config.update(PRIVACY_EXECUTION_ENABLED=True, PRIVACY_RETENTION_POLICY_APPROVED=True)
    client = app.test_client()
    owner = _login(client, "privacy-execute-owner")
    admin = _login(client, "privacy-execute-admin")
    _set_role(app, admin["user"]["id"], "admin")
    client.post(
        "/api/diaries",
        headers=_headers(owner["token"]),
        json={"scene": "沟通", "event_description": "DELETE_ME_RAW", "parent_emotion": "担心"},
    )
    request_id, version = _claim(client, owner, admin, ["account_identity", "participant_records"])

    response = client.post(
        f"/api/privacy/admin/requests/{request_id}/execute",
        headers=_headers(admin["token"], "execute-real-local"),
        json={"dry_run": False, "expected_version": version},
    )
    replay = client.post(
        f"/api/privacy/admin/requests/{request_id}/execute",
        headers=_headers(admin["token"], "execute-real-local"),
        json={"dry_run": False, "expected_version": version},
    )

    assert response.status_code == 200
    data = response.get_json()["data"]
    assert data["result"]["deleted"]["emotion_diaries"] == 1
    assert data["execution"]["proof_hash"]
    assert replay.status_code == 200
    assert replay.get_json()["data"]["already_processed"] is True
    with app.app_context():
        from database import get_connection

        with get_connection() as conn:
            assert conn.execute("SELECT COUNT(*) AS count FROM emotion_diaries WHERE user_id = ?", (owner["user"]["id"],)).fetchone()["count"] == 0
            user = conn.execute("SELECT * FROM users WHERE id = ?", (owner["user"]["id"],)).fetchone()
            assert user["status"] == "deleted" and user["wechat_openid"] is None
            request_row = conn.execute("SELECT * FROM privacy_requests WHERE id = ?", (request_id,)).fetchone()
            assert request_row["status"] == "completed" and request_row["reason"] is None
            assert conn.execute("SELECT COUNT(*) AS count FROM privacy_deletion_tombstones WHERE request_id = ?", (request_id,)).fetchone()["count"] == 1
            retained = str([dict(row) for row in conn.execute("SELECT * FROM audit_logs").fetchall()])
            assert "DELETE_ME_RAW" not in retained
        sys.path.insert(0, str(BACKEND_ROOT / "scripts"))
        verifier = importlib.import_module("verify_privacy_restore")
        from config import Config

        verified = verifier.verify(Path(Config.DATABASE_PATH), str(app.config["PRIVACY_TOMBSTONE_SECRET"]).encode())
        assert verified["ok"] is True and verified["raw_identifiers_included"] is False


def test_rejection_notice_and_participant_appeal_do_not_expose_internal_note(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    owner = _login(client, "privacy-appeal-owner")
    supervisor = _login(client, "privacy-appeal-supervisor")
    _set_role(app, supervisor["user"]["id"], "supervisor")
    request_id, _ = _claim(client, owner, supervisor, ["participant_records"])
    rejected = client.post(
        f"/api/privacy/admin/requests/{request_id}/transition",
        headers=_headers(supervisor["token"], "reject-with-private-note"),
        json={"action": "reject", "scope": [], "note": "INTERNAL_PRIVATE_REASON"},
    )
    listed = client.get("/api/privacy/requests", headers=_headers(owner["token"]))
    appealed = client.post(
        f"/api/privacy/requests/{request_id}/appeal",
        headers=_headers(owner["token"], "appeal-once"),
        json={"reason": "我希望补充范围后继续"},
    )

    assert rejected.status_code == 200
    item = listed.get_json()["data"]["items"][0]
    assert item["participant_notice"] and "INTERNAL_PRIVATE_REASON" not in str(item)
    assert appealed.status_code == 200
    assert appealed.get_json()["data"]["status"] == "pending"


def test_execution_exception_rolls_back_all_selected_rows_and_execution_evidence(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    app.config.update(PRIVACY_EXECUTION_ENABLED=True, PRIVACY_RETENTION_POLICY_APPROVED=True, TESTING=False)
    client = app.test_client()
    owner = _login(client, "privacy-rollback-owner")
    admin = _login(client, "privacy-rollback-admin")
    _set_role(app, admin["user"]["id"], "admin")
    client.post(
        "/api/diaries",
        headers=_headers(owner["token"]),
        json={"scene": "沟通", "event_description": "ROLLBACK_ME", "parent_emotion": "担心"},
    )
    request_id, version = _claim(client, owner, admin, ["participant_records"])
    with app.app_context():
        service = importlib.import_module("services.privacy_request_service")
        original = service._delete_table_rows

        def fail_after_first(conn, table, user_id):
            count = original(conn, table, user_id)
            if table == "emotion_diaries":
                raise RuntimeError("synthetic execution interruption")
            return count

        monkeypatch.setattr(service, "_delete_table_rows", fail_after_first)
        response = client.post(
            f"/api/privacy/admin/requests/{request_id}/execute",
            headers=_headers(admin["token"], "execute-interrupted"),
            json={"dry_run": False, "expected_version": version},
        )
    assert response.status_code == 500
    with app.app_context():
        from database import get_connection

        with get_connection() as conn:
            assert conn.execute("SELECT COUNT(*) AS count FROM emotion_diaries WHERE user_id = ?", (owner["user"]["id"],)).fetchone()["count"] == 1
            assert conn.execute("SELECT status FROM privacy_requests WHERE id = ?", (request_id,)).fetchone()["status"] == "processing"
            assert conn.execute("SELECT COUNT(*) AS count FROM privacy_request_executions WHERE request_id = ?", (request_id,)).fetchone()["count"] == 0


def test_production_execution_requires_two_distinct_approvals_including_admin(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    approved_content = tmp_path / "approved-content"
    approved_content.mkdir()
    policy = json.loads((PROJECT_ROOT / "content" / "privacy_retention_policy.json").read_text(encoding="utf-8"))
    policy["approval_status"] = "approved"
    (approved_content / "privacy_retention_policy.json").write_text(json.dumps(policy, ensure_ascii=False), encoding="utf-8")
    app.config.update(
        APP_ENV="production",
        CONTENT_DIR=approved_content,
        PRIVACY_EXECUTION_ENABLED=True,
        PRIVACY_RETENTION_POLICY_APPROVED=True,
        PRIVACY_PRODUCTION_EXECUTION_ENABLED=True,
    )
    client = app.test_client()
    owner = _login(client, "privacy-prod-owner")
    supervisor = _login(client, "privacy-prod-supervisor")
    admin = _login(client, "privacy-prod-admin")
    _set_role(app, supervisor["user"]["id"], "supervisor")
    _set_role(app, admin["user"]["id"], "admin")
    request_id, version = _claim(client, owner, supervisor, ["participant_records"])
    preview = client.get(f"/api/privacy/admin/requests/{request_id}/preview", headers=_headers(supervisor["token"])).get_json()["data"]
    one = client.post(
        f"/api/privacy/admin/requests/{request_id}/approvals",
        headers=_headers(supervisor["token"], "approval-one"),
        json={"scope_hash": preview["scope_hash"], "policy_version": preview["policy_version"]},
    )
    blocked = client.post(
        f"/api/privacy/admin/requests/{request_id}/execute",
        headers=_headers(supervisor["token"], "prod-execute-before-two"),
        json={"dry_run": False, "expected_version": version},
    )
    two = client.post(
        f"/api/privacy/admin/requests/{request_id}/approvals",
        headers=_headers(admin["token"], "approval-two"),
        json={"scope_hash": preview["scope_hash"], "policy_version": preview["policy_version"]},
    )

    assert one.status_code == 201 and two.status_code == 201
    assert blocked.status_code == 409
    assert blocked.get_json()["error"]["code"] == "dual_approval_required"


def test_schema_contains_execution_and_recovery_evidence_tables(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    with app.app_context():
        from database import CURRENT_SCHEMA_VERSION, check_database_health, get_connection

        assert CURRENT_SCHEMA_VERSION == "2026_07_27_030"
        assert check_database_health()["ok"] is True
        with get_connection() as conn:
            columns = {row["name"] for row in conn.execute("PRAGMA table_info(privacy_requests)").fetchall()}
            assert {"participant_notice", "policy_version", "execution_proof_hash"} <= columns
            tables = {row["name"] for row in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'").fetchall()}
            assert {"privacy_request_approvals", "privacy_request_executions", "privacy_deletion_tombstones"} <= tables


def test_research_withdrawal_blocks_matrix_exports_and_offline_text_but_keeps_support_data(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    owner = _login(client, "privacy-research-withdraw-owner")
    diary = client.post(
        "/api/diaries",
        headers=_headers(owner["token"]),
        json={"scene": "沟通", "event_description": "WITHDRAWN_RESEARCH_TEXT", "parent_emotion": "担心"},
    )
    assert diary.status_code == 201
    support = client.post(
        "/api/supervision",
        headers=_headers(owner["token"]),
        json={"message": "仍需要服务支持", "source_type": "diary", "source_id": diary.get_json()["data"]["id"]},
    )
    assert support.status_code == 201
    revoke = client.post(
        "/api/privacy/revoke-consent",
        headers=_headers(owner["token"]),
        json={"consent_type": "research_authorization"},
    )
    assert revoke.status_code == 200
    matrix = client.get(f"/api/research/participants?q={owner['user']['id']}", headers={"X-Admin-Token": "safehome-local-admin-token"})
    assert matrix.status_code == 200 and matrix.get_json()["data"]["count"] == 0

    with app.app_context():
        from config import Config
        from database import get_connection

        with get_connection() as conn:
            assert conn.execute("SELECT COUNT(*) AS count FROM supervision_requests WHERE user_id = ?", (owner["user"]["id"],)).fetchone()["count"] == 1
        sys.path.insert(0, str(PROJECT_ROOT / "analysis" / "text_analysis"))
        module = importlib.import_module("analyze_text_sources")
        with module.open_readonly_sqlite(Path(Config.DATABASE_PATH)) as conn:
            records = list(module._iter_text_records(conn, owner["user"]["id"], None))
        assert all("WITHDRAWN_RESEARCH_TEXT" not in item["text"] for item in records)
