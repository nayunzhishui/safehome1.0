import importlib
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = PROJECT_ROOT / "backend"


def _fresh_app(tmp_path, monkeypatch):
    sys.path.insert(0, str(BACKEND_ROOT))
    for name in list(sys.modules):
        if name in {"app", "config", "database", "models"} or name.startswith("routes.") or name.startswith("services."):
            sys.modules.pop(name, None)
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "safehome-test.sqlite3"))
    monkeypatch.setenv("CONTENT_DIR", str(PROJECT_ROOT / "content"))
    monkeypatch.setenv("SAFETY_SCHEDULER_ENABLED", "1")
    monkeypatch.delenv("DB_PROVIDER", raising=False)
    module = importlib.import_module("app")
    return module.app


def _now(offset_minutes=0):
    return (datetime.now(timezone.utc) + timedelta(minutes=offset_minutes)).isoformat()


def _risk_row(conn, review_id="risk-f15", due_at=None):
    timestamp = _now(-60)
    conn.execute(
        """INSERT INTO risk_review_records
        (id, user_id, source_type, source_id, risk_level, matched_categories_json,
         review_status, safety_route, priority, due_at, review_version, created_at, updated_at)
        VALUES (?, 'user-f15', 'feedback', 'feedback-f15', 'medium', '[]',
                'pending', 'human_review', 'high', ?, 0, ?, ?)""",
        (review_id, due_at or _now(-1), timestamp, timestamp),
    )


def test_due_risk_is_escalated_once_with_idempotent_event(tmp_path, monkeypatch):
    _fresh_app(tmp_path, monkeypatch)
    import database
    from services.safety_scheduler_service import run_safety_scheduler

    with database.get_connection() as conn:
        _risk_row(conn)
        conn.commit()
    first = run_safety_scheduler("worker-a", now=_now(), run_key="risk-once")
    second = run_safety_scheduler("worker-a", now=_now(), run_key="risk-once")
    with database.get_connection() as conn:
        row = conn.execute("SELECT * FROM risk_review_records WHERE id = 'risk-f15'").fetchone()
        events = conn.execute("SELECT COUNT(*) AS count FROM safety_scheduler_events WHERE source_id = 'risk-f15'").fetchone()["count"]
    assert first["risk_escalated"] == 1
    assert second == first
    assert row["review_status"] == "priority_review"
    assert row["escalated_at"]
    assert events == 1


def test_overdue_therapeutic_item_is_handed_off_and_queue_pauses(tmp_path, monkeypatch):
    _fresh_app(tmp_path, monkeypatch)
    import database
    from services.safety_scheduler_service import run_safety_scheduler

    with database.get_connection() as conn:
        timestamp = _now(-60)
        conn.execute("INSERT INTO therapeutic_assessment_cases (id, participant_user_id, assessment_question, consent_status, status, workflow_state, safety_state, risk_level, complexity_scope, readiness_level, version, created_by, created_at, updated_at) VALUES ('case-f15', 'user-f15', 'synthetic question', 'agreed', 'open', 'open', 'standard', 'low', 'single', 'L1', 1, 'system', ?, ?)", (timestamp, timestamp))
        conn.execute("INSERT INTO therapeutic_assessment_work_queue (id, case_id, queue_type, task_code, required_competency, priority, status, scope_snapshot_json, due_at, version, created_by, created_at, updated_at) VALUES ('queue-f15', 'case-f15', 'risk', 'feedback_review', 'T3', 'urgent', 'open', '{}', ?, 1, 'system', ?, ?)", (_now(-1), timestamp, timestamp))
        conn.commit()
    result = run_safety_scheduler("worker-a", now=_now(), run_key="queue-overdue")
    with database.get_connection() as conn:
        item = conn.execute("SELECT status FROM therapeutic_assessment_work_queue WHERE id = 'queue-f15'").fetchone()
        runtime = conn.execute("SELECT * FROM therapeutic_assessment_queue_runtime WHERE id = 'global'").fetchone()
        scheduler_runtime = conn.execute("SELECT * FROM safety_scheduler_runtime WHERE id = 'global'").fetchone()
    assert result["therapeutic_escalated"] == 1
    assert item["status"] == "handoff_required"
    assert runtime["paused"] == 1
    assert runtime["unattended_urgent_count"] == 1
    assert scheduler_runtime["kill_switch"] == 1


def test_safety_timeout_is_killed_by_scheduler_without_read_request(tmp_path, monkeypatch):
    _fresh_app(tmp_path, monkeypatch)
    import database
    from services.safety_scheduler_service import run_safety_scheduler

    with database.get_connection() as conn:
        timestamp = _now(-60)
        conn.execute("INSERT INTO therapeutic_assessment_cases (id, participant_user_id, assessment_question, consent_status, status, workflow_state, safety_state, risk_level, complexity_scope, readiness_level, version, created_by, created_at, updated_at) VALUES ('case-timeout', 'user-f15', 'synthetic question', 'agreed', 'support_required', 'safety_path', 'safety_path', 'high', 'single', 'L1', 1, 'system', ?, ?)", (timestamp, timestamp))
        conn.execute("INSERT INTO therapeutic_assessment_responsibility_chains (id, case_id, responsible_user_id, supervisor_user_id, support_channel, evidence_ref, status, queue_timeout_minutes, version, idempotency_key, created_at, updated_at) VALUES ('chain-f15', 'case-timeout', 'r1', 's1', 'phone', 'synthetic', 'active', 5, 1, 'chain-key', ?, ?)", (timestamp, timestamp))
        conn.execute("INSERT INTO therapeutic_assessment_safety_events (id, case_id, signal_type, state, source_ref, detected_by, idempotency_key, created_at, updated_at) VALUES ('event-f15', 'case-timeout', 'self_harm', 'needs_human_understanding', 'synthetic', 'user-f15', 'event-key', ?, ?)", (timestamp, timestamp))
        conn.commit()
    result = run_safety_scheduler("worker-a", now=_now(), run_key="safety-timeout")
    with database.get_connection() as conn:
        runtime = conn.execute("SELECT * FROM therapeutic_assessment_runtime_control WHERE id = 'global'").fetchone()
        scheduler_runtime = conn.execute("SELECT * FROM safety_scheduler_runtime WHERE id = 'global'").fetchone()
    assert result["safety_timeouts"] == 1
    assert runtime["killed"] == 1
    assert runtime["reason"] == "human_queue_timeout"
    assert scheduler_runtime["kill_switch"] == 1


def test_concurrent_workers_only_one_claims_the_scheduler_lease(tmp_path, monkeypatch):
    _fresh_app(tmp_path, monkeypatch)
    import database
    from services.safety_scheduler_service import SchedulerBusy, run_safety_scheduler

    with database.get_connection() as conn:
        _risk_row(conn)
        conn.commit()

    def run(worker):
        try:
            return run_safety_scheduler(worker, now=_now(), run_key=f"concurrent-{worker}", hold_lease=True)["status"]
        except SchedulerBusy:
            return "busy"

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(run, ["one", "two"]))
    assert sorted(outcomes) == ["busy", "leased"]


def test_expired_lease_is_reclaimed_after_worker_restart(tmp_path, monkeypatch):
    _fresh_app(tmp_path, monkeypatch)
    import database
    from services.safety_scheduler_service import run_safety_scheduler

    with database.get_connection() as conn:
        conn.execute("UPDATE safety_scheduler_runtime SET lease_owner = 'dead-worker', lease_expires_at = ? WHERE id = 'global'", (_now(-1),))
        _risk_row(conn)
        conn.commit()
    result = run_safety_scheduler("replacement", now=_now(), run_key="restart")
    assert result["reclaimed_expired_lease"] is True
    assert result["risk_escalated"] == 1


def test_repeated_failures_enter_dead_letter_and_metrics(tmp_path, monkeypatch):
    _fresh_app(tmp_path, monkeypatch)
    from services.safety_scheduler_service import SchedulerRunFailed, run_safety_scheduler, scheduler_status

    for attempt in range(3):
        try:
            run_safety_scheduler("worker-a", now=_now(), run_key="failing-run", inject_failure="scan")
        except SchedulerRunFailed:
            pass
    status = scheduler_status()
    assert status["dead_letter_count"] == 1
    assert status["claim_failure_count"] == 3
    assert status["last_run_status"] == "dead_letter"


def test_pause_resume_backfill_requires_human_evidence(tmp_path, monkeypatch):
    _fresh_app(tmp_path, monkeypatch)
    import pytest
    from services.safety_scheduler_service import SchedulerError, set_scheduler_pause

    paused = set_scheduler_pause(True, actor_id="admin", reason="maintenance")
    assert paused["paused"] is True
    with pytest.raises(SchedulerError):
        set_scheduler_pause(False, actor_id="admin", reason="resume")
    resumed = set_scheduler_pause(False, actor_id="admin", reason="resume", evidence_ref="human-evidence-1")
    assert resumed["paused"] is False
    assert resumed["kill_switch"] is False
    assert resumed["backfill_required"] is True


def test_kill_switch_blocks_automation_but_not_low_risk_diary_save(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    import database
    from services.safety_scheduler_service import activate_unattended_kill_switch

    with database.get_connection() as conn:
        activate_unattended_kill_switch(conn, "synthetic_unattended")
        conn.commit()
    client = app.test_client()
    registered = client.post("/api/auth/register", json={"username": "f15-parent", "password": "password123", "role": "parent"}).get_json()["data"]
    headers = {"Authorization": f"Bearer {registered['token']}"}
    user_id = registered["user"]["id"]
    diary = client.post("/api/diaries", headers=headers, json={"user_id": user_id, "scene": "晚饭", "event_description": "普通记录", "parent_emotion": "平静"})
    feedback = client.post("/api/feedback/generate", headers=headers, json={"user_id": user_id, "event_description": "普通记录"})
    therapeutic = client.post(
        "/api/therapeutic-assessment/cases",
        headers={**headers, "Idempotency-Key": "f15-kill-switch"},
        json={"assessment_question": "我想共同理解最近一次沟通。", "shared_scope": ["question"], "consent": True},
    )
    assert diary.status_code == 201
    assert feedback.status_code == 503
    assert feedback.get_json()["error"]["code"] == "safety_scheduler_kill_switch"
    assert therapeutic.status_code == 503
    assert therapeutic.get_json()["error"]["code"] == "safety_scheduler_kill_switch"


def test_policy_uses_utc_and_does_not_fabricate_production_capacity(tmp_path, monkeypatch):
    _fresh_app(tmp_path, monkeypatch)
    import json
    from services.schema_migration_service import migration_manifest

    policy = json.loads((PROJECT_ROOT / "config" / "rc0810" / "safety_scheduler_policy.json").read_text(encoding="utf-8"))
    assert policy["clock"]["storage_timezone"] == "UTC"
    assert policy["human_capacity"]["status"] == "pending_external"
    assert policy["human_capacity"]["daily_safe_capacity"] is None
    assert policy["production_enabled"] is False
    versions = [item["version"] for item in migration_manifest()]
    assert versions[-2:] == ["2026_08_25_069", "2026_08_25_070"]
