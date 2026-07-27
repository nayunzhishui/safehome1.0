import importlib
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
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "f07.sqlite3"))
    monkeypatch.setenv("CONTENT_DIR", str(ROOT / "content"))
    return importlib.import_module("app").app


def _seed(app):
    roles = {
        "p-f07": "parent",
        "p2-f07": "parent",
        "r-f07": "researcher",
        "s-f07": "supervisor",
        "a-f07": "admin",
    }
    with app.app_context():
        from database import get_connection, now_iso
        from routes.auth_utils import generate_auth_token
        now = now_iso()
        with get_connection() as conn:
            for user_id, role in roles.items():
                conn.execute(
                    "INSERT INTO users (id, nickname, role, status, created_at, updated_at) VALUES (?, ?, ?, 'active', ?, ?)",
                    (user_id, user_id, role, now, now),
                )
            conn.commit()
        return {
            user_id: {"Authorization": f"Bearer {generate_auth_token({'id': user_id, 'role': role})}"}
            for user_id, role in roles.items()
        }


def _case(client, headers, key="f07-case"):
    response = client.post(
        "/api/therapeutic-assessment/cases",
        headers={**headers["p-f07"], "Idempotency-Key": key},
        json={"assessment_question": "我想理解一次普通沟通", "shared_scope": ["question"], "consent": True},
    )
    assert response.status_code == 201
    return response.get_json()["data"]


def _chain(client, headers, case_id, key="f07-chain", status="active"):
    return client.put(
        f"/api/therapeutic-assessment/cases/{case_id}/responsibility-chain",
        headers={**headers["a-f07"], "Idempotency-Key": key},
        json={
            "responsible_user_id": "r-f07",
            "supervisor_user_id": "s-f07",
            "support_channel": "研究团队内部值守队列",
            "evidence_ref": "evidence:staff-roster-v1",
            "status": status,
            "queue_timeout_minutes": 5,
            "expected_version": 0,
        },
    )


def _signal(client, headers, case_id, key="f07-signal"):
    return client.post(
        f"/api/therapeutic-assessment/cases/{case_id}/safety-signals",
        headers={**headers["p-f07"], "Idempotency-Key": key},
        json={"signal_type": "other", "source_ref": "participant:self-report", "reason_summary": "希望真人了解"},
    )


def test_schema_036_and_participant_output_uses_human_understanding(tmp_path, monkeypatch):
    app = _app(tmp_path, monkeypatch)
    headers = _seed(app)
    client = app.test_client()
    case = _case(client, headers)
    assert _chain(client, headers, case["id"]).status_code == 200
    signal = _signal(client, headers, case["id"])
    detail = client.get(f"/api/therapeutic-assessment/cases/{case['id']}", headers=headers["p-f07"])
    assert signal.status_code == 201
    assert detail.get_json()["data"]["support_signal"] == "needs_human_understanding"
    assert "risk_level" not in detail.get_json()["data"]
    with app.app_context():
        from database import CURRENT_SCHEMA_NAME, CURRENT_SCHEMA_VERSION
        assert CURRENT_SCHEMA_VERSION == "2026_07_27_038"
        assert CURRENT_SCHEMA_NAME == "therapeutic_assessment_layered_feedback"


def test_signal_pauses_feedback_and_only_human_review_role_can_resolve(tmp_path, monkeypatch):
    app = _app(tmp_path, monkeypatch)
    headers = _seed(app)
    client = app.test_client()
    case = _case(client, headers)
    _chain(client, headers, case["id"])
    event = _signal(client, headers, case["id"]).get_json()["data"]
    blocked = client.post(
        f"/api/therapeutic-assessment/cases/{case['id']}/feedback-versions",
        headers={**headers["a-f07"], "Idempotency-Key": "f07-feedback"},
        json={
            "source": "human",
            "observations": ["一次具体记录"],
            "evidence": ["participant:self-report"],
            "alternatives": ["仍需了解情境"],
            "uncertainty": "当前信息有限",
            "next_step": "等待真人了解",
            "human_discussion": [],
            "participant_content": "先暂停普通反馈。",
        },
    )
    denied = client.post(
        f"/api/therapeutic-assessment/safety-events/{event['id']}/resolve",
        headers={**headers["p-f07"], "Idempotency-Key": "f07-resolve-denied"},
        json={"resolution_evidence_ref": "evidence:participant"},
    )
    resolved = client.post(
        f"/api/therapeutic-assessment/safety-events/{event['id']}/resolve",
        headers={**headers["a-f07"], "Idempotency-Key": "f07-resolve"},
        json={"resolution_evidence_ref": "evidence:human-review-1"},
    )
    assert blocked.status_code == 409
    assert denied.status_code == 403
    assert resolved.status_code == 200
    assert resolved.get_json()["data"]["state"] == "resolved_by_human"


def test_missing_chain_kills_flow_and_restore_requires_resolution_evidence(tmp_path, monkeypatch):
    app = _app(tmp_path, monkeypatch)
    headers = _seed(app)
    client = app.test_client()
    case = _case(client, headers)
    event = _signal(client, headers, case["id"], "f07-no-chain").get_json()["data"]
    killed = client.get("/api/therapeutic-assessment/safety/status", headers=headers["p-f07"])
    premature = client.post(
        "/api/therapeutic-assessment/safety/runtime/restore",
        headers=headers["a-f07"],
        json={"restoration_evidence_ref": "evidence:too-early"},
    )
    assert killed.get_json()["data"]["ordinary_flow_enabled"] is False
    assert premature.status_code == 409
    assert _chain(client, headers, case["id"], "f07-chain-after").status_code == 200
    assert client.post(
        f"/api/therapeutic-assessment/safety-events/{event['id']}/resolve",
        headers={**headers["a-f07"], "Idempotency-Key": "f07-resolve-after"},
        json={"resolution_evidence_ref": "evidence:human-review-after"},
    ).status_code == 200
    restored = client.post(
        "/api/therapeutic-assessment/safety/runtime/restore",
        headers=headers["a-f07"],
        json={"restoration_evidence_ref": "evidence:runtime-review"},
    )
    assert restored.status_code == 200
    assert restored.get_json()["data"]["ordinary_flow_enabled"] is True


def test_participant_status_does_not_expose_other_cases_or_internal_reason(tmp_path, monkeypatch):
    app = _app(tmp_path, monkeypatch)
    headers = _seed(app)
    client = app.test_client()
    case = _case(client, headers)
    _signal(client, headers, case["id"], "f07-private-signal")

    other = client.get("/api/therapeutic-assessment/safety/status", headers=headers["p2-f07"])
    owner = client.get("/api/therapeutic-assessment/safety/status", headers=headers["p-f07"])
    admin = client.get("/api/therapeutic-assessment/safety/status", headers=headers["a-f07"])

    assert other.get_json()["data"]["needs_human_understanding_count"] == 0
    assert owner.get_json()["data"]["needs_human_understanding_count"] == 1
    assert "pause_reason" not in other.get_json()["data"]
    assert "pause_reason" not in owner.get_json()["data"]
    assert admin.get_json()["data"]["pause_reason"] == "responsibility_chain_unavailable"


def test_queue_timeout_activates_kill_switch(tmp_path, monkeypatch):
    app = _app(tmp_path, monkeypatch)
    headers = _seed(app)
    client = app.test_client()
    case = _case(client, headers)
    _chain(client, headers, case["id"])
    event = _signal(client, headers, case["id"], "f07-timeout").get_json()["data"]
    with app.app_context():
        from database import get_connection
        with get_connection() as conn:
            conn.execute(
                "UPDATE therapeutic_assessment_safety_events SET created_at = '2020-01-01T00:00:00+00:00' WHERE id = ?",
                (event["id"],),
            )
            conn.commit()
    status = client.get("/api/therapeutic-assessment/safety/status", headers=headers["a-f07"])
    assert status.status_code == 200
    assert status.get_json()["data"]["ordinary_flow_enabled"] is False
    assert status.get_json()["data"]["pause_reason"] == "human_queue_timeout"
