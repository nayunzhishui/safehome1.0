import importlib
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
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "c07.sqlite3"))
    monkeypatch.setenv("CONTENT_DIR", str(ROOT / "content"))
    monkeypatch.setenv("AI_QA_SANDBOX_ENABLED", "1")
    return importlib.import_module("app").app


def _seed(app):
    users = {
        "researcher-c07": "researcher",
        "reviewer-c07": "researcher",
        "supervisor-c07": "supervisor",
        "admin-c07": "admin",
    }
    with app.app_context():
        from database import get_connection, now_iso
        from routes.auth_utils import generate_auth_token

        timestamp = now_iso()
        with get_connection() as conn:
            for user_id, role in users.items():
                conn.execute(
                    """
                    INSERT INTO users (
                        id, nickname, role, status, created_at, updated_at
                    ) VALUES (?, ?, ?, 'active', ?, ?)
                    """,
                    (user_id, user_id, role, timestamp, timestamp),
                )
            conn.commit()
        return {
            user_id: {
                "Authorization": (
                    "Bearer "
                    + generate_auth_token({"id": user_id, "role": role})
                )
            }
            for user_id, role in users.items()
        }


def _grant(
    client,
    headers,
    *,
    user_id,
    level,
    task_code,
    complexity_scope,
    key,
):
    now = datetime.now(timezone.utc)
    response = client.post(
        "/api/therapeutic-assessment/competency/authorizations",
        headers={**headers["admin-c07"], "Idempotency-Key": key},
        json={
            "user_id": user_id,
            "competency_level": level,
            "task_code": task_code,
            "scope": {"complexity_scopes": [complexity_scope]},
            "supervisor_user_id": "admin-c07",
            "evidence_ref": f"evidence:{key}",
            "starts_at": (now - timedelta(minutes=1)).isoformat(),
            "expires_at": (now + timedelta(days=30)).isoformat(),
        },
    )
    assert response.status_code == 201


def _create_review_case(
    app,
    *,
    suffix,
    draft_author_id="provider:fake",
    risk_level="low",
    involves_minor=False,
    multi_party=False,
    mechanism_explanation=False,
):
    with app.app_context():
        from database import get_connection, json_dumps, now_iso
        from services.ai_qa_review_service import create_review_case

        timestamp = now_iso()
        session_id = f"session-{suffix}"
        message_id = f"message-{suffix}"
        with get_connection() as conn:
            conn.execute(
                """
                INSERT INTO ai_qa_sessions (
                    id, user_id, mode, status, synthetic_data, context_policy,
                    research_use_allowed, use_case_id, use_case_policy_version,
                    created_at, updated_at
                ) VALUES (
                    ?, 'researcher-c07', 'research_sandbox', 'active', 1,
                    'current_session_only', 0, 'approved_material_organization',
                    'test-c07', ?, ?
                )
                """,
                (session_id, timestamp, timestamp),
            )
            citations = [
                {
                    "content_type": "training_card",
                    "content_id": "pause",
                    "title": "暂停练习",
                    "version_id": f"version-{suffix}",
                    "content_version": "v1",
                    "release_id": f"release-{suffix}",
                    "payload_hash": f"payload-{suffix}",
                    "excerpt": "情绪升高时可以先暂停。",
                    "governance_status": "published",
                    "rights_status": "owned",
                    "review_status": "approved",
                    "source_ref": "safehome://training_cards/pause",
                    "source_version": "v1",
                }
            ]
            conn.execute(
                """
                INSERT INTO ai_qa_messages (
                    id, session_id, user_id, role, content, citations_json,
                    model_json, safety_json, prompt_version, knowledge_version,
                    token_estimate, cost_micros, created_at
                ) VALUES (?, ?, 'researcher-c07', 'assistant', ?, ?, '{}', '{}',
                    'prompt-v3', 'knowledge-v1', 10, 0, ?)
                """,
                (
                    message_id,
                    session_id,
                    "基于已批准材料，可先暂停并核对当时情境。[S1]",
                    json_dumps(citations),
                    timestamp,
                ),
            )
            case = create_review_case(
                conn,
                message_id=message_id,
                session_id=session_id,
                subject_type="ai_qa_session",
                subject_id=session_id,
                recipient_user_id="researcher-c07",
                draft_author_id=draft_author_id,
                candidate_text="基于已批准材料，可先暂停并核对当时情境。[S1]",
                citations=citations,
                gate_violations=[],
                scope={
                    "object_scope": (
                        "individual_adult_low_risk"
                        if risk_level == "low"
                        else "high_risk"
                    ),
                    "risk_level": risk_level,
                    "involves_minor": involves_minor,
                    "multi_party": multi_party,
                    "mechanism_explanation": mechanism_explanation,
                },
                publication_candidate_id=None,
            )
            conn.commit()
            return case


def test_workbench_lists_source_candidate_gate_diff_final_and_publisher(
    tmp_path, monkeypatch
):
    app = _app(tmp_path, monkeypatch)
    headers = _seed(app)
    case = _create_review_case(app, suffix="visible")

    response = app.test_client().get(
        f"/api/ai-qa/review-cases/{case['id']}",
        headers=headers["reviewer-c07"],
    )
    data = response.get_json()["data"]

    assert response.status_code == 200
    assert data["candidate_text"].endswith("[S1]")
    assert data["citations"][0]["version_id"] == "version-visible"
    assert data["gate_violations"] == []
    assert data["diff"]["changed"] is False
    assert data["final_text"] is None
    assert data["published_by"] is None
    assert data["formal_feedback_written"] is False
    assert data["source_snapshot_hash"]
    assert data["scope"]["object_scope"] == "individual_adult_low_risk"


def test_modify_requires_independent_authorized_human_and_version_lock(
    tmp_path, monkeypatch
):
    app = _app(tmp_path, monkeypatch)
    headers = _seed(app)
    client = app.test_client()
    case = _create_review_case(app, suffix="modify")
    _grant(
        client,
        headers,
        user_id="reviewer-c07",
        level="T2",
        task_code="feedback_draft",
        complexity_scope="individual_adult_low_risk",
        key="grant-c07-standard",
    )

    modified = client.post(
        f"/api/ai-qa/review-cases/{case['id']}/decisions",
        headers={
            **headers["reviewer-c07"],
            "Idempotency-Key": "decision-c07-modify",
        },
        json={
            "decision": "modify",
            "expected_version": 1,
            "final_text": "根据已批准材料，可以先暂停，再由研究者核对适用情境。[S1]",
            "rationale": "缩小结论范围。",
        },
    )
    data = modified.get_json()["data"]
    conflict = client.post(
        f"/api/ai-qa/review-cases/{case['id']}/decisions",
        headers={
            **headers["reviewer-c07"],
            "Idempotency-Key": "decision-c07-stale",
        },
        json={
            "decision": "adopt",
            "expected_version": 1,
            "rationale": "旧版本。",
        },
    )

    assert modified.status_code == 200
    assert data["status"] == "modified"
    assert data["reviewed_by"] == "reviewer-c07"
    assert data["diff"]["changed"] is True
    assert data["published_by"] is None
    assert data["formal_feedback_written"] is False
    assert conflict.status_code == 409
    assert conflict.get_json()["error"]["code"] == "review_version_conflict"


@pytest.mark.parametrize(
    ("scope", "task_code", "complexity_scope"),
    [
        ({"risk_level": "high"}, "feedback_review", "high_risk"),
        ({"involves_minor": True}, "minor_or_family", "minor_or_family"),
        ({"multi_party": True}, "couple_or_multi_person", "couple_or_multi_person"),
        (
            {"mechanism_explanation": True},
            "formal_assessment",
            "mechanism_explanation",
        ),
    ],
)
def test_sensitive_cases_require_matching_t3_authorization(
    tmp_path,
    monkeypatch,
    scope,
    task_code,
    complexity_scope,
):
    app = _app(tmp_path, monkeypatch)
    headers = _seed(app)
    client = app.test_client()
    case = _create_review_case(
        app,
        suffix=task_code,
        risk_level=scope.get("risk_level", "low"),
        involves_minor=scope.get("involves_minor", False),
        multi_party=scope.get("multi_party", False),
        mechanism_explanation=scope.get("mechanism_explanation", False),
    )
    denied = client.post(
        f"/api/ai-qa/review-cases/{case['id']}/decisions",
        headers={
            **headers["supervisor-c07"],
            "Idempotency-Key": f"denied-{task_code}",
        },
        json={
            "decision": "adopt",
            "expected_version": 1,
            "rationale": "尚无专项授权。",
        },
    )
    _grant(
        client,
        headers,
        user_id="supervisor-c07",
        level="T3",
        task_code=task_code,
        complexity_scope=complexity_scope,
        key=f"grant-{task_code}",
    )
    adopted = client.post(
        f"/api/ai-qa/review-cases/{case['id']}/decisions",
        headers={
            **headers["supervisor-c07"],
            "Idempotency-Key": f"adopt-{task_code}",
        },
        json={
            "decision": "adopt",
            "expected_version": 1,
            "rationale": "已核对当前来源与范围。",
        },
    )

    assert case["required_task_code"] == task_code
    assert case["required_competency"] == "T3"
    assert denied.status_code == 403
    assert denied.get_json()["error"]["code"] == "review_authorization_required"
    assert adopted.status_code == 200


@pytest.mark.parametrize("decision", ["adopt", "modify", "reject", "none_match"])
def test_all_review_decisions_are_audited_without_formal_feedback_write(
    tmp_path, monkeypatch, decision
):
    app = _app(tmp_path, monkeypatch)
    headers = _seed(app)
    client = app.test_client()
    case = _create_review_case(app, suffix=decision)
    _grant(
        client,
        headers,
        user_id="reviewer-c07",
        level="T2",
        task_code="feedback_draft",
        complexity_scope="individual_adult_low_risk",
        key=f"grant-{decision}",
    )
    payload = {
        "decision": decision,
        "expected_version": 1,
        "rationale": "人工核对结果。",
    }
    if decision == "modify":
        payload["final_text"] = "人工修改后的内部候选，仍未发布为参与者反馈。[S1]"
    response = client.post(
        f"/api/ai-qa/review-cases/{case['id']}/decisions",
        headers={
            **headers["reviewer-c07"],
            "Idempotency-Key": f"decision-{decision}",
        },
        json=payload,
    )

    assert response.status_code == 200
    data = response.get_json()["data"]
    assert data["status"] == {
        "adopt": "adopted",
        "modify": "modified",
        "reject": "rejected",
        "none_match": "none_match",
    }[decision]
    assert data["formal_feedback_written"] is False
    with app.app_context():
        from database import get_connection

        with get_connection() as conn:
            action = conn.execute(
                "SELECT * FROM ai_qa_review_actions WHERE review_case_id = ?",
                (case["id"],),
            ).fetchone()
            formal = conn.execute(
                """
                SELECT COUNT(*) AS count FROM publication_candidates
                WHERE subject_id = ? AND channel != 'ai_candidate'
                """,
                (case["subject_id"],),
            ).fetchone()
    assert action["decision"] == decision
    assert formal["count"] == 0


def test_drafter_cannot_review_own_candidate(tmp_path, monkeypatch):
    app = _app(tmp_path, monkeypatch)
    headers = _seed(app)
    client = app.test_client()
    case = _create_review_case(
        app,
        suffix="same-person",
        draft_author_id="reviewer-c07",
    )
    _grant(
        client,
        headers,
        user_id="reviewer-c07",
        level="T2",
        task_code="feedback_draft",
        complexity_scope="individual_adult_low_risk",
        key="grant-same-person",
    )
    response = client.post(
        f"/api/ai-qa/review-cases/{case['id']}/decisions",
        headers={
            **headers["reviewer-c07"],
            "Idempotency-Key": "same-person-review",
        },
        json={
            "decision": "reject",
            "expected_version": 1,
            "rationale": "不能复核自己的草稿。",
        },
    )
    assert response.status_code == 409
    assert response.get_json()["error"]["code"] == "reviewer_separation_required"


def test_deleting_synthetic_session_removes_review_candidate_text(
    tmp_path, monkeypatch
):
    app = _app(tmp_path, monkeypatch)
    headers = _seed(app)
    case = _create_review_case(app, suffix="delete")

    response = app.test_client().delete(
        f"/api/ai-qa/sessions/{case['session_id']}",
        headers=headers["researcher-c07"],
    )

    assert response.status_code == 200
    with app.app_context():
        from database import get_connection

        with get_connection() as conn:
            remaining = conn.execute(
                "SELECT COUNT(*) AS count FROM ai_qa_review_cases WHERE id = ?",
                (case["id"],),
            ).fetchone()
    assert remaining["count"] == 0
