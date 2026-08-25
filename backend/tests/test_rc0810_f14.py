import json
import importlib
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
VERIFIER = ROOT / "scripts" / "verify_rc0810_f14_lineage.py"
CATALOG = ROOT / "config" / "rc0810" / "privacy_lineage_catalog.json"
REGISTRY = ROOT / "content" / "rc0810_release_candidate_registry.json"


def run_verifier(*args: str):
    return subprocess.run(
        [sys.executable, str(VERIFIER), *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def test_f14b_default_definition_is_fail_closed():
    completed = run_verifier()
    assert completed.returncode == 0, completed.stderr
    payload = json.loads(completed.stdout)
    assert payload["valid"] is True
    assert payload["status"] == "phase_b_ready"
    assert payload["privacy_owner_status"] == "pending_external"
    assert payload["release_gate_eligible"] is False


def test_f14a_catalog_covers_every_discovered_table():
    completed = run_verifier()
    assert completed.returncode == 0, completed.stderr
    payload = json.loads(completed.stdout)
    assert payload["asset_count"] >= 160
    assert payload["asset_count"] == payload["scanned_table_count"]
    assert payload["unregistered_tables"] == []
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    tables = {item["table_name"] for item in catalog["assets"]}
    assert {
        "explicit_schema_migrations",
        "participant_minor_safeguards",
        "supervision_request_events",
        "agent_runs",
        "agent_tool_calls",
    } <= tables
    assets = {item["table_name"]: item for item in catalog["assets"]}
    required = {
        "content_release_artifacts",
        "content_active_artifacts",
        "research_source_objects",
        "research_execution_manifests",
        "ai_capability_decisions",
    }
    assert required <= set(assets)
    assert all(assets[name]["access_paths"] for name in required)
    assert "actor_id" in assets["ai_capability_decisions"]["actor_keys"]
    assert payload["phase_b_required_assets_current"] is True


def test_f14a_each_asset_has_subject_actor_derivation_and_lifecycle_metadata():
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    required = {
        "asset_id",
        "table_name",
        "schema_sources",
        "columns_sha256",
        "subject_keys",
        "actor_keys",
        "relationship_keys",
        "access_paths",
        "collection_purpose",
        "retention_policy",
        "export_policy",
        "deletion_policy",
        "anonymization_policy",
        "tombstone_policy",
        "external_processor_ids",
        "review_status",
    }
    assert catalog["assets"]
    for asset in catalog["assets"]:
        assert required == set(asset)
        assert asset["asset_id"] == f"table:{asset['table_name']}"
        assert asset["review_status"] == "pending_external"


def test_f14a_rejects_tampered_asset_metadata(tmp_path):
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    catalog["assets"][0]["columns_sha256"] = "0" * 64
    candidate = tmp_path / "tampered-catalog.json"
    candidate.write_text(json.dumps(catalog), encoding="utf-8")
    completed = run_verifier("--catalog", str(candidate))
    assert completed.returncode != 0
    assert "asset_catalog_mismatch" in completed.stdout

    catalog["assets"].append(dict(catalog["assets"][0]))
    duplicate = tmp_path / "duplicate-assets.json"
    duplicate.write_text(json.dumps(catalog), encoding="utf-8")
    duplicate_result = run_verifier("--catalog", str(duplicate))
    assert duplicate_result.returncode != 0
    duplicate_payload = json.loads(duplicate_result.stdout)
    assert duplicate_payload["duplicate_asset_ids"] == [catalog["assets"][0]["asset_id"]]
    assert "duplicate_asset_ids" in duplicate_payload["errors"]


def test_f14a_catalog_binds_models_migrations_routes_and_services():
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    assert set(catalog["source_bindings"]) == {
        "models_sha256",
        "migration_manifest_sha256",
        "route_manifest_sha256",
        "service_manifest_sha256",
    }
    assert all(len(value) == 64 for value in catalog["source_bindings"].values())
    completed = run_verifier()
    assert completed.returncode == 0, completed.stderr
    assert json.loads(completed.stdout)["source_bindings_current"] is True


def test_f14a_external_processors_are_inventoried_without_approval():
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    processors = {item["processor_id"]: item for item in catalog["external_processors"]}
    assert {
        "endpoint:https://api.weixin.qq.com/sns/jscode2session",
        "endpoint:https://api.weixin.qq.com/cgi-bin/token",
        "endpoint:https://api.weixin.qq.com/wxa/business/getuserphonenumber",
        "endpoint:https://api.weixin.qq.com/cgi-bin/message/subscribe/send",
        "endpoint:https://api.openai.com/v1/chat/completions",
        "endpoint:https://api.deepseek.com/chat/completions",
        "dynamic:backend/services/embedding_service.py",
    } <= set(processors)
    required = {
        "processor_id",
        "endpoint_kind",
        "endpoint",
        "source_files",
        "fields",
        "purpose",
        "necessity",
        "sensitivity",
        "retention",
        "processor_role",
        "export_capability",
        "deletion_capability",
        "privacy_notice_status",
        "review_status",
    }
    assert all(set(item) == required for item in processors.values())
    assert all(item["review_status"] == "pending_external" for item in processors.values())
    completed = run_verifier()
    assert completed.returncode == 0, completed.stderr
    assert json.loads(completed.stdout)["processor_catalog_matches"] is True
    evidence = catalog["phase_b_evidence"]
    assert evidence["dependency_units"] == ["RC0810-F17", "RC0810-F18", "RC0810-F19"]
    assert evidence["participant_rights"] == {
        "export_mode": "synthetic_subject_dry_run",
        "deletion_mode": "preview_then_execute",
        "audit_actor_handling": "pseudonymize_minimal_ledger",
        "service": "backend/services/privacy_request_service.py",
    }
    assert evidence["isolated_restore"] == {
        "target_environment": "isolated_validation",
        "production_restore_forbidden": True,
        "tombstone_reconciliation": "required",
        "verifier": "backend/scripts/verify_privacy_restore.py",
    }
    external = evidence["external_data_flow"]
    assert external["status"] == "pending_external"
    assert external["automatic_approval_allowed"] is False
    assert set(external["required_evidence"]) == {
        "data_region",
        "cross_border_path",
        "provider_training_commitment",
        "provider_retention_commitment",
        "provider_deletion_commitment",
        "subprocessor_inventory",
        "wechat_privacy_notice_mapping",
    }


def test_f14a_new_table_without_registry_entry_fails_closed(tmp_path):
    models = tmp_path / "models.py"
    models.write_text(
        "SCHEMA_SQL = ['''CREATE TABLE IF NOT EXISTS rc0810_unregistered_probe "
        "(id TEXT PRIMARY KEY, participant_user_id TEXT)''']\n",
        encoding="utf-8",
    )
    completed = run_verifier("--models", str(models))
    assert completed.returncode != 0
    payload = json.loads(completed.stdout)
    assert "rc0810_unregistered_probe" in payload["unregistered_tables"]


def test_f14a_catalog_rejects_embedded_secret_values(tmp_path):
    current = run_verifier()
    assert current.returncode == 0, current.stderr
    assert json.loads(current.stdout)["sensitive_value_scan_passed"] is True

    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    catalog["external_processors"][0]["endpoint"] += "?secret=do-not-store-this"
    candidate = tmp_path / "secret-catalog.json"
    candidate.write_text(json.dumps(catalog), encoding="utf-8")
    completed = run_verifier("--catalog", str(candidate))
    assert completed.returncode != 0
    payload = json.loads(completed.stdout)
    assert payload["sensitive_value_scan_passed"] is False
    assert "sensitive_value_detected" in payload["errors"]


def test_f14a_reports_every_unconfirmed_privacy_decision_as_a_gap():
    completed = run_verifier()
    assert completed.returncode == 0, completed.stderr
    payload = json.loads(completed.stdout)
    assert payload["pending_asset_reviews"] == payload["asset_count"]
    assert payload["pending_processor_reviews"] == payload["processor_count"]
    assert payload["confirmed_privacy_reviews"] == 0
    assert payload["privacy_gap_count"] == (
        payload["pending_asset_reviews"] + payload["pending_processor_reviews"] + 1
    )
    assert payload["release_gate_eligible"] is False


def test_f14a_self_check_proves_fail_closed_mutations_are_rejected():
    completed = run_verifier("--self-check")
    assert completed.returncode == 0, completed.stderr
    payload = json.loads(completed.stdout)
    assert payload["status"] == "self_check_passed"
    assert payload["self_checks"] == {
        "embedded_secret_rejected": True,
        "processor_removal_rejected": True,
        "tampered_asset_rejected": True,
        "unregistered_table_rejected": True,
    }


def test_f14a_registry_freezes_exact_scope_without_migration_or_business_changes():
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    unit = next(item for item in registry["execution_units"] if item["id"] == "RC0810-F14-A")
    task = next(item for item in registry["tasks"] if item["id"] == "RC0810-F14")
    assert unit["subtasks"] == [f"F14.{index}" for index in range(1, 11)]
    assert unit["change_budget"] == {
        "expected_files": 12,
        "pause_when_actual_exceeds_percent": 50,
    }
    assert "backend/migrations/**" not in unit["allowed_files"]
    assert all(not path.startswith("apps/") for path in unit["allowed_files"])
    assert [item["expected_test_count"] for item in task["acceptance_commands"]] == [
        12,
        19,
        1,
        1,
        1,
    ]
    assert task["external_gates"] == [
        {
            "owner": "privacy_owner",
            "status": "pending_external",
            "automation_may_approve": False,
        }
    ]


def _fresh_f14b_app(tmp_path, monkeypatch):
    if str(ROOT / "backend") not in sys.path:
        sys.path.insert(0, str(ROOT / "backend"))
    for name in list(sys.modules):
        if name in {"app", "config", "database", "models"} or name.startswith(
            ("routes.", "services.")
        ):
            sys.modules.pop(name, None)
    monkeypatch.setenv("APP_ENV", "testing")
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "f14b.sqlite3"))
    monkeypatch.setenv("CONTENT_DIR", str(ROOT / "content"))
    app = importlib.import_module("app").app
    app.config.update(
        PRIVACY_EXECUTION_ENABLED=True,
        PRIVACY_RETENTION_POLICY_APPROVED=True,
    )
    return app


def _login(client, code):
    response = client.post("/api/auth/wechat-login", json={"code": code, "nickname": code})
    assert response.status_code == 200
    return response.get_json()["data"]


def _headers(token, key=None):
    result = {"Authorization": f"Bearer {token}"}
    if key:
        result["Idempotency-Key"] = key
    return result


def test_f14b_ai_decision_dry_run_then_execution_pseudonymizes_actor(
    tmp_path, monkeypatch
):
    app = _fresh_f14b_app(tmp_path, monkeypatch)
    client = app.test_client()
    owner = _login(client, "f14b-owner")
    admin = _login(client, "f14b-admin")
    owner_id = owner["user"]["id"]
    admin_id = admin["user"]["id"]
    with app.app_context():
        database = importlib.import_module("database")
        with database.get_connection() as conn:
            conn.execute("UPDATE users SET role = 'admin' WHERE id = ?", (admin_id,))
            conn.execute(
                """INSERT INTO ai_capability_decisions
                   (id, actor_id, actor_role, operation, environment, audience,
                    enabled, provider, real_provider_allowed, reason_code,
                    policy_version, data_mode, created_at)
                   VALUES ('f14b-capability', ?, 'parent', 'route_session_access',
                           'testing', 'participant', 0, 'fake', 0,
                           'participant_ai_not_available_in_environment',
                           '2026.08-rc0810-f19-v1', 'none', ?)""",
                (owner_id, database.now_iso()),
            )
            conn.commit()

    exported = client.get("/api/privacy/export-my-data", headers=_headers(owner["token"]))
    assert exported.status_code == 200
    assert exported.get_json()["data"]["counts"]["ai_capability_decisions"] == 1

    created = client.post(
        "/api/privacy/delete-my-data",
        headers=_headers(owner["token"]),
        json={"reason": "停止使用"},
    )
    request_id = created.get_json()["data"]["id"]
    claimed = client.post(
        f"/api/privacy/admin/requests/{request_id}/transition",
        headers=_headers(admin["token"], "f14b-claim"),
        json={"action": "start_processing", "scope": ["account_identity"], "note": "核对"},
    )
    version = claimed.get_json()["data"]["request"]["version"]
    dry_run = client.post(
        f"/api/privacy/admin/requests/{request_id}/execute",
        headers=_headers(admin["token"], "f14b-dry-run"),
        json={"dry_run": True, "expected_version": version},
    )
    assert dry_run.status_code == 200
    with app.app_context():
        database = importlib.import_module("database")
        with database.get_connection() as conn:
            assert conn.execute(
                "SELECT actor_id FROM ai_capability_decisions WHERE id = 'f14b-capability'"
            ).fetchone()["actor_id"] == owner_id

    executed = client.post(
        f"/api/privacy/admin/requests/{request_id}/execute",
        headers=_headers(admin["token"], "f14b-execute"),
        json={"dry_run": False, "expected_version": version},
    )
    assert executed.status_code == 200
    replacement = executed.get_json()["data"]["result"]["replacement_user_id"]
    with app.app_context():
        database = importlib.import_module("database")
        with database.get_connection() as conn:
            actor_id = conn.execute(
                "SELECT actor_id FROM ai_capability_decisions WHERE id = 'f14b-capability'"
            ).fetchone()["actor_id"]
    assert actor_id == replacement
    assert actor_id != owner_id
