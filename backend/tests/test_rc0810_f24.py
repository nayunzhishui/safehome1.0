import hashlib
import importlib
import json
import os
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = PROJECT_ROOT / "backend"


def _fresh_app(tmp_path):
    sys.path.insert(0, str(BACKEND_ROOT))
    for name in list(sys.modules):
        if name in {"app", "config", "database", "models"} or name.startswith("routes.") or name.startswith("services."):
            sys.modules.pop(name, None)
    os.environ["APP_ENV"] = "testing"
    os.environ["DATABASE_PATH"] = str(tmp_path / "f24.sqlite3")
    os.environ["CONTENT_DIR"] = str(PROJECT_ROOT / "content")
    os.environ.pop("REDIS_URL", None)
    os.environ.pop("REDIS_ENABLED", None)
    return importlib.import_module("app").app


def _seed_claimable_account(client, anonymous_id="web_user_1760000000000_a1b2c3"):
    database = importlib.import_module("database")
    timestamp = database.now_iso()
    with database.get_connection() as conn:
        database.ensure_user(conn, anonymous_id, "本机试用")
        conn.execute(
            """INSERT INTO goals
               (id, user_id, scene, smart_goal, motivation, start_date, status, created_at, updated_at)
               VALUES (?, ?, '沟通', '暂停三秒', NULL, NULL, 'active', ?, ?)""",
            (database.new_id("goal"), anonymous_id, timestamp, timestamp),
        )
        conn.commit()
    response = client.post(
        "/api/auth/register",
        json={"username": f"claim-{anonymous_id[-6:]}", "password": "password-123", "role": "parent", "anonymous_id": anonymous_id},
    )
    assert response.status_code == 201
    data = response.get_json()["data"]
    return data["user"]["id"], {"Authorization": f"Bearer {data['token']}"}


def test_therapeutic_case_machine_contract_closes_f23_schema_gap(tmp_path):
    _fresh_app(tmp_path)
    builder = importlib.import_module("scripts.build_api_contract")
    contract = builder.build_contract(importlib.import_module("app").app)
    endpoint = next(
        item for item in contract["endpoints"]
        if item["path"] == "/api/therapeutic-assessment/cases" and item["method"] == "POST"
    )
    assert set(endpoint["request"]["body_fields"]) == {
        "assessment_question", "complexity_scope", "consent", "enrollment_id", "shared_scope"
    }
    assert endpoint["request"]["idempotency"]["required"] is True
    assert endpoint["request"]["idempotency"]["header"] == "Idempotency-Key"


def test_redis_unavailable_policy_distinguishes_disabled_and_broken(monkeypatch):
    redis_service = importlib.import_module("services.redis_service")
    monkeypatch.setattr(redis_service, "get_client", lambda: None)
    monkeypatch.setattr(redis_service, "settings", lambda: {"enabled": False, "namespace": "safehome"})
    assert redis_service.rate_limit("login", limit=5, window_seconds=60, unavailable_policy="deny_if_enabled")["allowed"] is True
    monkeypatch.setattr(redis_service, "settings", lambda: {"enabled": True, "namespace": "safehome"})
    denied = redis_service.rate_limit("login", limit=5, window_seconds=60, unavailable_policy="deny_if_enabled")
    assert denied["available"] is False
    assert denied["allowed"] is False
    assert denied["reason"] == "redis_unavailable"


def test_auth_route_fails_closed_when_configured_redis_is_unavailable(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path)
    monkeypatch.setenv("REDIS_URL", "redis://configured-but-unavailable:6379/0")
    redis_service = importlib.import_module("services.redis_service")
    monkeypatch.setattr(redis_service, "get_client", lambda: None)
    importlib.import_module("services.runtime_bootstrap").configure_app(app)
    response = app.test_client().post(
        "/api/auth/login",
        json={"username": "nobody", "password": "password-123"},
    )
    assert response.status_code == 503
    assert response.get_json()["error"]["code"] == "rate_limit_unavailable"


def test_claim_token_is_high_entropy_digest_only_and_one_time(tmp_path):
    app = _fresh_app(tmp_path)
    client = app.test_client()
    user_id, headers = _seed_claimable_account(client)
    preview = client.get("/api/auth/data-claim-preview", headers=headers).get_json()["data"]
    token = preview["claim_id"]
    assert isinstance(token, str) and len(token) >= 40

    database = importlib.import_module("database")
    with database.get_connection() as conn:
        row = conn.execute("SELECT * FROM data_claims WHERE target_user_id = ?", (user_id,)).fetchone()
        assert token not in tuple(str(value) for value in row)
        assert row["claim_token_digest"] == hashlib.sha256(token.encode("utf-8")).hexdigest()
        assert row["claim_token_expires_at"]

    claim_headers = {**headers, "Idempotency-Key": "f24-claim-once"}
    payload = {"claim_id": token, "confirm": True, "expected_version": preview["version"]}
    first = client.post("/api/auth/data-claim", headers=claim_headers, json=payload)
    assert first.status_code == 200
    same_request = client.post("/api/auth/data-claim", headers=claim_headers, json=payload)
    assert same_request.status_code == 200
    assert same_request.get_json()["data"]["already_completed"] is True
    replay = client.post(
        "/api/auth/data-claim",
        headers={**headers, "Idempotency-Key": "f24-different-request"},
        json=payload,
    )
    assert replay.status_code == 409


def test_claim_guess_attempts_lock_the_actor_candidate(tmp_path):
    app = _fresh_app(tmp_path)
    client = app.test_client()
    _user_id, headers = _seed_claimable_account(client, "web_user_1760000000001_a1b2c4")
    preview = client.get("/api/auth/data-claim-preview", headers=headers).get_json()["data"]
    for attempt in range(5):
        response = client.post(
            "/api/auth/data-claim",
            headers={**headers, "Idempotency-Key": f"wrong-token-{attempt}"},
            json={"claim_id": f"wrong-token-{attempt}", "confirm": True},
        )
        assert response.status_code == 404
    valid = client.post(
        "/api/auth/data-claim",
        headers={**headers, "Idempotency-Key": "valid-after-lock"},
        json={"claim_id": preview["claim_id"], "confirm": True},
    )
    assert valid.status_code == 409
    assert valid.get_json()["error"]["code"] == "claim_unavailable"


def test_audit_chain_detects_row_modification(tmp_path):
    _fresh_app(tmp_path)
    database = importlib.import_module("database")
    with database.get_connection() as conn:
        legacy_id = database.new_id("audit")
        conn.execute(
            """INSERT INTO audit_logs
               (id, actor_id, action, target_type, target_id, metadata_json, created_at)
               VALUES (?, 'legacy', 'legacy_event', NULL, NULL, '{}', ?)""",
            (legacy_id, database.now_iso()),
        )
        migration_service = importlib.import_module("services.schema_migration_service")
        migration_service.MIGRATIONS[-1].apply(conn)
        assert database.verify_audit_chain(conn)["ok"] is True
        database.write_audit_log(conn, "f24_first", actor_id="reviewer", metadata={"value": 1})
        second_id = database.write_audit_log(conn, "f24_second", actor_id="reviewer", metadata={"value": 2})
        conn.commit()
        assert database.verify_audit_chain(conn)["ok"] is True
        conn.execute("UPDATE audit_logs SET metadata_json = '{\"value\":999}' WHERE id = ?", (second_id,))
        conn.commit()
        result = database.verify_audit_chain(conn)
        assert result["ok"] is False
        assert result["first_invalid_audit_id"] == second_id
    manifest = importlib.import_module("services.schema_migration_service").migration_manifest()
    assert [item["version"] for item in manifest[-2:]] == ["2026_08_26_077", "2026_08_26_078"]
    assert all(item["rollback_notes"] for item in manifest[-2:])


def test_home_summary_failures_are_not_converted_to_empty_data():
    source = (PROJECT_ROOT / "apps/miniprogram/pages/home/index.js").read_text(encoding="utf-8")
    template = (PROJECT_ROOT / "apps/miniprogram/pages/home/index.wxml").read_text(encoding="utf-8")
    assert "homeOverviewError" in source
    assert "homeOverviewError" in template
    assert "api.getProfileStats().catch(() => null)" not in source
    assert "api.getEmotionThermometerDay({ date: todayKey }).catch(() => null)" not in source
    assert 'action-label="重新加载"' in template


def test_config_inventory_and_legacy_compatibility_contract_are_current(tmp_path):
    result = subprocess.run(
        [sys.executable, "scripts/check_rc0810_f24_config.py"],
        cwd=PROJECT_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    inventory = json.loads((PROJECT_ROOT / "config/rc0810/config_read_inventory.json").read_text(encoding="utf-8"))
    assert inventory["unclassified_reads"] == []
    policy = json.loads((PROJECT_ROOT / "config/rc0810/f24_failure_policy.json").read_text(encoding="utf-8"))
    assert policy["routes"]["/api/auth/login"]["redis_unavailable"] == "fail_closed_503"
    contract = json.loads((PROJECT_ROOT / "shared/contracts/api-contract.json").read_text(encoding="utf-8"))
    assert any(item["path"] == "/api/auth/data-claim" and item["method"] == "POST" for item in contract["endpoints"])
