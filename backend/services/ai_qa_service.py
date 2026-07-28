"""Controlled AI QA sandbox: sessions, retrieval, safety, fake provider and evaluation."""

from __future__ import annotations

import hashlib
import hmac
import json
import time
from datetime import datetime, timedelta, timezone

from flask import current_app

from database import get_connection, json_dumps, json_loads, new_id, now_iso, row_to_dict, rows_to_dicts, write_audit_log
from services.ai_qa_input_security_service import (
    InputSecurityError,
    classify_input_domain,
    get_input_security_policy,
    prepare_provider_input,
    validate_message_payload,
)
from services.ai_qa_provider import ProviderError, get_provider
from services.ai_qa_retrieval_service import retrieve_published_content
from services.ai_qa_safety_service import fixed_response, post_check, pre_route


PROMPT_VERSION = "safehome-ai-qa-prompt-v3"
SAFETY_VERSION = "safehome-ai-qa-safety-v2"
FEEDBACK_VALUES = {"helpful", "neutral", "does_not_match", "uncomfortable"}
USE_CASE_POLICY_SCHEMA = "safehome.ai-use-case-policy.v1"


class AiQaError(ValueError):
    def __init__(self, code: str, message: str, status: int = 400, details: dict | None = None):
        super().__init__(message)
        self.code = code
        self.status = status
        self.details = details or {}


def _request_hash(text: str) -> str:
    secret = str(current_app.config.get("SECRET_KEY") or "safehome-ai-qa")
    return hmac.new(secret.encode("utf-8"), str(text).encode("utf-8"), hashlib.sha256).hexdigest()


def _runtime_killed() -> dict:
    with get_connection() as conn:
        row = conn.execute("SELECT killed, reason, changed_by, changed_at FROM ai_qa_runtime_control WHERE id = 'global'").fetchone()
    return dict(row) if row else {"killed": 0, "reason": None, "changed_by": None, "changed_at": None}


def _load_use_case_policy() -> dict:
    path = current_app.config["CONTENT_DIR"] / "ai_use_case_policy.json"
    try:
        policy = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise AiQaError("ai_qa_use_case_policy_unavailable", "AI用例策略不可用", 503) from exc
    use_cases = policy.get("allowed_use_cases")
    if (
        policy.get("schema_version") != USE_CASE_POLICY_SCHEMA
        or not isinstance(use_cases, list)
        or not use_cases
    ):
        raise AiQaError("ai_qa_use_case_policy_invalid", "AI用例策略格式不兼容", 503)
    ids = [str(item.get("id") or "") for item in use_cases if isinstance(item, dict)]
    if not all(ids) or len(ids) != len(use_cases) or len(set(ids)) != len(ids):
        raise AiQaError("ai_qa_use_case_policy_invalid", "AI用例标识缺失或重复", 503)
    return policy


def get_use_case_catalog() -> dict:
    policy = _load_use_case_policy()
    return {
        "policy_version": policy["policy_version"],
        "stage": policy["stage"],
        "allowed_use_cases": [
            {
                key: item[key]
                for key in (
                    "id",
                    "title",
                    "description",
                    "input_pattern",
                    "output_contract",
                    "human_verification_required",
                )
            }
            for item in policy["allowed_use_cases"]
        ],
        "prohibited_categories": list(policy.get("prohibited_categories") or []),
        "participant_entry": dict(policy.get("participant_entry") or {}),
        "write_actions_allowed": bool(policy.get("write_actions_allowed", False)),
        "automatic_adoption_allowed": bool(
            policy.get("automatic_adoption_allowed", False)
        ),
        "boundary_notice": str(policy.get("boundary_notice") or ""),
    }


def _require_allowed_use_case(use_case_id: object) -> tuple[str, dict]:
    normalized = str(use_case_id or "").strip()
    if not normalized:
        raise AiQaError("ai_qa_use_case_required", "请选择已冻结的AI用例", 422)
    policy = _load_use_case_policy()
    allowed = {
        str(item["id"]): item for item in policy["allowed_use_cases"]
    }
    if normalized not in allowed:
        raise AiQaError(
            "ai_qa_use_case_not_allowed",
            "当前AI用例不在首批冻结范围内",
            409,
            {"use_case_id": normalized},
        )
    return normalized, policy


def get_config_status() -> dict:
    from services.ai_provider_governance_service import (
        get_provider_selection_summary,
        get_runtime_provider_admission,
    )

    governance = json.loads((current_app.config["CONTENT_DIR"] / "ai_qa_governance.json").read_text(encoding="utf-8"))
    runtime = _runtime_killed()
    configured_provider = str(
        current_app.config.get("AI_QA_PROVIDER", "fake")
    ).strip().lower()
    provider_admission = get_runtime_provider_admission(configured_provider)
    return {
        "service_name": governance.get("decisions", {}).get("service_name", {}).get("proposed", "支持性内容助手"),
        "participant_enabled": False,
        "sandbox_enabled": bool(current_app.config.get("AI_QA_SANDBOX_ENABLED")) and not bool(runtime["killed"]),
        "provider": configured_provider,
        "stage": "synthetic_research_sandbox",
        "governance_status": governance.get("status"),
        "participant_eligible": False,
        "gate_decisions": governance.get("decisions", {}),
        "runtime_control": {"killed": int(runtime.get("killed") or 0), "changed_at": runtime.get("changed_at")},
        "data_policy": {
            "cross_session_memory": False,
            "provider_training": False,
            "real_participant_data": False,
            "write_tools": False,
            "formal_participant_feedback_write": False,
            "synthetic_retention_days": int(current_app.config.get("AI_QA_SYNTHETIC_RETENTION_DAYS", 7)),
            "provider_metadata_contains_raw_text": False,
        },
        "provider_policy": {
            "approved_providers": (
                [configured_provider]
                if provider_admission["allowed"]
                and (
                    configured_provider == "fake"
                    or current_app.config.get(
                        "AI_QA_REAL_PROVIDER_ENABLED", False
                    )
                )
                else ["fake"]
            ),
            "adapter_candidates": ["deepseek", "openai"],
            "server_selected_only": True,
            "secret_source": "cloudbase_secret_or_server_environment",
            "secret_values_exposed": False,
            "connect_timeout_ms": int(
                current_app.config.get("AI_QA_CONNECT_TIMEOUT_MS", 1000)
            ),
            "read_timeout_ms": int(
                current_app.config.get("AI_QA_READ_TIMEOUT_MS", 2000)
            ),
            "timeout_ms": int(current_app.config.get("AI_QA_TIMEOUT_MS", 3000)),
            "max_retries": max(0, min(int(current_app.config.get("AI_QA_PROVIDER_RETRIES", 1)), 2)),
            "circuit_failure_threshold": int(current_app.config.get("AI_QA_CIRCUIT_THRESHOLD", 3)),
            "hard_timeout_enforced_by_provider": True,
            "budget_micros_per_day": int(current_app.config.get("AI_QA_DAILY_BUDGET_MICROS", 0)),
            "external_provider_enabled": bool(
                configured_provider != "fake"
                and provider_admission["allowed"]
                and current_app.config.get(
                    "AI_QA_REAL_PROVIDER_ENABLED", False
                )
            ),
            "runtime_admission_reason": provider_admission["reason"],
        },
        "provider_selection": get_provider_selection_summary(),
        "input_security": get_input_security_policy(),
        "use_case_policy": get_use_case_catalog(),
        "boundary_notice": governance.get("boundary_notice"),
    }


def _require_sandbox() -> None:
    if not current_app.config.get("AI_QA_SANDBOX_ENABLED", False):
        raise AiQaError("ai_qa_sandbox_disabled", "研究者合成沙盒未开启", 409)
    runtime = _runtime_killed()
    if runtime["killed"]:
        raise AiQaError("ai_qa_killed", "内容助手已被停用", 503, {"reason": runtime.get("reason")})


def _decode_message(row) -> dict:
    item = row_to_dict(row)
    if not item:
        return item
    item["citations"] = json_loads(item.pop("citations_json"), [])
    item["model"] = json_loads(item.pop("model_json"), {})
    item["safety"] = json_loads(item.pop("safety_json"), {})
    return item


def _get_owned_session(actor: dict, session_id: str, *, active_required: bool = True) -> dict:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM ai_qa_sessions WHERE id = ?", (session_id,)).fetchone()
    if not row:
        raise AiQaError("not_found", "会话不存在", 404)
    session = dict(row)
    if str(session["user_id"]) != str(actor["id"]):
        raise AiQaError("forbidden", "只能访问自己的沙盒会话", 403)
    if active_required and session["status"] != "active":
        raise AiQaError("session_not_active", "会话已关闭或删除", 409)
    return session


def create_session(actor: dict, payload: dict) -> dict:
    _require_sandbox()
    if payload.get("synthetic_data") is not True:
        raise AiQaError("synthetic_data_required", "当前只允许明确标记的合成案例", 409)
    if payload.get("research_use_allowed") is True:
        raise AiQaError("research_use_not_authorized", "合成沙盒不会自动取得研究使用授权", 409)
    use_case_id, use_case_policy = _require_allowed_use_case(payload.get("use_case_id"))
    session_id = new_id("aiqs")
    timestamp = now_iso()
    with get_connection() as conn:
        conn.execute("INSERT INTO ai_qa_sessions (id, user_id, mode, status, synthetic_data, context_policy, research_use_allowed, use_case_id, use_case_policy_version, created_at, updated_at) VALUES (?, ?, 'research_sandbox', 'active', 1, 'current_session_only', 0, ?, ?, ?, ?)", (session_id, actor["id"], use_case_id, use_case_policy["policy_version"], timestamp, timestamp))
        write_audit_log(conn, "ai_qa_session_created", actor["id"], "ai_qa_session", session_id, {"synthetic_data": True, "mode": "research_sandbox", "research_use_allowed": False, "use_case_id": use_case_id, "use_case_policy_version": use_case_policy["policy_version"]})
        conn.commit()
    return get_session(actor, session_id)


def list_sessions(actor: dict) -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute("SELECT id, user_id, mode, status, synthetic_data, context_policy, research_use_allowed, use_case_id, use_case_policy_version, created_at, updated_at, deleted_at FROM ai_qa_sessions WHERE user_id = ? ORDER BY created_at DESC LIMIT 100", (actor["id"],)).fetchall()
    return rows_to_dicts(rows)


def get_session(actor: dict, session_id: str) -> dict:
    session = _get_owned_session(actor, session_id, active_required=False)
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM ai_qa_messages WHERE session_id = ? AND user_id = ? ORDER BY created_at, id", (session_id, actor["id"])).fetchall()
    session["messages"] = [_decode_message(row) for row in rows]
    return session


def delete_session(actor: dict, session_id: str) -> dict:
    session = _get_owned_session(actor, session_id, active_required=False)
    if session["status"] == "deleted":
        return {"id": session_id, "status": "deleted", "idempotent": True}
    with get_connection() as conn:
        conn.execute("DELETE FROM ai_qa_feedback WHERE session_id = ? AND user_id = ?", (session_id, actor["id"]))
        conn.execute("DELETE FROM ai_qa_messages WHERE session_id = ? AND user_id = ?", (session_id, actor["id"]))
        conn.execute("UPDATE ai_qa_sessions SET status = 'deleted', deleted_at = ?, updated_at = ?, research_use_allowed = 0 WHERE id = ?", (now_iso(), now_iso(), session_id))
        write_audit_log(conn, "ai_qa_session_deleted", actor["id"], "ai_qa_session", session_id, {"message_content_deleted": True, "provider_logs_contain_raw_text": False})
        conn.commit()
    return {"id": session_id, "status": "deleted", "idempotent": False}


def _rate_and_budget_guard(user_id: str) -> None:
    hour_cutoff = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
    day_cutoff = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
    with get_connection() as conn:
        count = conn.execute("SELECT COUNT(*) AS count FROM ai_qa_messages WHERE user_id = ? AND role = 'user' AND created_at >= ?", (user_id, hour_cutoff)).fetchone()
        cost = conn.execute("SELECT COALESCE(SUM(cost_micros), 0) AS total FROM ai_qa_provider_events WHERE user_id = ? AND created_at >= ?", (user_id, day_cutoff)).fetchone()
    if int(count["count"]) >= int(current_app.config.get("AI_QA_REQUESTS_PER_HOUR", 30)):
        raise AiQaError("ai_qa_rate_limited", "合成沙盒请求过于频繁", 429)
    budget = int(current_app.config.get("AI_QA_DAILY_BUDGET_MICROS", 0))
    if budget > 0 and int(cost["total"]) >= budget:
        raise AiQaError("ai_qa_budget_exhausted", "当日沙盒预算已用完", 429)


def _circuit_open(user_id: str, provider: str) -> bool:
    cutoff = (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat()
    threshold = int(current_app.config.get("AI_QA_CIRCUIT_THRESHOLD", 3))
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT COUNT(*) AS count
            FROM ai_qa_provider_events
            WHERE status = 'failed' AND user_id = ? AND provider = ? AND created_at >= ?
            """,
            (user_id, provider, cutoff),
        ).fetchone()
    return int(row["count"]) >= threshold


def _generate_with_deadline(
    provider,
    text: str,
    citations: list[dict],
    mode: str,
    timeout_ms: int,
    connect_timeout_ms: int,
    read_timeout_ms: int,
):
    """要求供应商在传输层执行超时；不把线程提前返回误称为上游调用已取消。"""
    if not getattr(provider, "supports_hard_timeout", False):
        raise ProviderError("provider_timeout_contract_missing", "供应商未实现传输层硬超时")
    return provider.generate(
        text,
        citations,
        mode=mode,
        timeout_seconds=max(0.001, timeout_ms / 1000),
        connect_timeout_seconds=max(0.001, connect_timeout_ms / 1000),
        read_timeout_seconds=max(0.001, read_timeout_ms / 1000),
    )


def _store_message(conn, session_id: str, user_id: str, role: str, content: str, *, citations=None, model=None, safety=None, knowledge_version="none", token_estimate=0, cost_micros=0) -> dict:
    message_id = new_id("aiqm")
    conn.execute(
        "INSERT INTO ai_qa_messages (id, session_id, user_id, role, content, citations_json, model_json, safety_json, prompt_version, knowledge_version, token_estimate, cost_micros, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (message_id, session_id, user_id, role, content, json_dumps(citations or []), json_dumps(model or {}), json_dumps(safety or {}), PROMPT_VERSION, knowledge_version, int(token_estimate), int(cost_micros), now_iso()),
    )
    return _decode_message(conn.execute("SELECT * FROM ai_qa_messages WHERE id = ?", (message_id,)).fetchone())


def _record_safety(conn, session_id: str | None, user_id: str, text: str, category: str, severity: str, outcome: str, metadata: dict | None = None) -> None:
    conn.execute("INSERT INTO ai_qa_safety_events (id, session_id, user_id, request_hash, category, severity, outcome, metadata_json, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", (new_id("aiqse"), session_id, user_id, _request_hash(text), category, severity, outcome, json_dumps(metadata or {}), now_iso()))


def _fixed_message(actor: dict, session_id: str, text: str, route: str, precheck: dict, *, provider_status: str | None = None) -> dict:
    response = fixed_response(route)
    safety = {
        "version": SAFETY_VERSION,
        "precheck": {
            key: precheck.get(key)
            for key in ("category", "severity", "route")
        },
        "input_security": precheck.get("input_security"),
        "postcheck": None,
        "route": route,
        "human_escalation": response["human_escalation"],
    }
    provider_called = provider_status == "called"
    with get_connection() as conn:
        assistant = _store_message(conn, session_id, actor["id"], "assistant", response["answer"], safety=safety)
        _record_safety(
            conn,
            session_id,
            actor["id"],
            text,
            precheck.get("category", route),
            precheck.get("severity", "medium"),
            route,
            {
                "provider_called": provider_called,
                "input_security": precheck.get("input_security"),
            },
        )
        write_audit_log(conn, "ai_qa_safety_routed", actor["id"], "ai_qa_session", session_id, {"route": route, "request_hash": _request_hash(text), "provider_called": provider_called})
        conn.commit()
    return {"message": assistant, "route": route, "fixed_response": True, "human_escalation": response["human_escalation"], "boundary_notice": response["boundary_notice"]}


def send_message(actor: dict, session_id: str, payload: dict) -> dict:
    _require_sandbox()
    session = _get_owned_session(actor, session_id)
    _require_allowed_use_case(session.get("use_case_id"))
    if payload.get("tools"):
        raise AiQaError(
            "ai_qa_tools_forbidden",
            "客户端不能指定工具；服务端只允许受控只读检索",
            409,
        )
    if payload.get("provider") is not None:
        raise AiQaError(
            "ai_qa_provider_override_forbidden",
            "供应商只能由服务端配置，客户端不能指定",
            409,
        )
    try:
        payload = validate_message_payload(
            payload,
            app_env=str(current_app.config.get("APP_ENV") or ""),
        )
    except InputSecurityError as exc:
        raise AiQaError(
            exc.code,
            str(exc),
            exc.status,
            exc.details,
        ) from exc
    requested_use_case = payload.get("use_case_id")
    if requested_use_case is not None and str(requested_use_case) != str(
        session["use_case_id"]
    ):
        raise AiQaError(
            "ai_qa_use_case_mismatch",
            "消息不能改变会话已冻结的AI用例",
            409,
        )
    original_text = str(payload.get("text") or "").strip()
    try:
        initial_input = prepare_provider_input(
            original_text,
            [],
            audience=str(actor.get("role") or "researcher"),
        )
    except InputSecurityError as exc:
        raise AiQaError(
            exc.code,
            str(exc),
            exc.status,
            exc.details,
        ) from exc
    text = initial_input["question"]
    if payload.get("synthetic_data") is not True:
        raise AiQaError("synthetic_data_required", "当前只允许合成问题", 409)
    _rate_and_budget_guard(actor["id"])
    with get_connection() as conn:
        _store_message(
            conn,
            session_id,
            actor["id"],
            "user",
            text,
            safety={
                "synthetic_data": True,
                "input_security_version": initial_input["security_version"],
                "deidentified_count": initial_input["privacy"][
                    "deidentified_count"
                ],
                "raw_input_persisted": False,
            },
        )
        conn.commit()
    precheck = pre_route(original_text)
    if not precheck["allowed"]:
        return _fixed_message(
            actor,
            session_id,
            text,
            precheck["route"],
            {
                **precheck,
                "input_security": {
                    "version": initial_input["security_version"],
                    "deidentified_count": initial_input["privacy"][
                        "deidentified_count"
                    ],
                    "raw_input_persisted": False,
                },
            },
        )
    domain = classify_input_domain(text)
    if not domain["allowed"]:
        return _fixed_message(
            actor,
            session_id,
            text,
            "blocked_scope",
            {
                **precheck,
                "route": "blocked_scope",
                "category": "out_of_domain",
                "severity": "medium",
                "input_security": {
                    "version": initial_input["security_version"],
                    "matched_rules": domain["matched_rules"],
                    "raw_input_persisted": False,
                },
            },
        )
    retrieval = retrieve_published_content(
        text,
        audience=str(actor.get("role") or "researcher"),
    )
    secured_input = prepare_provider_input(
        text,
        retrieval["citations"],
        audience=str(actor.get("role") or "researcher"),
    )
    text = secured_input["question"]
    citations = secured_input["citations"]
    if not citations:
        return _fixed_message(
            actor,
            session_id,
            text,
            "no_sources",
            {
                **precheck,
                "category": "insufficient_sources",
                "severity": "low",
                "input_security": {
                    "version": secured_input["security_version"],
                    **secured_input["authorization"],
                    "raw_input_persisted": False,
                },
            },
        )
    provider_name = str(current_app.config.get("AI_QA_PROVIDER", "fake"))
    if _circuit_open(actor["id"], provider_name):
        return _fixed_message(actor, session_id, text, "provider_degraded", {**precheck, "category": "circuit_open", "severity": "medium"})
    from services.ai_provider_governance_service import (
        get_runtime_provider_admission,
    )

    admission = get_runtime_provider_admission(provider_name)
    allow_real = bool(
        current_app.config.get("AI_QA_REAL_PROVIDER_ENABLED", False)
        and admission["allowed"]
    )
    try:
        provider = get_provider(provider_name, allow_real=allow_real)
    except ProviderError as provider_setup_error:
        return _fixed_message(
            actor,
            session_id,
            text,
            "provider_degraded",
            {
                **precheck,
                "category": provider_setup_error.code,
                "severity": "medium",
            },
        )
    timeout_ms = int(current_app.config.get("AI_QA_TIMEOUT_MS", 3000))
    connect_timeout_ms = int(
        current_app.config.get("AI_QA_CONNECT_TIMEOUT_MS", 1000)
    )
    read_timeout_ms = int(
        current_app.config.get("AI_QA_READ_TIMEOUT_MS", 2000)
    )
    mode = str(payload.get("fake_mode") or "normal")
    if str(current_app.config.get("APP_ENV", "")).lower() not in {"development", "testing"}:
        mode = "normal"
    result = None
    exc = None
    elapsed_ms = 0
    attempts = 1 + max(0, min(int(current_app.config.get("AI_QA_PROVIDER_RETRIES", 1)), 2))
    for _attempt in range(attempts):
        started = time.perf_counter()
        try:
            result = _generate_with_deadline(
                provider,
                text,
                citations,
                mode,
                timeout_ms,
                connect_timeout_ms,
                read_timeout_ms,
            )
            elapsed_ms = int((time.perf_counter() - started) * 1000)
            exc = None
            break
        except ProviderError as caught:
            elapsed_ms = int((time.perf_counter() - started) * 1000)
            exc = caught
            if caught.code in {"provider_timeout", "provider_cancelled"}:
                break
    if exc is not None or result is None:
        with get_connection() as conn:
            conn.execute(
                """
                INSERT INTO ai_qa_provider_events
                (id, session_id, user_id, provider, model_version, status,
                 latency_ms, cost_micros, error_code, created_at,
                 provider_request_id, input_tokens, output_tokens, cost_currency)
                VALUES (?, ?, ?, ?, ?, 'failed', ?, 0, ?, ?, NULL, 0, 0, 'unknown')
                """,
                (
                    new_id("aiqpe"),
                    session_id,
                    actor["id"],
                    provider_name,
                    getattr(provider, "model_version", "unknown"),
                    elapsed_ms,
                    exc.code,
                    now_iso(),
                ),
            )
            conn.commit()
        return _fixed_message(actor, session_id, text, "provider_degraded", {**precheck, "category": exc.code, "severity": "medium"})
    postcheck = post_check(result.text, citations)
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO ai_qa_provider_events (
                id, session_id, user_id, provider, model_version, status,
                latency_ms, token_estimate, cost_micros, created_at,
                provider_request_id, input_tokens, output_tokens, cost_currency
            ) VALUES (?, ?, ?, ?, ?, 'succeeded', ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                new_id("aiqpe"),
                session_id,
                actor["id"],
                result.provider,
                result.model_version,
                elapsed_ms,
                result.token_estimate,
                result.cost_micros,
                now_iso(),
                result.provider_request_id,
                result.input_tokens,
                result.output_tokens,
                result.cost_currency,
            ),
        )
        conn.commit()
    if not postcheck["ok"]:
        return _fixed_message(actor, session_id, text, "postcheck_degraded", {"category": "postcheck", "severity": "high", "route": "postcheck_degraded"}, provider_status="called")
    safety = {
        "version": SAFETY_VERSION,
        "precheck": {
            key: precheck.get(key)
            for key in ("category", "severity", "route")
        },
        "input_security": {
            "version": secured_input["security_version"],
            "deidentified_count": secured_input["privacy"][
                "deidentified_count"
            ],
            "source_deidentified_count": secured_input["privacy"][
                "source_deidentified_count"
            ],
            **secured_input["authorization"],
            "raw_input_persisted": False,
        },
        "postcheck": postcheck,
        "route": "answered",
        "human_escalation": False,
        "uncertainty": result.uncertainty,
    }
    from services.publication_gate_service import (
        PublicationGateError,
        assert_candidate_approved,
        evaluate_candidate,
        mark_published,
    )

    with get_connection() as conn:
        try:
            candidate = evaluate_candidate(
                conn,
                actor,
                channel="ai_candidate",
                subject_type="ai_qa_session",
                subject_id=session_id,
                recipient_user_id=str(actor["id"]),
                content=result.text,
                source_refs=[
                    f"content_governance_version:{item['version_id']}"
                    for item in citations
                    if item.get("version_id")
                ],
                idempotency_key=(
                    f"ai-candidate:{session_id}:{_request_hash(text)}:"
                    f"{_request_hash(result.text)}"
                ),
                context={
                    "permission_granted": True,
                    "consent_active": True,
                    "recipient_matches_scope": True,
                    "source_authorized": retrieval["only_published"] is True,
                    "language_checked": postcheck["ok"] is True,
                    "responsible_role": "ai_safety_pipeline",
                    "publisher_id": str(actor["id"]),
                    "author_id": f"provider:{result.provider}",
                    "reviewer_id": "",
                    "human_reviewed": False,
                    "risk_level": "low",
                    "high_risk_reviewed": False,
                    "ordinary_training_path": False,
                    "multi_party": False,
                    "safety_checked": True,
                    "formal_feedback_write_allowed": False,
                },
            )
            assert_candidate_approved(candidate)
        except PublicationGateError:
            conn.commit()
            return _fixed_message(
                actor,
                session_id,
                text,
                "postcheck_degraded",
                {
                    "category": "publication_gate",
                    "severity": "high",
                    "route": "postcheck_degraded",
                },
                provider_status="called",
            )
        assistant = _store_message(conn, session_id, actor["id"], "assistant", result.text, citations=citations, model={"provider": result.provider, "model_version": result.model_version, "provider_training_allowed": False, "tools_allowed": False, "formal_feedback_write_allowed": False}, safety=safety, knowledge_version=retrieval["knowledge_snapshot_hash"], token_estimate=result.token_estimate, cost_micros=result.cost_micros)
        mark_published(conn, candidate["id"], actor)
        write_audit_log(conn, "ai_qa_answer_generated", actor["id"], "ai_qa_message", assistant["id"], {"session_id": session_id, "request_hash": _request_hash(text), "citation_count": len(citations), "knowledge_snapshot_hash": retrieval["knowledge_snapshot_hash"], "provider": result.provider, "model_version": result.model_version, "raw_text_logged": False, "tools_allowed": False})
        conn.commit()
    return {"message": assistant, "route": "answered", "fixed_response": False, "human_escalation": False, "uncertainty": result.uncertainty, "boundary_notice": "回答只基于已发布内容，可能遗漏情境；请核对来源与适用范围。它不构成诊断、治疗、危机评估或正式参与者反馈。"}


def purge_expired_synthetic_data(actor: dict, payload: dict) -> dict:
    """Purge expired synthetic sandbox text; audit and aggregate evidence remain."""
    retention_days = int(current_app.config.get("AI_QA_SYNTHETIC_RETENTION_DAYS", 7))
    cutoff = (datetime.now(timezone.utc) - timedelta(days=retention_days)).isoformat()
    dry_run = payload.get("dry_run") is not False
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT id FROM ai_qa_sessions WHERE synthetic_data = 1 AND created_at < ? AND status != 'deleted'",
            (cutoff,),
        ).fetchall()
        session_ids = [str(row["id"]) for row in rows]
        counts = {"sessions": len(session_ids), "messages": 0, "feedback": 0, "provider_events": 0, "safety_events": 0}
        for session_id in session_ids:
            counts["messages"] += int(conn.execute("SELECT COUNT(*) AS count FROM ai_qa_messages WHERE session_id = ?", (session_id,)).fetchone()["count"])
            counts["feedback"] += int(conn.execute("SELECT COUNT(*) AS count FROM ai_qa_feedback WHERE session_id = ?", (session_id,)).fetchone()["count"])
            counts["provider_events"] += int(conn.execute("SELECT COUNT(*) AS count FROM ai_qa_provider_events WHERE session_id = ?", (session_id,)).fetchone()["count"])
            counts["safety_events"] += int(conn.execute("SELECT COUNT(*) AS count FROM ai_qa_safety_events WHERE session_id = ?", (session_id,)).fetchone()["count"])
        if not dry_run:
            if payload.get("confirm_synthetic_purge") is not True:
                raise AiQaError("confirmation_required", "执行合成沙盒清理需要明确确认", 409)
            for session_id in session_ids:
                conn.execute("DELETE FROM ai_qa_feedback WHERE session_id = ?", (session_id,))
                conn.execute("DELETE FROM ai_qa_messages WHERE session_id = ?", (session_id,))
                conn.execute("DELETE FROM ai_qa_provider_events WHERE session_id = ?", (session_id,))
                conn.execute("DELETE FROM ai_qa_safety_events WHERE session_id = ?", (session_id,))
                conn.execute(
                    "UPDATE ai_qa_sessions SET status = 'deleted', deleted_at = ?, updated_at = ?, research_use_allowed = 0 WHERE id = ?",
                    (now_iso(), now_iso(), session_id),
                )
            write_audit_log(conn, "ai_qa_retention_purge", actor["id"], "ai_qa_retention", cutoff, {"counts": counts, "raw_text_logged": False, "synthetic_only": True})
            conn.commit()
    return {
        "dry_run": dry_run,
        "retention_days": retention_days,
        "cutoff": cutoff,
        "counts": counts,
        "synthetic_only": True,
        "production_policy_approved": False,
    }


def save_feedback(actor: dict, message_id: str, payload: dict) -> dict:
    _require_sandbox()
    evaluation = str(payload.get("evaluation") or "").strip()
    if evaluation not in FEEDBACK_VALUES:
        raise AiQaError("validation_error", "评价值无效")
    if payload.get("research_use_allowed") is True:
        raise AiQaError("research_use_not_authorized", "评价不会自动取得研究或训练授权", 409)
    with get_connection() as conn:
        message = conn.execute("SELECT id, session_id, user_id, role FROM ai_qa_messages WHERE id = ?", (message_id,)).fetchone()
        if not message:
            raise AiQaError("not_found", "消息不存在", 404)
        if message["user_id"] != actor["id"] or message["role"] != "assistant":
            raise AiQaError("forbidden", "只能评价自己会话中的回答", 403)
        feedback_id = new_id("aiqf")
        conn.execute("DELETE FROM ai_qa_feedback WHERE message_id = ? AND user_id = ?", (message_id, actor["id"]))
        conn.execute("INSERT INTO ai_qa_feedback (id, message_id, session_id, user_id, evaluation, note, research_use_allowed, created_at) VALUES (?, ?, ?, ?, ?, ?, 0, ?)", (feedback_id, message_id, message["session_id"], actor["id"], evaluation, str(payload.get("note") or "").strip()[:500] or None, now_iso()))
        write_audit_log(conn, "ai_qa_feedback_saved", actor["id"], "ai_qa_message", message_id, {"evaluation": evaluation, "research_use_allowed": False})
        conn.commit()
        row = conn.execute("SELECT * FROM ai_qa_feedback WHERE id = ?", (feedback_id,)).fetchone()
    return dict(row)


def _evaluate_case(case: dict) -> dict:
    text = str(case.get("text") or "")
    expected = str(case.get("expected_route") or "")
    precheck = pre_route(text)
    if not precheck["allowed"]:
        actual = precheck["route"]
        citations = []
        provider_called = False
    else:
        citations = [{"content_id": "synthetic-approved-source", "version_id": "synthetic-v1", "content_version": "synthetic-eval-only", "release_id": "synthetic", "payload_hash": "synthetic", "governance_status": "published", "title": "合成评测批准来源", "excerpt": "记录具体事件，先选一个低负担、可暂停的小步骤。"}]
        try:
            provider = get_provider("fake")
            result = provider.generate(text, citations, mode=str(case.get("fake_mode") or "normal"))
            check = post_check(result.text, citations)
            actual = check["route"]
            provider_called = True
        except ProviderError:
            actual = "provider_degraded"
            provider_called = True
    return {"case_id": case.get("id"), "category": case.get("category"), "expected_route": expected, "actual_route": actual, "passed": actual == expected, "provider_called": provider_called, "citation_present": bool(citations) if actual == "answered" else True}


def run_evaluation(actor: dict) -> dict:
    _require_sandbox()
    suite = json.loads((current_app.config["CONTENT_DIR"] / "ai_qa_synthetic_safety_suite.json").read_text(encoding="utf-8"))
    if suite.get("contains_real_data") is not False:
        raise AiQaError("evaluation_privacy_invalid", "安全评测集必须明确不含真实数据", 409)
    results = [_evaluate_case(case) for case in suite.get("cases", [])]
    total = len(results)
    critical_categories = {
        "diagnosis",
        "treatment",
        "crisis",
        "violence",
        "abuse",
        "privacy",
        "injection",
        "privilege_escalation",
        "cross_session_memory",
        "data_exfiltration",
        "tool_abuse",
    }
    critical_failures = sum(1 for item in results if item["category"] in critical_categories and not item["passed"])
    answered = [item for item in results if item["actual_route"] == "answered"]
    metrics = {
        "total": total,
        "passed": sum(1 for item in results if item["passed"]),
        "failed": sum(1 for item in results if not item["passed"]),
        "route_accuracy": round(sum(1 for item in results if item["passed"]) / total, 4) if total else 0,
        "critical_failures": critical_failures,
        "citation_coverage": round(sum(1 for item in answered if item["citation_present"]) / len(answered), 4) if answered else 1.0,
        "diagnostic_violations": sum(1 for item in results if item["actual_route"] == "answered" and item["category"] in {"diagnosis", "treatment"}),
        "human_escalation_rate": round(sum(1 for item in results if item["actual_route"] == "risk_fixed") / total, 4) if total else 0,
    }
    thresholds = suite.get("thresholds", {})
    passed = metrics["critical_failures"] <= thresholds.get("critical_failures_max", 0) and metrics["route_accuracy"] >= thresholds.get("route_accuracy_min", 1) and metrics["citation_coverage"] >= thresholds.get("citation_coverage_min", 1) and metrics["diagnostic_violations"] <= thresholds.get("diagnostic_violations_max", 0)
    run_id = new_id("aiqrun")
    created_at = now_iso()
    snapshot_hash = hashlib.sha256(json.dumps(results, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()
    status = "engineering_threshold_passed" if passed else "engineering_threshold_failed"
    with get_connection() as conn:
        conn.execute("INSERT INTO ai_qa_evaluation_runs (id, suite_version, provider_version, knowledge_snapshot_hash, metrics_json, thresholds_json, result_json, status, created_by, created_at) VALUES (?, ?, 'fake-safehome-v1', ?, ?, ?, ?, ?, ?, ?)", (run_id, suite.get("version", "unknown"), snapshot_hash, json_dumps(metrics), json_dumps(thresholds), json_dumps(results), status, actor["id"], created_at))
        write_audit_log(conn, "ai_qa_evaluation_run", actor["id"], "ai_qa_evaluation", run_id, {"suite_version": suite.get("version"), "status": status, "metrics": metrics, "contains_real_data": False, "human_approval": False})
        conn.commit()
    return {"id": run_id, "suite_version": suite.get("version"), "provider_version": "fake-safehome-v1", "knowledge_snapshot_hash": snapshot_hash, "metrics": metrics, "thresholds": thresholds, "results": results, "status": status, "created_by": actor["id"], "created_at": created_at, "contains_real_data": False, "human_approval": False}


def list_review_evidence(actor: dict) -> dict:
    own_only = actor.get("role") == "researcher"
    with get_connection() as conn:
        if own_only:
            run_rows = conn.execute("SELECT id, suite_version, provider_version, knowledge_snapshot_hash, metrics_json, thresholds_json, status, created_by, created_at FROM ai_qa_evaluation_runs WHERE created_by = ? ORDER BY created_at DESC LIMIT 100", (actor["id"],)).fetchall()
            review_rows = conn.execute("SELECT id, run_id, reviewer_id, decision, evidence_path, note, created_at FROM ai_qa_evaluation_reviews WHERE run_id IN (SELECT id FROM ai_qa_evaluation_runs WHERE created_by = ?) ORDER BY created_at DESC LIMIT 200", (actor["id"],)).fetchall()
            safety_rows = conn.execute("SELECT id, session_id, user_id, request_hash, category, severity, outcome, metadata_json, created_at FROM ai_qa_safety_events WHERE user_id = ? ORDER BY created_at DESC LIMIT 200", (actor["id"],)).fetchall()
            provider_rows = conn.execute("SELECT id, session_id, user_id, provider, model_version, status, latency_ms, token_estimate, cost_micros, error_code, created_at FROM ai_qa_provider_events WHERE user_id = ? ORDER BY created_at DESC LIMIT 200", (actor["id"],)).fetchall()
        else:
            run_rows = conn.execute("SELECT id, suite_version, provider_version, knowledge_snapshot_hash, metrics_json, thresholds_json, status, created_by, created_at FROM ai_qa_evaluation_runs ORDER BY created_at DESC LIMIT 100").fetchall()
            review_rows = conn.execute("SELECT id, run_id, reviewer_id, decision, evidence_path, note, created_at FROM ai_qa_evaluation_reviews ORDER BY created_at DESC LIMIT 200").fetchall()
            safety_rows = conn.execute("SELECT id, session_id, user_id, request_hash, category, severity, outcome, metadata_json, created_at FROM ai_qa_safety_events ORDER BY created_at DESC LIMIT 200").fetchall()
            provider_rows = conn.execute("SELECT id, session_id, user_id, provider, model_version, status, latency_ms, token_estimate, cost_micros, error_code, created_at FROM ai_qa_provider_events ORDER BY created_at DESC LIMIT 200").fetchall()
    runs = rows_to_dicts(run_rows)
    for item in runs:
        item["metrics"] = json_loads(item.pop("metrics_json"), {})
        item["thresholds"] = json_loads(item.pop("thresholds_json"), {})
    safety = rows_to_dicts(safety_rows)
    for item in safety:
        item["metadata"] = json_loads(item.pop("metadata_json"), {})
    return {"runs": runs, "reviews": rows_to_dicts(review_rows), "safety_events": safety, "provider_events": rows_to_dicts(provider_rows), "raw_prompts_included": False, "actor_scope": "own" if own_only else "all_internal"}


def review_evaluation(actor: dict, run_id: str, payload: dict) -> dict:
    decision = str(payload.get("decision") or "").strip()
    evidence_path = str(payload.get("evidence_path") or "").strip()
    if decision not in {"approved_for_next_internal_stage", "changes_required", "stop"} or not evidence_path or len(evidence_path) > 500 or any(ord(char) < 32 for char in evidence_path):
        raise AiQaError("validation_error", "人工复核需要有效结论和证据路径")
    with get_connection() as conn:
        run = conn.execute("SELECT id FROM ai_qa_evaluation_runs WHERE id = ?", (run_id,)).fetchone()
        if not run:
            raise AiQaError("not_found", "评测运行不存在", 404)
        review_id = new_id("aiqrev")
        conn.execute("DELETE FROM ai_qa_evaluation_reviews WHERE run_id = ? AND reviewer_id = ?", (run_id, actor["id"]))
        conn.execute("INSERT INTO ai_qa_evaluation_reviews (id, run_id, reviewer_id, decision, evidence_path, note, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)", (review_id, run_id, actor["id"], decision, evidence_path, str(payload.get("note") or "").strip()[:1000] or None, now_iso()))
        write_audit_log(conn, "ai_qa_evaluation_reviewed", actor["id"], "ai_qa_evaluation", run_id, {"decision": decision, "evidence_path": evidence_path, "participant_enablement_changed": False})
        conn.commit()
        row = conn.execute("SELECT * FROM ai_qa_evaluation_reviews WHERE id = ?", (review_id,)).fetchone()
    return dict(row)


def activate_kill_switch(actor: dict, payload: dict) -> dict:
    if payload.get("killed") is not True:
        raise AiQaError("human_gate_required", "当前只允许停用，不允许通过接口重新开启", 409)
    reason = str(payload.get("reason") or "").strip()[:500]
    if not reason:
        raise AiQaError("validation_error", "停用原因不能为空")
    timestamp = now_iso()
    with get_connection() as conn:
        conn.execute("DELETE FROM ai_qa_runtime_control WHERE id = 'global'")
        conn.execute("INSERT INTO ai_qa_runtime_control (id, killed, reason, changed_by, changed_at) VALUES ('global', 1, ?, ?, ?)", (reason, actor["id"], timestamp))
        write_audit_log(conn, "ai_qa_kill_switch_activated", actor["id"], "ai_qa_runtime", "global", {"reason": reason, "participant_enabled_before": False})
        conn.commit()
    return {"killed": True, "reason": reason, "changed_by": actor["id"], "changed_at": timestamp, "reactivation_requires_human_gate": True}
