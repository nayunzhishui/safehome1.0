"""RC0810-F21 protected health, incident and isolated drill contracts."""

from __future__ import annotations

import hmac
import ipaddress
import json
from pathlib import Path
from typing import Any

from flask import current_app, request

from database import get_connection
from services.redis_service import health as redis_health


ROOT = Path(__file__).resolve().parents[2]
POLICY_PATH = ROOT / "config" / "rc0810" / "operations_reliability_policy.json"
INTERNAL_NETWORKS = tuple(
    ipaddress.ip_network(value)
    for value in ("127.0.0.0/8", "10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16", "::1/128", "fc00::/7", "fe80::/10")
)


class OperationsReliabilityError(ValueError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


def load_operations_policy() -> dict:
    return json.loads(POLICY_PATH.read_text(encoding="utf-8"))


def _internal_source(remote_addr: str | None) -> bool:
    try:
        address = ipaddress.ip_address(str(remote_addr or ""))
    except ValueError:
        return False
    return any(address in network for network in INTERNAL_NETWORKS)


def protected_health_allowed() -> bool:
    """Trust only the socket peer or an explicit operations token."""

    if _internal_source(request.remote_addr):
        return True
    configured = str(current_app.config.get("OPERATIONS_HEALTH_TOKEN") or "")
    supplied = str(request.headers.get("X-Operations-Token") or "")
    return bool(configured and supplied and hmac.compare_digest(configured, supplied))


def protected_runtime_components() -> dict:
    redis = redis_health()
    try:
        with get_connection() as conn:
            scheduler_row = conn.execute(
                "SELECT * FROM safety_scheduler_runtime WHERE id = 'global'"
            ).fetchone()
            latest_run = conn.execute(
                "SELECT status FROM safety_scheduler_runs ORDER BY updated_at DESC LIMIT 1"
            ).fetchone()
        if scheduler_row is None:
            raise LookupError("scheduler_runtime_missing")
        scheduler_enabled = bool(current_app.config.get("SAFETY_SCHEDULER_ENABLED", False))
        scheduler_public = {
            "enabled": scheduler_enabled,
            "ok": not scheduler_enabled or not scheduler_row["paused"] and not scheduler_row["kill_switch"],
            "paused": bool(scheduler_row["paused"]),
            "kill_switch": bool(scheduler_row["kill_switch"]),
            "backlog_count": int(scheduler_row["backlog_count"] or 0),
            "oldest_due_age_seconds": int(scheduler_row["oldest_due_age_seconds"] or 0),
            "last_run_status": latest_run["status"] if latest_run else None,
        }
    except Exception:
        scheduler_public = {"enabled": bool(current_app.config.get("SAFETY_SCHEDULER_ENABLED", False)), "ok": False}
    try:
        with get_connection() as conn:
            pending = int(
                conn.execute(
                    "SELECT COUNT(*) AS count FROM reliable_jobs WHERE status IN ('pending','leased','retrying')"
                ).fetchone()["count"]
            )
            dead = int(
                conn.execute(
                    "SELECT COUNT(*) AS count FROM reliable_jobs WHERE status = 'dead_letter'"
                ).fetchone()["count"]
            )
            notification_backlog = int(
                conn.execute(
                    "SELECT COUNT(*) AS count FROM notification_deliveries WHERE status IN ('pending','retrying')"
                ).fetchone()["count"]
            )
        queues = {
            "ok": pending < 100 and dead == 0,
            "pending_jobs": pending,
            "dead_letter_jobs": dead,
            "notification_backlog": notification_backlog,
        }
    except Exception:
        queues = {"ok": False, "pending_jobs": None, "dead_letter_jobs": None, "notification_backlog": None}
    redis_public = {
        "enabled": bool(redis.get("enabled")),
        "ok": bool(redis.get("ok")),
        "status": redis.get("status"),
        "latency_ms": redis.get("latency_ms"),
    }
    return {"redis": redis_public, "queues": queues, "scheduler": scheduler_public}


def sanitize_incident_record(payload: dict[str, Any]) -> dict:
    policy = load_operations_policy()["incident_record"]
    prohibited = set(policy["prohibited_fields"])
    forbidden = sorted(prohibited.intersection(payload))
    if forbidden:
        raise OperationsReliabilityError(
            "incident_sensitive_field_forbidden",
            "事件记录不得包含参与者正文、回答或凭据。",
        )
    allowed = set(policy["required_fields"])
    unknown = sorted(set(payload) - allowed)
    if unknown:
        raise OperationsReliabilityError("incident_unknown_field", "事件记录包含未登记字段。")
    required = allowed - {"recovered_at"}
    if any(payload.get(field) in (None, "", []) for field in required):
        raise OperationsReliabilityError("incident_required_field_missing", "事件时间线或处置字段不完整。")
    if not all(isinstance(payload.get(field), list) for field in ("evidence_refs", "decisions", "followup_actions")):
        raise OperationsReliabilityError("incident_list_field_invalid", "事件证据、决策和后续动作必须为数组。")
    return {field: payload.get(field) for field in policy["required_fields"]}


def _alert_state(alert_id: str, metrics: dict[str, Any]) -> bool:
    checks = {
        "http_5xx_spike": lambda: float(metrics.get("http_5xx_rate", 0)) > 0.02,
        "database_unavailable": lambda: metrics.get("database_ok") is False,
        "redis_unavailable": lambda: metrics.get("redis_enabled") is True and metrics.get("redis_ok") is False,
        "queue_backlog": lambda: int(metrics.get("pending_jobs", 0)) >= 100 or int(metrics.get("dead_letter_jobs", 0)) > 0,
        "content_version_mismatch": lambda: metrics.get("content_version_match") is False,
    }
    return bool(checks[alert_id]())


def _recovery_state(alert_id: str, metrics: dict[str, Any]) -> bool:
    checks = {
        "http_5xx_spike": lambda: float(metrics.get("http_5xx_rate", 1)) <= 0.005,
        "database_unavailable": lambda: metrics.get("database_ok") is True and metrics.get("integrity_check") is True,
        "redis_unavailable": lambda: metrics.get("redis_ok") is True,
        "queue_backlog": lambda: int(metrics.get("pending_jobs", 100)) < 50 and int(metrics.get("dead_letter_jobs", 1)) == 0,
        "content_version_mismatch": lambda: metrics.get("content_version_match") is True and metrics.get("artifact_hash_verified") is True,
    }
    return bool(checks[alert_id]())


def run_isolated_drills(policy: dict | None = None) -> dict:
    policy = policy or load_operations_policy()
    results = []
    for drill in policy["isolated_drills"]:
        results.append(
            {
                "scenario": drill["scenario"],
                "alert": drill["alert"],
                "alert_detected": _alert_state(drill["alert"], drill["injected"]),
                "recovery_verified": _recovery_state(drill["alert"], drill["recovered"]),
                "evidence_mode": "isolated_policy_injection",
            }
        )
    return {
        "ok": all(item["alert_detected"] and item["recovery_verified"] for item in results),
        "results": results,
        "contains_real_participant_data": False,
        "production_mutation_executed": False,
        "production_gate_eligible": False,
    }
