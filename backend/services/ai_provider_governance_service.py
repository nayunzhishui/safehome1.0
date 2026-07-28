"""Fail-closed AI provider comparison and external contract-evidence ledger."""

from __future__ import annotations

import json
from pathlib import Path

from flask import current_app

from database import (
    get_connection,
    new_id,
    now_iso,
    row_to_dict,
    rows_to_dicts,
    write_audit_log,
)
from services.ai_qa_service import AiQaError


POLICY_SCHEMA = "safehome.ai-provider-selection-policy.v1"
EVIDENCE_DECISIONS = {"verified", "rejected"}
WRITE_ROLES = {"supervisor", "admin"}
SECRET_MARKERS = (
    "sk-",
    "api_key=",
    "apikey=",
    "authorization:",
    "bearer ",
)


def _policy() -> dict:
    path = Path(current_app.config["CONTENT_DIR"]) / "ai_provider_selection_policy.json"
    try:
        policy = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise AiQaError(
            "ai_provider_policy_unavailable",
            "AI供应商遴选策略不可用",
            503,
        ) from exc
    candidates = policy.get("candidates")
    if (
        policy.get("schema_version") != POLICY_SCHEMA
        or not isinstance(candidates, list)
        or not candidates
    ):
        raise AiQaError(
            "ai_provider_policy_invalid",
            "AI供应商遴选策略格式不兼容",
            503,
        )
    candidate_ids = [str(item.get("id") or "") for item in candidates]
    if (
        not all(candidate_ids)
        or len(candidate_ids) != len(set(candidate_ids))
        or not isinstance(policy.get("required_evidence"), list)
    ):
        raise AiQaError(
            "ai_provider_policy_invalid",
            "AI供应商候选或证据类型无效",
            503,
        )
    return policy


def _require_write_role(actor: dict) -> None:
    if str(actor.get("role") or "") not in WRITE_ROLES:
        raise AiQaError("forbidden", "供应商合同证据登记需要督导或管理员。", 403)


def _idempotency(value: str) -> str:
    key = str(value or "").strip()
    if not key or len(key) > 120:
        raise AiQaError(
            "idempotency_key_required",
            "必须提供不超过120字的Idempotency-Key。",
            422,
        )
    return key


def _contains_secret(value: str) -> bool:
    normalized = str(value or "").lower()
    return any(marker in normalized for marker in SECRET_MARKERS)


def _present_evidence(row: dict) -> dict:
    item = dict(row)
    item["qualifies_for_selection"] = bool(
        item["status"] == "verified"
        and item.get("verified_by")
        and item["verified_by"] != item["recorded_by"]
        and len(str(item.get("artifact_sha256") or "")) == 64
    )
    return item


def _verified_by_provider() -> dict[str, set[str]]:
    with get_connection() as conn:
        rows = rows_to_dicts(
            conn.execute(
                """
                SELECT * FROM ai_provider_contract_evidence
                WHERE status = 'verified'
                  AND verified_by IS NOT NULL
                  AND verified_by != recorded_by
                ORDER BY created_at, id
                """
            ).fetchall()
        )
    result: dict[str, set[str]] = {}
    for row in rows:
        if len(str(row.get("artifact_sha256") or "")) != 64:
            continue
        result.setdefault(str(row["provider_id"]), set()).add(
            str(row["evidence_type"])
        )
    return result


def get_provider_selection_summary() -> dict:
    policy = _policy()
    return {
        "policy_version": policy["policy_version"],
        "status": policy["status"],
        "selected_provider": policy["selected_provider"],
        "external_provider_enabled": False,
        "candidate_ids": sorted(str(item["id"]) for item in policy["candidates"]),
    }


def list_provider_candidates(actor: dict) -> dict:
    policy = _policy()
    verified = _verified_by_provider()
    required = set(str(item) for item in policy["required_evidence"])
    candidates = []
    for source in policy["candidates"]:
        item = dict(source)
        available = verified.get(str(item["id"]), set())
        item["verified_evidence"] = sorted(available)
        item["missing_evidence"] = sorted(required - available)
        item["production_eligible"] = bool(
            not item["missing_evidence"]
            and policy.get("selected_provider") == item["id"]
            and policy.get("external_provider_enabled") is True
        )
        candidates.append(item)
    with get_connection() as conn:
        write_audit_log(
            conn,
            "ai_provider_selection_viewed",
            str(actor["id"]),
            "ai_provider_selection",
            policy["policy_version"],
            {
                "candidate_ids": [item["id"] for item in candidates],
                "selected_provider": None,
                "external_provider_enabled": False,
                "raw_contracts_included": False,
                "secret_values_included": False,
            },
        )
        conn.commit()
    return {
        "policy_version": policy["policy_version"],
        "reviewed_at": policy["reviewed_at"],
        "status": policy["status"],
        "selected_provider": None,
        "external_provider_enabled": False,
        "selection_rule": policy["selection_rule"],
        "required_evidence": list(policy["required_evidence"]),
        "outbound_policy": policy["outbound_policy"],
        "candidates": candidates,
        "continuity_plans": policy["continuity_plans"],
        "boundary_notice": policy["boundary_notice"],
    }


def list_provider_evidence(actor: dict) -> dict:
    with get_connection() as conn:
        rows = rows_to_dicts(
            conn.execute(
                """
                SELECT * FROM ai_provider_contract_evidence
                ORDER BY created_at, id
                """
            ).fetchall()
        )
        write_audit_log(
            conn,
            "ai_provider_contract_evidence_viewed",
            str(actor["id"]),
            "ai_provider_contract_evidence",
            "all",
            {"count": len(rows), "artifact_contents_included": False},
        )
        conn.commit()
    return {
        "items": [_present_evidence(item) for item in rows],
        "count": len(rows),
        "boundary_notice": _policy()["boundary_notice"],
    }


def record_provider_evidence(
    actor: dict,
    payload: dict,
    idempotency_key: str,
) -> tuple[dict, int]:
    _require_write_role(actor)
    key = _idempotency(idempotency_key)
    policy = _policy()
    provider_id = str(payload.get("provider_id") or "").strip()
    evidence_type = str(payload.get("evidence_type") or "").strip()
    artifact_ref = str(payload.get("artifact_ref") or "").strip()
    artifact_sha256 = str(payload.get("artifact_sha256") or "").strip().lower()
    notes = str(payload.get("notes") or "").strip()[:1000]
    if provider_id not in {str(item["id"]) for item in policy["candidates"]}:
        raise AiQaError("validation_error", "供应商不在候选清单中。", 422)
    if evidence_type not in set(policy["required_evidence"]):
        raise AiQaError("validation_error", "不支持的供应商证据类型。", 422)
    if not artifact_ref or len(artifact_ref) > 500:
        raise AiQaError("validation_error", "证据引用不能为空且不能超过500字。", 422)
    if _contains_secret(artifact_ref) or _contains_secret(notes):
        raise AiQaError(
            "secret_material_rejected",
            "证据元数据不得包含密钥或授权头。",
            422,
        )
    if len(artifact_sha256) != 64 or any(
        char not in "0123456789abcdef" for char in artifact_sha256
    ):
        raise AiQaError("validation_error", "证据必须提供64位SHA-256。", 422)
    timestamp = now_iso()
    actor_id = str(actor["id"])
    with get_connection() as conn:
        replay = conn.execute(
            """
            SELECT * FROM ai_provider_contract_evidence
            WHERE recorded_by = ? AND idempotency_key = ?
            """,
            (actor_id, key),
        ).fetchone()
        if replay is not None:
            item = row_to_dict(replay)
            if (
                item["provider_id"] != provider_id
                or item["evidence_type"] != evidence_type
                or item["artifact_sha256"] != artifact_sha256
            ):
                raise AiQaError(
                    "idempotency_conflict",
                    "该提交标识已用于不同供应商证据。",
                    409,
                )
            return _present_evidence(item), 200
        evidence_id = new_id("ai_provider_evidence")
        conn.execute(
            """
            INSERT INTO ai_provider_contract_evidence (
                id, provider_id, evidence_type, artifact_ref, artifact_sha256,
                status, recorded_by, notes, version, idempotency_key,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, 'pending', ?, ?, 1, ?, ?, ?)
            """,
            (
                evidence_id,
                provider_id,
                evidence_type,
                artifact_ref,
                artifact_sha256,
                actor_id,
                notes or None,
                key,
                timestamp,
                timestamp,
            ),
        )
        write_audit_log(
            conn,
            "ai_provider_contract_evidence_recorded",
            actor_id,
            "ai_provider_contract_evidence",
            evidence_id,
            {
                "provider_id": provider_id,
                "evidence_type": evidence_type,
                "artifact_sha256": artifact_sha256,
                "artifact_contents_logged": False,
                "secret_values_logged": False,
            },
        )
        conn.commit()
        item = row_to_dict(
            conn.execute(
                "SELECT * FROM ai_provider_contract_evidence WHERE id = ?",
                (evidence_id,),
            ).fetchone()
        )
    return _present_evidence(item), 201


def verify_provider_evidence(
    actor: dict,
    evidence_id: str,
    payload: dict,
    idempotency_key: str,
) -> dict:
    _require_write_role(actor)
    key = _idempotency(idempotency_key)
    decision = str(payload.get("decision") or "").strip()
    expected_version = payload.get("expected_version")
    if decision not in EVIDENCE_DECISIONS:
        raise AiQaError("validation_error", "复核结论必须为verified或rejected。", 422)
    if (
        isinstance(expected_version, bool)
        or not isinstance(expected_version, int)
        or expected_version < 1
    ):
        raise AiQaError("validation_error", "expected_version必须为正整数。", 422)
    actor_id = str(actor["id"])
    timestamp = now_iso()
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM ai_provider_contract_evidence WHERE id = ?",
            (evidence_id,),
        ).fetchone()
        if row is None:
            raise AiQaError("not_found", "供应商证据不存在。", 404)
        item = row_to_dict(row)
        if item["recorded_by"] == actor_id:
            raise AiQaError(
                "independent_review_required",
                "供应商证据必须由不同人员独立复核。",
                409,
            )
        if (
            item.get("verification_idempotency_key") == key
            and item.get("verified_by") == actor_id
        ):
            return _present_evidence(item)
        if item["status"] != "pending":
            raise AiQaError("evidence_already_reviewed", "供应商证据已经复核。", 409)
        cursor = conn.execute(
            """
            UPDATE ai_provider_contract_evidence
            SET status = ?, verified_by = ?, verified_at = ?,
                verification_idempotency_key = ?, version = version + 1,
                updated_at = ?
            WHERE id = ? AND status = 'pending' AND version = ?
            """,
            (
                decision,
                actor_id,
                timestamp,
                key,
                timestamp,
                evidence_id,
                expected_version,
            ),
        )
        if cursor.rowcount != 1:
            raise AiQaError("version_conflict", "供应商证据版本已变化。", 409)
        write_audit_log(
            conn,
            "ai_provider_contract_evidence_verified",
            actor_id,
            "ai_provider_contract_evidence",
            evidence_id,
            {
                "provider_id": item["provider_id"],
                "evidence_type": item["evidence_type"],
                "decision": decision,
                "artifact_contents_logged": False,
            },
        )
        conn.commit()
        updated = row_to_dict(
            conn.execute(
                "SELECT * FROM ai_provider_contract_evidence WHERE id = ?",
                (evidence_id,),
            ).fetchone()
        )
    return _present_evidence(updated)
