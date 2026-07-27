import importlib
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"


def _app(tmp_path, monkeypatch):
    sys.path.insert(0, str(BACKEND))
    for name in list(sys.modules):
        if name in {"app", "config", "database", "models"} or name.startswith(("routes.", "services.")):
            sys.modules.pop(name, None)
    monkeypatch.setenv("APP_ENV", "testing")
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "f09.sqlite3"))
    monkeypatch.setenv("CONTENT_DIR", str(ROOT / "content"))
    return importlib.import_module("app").app


def _seed(app):
    users = {
        "p-f09": "parent",
        "p2-f09": "parent",
        "r-f09": "researcher",
        "s-f09": "supervisor",
        "a-f09": "admin",
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
                ("auth-f09-draft", "r-f09", "T2", "feedback_draft"),
                ("auth-f09-review", "s-f09", "T3", "feedback_review"),
            ):
                conn.execute(
                    """
                    INSERT INTO therapeutic_assessment_authorizations (
                        id, user_id, competency_level, task_code, scope_json,
                        supervisor_user_id, evidence_ref, starts_at, expires_at,
                        status, version, granted_by, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, 'a-f09', ?, ?,
                        '2099-01-01T00:00:00+00:00', 'active', 1, 'a-f09', ?, ?)
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
            user_id: {"Authorization": f"Bearer {generate_auth_token({'id': user_id, 'role': role})}"}
            for user_id, role in users.items()
        }


def _case(client, headers):
    created = client.post(
        "/api/therapeutic-assessment/cases",
        headers={**headers["p-f09"], "Idempotency-Key": "f09-case"},
        json={"assessment_question": "我想核对一次沟通中的理解", "shared_scope": ["question"], "consent": True},
    )
    assert created.status_code == 201
    case = created.get_json()["data"]
    assigned = client.post(
        f"/api/therapeutic-assessment/cases/{case['id']}/assign",
        headers={**headers["s-f09"], "Idempotency-Key": "f09-assign"},
        json={"researcher_id": "r-f09"},
    )
    assert assigned.status_code == 200
    readiness = client.post(
        f"/api/therapeutic-assessment/cases/{case['id']}/readiness",
        headers={**headers["s-f09"], "Idempotency-Key": "f09-readiness"},
        json={
            "qualification_evidence_ref": "evidence:qualification-f09",
            "supervision_evidence_ref": "evidence:supervision-f09",
            "ethics_evidence_ref": "evidence:ethics-f09",
        },
    )
    assert readiness.status_code == 200
    return readiness.get_json()["data"]


def _feedback_payload(**overrides):
    payload = {
        "source": "human",
        "feedback_layer": "layer_1",
        "letter_title": "给你的阶段性反馈",
        "observations": ["你记录了当时先停下来再回应"],
        "evidence": ["participant:self-report"],
        "alternatives": ["这也可能与当时需要整理思路有关"],
        "uncertainty": "目前只依据这一次记录，仍需要和你核对。",
        "next_step": "可以选择一个你愿意继续观察的小动作。",
        "human_discussion": ["这份理解哪里像，哪里不像？"],
        "participant_content": "从这次记录看，你先停下来再回应；这只是当前理解，可以不同意。",
    }
    payload.update(overrides)
    return payload


def _draft(client, headers, case_id, key="f09-draft", **overrides):
    return client.post(
        f"/api/therapeutic-assessment/cases/{case_id}/feedback-versions",
        headers={**headers["r-f09"], "Idempotency-Key": key},
        json=_feedback_payload(**overrides),
    )


def _send(client, headers, feedback_id, prefix="f09"):
    reviewed = client.post(
        f"/api/therapeutic-assessment/feedback-versions/{feedback_id}/review",
        headers={**headers["s-f09"], "Idempotency-Key": f"{prefix}-review"},
        json={"decision": "approved"},
    )
    sent = client.post(
        f"/api/therapeutic-assessment/feedback-versions/{feedback_id}/send",
        headers={**headers["s-f09"], "Idempotency-Key": f"{prefix}-send"},
    )
    assert reviewed.status_code == 200
    assert sent.status_code == 200
    return sent.get_json()["data"]


def test_schema_038_adds_layered_feedback_ledger(tmp_path, monkeypatch):
    app = _app(tmp_path, monkeypatch)
    with app.app_context():
        from database import CURRENT_SCHEMA_NAME, CURRENT_SCHEMA_VERSION, get_connection

        with get_connection() as conn:
            tables = {row["name"] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            columns = {
                row["name"]
                for row in conn.execute("PRAGMA table_info(therapeutic_assessment_feedback_versions)")
            }
        assert {
            "therapeutic_assessment_feedback_deliveries",
            "therapeutic_assessment_feedback_responses",
        }.issubset(tables)
        assert {
            "feedback_layer",
            "recipient_user_id",
            "letter_title",
            "supersedes_feedback_id",
            "withdrawn_at",
            "lifecycle_version",
        }.issubset(columns)
        assert CURRENT_SCHEMA_VERSION >= "2026_07_27_038"
        assert CURRENT_SCHEMA_NAME


def test_digital_layers_and_language_boundary_are_hard_gates(tmp_path, monkeypatch):
    app = _app(tmp_path, monkeypatch)
    headers = _seed(app)
    client = app.test_client()
    case = _case(client, headers)

    challenge = _draft(client, headers, case["id"], "f09-layer3", feedback_layer="layer_3")
    diagnostic = _draft(
        client,
        headers,
        case["id"],
        "f09-diagnostic",
        participant_content="你就是控制型人格。",
    )
    wrong_recipient = _draft(
        client,
        headers,
        case["id"],
        "f09-recipient",
        recipient_user_id="p2-f09",
    )
    unauthorized_material = _draft(
        client,
        headers,
        case["id"],
        "f09-unauthorized-material",
        evidence=["data-item:not-authorized"],
    )
    allowed = _draft(client, headers, case["id"], "f09-layer2", feedback_layer="layer_2")

    assert challenge.status_code == 409
    assert challenge.get_json()["error"]["code"] == "challenge_layer_offline_only"
    assert diagnostic.status_code == 422
    assert diagnostic.get_json()["error"]["code"] == "feedback_language_blocked"
    assert wrong_recipient.status_code == 422
    assert unauthorized_material.status_code == 403
    assert unauthorized_material.get_json()["error"]["code"] == "evidence_scope_error"
    assert allowed.status_code == 201
    assert allowed.get_json()["data"]["feedback_layer"] == "layer_2"


def test_delivery_and_participant_response_preserve_disagreement_history(tmp_path, monkeypatch):
    app = _app(tmp_path, monkeypatch)
    headers = _seed(app)
    client = app.test_client()
    case = _case(client, headers)
    feedback = _draft(client, headers, case["id"]).get_json()["data"]
    _send(client, headers, feedback["id"])

    forbidden = client.post(
        f"/api/therapeutic-assessment/feedback-versions/{feedback['id']}/responses",
        headers={**headers["p2-f09"], "Idempotency-Key": "f09-other-response"},
        json={"recognition": "like"},
    )
    missing_note = client.post(
        f"/api/therapeutic-assessment/feedback-versions/{feedback['id']}/responses",
        headers={**headers["p-f09"], "Idempotency-Key": "f09-response-missing"},
        json={"recognition": "not_like"},
    )
    first = client.post(
        f"/api/therapeutic-assessment/feedback-versions/{feedback['id']}/responses",
        headers={**headers["p-f09"], "Idempotency-Key": "f09-response-1"},
        json={"recognition": "not_like", "disagreement_note": "这和我的当时感受不一致。"},
    )
    replay = client.post(
        f"/api/therapeutic-assessment/feedback-versions/{feedback['id']}/responses",
        headers={**headers["p-f09"], "Idempotency-Key": "f09-response-1"},
        json={"recognition": "not_like", "disagreement_note": "这和我的当时感受不一致。"},
    )
    second = client.post(
        f"/api/therapeutic-assessment/feedback-versions/{feedback['id']}/responses",
        headers={**headers["p-f09"], "Idempotency-Key": "f09-response-2"},
        json={"recognition": "need_time"},
    )

    assert forbidden.status_code == 403
    assert missing_note.status_code == 422
    assert first.status_code == 201
    assert replay.status_code == 200
    assert replay.get_json()["data"]["id"] == first.get_json()["data"]["id"]
    assert second.status_code == 201
    assert second.get_json()["data"]["supersedes_response_id"] == first.get_json()["data"]["id"]
    detail = client.get(f"/api/therapeutic-assessment/cases/{case['id']}", headers=headers["p-f09"])
    participant_feedback = detail.get_json()["data"]["feedback_versions"][0]
    assert participant_feedback["participant_response"]["recognition"] == "need_time"
    assert participant_feedback["delivery_count"] == 1


def test_revision_withdrawal_and_resend_are_versioned_and_audited(tmp_path, monkeypatch):
    app = _app(tmp_path, monkeypatch)
    headers = _seed(app)
    client = app.test_client()
    case = _case(client, headers)
    feedback = _draft(client, headers, case["id"]).get_json()["data"]
    sent = _send(client, headers, feedback["id"])

    resent = client.post(
        f"/api/therapeutic-assessment/feedback-versions/{feedback['id']}/resend",
        headers={**headers["s-f09"], "Idempotency-Key": "f09-resend"},
    )
    replay = client.post(
        f"/api/therapeutic-assessment/feedback-versions/{feedback['id']}/resend",
        headers={**headers["s-f09"], "Idempotency-Key": "f09-resend"},
    )
    revised = client.post(
        f"/api/therapeutic-assessment/feedback-versions/{feedback['id']}/revise",
        headers={**headers["r-f09"], "Idempotency-Key": "f09-revise"},
        json={
            **_feedback_payload(participant_content="结合你的核对意见，这里改成更贴近当时记录的阶段性理解。"),
            "revision_reason": "根据参与者核对修订",
            "expected_lifecycle_version": sent["lifecycle_version"],
        },
    )
    withdrawn = client.post(
        f"/api/therapeutic-assessment/feedback-versions/{feedback['id']}/withdraw",
        headers={**headers["s-f09"], "Idempotency-Key": "f09-withdraw"},
        json={"reason": "已由修订版本替代", "expected_lifecycle_version": sent["lifecycle_version"]},
    )
    withdraw_replay = client.post(
        f"/api/therapeutic-assessment/feedback-versions/{feedback['id']}/withdraw",
        headers={**headers["s-f09"], "Idempotency-Key": "f09-withdraw"},
        json={"reason": "已由修订版本替代", "expected_lifecycle_version": sent["lifecycle_version"]},
    )

    assert resent.status_code == 200
    assert replay.status_code == 200
    assert replay.get_json()["data"]["id"] == resent.get_json()["data"]["id"]
    assert resent.get_json()["data"]["sequence_no"] == 2
    assert revised.status_code == 201
    assert revised.get_json()["data"]["supersedes_feedback_id"] == feedback["id"]
    assert revised.get_json()["data"]["version_no"] == 2
    assert withdrawn.status_code == 200
    assert withdrawn.get_json()["data"]["status"] == "withdrawn"
    assert withdraw_replay.status_code == 200
    participant = client.get(f"/api/therapeutic-assessment/cases/{case['id']}", headers=headers["p-f09"])
    visible_ids = {item["id"] for item in participant.get_json()["data"]["feedback_versions"]}
    assert feedback["id"] not in visible_ids


def test_migration_is_additive_and_production_guarded(tmp_path):
    database_path = tmp_path / "migration-f09.sqlite3"
    env = {
        **os.environ,
        "APP_ENV": "testing",
        "DATABASE_PATH": str(database_path),
        "CONTENT_DIR": str(ROOT / "content"),
    }
    applied = subprocess.run(
        [sys.executable, str(BACKEND / "scripts/migrate_task38_f09_layered_feedback.py"), "apply"],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
    )
    blocked = subprocess.run(
        [sys.executable, str(BACKEND / "scripts/migrate_task38_f09_layered_feedback.py"), "apply"],
        cwd=ROOT,
        env={**env, "APP_ENV": "production"},
        capture_output=True,
        text=True,
    )
    rolled_back = subprocess.run(
        [sys.executable, str(BACKEND / "scripts/migrate_task38_f09_layered_feedback.py"), "rollback"],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
    )
    assert applied.returncode == 0
    assert '"ok": true' in applied.stdout.lower()
    assert blocked.returncode != 0
    assert "生产迁移已阻断" in blocked.stderr
    assert rolled_back.returncode == 0
    assert '"history_deleted": false' in rolled_back.stdout.lower()
