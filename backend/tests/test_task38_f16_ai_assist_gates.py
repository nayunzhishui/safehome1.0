import importlib
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
POLICY = ROOT / "content" / "therapeutic_assessment_ai_assist_policy.json"


def _app(tmp_path, monkeypatch):
    sys.path.insert(0, str(BACKEND))
    for name in list(sys.modules):
        if name in {"app", "config", "database", "models"} or name.startswith(
            ("routes.", "services.")
        ):
            sys.modules.pop(name, None)
    monkeypatch.setenv("APP_ENV", "testing")
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "f16.sqlite3"))
    monkeypatch.setenv("CONTENT_DIR", str(ROOT / "content"))
    return importlib.import_module("app").app


def _seed(app):
    users = {
        "participant-f16": "parent",
        "outsider-f16": "researcher",
        "researcher-f16": "researcher",
        "supervisor-f16": "supervisor",
    }
    with app.app_context():
        from database import get_connection, now_iso
        from routes.auth_utils import generate_auth_token

        now = now_iso()
        with get_connection() as conn:
            for user_id, role in users.items():
                conn.execute(
                    "INSERT INTO users (id, nickname, role, status, created_at, updated_at) "
                    "VALUES (?, ?, ?, 'active', ?, ?)",
                    (user_id, user_id, role, now, now),
                )
            conn.execute(
                """INSERT INTO therapeutic_assessment_cases
                (id, participant_user_id, assessment_question, shared_scope_json,
                 consent_status, status, risk_level, workflow_state, hypothesis_state,
                 safety_state, complexity_scope, readiness_level, assigned_researcher_id,
                 version, created_by, created_at, updated_at)
                VALUES ('case-f16', 'participant-f16',
                        '我想理解最近一次沟通里为什么会突然停下来',
                        '["question"]', 'active', 'open', 'low', 'submitted',
                        'observations_only', 'low_risk', 'individual_adult_low_risk',
                        'L1', 'researcher-f16', 1, 'participant-f16', ?, ?)""",
                (now, now),
            )
            conn.execute(
                """INSERT INTO therapeutic_assessment_cases
                (id, participant_user_id, assessment_question, shared_scope_json,
                 consent_status, status, risk_level, workflow_state, hypothesis_state,
                 safety_state, complexity_scope, readiness_level, assigned_researcher_id,
                 version, created_by, created_at, updated_at)
                VALUES ('case-f16-risk', 'participant-f16', '我担心会再次发生伤害',
                        '["question"]', 'active', 'open', 'high', 'safety_path',
                        'observations_only', 'safety_path', 'individual_adult_low_risk',
                        'L1', 'researcher-f16', 1, 'participant-f16', ?, ?)""",
                (now, now),
            )
            conn.commit()
        return {
            user_id: {
                "Authorization": f"Bearer {generate_auth_token({'id': user_id, 'role': role})}"
            }
            for user_id, role in users.items()
        }


def _create(client, headers, case_id="case-f16", task_type="question_candidates", key="create"):
    return client.post(
        f"/api/therapeutic-assessment/cases/{case_id}/ai-assist/candidates",
        headers={**headers, "Idempotency-Key": f"f16-{key}"},
        json={
            "task_type": task_type,
            "source_field": "assessment_question",
            "expected_case_version": 1,
        },
    )


def test_policy_has_five_gates_and_human_only_boundaries():
    policy = json.loads(POLICY.read_text(encoding="utf-8"))
    assert policy["schema"] == "safehome.therapeutic-assessment.ai-assist.v1"
    assert policy["five_gates"] == [
        "minimum_input",
        "permission",
        "source",
        "language",
        "responsibility",
    ]
    assert policy["auto_publish"] is False
    assert policy["may_clear_safety_signal"] is False
    assert policy["may_create_hypothesis_h"] is False
    assert {"hypothesis_h", "assessment_interpretation", "safety_disposition"} <= set(
        policy["human_only_tasks"]
    )


def test_participant_and_out_of_scope_researcher_cannot_use_internal_assistant(tmp_path, monkeypatch):
    app = _app(tmp_path, monkeypatch)
    headers = _seed(app)
    client = app.test_client()
    assert _create(client, headers["participant-f16"], key="participant").status_code == 403
    assert _create(client, headers["outsider-f16"], key="outsider").status_code == 403


def test_low_risk_assigned_researcher_gets_original_candidates_and_all_gates(tmp_path, monkeypatch):
    app = _app(tmp_path, monkeypatch)
    headers = _seed(app)
    response = _create(app.test_client(), headers["researcher-f16"])
    assert response.status_code == 201
    data = response.get_json()["data"]
    assert data["original_text"] == "我想理解最近一次沟通里为什么会突然停下来"
    assert len(data["candidates"]) >= 2
    assert data["status"] == "pending_human_decision"
    assert all(data["five_gate_results"].values())
    assert data["auto_publish"] is False
    assert data["may_clear_safety_signal"] is False
    assert data["human_review_completed"] is False


def test_human_only_and_safety_cases_default_to_deny(tmp_path, monkeypatch):
    app = _app(tmp_path, monkeypatch)
    headers = _seed(app)
    client = app.test_client()
    human_only = _create(
        client,
        headers["researcher-f16"],
        task_type="assessment_interpretation",
        key="human-only",
    )
    assert human_only.status_code == 409
    assert human_only.get_json()["error"]["code"] == "human_only_task"
    unsafe = _create(
        client,
        headers["researcher-f16"],
        case_id="case-f16-risk",
        key="unsafe",
    )
    assert unsafe.status_code == 409
    assert unsafe.get_json()["error"]["code"] == "ai_assist_scope_blocked"


def test_human_can_modify_or_choose_none_fit_without_creating_feedback(tmp_path, monkeypatch):
    app = _app(tmp_path, monkeypatch)
    headers = _seed(app)
    client = app.test_client()
    created = _create(client, headers["researcher-f16"]).get_json()["data"]
    modified = client.patch(
        f"/api/therapeutic-assessment/ai-assist/candidates/{created['id']}",
        headers={**headers["researcher-f16"], "Idempotency-Key": "f16-modify"},
        json={
            "decision": "modified",
            "selected_candidate_index": 0,
            "modified_text": "我想先核对：停下来之前，你最先注意到的是什么？",
            "expected_version": created["version"],
        },
    )
    assert modified.status_code == 200
    item = modified.get_json()["data"]
    assert item["status"] == "modified"
    assert item["reviewer_text"].startswith("我想先核对")
    with app.app_context():
        from database import get_connection

        with get_connection() as conn:
            assert conn.execute(
                "SELECT COUNT(*) AS n FROM therapeutic_assessment_feedback_versions"
            ).fetchone()["n"] == 0
            assert conn.execute(
                "SELECT safety_state FROM therapeutic_assessment_cases WHERE id = 'case-f16'"
            ).fetchone()["safety_state"] == "low_risk"

    second = _create(client, headers["researcher-f16"], key="second").get_json()["data"]
    none_fit = client.patch(
        f"/api/therapeutic-assessment/ai-assist/candidates/{second['id']}",
        headers={**headers["researcher-f16"], "Idempotency-Key": "f16-none-fit"},
        json={"decision": "none_fit", "expected_version": second["version"]},
    )
    assert none_fit.status_code == 200
    assert none_fit.get_json()["data"]["status"] == "none_fit"


def test_candidate_writes_are_idempotent_and_versioned(tmp_path, monkeypatch):
    app = _app(tmp_path, monkeypatch)
    headers = _seed(app)
    client = app.test_client()
    first = _create(client, headers["supervisor-f16"], key="same").get_json()["data"]
    replay = _create(client, headers["supervisor-f16"], key="same").get_json()["data"]
    assert replay["id"] == first["id"]
    conflict = client.patch(
        f"/api/therapeutic-assessment/ai-assist/candidates/{first['id']}",
        headers={**headers["supervisor-f16"], "Idempotency-Key": "f16-stale"},
        json={"decision": "rejected", "expected_version": first["version"] + 1},
    )
    assert conflict.status_code == 409


def test_migration_plan_apply_verify_and_rollback(tmp_path):
    database_path = tmp_path / "f16-migration.sqlite3"
    script = BACKEND / "scripts" / "migrate_task38_f16_ai_assist_candidates.py"
    for action in ("plan", "apply", "verify", "rollback"):
        result = subprocess.run(
            [sys.executable, str(script), action, "--database-path", str(database_path)],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )
        assert result.returncode == 0, result.stdout + result.stderr
