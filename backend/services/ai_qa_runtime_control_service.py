"""Budgets, rate limits, durable circuit state and retention policy."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from flask import current_app

from database import get_connection, new_id


POLICY_SCHEMA = "safehome.ai-qa-runtime-policy.v1"
SCOPES = ("user", "role", "provider", "project")


class UsageControlError(ValueError):
    def __init__(self, code: str, message: str, scope: str):
        super().__init__(message)
        self.code = code
        self.scope = scope


def load_runtime_policy(content_dir: Path | None = None) -> dict:
    directory = Path(content_dir or current_app.config["CONTENT_DIR"])
    try:
        policy = json.loads(
            (directory / "ai_qa_runtime_policy.json").read_text(
                encoding="utf-8"
            )
        )
    except (OSError, json.JSONDecodeError) as exc:
        raise UsageControlError(
            "ai_qa_runtime_policy_unavailable",
            "AI运行控制策略不可用",
            "policy",
        ) from exc
    if policy.get("schema_version") != POLICY_SCHEMA:
        raise UsageControlError(
            "ai_qa_runtime_policy_invalid",
            "AI运行控制策略版本不兼容",
            "policy",
        )
    for key in ("budgets_micros_per_day", "rate_limits_per_hour"):
        if set(policy.get(key) or {}) != set(SCOPES):
            raise UsageControlError(
                "ai_qa_runtime_policy_invalid",
                "AI运行控制策略缺少用户、角色、供应商或项目范围",
                "policy",
            )
    return policy


def _scope_value(config: dict, key: str) -> int:
    value = config.get(key, config.get("default", 0))
    return max(0, int(value or 0))


def _usage_rows(actor: dict, session: dict, provider: str) -> dict:
    day_cutoff = datetime.now(timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0
    ).isoformat()
    hour_cutoff = (
        datetime.now(timezone.utc) - timedelta(hours=1)
    ).isoformat()
    user_id = str(actor["id"])
    role = str(actor.get("role") or "")
    project = str(session.get("use_case_id") or "unscoped")
    with get_connection() as conn:
        rows = {
            "user": conn.execute(
                """
                SELECT COUNT(*) AS requests,
                       COALESCE(SUM(cost_micros), 0) AS cost
                FROM ai_qa_provider_events
                WHERE user_id = ? AND created_at >= ?
                """,
                (user_id, day_cutoff),
            ).fetchone(),
            "role": conn.execute(
                """
                SELECT COUNT(*) AS requests,
                       COALESCE(SUM(e.cost_micros), 0) AS cost
                FROM ai_qa_provider_events e
                JOIN users u ON u.id = e.user_id
                WHERE u.role = ? AND e.created_at >= ?
                """,
                (role, day_cutoff),
            ).fetchone(),
            "provider": conn.execute(
                """
                SELECT COUNT(*) AS requests,
                       COALESCE(SUM(cost_micros), 0) AS cost
                FROM ai_qa_provider_events
                WHERE provider = ? AND created_at >= ?
                """,
                (provider, day_cutoff),
            ).fetchone(),
            "project": conn.execute(
                """
                SELECT COUNT(*) AS requests,
                       COALESCE(SUM(e.cost_micros), 0) AS cost
                FROM ai_qa_provider_events e
                JOIN ai_qa_sessions s ON s.id = e.session_id
                WHERE s.use_case_id = ? AND e.created_at >= ?
                """,
                (project, day_cutoff),
            ).fetchone(),
        }
        hourly = {
            "user": conn.execute(
                """
                SELECT COUNT(*) AS requests
                FROM ai_qa_messages
                WHERE user_id = ? AND role = 'user' AND created_at >= ?
                """,
                (user_id, hour_cutoff),
            ).fetchone(),
            "role": conn.execute(
                "SELECT COUNT(*) AS requests FROM ai_qa_provider_events e JOIN users u ON u.id = e.user_id WHERE u.role = ? AND e.created_at >= ?",
                (role, hour_cutoff),
            ).fetchone(),
            "provider": conn.execute(
                "SELECT COUNT(*) AS requests FROM ai_qa_provider_events WHERE provider = ? AND created_at >= ?",
                (provider, hour_cutoff),
            ).fetchone(),
            "project": conn.execute(
                "SELECT COUNT(*) AS requests FROM ai_qa_provider_events e JOIN ai_qa_sessions s ON s.id = e.session_id WHERE s.use_case_id = ? AND e.created_at >= ?",
                (project, hour_cutoff),
            ).fetchone(),
        }
    return {
        "keys": {
            "user": user_id,
            "role": role,
            "provider": provider,
            "project": project,
        },
        "daily": rows,
        "hourly": hourly,
    }


def enforce_usage_control(
    actor: dict,
    session: dict,
    provider: str,
    *,
    policy: dict | None = None,
) -> dict:
    policy = policy or load_runtime_policy()
    usage = _usage_rows(actor, session, provider)
    for scope in SCOPES:
        key = usage["keys"][scope]
        budget = _scope_value(
            policy["budgets_micros_per_day"][scope], key
        )
        if scope == "user":
            configured = int(
                current_app.config.get("AI_QA_DAILY_BUDGET_MICROS", 0)
            )
            if configured > 0:
                budget = configured
        if budget > 0 and int(usage["daily"][scope]["cost"] or 0) >= budget:
            raise UsageControlError(
                f"ai_qa_{scope}_budget_exhausted",
                "AI当日预算已用完",
                scope,
            )
        rate_limit = _scope_value(
            policy["rate_limits_per_hour"][scope], key
        )
        if scope == "user":
            configured = int(
                current_app.config.get("AI_QA_REQUESTS_PER_HOUR", 0)
            )
            if configured > 0:
                rate_limit = configured
        if (
            rate_limit > 0
            and int(usage["hourly"][scope]["requests"] or 0) >= rate_limit
        ):
            raise UsageControlError(
                f"ai_qa_{scope}_rate_limited",
                "AI请求过于频繁",
                scope,
            )
    return {
        "allowed": True,
        "scopes_checked": list(SCOPES),
        "policy_version": policy.get("policy_version"),
    }


def _now(value: datetime | None) -> datetime:
    return value or datetime.now(timezone.utc)


def _parse(value: str | None) -> datetime | None:
    if not value:
        return None
    parsed = datetime.fromisoformat(value)
    return (
        parsed.replace(tzinfo=timezone.utc)
        if parsed.tzinfo is None
        else parsed
    )


def claim_circuit_permission(
    provider: str,
    *,
    policy: dict | None = None,
    now: datetime | None = None,
) -> dict:
    policy = policy or load_runtime_policy()
    moment = _now(now)
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT * FROM ai_qa_circuit_states
            WHERE provider = ? AND scope_type = 'provider'
              AND scope_id = ?
            """,
            (provider, provider),
        ).fetchone()
        if not row or row["state"] == "closed":
            return {"allowed": True, "state": "closed", "probe": False}
        if row["state"] == "open":
            next_probe = _parse(row["next_probe_at"])
            if next_probe and moment < next_probe:
                return {"allowed": False, "state": "open", "probe": False}
        if int(row["probe_in_flight"] or 0):
            return {
                "allowed": False,
                "state": "half_open",
                "probe": False,
            }
        updated = conn.execute(
            """
            UPDATE ai_qa_circuit_states
            SET state = 'half_open', probe_in_flight = 1,
                version = version + 1, updated_at = ?
            WHERE id = ? AND version = ? AND probe_in_flight = 0
            """,
            (moment.isoformat(), row["id"], row["version"]),
        )
        conn.commit()
        if updated.rowcount != 1:
            return {
                "allowed": False,
                "state": "half_open",
                "probe": False,
            }
    return {"allowed": True, "state": "half_open", "probe": True}


def record_circuit_outcome(
    provider: str,
    *,
    success: bool,
    policy: dict | None = None,
    now: datetime | None = None,
) -> dict:
    policy = policy or load_runtime_policy()
    circuit = policy["circuit_breaker"]
    threshold = max(1, int(circuit.get("failure_threshold", 3)))
    cooldown = max(1, int(circuit.get("cooldown_seconds", 60)))
    moment = _now(now)
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT * FROM ai_qa_circuit_states
            WHERE provider = ? AND scope_type = 'provider'
              AND scope_id = ?
            """,
            (provider, provider),
        ).fetchone()
        if success:
            if row:
                conn.execute(
                    """
                    UPDATE ai_qa_circuit_states
                    SET state = 'closed', failure_count = 0,
                        opened_at = NULL, next_probe_at = NULL,
                        probe_in_flight = 0, version = version + 1,
                        updated_at = ?
                    WHERE id = ?
                    """,
                    (moment.isoformat(), row["id"]),
                )
            state = "closed"
            failure_count = 0
        else:
            failure_count = int(row["failure_count"] or 0) + 1 if row else 1
            should_open = (
                failure_count >= threshold
                or (row and row["state"] == "half_open")
            )
            state = "open" if should_open else "closed"
            opened_at = moment.isoformat() if should_open else None
            next_probe_at = (
                (moment + timedelta(seconds=cooldown)).isoformat()
                if should_open
                else None
            )
            if row:
                conn.execute(
                    """
                    UPDATE ai_qa_circuit_states
                    SET state = ?, failure_count = ?, opened_at = ?,
                        next_probe_at = ?, probe_in_flight = 0,
                        version = version + 1, updated_at = ?
                    WHERE id = ?
                    """,
                    (
                        state,
                        failure_count,
                        opened_at,
                        next_probe_at,
                        moment.isoformat(),
                        row["id"],
                    ),
                )
            else:
                conn.execute(
                    """
                    INSERT INTO ai_qa_circuit_states (
                        id, provider, scope_type, scope_id, state,
                        failure_count, opened_at, next_probe_at,
                        probe_in_flight, version, updated_at
                    ) VALUES (?, ?, 'provider', ?, ?, ?, ?, ?, 0, 1, ?)
                    """,
                    (
                        new_id("aiqcb"),
                        provider,
                        provider,
                        state,
                        failure_count,
                        opened_at,
                        next_probe_at,
                        moment.isoformat(),
                    ),
                )
        conn.commit()
    return {"state": state, "failure_count": failure_count}


def runtime_policy_summary() -> dict:
    policy = load_runtime_policy()
    return {
        "policy_version": policy.get("policy_version"),
        "scopes": list(SCOPES),
        "circuit_breaker": policy["circuit_breaker"],
        "degradation": policy["degradation"],
        "retention": policy["retention"],
        "core_services_unaffected": policy["core_services_unaffected"],
        "kill_switch_reactivation_via_api": False,
        "production_release_approved": False,
    }
