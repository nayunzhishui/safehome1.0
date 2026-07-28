import importlib
import sys
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"


def _app(tmp_path, monkeypatch, *, lifecycle_enabled=True):
    sys.path.insert(0, str(BACKEND))
    for name in list(sys.modules):
        if name in {"app", "config", "database", "models"} or name.startswith(("routes.", "services.")):
            sys.modules.pop(name, None)
    monkeypatch.setenv("APP_ENV", "testing")
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "b04.sqlite3"))
    monkeypatch.setenv("CONTENT_DIR", str(ROOT / "content"))
    monkeypatch.setenv(
        "THERAPEUTIC_ASSESSMENT_LIFECYCLE_ENABLED",
        "1" if lifecycle_enabled else "0",
    )
    return importlib.import_module("app").app


def _seed(app):
    users = {
        "p-b04": "parent",
        "p2-b04": "parent",
        "r-b04": "researcher",
        "s-b04": "supervisor",
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
            for authorization_id, user_id, level, task_code in (
                ("auth-b04-draft", "r-b04", "T2", "feedback_draft"),
                ("auth-b04-review", "s-b04", "T3", "feedback_review"),
            ):
                conn.execute(
                    """
                    INSERT INTO therapeutic_assessment_authorizations (
                        id, user_id, competency_level, task_code, scope_json,
                        supervisor_user_id, evidence_ref, starts_at, expires_at,
                        status, version, granted_by, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, 's-b04', ?, ?,
                        '2099-01-01T00:00:00+00:00', 'active', 1, 's-b04', ?, ?)
                    """,
                    (
                        authorization_id,
                        user_id,
                        level,
                        task_code,
                        '{"complexity_scopes":["individual_adult_low_risk"]}',
                        f"test-evidence:{authorization_id}",
                        now,
                        now,
                        now,
                    ),
                )
            conn.commit()
        return {
            user_id: {
                "Authorization": f"Bearer {generate_auth_token({'id': user_id, 'role': role})}"
            }
            for user_id, role in users.items()
        }


def _feedback_payload():
    return {
        "source": "human",
        "feedback_layer": "layer_1",
        "letter_title": "给你的阶段性反馈",
        "observations": ["你记录了先停下来再回应"],
        "evidence": ["participant:self-report"],
        "alternatives": ["也可能是当时需要整理思路"],
        "uncertainty": "目前只依据这一次记录，仍需要核对。",
        "next_step": "可以选择一个自己愿意尝试的小动作。",
        "human_discussion": ["哪些部分贴近你的体验？"],
        "participant_content": "从这次记录看，你先停下来再回应；这只是当前理解，可以不同意。",
    }


def _ready_case(client, headers):
    created = client.post(
        "/api/therapeutic-assessment/cases",
        headers={**headers["p-b04"], "Idempotency-Key": "b04-case"},
        json={
            "assessment_question": "我想理解一次沟通",
            "shared_scope": ["question"],
            "consent": True,
        },
    )
    case = created.get_json()["data"]
    assert created.status_code == 201
    assert client.post(
        f"/api/therapeutic-assessment/cases/{case['id']}/assign",
        headers={**headers["s-b04"], "Idempotency-Key": "b04-assign"},
        json={"researcher_id": "r-b04"},
    ).status_code == 200
    assert client.post(
        f"/api/therapeutic-assessment/cases/{case['id']}/readiness",
        headers={**headers["s-b04"], "Idempotency-Key": "b04-ready"},
        json={
            "qualification_evidence_ref": "evidence:qualification-b04",
            "supervision_evidence_ref": "evidence:supervision-b04",
            "ethics_evidence_ref": "evidence:ethics-b04",
        },
    ).status_code == 200
    return case["id"]


def _draft_review_send(client, headers, case_id, prefix):
    draft = client.post(
        f"/api/therapeutic-assessment/cases/{case_id}/feedback-versions",
        headers={**headers["r-b04"], "Idempotency-Key": f"{prefix}-draft"},
        json=_feedback_payload(),
    )
    assert draft.status_code == 201
    feedback = draft.get_json()["data"]
    assert client.post(
        f"/api/therapeutic-assessment/feedback-versions/{feedback['id']}/review",
        headers={**headers["s-b04"], "Idempotency-Key": f"{prefix}-review"},
        json={"decision": "approved"},
    ).status_code == 200
    assert client.post(
        f"/api/therapeutic-assessment/feedback-versions/{feedback['id']}/send",
        headers={**headers["s-b04"], "Idempotency-Key": f"{prefix}-send"},
    ).status_code == 200
    return feedback


def test_feedback_lifecycle_connects_draft_review_revision_action_followup_and_archive(
    tmp_path, monkeypatch
):
    app = _app(tmp_path, monkeypatch)
    headers = _seed(app)
    client = app.test_client()
    case_id = _ready_case(client, headers)
    first = _draft_review_send(client, headers, case_id, "b04-first")

    response = client.post(
        f"/api/therapeutic-assessment/feedback-versions/{first['id']}/responses",
        headers={**headers["p-b04"], "Idempotency-Key": "b04-response"},
        json={"recognition": "not_like", "disagreement_note": "这与我当时的感受不完全一致。"},
    )
    assert response.status_code == 201
    revised = client.post(
        f"/api/therapeutic-assessment/feedback-versions/{first['id']}/revise",
        headers={**headers["r-b04"], "Idempotency-Key": "b04-revise"},
        json={
            **_feedback_payload(),
            "revision_reason": "根据参与者核对意见修改",
            "participant_content": "你指出原来的理解不完全贴近；这一版保留不确定性并继续核对。",
            "expected_lifecycle_version": 1,
        },
    )
    assert revised.status_code == 201
    second = revised.get_json()["data"]
    assert client.post(
        f"/api/therapeutic-assessment/feedback-versions/{second['id']}/review",
        headers={**headers["s-b04"], "Idempotency-Key": "b04-second-review"},
        json={"decision": "approved"},
    ).status_code == 200
    assert client.post(
        f"/api/therapeutic-assessment/feedback-versions/{second['id']}/send",
        headers={**headers["s-b04"], "Idempotency-Key": "b04-second-send"},
    ).status_code == 200
    action = client.post(
        f"/api/therapeutic-assessment/cases/{case_id}/actions",
        headers={**headers["p-b04"], "Idempotency-Key": "b04-action"},
        json={
            "feedback_version_id": second["id"],
            "action_text": "下一次回应前先停顿三秒。",
            "purpose_text": "给自己一点整理思路的空间。",
            "planned_date": date.today().isoformat(),
            "reminder_mode": "in_app",
            "reminder_privacy": "generic_preview",
            "stop_conditions": ["如果我不再愿意，就先停止。"],
            "setback_plan": "只记录阻碍，不责备自己。",
            "voluntary_confirmed": True,
            "reversible_confirmed": True,
            "stoppable_confirmed": True,
        },
    )
    assert action.status_code == 201
    action_item = action.get_json()["data"]
    completed = client.patch(
        f"/api/therapeutic-assessment/actions/{action_item['id']}",
        headers={**headers["p-b04"], "Idempotency-Key": "b04-action-complete"},
        json={
            "status": "completed",
            "followup_note": "我记录了这次尝试。",
            "expected_version": 1,
        },
    )
    assert completed.status_code == 200
    detail = client.get(
        f"/api/therapeutic-assessment/cases/{case_id}",
        headers=headers["r-b04"],
    ).get_json()["data"]
    archived = client.post(
        f"/api/therapeutic-assessment/cases/{case_id}/transitions",
        headers={**headers["r-b04"], "Idempotency-Key": "b04-archive"},
        json={
            "track": "workflow",
            "target_state": "archived",
            "expected_version": detail["version"],
            "reason_code": "followup_complete",
        },
    )
    assert archived.status_code == 200
    assert archived.get_json()["data"]["workflow_state"] == "archived"

    lifecycle = client.get(
        f"/api/therapeutic-assessment/cases/{case_id}/lifecycle",
        headers=headers["p-b04"],
    )
    data = lifecycle.get_json()["data"]
    assert lifecycle.status_code == 200
    assert data["workflow_state"] == "archived"
    assert data["metrics"]["process_quality"]["feedback_version_count"] == 2
    assert data["metrics"]["process_quality"]["participant_response_count"] == 1
    assert data["metrics"]["process_quality"]["action_followup_count"] == 1
    assert data["metrics"]["implementation_quality"]["withdrawal_propagation_ok"] is True


def test_withdrawal_receipts_and_scope_are_enforced(tmp_path, monkeypatch):
    app = _app(tmp_path, monkeypatch)
    headers = _seed(app)
    client = app.test_client()
    case_id = _ready_case(client, headers)
    feedback = _draft_review_send(client, headers, case_id, "b04-withdraw")
    withdrawn = client.post(
        f"/api/therapeutic-assessment/feedback-versions/{feedback['id']}/withdraw",
        headers={**headers["s-b04"], "Idempotency-Key": "b04-withdraw-feedback"},
        json={"expected_lifecycle_version": 1, "reason": "参与者要求撤回这份反馈。"},
    )
    assert withdrawn.status_code == 200
    assert withdrawn.get_json()["data"]["status"] == "withdrawn"

    other = client.get(
        f"/api/therapeutic-assessment/cases/{case_id}/lifecycle",
        headers=headers["p2-b04"],
    )
    own = client.get(
        f"/api/therapeutic-assessment/cases/{case_id}/lifecycle",
        headers=headers["p-b04"],
    )
    assert other.status_code == 403
    assert own.status_code == 200
    assert own.get_json()["data"]["delivery_receipts"][0]["status"] == "withdrawn"
    assert own.get_json()["data"]["recovery"]["withdrawal_propagation_ok"] is True


def test_lifecycle_metrics_separate_process_implementation_and_harm(tmp_path, monkeypatch):
    app = _app(tmp_path, monkeypatch)
    headers = _seed(app)
    client = app.test_client()
    case_id = _ready_case(client, headers)
    feedback = _draft_review_send(client, headers, case_id, "b04-metrics")
    with app.app_context():
        from database import get_connection, now_iso

        now = now_iso()
        with get_connection() as conn:
            conn.execute(
                """
                INSERT INTO therapeutic_assessment_quality_incidents (
                    id, case_id, feedback_id, reporter_user_id, source_type,
                    category, description, requested_resolution, status,
                    version, idempotency_key, created_at, updated_at
                ) VALUES ('incident-b04', ?, ?, 'p-b04', 'participant_report',
                    'correction_request', '这份反馈让我感到不适。', '希望重新核对。',
                    'reported', 1, 'incident-b04-key', ?, ?)
                """,
                (case_id, feedback["id"], now, now),
            )
            conn.commit()
    metrics = client.get(
        "/api/therapeutic-assessment/lifecycle/metrics",
        headers=headers["s-b04"],
    )
    denied = client.get(
        "/api/therapeutic-assessment/lifecycle/metrics",
        headers=headers["p-b04"],
    )
    data = metrics.get_json()["data"]
    assert metrics.status_code == 200
    assert denied.status_code == 403
    assert data["process_quality"]["case_count"] == 1
    assert data["implementation_quality"]["withdrawal_propagation_failures"] == 0
    assert data["harm_incidents"] == {"total": 1, "open": 1}


def test_disabled_lifecycle_keeps_core_routes_independent(tmp_path, monkeypatch):
    app = _app(tmp_path, monkeypatch, lifecycle_enabled=False)
    headers = _seed(app)
    client = app.test_client()
    case_id = _ready_case(client, headers)
    lifecycle = client.get(
        f"/api/therapeutic-assessment/cases/{case_id}/lifecycle",
        headers=headers["p-b04"],
    )
    goals = client.get("/api/goals", headers=headers["p-b04"])
    cards = client.get("/api/cards/recommend", headers=headers["p-b04"])
    messages = client.get("/api/messages", headers=headers["p-b04"])
    assert lifecycle.status_code == 200
    assert lifecycle.get_json()["data"]["enabled"] is False
    assert goals.status_code == 200
    assert cards.status_code == 200
    assert messages.status_code == 200


def test_privacy_scope_covers_lifecycle_children(tmp_path, monkeypatch):
    app = _app(tmp_path, monkeypatch)
    headers = _seed(app)
    client = app.test_client()
    case_id = _ready_case(client, headers)
    feedback = _draft_review_send(client, headers, case_id, "b04-privacy")
    with app.app_context():
        from database import get_connection
        from services.privacy_request_service import SCOPE_TABLES, _table_count

        expected = {
            "therapeutic_assessment_feedback_deliveries",
            "therapeutic_assessment_feedback_responses",
            "therapeutic_assessment_evidence_items",
            "therapeutic_assessment_data_items",
            "therapeutic_assessment_actions",
            "therapeutic_assessment_cases",
        }
        assert expected.issubset(set(SCOPE_TABLES["therapeutic_assessment"]))
        with get_connection() as conn:
            assert _table_count(
                conn, "therapeutic_assessment_feedback_deliveries", "p-b04"
            ) == 1
            assert _table_count(conn, "publication_candidates", "p-b04") == 1
            assert conn.execute(
                "SELECT status FROM publication_candidates WHERE subject_id = ?",
                (feedback["id"],),
            ).fetchone()["status"] == "published"
