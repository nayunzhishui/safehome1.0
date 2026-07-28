import importlib
import json
import shutil
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = PROJECT_ROOT / "backend"
CONTENT_ROOT = PROJECT_ROOT / "content"


def _fresh_app(tmp_path, monkeypatch):
    sys.path.insert(0, str(BACKEND_ROOT))
    for name in list(sys.modules):
        if (
            name in {"app", "config", "database", "models"}
            or name.startswith("routes.")
            or name.startswith("services.")
        ):
            sys.modules.pop(name, None)
    content_dir = tmp_path / "content"
    shutil.copytree(CONTENT_ROOT, content_dir)
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "safehome-test.sqlite3"))
    monkeypatch.setenv("CONTENT_DIR", str(content_dir))
    monkeypatch.setenv("APP_ENV", "testing")
    monkeypatch.setenv("AI_QA_PROVIDER", "fake")
    monkeypatch.setenv("AI_QA_SANDBOX_ENABLED", "1")
    module = importlib.import_module("app")
    return module.app


def _actors(app):
    specs = [
        ("researcher-c10", "researcher"),
        ("supervisor-c10", "supervisor"),
        ("admin-c10", "admin"),
        ("participant-c10", "participant"),
    ]
    with app.app_context():
        database = importlib.import_module("database")
        auth_utils = importlib.import_module("routes.auth_utils")
        with database.get_connection() as conn:
            now = database.now_iso()
            for actor_id, role in specs:
                conn.execute(
                    """
                    INSERT INTO users (
                        id, nickname, role, source, status,
                        created_at, updated_at
                    ) VALUES (?, ?, ?, 'test', 'active', ?, ?)
                    """,
                    (actor_id, actor_id, role, now, now),
                )
            conn.commit()
        return {
            actor_id: {
                "Authorization": "Bearer "
                + auth_utils.generate_auth_token(
                    {"id": actor_id, "role": role}
                )
            }
            for actor_id, role in specs
        }


def test_release_policy_has_exact_order_and_fail_closed_participant_gate(
    tmp_path, monkeypatch
):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    response = client.get("/api/ai-qa/config")
    assert response.status_code == 200
    release = response.get_json()["data"]["release_plan"]
    assert [item["id"] for item in release["stages"]] == [
        "local_fake",
        "synthetic_real_provider",
        "test_cloud_shadow",
        "researcher_read_only",
        "researcher_editable_candidate",
        "restricted_participant_evaluation",
    ]
    assert release["current_stage"] == "local_fake"
    assert release["participant_entry_enabled"] is False
    assert release["production_release_approved"] is False


def test_status_is_internal_only_and_exposes_next_stage_blockers(
    tmp_path, monkeypatch
):
    app = _fresh_app(tmp_path, monkeypatch)
    headers = _actors(app)
    client = app.test_client()
    denied = client.get(
        "/api/ai-qa/release/status", headers=headers["participant-c10"]
    )
    allowed = client.get(
        "/api/ai-qa/release/status", headers=headers["researcher-c10"]
    )
    assert denied.status_code == 403
    assert allowed.status_code == 200
    data = allowed.get_json()["data"]
    assert data["current_stage"] == "local_fake"
    assert "verified_provider_governance" in data["next_stage_blockers"]
    assert data["automatic_advance_allowed"] is False


def test_transition_cannot_skip_or_use_simulated_signoff(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    headers = _actors(app)
    client = app.test_client()
    skipped = client.post(
        "/api/ai-qa/release/transition",
        json={
            "target_stage": "test_cloud_shadow",
            "expected_version": 1,
            "simulated_agent": False,
        },
        headers={
            **headers["admin-c10"],
            "Idempotency-Key": "c10-skip-stage",
        },
    )
    simulated = client.post(
        "/api/ai-qa/release/transition",
        json={
            "target_stage": "synthetic_real_provider",
            "expected_version": 1,
            "simulated_agent": True,
        },
        headers={
            **headers["admin-c10"],
            "Idempotency-Key": "c10-simulated-signoff",
        },
    )
    assert skipped.status_code == 409
    assert skipped.get_json()["error"]["code"] == "release_stage_order_invalid"
    assert simulated.status_code == 409
    assert (
        simulated.get_json()["error"]["code"]
        == "simulated_release_signoff_forbidden"
    )


def test_next_stage_is_blocked_without_provider_and_quality_evidence(
    tmp_path, monkeypatch
):
    app = _fresh_app(tmp_path, monkeypatch)
    headers = _actors(app)
    client = app.test_client()
    response = client.post(
        "/api/ai-qa/release/transition",
        json={
            "target_stage": "synthetic_real_provider",
            "expected_version": 1,
            "simulated_agent": False,
        },
        headers={
            **headers["admin-c10"],
            "Idempotency-Key": "c10-provider-blocked",
        },
    )
    assert response.status_code == 409
    error = response.get_json()["error"]
    assert error["code"] == "release_stage_blocked"
    assert "verified_provider_governance" in error["details"]["blockers"]
    assert "approved_synthetic_quality_run" in error["details"]["blockers"]


def test_evidence_package_is_stored_hashed_and_never_approves_release(
    tmp_path, monkeypatch
):
    app = _fresh_app(tmp_path, monkeypatch)
    headers = _actors(app)
    client = app.test_client()
    response = client.post(
        "/api/ai-qa/release/evidence-packages",
        headers=headers["supervisor-c10"],
    )
    assert response.status_code == 200
    data = response.get_json()["data"]
    assert len(data["artifact_sha256"]) == 64
    assert data["production_release_approved"] is False
    assert data["simulated_signoffs_counted"] is False
    serialized = json.dumps(data, ensure_ascii=False).lower()
    assert "api_key" not in serialized
    assert "secret_key" not in serialized
    with app.app_context():
        database = importlib.import_module("database")
        with database.get_connection() as conn:
            row = conn.execute(
                "SELECT artifact_sha256, production_release_approved "
                "FROM ai_qa_release_evidence_packages"
            ).fetchone()
    assert row["artifact_sha256"] == data["artifact_sha256"]
    assert row["production_release_approved"] == 0


def test_immediate_rollback_sets_kill_switch_and_keeps_core_services(
    tmp_path, monkeypatch
):
    app = _fresh_app(tmp_path, monkeypatch)
    headers = _actors(app)
    assert app.test_client().get("/api/ai-qa/config").status_code == 200
    with app.app_context():
        database = importlib.import_module("database")
        with database.get_connection() as conn:
            conn.execute(
                """
                UPDATE ai_qa_release_state
                SET current_stage = 'researcher_editable_candidate',
                    version = 4
                WHERE singleton_key = 'ai_qa'
                """
            )
            conn.commit()
    response = app.test_client().post(
        "/api/ai-qa/release/rollback",
        json={
            "trigger": "unauthorized_access",
            "target_stage": "local_fake",
            "expected_version": 4,
            "reason": "synthetic drill",
        },
        headers={
            **headers["admin-c10"],
            "Idempotency-Key": "c10-immediate-rollback",
        },
    )
    assert response.status_code == 200
    data = response.get_json()["data"]
    assert data["current_stage"] == "local_fake"
    assert data["kill_switch_activated"] is True
    assert data["core_services_unaffected"] == [
        "messages",
        "records",
        "human_feedback",
    ]
    with app.app_context():
        database = importlib.import_module("database")
        with database.get_connection() as conn:
            killed = conn.execute(
                "SELECT killed FROM ai_qa_runtime_control "
                "WHERE id = 'global'"
            ).fetchone()
    assert killed["killed"] == 1


def test_release_schema_and_migration_contract(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    with app.app_context():
        database = importlib.import_module("database")
        assert database.CURRENT_SCHEMA_VERSION == "2026_07_29_056"
        assert database.CURRENT_SCHEMA_NAME == "ai_staged_release"
        with database.get_connection() as conn:
            tables = {
                row["name"]
                for row in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table'"
                ).fetchall()
            }
        assert {
            "ai_qa_release_state",
            "ai_qa_release_events",
            "ai_qa_release_evidence_packages",
        }.issubset(tables)


def test_release_api_is_in_generated_contract():
    contract = json.loads(
        (PROJECT_ROOT / "shared/contracts/api-contract.json").read_text(
            encoding="utf-8"
        )
    )
    paths = {item["path"] for item in contract["endpoints"]}
    assert {
        "/api/ai-qa/release/status",
        "/api/ai-qa/release/transition",
        "/api/ai-qa/release/rollback",
        "/api/ai-qa/release/evidence-packages",
    }.issubset(paths)
