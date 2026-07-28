import importlib
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"


def _app(tmp_path, monkeypatch):
    sys.path.insert(0, str(BACKEND))
    for name in list(sys.modules):
        if name in {"app", "config", "database", "models"} or name.startswith(
            ("routes.", "services.")
        ):
            sys.modules.pop(name, None)
    monkeypatch.setenv("APP_ENV", "testing")
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "b02.sqlite3"))
    return importlib.import_module("app").app


def _seed(app):
    specs = [
        ("admin-b02", "admin"),
        ("supervisor-b02", "supervisor"),
        ("researcher-b02", "researcher"),
        ("parent-b02", "parent"),
    ]
    with app.app_context():
        database = importlib.import_module("database")
        auth_utils = importlib.import_module("routes.auth_utils")
        with database.get_connection() as conn:
            now = database.now_iso()
            for actor_id, role in specs:
                conn.execute(
                    "INSERT INTO users (id, nickname, role, source, status, created_at, updated_at) "
                    "VALUES (?, ?, ?, 'test', 'active', ?, ?)",
                    (actor_id, actor_id, role, now, now),
                )
            conn.execute(
                """
                INSERT INTO therapeutic_assessment_cases (
                    id, participant_user_id, assessment_question, shared_scope_json,
                    consent_status, status, risk_level, readiness_level,
                    complexity_scope, safety_state, created_by, created_at, updated_at
                ) VALUES (
                    'case-b02', 'parent-b02', '想理解一次沟通', '["question"]',
                    'active', 'active', 'low', 'L1',
                    'individual_adult_low_risk', 'low_risk',
                    'parent-b02', ?, ?
                )
                """,
                (now, now),
            )
            for index, (user_id, task_code, level) in enumerate(
                [
                    ("researcher-b02", "feedback_review", "T3"),
                    ("supervisor-b02", "feedback_review", "T3"),
                ],
                start=1,
            ):
                conn.execute(
                    """
                    INSERT INTO therapeutic_assessment_authorizations (
                        id, user_id, competency_level, task_code, scope_json,
                        supervisor_user_id, evidence_ref, starts_at, expires_at,
                        status, version, granted_by, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, '{"case_ids":["case-b02"]}',
                        'supervisor-b02', 'test-evidence', ?, ?,
                        'active', 1, 'admin-b02', ?, ?)
                    """,
                    (
                        f"auth-b02-{index}",
                        user_id,
                        level,
                        task_code,
                        "2020-01-01T00:00:00+00:00",
                        "2099-01-01T00:00:00+00:00",
                        now,
                        now,
                    ),
                )
            conn.commit()
        return {
            actor_id: {
                "Authorization": "Bearer "
                + auth_utils.generate_auth_token({"id": actor_id, "role": role})
            }
            for actor_id, role in specs
        }


def _shift(client, headers, user_id, queue_types, key):
    now = datetime.now(timezone.utc)
    return client.post(
        "/api/therapeutic-assessment/duty-shifts",
        headers={**headers, "Idempotency-Key": key},
        json={
            "user_id": user_id,
            "supervisor_user_id": "supervisor-b02",
            "queue_types": queue_types,
            "scope": {"case_ids": ["case-b02"]},
            "starts_at": (now - timedelta(hours=1)).isoformat(),
            "expires_at": (now + timedelta(hours=8)).isoformat(),
            "evidence_ref": "duty-plan-b02",
        },
    )


def test_queue_claim_requires_scope_competency_duty_and_independent_reviewer(
    tmp_path, monkeypatch
):
    app = _app(tmp_path, monkeypatch)
    headers = _seed(app)
    client = app.test_client()
    assert _shift(
        client, headers["admin-b02"], "researcher-b02", ["review"], "shift-researcher"
    ).status_code == 201
    assert _shift(
        client, headers["admin-b02"], "supervisor-b02", ["review"], "shift-supervisor"
    ).status_code == 201
    created = client.post(
        "/api/therapeutic-assessment/cases/case-b02/work-queue",
        headers={**headers["admin-b02"], "Idempotency-Key": "queue-review"},
        json={"queue_type": "review", "drafted_by": "researcher-b02"},
    ).get_json()["data"]
    visible = client.get(
        "/api/therapeutic-assessment/work-queue",
        headers=headers["researcher-b02"],
    ).get_json()["data"]
    assert [item["id"] for item in visible["items"]] == [created["id"]]
    same_person = client.post(
        f"/api/therapeutic-assessment/work-queue/{created['id']}/claim",
        headers={**headers["researcher-b02"], "Idempotency-Key": "claim-same"},
        json={"expected_version": created["version"]},
    )
    assert same_person.status_code == 409
    assert same_person.get_json()["error"]["code"] == "independent_reviewer_required"
    claimed = client.post(
        f"/api/therapeutic-assessment/work-queue/{created['id']}/claim",
        headers={**headers["supervisor-b02"], "Idempotency-Key": "claim-supervisor"},
        json={"expected_version": created["version"]},
    )
    assert claimed.status_code == 200
    assert claimed.get_json()["data"]["assigned_user_id"] == "supervisor-b02"


def test_urgent_queue_without_matching_duty_pauses_and_never_downgrades(
    tmp_path, monkeypatch
):
    app = _app(tmp_path, monkeypatch)
    headers = _seed(app)
    client = app.test_client()
    created = client.post(
        "/api/therapeutic-assessment/cases/case-b02/work-queue",
        headers={**headers["admin-b02"], "Idempotency-Key": "queue-risk"},
        json={"queue_type": "risk"},
    ).get_json()["data"]
    monitored = client.post(
        "/api/therapeutic-assessment/work-queue/monitor",
        headers=headers["admin-b02"],
    ).get_json()["data"]
    assert monitored["paused"] == 1
    assert monitored["unattended_urgent_count"] == 1
    denied = client.post(
        f"/api/therapeutic-assessment/work-queue/{created['id']}/claim",
        headers={**headers["supervisor-b02"], "Idempotency-Key": "claim-risk"},
        json={"expected_version": created["version"]},
    )
    assert denied.status_code == 409
    assert denied.get_json()["error"]["code"] == "queue_runtime_paused"
    assert client.get(
        "/api/therapeutic-assessment/work-queue",
        headers=headers["parent-b02"],
    ).status_code == 403


def test_scope_change_and_missing_duty_fail_closed(tmp_path, monkeypatch):
    app = _app(tmp_path, monkeypatch)
    headers = _seed(app)
    client = app.test_client()
    created = client.post(
        "/api/therapeutic-assessment/cases/case-b02/work-queue",
        headers={**headers["admin-b02"], "Idempotency-Key": "queue-scope"},
        json={"queue_type": "review"},
    ).get_json()["data"]
    with app.app_context():
        database = importlib.import_module("database")
        with database.get_connection() as conn:
            conn.execute(
                "UPDATE therapeutic_assessment_cases SET readiness_level = 'L2' WHERE id = 'case-b02'"
            )
            conn.commit()
    denied = client.post(
        f"/api/therapeutic-assessment/work-queue/{created['id']}/claim",
        headers={**headers["supervisor-b02"], "Idempotency-Key": "claim-scope"},
        json={"expected_version": created["version"]},
    )
    assert denied.status_code == 409
    assert denied.get_json()["error"]["code"] == "object_scope_changed"


def test_policy_keeps_showcase_and_automatic_downgrade_disabled():
    import json

    policy = json.loads(
        (ROOT / "content" / "therapeutic_assessment_queue_policy.json").read_text(
            encoding="utf-8"
        )
    )
    assert set(policy["queue_types"]) == {
        "review",
        "information",
        "feedback",
        "risk",
        "supervision",
    }
    assert policy["temporary_showcase_bypass_changes_write_permission"] is False
    assert policy["automatic_role_downgrade_allowed"] is False
