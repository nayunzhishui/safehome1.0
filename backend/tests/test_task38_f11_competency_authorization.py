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
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "f11.sqlite3"))
    monkeypatch.setenv("CONTENT_DIR", str(ROOT / "content"))
    return importlib.import_module("app").app


def _seed(app):
    users = {
        "p-f11": "parent",
        "r-f11": "researcher",
        "r2-f11": "researcher",
        "s-f11": "supervisor",
        "a-f11": "admin",
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


def _case(client, headers, key="f11-case"):
    created = client.post(
        "/api/therapeutic-assessment/cases",
        headers={**headers["p-f11"], "Idempotency-Key": key},
        json={
            "assessment_question": "我想理解一次沟通中停下来的时刻",
            "shared_scope": ["question"],
            "consent": True,
        },
    )
    case = created.get_json()["data"]
    assigned = client.post(
        f"/api/therapeutic-assessment/cases/{case['id']}/assign",
        headers={**headers["s-f11"], "Idempotency-Key": f"{key}-assign"},
        json={"researcher_id": "r-f11"},
    )
    assert created.status_code == 201
    assert assigned.status_code == 200
    return assigned.get_json()["data"]


def _grant(
    client,
    headers,
    *,
    user_id,
    level,
    task_code,
    scope,
    key,
    starts_at=None,
    expires_at=None,
):
    now = datetime.now(timezone.utc)
    return client.post(
        "/api/therapeutic-assessment/competency/authorizations",
        headers={**headers["a-f11"], "Idempotency-Key": key},
        json={
            "user_id": user_id,
            "competency_level": level,
            "task_code": task_code,
            "scope": scope,
            "supervisor_user_id": "a-f11",
            "evidence_ref": f"evidence:{key}",
            "starts_at": starts_at or (now - timedelta(minutes=1)).isoformat(),
            "expires_at": expires_at or (now + timedelta(days=30)).isoformat(),
        },
    )


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


def test_schema_040_adds_competency_authorization_ledger(tmp_path, monkeypatch):
    app = _app(tmp_path, monkeypatch)
    with app.app_context():
        from database import CURRENT_SCHEMA_NAME, CURRENT_SCHEMA_VERSION, get_connection

        with get_connection() as conn:
            tables = {
                row["name"]
                for row in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table'"
                )
            }
            authorization_columns = {
                row["name"]
                for row in conn.execute(
                    "PRAGMA table_info(therapeutic_assessment_authorizations)"
                )
            }
        assert {
            "therapeutic_assessment_authorizations",
            "therapeutic_assessment_authorization_events",
        }.issubset(tables)
        assert "status_reason" in authorization_columns
        assert CURRENT_SCHEMA_VERSION >= "2026_07_27_040"
        assert CURRENT_SCHEMA_NAME == "therapeutic_assessment_competency_authorization"


def test_roles_and_showcase_do_not_replace_task_authorization(tmp_path, monkeypatch):
    app = _app(tmp_path, monkeypatch)
    headers = _seed(app)
    client = app.test_client()
    case = _case(client, headers)

    ungranted = client.put(
        f"/api/therapeutic-assessment/cases/{case['id']}/researcher-workbench/draft",
        headers={**headers["r-f11"], "Idempotency-Key": "f11-no-grant"},
        json={
            "internal_notes": "仅供团队整理",
            "participant_visible_draft": "这份理解可以一起核对。",
            "filters": {},
            "expected_version": 0,
        },
    )
    ordinary_grant = _grant(
        client,
        {**headers, "a-f11": headers["p-f11"]},
        user_id="r-f11",
        level="T1",
        task_code="workbench_draft",
        scope={"case_ids": [case["id"]]},
        key="f11-ordinary-grant",
    )
    effective = client.get(
        f"/api/therapeutic-assessment/competency/effective?case_id={case['id']}&task_code=workbench_draft",
        headers=headers["r-f11"],
    )

    assert ungranted.status_code == 403
    assert ungranted.get_json()["error"]["code"] == "competency_authorization_required"
    assert ordinary_grant.status_code == 403
    assert effective.get_json()["data"]["authorized"] is False


def test_t1_and_t2_are_task_and_scope_bound(tmp_path, monkeypatch):
    app = _app(tmp_path, monkeypatch)
    headers = _seed(app)
    client = app.test_client()
    case = _case(client, headers)
    other = _case(client, headers, "f11-other")

    t1 = _grant(
        client,
        headers,
        user_id="r-f11",
        level="T1",
        task_code="workbench_draft",
        scope={"case_ids": [case["id"]]},
        key="f11-t1",
    )
    organized = _grant(
        client,
        headers,
        user_id="r-f11",
        level="T1",
        task_code="evidence_organize",
        scope={"case_ids": [case["id"]]},
        key="f11-t1-evidence",
    )
    saved = client.put(
        f"/api/therapeutic-assessment/cases/{case['id']}/researcher-workbench/draft",
        headers={**headers["r-f11"], "Idempotency-Key": "f11-draft"},
        json={
            "internal_notes": "只整理原话与状态",
            "participant_visible_draft": "这份理解可以一起核对。",
            "filters": {},
            "expected_version": 0,
        },
    )
    wrong_task = client.post(
        f"/api/therapeutic-assessment/cases/{case['id']}/feedback-versions",
        headers={**headers["r-f11"], "Idempotency-Key": "f11-feedback-denied"},
        json=_feedback_payload(),
    )
    wrong_scope = client.put(
        f"/api/therapeutic-assessment/cases/{other['id']}/researcher-workbench/draft",
        headers={**headers["r-f11"], "Idempotency-Key": "f11-other-draft"},
        json={
            "internal_notes": "不能跨对象范围",
            "participant_visible_draft": "",
            "filters": {},
            "expected_version": 0,
        },
    )
    insufficient = _grant(
        client,
        headers,
        user_id="r-f11",
        level="T1",
        task_code="feedback_draft",
        scope={"case_ids": [case["id"]]},
        key="f11-insufficient",
    )
    observation = client.post(
        f"/api/therapeutic-assessment/cases/{case['id']}/evidence",
        headers={**headers["r-f11"], "Idempotency-Key": "f11-o"},
        json={
            "kind": "O",
            "content": "参与者在一次对话中停顿了几秒",
            "source_ref": "diary:f11",
            "provider_id": "p-f11",
            "observed_at": "2026-07-27T10:00:00+08:00",
            "context": "一次具体对话",
            "visibility_scope": ["participant", "research_team"],
        },
    )
    pattern = client.post(
        f"/api/therapeutic-assessment/cases/{case['id']}/evidence",
        headers={**headers["r-f11"], "Idempotency-Key": "f11-p"},
        json={
            "kind": "P",
            "content": "两次相似情境都出现停顿",
            "source_origin": "human",
            "applicability_scope": "相似对话",
            "exceptions": ["其它情境未知"],
            "time_window": "最近两周",
            "supporting_evidence": [
                {"ref": "diary:1", "source": "diary"},
                {"ref": "diary:2", "source": "diary"},
            ],
            "visibility_scope": ["research_team"],
        },
    )

    assert t1.status_code == 201
    assert organized.status_code == 201
    assert saved.status_code == 200
    assert wrong_task.status_code == 403
    assert wrong_scope.status_code == 403
    assert insufficient.status_code == 422
    assert insufficient.get_json()["error"]["code"] == "insufficient_competency"
    assert observation.status_code == 201
    assert pattern.status_code == 403
    assert pattern.get_json()["error"]["code"] == "competency_authorization_required"


def test_case_scope_change_requires_new_authorization(tmp_path, monkeypatch):
    app = _app(tmp_path, monkeypatch)
    headers = _seed(app)
    client = app.test_client()
    case = _case(client, headers)
    granted = _grant(
        client,
        headers,
        user_id="r-f11",
        level="T1",
        task_code="workbench_draft",
        scope={"case_ids": [case["id"]]},
        key="f11-scope-change",
    )
    ready = client.post(
        f"/api/therapeutic-assessment/cases/{case['id']}/readiness",
        headers={**headers["s-f11"], "Idempotency-Key": "f11-scope-ready"},
        json={
            "qualification_evidence_ref": "evidence:q-scope-f11",
            "supervision_evidence_ref": "evidence:s-scope-f11",
            "ethics_evidence_ref": "evidence:e-scope-f11",
        },
    )
    effective = client.get(
        f"/api/therapeutic-assessment/competency/effective?case_id={case['id']}&task_code=workbench_draft",
        headers=headers["r-f11"],
    )

    assert granted.status_code == 201
    assert ready.status_code == 200
    assert effective.status_code == 200
    assert effective.get_json()["data"]["authorized"] is False


def test_t2_draft_t3_review_expiry_and_revocation(tmp_path, monkeypatch):
    app = _app(tmp_path, monkeypatch)
    headers = _seed(app)
    client = app.test_client()
    case = _case(client, headers)
    ready = client.post(
        f"/api/therapeutic-assessment/cases/{case['id']}/readiness",
        headers={**headers["s-f11"], "Idempotency-Key": "f11-ready"},
        json={
            "qualification_evidence_ref": "evidence:q-f11",
            "supervision_evidence_ref": "evidence:s-f11",
            "ethics_evidence_ref": "evidence:e-f11",
        },
    )
    assert ready.status_code == 200
    t2 = _grant(
        client,
        headers,
        user_id="r-f11",
        level="T2",
        task_code="feedback_draft",
        scope={"case_ids": [case["id"]]},
        key="f11-t2",
    )
    t3 = _grant(
        client,
        headers,
        user_id="s-f11",
        level="T3",
        task_code="feedback_review",
        scope={"case_ids": [case["id"]]},
        key="f11-t3",
    )
    draft = client.post(
        f"/api/therapeutic-assessment/cases/{case['id']}/feedback-versions",
        headers={**headers["r-f11"], "Idempotency-Key": "f11-feedback"},
        json=_feedback_payload(),
    )
    reviewed = client.post(
        f"/api/therapeutic-assessment/feedback-versions/{draft.get_json()['data']['id']}/review",
        headers={**headers["s-f11"], "Idempotency-Key": "f11-review"},
        json={"decision": "approved"},
    )
    revoked = client.patch(
        f"/api/therapeutic-assessment/competency/authorizations/{t3.get_json()['data']['id']}/revoke",
        headers={**headers["a-f11"], "Idempotency-Key": "f11-revoke"},
        json={"reason": "任务结束", "expected_version": 1},
    )
    denied_after_revoke = client.post(
        f"/api/therapeutic-assessment/feedback-versions/{draft.get_json()['data']['id']}/send",
        headers={**headers["s-f11"], "Idempotency-Key": "f11-send-after-revoke"},
    )
    past = datetime.now(timezone.utc) - timedelta(days=3)
    expired = _grant(
        client,
        headers,
        user_id="r2-f11",
        level="T1",
        task_code="workbench_draft",
        scope={"case_ids": [case["id"]]},
        key="f11-expired",
        starts_at=past.isoformat(),
        expires_at=(past + timedelta(days=1)).isoformat(),
    )
    expired_effective = client.get(
        f"/api/therapeutic-assessment/competency/effective?case_id={case['id']}&task_code=workbench_draft",
        headers=headers["r2-f11"],
    )

    assert t2.status_code == 201
    assert t3.status_code == 201
    assert draft.status_code == 201
    assert reviewed.status_code == 200
    assert revoked.status_code == 200
    assert revoked.get_json()["data"]["status"] == "revoked"
    assert denied_after_revoke.status_code == 403
    assert expired.status_code == 201
    assert expired_effective.get_json()["data"]["authorized"] is False


def test_major_safety_event_requires_authorization_recheck(tmp_path, monkeypatch):
    app = _app(tmp_path, monkeypatch)
    headers = _seed(app)
    client = app.test_client()
    case = _case(client, headers)
    granted = _grant(
        client,
        headers,
        user_id="r-f11",
        level="T1",
        task_code="workbench_draft",
        scope={"case_ids": [case["id"]]},
        key="f11-major-grant",
    )
    signal = client.post(
        f"/api/therapeutic-assessment/cases/{case['id']}/safety-signals",
        headers={**headers["p-f11"], "Idempotency-Key": "f11-major-signal"},
        json={
            "signal_type": "violence",
            "source_ref": "participant:self-report",
            "reason_summary": "需要真人进一步了解",
        },
    )
    effective = client.get(
        f"/api/therapeutic-assessment/competency/effective?case_id={case['id']}&task_code=workbench_draft",
        headers=headers["r-f11"],
    )

    assert granted.status_code == 201
    assert signal.status_code == 201
    assert effective.get_json()["data"]["authorized"] is False
    with app.app_context():
        from database import get_connection

        with get_connection() as conn:
            authorization = conn.execute(
                "SELECT status, status_reason FROM therapeutic_assessment_authorizations WHERE id = ?",
                (granted.get_json()["data"]["id"],),
            ).fetchone()
            event = conn.execute(
                "SELECT action FROM therapeutic_assessment_authorization_events WHERE authorization_id = ? ORDER BY created_at DESC LIMIT 1",
                (granted.get_json()["data"]["id"],),
            ).fetchone()
        assert authorization["status"] == "review_required"
        assert authorization["status_reason"] == "major_incident_recheck"
        assert event["action"] == "review_required"


def test_f11_migration_plan_apply_verify_and_logical_rollback(tmp_path):
    database_path = tmp_path / "f11-migration.sqlite3"
    env = os.environ.copy()
    env.update(
        {
            "APP_ENV": "testing",
            "DATABASE_PATH": str(database_path),
            "CONTENT_DIR": str(ROOT / "content"),
        }
    )
    script = BACKEND / "scripts" / "migrate_task38_f11_competency_authorization.py"
    plan = subprocess.run(
        [sys.executable, str(script), "plan"],
        cwd=str(BACKEND),
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    applied = subprocess.run(
        [sys.executable, str(script), "apply"],
        cwd=str(BACKEND),
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    verified = subprocess.run(
        [sys.executable, str(script), "verify"],
        cwd=str(BACKEND),
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    rollback = subprocess.run(
        [sys.executable, str(script), "rollback"],
        cwd=str(BACKEND),
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert plan.returncode == 1
    assert applied.returncode == 0
    assert verified.returncode == 0
    assert '"ok": true' in verified.stdout.lower()
    assert rollback.returncode == 0
    assert '"tables_dropped": false' in rollback.stdout.lower()
