import importlib
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"


def _fresh_app(tmp_path, monkeypatch):
    sys.path.insert(0, str(BACKEND))
    for name in list(sys.modules):
        if name in {"app", "config", "database", "models"} or name.startswith(("routes.", "services.")):
            sys.modules.pop(name, None)
    monkeypatch.setenv("APP_ENV", "testing")
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "task38-f02.sqlite3"))
    monkeypatch.setenv("CONTENT_DIR", str(ROOT / "content"))
    return importlib.import_module("app").app


def _seed(app):
    with app.app_context():
        from database import get_connection, now_iso
        from routes.auth_utils import generate_auth_token

        now = now_iso()
        users = {
            "parent-f02": "parent",
            "researcher-f02": "researcher",
            "supervisor-f02": "supervisor",
        }
        with get_connection() as conn:
            for actor_id, role in users.items():
                conn.execute(
                    "INSERT INTO users (id, nickname, role, status, created_at, updated_at) VALUES (?, ?, ?, 'active', ?, ?)",
                    (actor_id, actor_id, role, now, now),
                )
            conn.commit()
        return {
            role: {"Authorization": f"Bearer {generate_auth_token({'id': actor_id, 'role': role})}"}
            for actor_id, role in users.items()
        }


def _create_case(client, headers):
    response = client.post(
        "/api/therapeutic-assessment/cases",
        headers={**headers["parent"], "Idempotency-Key": "f02-create"},
        json={
            "assessment_question": "我想理解一次沟通为什么让我退开",
            "shared_scope": ["question"],
            "consent": True,
        },
    )
    assert response.status_code == 201
    return response.get_json()["data"]


def _transition(client, headers, case_id, track, target, version, key, reason="participant_choice"):
    return client.post(
        f"/api/therapeutic-assessment/cases/{case_id}/transitions",
        headers={**headers, "Idempotency-Key": key},
        json={
            "track": track,
            "target_state": target,
            "expected_version": version,
            "reason_code": reason,
        },
    )


def test_schema_031_has_three_state_tracks(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    with app.app_context():
        from database import CURRENT_SCHEMA_NAME, CURRENT_SCHEMA_VERSION, get_connection

        with get_connection() as conn:
            columns = {row["name"] for row in conn.execute("PRAGMA table_info(therapeutic_assessment_cases)").fetchall()}
            assert {"workflow_state", "hypothesis_state", "safety_state"}.issubset(columns)
        assert CURRENT_SCHEMA_VERSION == "2026_07_27_037"
        assert CURRENT_SCHEMA_NAME == "therapeutic_assessment_researcher_workbench"


def test_workflow_transition_is_versioned_idempotent_and_rejects_skip(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    headers = _seed(app)
    client = app.test_client()
    case = _create_case(client, headers)
    assert case["workflow_state"] == "submitted"

    illegal = _transition(
        client,
        headers["supervisor"],
        case["id"],
        "workflow",
        "participant_check",
        case["version"],
        "f02-illegal",
        "research_review",
    )
    pending = _transition(
        client,
        headers["supervisor"],
        case["id"],
        "workflow",
        "pending_human_review",
        case["version"],
        "f02-pending",
        "research_review",
    )
    replay = _transition(
        client,
        headers["supervisor"],
        case["id"],
        "workflow",
        "pending_human_review",
        case["version"],
        "f02-pending",
        "research_review",
    )
    assert illegal.status_code == 409
    assert pending.status_code == 200
    assert pending.get_json()["data"]["workflow_state"] == "pending_human_review"
    assert replay.status_code == 200
    assert replay.get_json()["data"]["version"] == pending.get_json()["data"]["version"]


def test_tracks_have_role_guards_and_optimistic_lock(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    headers = _seed(app)
    client = app.test_client()
    case = _create_case(client, headers)
    denied = _transition(
        client,
        headers["parent"],
        case["id"],
        "hypothesis",
        "pattern_candidate",
        case["version"],
        "f02-denied",
        "evidence_updated",
    )
    hypothesis = _transition(
        client,
        headers["supervisor"],
        case["id"],
        "hypothesis",
        "pattern_candidate",
        case["version"],
        "f02-hypothesis",
        "evidence_updated",
    )
    stale = _transition(
        client,
        headers["supervisor"],
        case["id"],
        "safety",
        "needs_human_review",
        case["version"],
        "f02-stale",
        "risk_signal",
    )
    assert denied.status_code == 403
    assert hypothesis.status_code == 200
    assert hypothesis.get_json()["data"]["hypothesis_state"] == "pattern_candidate"
    assert stale.status_code == 409
    assert stale.get_json()["error"]["code"] == "version_conflict"


def test_withdrawn_workflow_is_terminal(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    headers = _seed(app)
    client = app.test_client()
    case = _create_case(client, headers)
    withdrawn = _transition(
        client,
        headers["parent"],
        case["id"],
        "workflow",
        "withdrawn",
        case["version"],
        "f02-withdraw",
    )
    again = _transition(
        client,
        headers["parent"],
        case["id"],
        "workflow",
        "submitted",
        withdrawn.get_json()["data"]["version"],
        "f02-after-withdraw",
    )
    assert withdrawn.status_code == 200
    assert withdrawn.get_json()["data"]["workflow_state"] == "withdrawn"
    assert again.status_code == 409
    assert again.get_json()["error"]["code"] == "withdrawn"


def test_migration_is_additive_and_production_guarded(tmp_path):
    database_path = tmp_path / "migration-f02.sqlite3"
    env = {**os.environ, "APP_ENV": "testing", "DATABASE_PATH": str(database_path), "CONTENT_DIR": str(ROOT / "content")}
    apply_result = subprocess.run(
        [sys.executable, str(BACKEND / "scripts/migrate_task38_f02_state_machine.py"), "apply"],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
    )
    assert apply_result.returncode == 0
    assert '"columns_ok": true' in apply_result.stdout.lower()

    blocked_env = {**env, "APP_ENV": "production"}
    blocked = subprocess.run(
        [sys.executable, str(BACKEND / "scripts/migrate_task38_f02_state_machine.py"), "apply"],
        cwd=ROOT,
        env=blocked_env,
        capture_output=True,
        text=True,
    )
    assert blocked.returncode != 0
    assert "精确确认" in (blocked.stdout + blocked.stderr)
