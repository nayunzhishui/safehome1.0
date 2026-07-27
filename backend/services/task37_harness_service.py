"""Metadata-only execution harness for Task 37 production computations."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from database import get_connection, json_loads, new_id, now_iso, row_to_dict
from services.reliability_service import (
    ALLOWED_REASON_CODES,
    ReliabilityError,
    _record_job_action,
    create_job,
)


ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = ROOT / "content" / "task37_execution_harness.json"
SENSITIVE_KEYS = {
    "raw_text",
    "text",
    "content",
    "body",
    "prompt",
    "answer",
    "password",
    "secret",
    "token",
    "phone",
    "openid",
    "user_id",
}
ALLOWED_DISPATCH_KEYS = {
    "capability",
    "source_type",
    "source_id",
    "idempotency_key",
    "max_attempts",
}


def contract() -> dict:
    return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))


def _job_dict(row) -> dict:
    item = row_to_dict(row)
    item.pop("lease_owner", None)
    return item


def _job(conn, job_id: str):
    row = conn.execute("SELECT * FROM reliable_jobs WHERE id = ?", (job_id,)).fetchone()
    if row is None:
        raise ReliabilityError("not_found", "没有找到该计算任务。", 404)
    return row


def dispatch(actor: dict, payload: dict) -> tuple[dict, bool]:
    keys = {str(key) for key in payload}
    sensitive = sorted(keys & SENSITIVE_KEYS)
    if sensitive:
        raise ReliabilityError(
            "sensitive_payload_rejected",
            "计算队列只接受资源引用，不接受原文、身份、凭据或任意正文。",
            details={"forbidden_fields": sensitive},
        )
    unknown = sorted(keys - ALLOWED_DISPATCH_KEYS)
    if unknown:
        raise ReliabilityError(
            "validation_error",
            "计算任务包含未登记字段。",
            details={"unknown_fields": unknown},
        )
    registry = contract()
    capability = str(payload.get("capability") or "")
    capability_item = registry["capabilities"].get(capability)
    if not capability_item:
        raise ReliabilityError("validation_error", "计算能力未登记。")
    max_attempts = int(payload.get("max_attempts") or 3)
    if max_attempts < 1 or max_attempts > int(registry["resource_limits"]["max_attempts"]):
        raise ReliabilityError("resource_limit_exceeded", "最大尝试次数超过资源上限。")
    job_payload = {
        "job_type": capability_item["job_type"],
        "source_type": str(payload.get("source_type") or ""),
        "source_id": str(payload.get("source_id") or ""),
        "idempotency_key": str(payload.get("idempotency_key") or ""),
        "max_attempts": max_attempts,
    }
    return create_job(actor, job_payload)


def cancel(actor: dict, job_id: str) -> dict:
    timestamp = now_iso()
    with get_connection() as conn:
        row = _job(conn, job_id)
        item = row_to_dict(row)
        before = str(item["status"])
        if before not in {"pending", "retrying", "leased", "suspended"}:
            raise ReliabilityError("job_state_conflict", "该任务当前不能取消。", 409)
        conn.execute(
            """UPDATE reliable_jobs SET status = 'canceled', lease_owner = NULL,
               lease_expires_at = NULL, updated_at = ? WHERE id = ?""",
            (timestamp, job_id),
        )
        _record_job_action(conn, job_id, actor["id"], "cancel", before, "canceled")
        conn.commit()
        return _job_dict(_job(conn, job_id))


def freeze(actor: dict, job_id: str, payload: dict) -> dict:
    reason = str(payload.get("reason_code") or "")
    if reason not in ALLOWED_REASON_CODES:
        raise ReliabilityError("validation_error", "需要选择受控冻结原因。")
    timestamp = now_iso()
    with get_connection() as conn:
        row = _job(conn, job_id)
        item = row_to_dict(row)
        before = str(item["status"])
        if before not in {"pending", "retrying", "leased"}:
            raise ReliabilityError("job_state_conflict", "该任务当前不能冻结。", 409)
        conn.execute(
            """UPDATE reliable_jobs SET status = 'suspended', lease_owner = NULL,
               lease_expires_at = NULL, updated_at = ? WHERE id = ?""",
            (timestamp, job_id),
        )
        _record_job_action(
            conn,
            job_id,
            actor["id"],
            "freeze",
            before,
            "suspended",
            metadata={"reason_code": reason},
        )
        conn.commit()
        return _job_dict(_job(conn, job_id))


def resume(actor: dict, job_id: str, payload: dict) -> dict:
    reason = str(payload.get("reason_code") or "")
    if reason not in ALLOWED_REASON_CODES:
        raise ReliabilityError("validation_error", "需要选择受控恢复原因。")
    timestamp = now_iso()
    with get_connection() as conn:
        row = _job(conn, job_id)
        if str(row["status"]) != "suspended":
            raise ReliabilityError("job_state_conflict", "只有冻结任务可以恢复。", 409)
        conn.execute(
            """UPDATE reliable_jobs SET status = 'pending', available_at = ?,
               lease_owner = NULL, lease_expires_at = NULL, updated_at = ? WHERE id = ?""",
            (timestamp, timestamp, job_id),
        )
        _record_job_action(
            conn,
            job_id,
            actor["id"],
            "resume",
            "suspended",
            "pending",
            metadata={"reason_code": reason},
        )
        conn.commit()
        return _job_dict(_job(conn, job_id))


def heartbeat(payload: dict) -> dict:
    unknown = set(payload) - {"worker_id", "capacity", "active_jobs"}
    if unknown:
        raise ReliabilityError(
            "validation_error",
            "worker心跳只接受容量元数据。",
            details={"unknown_fields": sorted(unknown)},
        )
    worker_id = str(payload.get("worker_id") or "")
    capacity = int(payload.get("capacity") or 0)
    active_jobs = int(payload.get("active_jobs") or 0)
    limits = contract()["resource_limits"]
    if (
        len(worker_id) < 4
        or capacity < 1
        or capacity > int(limits["heartbeat_capacity_max"])
        or active_jobs < 0
        or active_jobs > min(capacity, int(limits["heartbeat_active_jobs_max"]))
    ):
        raise ReliabilityError("resource_limit_exceeded", "worker容量或活动任务数超出限制。")
    worker_ref = "worker_" + hashlib.sha256(worker_id.encode("utf-8")).hexdigest()[:16]
    timestamp = now_iso()
    with get_connection() as conn:
        conn.execute(
            """INSERT INTO observability_events
               (id, request_id, method, path, actor_scope, module, journey, outcome,
                error_code, status_code, latency_ms, retry_count, recovered, created_at)
               VALUES (?, ?, 'HEARTBEAT', '/internal/computation-worker', 'admin',
                       'computation_worker', 'computation_harness', 'success', ?, 200, 0, ?, 0, ?)""",
            (
                new_id("obs"),
                worker_ref,
                f"capacity_{capacity}",
                active_jobs,
                timestamp,
            ),
        )
        conn.commit()
    return {
        "worker_ref": worker_ref,
        "capacity": capacity,
        "active_jobs": active_jobs,
        "recorded_at": timestamp,
    }


def _duration_ms(start: str | None, end: str | None) -> float:
    if not start or not end:
        return 0.0
    try:
        return max(
            0.0,
            (datetime.fromisoformat(str(end)) - datetime.fromisoformat(str(start))).total_seconds() * 1000,
        )
    except (TypeError, ValueError):
        return 0.0


def metrics() -> dict:
    job_types = tuple(item["job_type"] for item in contract()["capabilities"].values())
    placeholders = ",".join("?" for _ in job_types)
    with get_connection() as conn:
        jobs = [
            row_to_dict(row)
            for row in conn.execute(
                f"SELECT * FROM reliable_jobs WHERE job_type IN ({placeholders})",
                job_types,
            ).fetchall()
        ]
        actions = [
            row_to_dict(row)
            for row in conn.execute(
                f"""SELECT a.* FROM reliable_job_actions a
                    JOIN reliable_jobs j ON j.id = a.job_id
                    WHERE j.job_type IN ({placeholders}) AND a.action IN ('claim', 'reclaim')""",
                job_types,
            ).fetchall()
        ]
        artifacts = [
            row_to_dict(row)
            for row in conn.execute(
                "SELECT metrics_json FROM research_analysis_artifacts WHERE deleted_at IS NULL"
            ).fetchall()
        ]
        backlog_row = conn.execute(
            """SELECT COUNT(*) AS count FROM research_work_items
               WHERE status IN ('open', 'claimed', 'processing', 'waiting', 'dead_letter')"""
        ).fetchone()
    total = len(jobs)
    failures = sum(item["status"] in {"retrying", "dead_letter"} for item in jobs)
    throughput = sum(item["status"] == "completed" for item in jobs)
    created = {item["id"]: item["created_at"] for item in jobs}
    queue_durations = [
        _duration_ms(created.get(item["job_id"]), item["created_at"])
        for item in actions
        if item["job_id"] in created
    ]
    coverage_values: list[float] = []
    abstention_values: list[float] = []
    for artifact in artifacts:
        value = json_loads(artifact.get("metrics_json"), {})
        if isinstance(value.get("coverage_rate"), (int, float)):
            coverage_values.append(float(value["coverage_rate"]))
        if isinstance(value.get("unknown_rate"), (int, float)):
            abstention_values.append(float(value["unknown_rate"]))
    return {
        "throughput": throughput,
        "queue_duration_ms": round(sum(queue_durations) / len(queue_durations), 2) if queue_durations else 0.0,
        "failure_rate": round(failures / total, 4) if total else 0.0,
        "coverage_rate": round(sum(coverage_values) / len(coverage_values), 4) if coverage_values else 0.0,
        "abstention_rate": round(sum(abstention_values) / len(abstention_values), 4) if abstention_values else 0.0,
        "cost_microunits": 0,
        "human_backlog": int(backlog_row["count"] if backlog_row else 0),
        "production_observation": False,
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
    }


def error_categories() -> dict:
    return {
        "items": list(contract()["error_categories"]),
        "mapping": {
            "validation_error": "user",
            "authorization_or_data_error": "data",
            "model_execution_error": "model",
            "provider_unavailable": "provider",
            "forbidden": "permission",
        },
    }
