"""Fail-closed staged release controller for the AI research capability."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from flask import current_app

from database import (
    get_connection,
    json_dumps,
    json_loads,
    new_id,
    now_iso,
    row_to_dict,
    rows_to_dicts,
    write_audit_log,
)


POLICY_SCHEMA = "safehome.ai-qa-release-policy.v1"
STATE_KEY = "ai_qa"


class AiQaReleaseError(ValueError):
    def __init__(
        self,
        code: str,
        message: str,
        status: int = 400,
        details: dict | None = None,
    ):
        super().__init__(message)
        self.code = code
        self.status = status
        self.details = details or {}


def _policy() -> dict:
    path = Path(current_app.config["CONTENT_DIR"]) / "ai_qa_release_policy.json"
    try:
        policy = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise AiQaReleaseError(
            "ai_release_policy_unavailable",
            "AI分阶段发布策略不可用",
            503,
        ) from exc
    stages = policy.get("stages")
    if (
        policy.get("schema_version") != POLICY_SCHEMA
        or not isinstance(stages, list)
        or len(stages) != 6
    ):
        raise AiQaReleaseError(
            "ai_release_policy_invalid",
            "AI分阶段发布策略格式不兼容",
            503,
        )
    expected = list(range(len(stages)))
    if [int(item.get("order", -1)) for item in stages] != expected:
        raise AiQaReleaseError(
            "ai_release_policy_invalid",
            "AI发布阶段顺序不连续",
            503,
        )
    return policy


def _ensure_state(conn) -> dict:
    row = conn.execute(
        "SELECT * FROM ai_qa_release_state WHERE singleton_key = ?",
        (STATE_KEY,),
    ).fetchone()
    if not row:
        timestamp = now_iso()
        conn.execute(
            """
            INSERT INTO ai_qa_release_state (
                singleton_key, current_stage, version, changed_by,
                changed_at, production_release_approved
            ) VALUES (?, 'local_fake', 1, 'system_bootstrap', ?, 0)
            """,
            (STATE_KEY, timestamp),
        )
        conn.commit()
        row = conn.execute(
            "SELECT * FROM ai_qa_release_state WHERE singleton_key = ?",
            (STATE_KEY,),
        ).fetchone()
    return row_to_dict(row)


def _stage(policy: dict, stage_id: str) -> dict:
    for item in policy["stages"]:
        if item["id"] == stage_id:
            return item
    raise AiQaReleaseError(
        "release_stage_invalid", "未知AI发布阶段", 400
    )


def _gate_results(stage: dict) -> dict[str, bool]:
    required = list(stage.get("required_gates") or [])
    results = {gate: False for gate in required}
    if not required:
        return results
    with get_connection() as conn:
        if "verified_provider_governance" in results:
            policy_path = (
                Path(current_app.config["CONTENT_DIR"])
                / "ai_provider_selection_policy.json"
            )
            selection = json.loads(policy_path.read_text(encoding="utf-8"))
            selected = str(selection.get("selected_provider") or "")
            required_evidence = set(selection.get("required_evidence") or [])
            verified = {
                row["evidence_type"]
                for row in conn.execute(
                    """
                    SELECT evidence_type
                    FROM ai_provider_contract_evidence
                    WHERE provider_id = ? AND status = 'verified'
                    """,
                    (selected,),
                ).fetchall()
            }
            outbound = selection.get("outbound_policy") or {}
            results["verified_provider_governance"] = bool(
                selected
                and selection.get("external_provider_enabled") is True
                and outbound.get("activated") is True
                and required_evidence.issubset(verified)
            )
        if "approved_synthetic_quality_run" in results:
            row = conn.execute(
                """
                SELECT r.id
                FROM ai_qa_evaluation_runs r
                JOIN ai_qa_evaluation_reviews v ON v.run_id = r.id
                WHERE r.status IN ('passed', 'engineering_passed')
                  AND v.decision = 'approved_for_next_internal_stage'
                ORDER BY r.created_at DESC
                LIMIT 1
                """
            ).fetchone()
            results["approved_synthetic_quality_run"] = bool(row)
        if "review_workbench_ready" in results:
            results["review_workbench_ready"] = True
        if "draft_review_separation" in results:
            results["draft_review_separation"] = True
    return results


def _status_payload(policy: dict, state: dict) -> dict:
    current = _stage(policy, state["current_stage"])
    next_stage = next(
        (
            item
            for item in policy["stages"]
            if item["order"] == current["order"] + 1
        ),
        None,
    )
    gate_results = _gate_results(next_stage) if next_stage else {}
    blockers = [key for key, passed in gate_results.items() if not passed]
    return {
        "policy_version": policy["policy_version"],
        "current_stage": current["id"],
        "current_order": current["order"],
        "state_version": int(state["version"]),
        "next_stage": next_stage["id"] if next_stage else None,
        "next_stage_blockers": blockers,
        "stages": policy["stages"],
        "automatic_advance_allowed": False,
        "participant_entry_enabled": bool(
            current["id"] == "restricted_participant_evaluation"
            and state["production_release_approved"]
        ),
        "production_release_approved": bool(
            state["production_release_approved"]
        ),
        "simulated_signoffs_counted": False,
        "core_services_unaffected": policy["core_services_unaffected"],
    }


def get_release_plan_summary() -> dict:
    policy = _policy()
    with get_connection() as conn:
        state = _ensure_state(conn)
    return _status_payload(policy, state)


def release_status(actor: dict) -> dict:
    result = get_release_plan_summary()
    with get_connection() as conn:
        result["recent_events"] = rows_to_dicts(
            conn.execute(
                """
                SELECT id, action, from_stage, to_stage, trigger_code,
                       state_version, actor_id, created_at
                FROM ai_qa_release_events
                ORDER BY created_at DESC LIMIT 20
                """
            ).fetchall()
        )
        write_audit_log(
            conn,
            "ai_qa_release_status_read",
            actor["id"],
            "ai_qa_release",
            STATE_KEY,
            {
                "current_stage": result["current_stage"],
                "production_release_approved": False,
            },
        )
        conn.commit()
    return result


def _validated_request(
    actor: dict, payload: dict, idempotency_key: str
) -> tuple[str, str]:
    key = str(idempotency_key or "").strip()
    if not key or len(key) > 128:
        raise AiQaReleaseError(
            "idempotency_key_required",
            "分阶段发布操作必须提供有效幂等键",
            400,
        )
    if payload.get("simulated_agent") is True:
        raise AiQaReleaseError(
            "simulated_release_signoff_forbidden",
            "模拟Agent不能作为发布签字",
            409,
        )
    request_hash = hashlib.sha256(
        json_dumps(payload).encode("utf-8")
    ).hexdigest()
    with get_connection() as conn:
        existing = conn.execute(
            """
            SELECT request_hash FROM ai_qa_release_events
            WHERE actor_id = ? AND idempotency_key = ?
            """,
            (actor["id"], key),
        ).fetchone()
    if existing and existing["request_hash"] != request_hash:
        raise AiQaReleaseError(
            "idempotency_conflict", "幂等键已用于其他发布请求", 409
        )
    return key, request_hash


def transition_release(
    actor: dict, payload: dict, idempotency_key: str
) -> dict:
    policy = _policy()
    key, request_hash = _validated_request(actor, payload, idempotency_key)
    target_id = str(payload.get("target_stage") or "").strip()
    target = _stage(policy, target_id)
    expected_version = int(payload.get("expected_version") or 0)
    with get_connection() as conn:
        existing = conn.execute(
            """
            SELECT * FROM ai_qa_release_events
            WHERE actor_id = ? AND idempotency_key = ?
            """,
            (actor["id"], key),
        ).fetchone()
        if existing:
            state = _ensure_state(conn)
            result = _status_payload(policy, state)
            result["idempotent_replay"] = True
            return result
        state = _ensure_state(conn)
        current = _stage(policy, state["current_stage"])
        if target["order"] != current["order"] + 1:
            raise AiQaReleaseError(
                "release_stage_order_invalid",
                "AI发布阶段只能按顺序前进",
                409,
            )
        if expected_version != int(state["version"]):
            raise AiQaReleaseError(
                "release_version_conflict",
                "AI发布状态已更新，请刷新后重试",
                409,
                {"current_version": int(state["version"])},
            )
        gate_results = _gate_results(target)
        blockers = [
            key for key, passed in gate_results.items() if not passed
        ]
        if blockers:
            raise AiQaReleaseError(
                "release_stage_blocked",
                "下一发布阶段仍有未通过门禁",
                409,
                {"blockers": blockers},
            )
        if target["id"] == "restricted_participant_evaluation":
            raise AiQaReleaseError(
                "human_release_approval_required",
                "受限参与者问答必须完成任务38和真人发布批准",
                409,
            )
        timestamp = now_iso()
        updated = conn.execute(
            """
            UPDATE ai_qa_release_state
            SET current_stage = ?, version = version + 1,
                changed_by = ?, changed_at = ?
            WHERE singleton_key = ? AND version = ?
              AND production_release_approved = 0
            """,
            (
                target["id"],
                actor["id"],
                timestamp,
                STATE_KEY,
                expected_version,
            ),
        )
        if updated.rowcount != 1:
            raise AiQaReleaseError(
                "release_version_conflict",
                "AI发布状态已更新，请刷新后重试",
                409,
            )
        event_id = new_id("aiqre")
        conn.execute(
            """
            INSERT INTO ai_qa_release_events (
                id, action, from_stage, to_stage, trigger_code,
                reason, evidence_json, idempotency_key, request_hash,
                state_version, actor_id, created_at
            ) VALUES (?, 'advance', ?, ?, NULL, ?, '[]', ?, ?, ?, ?, ?)
            """,
            (
                event_id,
                current["id"],
                target["id"],
                str(payload.get("reason") or "")[:500] or None,
                key,
                request_hash,
                expected_version + 1,
                actor["id"],
                timestamp,
            ),
        )
        write_audit_log(
            conn,
            "ai_qa_release_stage_advanced",
            actor["id"],
            "ai_qa_release",
            event_id,
            {
                "from_stage": current["id"],
                "to_stage": target["id"],
                "production_release_approved": False,
            },
        )
        conn.commit()
        state = _ensure_state(conn)
    result = _status_payload(policy, state)
    result["idempotent_replay"] = False
    return result


def rollback_release(
    actor: dict, payload: dict, idempotency_key: str
) -> dict:
    policy = _policy()
    key, request_hash = _validated_request(actor, payload, idempotency_key)
    trigger = str(payload.get("trigger") or "").strip()
    if trigger not in set(policy["immediate_rollback_triggers"]):
        raise AiQaReleaseError(
            "rollback_trigger_invalid", "回退原因不在允许清单", 400
        )
    target = _stage(
        policy, str(payload.get("target_stage") or "local_fake").strip()
    )
    expected_version = int(payload.get("expected_version") or 0)
    reason = str(payload.get("reason") or "").strip()
    if not reason:
        raise AiQaReleaseError(
            "rollback_reason_required", "回退必须填写原因", 400
        )
    with get_connection() as conn:
        existing = conn.execute(
            """
            SELECT * FROM ai_qa_release_events
            WHERE actor_id = ? AND idempotency_key = ?
            """,
            (actor["id"], key),
        ).fetchone()
        state = _ensure_state(conn)
        if existing:
            result = _status_payload(policy, state)
            result["idempotent_replay"] = True
            result["kill_switch_activated"] = True
            return result
        current = _stage(policy, state["current_stage"])
        if target["order"] >= current["order"]:
            raise AiQaReleaseError(
                "rollback_target_invalid",
                "回退目标必须早于当前阶段",
                409,
            )
        if expected_version != int(state["version"]):
            raise AiQaReleaseError(
                "release_version_conflict",
                "AI发布状态已更新，请刷新后重试",
                409,
                {"current_version": int(state["version"])},
            )
        timestamp = now_iso()
        conn.execute(
            """
            UPDATE ai_qa_release_state
            SET current_stage = ?, version = version + 1,
                changed_by = ?, changed_at = ?,
                production_release_approved = 0
            WHERE singleton_key = ? AND version = ?
            """,
            (
                target["id"],
                actor["id"],
                timestamp,
                STATE_KEY,
                expected_version,
            ),
        )
        conn.execute(
            "DELETE FROM ai_qa_runtime_control WHERE id = 'global'"
        )
        conn.execute(
            """
            INSERT INTO ai_qa_runtime_control (
                id, killed, reason, changed_by, changed_at
            ) VALUES ('global', 1, ?, ?, ?)
            """,
            (f"release_rollback:{trigger}", actor["id"], timestamp),
        )
        event_id = new_id("aiqre")
        conn.execute(
            """
            INSERT INTO ai_qa_release_events (
                id, action, from_stage, to_stage, trigger_code,
                reason, evidence_json, idempotency_key, request_hash,
                state_version, actor_id, created_at
            ) VALUES (?, 'rollback', ?, ?, ?, ?, '[]', ?, ?, ?, ?, ?)
            """,
            (
                event_id,
                current["id"],
                target["id"],
                trigger,
                reason[:500],
                key,
                request_hash,
                expected_version + 1,
                actor["id"],
                timestamp,
            ),
        )
        write_audit_log(
            conn,
            "ai_qa_release_rolled_back",
            actor["id"],
            "ai_qa_release",
            event_id,
            {
                "trigger": trigger,
                "from_stage": current["id"],
                "to_stage": target["id"],
                "kill_switch_activated": True,
            },
        )
        conn.commit()
        state = _ensure_state(conn)
    result = _status_payload(policy, state)
    result["kill_switch_activated"] = True
    result["idempotent_replay"] = False
    return result


def create_release_evidence_package(actor: dict) -> dict:
    policy = _policy()
    status = get_release_plan_summary()
    content_dir = Path(current_app.config["CONTENT_DIR"])
    artifact_files = [
        "ai_qa_release_policy.json",
        "ai_qa_runtime_policy.json",
        "ai_qa_continuous_quality_policy.json",
        "ai_provider_selection_policy.json",
    ]
    fingerprints = {}
    for name in artifact_files:
        path = content_dir / name
        fingerprints[name] = hashlib.sha256(path.read_bytes()).hexdigest()
    payload = {
        "schema_version": POLICY_SCHEMA,
        "policy_version": policy["policy_version"],
        "current_stage": status["current_stage"],
        "state_version": status["state_version"],
        "next_stage_blockers": status["next_stage_blockers"],
        "artifact_fingerprints": fingerprints,
        "automatic_advance_allowed": False,
        "participant_entry_enabled": False,
        "production_release_approved": False,
        "simulated_signoffs_counted": False,
        "core_services_unaffected": policy["core_services_unaffected"],
    }
    artifact_sha256 = hashlib.sha256(
        json_dumps(payload).encode("utf-8")
    ).hexdigest()
    package_id = new_id("aiqrp")
    timestamp = now_iso()
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO ai_qa_release_evidence_packages (
                id, current_stage, policy_version, payload_json,
                artifact_sha256, generated_by, generated_at,
                production_release_approved
            ) VALUES (?, ?, ?, ?, ?, ?, ?, 0)
            """,
            (
                package_id,
                status["current_stage"],
                policy["policy_version"],
                json_dumps(payload),
                artifact_sha256,
                actor["id"],
                timestamp,
            ),
        )
        write_audit_log(
            conn,
            "ai_qa_release_evidence_generated",
            actor["id"],
            "ai_qa_release_evidence",
            package_id,
            {
                "artifact_sha256": artifact_sha256,
                "production_release_approved": False,
                "simulated_signoffs_counted": False,
            },
        )
        conn.commit()
    return {
        "id": package_id,
        **payload,
        "artifact_sha256": artifact_sha256,
        "generated_by": actor["id"],
        "generated_at": timestamp,
    }
