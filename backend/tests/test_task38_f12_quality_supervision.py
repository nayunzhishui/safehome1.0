import importlib
import os
import subprocess
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
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "f12.sqlite3"))
    monkeypatch.setenv("CONTENT_DIR", str(ROOT / "content"))
    return importlib.import_module("app").app


def _seed(app):
    users = {
        "p-f12": "parent",
        "r-f12": "researcher",
        "s-f12": "supervisor",
        "a-f12": "admin",
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
            conn.commit()
        return {
            user_id: {
                "Authorization": f"Bearer {generate_auth_token({'id': user_id, 'role': role})}"
            }
            for user_id, role in users.items()
        }


def _grant(client, headers, user_id, task_code, key):
    now = datetime.now(timezone.utc)
    return client.post(
        "/api/therapeutic-assessment/competency/authorizations",
        headers={**headers["a-f12"], "Idempotency-Key": key},
        json={
            "user_id": user_id,
            "competency_level": "T3" if task_code != "feedback_draft" else "T2",
            "task_code": task_code,
            "scope": {"case_ids": [headers["case_id"]]},
            "supervisor_user_id": "a-f12",
            "evidence_ref": f"evidence:{key}",
            "starts_at": (now - timedelta(minutes=1)).isoformat(),
            "expires_at": (now + timedelta(days=30)).isoformat(),
        },
    )


def _create_ready_case(client, headers, key="f12-case"):
    created = client.post(
        "/api/therapeutic-assessment/cases",
        headers={**headers["p-f12"], "Idempotency-Key": key},
        json={
            "assessment_question": "我想理解一次沟通中停下来的时刻",
            "shared_scope": ["question"],
            "consent": True,
        },
    )
    assert created.status_code == 201
    case_id = created.get_json()["data"]["id"]
    headers["case_id"] = case_id
    assigned = client.post(
        f"/api/therapeutic-assessment/cases/{case_id}/assign",
        headers={**headers["s-f12"], "Idempotency-Key": f"{key}-assign"},
        json={"researcher_id": "r-f12"},
    )
    ready = client.post(
        f"/api/therapeutic-assessment/cases/{case_id}/readiness",
        headers={**headers["s-f12"], "Idempotency-Key": f"{key}-ready"},
        json={
            "qualification_evidence_ref": "evidence:q-f12",
            "supervision_evidence_ref": "evidence:s-f12",
            "ethics_evidence_ref": "evidence:e-f12",
        },
    )
    assert assigned.status_code == 200
    assert ready.status_code == 200
    return ready.get_json()["data"]


def _feedback_payload():
    return {
        "source": "human",
        "feedback_layer": "layer_1",
        "letter_title": "给你的阶段性反馈",
        "observations": ["你记录了当时先停下来再回应"],
        "evidence": ["participant:self-report"],
        "alternatives": ["也可能与当时需要整理思路有关"],
        "uncertainty": "目前只有一次记录，需要和你核对。",
        "next_step": "可以选择一个愿意继续观察的小动作。",
        "human_discussion": ["这份理解哪里像，哪里不像？"],
        "participant_content": "从这次记录看，你先停下来再回应；这只是当前理解，可以不同意。",
    }


def _send_feedback(client, headers):
    for user_id, task_code, key in (
        ("r-f12", "feedback_draft", "f12-grant-draft"),
        ("s-f12", "feedback_review", "f12-grant-review"),
    ):
        granted = _grant(client, headers, user_id, task_code, key)
        assert granted.status_code == 201
    draft = client.post(
        f"/api/therapeutic-assessment/cases/{headers['case_id']}/feedback-versions",
        headers={**headers["r-f12"], "Idempotency-Key": "f12-feedback"},
        json=_feedback_payload(),
    )
    reviewed = client.post(
        f"/api/therapeutic-assessment/feedback-versions/{draft.get_json()['data']['id']}/review",
        headers={**headers["s-f12"], "Idempotency-Key": "f12-review"},
        json={"decision": "approved"},
    )
    sent = client.post(
        f"/api/therapeutic-assessment/feedback-versions/{draft.get_json()['data']['id']}/send",
        headers={**headers["s-f12"], "Idempotency-Key": "f12-send"},
    )
    assert draft.status_code == 201
    assert reviewed.status_code == 200
    assert sent.status_code == 200
    return sent.get_json()["data"]


def _dimensions(concern=False):
    names = (
        "question_quality",
        "evidence_sufficiency",
        "authorization",
        "language",
        "participant_recognition",
        "action_fit",
    )
    return {
        name: {
            "status": "concern" if concern and name == "language" else "pass",
            "note": "发现需要修复的表达" if concern and name == "language" else "",
            "evidence_ref": "feedback:participant_content" if concern and name == "language" else "",
        }
        for name in names
    }


def test_schema_041_adds_quality_supervision_tables(tmp_path, monkeypatch):
    app = _app(tmp_path, monkeypatch)
    with app.app_context():
        from database import CURRENT_SCHEMA_NAME, CURRENT_SCHEMA_VERSION, get_connection

        with get_connection() as conn:
            tables = {
                row["name"]
                for row in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
            }
        assert {
            "therapeutic_assessment_quality_reviews",
            "therapeutic_assessment_quality_incidents",
            "therapeutic_assessment_quality_events",
            "therapeutic_assessment_quality_runtime",
        }.issubset(tables)
        assert CURRENT_SCHEMA_VERSION >= "2026_07_28_041"
        assert CURRENT_SCHEMA_NAME == "therapeutic_assessment_quality_supervision"


def test_l2_feedback_enters_quality_queue_and_requires_task_grant(tmp_path, monkeypatch):
    app = _app(tmp_path, monkeypatch)
    headers = _seed(app)
    client = app.test_client()
    _create_ready_case(client, headers)
    feedback = _send_feedback(client, headers)

    denied = client.get(
        "/api/therapeutic-assessment/quality/reviews",
        headers=headers["s-f12"],
    )
    granted = _grant(client, headers, "a-f12", "quality_review", "f12-grant-quality")
    queue = client.get(
        "/api/therapeutic-assessment/quality/reviews",
        headers=headers["a-f12"],
    )

    assert denied.status_code == 200
    assert denied.get_json()["data"]["items"] == []
    assert granted.status_code == 201
    assert queue.status_code == 200
    item = queue.get_json()["data"]["items"][0]
    assert item["feedback_id"] == feedback["id"]
    assert item["sample_reason"] == "mandatory_l2"
    assert queue.get_json()["data"]["runtime"]["paused"] is False


def test_independent_review_and_remediation_preserve_error_case(tmp_path, monkeypatch):
    app = _app(tmp_path, monkeypatch)
    headers = _seed(app)
    client = app.test_client()
    _create_ready_case(client, headers)
    _send_feedback(client, headers)
    assert _grant(client, headers, "a-f12", "quality_review", "f12-quality").status_code == 201
    item = client.get(
        "/api/therapeutic-assessment/quality/reviews",
        headers=headers["a-f12"],
    ).get_json()["data"]["items"][0]
    claimed = client.post(
        f"/api/therapeutic-assessment/quality/reviews/{item['id']}/claim",
        headers={**headers["a-f12"], "Idempotency-Key": "f12-claim"},
        json={"expected_version": item["version"]},
    )
    completed = client.post(
        f"/api/therapeutic-assessment/quality/reviews/{item['id']}/complete",
        headers={**headers["a-f12"], "Idempotency-Key": "f12-complete"},
        json={
            "expected_version": claimed.get_json()["data"]["version"],
            "dimensions": _dimensions(concern=True),
            "decision": "remediation_required",
            "remediation_summary": "保留原记录，补充影响分析并完成独立修复。",
        },
    )
    assert _grant(
        client,
        headers,
        "a-f12",
        "quality_incident_analysis",
        "f12-remediation-analysis-grant",
    ).status_code == 201
    incidents = client.get(
        "/api/therapeutic-assessment/quality/incidents",
        headers=headers["a-f12"],
    )

    assert claimed.status_code == 200
    assert completed.status_code == 200
    assert completed.get_json()["data"]["status"] == "remediation_required"
    assert completed.get_json()["data"]["incident_id"]
    assert incidents.status_code == 200
    assert incidents.get_json()["data"]["items"][0]["source_type"] == "quality_sample"


def test_participant_complaint_has_impact_analysis_independent_resolution_and_message(
    tmp_path, monkeypatch
):
    app = _app(tmp_path, monkeypatch)
    headers = _seed(app)
    client = app.test_client()
    _create_ready_case(client, headers)
    feedback = _send_feedback(client, headers)
    reported = client.post(
        f"/api/therapeutic-assessment/cases/{headers['case_id']}/quality-incidents",
        headers={**headers["p-f12"], "Idempotency-Key": "f12-report"},
        json={
            "feedback_id": feedback["id"],
            "category": "correction_request",
            "description": "其中一句不像我的实际感受。",
            "requested_resolution": "希望记录这处不同并重新核对。",
        },
    )
    assert _grant(
        client, headers, "s-f12", "quality_incident_analysis", "f12-analysis-grant"
    ).status_code == 201
    assert _grant(
        client, headers, "a-f12", "quality_incident_resolution", "f12-resolution-grant"
    ).status_code == 201
    incident = reported.get_json()["data"]
    analyzed = client.post(
        f"/api/therapeutic-assessment/quality/incidents/{incident['id']}/impact-analysis",
        headers={**headers["s-f12"], "Idempotency-Key": "f12-analysis"},
        json={
            "expected_version": incident["version"],
            "impact_analysis": {
                "severity": "low",
                "affected_scope": "single_feedback",
                "affected_participant_count": 1,
                "immediate_action": "保留异议并停止沿用该句。",
                "evidence_refs": [f"feedback:{feedback['id']}"],
            },
        },
    )
    resolved = client.post(
        f"/api/therapeutic-assessment/quality/incidents/{incident['id']}/resolve",
        headers={**headers["a-f12"], "Idempotency-Key": "f12-resolution"},
        json={
            "expected_version": analyzed.get_json()["data"]["version"],
            "resolution_action": "no_change",
            "resolution_summary": "已记录你的不同理解，原反馈保留为历史，不再作为确定结论使用。",
        },
    )

    with app.app_context():
        from database import get_connection

        with get_connection() as conn:
            message = conn.execute(
                "SELECT * FROM messages WHERE source_type = 'therapeutic_assessment_quality_incident' AND source_id = ?",
                (incident["id"],),
            ).fetchone()
    assert reported.status_code == 201
    assert analyzed.status_code == 200
    assert resolved.status_code == 200
    assert resolved.get_json()["data"]["notification_status"] == "sent"
    assert message is not None


def test_overdue_queue_pauses_only_new_case_intake_and_retry_recovers(tmp_path, monkeypatch):
    app = _app(tmp_path, monkeypatch)
    headers = _seed(app)
    client = app.test_client()
    with app.app_context():
        from database import get_connection, now_iso

        now = now_iso()
        old = (datetime.now(timezone.utc) - timedelta(days=2)).isoformat()
        with get_connection() as conn:
            for index in range(3):
                conn.execute(
                    """
                    INSERT INTO therapeutic_assessment_quality_reviews (
                        id, case_id, feedback_id, service_level, sample_reason,
                        status, due_at, version, created_at, updated_at
                    ) VALUES (?, ?, ?, 'L2', 'test_overdue', 'pending', ?, 1, ?, ?)
                    """,
                    (f"overdue-{index}", "case-test", f"feedback-test-{index}", old, now, now),
                )
            conn.commit()
    paused = client.post(
        "/api/therapeutic-assessment/cases",
        headers={**headers["p-f12"], "Idempotency-Key": "f12-paused-case"},
        json={
            "assessment_question": "想记录一次沟通",
            "shared_scope": ["question"],
            "consent": True,
        },
    )
    with app.app_context():
        from database import get_connection

        with get_connection() as conn:
            conn.execute(
                "UPDATE therapeutic_assessment_quality_reviews SET status = 'passed'"
            )
            conn.commit()
    recovered = client.post(
        "/api/therapeutic-assessment/cases",
        headers={**headers["p-f12"], "Idempotency-Key": "f12-paused-case"},
        json={
            "assessment_question": "想记录一次沟通",
            "shared_scope": ["question"],
            "consent": True,
        },
    )
    assert paused.status_code == 503
    assert paused.get_json()["error"]["code"] == "quality_queue_paused"
    assert recovered.status_code == 201


def test_migration_plan_verify_and_rollback_are_safe(tmp_path, monkeypatch):
    app = _app(tmp_path, monkeypatch)
    env = os.environ.copy()
    env.update(
        {
            "APP_ENV": "testing",
            "DATABASE_PATH": str(tmp_path / "f12.sqlite3"),
            "CONTENT_DIR": str(ROOT / "content"),
        }
    )
    script = BACKEND / "scripts" / "migrate_task38_f12_quality_supervision.py"
    for action in ("plan", "verify", "rollback"):
        result = subprocess.run(
            [sys.executable, str(script), action],
            cwd=ROOT,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, result.stderr
    assert app is not None
