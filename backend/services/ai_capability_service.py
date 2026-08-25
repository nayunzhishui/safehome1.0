"""Single fail-closed AI capability decision for UI, routes, services and providers."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass

from flask import current_app

from database import get_connection, new_id, now_iso
PARTICIPANT_ROLES = {"parent", "student"}
INTERNAL_ROLES = {"researcher", "supervisor", "admin"}


@dataclass(frozen=True)
class AiCapabilityDecision:
    enabled: bool
    environment: str
    audience: str
    operation: str
    provider: str
    real_provider_allowed: bool
    participant_entry_visible: bool
    data_mode: str
    reason_code: str
    policy_version: str
    response_origin: str
    response_origin_label: str

    def public(self) -> dict:
        return asdict(self)


def _read(name: str) -> dict:
    path = current_app.config["CONTENT_DIR"] / name
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"AI capability fact unavailable: {name}") from exc


def _facts() -> tuple[dict, bool]:
    policy = _read("ai_capability_policy.json")
    governance = _read("ai_qa_governance.json")
    release = _read("ai_qa_release_policy.json")
    participant = _read("ai_participant_use_case_policy.json")
    drift = not (
        policy.get("schema_version") == "safehome.ai-capability-policy.v1"
        and policy.get("production", {}).get("participant_enabled") is False
        and policy.get("production", {}).get("participant_entry_visible") is False
        and policy.get("production", {}).get("provider_calls_enabled") is False
        and policy.get("future_production_gate", {}).get("automatic_approval_allowed") is False
        and governance.get("participant_feature_enabled") is False
        and governance.get("engineering_controls", {}).get("participant_enabled") is False
        and release.get("participant_entry_enabled") is False
        and release.get("production_release_approved") is False
        and release.get("automatic_advance_allowed") is False
        and participant.get("production_runtime_enabled") is False
    )
    return policy, drift


def _runtime_killed() -> bool:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT killed FROM ai_qa_runtime_control WHERE id = 'global'"
        ).fetchone()
    return bool(row and row["killed"])


def _record(actor: dict | None, decision: AiCapabilityDecision) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO ai_capability_decisions
            (id, actor_id, actor_role, operation, environment, audience,
             enabled, provider, real_provider_allowed, reason_code,
             policy_version, data_mode, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                new_id("aicap"),
                str((actor or {}).get("id") or "") or None,
                str((actor or {}).get("role") or "anonymous"),
                decision.operation,
                decision.environment,
                decision.audience,
                int(decision.enabled),
                decision.provider,
                int(decision.real_provider_allowed),
                decision.reason_code,
                decision.policy_version,
                decision.data_mode,
                now_iso(),
            ),
        )
        conn.commit()


def resolve_ai_capability(
    actor: dict | None,
    operation: str,
    *,
    audit: bool = False,
) -> AiCapabilityDecision:
    policy, drift = _facts()
    environment = str(current_app.config.get("APP_ENV") or "development").lower()
    role = str((actor or {}).get("role") or "anonymous")
    audience = "participant" if role in PARTICIPANT_ROLES else "internal"
    provider = str(current_app.config.get("AI_QA_PROVIDER") or "fake").lower()
    killed = _runtime_killed()
    enabled = False
    real_allowed = False
    entry_visible = False
    data_mode = "none"
    reason = "ai_capability_disabled"

    if drift:
        reason = "ai_governance_drift"
    elif killed:
        reason = "ai_qa_killed"
    elif environment == "production":
        reason = str(policy["production"]["reason_code"])
    elif audience == "participant":
        if environment in {"development", "testing"} and provider == "fake" and bool(
            current_app.config.get("AI_QA_ENABLED")
        ):
            enabled = True
            entry_visible = True
            data_mode = str(policy["local"]["data_mode"])
            reason = "local_fake_participant_enabled"
        else:
            reason = "participant_ai_not_available_in_environment"
    elif role not in INTERNAL_ROLES:
        reason = "ai_role_not_allowed"
    elif environment not in {"development", "testing", "validation"}:
        reason = "ai_environment_not_allowed"
    elif not bool(current_app.config.get("AI_QA_SANDBOX_ENABLED")):
        reason = "ai_qa_sandbox_disabled"
    elif provider == "fake":
        enabled = True
        data_mode = (
            str(policy["validation"]["data_mode"])
            if environment == "validation"
            else str(policy["local"]["data_mode"])
        )
        reason = "controlled_fake_sandbox"
    elif environment != "validation":
        reason = "real_provider_validation_only"
    else:
        from services.ai_provider_governance_service import (
            get_runtime_provider_admission,
        )

        admission = get_runtime_provider_admission(provider)
        real_allowed = bool(
            current_app.config.get("AI_QA_REAL_PROVIDER_ENABLED")
            and admission.get("allowed")
            and int(current_app.config.get("AI_QA_DAILY_BUDGET_MICROS") or 0) > 0
        )
        enabled = real_allowed
        data_mode = str(policy["validation"]["data_mode"])
        reason = (
            "validation_real_provider_admitted"
            if enabled
            else "validation_real_provider_gate_blocked"
        )

    response_origin = "unavailable"
    response_label = str(policy["copy"]["unavailable_label"])
    if enabled and provider == "fake":
        response_origin = "synthetic_simulation"
        response_label = str(policy["copy"]["fake_origin_label"])
    elif enabled and real_allowed:
        response_origin = "controlled_external_provider"
        response_label = str(policy["copy"]["external_origin_label"])

    decision = AiCapabilityDecision(
        enabled=enabled,
        environment=environment,
        audience=audience,
        operation=str(operation),
        provider=provider,
        real_provider_allowed=real_allowed,
        participant_entry_visible=entry_visible,
        data_mode=data_mode,
        reason_code=reason,
        policy_version=str(policy["policy_version"]),
        response_origin=response_origin,
        response_origin_label=response_label,
    )
    if audit:
        _record(actor, decision)
    return decision


def capability_policy_summary() -> dict:
    policy, drift = _facts()
    return {
        "policy_version": policy["policy_version"],
        "governance_drift": drift,
        "future_production_gate": policy["future_production_gate"],
        "copy": policy["copy"],
    }
