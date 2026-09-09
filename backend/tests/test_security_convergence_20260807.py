import importlib
import json
import sys
from pathlib import Path

from werkzeug.security import generate_password_hash


ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"


def _fresh_app(tmp_path, monkeypatch, env="testing"):
    sys.path.insert(0, str(BACKEND))
    for name in list(sys.modules):
        if name in {"app", "config", "database", "models"} or name.startswith("routes.") or name.startswith("services."):
            sys.modules.pop(name, None)
    monkeypatch.setenv("APP_ENV", env)
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "security-convergence.sqlite3"))
    monkeypatch.setenv("CONTENT_DIR", str(ROOT / "content"))
    monkeypatch.setenv("DB_PROVIDER", "sqlite")
    monkeypatch.setenv("SECRET_KEY", "security-convergence-secret-key-long-enough")
    monkeypatch.setenv("ADMIN_EXPORT_TOKEN", "legacy-admin-token")
    monkeypatch.setenv("LEGACY_ADMIN_TOKEN_ENABLED", "0")
    app = importlib.import_module("app").app
    safeguard_service = importlib.import_module("services.participant_safeguard_service")
    monkeypatch.setattr(safeguard_service.Config, "MINOR_SAFEGUARDS_ENFORCED", True, raising=False)
    return app


def _register(client, username, role):
    response = client.post(
        "/api/auth/register",
        json={"username": username, "password": "StrongPass123!", "role": role, "nickname": username},
    )
    assert response.status_code == 201, response.get_json()
    return response.get_json()["data"]


def _headers(token):
    return {"Authorization": f"Bearer {token}"}


def _promote(app, user_id, role):
    with app.app_context():
        from database import get_connection

        with get_connection() as conn:
            conn.execute("UPDATE users SET role = ?, password_hash = ? WHERE id = ?", (role, generate_password_hash("StrongPass123!"), user_id))
            conn.commit()


def test_explicit_migration_is_idempotent_and_does_not_replace_legacy_schema_marker(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    with app.app_context():
        from database import CURRENT_SCHEMA_VERSION, get_connection
        from services.schema_migration_service import apply_pending_schema_migrations

        with get_connection() as conn:
            first = apply_pending_schema_migrations(conn)
            second = apply_pending_schema_migrations(conn)
            count = conn.execute("SELECT COUNT(*) AS count FROM explicit_schema_migrations").fetchone()["count"]
            legacy = conn.execute("SELECT version FROM schema_migrations ORDER BY applied_at DESC LIMIT 1").fetchone()["version"]
            conn.commit()

    assert second == []
    assert count >= 1
    assert legacy == CURRENT_SCHEMA_VERSION
    assert all(version != CURRENT_SCHEMA_VERSION for version in first)


def test_student_age_gate_then_under14_guardian_and_child_assent(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    parent = _register(client, "minor-parent", "parent")
    student = _register(client, "minor-student", "student")
    parent_headers = _headers(parent["token"])
    student_headers = _headers(student["token"])

    initial = client.get("/api/minor-safeguards/status", headers=student_headers)
    assert initial.status_code == 200
    assert initial.get_json()["data"]["status"] == "age_verification_required"

    code = client.post("/api/family/create-bind-code", headers=parent_headers, json={}).get_json()["data"]["bind_code"]
    blocked_bind = client.post("/api/family/bind-student", headers=student_headers, json={"bind_code": code})
    assert blocked_bind.status_code == 403
    assert blocked_bind.get_json()["error"]["code"] == "age_verification_required"

    age = client.post(
        "/api/minor-safeguards/age-confirmation",
        headers=student_headers,
        json={"age_band": "under_14"},
    )
    assert age.status_code == 200
    assert age.get_json()["data"]["status"] == "guardian_link_required"

    bound = client.post("/api/family/bind-student", headers=student_headers, json={"bind_code": code})
    assert bound.status_code == 200
    assert bound.get_json()["data"]["minor_safeguards"]["status"] == "guardian_consent_required"

    consent = client.post(
        "/api/minor-safeguards/guardian-consent",
        headers=parent_headers,
        json={"child_user_id": student["user"]["id"], "agreed": True},
    )
    assert consent.status_code == 200
    assert consent.get_json()["data"]["status"] == "child_assent_required"

    assent = client.post(
        "/api/minor-safeguards/child-assent",
        headers=student_headers,
        json={"assented": True},
    )
    assert assent.status_code == 200
    assert assent.get_json()["data"]["status"] == "active"

    with app.app_context():
        from services.participant_safeguard_service import assert_participant_capability

        status = assert_participant_capability(student["user"]["id"], "assessment")
    assert status["status"] == "active"


def test_child_refusal_wins_over_guardian_consent(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    parent = _register(client, "refusal-parent", "parent")
    student = _register(client, "refusal-student", "student")
    ph = _headers(parent["token"])
    sh = _headers(student["token"])
    client.post("/api/minor-safeguards/age-confirmation", headers=sh, json={"age_band": "under_14"})
    code = client.post("/api/family/create-bind-code", headers=ph, json={}).get_json()["data"]["bind_code"]
    client.post("/api/family/bind-student", headers=sh, json={"bind_code": code})
    client.post("/api/minor-safeguards/guardian-consent", headers=ph, json={"child_user_id": student["user"]["id"], "agreed": True})
    refusal = client.post("/api/minor-safeguards/child-assent", headers=sh, json={"assented": False})
    assert refusal.get_json()["data"]["status"] == "blocked_withdrawn_or_refused"


def test_risk_review_rejects_client_selected_reviewer_and_audits_authenticated_actor(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    reviewer = _register(client, "risk-reviewer", "parent")
    reviewer_id = reviewer["user"]["id"]
    _promote(app, reviewer_id, "supervisor")
    headers = _headers(reviewer["token"])

    with app.app_context():
        from database import ensure_user, get_connection
        from services.risk_review_service import create_risk_review_record
        from services.risk_service import check_text_risk

        with get_connection() as conn:
            ensure_user(conn, "participant-risk", "participant")
            created = create_risk_review_record(
                conn,
                "participant-risk",
                "test",
                "source-1",
                check_text_risk("我现在不想活，已经计划今晚伤害自己。"),
            )
            conn.commit()
            review_id = created["id"]

    spoof = client.post(
        f"/api/risk-review/{review_id}/review",
        headers=headers,
        json={"reviewer_id": "someone-else", "review_status": "reviewed"},
    )
    assert spoof.status_code == 403
    assert spoof.get_json()["error"]["code"] == "reviewer_identity_mismatch"

    reviewed = client.post(
        f"/api/risk-review/{review_id}/review",
        headers=headers,
        json={"review_status": "reviewed", "review_note": "已人工查看并按流程处理。"},
    )
    assert reviewed.status_code == 200
    assert reviewed.get_json()["data"]["reviewer_id"] == reviewer_id

    with app.app_context():
        from database import get_connection

        with get_connection() as conn:
            audit = conn.execute(
                "SELECT * FROM audit_logs WHERE action = 'review_risk' AND target_id = ? ORDER BY created_at DESC LIMIT 1",
                (review_id,),
            ).fetchone()
    assert audit["actor_id"] == reviewer_id


def test_supervision_sla_masks_contact_and_audits_sensitive_reviewer_read(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    participant = _register(client, "support-parent", "parent")
    reviewer = _register(client, "support-reviewer", "parent")
    reviewer_id = reviewer["user"]["id"]
    _promote(app, reviewer_id, "supervisor")

    created = client.post(
        "/api/supervision",
        headers=_headers(participant["token"]),
        json={
            "message": "我现在撑不住，担心今晚会伤害自己。",
            "contact": "13800138000",
            "risk_hint": "现在需要人工支持",
        },
    )
    assert created.status_code == 201
    item = created.get_json()["data"]
    assert item["priority"] == "urgent"
    assert item["due_at"]
    assert "contact" not in item
    assert item["contact_masked"] == "138****8000"

    request_id = item["id"]
    reviewer_headers = _headers(reviewer["token"])
    detail = client.get(f"/api/supervision/{request_id}/reviewer", headers=reviewer_headers)
    assert detail.status_code == 200
    assert detail.get_json()["data"]["contact"] == "13800138000"

    acknowledged = client.post(f"/api/supervision/{request_id}/acknowledge", headers=reviewer_headers, json={})
    assert acknowledged.get_json()["data"]["status"] == "acknowledged"
    resolved = client.post(
        f"/api/supervision/{request_id}/resolve",
        headers=reviewer_headers,
        json={"resolution_code": "referred_to_offline_support"},
    )
    assert resolved.get_json()["data"]["status"] == "resolved"

    with app.app_context():
        from database import get_connection

        with get_connection() as conn:
            events = conn.execute("SELECT COUNT(*) AS count FROM supervision_request_events WHERE request_id = ?", (request_id,)).fetchone()["count"]
            audit = conn.execute(
                "SELECT * FROM audit_logs WHERE action = 'supervision_sensitive_contact_viewed' AND target_id = ? ORDER BY created_at DESC LIMIT 1",
                (request_id,),
            ).fetchone()
    assert events >= 3
    assert audit["actor_id"] == reviewer_id


def test_legacy_admin_header_disabled_by_default_in_pilot(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    response = client.get("/api/risk-review", headers={"X-Admin-Token": "legacy-admin-token"})
    assert response.status_code == 401
    assert response.get_json()["error"]["code"] == "legacy_admin_token_disabled"


def test_governance_sync_does_not_append_empty_legacy_capability():
    script = BACKEND / "scripts" / "sync_api_governance_registries.py"
    spec = importlib.util.spec_from_file_location("sync_api_governance_registries", script)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)

    contract = {
        "version": "test-contract",
        "endpoints": [{"operation_id": "example.read.get"}],
    }
    registry = {
        "capabilities": [
            {"id": "capability.example", "operation_ids": ["example.read.get"]}
        ],
        "production_release_approved": False,
    }

    synchronized, convergence_operations = module.sync_operations(contract, registry)

    assert convergence_operations == []
    assert [item["id"] for item in synchronized["capabilities"]] == [
        "capability.example"
    ]


def test_security_generator_is_stable_under_governance_sync():
    generator_path = BACKEND / "scripts" / "generate_task31_security_registry.py"
    sync_path = BACKEND / "scripts" / "sync_api_governance_registries.py"
    generator_spec = importlib.util.spec_from_file_location("generate_task31_security_registry", generator_path)
    sync_spec = importlib.util.spec_from_file_location("sync_api_governance_registries_for_security", sync_path)
    generator = importlib.util.module_from_spec(generator_spec)
    sync = importlib.util.module_from_spec(sync_spec)
    assert generator_spec.loader is not None
    assert sync_spec.loader is not None
    generator_spec.loader.exec_module(generator)
    sync_spec.loader.exec_module(sync)

    generated = generator.build_registry()
    contract = json.loads(generator.CONTRACT_PATH.read_text(encoding="utf-8"))
    synchronized, added = sync.sync_security(contract, generated.copy())

    assert added == []
    assert synchronized == generated
