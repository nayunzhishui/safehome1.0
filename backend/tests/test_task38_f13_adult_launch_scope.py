import importlib
import json
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
POLICY = ROOT / "content" / "therapeutic_assessment_adult_launch_policy.json"


def _app(tmp_path, monkeypatch):
    sys.path.insert(0, str(BACKEND))
    for name in list(sys.modules):
        if name in {"app", "config", "database", "models"} or name.startswith(
            ("routes.", "services.")
        ):
            sys.modules.pop(name, None)
    monkeypatch.setenv("APP_ENV", "testing")
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "f13.sqlite3"))
    monkeypatch.setenv("CONTENT_DIR", str(ROOT / "content"))
    return importlib.import_module("app").app


def _seed(app):
    users = {
        "p-f13": "parent",
        "other-f13": "parent",
        "r-f13": "researcher",
        "s-f13": "supervisor",
        "a-f13": "admin",
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
                VALUES ('case-f13', 'p-f13', '我想理解最近一次沟通', '["question"]',
                        'active', 'open', 'low', 'submitted', 'observations_only',
                        'low_risk', 'individual_adult_low_risk', 'L0', 'r-f13',
                        1, 'p-f13', ?, ?)""",
                (now, now),
            )
            conn.commit()
        return {
            user_id: {
                "Authorization": f"Bearer {generate_auth_token({'id': user_id, 'role': role})}"
            }
            for user_id, role in users.items()
        }


def _eligible_payload():
    return {
        "requested_level": "L1",
        "age_band": "adult",
        "voluntary_participation": True,
        "data_scope": "single_person",
        "urgency": "non_urgent",
        "concern_scope": "ordinary_relationship_stress",
        "excluded_signals": [],
        "acknowledged_notices": [
            "waiting_time",
            "withdrawal",
            "privacy",
            "confidentiality_exceptions",
            "complaint_path",
        ],
        "expected_case_version": 1,
    }


def test_policy_limits_first_release_and_excludes_high_challenge_methods():
    payload = json.loads(POLICY.read_text(encoding="utf-8"))
    assert payload["schema"] == "safehome.therapeutic-assessment.adult-launch.v1"
    assert payload["allowed_levels"] == ["L1", "L2"]
    assert payload["eligible_age_bands"] == ["adult"]
    assert payload["allowed_data_scopes"] == ["single_person"]
    assert {"AIS", "FIS", "layer_3", "trauma_activation", "family_confrontation"} <= set(
        payload["excluded_methods"]
    )
    assert payload["production_release_approved"] is False


def test_participant_can_record_eligible_scope_with_idempotency(tmp_path, monkeypatch):
    app = _app(tmp_path, monkeypatch)
    headers = _seed(app)
    client = app.test_client()
    first = client.post(
        "/api/therapeutic-assessment/cases/case-f13/launch-screenings",
        headers={**headers["p-f13"], "Idempotency-Key": "f13-eligible"},
        json=_eligible_payload(),
    )
    replay = client.post(
        "/api/therapeutic-assessment/cases/case-f13/launch-screenings",
        headers={**headers["p-f13"], "Idempotency-Key": "f13-eligible"},
        json=_eligible_payload(),
    )
    assert first.status_code == 201
    assert replay.status_code == 200
    data = first.get_json()["data"]
    assert data["decision"] == "eligible_l1_l2"
    assert data["production_release_approved"] is False
    assert data["external_gates_required"] is True
    assert replay.get_json()["data"]["id"] == data["id"]


def test_minor_multi_party_urgent_and_excluded_signal_are_outside_scope(tmp_path, monkeypatch):
    app = _app(tmp_path, monkeypatch)
    headers = _seed(app)
    client = app.test_client()
    payload = _eligible_payload()
    payload.update(
        {
            "age_band": "minor",
            "data_scope": "multi_party",
            "urgency": "urgent",
            "excluded_signals": ["coercive_control"],
        }
    )
    response = client.post(
        "/api/therapeutic-assessment/cases/case-f13/launch-screenings",
        headers={**headers["p-f13"], "Idempotency-Key": "f13-excluded"},
        json=payload,
    )
    assert response.status_code == 201
    data = response.get_json()["data"]
    assert data["decision"] == "outside_first_release_scope"
    assert {
        "minor_or_unknown_age",
        "multi_party_data",
        "urgent_or_emergency",
        "excluded_safety_signal",
    } <= set(data["reason_codes"])
    assert data["recommended_route"] == "human_scope_review"


def test_unknown_or_incomplete_answers_default_to_human_review(tmp_path, monkeypatch):
    app = _app(tmp_path, monkeypatch)
    headers = _seed(app)
    client = app.test_client()
    payload = _eligible_payload()
    payload["age_band"] = "unknown"
    payload["acknowledged_notices"] = ["waiting_time"]
    response = client.post(
        "/api/therapeutic-assessment/cases/case-f13/launch-screenings",
        headers={**headers["p-f13"], "Idempotency-Key": "f13-unknown"},
        json=payload,
    )
    assert response.status_code == 201
    data = response.get_json()["data"]
    assert data["decision"] == "human_review_required"
    assert "missing_required_notices" in data["reason_codes"]
    assert "unknown_age" in data["reason_codes"]


def test_object_scope_and_researcher_assignment_are_enforced(tmp_path, monkeypatch):
    app = _app(tmp_path, monkeypatch)
    headers = _seed(app)
    client = app.test_client()
    denied = client.post(
        "/api/therapeutic-assessment/cases/case-f13/launch-screenings",
        headers={**headers["other-f13"], "Idempotency-Key": "f13-cross-object"},
        json=_eligible_payload(),
    )
    assert denied.status_code == 403
    created = client.post(
        "/api/therapeutic-assessment/cases/case-f13/launch-screenings",
        headers={**headers["p-f13"], "Idempotency-Key": "f13-readable"},
        json=_eligible_payload(),
    )
    assert created.status_code == 201
    researcher = client.get(
        "/api/therapeutic-assessment/cases/case-f13/launch-screenings/latest",
        headers=headers["r-f13"],
    )
    supervisor = client.get(
        "/api/therapeutic-assessment/cases/case-f13/launch-screenings/latest",
        headers=headers["s-f13"],
    )
    assert researcher.status_code == 200
    assert supervisor.status_code == 200


def test_version_conflict_and_withdrawn_case_do_not_create_screening(tmp_path, monkeypatch):
    app = _app(tmp_path, monkeypatch)
    headers = _seed(app)
    client = app.test_client()
    payload = _eligible_payload()
    payload["expected_case_version"] = 99
    conflict = client.post(
        "/api/therapeutic-assessment/cases/case-f13/launch-screenings",
        headers={**headers["p-f13"], "Idempotency-Key": "f13-version"},
        json=payload,
    )
    assert conflict.status_code == 409
    with app.app_context():
        from database import get_connection

        with get_connection() as conn:
            conn.execute(
                "UPDATE therapeutic_assessment_cases SET status = 'withdrawn', consent_status = 'withdrawn' WHERE id = 'case-f13'"
            )
            conn.commit()
    withdrawn = client.post(
        "/api/therapeutic-assessment/cases/case-f13/launch-screenings",
        headers={**headers["p-f13"], "Idempotency-Key": "f13-withdrawn"},
        json=_eligible_payload(),
    )
    assert withdrawn.status_code == 409


def test_status_endpoint_shared_and_clients_expose_launch_contract(tmp_path, monkeypatch):
    app = _app(tmp_path, monkeypatch)
    headers = _seed(app)
    client = app.test_client()
    response = client.get(
        "/api/therapeutic-assessment/launch-scope",
        headers=headers["p-f13"],
    )
    assert response.status_code == 200
    data = response.get_json()["data"]
    assert data["allowed_levels"] == ["L1", "L2"]
    assert data["production_release_approved"] is False
    shared = (ROOT / "shared/types/api.ts").read_text(encoding="utf-8")
    web = (ROOT / "apps/web/src/services/safehomeApi.ts").read_text(encoding="utf-8")
    mini = (ROOT / "apps/miniprogram/services/api.js").read_text(encoding="utf-8")
    assert "TherapeuticAssessmentAdultLaunchScope" in shared
    assert "getTherapeuticAssessmentAdultLaunchScope" in web
    assert "submitTherapeuticAssessmentLaunchScreening" in mini


def test_migration_plan_apply_verify_and_rollback(tmp_path):
    env = os.environ.copy()
    env.update(
        {
            "APP_ENV": "testing",
            "DATABASE_PATH": str(tmp_path / "migration-f13.sqlite3"),
            "CONTENT_DIR": str(ROOT / "content"),
            "PYTHONPATH": str(BACKEND),
        }
    )
    script = BACKEND / "scripts" / "migrate_task38_f13_adult_launch_scope.py"
    plan = subprocess.run(
        [sys.executable, str(script), "plan"],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    apply = subprocess.run(
        [sys.executable, str(script), "apply"],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    verify = subprocess.run(
        [sys.executable, str(script), "verify"],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    rollback = subprocess.run(
        [sys.executable, str(script), "rollback"],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert plan.returncode == 0
    assert apply.returncode == verify.returncode == rollback.returncode == 0
    assert json.loads(verify.stdout)["ok"] is True
    assert json.loads(rollback.stdout)["history_deleted"] is False
