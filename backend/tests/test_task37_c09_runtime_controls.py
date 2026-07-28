import importlib
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"


def _app(tmp_path, monkeypatch):
    if str(BACKEND) not in sys.path:
        sys.path.insert(0, str(BACKEND))
    for name in list(sys.modules):
        if name in {"app", "config", "database", "models"} or name.startswith(
            ("routes.", "services.")
        ):
            sys.modules.pop(name, None)
    monkeypatch.setenv("APP_ENV", "testing")
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "c09.sqlite3"))
    monkeypatch.setenv("CONTENT_DIR", str(ROOT / "content"))
    monkeypatch.setenv("AI_QA_SANDBOX_ENABLED", "1")
    return importlib.import_module("app").app


def _seed_user_and_session(app):
    with app.app_context():
        from database import get_connection, now_iso

        timestamp = now_iso()
        with get_connection() as conn:
            conn.execute(
                """
                INSERT INTO users (
                    id, nickname, role, status, created_at, updated_at
                ) VALUES (
                    'researcher-c09', 'researcher-c09', 'researcher',
                    'active', ?, ?
                )
                """,
                (timestamp, timestamp),
            )
            conn.execute(
                """
                INSERT INTO users (
                    id, nickname, role, status, created_at, updated_at
                ) VALUES (
                    'admin-c09', 'admin-c09', 'admin',
                    'active', ?, ?
                )
                """,
                (timestamp, timestamp),
            )
            conn.execute(
                """
                INSERT INTO ai_qa_sessions (
                    id, user_id, mode, status, synthetic_data,
                    context_policy, research_use_allowed, use_case_id,
                    use_case_policy_version, created_at, updated_at
                ) VALUES (
                    'session-c09', 'researcher-c09', 'research_sandbox',
                    'active', 1, 'current_session_only', 0,
                    'approved_material_organization', 'c09', ?, ?
                )
                """,
                (timestamp, timestamp),
            )
            conn.commit()
    return {
        "actor": {"id": "researcher-c09", "role": "researcher"},
        "session": {
            "id": "session-c09",
            "use_case_id": "approved_material_organization",
        },
    }


def _seed_cost(app, *, cost=100):
    with app.app_context():
        from database import get_connection, now_iso

        with get_connection() as conn:
            conn.execute(
                """
                INSERT INTO ai_qa_provider_events (
                    id, session_id, user_id, provider, model_version,
                    status, latency_ms, cost_micros, error_code, created_at,
                    provider_request_id, input_tokens, output_tokens,
                    cost_currency
                ) VALUES (
                    'provider-event-c09', 'session-c09', 'researcher-c09',
                    'fake', 'fake-v1', 'success', 10, ?, NULL, ?,
                    'request-c09', 10, 10, 'CNY'
                )
                """,
                (cost, now_iso()),
            )
            conn.commit()


def _policy_with_budget(scope, limit=100):
    budgets = {
        "user": {"default": 0},
        "role": {"default": 0},
        "provider": {"default": 0},
        "project": {"default": 0},
    }
    if scope == "user":
        budgets[scope]["researcher-c09"] = limit
    elif scope == "role":
        budgets[scope]["researcher"] = limit
    elif scope == "provider":
        budgets[scope]["fake"] = limit
    else:
        budgets[scope]["approved_material_organization"] = limit
    return {
        "budgets_micros_per_day": budgets,
        "rate_limits_per_hour": {
            item: {"default": 0}
            for item in ("user", "role", "provider", "project")
        },
        "circuit_breaker": {
            "failure_threshold": 3,
            "cooldown_seconds": 60,
            "half_open_max_probes": 1,
        },
        "retention": {
            "session_text_days": 7,
            "deidentified_derived_days": 90,
            "provider_metadata_days": 30,
            "audit_days": 180,
        },
    }


@pytest.mark.parametrize(
    ("scope", "code"),
    [
        ("user", "ai_qa_user_budget_exhausted"),
        ("role", "ai_qa_role_budget_exhausted"),
        ("provider", "ai_qa_provider_budget_exhausted"),
        ("project", "ai_qa_project_budget_exhausted"),
    ],
)
def test_budget_is_enforced_by_user_role_provider_and_project(
    tmp_path, monkeypatch, scope, code
):
    app = _app(tmp_path, monkeypatch)
    seeded = _seed_user_and_session(app)
    _seed_cost(app)
    with app.app_context():
        service = importlib.import_module(
            "services.ai_qa_runtime_control_service"
        )
        with pytest.raises(service.UsageControlError) as caught:
            service.enforce_usage_control(
                seeded["actor"],
                seeded["session"],
                "fake",
                policy=_policy_with_budget(scope),
            )
    assert caught.value.code == code


def test_circuit_opens_half_opens_single_probe_and_closes(
    tmp_path, monkeypatch
):
    app = _app(tmp_path, monkeypatch)
    with app.app_context():
        service = importlib.import_module(
            "services.ai_qa_runtime_control_service"
        )
        policy = _policy_with_budget("user")
        now = datetime(2026, 7, 28, tzinfo=timezone.utc)
        for offset in range(3):
            service.record_circuit_outcome(
                "fake",
                success=False,
                policy=policy,
                now=now + timedelta(seconds=offset),
            )
        blocked = service.claim_circuit_permission(
            "fake", policy=policy, now=now + timedelta(seconds=10)
        )
        probe = service.claim_circuit_permission(
            "fake", policy=policy, now=now + timedelta(seconds=63)
        )
        second_probe = service.claim_circuit_permission(
            "fake", policy=policy, now=now + timedelta(seconds=64)
        )
        assert blocked["allowed"] is False
        assert blocked["state"] == "open"
        assert probe == {"allowed": True, "state": "half_open", "probe": True}
        assert second_probe["allowed"] is False
        assert second_probe["state"] == "half_open"
        service.record_circuit_outcome(
            "fake",
            success=True,
            policy=policy,
            now=now + timedelta(seconds=65),
        )
        closed = service.claim_circuit_permission(
            "fake", policy=policy, now=now + timedelta(seconds=66)
        )
        assert closed == {"allowed": True, "state": "closed", "probe": False}


def test_retention_separates_text_provider_metadata_and_audit(
    tmp_path, monkeypatch
):
    app = _app(tmp_path, monkeypatch)
    seeded = _seed_user_and_session(app)
    old_text = (datetime.now(timezone.utc) - timedelta(days=10)).isoformat()
    with app.app_context():
        from database import get_connection, now_iso
        from routes.auth_utils import generate_auth_token

        with get_connection() as conn:
            conn.execute(
                "UPDATE ai_qa_sessions SET created_at = ? WHERE id = 'session-c09'",
                (old_text,),
            )
            conn.execute(
                """
                INSERT INTO ai_qa_messages (
                    id, session_id, user_id, role, content, citations_json,
                    model_json, safety_json, prompt_version, knowledge_version,
                    token_estimate, cost_micros, created_at
                ) VALUES (
                    'message-c09', 'session-c09', 'researcher-c09', 'user',
                    'synthetic text', '[]', '{}', '{}', 'c09', 'c09', 0, 0, ?
                )
                """,
                (old_text,),
            )
            conn.execute(
                """
                INSERT INTO ai_qa_provider_events (
                    id, session_id, user_id, provider, model_version, status,
                    latency_ms, cost_micros, error_code, created_at,
                    provider_request_id, input_tokens, output_tokens,
                    cost_currency
                ) VALUES (
                    'provider-retain-c09', 'session-c09', 'researcher-c09',
                    'fake', 'fake-v1', 'success', 10, 0, NULL, ?, NULL,
                    0, 0, 'unknown'
                )
                """,
                (old_text,),
            )
            conn.commit()
        token = generate_auth_token(
            {"id": "admin-c09", "role": "admin"}
        )
    response = app.test_client().post(
        "/api/ai-qa/retention/purge",
        json={"dry_run": False, "confirm_synthetic_purge": True},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.get_json()["data"]
    assert data["retention"]["session_text_days"] == 7
    assert data["retention"]["provider_metadata_days"] == 30
    assert data["retention"]["audit_days"] == 180
    with app.app_context():
        from database import get_connection

        with get_connection() as conn:
            assert (
                conn.execute(
                    "SELECT COUNT(*) AS n FROM ai_qa_messages"
                ).fetchone()["n"]
                == 0
            )
            assert (
                conn.execute(
                    "SELECT COUNT(*) AS n FROM ai_qa_provider_events"
                ).fetchone()["n"]
                == 1
            )
            assert (
                conn.execute(
                    "SELECT COUNT(*) AS n FROM audit_logs"
                ).fetchone()["n"]
                >= 1
            )


def test_runtime_policy_and_config_keep_core_services_independent(
    tmp_path, monkeypatch
):
    app = _app(tmp_path, monkeypatch)
    policy = json.loads(
        (ROOT / "content" / "ai_qa_runtime_policy.json").read_text(
            encoding="utf-8"
        )
    )
    assert set(policy["budgets_micros_per_day"]) == {
        "user",
        "role",
        "provider",
        "project",
    }
    assert policy["core_services_unaffected"] == [
        "messages",
        "records",
        "human_feedback",
    ]
    config = app.test_client().get("/api/ai-qa/config").get_json()["data"]
    assert config["runtime_limits"]["core_services_unaffected"] == [
        "messages",
        "records",
        "human_feedback",
    ]
    assert config["runtime_limits"]["kill_switch_reactivation_via_api"] is False


def test_schema_055_adds_durable_circuit_state(tmp_path, monkeypatch):
    app = _app(tmp_path, monkeypatch)
    with app.app_context():
        database = importlib.import_module("database")
        with database.get_connection() as conn:
            tables = {
                row["name"]
                for row in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                )
            }
    assert database.CURRENT_SCHEMA_VERSION == "2026_07_28_055"
    assert database.CURRENT_SCHEMA_NAME == "ai_runtime_controls"
    assert "ai_qa_circuit_states" in tables
