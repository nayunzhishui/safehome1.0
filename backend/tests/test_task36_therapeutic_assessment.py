import importlib
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"


def _fresh_app(tmp_path, monkeypatch):
    sys.path.insert(0, str(BACKEND))
    for name in list(sys.modules):
        if name in {"app", "config", "database", "models"} or name.startswith("routes.") or name.startswith("services."):
            sys.modules.pop(name, None)
    monkeypatch.setenv("APP_ENV", "testing")
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "task36-f16.sqlite3"))
    monkeypatch.setenv("CONTENT_DIR", str(ROOT / "content"))
    return importlib.import_module("app").app


def _seed(app):
    with app.app_context():
        from database import get_connection, now_iso
        from routes.auth_utils import generate_auth_token

        now = now_iso()
        actors = {
            "participant-f16": "parent",
            "other-f16": "parent",
            "researcher-f16": "researcher",
            "supervisor-f16": "supervisor",
            "admin-f16": "admin",
        }
        with get_connection() as conn:
            for actor_id, role in actors.items():
                conn.execute(
                    "INSERT INTO users (id, nickname, role, status, created_at, updated_at) VALUES (?, ?, ?, 'active', ?, ?)",
                    (actor_id, actor_id, role, now, now),
                )
            conn.commit()
        return {
            actor_id: {"Authorization": f"Bearer {generate_auth_token({'id': actor_id, 'role': role})}"}
            for actor_id, role in actors.items()
        }


def _create(client, headers, key="case-f16", question="我想和研究者一起理解最近一次沟通中的感受。"):
    return client.post(
        "/api/therapeutic-assessment/cases",
        headers={**headers["participant-f16"], "Idempotency-Key": key},
        json={
            "assessment_question": question,
            "shared_scope": ["question", "recent_record"],
            "consent": True,
            "assigned_researcher_id": "researcher-f16",
        },
    )


def _feedback_payload(**overrides):
    payload = {
        "source": "human",
        "observations": ["这次记录中可以看到你愿意停下来观察。"],
        "evidence": ["参与者主动提出共同理解问题。"],
        "alternatives": ["也可能与当时精力不足有关。"],
        "uncertainty": "目前只有一次记录，需要与你核对。",
        "next_step": "选择一次低压力沟通，先停顿三秒。",
        "human_discussion": ["哪些描述与你的体验一致？"],
        "participant_content": "这是待人工复核的共同理解草稿。",
    }
    payload.update(overrides)
    return payload


def _assign_and_prepare(client, headers, case_id, prefix):
    assigned = client.post(
        f"/api/therapeutic-assessment/cases/{case_id}/assign",
        headers={**headers["supervisor-f16"], "Idempotency-Key": f"{prefix}-assign"},
        json={"researcher_id": "researcher-f16"},
    )
    assert assigned.status_code == 200
    draft = client.post(
        f"/api/therapeutic-assessment/cases/{case_id}/feedback-versions",
        headers={**headers["researcher-f16"], "Idempotency-Key": f"{prefix}-draft"},
        json=_feedback_payload(),
    )
    assert draft.status_code == 201
    ready = client.post(
        f"/api/therapeutic-assessment/cases/{case_id}/readiness",
        headers={**headers["supervisor-f16"], "Idempotency-Key": f"{prefix}-ready"},
        json={
            "qualification_evidence_ref": "evidence://q",
            "supervision_evidence_ref": "evidence://s",
            "ethics_evidence_ref": "evidence://e",
        },
    )
    assert ready.status_code == 200
    return draft.get_json()["data"]["id"]


def test_complete_human_led_collaboration_and_version_scope(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    headers = _seed(app)
    client = app.test_client()
    created = _create(client, headers)
    replay = _create(client, headers)
    assert created.status_code == 201 and replay.status_code == 200
    case = created.get_json()["data"]
    case_id = case["id"]
    assert case["readiness_level"] == "L0" and case["efficacy_score"] is None

    conflict = client.patch(
        f"/api/therapeutic-assessment/cases/{case_id}/scope",
        headers={**headers["participant-f16"], "Idempotency-Key": "scope-conflict"},
        json={"expected_version": 9, "shared_scope": ["question"]},
    )
    changed = client.patch(
        f"/api/therapeutic-assessment/cases/{case_id}/scope",
        headers={**headers["participant-f16"], "Idempotency-Key": "scope-ok"},
        json={"expected_version": 1, "shared_scope": ["question"]},
    )
    assert conflict.status_code == 409 and changed.status_code == 200
    assert changed.get_json()["data"]["version"] == 2

    # 参与者不能自选研究者：研究者必须由督导/管理员通过 assign 分配后才能起草反馈。
    unassigned = client.post(
        f"/api/therapeutic-assessment/cases/{case_id}/feedback-versions",
        headers={**headers["researcher-f16"], "Idempotency-Key": "draft-unassigned"},
        json={
            "source": "human",
            "uncertainty": "尚未分配。",
            "next_step": "尚未分配。",
            "participant_content": "研究者尚未被分配，不应能起草。",
        },
    )
    assert unassigned.status_code == 403
    assigned = client.post(
        f"/api/therapeutic-assessment/cases/{case_id}/assign",
        headers={**headers["supervisor-f16"], "Idempotency-Key": "assign-f16"},
        json={"researcher_id": "researcher-f16"},
    )
    assert assigned.status_code == 200 and assigned.get_json()["data"]["assigned_researcher_id"] == "researcher-f16"

    draft = client.post(
        f"/api/therapeutic-assessment/cases/{case_id}/feedback-versions",
        headers={**headers["researcher-f16"], "Idempotency-Key": "draft-f16"},
        json={
            "source": "ai_draft",
            "observations": ["这次记录中可以看到你愿意停下来观察。"],
            "evidence": ["参与者主动提出共同理解问题。"],
            "alternatives": ["也可能与当时精力不足有关。"],
            "uncertainty": "目前只有一次记录，需要与你核对。",
            "next_step": "选择一次低压力沟通，先停顿三秒。",
            "human_discussion": ["哪些描述与你的体验一致？"],
            "participant_content": "这是待人工复核的共同理解草稿，你可以不同意或补充。",
        },
    )
    assert draft.status_code == 201
    feedback_id = draft.get_json()["data"]["id"]
    blocked = client.post(
        f"/api/therapeutic-assessment/feedback-versions/{feedback_id}/review",
        headers={**headers["supervisor-f16"], "Idempotency-Key": "review-too-early"},
        json={"decision": "approved"},
    )
    assert blocked.status_code == 409 and blocked.get_json()["error"]["code"] == "readiness_gate"

    ready = client.post(
        f"/api/therapeutic-assessment/cases/{case_id}/readiness",
        headers={**headers["supervisor-f16"], "Idempotency-Key": "ready-f16"},
        json={
            "qualification_evidence_ref": "evidence://synthetic/qualification",
            "supervision_evidence_ref": "evidence://synthetic/supervision",
            "ethics_evidence_ref": "evidence://synthetic/ethics",
        },
    )
    assert ready.status_code == 200 and ready.get_json()["data"]["readiness_level"] == "L2"
    reviewed = client.post(
        f"/api/therapeutic-assessment/feedback-versions/{feedback_id}/review",
        headers={**headers["supervisor-f16"], "Idempotency-Key": "review-f16"},
        json={"decision": "approved"},
    )
    sent = client.post(
        f"/api/therapeutic-assessment/feedback-versions/{feedback_id}/send",
        headers={**headers["supervisor-f16"], "Idempotency-Key": "send-f16"},
    )
    assert reviewed.get_json()["data"]["status"] == "reviewed"
    assert sent.get_json()["data"]["status"] == "sent"

    chosen = client.post(
        f"/api/therapeutic-assessment/cases/{case_id}/actions",
        headers={**headers["participant-f16"], "Idempotency-Key": "action-f16"},
        json={"feedback_version_id": feedback_id, "action_text": "下一次沟通前先停顿三秒。"},
    )
    action_id = chosen.get_json()["data"]["id"]
    completed = client.patch(
        f"/api/therapeutic-assessment/actions/{action_id}",
        headers={**headers["participant-f16"], "Idempotency-Key": "followup-f16"},
        json={"status": "completed", "followup_note": "停顿后更容易说明自己的需要。"},
    )
    assert chosen.status_code == 201 and completed.get_json()["data"]["status"] == "completed"

    detail = client.get(f"/api/therapeutic-assessment/cases/{case_id}", headers=headers["participant-f16"])
    denied = client.get(f"/api/therapeutic-assessment/cases/{case_id}", headers=headers["other-f16"])
    assert detail.status_code == 200 and denied.status_code == 403
    assert detail.get_json()["data"]["feedback_versions"][-1]["status"] == "sent"


def test_disagree_withdraw_risk_and_external_complexity_gates(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    headers = _seed(app)
    client = app.test_client()
    case_id = _create(client, headers, "case-disagree").get_json()["data"]["id"]
    disagreed = client.post(
        f"/api/therapeutic-assessment/cases/{case_id}/disagree",
        headers={**headers["participant-f16"], "Idempotency-Key": "disagree-f16"},
        json={"note": "这段理解和我的体验不完全一致。"},
    )
    withdrawn = client.post(
        f"/api/therapeutic-assessment/cases/{case_id}/withdraw",
        headers={**headers["participant-f16"], "Idempotency-Key": "withdraw-f16"},
        json={"note": "暂时不继续。"},
    )
    assert disagreed.status_code == 200
    assert withdrawn.get_json()["data"]["consent_status"] == "withdrawn"

    risky = _create(client, headers, "case-risk", "我现在想自杀，需要你替我诊断。")
    assert risky.status_code == 201
    risky_data = risky.get_json()["data"]
    assert risky_data["status"] == "support_required"
    readiness = client.post(
        f"/api/therapeutic-assessment/cases/{risky_data['id']}/readiness",
        headers={**headers["admin-f16"], "Idempotency-Key": "risk-ready"},
        json={
            "qualification_evidence_ref": "evidence://q",
            "supervision_evidence_ref": "evidence://s",
            "ethics_evidence_ref": "evidence://e",
        },
    )
    assert readiness.status_code == 409 and readiness.get_json()["error"]["code"] == "external_gate_required"

    with app.app_context():
        from database import get_connection

        with get_connection() as conn:
            audit_count = conn.execute("SELECT COUNT(*) AS count FROM audit_logs WHERE action LIKE 'therapeutic_assessment_%'").fetchone()["count"]
            event_count = conn.execute("SELECT COUNT(*) AS count FROM therapeutic_assessment_events").fetchone()["count"]
            assert audit_count >= 4 and event_count >= 4


def test_feedback_requires_evidence_and_independent_review(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    headers = _seed(app)
    client = app.test_client()
    case_id = _create(client, headers, "case-hardening").get_json()["data"]["id"]
    client.post(
        f"/api/therapeutic-assessment/cases/{case_id}/assign",
        headers={**headers["supervisor-f16"], "Idempotency-Key": "hard-assign"},
        json={"researcher_id": "researcher-f16"},
    )

    no_evidence = client.post(
        f"/api/therapeutic-assessment/cases/{case_id}/feedback-versions",
        headers={**headers["researcher-f16"], "Idempotency-Key": "hard-no-evidence"},
        json=_feedback_payload(evidence=[]),
    )
    assert no_evidence.status_code == 422
    assert no_evidence.get_json()["error"]["code"] == "evidence_required"

    self_draft = client.post(
        f"/api/therapeutic-assessment/cases/{case_id}/feedback-versions",
        headers={**headers["supervisor-f16"], "Idempotency-Key": "hard-self-draft"},
        json=_feedback_payload(),
    )
    feedback_id = self_draft.get_json()["data"]["id"]
    client.post(
        f"/api/therapeutic-assessment/cases/{case_id}/readiness",
        headers={**headers["supervisor-f16"], "Idempotency-Key": "hard-ready"},
        json={
            "qualification_evidence_ref": "evidence://q",
            "supervision_evidence_ref": "evidence://s",
            "ethics_evidence_ref": "evidence://e",
        },
    )
    reviewed = client.post(
        f"/api/therapeutic-assessment/feedback-versions/{feedback_id}/review",
        headers={**headers["supervisor-f16"], "Idempotency-Key": "hard-self-review"},
        json={"decision": "approved"},
    )
    assert reviewed.status_code == 403
    assert reviewed.get_json()["error"]["code"] == "self_review_forbidden"


def test_risk_queue_version_and_feedback_ownership_guards(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    headers = _seed(app)
    client = app.test_client()
    risky = _create(client, headers, "case-risk-queue", "我现在想自杀，需要人工支持。")
    assert risky.status_code == 201
    with app.app_context():
        from database import get_connection

        with get_connection() as conn:
            queued = conn.execute(
                "SELECT COUNT(*) AS count FROM risk_review_records "
                "WHERE source_type = 'therapeutic_assessment_case' AND source_id = ?",
                (risky.get_json()["data"]["id"],),
            ).fetchone()["count"]
            assert queued == 1

    case_one = _create(client, headers, "case-owner-one").get_json()["data"]["id"]
    stale = client.post(
        f"/api/therapeutic-assessment/cases/{case_one}/disagree",
        headers={**headers["participant-f16"], "Idempotency-Key": "stale-transition"},
        json={"expected_version": 99, "note": "这段理解不完全一致。"},
    )
    assert stale.status_code == 409
    assert stale.get_json()["error"]["code"] == "version_conflict"

    feedback_one = _assign_and_prepare(client, headers, case_one, "owner-one")
    reviewed = client.post(
        f"/api/therapeutic-assessment/feedback-versions/{feedback_one}/review",
        headers={**headers["supervisor-f16"], "Idempotency-Key": "owner-one-review"},
        json={"decision": "approved"},
    )
    assert reviewed.status_code == 200
    sent = client.post(
        f"/api/therapeutic-assessment/feedback-versions/{feedback_one}/send",
        headers={**headers["supervisor-f16"], "Idempotency-Key": "owner-one-send"},
    )
    assert sent.status_code == 200

    case_two = _create(client, headers, "case-owner-two").get_json()["data"]["id"]
    feedback_two = _assign_and_prepare(client, headers, case_two, "owner-two")
    cross_case = client.post(
        f"/api/therapeutic-assessment/cases/{case_one}/actions",
        headers={**headers["participant-f16"], "Idempotency-Key": "owner-cross"},
        json={"feedback_version_id": feedback_two, "action_text": "先停顿三秒。"},
    )
    assert cross_case.status_code == 422
    assert cross_case.get_json()["error"]["code"] == "validation_error"
