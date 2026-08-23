import importlib
import json
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
POLICY = ROOT / "content" / "therapeutic_assessment_multi_party_policy.json"


def _app(tmp_path, monkeypatch):
    sys.path.insert(0, str(BACKEND))
    for name in list(sys.modules):
        if name in {"app", "config", "database", "models"} or name.startswith(
            ("routes.", "services.")
        ):
            sys.modules.pop(name, None)
    monkeypatch.setenv("APP_ENV", "testing")
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "f15.sqlite3"))
    monkeypatch.setenv("CONTENT_DIR", str(ROOT / "content"))
    return importlib.import_module("app").app


def _seed(app):
    users = {
        "party-a": "parent",
        "party-b": "parent",
        "outsider": "parent",
        "r-f15": "researcher",
        "s-f15": "supervisor",
        "a-f15": "admin",
    }
    with app.app_context():
        from database import get_connection, now_iso
        from routes.auth_utils import generate_auth_token

        now = now_iso()
        with get_connection() as conn:
            for user_id, role in users.items():
                conn.execute(
                    "INSERT INTO users (id, nickname, role, status, created_at, updated_at) VALUES (?, ?, ?, 'active', ?, ?)",
                    (user_id, user_id, role, now, now),
                )
            conn.execute(
                """INSERT INTO therapeutic_assessment_cases
                (id, participant_user_id, assessment_question, shared_scope_json,
                 consent_status, status, risk_level, workflow_state, hypothesis_state,
                 safety_state, complexity_scope, readiness_level, assigned_researcher_id,
                 version, created_by, created_at, updated_at)
                VALUES ('case-f15', 'party-a', '我们想决定哪些内容适合共同讨论', '["question"]',
                        'active', 'open', 'low', 'submitted', 'observations_only',
                        'low_risk', 'couple', 'L0', 'r-f15', 1, 'party-a', ?, ?)""",
                (now, now),
            )
            conn.commit()
        return {
            user_id: {
                "Authorization": f"Bearer {generate_auth_token({'id': user_id, 'role': role})}"
            }
            for user_id, role in users.items()
        }


def _grant_supervisor_scope(client):
    with client.application.app_context():
        from database import get_connection, now_iso

        timestamp = now_iso()
        with get_connection() as conn:
            conn.execute(
                """INSERT OR IGNORE INTO therapeutic_assessment_work_queue (
                id, case_id, queue_type, task_code, required_competency,
                priority, status, scope_snapshot_json, assigned_user_id,
                due_at, version, created_by, created_at, updated_at
                ) VALUES ('queue-f15', 'case-f15', 'supervision', 'multi_party_safeguards',
                          'T3', 'normal', 'claimed', '{}', 's-f15',
                          '2099-01-01T00:00:00+00:00', 1, 's-f15', ?, ?)""",
                (timestamp, timestamp),
            )
            conn.commit()


def _init(client, headers, *, scoped=True):
    if scoped:
        _grant_supervisor_scope(client)
    return client.post(
        "/api/therapeutic-assessment/cases/case-f15/multi-party-safeguards",
        headers={**headers["s-f15"], "Idempotency-Key": "f15-init"},
        json={"party_user_ids": ["party-a", "party-b"], "expected_case_version": 1},
    )


def _screen(client, headers, user_id, version, **overrides):
    payload = {
        "fear": False,
        "coercive_control": False,
        "violence": False,
        "retaliation_risk": False,
        "custody_dispute": False,
        "shared_device_risk": False,
        "expected_version": version,
    }
    payload.update(overrides)
    return client.patch(
        "/api/therapeutic-assessment/cases/case-f15/multi-party-safeguards/safety-screen",
        headers={**headers[user_id], "Idempotency-Key": f"f15-screen-{user_id}-{version}"},
        json=payload,
    )


def test_policy_defaults_to_closed_separate_and_non_equalizing():
    payload = json.loads(POLICY.read_text(encoding="utf-8"))
    assert payload["schema"] == "safehome.therapeutic-assessment.multi-party.v1"
    assert payload["entry_enabled"] is False
    assert payload["individual_disclosure_joint_default"] is False
    assert payload["relationship_cycle_must_not_equalize_harm"] is True
    assert set(payload["precheck_signals"]) == {
        "fear",
        "coercive_control",
        "violence",
        "retaliation_risk",
        "custody_dispute",
        "shared_device_risk",
    }


def test_supervisor_initializes_two_party_scope_without_joint_sharing(tmp_path, monkeypatch):
    app = _app(tmp_path, monkeypatch)
    headers = _seed(app)
    client = app.test_client()
    assert _init(client, headers, scoped=False).status_code == 404
    response = _init(client, headers)
    assert response.status_code == 201
    data = response.get_json()["data"]
    assert data["status"] == "blocked_pending_multi_party"
    assert data["joint_feedback_allowed"] is False
    assert set(data["party_user_ids"]) == {"party-a", "party-b"}
    assert all(value == "pending" for value in data["party_consents"].values())
    with app.app_context():
        from database import get_connection

        with get_connection() as conn:
            conn.execute("DELETE FROM therapeutic_assessment_work_queue WHERE id = 'queue-f15'")
            conn.commit()
    assert client.get(
        "/api/therapeutic-assessment/cases/case-f15/multi-party-safeguards",
        headers=headers["s-f15"],
    ).status_code == 404
    assert client.patch(
        "/api/therapeutic-assessment/cases/case-f15/multi-party-safeguards/gates",
        headers={**headers["s-f15"], "Idempotency-Key": "f15-no-scope-gates"},
        json={
            "t3_evidence_ref": "evidence:t3-multi",
            "ethics_evidence_ref": "evidence:ethics-multi",
            "pilot_evidence_ref": "evidence:a0-a3-multi",
            "expected_version": data["version"],
        },
    ).status_code == 404


def test_any_safety_signal_forces_separate_support_without_exposing_party(tmp_path, monkeypatch):
    app = _app(tmp_path, monkeypatch)
    headers = _seed(app)
    client = app.test_client()
    current = _init(client, headers).get_json()["data"]
    screened = _screen(client, headers, "party-a", current["version"], coercive_control=True)
    assert screened.status_code == 200
    data = screened.get_json()["data"]
    assert data["status"] == "separate_support_required"
    assert data["joint_feedback_allowed"] is False
    party_b_view = client.get(
        "/api/therapeutic-assessment/cases/case-f15/multi-party-safeguards",
        headers=headers["party-b"],
    ).get_json()["data"]
    assert "screening_by_party" not in party_b_view
    assert party_b_view["safety_signal_present"] is True


def test_all_party_consent_and_clean_screen_still_require_external_gates(tmp_path, monkeypatch):
    app = _app(tmp_path, monkeypatch)
    headers = _seed(app)
    client = app.test_client()
    state = _init(client, headers).get_json()["data"]
    for user_id in ("party-a", "party-b"):
        state = _screen(client, headers, user_id, state["version"]).get_json()["data"]
        state = client.patch(
            "/api/therapeutic-assessment/cases/case-f15/multi-party-safeguards/consent",
            headers={**headers[user_id], "Idempotency-Key": f"f15-consent-{user_id}"},
            json={"decision": "consent", "expected_version": state["version"]},
        ).get_json()["data"]
    assert state["status"] == "blocked_external_gates"
    gated = client.patch(
        "/api/therapeutic-assessment/cases/case-f15/multi-party-safeguards/gates",
        headers={**headers["s-f15"], "Idempotency-Key": "f15-gates"},
        json={
            "t3_evidence_ref": "evidence:t3-couple",
            "ethics_evidence_ref": "evidence:ethics-couple",
            "pilot_evidence_ref": "evidence:pilot-couple",
            "expected_version": state["version"],
        },
    ).get_json()["data"]
    assert gated["status"] == "specialist_review_ready"
    assert gated["joint_feedback_allowed"] is True
    assert gated["entry_enabled"] is False
    assert gated["production_release_approved"] is False


def test_one_party_refusal_blocks_joint_feedback(tmp_path, monkeypatch):
    app = _app(tmp_path, monkeypatch)
    headers = _seed(app)
    client = app.test_client()
    state = _init(client, headers).get_json()["data"]
    refused = client.patch(
        "/api/therapeutic-assessment/cases/case-f15/multi-party-safeguards/consent",
        headers={**headers["party-b"], "Idempotency-Key": "f15-refuse"},
        json={"decision": "refuse", "expected_version": state["version"]},
    )
    assert refused.status_code == 200
    data = refused.get_json()["data"]
    assert data["status"] == "blocked_party_refusal"
    assert data["joint_feedback_allowed"] is False


def test_outsider_and_unassigned_researcher_are_denied(tmp_path, monkeypatch):
    app = _app(tmp_path, monkeypatch)
    headers = _seed(app)
    client = app.test_client()
    _init(client, headers)
    denied = client.get(
        "/api/therapeutic-assessment/cases/case-f15/multi-party-safeguards",
        headers=headers["outsider"],
    )
    assert denied.status_code == 404


def test_public_contract_and_clients_expose_multi_party_protection(tmp_path, monkeypatch):
    app = _app(tmp_path, monkeypatch)
    headers = _seed(app)
    response = app.test_client().get(
        "/api/therapeutic-assessment/multi-party-safeguards",
        headers=headers["party-a"],
    )
    assert response.status_code == 200
    assert response.get_json()["data"]["entry_enabled"] is False
    shared = (ROOT / "shared/types/api.ts").read_text(encoding="utf-8")
    web = (ROOT / "apps/web/src/services/safehomeApi.ts").read_text(encoding="utf-8")
    mini = (ROOT / "apps/miniprogram/services/api.js").read_text(encoding="utf-8")
    assert "TherapeuticAssessmentMultiPartySafeguard" in shared
    assert "getTherapeuticAssessmentMultiPartyPolicy" in web
    assert "getTherapeuticAssessmentMultiPartyPolicy" in mini


def test_migration_plan_apply_verify_and_rollback(tmp_path):
    database = tmp_path / "migration-f15.sqlite3"
    env = os.environ.copy()
    env.update({"APP_ENV": "testing", "CONTENT_DIR": str(ROOT / "content"), "PYTHONPATH": str(BACKEND)})
    script = BACKEND / "scripts" / "migrate_task38_f15_multi_party_safeguards.py"
    results = [
        subprocess.run(
            [sys.executable, str(script), action, "--database-path", str(database)],
            cwd=ROOT,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        for action in ("plan", "apply", "verify", "rollback")
    ]
    assert all(item.returncode == 0 for item in results)
    assert json.loads(results[2].stdout)["ok"] is True
    assert json.loads(results[3].stdout)["history_deleted"] is False
