"""SafeHome Agent v1: deterministic, read-only and synthetic-data-only.

The runtime deliberately does not expose arbitrary SQL, shell, browser or write
capabilities.  It orchestrates a small allowlisted tool set and stores only
hash/operational metadata in MySQL/SQLite for auditability.
"""

from __future__ import annotations

import hashlib
import json
import os
import time
from pathlib import Path
from typing import Any

from config import Config
from database import get_connection, json_dumps, new_id, now_iso, write_audit_log
from services.rag_v2_service import retrieve_published_content_v2
from services.redis_service import health as redis_health, settings as redis_settings
from services.schema_migration_service import migration_manifest
from services.mysql_pool_runtime import status as mysql_pool_status
from services.embedding_service import public_status as embedding_status


POLICY_SCHEMA = "safehome.agent-runtime.v1"
DEFAULT_POLICY_PATH = Path(__file__).resolve().parents[2] / "content" / "agent_runtime_policy.json"


class AgentRuntimeError(ValueError):
    def __init__(self, code: str, message: str, status: int = 400, details: dict | None = None):
        super().__init__(message)
        self.code = code
        self.status = status
        self.details = details or {}


def _canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)


def _hash(value: Any) -> str:
    text = value if isinstance(value, str) else _canonical(value)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _policy_path() -> Path:
    configured = Path(getattr(Config, "CONTENT_DIR", DEFAULT_POLICY_PATH.parent)) / "agent_runtime_policy.json"
    return configured if configured.exists() else DEFAULT_POLICY_PATH


def load_policy() -> dict:
    try:
        payload = json.loads(_policy_path().read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise AgentRuntimeError("agent_policy_unavailable", "Agent运行策略不可用", 503) from exc
    if payload.get("schema") != POLICY_SCHEMA:
        raise AgentRuntimeError("agent_policy_invalid", "Agent运行策略版本不兼容", 503)
    if payload.get("write_tools_allowed") is not False:
        raise AgentRuntimeError("agent_policy_invalid", "Agent v1必须保持只读工具", 503)
    allowed = payload.get("allowed_tools") or []
    names = [str(item.get("name") or "") for item in allowed if isinstance(item, dict)]
    if not names or not all(names) or len(names) != len(set(names)):
        raise AgentRuntimeError("agent_policy_invalid", "Agent工具白名单无效", 503)
    return payload


def public_policy() -> dict:
    policy = load_policy()
    return {
        "schema": policy["schema"],
        "version": policy["version"],
        "status": policy["status"],
        "enabled_roles": list(policy["enabled_roles"]),
        "synthetic_data_required": bool(policy["synthetic_data_required"]),
        "participant_data_allowed": bool(policy["participant_data_allowed"]),
        "planner": policy["planner"],
        "max_tool_calls": int(policy["max_tool_calls"]),
        "allowed_tools": list(policy["allowed_tools"]),
        "write_tools_allowed": bool(policy["write_tools_allowed"]),
        "prohibited_actions": list(policy.get("prohibited_actions") or []),
        "boundary_notice": str(policy.get("boundary_notice") or ""),
    }


def _assert_actor(actor: dict, synthetic_data: bool) -> dict:
    policy = load_policy()
    role = str(actor.get("role") or "").strip()
    actor_id = str(actor.get("id") or "").strip()
    if not actor_id or role not in set(policy["enabled_roles"]):
        raise AgentRuntimeError("agent_forbidden", "当前身份不能运行Agent v1", 403)
    if policy.get("synthetic_data_required") and synthetic_data is not True:
        raise AgentRuntimeError("agent_synthetic_data_required", "Agent v1只允许明确标记的合成数据任务", 409)
    return policy


def _safe_runtime_config() -> dict:
    return {
        "app_env": str(Config.APP_ENV),
        "db_provider": str(Config.DB_PROVIDER),
        "mysql_pool": mysql_pool_status(),
        "redis": {
            "health": redis_health(),
            "settings": redis_settings(),
        },
        "rag": {
            "v2_enabled": os.environ.get("RAG_V2_ENABLED", "1").strip().lower() in {"1", "true", "yes", "on"},
            "embedding": embedding_status(),
        },
        "agent": public_policy(),
        "secrets_exposed": False,
    }


def _tool_map() -> dict[str, Any]:
    return {
        "knowledge.search": lambda arguments: retrieve_published_content_v2(
            str(arguments.get("query") or ""),
            int(arguments.get("limit") or 4),
            method=str(arguments.get("method") or "rrf"),
            audience="researcher",
        ),
        "runtime.config": lambda arguments: _safe_runtime_config(),
        "schema.migrations": lambda arguments: {"migrations": migration_manifest(), "mutated": False},
    }


def _plan(objective: str, max_calls: int) -> list[dict]:
    """Deterministic router; no model decides permissions or tools in Agent v1."""
    text = objective.lower()
    steps: list[dict] = []
    knowledge_tokens = ("知识", "内容", "检索", "rag", "文献", "指南", "卡片", "课程")
    runtime_tokens = ("运行", "配置", "mysql", "redis", "embedding", "缓存", "连接池", "runtime")
    migration_tokens = ("迁移", "migration", "schema", "数据库结构")

    if any(token in text for token in knowledge_tokens):
        steps.append({"tool": "knowledge.search", "arguments": {"query": objective, "limit": 4, "method": "rrf"}})
    if any(token in text for token in runtime_tokens):
        steps.append({"tool": "runtime.config", "arguments": {}})
    if any(token in text for token in migration_tokens):
        steps.append({"tool": "schema.migrations", "arguments": {}})
    if not steps:
        # Default to the least-privileged useful tool.  It returns approved
        # knowledge only and performs no state-changing operation.
        steps.append({"tool": "knowledge.search", "arguments": {"query": objective, "limit": 4, "method": "rrf"}})
    return steps[:max_calls]


def _insert_run(actor: dict, objective_hash: str, tool_budget: int, policy: dict) -> str:
    run_id = new_id("agent_run")
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO agent_runs
            (id, actor_id, actor_role, objective_hash, status, planner,
             policy_version, tool_budget, tool_count, synthetic_data,
             metadata_json, created_at)
            VALUES (?, ?, ?, ?, 'running', ?, ?, ?, 0, 1, '{}', ?)
            """,
            (
                run_id,
                str(actor["id"]),
                str(actor["role"]),
                objective_hash,
                str(policy["planner"]),
                str(policy["version"]),
                tool_budget,
                now_iso(),
            ),
        )
        write_audit_log(
            conn,
            "agent_run_started",
            str(actor["id"]),
            "agent_run",
            run_id,
            {
                "objective_hash": objective_hash,
                "planner": policy["planner"],
                "synthetic_data": True,
                "raw_objective_stored": False,
            },
        )
        conn.commit()
    return run_id


def _record_tool_call(run_id: str, tool_name: str, arguments: dict, result: Any = None, *, error_code: str | None = None, latency_ms: float = 0.0) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO agent_tool_calls
            (id, run_id, tool_name, status, input_hash, output_hash,
             latency_ms, error_code, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                new_id("agent_tool"),
                run_id,
                tool_name,
                "failed" if error_code else "completed",
                _hash(arguments),
                None if error_code else _hash(result),
                round(float(latency_ms), 2),
                error_code,
                now_iso(),
            ),
        )
        conn.commit()


def _finish_run(run_id: str, actor: dict, *, status: str, tool_names: list[str], error_code: str | None = None) -> None:
    metadata = {
        "tool_names": tool_names,
        "error_code": error_code,
        "raw_objective_stored": False,
        "raw_tool_io_stored": False,
    }
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE agent_runs
            SET status = ?, tool_count = ?, metadata_json = ?, completed_at = ?
            WHERE id = ?
            """,
            (status, len(tool_names), json_dumps(metadata), now_iso(), run_id),
        )
        write_audit_log(
            conn,
            "agent_run_completed" if status == "completed" else "agent_run_failed",
            str(actor["id"]),
            "agent_run",
            run_id,
            metadata,
        )
        conn.commit()


def run_agent(actor: dict, objective: str, *, synthetic_data: bool) -> dict:
    policy = _assert_actor(actor, synthetic_data)
    objective = str(objective or "").strip()
    if not objective or len(objective) > 800:
        raise AgentRuntimeError("agent_objective_invalid", "objective不能为空且不能超过800字符", 422)

    configured_cap = max(1, min(int(os.environ.get("AGENT_MAX_TOOL_CALLS", policy["max_tool_calls"])), 8))
    tool_budget = min(configured_cap, int(policy["max_tool_calls"]))
    run_id = _insert_run(actor, _hash(objective), tool_budget, policy)
    allowed_names = {str(item["name"]) for item in policy["allowed_tools"]}
    tools = _tool_map()
    plan = _plan(objective, tool_budget)
    outputs = []
    invoked: list[str] = []
    try:
        for step in plan:
            tool_name = str(step["tool"])
            arguments = dict(step.get("arguments") or {})
            if tool_name not in allowed_names or tool_name not in tools:
                raise AgentRuntimeError("agent_tool_forbidden", f"工具未在白名单中：{tool_name}", 403)
            started = time.perf_counter()
            try:
                result = tools[tool_name](arguments)
            except Exception as exc:
                latency = (time.perf_counter() - started) * 1000
                _record_tool_call(run_id, tool_name, arguments, error_code=exc.__class__.__name__, latency_ms=latency)
                invoked.append(tool_name)
                raise
            latency = (time.perf_counter() - started) * 1000
            _record_tool_call(run_id, tool_name, arguments, result, latency_ms=latency)
            invoked.append(tool_name)
            outputs.append({"tool": tool_name, "result": result, "latency_ms": round(latency, 2)})
        _finish_run(run_id, actor, status="completed", tool_names=invoked)
    except Exception as exc:
        _finish_run(run_id, actor, status="failed", tool_names=invoked, error_code=exc.__class__.__name__)
        if isinstance(exc, AgentRuntimeError):
            raise
        raise AgentRuntimeError("agent_tool_failed", "Agent只读工具执行失败", 503, {"error_class": exc.__class__.__name__}) from exc

    return {
        "run_id": run_id,
        "status": "completed",
        "planner": policy["planner"],
        "policy_version": policy["version"],
        "synthetic_data": True,
        "write_tools_allowed": False,
        "plan": [{"tool": item["tool"]} for item in plan],
        "outputs": outputs,
        "boundary_notice": policy["boundary_notice"],
    }
