import importlib
import json
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
POLICY = ROOT / "content" / "therapeutic_assessment_child_policy.json"


def _app(tmp_path, monkeypatch):
    sys.path.insert(0, str(BACKEND))
    for name in list(sys.modules):
        if name in {"app", "config", "database", "models"} or name.startswith(
            ("routes.", "services.")
        ):
            sys.modules.pop(name, None)
    monkeypatch.setenv("APP_ENV", "testing")
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "f14.sqlite3"))
    monkeypatch.setenv("CONTENT_DIR", str(ROOT / "content"))
    return importlib.import_module("app").app


def _seed(app):
    users = {
        "guardian-f14": "parent",
        "child-f14": "student",
        "other-f14": "parent",
        "r-f14": "researcher",
        "s-f14": "supervisor",
        "a-f14": "admin",
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
                VALUES ('case-f14', 'child-f14', '我想决定愿意说到哪里', '["question"]',
                        'active', 'open', 'low', 'submitted', 'observations_only',
                        'low_risk', 'child', 'L0', 'r-f14', 1, 'child-f14', ?, ?)""",
                (now, now),
            )
            conn.commit()
        return {
            user_id: {
                "Authorization": f"Bearer {generate_auth_token({'id': user_id, 'role': role})}"
            }
            for user_id, role in users.items()
        }


def _initialize(client, headers):
    return client.post(
        "/api/therapeutic-assessment/cases/case-f14/child-safeguards",
        headers={**headers["s-f14"], "Idempotency-Key": "f14-init"},
        json={
            "guardian_user_id": "guardian-f14",
            "child_user_id": "child-f14",
            "expected_case_version": 1,
        },
    )


def test_policy_keeps_child_entry_closed_and_separates_decisions_and_sources():
    payload = json.loads(POLICY.read_text(encoding="utf-8"))
    assert payload["schema"] == "safehome.therapeutic-assessment.child-safeguards.v1"
    assert payload["entry_enabled"] is False
    assert payload["production_release_approved"] is False
    assert payload["guardian_consent_does_not_override_child_refusal"] is True
    assert payload["required_external_gates"] == [
        "t3_child_competency",
        "ethics_approval",
        "a0_a3_pilot_evidence",
    ]
    assert set(payload["source_domains"]) == {
        "child",
        "guardian",
        "school",
        "professional",
    }


def test_supervisor_initializes_separate_guardian_and_child_controls(tmp_path, monkeypatch):
    app = _app(tmp_path, monkeypatch)
    headers = _seed(app)
    response = _initialize(app.test_client(), headers)
    assert response.status_code == 201
    data = response.get_json()["data"]
    assert data["guardian_consent_status"] == "pending"
    assert data["child_assent_status"] == "pending"
    assert data["status"] == "blocked_pending_child_safeguards"
    assert all(
        item["joint_feedback_allowed"] is False
        for item in data["source_permissions"].values()
    )


def test_guardian_consent_cannot_override_child_refusal(tmp_path, monkeypatch):
    app = _app(tmp_path, monkeypatch)
    headers = _seed(app)
    client = app.test_client()
    initialized = _initialize(client, headers).get_json()["data"]
    guardian = client.patch(
        "/api/therapeutic-assessment/cases/case-f14/child-safeguards/decision",
        headers={**headers["guardian-f14"], "Idempotency-Key": "f14-guardian-consent"},
        json={"action": "guardian_consent", "expected_version": initialized["version"]},
    )
    child = client.patch(
        "/api/therapeutic-assessment/cases/case-f14/child-safeguards/decision",
        headers={**headers["child-f14"], "Idempotency-Key": "f14-child-refuse"},
        json={"action": "child_refuse", "expected_version": guardian.get_json()["data"]["version"]},
    )
    assert guardian.status_code == child.status_code == 200
    data = child.get_json()["data"]
    assert data["guardian_consent_status"] == "active"
    assert data["child_assent_status"] == "refused"
    assert data["status"] == "blocked_child_refusal"
    assert data["entry_enabled"] is False


def test_child_assent_still_requires_t3_ethics_and_pilot_evidence(tmp_path, monkeypatch):
    app = _app(tmp_path, monkeypatch)
    headers = _seed(app)
    client = app.test_client()
    current = _initialize(client, headers).get_json()["data"]
    guardian = client.patch(
        "/api/therapeutic-assessment/cases/case-f14/child-safeguards/decision",
        headers={**headers["guardian-f14"], "Idempotency-Key": "f14-consent"},
        json={"action": "guardian_consent", "expected_version": current["version"]},
    ).get_json()["data"]
    child = client.patch(
        "/api/therapeutic-assessment/cases/case-f14/child-safeguards/decision",
        headers={**headers["child-f14"], "Idempotency-Key": "f14-assent"},
        json={"action": "child_assent", "expected_version": guardian["version"]},
    ).get_json()["data"]
    assert child["status"] == "blocked_external_gates"
    gated = client.patch(
        "/api/therapeutic-assessment/cases/case-f14/child-safeguards/gates",
        headers={**headers["s-f14"], "Idempotency-Key": "f14-gates"},
        json={
            "t3_evidence_ref": "evidence:t3-child",
            "ethics_evidence_ref": "evidence:ethics-child",
            "pilot_evidence_ref": "evidence:a0-a3-child",
            "expected_version": child["version"],
        },
    )
    assert gated.status_code == 200
    result = gated.get_json()["data"]
    assert result["status"] == "specialist_review_ready"
    assert result["entry_enabled"] is False
    assert result["production_release_approved"] is False


def test_linked_child_sources_never_auto_enter_joint_feedback(tmp_path, monkeypatch):
    app = _app(tmp_path, monkeypatch)
    headers = _seed(app)
    client = app.test_client()
    _initialize(client, headers)
    child_view = client.get(
        "/api/therapeutic-assessment/cases/case-f14/child-safeguards",
        headers=headers["child-f14"],
    )
    guardian_view = client.get(
        "/api/therapeutic-assessment/cases/case-f14/child-safeguards",
        headers=headers["guardian-f14"],
    )
    assert child_view.status_code == guardian_view.status_code == 200
    assert child_view.get_json()["data"]["child_private_material_auto_shared"] is False
    assert guardian_view.get_json()["data"]["child_private_material_auto_shared"] is False


def test_unlinked_account_and_wrong_capacity_are_denied(tmp_path, monkeypatch):
    app = _app(tmp_path, monkeypatch)
    headers = _seed(app)
    client = app.test_client()
    current = _initialize(client, headers).get_json()["data"]
    denied = client.get(
        "/api/therapeutic-assessment/cases/case-f14/child-safeguards",
        headers=headers["other-f14"],
    )
    wrong = client.patch(
        "/api/therapeutic-assessment/cases/case-f14/child-safeguards/decision",
        headers={**headers["guardian-f14"], "Idempotency-Key": "f14-wrong"},
        json={"action": "child_assent", "expected_version": current["version"]},
    )
    assert denied.status_code == 403
    assert wrong.status_code == 403


def test_public_contract_and_clients_expose_closed_child_subline(tmp_path, monkeypatch):
    app = _app(tmp_path, monkeypatch)
    headers = _seed(app)
    response = app.test_client().get(
        "/api/therapeutic-assessment/child-safeguards",
        headers=headers["child-f14"],
    )
    assert response.status_code == 200
    assert response.get_json()["data"]["entry_enabled"] is False
    shared = (ROOT / "shared/types/api.ts").read_text(encoding="utf-8")
    web = (ROOT / "apps/web/src/services/safehomeApi.ts").read_text(encoding="utf-8")
    mini = (ROOT / "apps/miniprogram/services/api.js").read_text(encoding="utf-8")
    assert "TherapeuticAssessmentChildSafeguard" in shared
    assert "getTherapeuticAssessmentChildPolicy" in web
    assert "getTherapeuticAssessmentChildPolicy" in mini


def test_migration_plan_apply_verify_and_rollback(tmp_path):
    database = tmp_path / "migration-f14.sqlite3"
    env = os.environ.copy()
    env.update({"APP_ENV": "testing", "CONTENT_DIR": str(ROOT / "content"), "PYTHONPATH": str(BACKEND)})
    script = BACKEND / "scripts" / "migrate_task38_f14_child_safeguards.py"
    results = []
    for action in ("plan", "apply", "verify", "rollback"):
        results.append(
            subprocess.run(
                [sys.executable, str(script), action, "--database-path", str(database)],
                cwd=ROOT,
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
        )
    assert all(item.returncode == 0 for item in results)
    assert json.loads(results[2].stdout)["ok"] is True
    assert json.loads(results[3].stdout)["history_deleted"] is False
