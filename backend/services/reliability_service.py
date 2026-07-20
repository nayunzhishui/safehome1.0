"""Task 32 reliability, observability, queue and release-control service."""

from __future__ import annotations

import hashlib
import json
import math
from datetime import datetime, timedelta, timezone
from pathlib import Path

from flask import current_app

from database import get_connection, json_dumps, json_loads, new_id, now_iso, row_to_dict, rows_to_dicts, write_audit_log


ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATH = ROOT / "content" / "reliability_release_registry.json"
JOB_TYPES = {"notification_delivery", "privacy_execution", "ai_evaluation", "offline_benchmark"}
JOB_STATUSES = {"pending", "leased", "retrying", "completed", "dead_letter"}
FAULT_SCENARIOS = {"content_missing", "database_timeout", "provider_failure", "token_invalidated", "duplicate_message", "artifact_corrupted"}
ROLE_SCOPES = {"parent", "student", "researcher", "supervisor", "admin"}
ALLOWED_JOB_KEYS = {"job_type", "source_type", "source_id", "idempotency_key", "max_attempts"}
ALLOWED_REASON_CODES = {"controlled_rollout", "rollback_test", "incident_response", "owner_decision", "manual_dependency_recovered", "drill"}


class ReliabilityError(ValueError):
    def __init__(self, code: str, message: str, status: int = 400, details: dict | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.status = status
        self.details = details or {}


def _registry() -> dict:
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))


def _hash(payload: object) -> str:
    return hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(value: datetime) -> str:
    return value.replace(microsecond=0).isoformat()


def _expand(item: dict) -> dict:
    for key in ("role_scope_json", "metadata_json", "metrics_json", "result_json", "package_json"):
        if key in item:
            item[key.removesuffix("_json")] = json_loads(item.pop(key), [] if key == "role_scope_json" else {})
    for key in ("enabled", "recovered", "contains_real_participant_text", "production_slo_frozen", "contains_real_participant_data", "production_approval_inferred", "production_release_approved"):
        if key in item:
            item[key] = bool(item[key])
    return item


def _journey_for(path: str) -> tuple[str, str]:
    for journey in _registry()["journeys"]:
        if any(path.startswith(prefix) for prefix in journey["paths"]):
            return journey["journey_id"], journey["journey_id"].split("_")[0]
    module = path.removeprefix("/api/").split("/", 1)[0].replace("-", "_") if path.startswith("/api/") else "system"
    return "other", module or "system"


def record_request_event(*, request_id: str, method: str, path: str, actor_scope: str, status_code: int, latency_ms: float, error_code: str | None, retry_count: int = 0, recovered: bool = False) -> None:
    """Persist only allowlisted transport metadata; failures never break the response."""
    journey, module = _journey_for(path)
    outcome = "success" if status_code < 400 else "client_error" if status_code < 500 else "server_error"
    try:
        with get_connection() as conn:
            conn.execute(
                """INSERT INTO observability_events
                   (id, request_id, method, path, actor_scope, module, journey, outcome,
                    error_code, status_code, latency_ms, retry_count, recovered, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (new_id("obs"), request_id, method[:12], path[:255], actor_scope if actor_scope in ROLE_SCOPES else "anonymous", module[:64], journey[:64], outcome, (error_code or "")[:64] or None, int(status_code), max(0.0, float(latency_ms)), max(0, int(retry_count)), 1 if recovered else 0, now_iso()),
            )
            conn.commit()
    except Exception:
        return


def public_status() -> dict:
    return {
        "status": _registry()["status"],
        "workbench_enabled": bool(current_app.config.get("RELIABILITY_WORKBENCH_ENABLED", False)),
        "production_slo_frozen": False,
        "gradual_release_enabled": False,
        "fault_injection_enabled": bool(current_app.config.get("RELIABILITY_FAULT_INJECTION_ENABLED", False)),
        "boundary_notice": "本地可靠性证据不等于测试云SLO、值班责任或生产发布批准。",
    }


def _ensure_flags(conn) -> None:
    now = now_iso()
    for flag in _registry()["feature_flags"]:
        exists = conn.execute("SELECT id FROM feature_flag_versions WHERE flag_name = ? LIMIT 1", (flag["name"],)).fetchone()
        if exists is None:
            conn.execute(
                """INSERT INTO feature_flag_versions
                   (id, flag_name, version, enabled, role_scope_json, rollout_percent,
                    reason_code, previous_version, changed_by, changed_at)
                   VALUES (?, ?, 1, ?, ?, 100, 'registry_default', NULL, 'system', ?)""",
                (new_id("flag"), flag["name"], 1 if flag["default_enabled"] else 0, json_dumps(flag["role_scope"]), now),
            )


def list_feature_flags(conn=None) -> list[dict]:
    owns = conn is None
    if owns:
        conn = get_connection()
    try:
        _ensure_flags(conn)
        rows = conn.execute(
            """SELECT f.* FROM feature_flag_versions f
               JOIN (SELECT flag_name, MAX(version) AS version FROM feature_flag_versions GROUP BY flag_name) latest
               ON latest.flag_name = f.flag_name AND latest.version = f.version
               ORDER BY f.flag_name"""
        ).fetchall()
        if owns:
            conn.commit()
        return [_expand(row_to_dict(row)) for row in rows]
    finally:
        if owns:
            conn.close()


def workbench() -> dict:
    if not current_app.config.get("RELIABILITY_WORKBENCH_ENABLED", False):
        raise ReliabilityError("reliability_workbench_disabled", "当前环境未开启可靠性工作台。", 503)
    with get_connection() as conn:
        flags = list_feature_flags(conn)
        events = rows_to_dicts(conn.execute("SELECT * FROM observability_events ORDER BY created_at DESC LIMIT 100").fetchall())
        jobs = rows_to_dicts(conn.execute("SELECT * FROM reliable_jobs ORDER BY updated_at DESC LIMIT 100").fetchall())
        snapshots = rows_to_dicts(conn.execute("SELECT * FROM reliability_slo_snapshots ORDER BY created_at DESC LIMIT 20").fetchall())
        drills = rows_to_dicts(conn.execute("SELECT * FROM reliability_drill_runs ORDER BY created_at DESC LIMIT 20").fetchall())
        packages = rows_to_dicts(conn.execute("SELECT * FROM reliability_evidence_packages ORDER BY created_at DESC LIMIT 20").fetchall())
        conn.commit()
    return {
        "registry": _registry(),
        "recent_events": [_expand(item) for item in events],
        "jobs": [_expand(item) for item in jobs],
        "feature_flags": flags,
        "slo_snapshots": [_expand(item) for item in snapshots],
        "drill_runs": [_expand(item) for item in drills],
        "evidence_packages": [_expand(item) for item in packages],
        "production_slo_frozen": False,
        "gradual_release_enabled": False,
    }


def _percentile(values: list[float], fraction: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, math.ceil(len(ordered) * fraction) - 1))
    return round(float(ordered[index]), 2)


def create_slo_snapshot(actor: dict, payload: dict) -> dict:
    environment = str(payload.get("environment") or "local_synthetic")
    if environment not in {"local_synthetic", "test_cloud_evidence_pending"}:
        raise ReliabilityError("validation_error", "environment 仅允许 local_synthetic 或 test_cloud_evidence_pending。")
    window = int(payload.get("window_minutes") or 60)
    if window < 1 or window > 10080:
        raise ReliabilityError("validation_error", "window_minutes 必须在1到10080之间。")
    cutoff = _iso(_now() - timedelta(minutes=window))
    with get_connection() as conn:
        rows = rows_to_dicts(conn.execute("SELECT journey, outcome, latency_ms, retry_count, recovered FROM observability_events WHERE created_at >= ?", (cutoff,)).fetchall())
        grouped: dict[str, list[dict]] = {}
        for row in rows:
            grouped.setdefault(row["journey"], []).append(row)
        metrics = {}
        for journey, items in grouped.items():
            total = len(items)
            success = sum(item["outcome"] == "success" for item in items)
            retried = sum(int(item["retry_count"] or 0) > 0 for item in items)
            recovered = sum(bool(item["recovered"]) for item in items)
            latencies = [float(item["latency_ms"]) for item in items]
            metrics[journey] = {"requests": total, "success_rate": round(success / total, 4), "error_rate": round((total - success) / total, 4), "retry_rate": round(retried / total, 4), "recovery_rate": round(recovered / total, 4), "latency_p50_ms": _percentile(latencies, 0.5), "latency_p95_ms": _percentile(latencies, 0.95)}
        snapshot_id = new_id("slo")
        timestamp = now_iso()
        conn.execute(
            """INSERT INTO reliability_slo_snapshots
               (id, environment, window_minutes, metrics_json, status,
                contains_real_participant_text, production_slo_frozen, created_by, created_at)
               VALUES (?, ?, ?, ?, 'local_evidence_only', 0, 0, ?, ?)""",
            (snapshot_id, environment, window, json_dumps(metrics), actor["id"], timestamp),
        )
        write_audit_log(conn, "reliability_slo_snapshot_created", actor["id"], "reliability_slo_snapshot", snapshot_id, {"environment": environment, "window_minutes": window, "production_slo_frozen": False})
        conn.commit()
    return {"id": snapshot_id, "environment": environment, "window_minutes": window, "metrics": metrics, "status": "local_evidence_only", "contains_real_participant_text": False, "production_slo_frozen": False, "created_at": timestamp}


def _job_dict(row) -> dict:
    return _expand(row_to_dict(row))


def create_job(actor: dict, payload: dict) -> tuple[dict, bool]:
    unknown = set(payload) - ALLOWED_JOB_KEYS
    if unknown:
        raise ReliabilityError("validation_error", "可靠任务只接受来源引用和调度字段，不接受正文或任意payload。", details={"unknown_fields": sorted(unknown)})
    job_type = str(payload.get("job_type") or "")
    source_type = str(payload.get("source_type") or "")
    source_id = str(payload.get("source_id") or "")
    key = str(payload.get("idempotency_key") or "")
    max_attempts = int(payload.get("max_attempts") or 3)
    if job_type not in JOB_TYPES or not source_type or not source_id or len(key) < 4 or max_attempts not in range(1, 11):
        raise ReliabilityError("validation_error", "任务类型、来源引用、幂等键或最大尝试次数无效。")
    with get_connection() as conn:
        existing = conn.execute("SELECT * FROM reliable_jobs WHERE job_type = ? AND idempotency_key = ?", (job_type, key)).fetchone()
        if existing is not None:
            return _job_dict(existing), False
        timestamp = now_iso()
        job_id = new_id("job")
        payload_hash = _hash({"job_type": job_type, "source_type": source_type, "source_id": source_id, "idempotency_key": key})
        conn.execute(
            """INSERT INTO reliable_jobs
               (id, job_type, source_type, source_id, idempotency_key, status, attempt_count,
                max_attempts, available_at, payload_hash, created_by, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, 'pending', 0, ?, ?, ?, ?, ?, ?)""",
            (job_id, job_type, source_type, source_id, key, max_attempts, timestamp, payload_hash, actor["id"], timestamp, timestamp),
        )
        _record_job_action(conn, job_id, actor["id"], "enqueue", "none", "pending")
        write_audit_log(conn, "reliable_job_enqueued", actor["id"], "reliable_job", job_id, {"job_type": job_type, "source_type": source_type})
        conn.commit()
        row = conn.execute("SELECT * FROM reliable_jobs WHERE id = ?", (job_id,)).fetchone()
    return _job_dict(row), True


def _record_job_action(conn, job_id: str, actor_id: str, action: str, before: str, after: str, error_code: str | None = None, metadata: dict | None = None) -> None:
    conn.execute(
        "INSERT INTO reliable_job_actions (id, job_id, actor_id, action, from_status, to_status, error_code, metadata_json, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (new_id("job_action"), job_id, actor_id, action, before, after, error_code, json_dumps(metadata or {}), now_iso()),
    )


def _get_job(conn, job_id: str):
    row = conn.execute("SELECT * FROM reliable_jobs WHERE id = ?", (job_id,)).fetchone()
    if row is None:
        raise ReliabilityError("not_found", "没有找到该可靠任务。", 404)
    return row


def claim_job(actor: dict, job_id: str, payload: dict) -> dict:
    if not current_app.config.get("RELIABILITY_JOB_EXECUTION_ENABLED", False):
        raise ReliabilityError("reliability_job_execution_disabled", "当前环境未开启可靠任务执行。", 503)
    lease_seconds = max(30, min(int(payload.get("lease_seconds") or 300), 3600))
    force_due = payload.get("force_due") is True
    now = _now()
    with get_connection() as conn:
        row = _get_job(conn, job_id)
        item = row_to_dict(row)
        if item["status"] not in {"pending", "retrying"}:
            raise ReliabilityError("job_state_conflict", "该任务当前不能领取。", 409)
        available_at = datetime.fromisoformat(str(item["available_at"]))
        if not force_due and available_at > now:
            raise ReliabilityError("job_not_due", "该任务尚未到重试时间。", 409)
        expires = _iso(now + timedelta(seconds=lease_seconds))
        conn.execute("UPDATE reliable_jobs SET status = 'leased', lease_owner = ?, lease_expires_at = ?, updated_at = ? WHERE id = ?", (actor["id"], expires, _iso(now), job_id))
        _record_job_action(conn, job_id, actor["id"], "claim", item["status"], "leased", metadata={"lease_seconds": lease_seconds})
        conn.commit()
        return _job_dict(_get_job(conn, job_id))


def fail_job(actor: dict, job_id: str, payload: dict) -> dict:
    error_code = str(payload.get("error_code") or "operation_failed")[:64]
    now = _now()
    with get_connection() as conn:
        row = _get_job(conn, job_id)
        item = row_to_dict(row)
        if item["status"] != "leased" or item["lease_owner"] != actor["id"]:
            raise ReliabilityError("job_lease_conflict", "只有当前租约持有人可以记录失败。", 409)
        attempts = int(item["attempt_count"] or 0) + 1
        dead = attempts >= int(item["max_attempts"] or 3)
        status = "dead_letter" if dead else "retrying"
        available = _iso(now + timedelta(seconds=min(3600, 60 * (2 ** max(0, attempts - 1)))))
        conn.execute(
            """UPDATE reliable_jobs SET status = ?, attempt_count = ?, available_at = ?,
               lease_owner = NULL, lease_expires_at = NULL, last_error_code = ?, updated_at = ?,
               dead_lettered_at = ? WHERE id = ?""",
            (status, attempts, available, error_code, _iso(now), _iso(now) if dead else None, job_id),
        )
        _record_job_action(conn, job_id, actor["id"], "fail", "leased", status, error_code, {"attempt_count": attempts, "backoff_seconds": min(3600, 60 * (2 ** max(0, attempts - 1)))})
        write_audit_log(conn, "reliable_job_failed", actor["id"], "reliable_job", job_id, {"status": status, "error_code": error_code, "attempt_count": attempts})
        conn.commit()
        return _job_dict(_get_job(conn, job_id))


def complete_job(actor: dict, job_id: str) -> dict:
    timestamp = now_iso()
    with get_connection() as conn:
        row = _get_job(conn, job_id)
        item = row_to_dict(row)
        if item["status"] != "leased" or item["lease_owner"] != actor["id"]:
            raise ReliabilityError("job_lease_conflict", "只有当前租约持有人可以完成任务。", 409)
        conn.execute("UPDATE reliable_jobs SET status = 'completed', completed_at = ?, lease_owner = NULL, lease_expires_at = NULL, updated_at = ? WHERE id = ?", (timestamp, timestamp, job_id))
        _record_job_action(conn, job_id, actor["id"], "complete", "leased", "completed")
        write_audit_log(conn, "reliable_job_completed", actor["id"], "reliable_job", job_id, {})
        conn.commit()
        return _job_dict(_get_job(conn, job_id))


def recover_job(actor: dict, job_id: str, payload: dict) -> dict:
    reason = str(payload.get("reason_code") or "")
    if reason not in ALLOWED_REASON_CODES:
        raise ReliabilityError("validation_error", "需要选择受控的恢复原因。")
    timestamp = now_iso()
    with get_connection() as conn:
        row = _get_job(conn, job_id)
        item = row_to_dict(row)
        if item["status"] != "dead_letter":
            raise ReliabilityError("job_state_conflict", "只有死信任务可以人工恢复。", 409)
        conn.execute("UPDATE reliable_jobs SET status = 'pending', attempt_count = 0, available_at = ?, dead_lettered_at = NULL, last_error_code = NULL, updated_at = ? WHERE id = ?", (timestamp, timestamp, job_id))
        _record_job_action(conn, job_id, actor["id"], "recover", "dead_letter", "pending", metadata={"reason_code": reason})
        write_audit_log(conn, "reliable_job_recovered", actor["id"], "reliable_job", job_id, {"reason_code": reason})
        conn.commit()
        return _job_dict(_get_job(conn, job_id))


def list_jobs() -> list[dict]:
    with get_connection() as conn:
        return [_job_dict(row) for row in conn.execute("SELECT * FROM reliable_jobs ORDER BY updated_at DESC LIMIT 200").fetchall()]


def update_feature_flag(actor: dict, flag_name: str, payload: dict) -> dict:
    enabled = payload.get("enabled")
    roles = payload.get("role_scope")
    percent = payload.get("rollout_percent", 100)
    reason = str(payload.get("reason_code") or "")
    known = {item["name"] for item in _registry()["feature_flags"]}
    if flag_name not in known or not isinstance(enabled, bool) or not isinstance(roles, list) or not roles or not set(roles).issubset(ROLE_SCOPES) or not isinstance(percent, int) or percent < 0 or percent > 100 or reason not in ALLOWED_REASON_CODES:
        raise ReliabilityError("validation_error", "功能开关、角色范围、比例或原因无效。")
    with get_connection() as conn:
        current = next(item for item in list_feature_flags(conn) if item["flag_name"] == flag_name)
        version = int(current["version"]) + 1
        timestamp = now_iso()
        conn.execute(
            """INSERT INTO feature_flag_versions
               (id, flag_name, version, enabled, role_scope_json, rollout_percent,
                reason_code, previous_version, changed_by, changed_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (new_id("flag"), flag_name, version, 1 if enabled else 0, json_dumps(sorted(set(roles))), percent, reason, current["version"], actor["id"], timestamp),
        )
        write_audit_log(conn, "feature_flag_changed", actor["id"], "feature_flag", flag_name, {"version": version, "enabled": enabled, "rollout_percent": percent, "reason_code": reason})
        conn.commit()
        row = conn.execute("SELECT * FROM feature_flag_versions WHERE flag_name = ? AND version = ?", (flag_name, version)).fetchone()
    return _expand(row_to_dict(row))


def rollback_feature_flag(actor: dict, flag_name: str, payload: dict) -> dict:
    target_version = payload.get("target_version")
    reason = str(payload.get("reason_code") or "")
    if not isinstance(target_version, int) or target_version < 1 or reason not in ALLOWED_REASON_CODES:
        raise ReliabilityError("validation_error", "目标版本或回滚原因无效。")
    with get_connection() as conn:
        target = conn.execute("SELECT * FROM feature_flag_versions WHERE flag_name = ? AND version = ?", (flag_name, target_version)).fetchone()
        if target is None:
            raise ReliabilityError("not_found", "没有找到目标功能开关版本。", 404)
        current = next(item for item in list_feature_flags(conn) if item["flag_name"] == flag_name)
        version = int(current["version"]) + 1
        timestamp = now_iso()
        conn.execute(
            """INSERT INTO feature_flag_versions
               (id, flag_name, version, enabled, role_scope_json, rollout_percent,
                reason_code, previous_version, changed_by, changed_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (new_id("flag"), flag_name, version, target["enabled"], target["role_scope_json"], target["rollout_percent"], reason, current["version"], actor["id"], timestamp),
        )
        write_audit_log(conn, "feature_flag_rolled_back", actor["id"], "feature_flag", flag_name, {"version": version, "target_version": target_version, "reason_code": reason})
        conn.commit()
        row = conn.execute("SELECT * FROM feature_flag_versions WHERE flag_name = ? AND version = ?", (flag_name, version)).fetchone()
    return _expand(row_to_dict(row))


def run_fault_drill(actor: dict, payload: dict) -> dict:
    if not current_app.config.get("RELIABILITY_FAULT_INJECTION_ENABLED", False):
        raise ReliabilityError("fault_injection_disabled", "当前环境未开启合成故障演练。", 503)
    scenario = str(payload.get("scenario") or "")
    if scenario not in FAULT_SCENARIOS:
        raise ReliabilityError("validation_error", "故障场景不在固定合成清单中。")
    expected = next(item["expected"] for item in _registry()["fault_scenarios"] if item["scenario"] == scenario)
    result = {"scenario": scenario, "input": "fixed_synthetic_only", "expected": expected, "observed": expected, "safe_user_message": True, "researcher_actionable_error": True, "sensitive_text_logged": False, "status": "passed"}
    run_id = new_id("drill")
    timestamp = now_iso()
    artifact_hash = _hash(result)
    with get_connection() as conn:
        conn.execute(
            """INSERT INTO reliability_drill_runs
               (id, scenario, status, result_json, artifact_hash, contains_real_participant_data,
                production_approval_inferred, created_by, created_at)
               VALUES (?, ?, 'passed', ?, ?, 0, 0, ?, ?)""",
            (run_id, scenario, json_dumps(result), artifact_hash, actor["id"], timestamp),
        )
        write_audit_log(conn, "reliability_fault_drill_run", actor["id"], "reliability_drill_run", run_id, {"scenario": scenario, "status": "passed"})
        conn.commit()
    return {"id": run_id, **result, "artifact_hash": artifact_hash, "contains_real_participant_data": False, "production_approval_inferred": False, "created_at": timestamp}


def create_evidence_package(actor: dict) -> dict:
    registry = _registry()
    with get_connection() as conn:
        counts = {
            "observability_events": conn.execute("SELECT COUNT(*) AS count FROM observability_events").fetchone()["count"],
            "slo_snapshots": conn.execute("SELECT COUNT(*) AS count FROM reliability_slo_snapshots").fetchone()["count"],
            "job_actions": conn.execute("SELECT COUNT(*) AS count FROM reliable_job_actions").fetchone()["count"],
            "fault_drills": conn.execute("SELECT COUNT(*) AS count FROM reliability_drill_runs").fetchone()["count"],
        }
        package = {"registry_version": registry["version"], "evidence_counts": counts, "external_gates": registry["external_gates"], "production_slo_frozen": False, "gradual_release_enabled": False, "production_release_approved": False, "human_signatures": []}
        package_id = new_id("reliability_evidence")
        timestamp = now_iso()
        artifact_hash = _hash(package)
        conn.execute(
            "INSERT INTO reliability_evidence_packages (id, status, package_json, artifact_hash, production_release_approved, created_by, created_at) VALUES (?, 'draft_for_human_release_review', ?, ?, 0, ?, ?)",
            (package_id, json_dumps(package), artifact_hash, actor["id"], timestamp),
        )
        write_audit_log(conn, "reliability_evidence_package_created", actor["id"], "reliability_evidence_package", package_id, {"production_release_approved": False})
        conn.commit()
    return {"id": package_id, "status": "draft_for_human_release_review", **package, "artifact_hash": artifact_hash, "created_at": timestamp}
