import importlib
import json
import shutil
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"


def _fresh_app(tmp_path, monkeypatch):
    content_dir = tmp_path / "content"
    shutil.copytree(ROOT / "content", content_dir)
    showcase = json.loads((content_dir / "showcase_access.json").read_text(encoding="utf-8"))
    showcase.update(
        {
            "researcher_platform_full_access": False,
            "read_only_role_bypass": False,
        }
    )
    (content_dir / "showcase_access.json").write_text(
        json.dumps(showcase, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    sys.path.insert(0, str(BACKEND))
    for name in list(sys.modules):
        if name in {"app", "config", "database", "models"} or name.startswith("routes.") or name.startswith("services."):
            sys.modules.pop(name, None)
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "task36-f03.sqlite3"))
    monkeypatch.setenv("CONTENT_DIR", str(content_dir))
    monkeypatch.setenv("DB_PROVIDER", "sqlite")
    monkeypatch.setenv("ALLOW_PRODUCTION_SQLITE", "1")
    monkeypatch.setenv("SECRET_KEY", "task36-f03-test-secret-key-that-is-long-enough")
    monkeypatch.setenv("ADMIN_EXPORT_TOKEN", "task36-f03-admin-token")
    return importlib.import_module("app").app


def _seed(app):
    with app.app_context():
        from database import get_connection, now_iso
        from routes.auth_utils import generate_auth_token

        timestamp = now_iso()
        actors = {
            "parent-a": "parent",
            "parent-b": "parent",
            "researcher-a": "researcher",
            "researcher-b": "researcher",
            "supervisor-a": "supervisor",
            "admin-a": "admin",
        }
        with get_connection() as conn:
            for actor_id, role in actors.items():
                conn.execute(
                    "INSERT INTO users (id, nickname, role, status, created_at, updated_at) VALUES (?, ?, ?, 'active', ?, ?)",
                    (actor_id, actor_id, role, timestamp, timestamp),
                )
            for suffix, user_id, status in [
                ("a", "parent-a", "enrolled"),
                ("b", "parent-b", "enrolled"),
                ("inactive", "parent-b", "withdrawn"),
            ]:
                conn.execute(
                    """
                    INSERT INTO relationship_pilot_enrollments (
                        id, user_id, assessment_result_id, worksheet_id, dimensions_json,
                        radar_features_json, profile_json, consent_scope, status,
                        review_status, created_at, updated_at
                    ) VALUES (?, ?, ?, 'regulatory_focus_relationship_18', '[]', '[]', '{}',
                              'relationship_pilot_stage2_v1', ?, 'pending_review', ?, ?)
                    """,
                    (f"enrollment-{suffix}", user_id, f"result-{suffix}", status, timestamp, timestamp),
                )
            conn.commit()
        return {
            actor_id: {"Authorization": f"Bearer {generate_auth_token({'id': actor_id, 'role': role})}"}
            for actor_id, role in actors.items()
        }


def _assign(client, headers, enrollment_id, actor_id, assignment_role="researcher", key="assignment-1"):
    return client.post(
        "/api/research/access/assignments",
        headers={**headers, "Idempotency-Key": key},
        json={
            "enrollment_id": enrollment_id,
            "actor_id": actor_id,
            "assignment_role": assignment_role,
        },
    )


def test_capability_registry_is_complete_and_keeps_dangerous_operations_admin_only():
    payload = json.loads((ROOT / "content" / "researcher_capability_registry.json").read_text(encoding="utf-8"))

    assert payload["version"] == "2026.07.task36-f13-v1"
    assert payload["default_decision"] == "deny"
    assert len(payload["capabilities"]) >= 12
    for capability in payload["capabilities"]:
        assert capability["id"]
        assert capability["operations"]
        assert capability["roles"]
        assert capability["object_scope"]
        assert capability["sensitivity"] in {"low", "medium", "high", "restricted"}
        assert isinstance(capability["audit_required"], bool)
        assert isinstance(capability["mobile_available"], bool)
    dangerous = {
        item["id"]: item
        for item in payload["capabilities"]
        if item["id"] in {
            "research.export",
            "research.account.manage",
            "research.security.manage",
            "research.production.manage",
        }
    }
    assert set(dangerous) == {
        "research.export",
        "research.account.manage",
        "research.security.manage",
        "research.production.manage",
    }
    assert all(item["roles"] == ["admin"] for item in dangerous.values())
    assert all(item["development_exception"] is False for item in dangerous.values())


def test_formal_participant_cannot_open_researcher_dashboard(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    headers = _seed(app)
    response = app.test_client().get(
        "/api/relationship-pilot/researcher/dashboard", headers=headers["parent-a"]
    )

    assert response.status_code == 403
    body = response.get_json()
    assert body["error"]["code"] == "forbidden"
    assert body["error"]["details"]["required_capability"] == "research.dashboard.read"
    assert body["request_id"]


def test_admin_assignment_enforces_researcher_and_supervisor_object_scope(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    headers = _seed(app)
    client = app.test_client()

    assert _assign(client, headers["admin-a"], "enrollment-a", "researcher-a").status_code == 201
    assert _assign(
        client,
        headers["admin-a"],
        "enrollment-a",
        "supervisor-a",
        assignment_role="supervisor",
        key="assignment-supervisor",
    ).status_code == 201

    assert client.get("/api/relationship-pilot/enrollments/enrollment-a", headers=headers["researcher-a"]).status_code == 200
    assert client.get("/api/relationship-pilot/enrollments/enrollment-a", headers=headers["researcher-b"]).status_code == 403
    assert client.get("/api/relationship-pilot/enrollments/enrollment-a", headers=headers["supervisor-a"]).status_code == 200
    assert client.get("/api/relationship-pilot/enrollments/enrollment-b", headers=headers["supervisor-a"]).status_code == 403
    assert client.get("/api/relationship-pilot/enrollments/enrollment-b", headers=headers["admin-a"]).status_code == 200


def test_claim_is_idempotent_and_rejects_inactive_or_cross_researcher_claim(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    headers = _seed(app)
    client = app.test_client()
    request_headers = {**headers["researcher-a"], "Idempotency-Key": "claim-a"}

    first = client.post("/api/research/access/enrollments/enrollment-a/claim", headers=request_headers)
    repeated = client.post("/api/research/access/enrollments/enrollment-a/claim", headers=request_headers)
    cross = client.post(
        "/api/research/access/enrollments/enrollment-a/claim",
        headers={**headers["researcher-b"], "Idempotency-Key": "claim-b"},
    )
    inactive = client.post(
        "/api/research/access/enrollments/enrollment-inactive/claim",
        headers={**headers["researcher-a"], "Idempotency-Key": "claim-inactive"},
    )

    assert first.status_code == 201
    assert repeated.status_code == 200
    assert repeated.get_json()["data"]["id"] == first.get_json()["data"]["id"]
    assert cross.status_code == 403
    assert inactive.status_code == 409


def test_assignment_revocation_and_version_conflict_are_enforced(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    headers = _seed(app)
    client = app.test_client()
    created = _assign(client, headers["admin-a"], "enrollment-a", "researcher-a").get_json()["data"]

    stale = client.patch(
        f"/api/research/access/assignments/{created['id']}",
        headers={**headers["admin-a"], "Idempotency-Key": "revoke-stale"},
        json={"status": "revoked", "expected_version": 99},
    )
    revoked = client.patch(
        f"/api/research/access/assignments/{created['id']}",
        headers={**headers["admin-a"], "Idempotency-Key": "revoke-ok"},
        json={"status": "revoked", "expected_version": created["version"]},
    )

    assert stale.status_code == 409
    assert revoked.status_code == 200
    assert client.get("/api/relationship-pilot/enrollments/enrollment-a", headers=headers["researcher-a"]).status_code == 403


def test_assignment_update_replays_same_result_and_rejects_changed_payload(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    headers = _seed(app)
    client = app.test_client()
    created = _assign(client, headers["admin-a"], "enrollment-a", "researcher-a").get_json()["data"]
    request_headers = {**headers["admin-a"], "Idempotency-Key": "transfer-replay"}
    payload = {
        "action": "transfer",
        "target_actor_id": "researcher-b",
        "expected_version": created["version"],
    }

    first = client.patch(
        f"/api/research/access/assignments/{created['id']}",
        headers=request_headers,
        json=payload,
    )
    replay = client.patch(
        f"/api/research/access/assignments/{created['id']}",
        headers=request_headers,
        json=payload,
    )
    conflict = client.patch(
        f"/api/research/access/assignments/{created['id']}",
        headers=request_headers,
        json={"status": "revoked", "expected_version": created["version"]},
    )

    assert first.status_code == 200
    assert replay.status_code == 200
    assert replay.get_json()["data"] == first.get_json()["data"]
    assert conflict.status_code == 409
    assert conflict.get_json()["error"]["code"] == "idempotency_conflict"


def test_assignment_transfer_is_atomic_and_revokes_old_scope(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    headers = _seed(app)
    client = app.test_client()
    created = _assign(client, headers["admin-a"], "enrollment-a", "researcher-a").get_json()["data"]

    transferred = client.patch(
        f"/api/research/access/assignments/{created['id']}",
        headers={**headers["admin-a"], "Idempotency-Key": "transfer-a-to-b"},
        json={
            "action": "transfer",
            "target_actor_id": "researcher-b",
            "expected_version": created["version"],
        },
    )

    assert transferred.status_code == 200
    assert transferred.get_json()["data"]["active_assignment"]["actor_id"] == "researcher-b"
    assert client.get("/api/relationship-pilot/enrollments/enrollment-a", headers=headers["researcher-a"]).status_code == 403
    assert client.get("/api/relationship-pilot/enrollments/enrollment-a", headers=headers["researcher-b"]).status_code == 200


def test_schema_contains_recoverable_assignment_table(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    with app.app_context():
        from database import CURRENT_SCHEMA_NAME, CURRENT_SCHEMA_VERSION, get_connection

        with get_connection() as conn:
            columns = {
                row["name"] for row in conn.execute("PRAGMA table_info(research_scope_assignments)").fetchall()
            }
            indexes = {
                row["name"] for row in conn.execute("PRAGMA index_list(research_scope_assignments)").fetchall()
            }
            action_columns = {
                row["name"]
                for row in conn.execute("PRAGMA table_info(research_scope_assignment_actions)").fetchall()
            }
            action_indexes = {
                row["name"]
                for row in conn.execute("PRAGMA index_list(research_scope_assignment_actions)").fetchall()
            }
        assert CURRENT_SCHEMA_VERSION == "2026_07_27_032"
        assert CURRENT_SCHEMA_NAME == "therapeutic_assessment_evidence_ledger"
        assert {"enrollment_id", "actor_id", "assignment_role", "status", "version", "idempotency_key"} <= columns
        assert "idx_research_scope_actor_status" in indexes
        assert "idx_research_scope_enrollment_status" in indexes
        assert {"assignment_id", "actor_id", "idempotency_key", "request_hash", "result_json"} <= action_columns
        assert "idx_research_scope_action_actor_idempotency" in action_indexes


def test_capability_endpoint_reports_formal_scope_and_development_exception(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    headers = _seed(app)
    response = app.test_client().get("/api/research/access/capabilities", headers=headers["researcher-a"])

    assert response.status_code == 200
    data = response.get_json()["data"]
    assert data["registry_version"] == "2026.07.task36-f13-v1"
    assert data["formal_role"] == "researcher"
    assert data["development_exception_active"] is False
    assert "research.dashboard.read" in data["capability_ids"]


def test_claimable_queue_never_exposes_profile_or_task_summary_before_claim(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    headers = _seed(app)
    client = app.test_client()

    enrollments = client.get("/api/relationship-pilot/enrollments", headers=headers["researcher-a"])
    dashboard = client.get("/api/relationship-pilot/researcher/dashboard", headers=headers["researcher-a"])

    assert enrollments.status_code == 200
    claimable = next(item for item in enrollments.get_json()["data"]["items"] if item["id"] == "enrollment-a")
    assert claimable["scope_status"] == "claimable"
    assert claimable["profile"] == {}
    assert claimable["dimensions"] == []
    assert "tasks_count" not in claimable
    dashboard_item = next(item for item in dashboard.get_json()["data"]["items"] if item["id"] == "enrollment-a")
    assert dashboard_item["scope_status"] == "claimable"
    assert dashboard_item["profile"] == {}
    assert "report_id" not in dashboard_item


def test_researcher_unknown_user_growth_is_forbidden_without_object_leak(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    headers = _seed(app)
    response = app.test_client().get(
        "/api/relationship-pilot/growth?user_id=not-a-visible-participant",
        headers=headers["researcher-a"],
    )

    assert response.status_code == 403
    body = response.get_json()
    assert body["error"]["code"] == "forbidden"
    assert body["error"]["details"]["required_capability"] == "research.report.read"
    assert "not-a-visible-participant" not in json.dumps(body, ensure_ascii=False)


def test_backfill_is_recoverable_and_preserves_legacy_assignment(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    _seed(app)
    with app.app_context():
        from database import get_connection

        module_path = BACKEND / "scripts" / "migrate_task36_research_access.py"
        spec = importlib.util.spec_from_file_location("task36_f03_migration", module_path)
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(module)
        with get_connection() as conn:
            conn.execute(
                "UPDATE relationship_pilot_enrollments SET assigned_researcher_id = 'researcher-a' WHERE id = 'enrollment-a'"
            )
            conn.commit()
            assert module.build_plan(conn)["pending_backfill_count"] == 1
            assert module.apply_backfill(conn)["created_count"] == 1
            assert module.verify(conn)["ok"] is True
            assert module.rollback_backfill(conn)["revoked_count"] == 1
            legacy = conn.execute(
                "SELECT assigned_researcher_id FROM relationship_pilot_enrollments WHERE id = 'enrollment-a'"
            ).fetchone()
            assert legacy["assigned_researcher_id"] == "researcher-a"
