import importlib
import os
import subprocess
import sys
from datetime import date, timedelta
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"


def _app(tmp_path, monkeypatch):
    sys.path.insert(0, str(BACKEND))
    for name in list(sys.modules):
        if name in {"app", "config", "database", "models"} or name.startswith(("routes.", "services.")):
            sys.modules.pop(name, None)
    monkeypatch.setenv("APP_ENV", "testing")
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "f10.sqlite3"))
    monkeypatch.setenv("CONTENT_DIR", str(ROOT / "content"))
    return importlib.import_module("app").app


def _seed(app):
    users = {"p-f10": "parent", "p2-f10": "parent", "r-f10": "researcher", "s-f10": "supervisor"}
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
            user_id: {"Authorization": f"Bearer {generate_auth_token({'id': user_id, 'role': role})}"}
            for user_id, role in users.items()
        }


def _ready_case(client, headers):
    created = client.post(
        "/api/therapeutic-assessment/cases",
        headers={**headers["p-f10"], "Idempotency-Key": "f10-case"},
        json={"assessment_question": "我想理解一次沟通", "shared_scope": ["question"], "consent": True},
    ).get_json()["data"]
    client.post(
        f"/api/therapeutic-assessment/cases/{created['id']}/assign",
        headers={**headers["s-f10"], "Idempotency-Key": "f10-assign"},
        json={"researcher_id": "r-f10"},
    )
    client.post(
        f"/api/therapeutic-assessment/cases/{created['id']}/readiness",
        headers={**headers["s-f10"], "Idempotency-Key": "f10-ready"},
        json={
            "qualification_evidence_ref": "evidence:qualification-f10",
            "supervision_evidence_ref": "evidence:supervision-f10",
            "ethics_evidence_ref": "evidence:ethics-f10",
        },
    )
    draft = client.post(
        f"/api/therapeutic-assessment/cases/{created['id']}/feedback-versions",
        headers={**headers["r-f10"], "Idempotency-Key": "f10-feedback"},
        json={
            "source": "human",
            "feedback_layer": "layer_1",
            "letter_title": "给你的阶段性反馈",
            "observations": ["你记录了先停下来"],
            "evidence": ["participant:self-report"],
            "alternatives": ["也可能是当时需要整理思路"],
            "uncertainty": "目前只有一次记录。",
            "next_step": "可以选择一个低压力的小动作。",
            "human_discussion": ["哪些描述贴近你的体验？"],
            "participant_content": "从这次记录看，你先停下来；这只是当前理解，可以不同意。",
        },
    ).get_json()["data"]
    client.post(
        f"/api/therapeutic-assessment/feedback-versions/{draft['id']}/review",
        headers={**headers["s-f10"], "Idempotency-Key": "f10-review"},
        json={"decision": "approved"},
    )
    client.post(
        f"/api/therapeutic-assessment/feedback-versions/{draft['id']}/send",
        headers={**headers["s-f10"], "Idempotency-Key": "f10-send"},
    )
    return created["id"], draft["id"]


def _action_payload(feedback_id, **overrides):
    payload = {
        "feedback_version_id": feedback_id,
        "action_text": "下一次回应前先停顿三秒。",
        "purpose_text": "给自己一点整理思路的空间。",
        "planned_date": date.today().isoformat(),
        "reminder_mode": "in_app",
        "reminder_privacy": "generic_preview",
        "stop_conditions": ["如果冲突升级或我不再愿意，就先停止。"],
        "setback_plan": "只记录当时的阻碍，不责备自己。",
        "training_card_id": "emotion_naming",
        "voluntary_confirmed": True,
        "reversible_confirmed": True,
        "stoppable_confirmed": True,
    }
    payload.update(overrides)
    return payload


def test_schema_039_adds_action_followup_fields(tmp_path, monkeypatch):
    app = _app(tmp_path, monkeypatch)
    with app.app_context():
        from database import CURRENT_SCHEMA_VERSION, get_connection

        with get_connection() as conn:
            columns = {
                row["name"]
                for row in conn.execute("PRAGMA table_info(therapeutic_assessment_actions)")
            }
        assert {
            "purpose_text",
            "planned_date",
            "reminder_mode",
            "reminder_privacy",
            "stop_conditions_json",
            "setback_plan",
            "training_card_id",
            "linked_checkin_id",
            "version",
            "completed_at",
        }.issubset(columns)
        assert CURRENT_SCHEMA_VERSION >= "2026_07_27_039"


def test_action_requires_scope_and_explicit_safety_choice(tmp_path, monkeypatch):
    app = _app(tmp_path, monkeypatch)
    headers = _seed(app)
    client = app.test_client()
    case_id, feedback_id = _ready_case(client, headers)

    missing_confirmation = client.post(
        f"/api/therapeutic-assessment/cases/{case_id}/actions",
        headers={**headers["p-f10"], "Idempotency-Key": "f10-no-confirm"},
        json=_action_payload(feedback_id, voluntary_confirmed=False),
    )
    invalid_card = client.post(
        f"/api/therapeutic-assessment/cases/{case_id}/actions",
        headers={**headers["p-f10"], "Idempotency-Key": "f10-invalid-card"},
        json=_action_payload(feedback_id, training_card_id="missing-card"),
    )
    with app.app_context():
        from database import get_connection

        with get_connection() as conn:
            conn.execute(
                "UPDATE therapeutic_assessment_cases SET risk_level = 'high', safety_state = 'needs_human_review' WHERE id = ?",
                (case_id,),
            )
            conn.commit()
    high_risk = client.post(
        f"/api/therapeutic-assessment/cases/{case_id}/actions",
        headers={**headers["p-f10"], "Idempotency-Key": "f10-high-risk"},
        json=_action_payload(feedback_id),
    )

    assert missing_confirmation.status_code == 422
    assert missing_confirmation.get_json()["error"]["code"] == "action_safety_confirmation_required"
    assert invalid_card.status_code == 422
    assert high_risk.status_code == 409


def test_action_followup_is_owned_versioned_and_returns_to_evidence(tmp_path, monkeypatch):
    app = _app(tmp_path, monkeypatch)
    headers = _seed(app)
    client = app.test_client()
    case_id, feedback_id = _ready_case(client, headers)

    created = client.post(
        f"/api/therapeutic-assessment/cases/{case_id}/actions",
        headers={**headers["p-f10"], "Idempotency-Key": "f10-action"},
        json=_action_payload(feedback_id),
    )
    replay = client.post(
        f"/api/therapeutic-assessment/cases/{case_id}/actions",
        headers={**headers["p-f10"], "Idempotency-Key": "f10-action"},
        json=_action_payload(feedback_id),
    )
    action = created.get_json()["data"]
    other_owner = client.patch(
        f"/api/therapeutic-assessment/actions/{action['id']}",
        headers={**headers["p2-f10"], "Idempotency-Key": "f10-other"},
        json={"status": "completed", "expected_version": 1},
    )
    completed = client.patch(
        f"/api/therapeutic-assessment/actions/{action['id']}",
        headers={**headers["p-f10"], "Idempotency-Key": "f10-complete"},
        json={"status": "completed", "followup_note": "我注意到自己更能说清当时发生了什么。", "expected_version": 1},
    )
    stale = client.patch(
        f"/api/therapeutic-assessment/actions/{action['id']}",
        headers={**headers["p-f10"], "Idempotency-Key": "f10-stale"},
        json={"status": "stopped", "expected_version": 1},
    )
    followup = client.post(
        f"/api/therapeutic-assessment/actions/{action['id']}/followups",
        headers={**headers["p-f10"], "Idempotency-Key": "f10-followup"},
        json={
            "kind": "O",
            "content": "我停顿后注意到自己仍然紧张，但更容易描述具体事件。",
            "observed_at": "2026-07-27T12:00:00+08:00",
        },
    )
    forbidden_kind = client.post(
        f"/api/therapeutic-assessment/actions/{action['id']}/followups",
        headers={**headers["p-f10"], "Idempotency-Key": "f10-pattern"},
        json={"kind": "P", "content": "把一次完成解释成稳定模式"},
    )

    assert created.status_code == 201
    assert replay.status_code == 200 and replay.get_json()["data"]["id"] == action["id"]
    assert other_owner.status_code == 403
    assert completed.status_code == 200 and completed.get_json()["data"]["version"] == 2
    assert stale.status_code == 409
    assert followup.status_code == 201
    assert followup.get_json()["data"]["source_ref"] == f"therapeutic-action:{action['id']}"
    assert "不代表疗效" in followup.get_json()["data"]["method_limitations"]
    assert forbidden_kind.status_code == 422

    detail = client.get(f"/api/therapeutic-assessment/cases/{case_id}", headers=headers["p-f10"])
    assert detail.get_json()["data"]["efficacy_score"] is None
    week_start = (date.today() - timedelta(days=date.today().weekday())).isoformat()
    report = client.get(
        f"/api/weekly-report?week_start={week_start}",
        headers=headers["p-f10"],
    )
    summary = report.get_json()["data"]["therapeutic_action_summary"]
    assert summary["completed_count"] == 1
    assert "不把完成次数解释为疗效" in summary["interpretation_boundary"]


def test_migration_is_additive_and_production_guarded(tmp_path):
    database_path = tmp_path / "migration-f10.sqlite3"
    env = {
        **os.environ,
        "APP_ENV": "testing",
        "DATABASE_PATH": str(database_path),
        "CONTENT_DIR": str(ROOT / "content"),
    }
    applied = subprocess.run(
        [sys.executable, str(BACKEND / "scripts/migrate_task38_f10_action_followup.py"), "apply"],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
    )
    blocked = subprocess.run(
        [sys.executable, str(BACKEND / "scripts/migrate_task38_f10_action_followup.py"), "apply"],
        cwd=ROOT,
        env={**env, "APP_ENV": "production"},
        capture_output=True,
        text=True,
    )
    rolled_back = subprocess.run(
        [sys.executable, str(BACKEND / "scripts/migrate_task38_f10_action_followup.py"), "rollback"],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
    )
    assert applied.returncode == 0 and '"ok": true' in applied.stdout.lower()
    assert blocked.returncode != 0 and "生产迁移已阻断" in blocked.stderr
    assert rolled_back.returncode == 0 and '"history_deleted": false' in rolled_back.stdout.lower()
