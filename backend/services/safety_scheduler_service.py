"""Active UTC scheduler for risk SLA and therapeutic safety deadlines."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from config import Config
from database import get_connection, json_dumps, json_loads, new_id, now_iso, row_to_dict, write_audit_log
from services.schema_migration_service import apply_pending_schema_migrations


DISABLED_SCOPES = ["automatic_feedback", "free_text_ai", "therapeutic_intake"]
OPEN_RISK_STATUSES = ("pending", "priority_review")
OPEN_QUEUE_STATUSES = ("open", "claimed", "handoff_required")
OPEN_SAFETY_STATES = ("needs_human_understanding", "safety_paused", "human_taken_over")


@dataclass(frozen=True)
class SchedulerError(Exception):
    code: str
    message: str
    status: int = 409

    def __str__(self) -> str:
        return self.message


class SchedulerBusy(SchedulerError):
    def __init__(self):
        super().__init__("safety_scheduler_busy", "安全调度器已有有效租约。", 409)


class SchedulerRunFailed(SchedulerError):
    def __init__(self, status: str):
        super().__init__("safety_scheduler_run_failed", f"安全调度运行失败：{status}", 500)


def _utc(value: str | datetime | None = None) -> datetime:
    if value is None:
        return datetime.now(timezone.utc)
    parsed = value if isinstance(value, datetime) else datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat()


def _begin_write(conn) -> None:
    conn.commit()
    conn.execute("START TRANSACTION" if getattr(conn, "provider", "sqlite") == "mysql" else "BEGIN IMMEDIATE")


def _runtime(conn) -> dict:
    row = conn.execute("SELECT * FROM safety_scheduler_runtime WHERE id = 'global'").fetchone()
    if row is None:
        timestamp = now_iso()
        conn.execute(
            """INSERT INTO safety_scheduler_runtime
            (id, paused, kill_switch, disabled_scopes_json, version, updated_at)
            VALUES ('global', 0, 0, '[]', 1, ?)""",
            (timestamp,),
        )
        row = conn.execute("SELECT * FROM safety_scheduler_runtime WHERE id = 'global'").fetchone()
    return row_to_dict(row)


def _stats(row: dict) -> dict:
    return json_loads(row.get("stats_json"), {})


def _event(conn, *, key: str, source_type: str, source_id: str, action: str, due_at: str | None, metadata: dict, timestamp: str) -> None:
    conn.execute(
        """INSERT INTO safety_scheduler_events
        (id, event_key, source_type, source_id, action, due_at, metadata_json, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (new_id("safety_clock"), key, source_type, source_id, action, due_at, json_dumps(metadata), timestamp),
    )


def _claim(worker_id: str, now: datetime) -> tuple[bool, dict]:
    lease_expires = _iso(now + timedelta(seconds=int(Config.SAFETY_SCHEDULER_LEASE_SECONDS)))
    timestamp = _iso(now)
    with get_connection() as conn:
        apply_pending_schema_migrations(conn)
        _begin_write(conn)
        runtime = _runtime(conn)
        if runtime["paused"]:
            conn.rollback()
            raise SchedulerError("safety_scheduler_paused", "安全调度器已暂停。", 503)
        prior_owner = runtime.get("lease_owner")
        prior_expiry = runtime.get("lease_expires_at")
        active = prior_owner and prior_expiry and _utc(prior_expiry) > now and prior_owner != worker_id
        if active:
            conn.execute(
                "UPDATE safety_scheduler_runtime SET claim_failure_count = claim_failure_count + 1, updated_at = ? WHERE id = 'global'",
                (timestamp,),
            )
            conn.commit()
            raise SchedulerBusy()
        reclaimed = bool(prior_owner and prior_expiry and _utc(prior_expiry) <= now)
        cursor = conn.execute(
            """UPDATE safety_scheduler_runtime
            SET lease_owner = ?, lease_expires_at = ?, last_started_at = ?,
                version = version + 1, updated_at = ?
            WHERE id = 'global' AND version = ?""",
            (worker_id, lease_expires, timestamp, timestamp, runtime["version"]),
        )
        if cursor.rowcount != 1:
            conn.rollback()
            raise SchedulerBusy()
        conn.commit()
        return reclaimed, _runtime(conn)


def _release(conn, worker_id: str, timestamp: str) -> None:
    conn.execute(
        """UPDATE safety_scheduler_runtime SET lease_owner = NULL,
        lease_expires_at = NULL, version = version + 1, updated_at = ?
        WHERE id = 'global' AND lease_owner = ?""",
        (timestamp, worker_id),
    )


def _escalate_risks(conn, timestamp: str) -> int:
    rows = conn.execute(
        """SELECT * FROM risk_review_records
        WHERE review_status IN ('pending', 'priority_review')
          AND due_at IS NOT NULL AND due_at <= ?
        ORDER BY due_at, id""",
        (timestamp,),
    ).fetchall()
    count = 0
    for raw in rows:
        row = row_to_dict(raw)
        key = f"risk_review:{row['id']}:overdue:{row['due_at']}"
        if conn.execute("SELECT id FROM safety_scheduler_events WHERE event_key = ?", (key,)).fetchone():
            continue
        cursor = conn.execute(
            """UPDATE risk_review_records
            SET review_status = 'priority_review', priority = 'urgent',
                escalated_at = COALESCE(escalated_at, ?),
                review_version = review_version + 1, updated_at = ?
            WHERE id = ? AND review_version = ?
              AND review_status IN ('pending', 'priority_review') AND due_at <= ?""",
            (timestamp, timestamp, row["id"], row.get("review_version") or 0, timestamp),
        )
        if cursor.rowcount == 1:
            _event(conn, key=key, source_type="risk_review", source_id=row["id"], action="sla_escalated", due_at=row["due_at"], metadata={"raw_text_logged": False}, timestamp=timestamp)
            count += 1
    return count


def _escalate_therapeutic_queue(conn, timestamp: str) -> int:
    rows = conn.execute(
        """SELECT * FROM therapeutic_assessment_work_queue
        WHERE status IN ('open', 'claimed', 'handoff_required') AND due_at <= ?
        ORDER BY due_at, id""",
        (timestamp,),
    ).fetchall()
    count = 0
    for raw in rows:
        row = row_to_dict(raw)
        key = f"therapeutic_queue:{row['id']}:overdue:{row['due_at']}"
        if conn.execute("SELECT id FROM safety_scheduler_events WHERE event_key = ?", (key,)).fetchone():
            continue
        cursor = conn.execute(
            """UPDATE therapeutic_assessment_work_queue
            SET status = 'handoff_required', version = version + 1, updated_at = ?
            WHERE id = ? AND version = ? AND status IN ('open', 'claimed', 'handoff_required')
              AND due_at <= ?""",
            (timestamp, row["id"], row["version"], timestamp),
        )
        if cursor.rowcount == 1:
            _event(conn, key=key, source_type="therapeutic_queue", source_id=row["id"], action="sla_handoff_required", due_at=row["due_at"], metadata={"prior_status": row["status"]}, timestamp=timestamp)
            count += 1
    return count


def _scan_safety_timeouts(conn, timestamp: str) -> int:
    rows = conn.execute(
        """SELECT e.*, c.queue_timeout_minutes, c.status AS chain_status
        FROM therapeutic_assessment_safety_events e
        LEFT JOIN therapeutic_assessment_responsibility_chains c ON c.case_id = e.case_id
        WHERE e.state IN ('needs_human_understanding', 'safety_paused', 'human_taken_over')
        ORDER BY e.created_at, e.id"""
    ).fetchall()
    count = 0
    now = _utc(timestamp)
    for raw in rows:
        row = row_to_dict(raw)
        no_chain = row.get("chain_status") != "active"
        timed_out = no_chain or _utc(row["created_at"]) + timedelta(minutes=int(row.get("queue_timeout_minutes") or 0)) <= now
        if not timed_out:
            continue
        reason = "responsibility_chain_unavailable" if no_chain else "human_queue_timeout"
        key = f"therapeutic_safety:{row['id']}:{reason}"
        if conn.execute("SELECT id FROM safety_scheduler_events WHERE event_key = ?", (key,)).fetchone():
            continue
        conn.execute("UPDATE therapeutic_assessment_safety_events SET state = 'safety_paused', updated_at = ? WHERE id = ? AND state IN ('needs_human_understanding', 'human_taken_over', 'safety_paused')", (timestamp, row["id"]))
        if conn.execute("SELECT id FROM therapeutic_assessment_runtime_control WHERE id = 'global'").fetchone():
            conn.execute("UPDATE therapeutic_assessment_runtime_control SET killed = 1, reason = ?, changed_by = 'safety_scheduler', changed_at = ? WHERE id = 'global'", (reason, timestamp))
        else:
            conn.execute("INSERT INTO therapeutic_assessment_runtime_control (id, killed, reason, changed_by, changed_at) VALUES ('global', 1, ?, 'safety_scheduler', ?)", (reason, timestamp))
        _event(conn, key=key, source_type="therapeutic_safety", source_id=row["id"], action="kill_switch_activated", due_at=None, metadata={"reason": reason}, timestamp=timestamp)
        count += 1
    return count


def _refresh_queue_runtime(conn, timestamp: str) -> dict:
    from services.therapeutic_assessment_queue_service import refresh_queue_runtime

    return refresh_queue_runtime(conn, timestamp=timestamp, actor_id="safety_scheduler")


def _backlog_metrics(conn, timestamp: str) -> tuple[int, int]:
    due_values = []
    for query in (
        "SELECT due_at FROM risk_review_records WHERE review_status IN ('pending', 'priority_review') AND due_at IS NOT NULL",
        "SELECT due_at FROM therapeutic_assessment_work_queue WHERE status IN ('open', 'claimed', 'handoff_required')",
    ):
        due_values.extend(str(row["due_at"]) for row in conn.execute(query).fetchall() if row["due_at"])
    oldest = max((int((_utc(timestamp) - _utc(value)).total_seconds()) for value in due_values), default=0)
    return len(due_values), max(0, oldest)


def run_safety_scheduler(worker_id: str, *, now: str | datetime | None = None, run_key: str | None = None, inject_failure: str | None = None, hold_lease: bool = False) -> dict:
    if not Config.SAFETY_SCHEDULER_ENABLED:
        raise SchedulerError("safety_scheduler_disabled", "当前环境未开启安全调度器。", 503)
    current = _utc(now)
    timestamp = _iso(current)
    key = str(run_key or f"scheduled:{timestamp[:16]}")
    reclaimed, _ = _claim(str(worker_id), current)
    with get_connection() as conn:
        apply_pending_schema_migrations(conn)
        existing = conn.execute("SELECT * FROM safety_scheduler_runs WHERE run_key = ?", (key,)).fetchone()
        if existing is not None and existing["status"] == "completed":
            result = _stats(row_to_dict(existing))
            _release(conn, str(worker_id), timestamp)
            conn.commit()
            return result
        attempts = int(existing["attempt_count"] if existing else 0)
        max_attempts = int(existing["max_attempts"] if existing else Config.SAFETY_SCHEDULER_MAX_ATTEMPTS)
        if existing is not None and existing["status"] == "dead_letter":
            _release(conn, str(worker_id), timestamp)
            conn.commit()
            raise SchedulerRunFailed("dead_letter")
        run_id = str(existing["id"]) if existing else new_id("safety_run")
        if existing is None:
            conn.execute("INSERT INTO safety_scheduler_runs (id, run_key, worker_id, status, attempt_count, max_attempts, started_at, lease_expires_at, stats_json, created_at, updated_at) VALUES (?, ?, ?, 'leased', 0, ?, ?, ?, '{}', ?, ?)", (run_id, key, worker_id, max_attempts, timestamp, _iso(current + timedelta(seconds=Config.SAFETY_SCHEDULER_LEASE_SECONDS)), timestamp, timestamp))
        else:
            conn.execute("UPDATE safety_scheduler_runs SET worker_id = ?, status = 'leased', started_at = ?, lease_expires_at = ?, updated_at = ? WHERE id = ?", (worker_id, timestamp, _iso(current + timedelta(seconds=Config.SAFETY_SCHEDULER_LEASE_SECONDS)), timestamp, run_id))
        conn.commit()
    if hold_lease:
        return {"status": "leased", "reclaimed_expired_lease": reclaimed}
    try:
        if inject_failure == "scan":
            raise RuntimeError("injected_scan_failure")
        with get_connection() as conn:
            _begin_write(conn)
            risk_count = _escalate_risks(conn, timestamp)
            queue_count = _escalate_therapeutic_queue(conn, timestamp)
            safety_count = _scan_safety_timeouts(conn, timestamp)
            queue_runtime = _refresh_queue_runtime(conn, timestamp)
            if queue_runtime["paused"] or safety_count:
                activate_unattended_kill_switch(
                    conn,
                    "human_queue_timeout"
                    if safety_count
                    else str(queue_runtime.get("reason") or "human_queue_unavailable"),
                )
            backlog, oldest = _backlog_metrics(conn, timestamp)
            result = {
                "status": "completed",
                "risk_escalated": risk_count,
                "therapeutic_escalated": queue_count,
                "safety_timeouts": safety_count,
                "queue_paused": bool(queue_runtime["paused"]),
                "backlog_count": backlog,
                "oldest_due_age_seconds": oldest,
                "reclaimed_expired_lease": reclaimed,
                "clock_timezone": "UTC",
            }
            conn.execute("UPDATE safety_scheduler_runs SET status = 'completed', finished_at = ?, lease_expires_at = NULL, stats_json = ?, updated_at = ? WHERE id = ?", (timestamp, json_dumps(result), timestamp, run_id))
            conn.execute("UPDATE safety_scheduler_runtime SET last_success_at = ?, backlog_count = ?, oldest_due_age_seconds = ?, backfill_required = 0, updated_at = ? WHERE id = 'global'", (timestamp, backlog, oldest, timestamp))
            _release(conn, str(worker_id), timestamp)
            write_audit_log(conn, "safety_scheduler_completed", str(worker_id), "safety_scheduler_run", run_id, {"run_key": key, "stats": result})
            conn.commit()
            return result
    except Exception as exc:
        with get_connection() as conn:
            _begin_write(conn)
            attempts += 1
            dead = attempts >= max_attempts
            status = "dead_letter" if dead else "retrying"
            conn.execute("UPDATE safety_scheduler_runs SET status = ?, attempt_count = ?, finished_at = ?, lease_expires_at = NULL, error_code = ?, updated_at = ? WHERE id = ?", (status, attempts, timestamp, type(exc).__name__, timestamp, run_id))
            if dead:
                activate_unattended_kill_switch(conn, "scheduler_dead_letter")
                write_audit_log(
                    conn,
                    "safety_scheduler_dead_letter_kill_switch_activated",
                    str(worker_id),
                    "safety_scheduler_run",
                    run_id,
                    {"run_key": key, "disabled_scopes": DISABLED_SCOPES},
                )
            conn.execute("UPDATE safety_scheduler_runtime SET last_failure_at = ?, claim_failure_count = claim_failure_count + 1, dead_letter_count = dead_letter_count + ?, updated_at = ? WHERE id = 'global'", (timestamp, int(dead), timestamp))
            _release(conn, str(worker_id), timestamp)
            conn.commit()
        raise SchedulerRunFailed(status) from exc


def scheduler_status() -> dict:
    with get_connection() as conn:
        apply_pending_schema_migrations(conn)
        runtime = _runtime(conn)
        latest = conn.execute("SELECT * FROM safety_scheduler_runs ORDER BY updated_at DESC LIMIT 1").fetchone()
        result = row_to_dict(runtime)
        result["paused"] = bool(result["paused"])
        result["kill_switch"] = bool(result["kill_switch"])
        result["backfill_required"] = bool(result["backfill_required"])
        result["disabled_scopes"] = json_loads(result.pop("disabled_scopes_json"), [])
        result["last_run_status"] = latest["status"] if latest else None
        return result


def set_scheduler_pause(paused: bool, *, actor_id: str, reason: str, evidence_ref: str | None = None) -> dict:
    if not paused and not evidence_ref:
        raise SchedulerError("human_evidence_required", "恢复安全调度必须提供真人证据。", 422)
    timestamp = now_iso()
    with get_connection() as conn:
        apply_pending_schema_migrations(conn)
        _runtime(conn)
        conn.execute("UPDATE safety_scheduler_runtime SET paused = ?, kill_switch = CASE WHEN ? = 0 THEN 0 ELSE kill_switch END, reason = ?, disabled_scopes_json = CASE WHEN ? = 0 THEN '[]' ELSE disabled_scopes_json END, backfill_required = ?, lease_owner = NULL, lease_expires_at = NULL, version = version + 1, updated_at = ? WHERE id = 'global'", (int(paused), int(paused), reason[:500], int(paused), int(not paused), timestamp))
        write_audit_log(conn, "safety_scheduler_paused" if paused else "safety_scheduler_resumed", actor_id, "safety_scheduler_runtime", "global", {"reason": reason, "human_evidence_recorded": bool(evidence_ref)})
        conn.commit()
    return scheduler_status()


def activate_unattended_kill_switch(conn, reason: str) -> None:
    _runtime(conn)
    conn.execute("UPDATE safety_scheduler_runtime SET kill_switch = 1, reason = ?, disabled_scopes_json = ?, version = version + 1, updated_at = ? WHERE id = 'global'", (reason[:500], json_dumps(DISABLED_SCOPES), now_iso()))


def assert_automation_allowed(conn, scope: str) -> None:
    apply_pending_schema_migrations(conn)
    runtime = _runtime(conn)
    disabled = set(json_loads(runtime.get("disabled_scopes_json"), []))
    if runtime["kill_switch"] and scope in disabled:
        raise SchedulerError("safety_scheduler_kill_switch", "人工安全队列暂不可用，自动反馈已暂停；记录仍会保留。", 503)
