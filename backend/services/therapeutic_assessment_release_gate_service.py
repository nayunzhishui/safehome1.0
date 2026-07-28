"""Fail-closed production gate for collaborative therapeutic assessment."""

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
from services.therapeutic_assessment_service import (
    FORMAL_ROLES,
    REVIEW_ROLES,
    TherapeuticAssessmentError,
    _idempotency,
)


def _policy() -> dict:
    path = Path(current_app.config["CONTENT_DIR"]) / "therapeutic_assessment_release_gate_policy.json"
    return json.loads(path.read_text(encoding="utf-8"))


def _registry() -> tuple[dict, str]:
    path = Path(current_app.config["CONTENT_DIR"]).parent / "config" / "task37_38_registry.json"
    raw = path.read_bytes()
    return json.loads(raw.decode("utf-8")), hashlib.sha256(raw).hexdigest()


def _assert_formal(actor: dict) -> None:
    if str(actor.get("role") or "") not in FORMAL_ROLES:
        raise TherapeuticAssessmentError(
            "forbidden",
            "生产门禁只向正式研究角色开放。",
            403,
        )


def _evidence_types(policy: dict) -> set[str]:
    return {
        item
        for items in policy["required_evidence"].values()
        for item in items
    }


def _present_evidence(row: dict) -> dict:
    item = dict(row)
    item["qualifies_for_production"] = bool(
        item["status"] == "verified"
        and item["environment"] == "production"
        and item.get("verified_by")
        and item["verified_by"] != item["recorded_by"]
        and len(str(item["artifact_sha256"])) == 64
    )
    return item


def list_release_evidence(actor: dict) -> dict:
    _assert_formal(actor)
    with get_connection() as conn:
        items = [
            _present_evidence(item)
            for item in rows_to_dicts(
                conn.execute(
                    "SELECT * FROM therapeutic_assessment_release_evidence ORDER BY created_at, id"
                ).fetchall()
            )
        ]
        write_audit_log(
            conn,
            "therapeutic_assessment_release_evidence_viewed",
            str(actor["id"]),
            "therapeutic_assessment_release_gate",
            "evidence",
            {"count": len(items)},
        )
        conn.commit()
    return {
        "items": items,
        "count": len(items),
        "boundary_notice": _policy()["boundary_notice"],
    }


def record_release_evidence(
    actor: dict,
    payload: dict,
    idempotency_key: str,
) -> tuple[dict, int]:
    _assert_formal(actor)
    key = _idempotency(idempotency_key)
    policy = _policy()
    evidence_type = str(payload.get("evidence_type") or "").strip()
    artifact_ref = str(payload.get("artifact_ref") or "").strip()
    artifact_sha256 = str(payload.get("artifact_sha256") or "").strip().lower()
    notes = str(payload.get("notes") or "").strip()[:1000]
    if evidence_type not in _evidence_types(policy):
        raise TherapeuticAssessmentError("validation_error", "不支持的生产证据类型。", 422)
    if not artifact_ref or len(artifact_ref) > 500:
        raise TherapeuticAssessmentError("validation_error", "证据引用不能为空且不能超过500字。", 422)
    if len(artifact_sha256) != 64 or any(ch not in "0123456789abcdef" for ch in artifact_sha256):
        raise TherapeuticAssessmentError("validation_error", "证据必须提供64位SHA-256。", 422)
    timestamp = now_iso()
    environment = str(current_app.config.get("APP_ENV", "development")).lower()
    with get_connection() as conn:
        replay = conn.execute(
            "SELECT * FROM therapeutic_assessment_release_evidence WHERE recorded_by = ? AND idempotency_key = ?",
            (str(actor["id"]), key),
        ).fetchone()
        if replay is not None:
            item = row_to_dict(replay)
            if (
                item["evidence_type"] != evidence_type
                or item["artifact_sha256"] != artifact_sha256
            ):
                raise TherapeuticAssessmentError(
                    "idempotency_conflict",
                    "该提交标识已用于其它生产证据。",
                    409,
                )
            return _present_evidence(item), 200
        evidence_id = new_id("ta_release_evidence")
        conn.execute(
            """
            INSERT INTO therapeutic_assessment_release_evidence (
                id, evidence_type, artifact_ref, artifact_sha256, environment,
                status, recorded_by, notes, version, idempotency_key,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, 'pending', ?, ?, 1, ?, ?, ?)
            """,
            (
                evidence_id,
                evidence_type,
                artifact_ref,
                artifact_sha256,
                environment,
                str(actor["id"]),
                notes or None,
                key,
                timestamp,
                timestamp,
            ),
        )
        write_audit_log(
            conn,
            "therapeutic_assessment_release_evidence_recorded",
            str(actor["id"]),
            "therapeutic_assessment_release_evidence",
            evidence_id,
            {
                "evidence_type": evidence_type,
                "environment": environment,
                "artifact_sha256": artifact_sha256,
                "status": "pending",
            },
        )
        conn.commit()
        item = row_to_dict(
            conn.execute(
                "SELECT * FROM therapeutic_assessment_release_evidence WHERE id = ?",
                (evidence_id,),
            ).fetchone()
        )
    return _present_evidence(item), 201


def verify_release_evidence(
    actor: dict,
    evidence_id: str,
    payload: dict,
    idempotency_key: str,
) -> dict:
    if str(actor.get("role") or "") not in REVIEW_ROLES:
        raise TherapeuticAssessmentError("forbidden", "证据核验需要督导或管理员。", 403)
    key = _idempotency(idempotency_key)
    decision = str(payload.get("decision") or "").strip()
    expected_version = payload.get("expected_version")
    if decision not in {"verified", "rejected"} or not isinstance(expected_version, int):
        raise TherapeuticAssessmentError(
            "validation_error",
            "需要有效decision和expected_version。",
            422,
        )
    with get_connection() as conn:
        replay = conn.execute(
            """
            SELECT * FROM therapeutic_assessment_release_evidence
            WHERE verified_by = ? AND verification_idempotency_key = ?
            """,
            (str(actor["id"]), key),
        ).fetchone()
        if replay is not None:
            replay_item = row_to_dict(replay)
            if replay_item["id"] != evidence_id:
                raise TherapeuticAssessmentError(
                    "idempotency_conflict",
                    "该提交标识已用于其它证据核验。",
                    409,
                )
            return _present_evidence(replay_item)
        row = conn.execute(
            "SELECT * FROM therapeutic_assessment_release_evidence WHERE id = ?",
            (evidence_id,),
        ).fetchone()
        if row is None:
            raise TherapeuticAssessmentError("not_found", "没有找到生产证据。", 404)
        item = row_to_dict(row)
        if str(item["recorded_by"]) == str(actor["id"]):
            raise TherapeuticAssessmentError(
                "self_verification_forbidden",
                "证据记录人不能核验自己提交的材料。",
                403,
            )
        if int(item["version"]) != expected_version:
            raise TherapeuticAssessmentError("version_conflict", "证据版本已变化。", 409)
        timestamp = now_iso()
        cursor = conn.execute(
            """
            UPDATE therapeutic_assessment_release_evidence
            SET status = ?, verified_by = ?, verified_at = ?,
                verification_idempotency_key = ?,
                version = version + 1, updated_at = ?
            WHERE id = ? AND version = ?
            """,
            (
                decision,
                str(actor["id"]),
                timestamp,
                key,
                timestamp,
                evidence_id,
                expected_version,
            ),
        )
        if cursor.rowcount != 1:
            raise TherapeuticAssessmentError("version_conflict", "证据版本已变化。", 409)
        write_audit_log(
            conn,
            "therapeutic_assessment_release_evidence_verified",
            str(actor["id"]),
            "therapeutic_assessment_release_evidence",
            evidence_id,
            {
                "decision": decision,
                "environment": item["environment"],
                "idempotency_key": key,
            },
        )
        conn.commit()
        updated = row_to_dict(
            conn.execute(
                "SELECT * FROM therapeutic_assessment_release_evidence WHERE id = ?",
                (evidence_id,),
            ).fetchone()
        )
    return _present_evidence(updated)


def _evaluate() -> tuple[dict, str]:
    policy = _policy()
    registry, registry_hash = _registry()
    by_id = {item["id"]: item for item in registry["tasks"]}
    engineering_missing = [
        task_id
        for task_id in policy["engineering_tasks"]
        if not by_id.get(task_id, {}).get("engineering_complete")
    ]
    with get_connection() as conn:
        verified_rows = rows_to_dicts(
            conn.execute(
                """
                SELECT * FROM therapeutic_assessment_release_evidence
                WHERE status = 'verified' AND environment = 'production'
                  AND verified_by IS NOT NULL AND verified_by != recorded_by
                """
            ).fetchall()
        )
    verified_by_type = {
        item["evidence_type"]: item
        for item in verified_rows
        if len(str(item.get("artifact_sha256") or "")) == 64
    }
    checks: dict[str, dict] = {
        "engineering_content": {
            "passed": not engineering_missing,
            "missing": engineering_missing,
            "evidence_ids": [],
        }
    }
    for gate_name, required in policy["required_evidence"].items():
        missing = [item for item in required if item not in verified_by_type]
        checks[gate_name] = {
            "passed": not missing,
            "missing": missing,
            "evidence_ids": [
                verified_by_type[item]["id"]
                for item in required
                if item in verified_by_type
            ],
        }
    ordered = policy["gate_order"]
    overall = all(checks[name]["passed"] for name in ordered)
    return (
        {
            "policy_version": policy["version"],
            "status": "ready_for_owner_release" if overall else "blocked",
            "checks": checks,
            "engineering_ready": checks["engineering_content"]["passed"],
            "human_evidence_ready": checks["human_evidence"]["passed"],
            "workforce_ready": checks["workforce_duty"]["passed"],
            "privacy_recovery_ready": checks["privacy_recovery"]["passed"],
            "infrastructure_ready": checks["infrastructure_release"]["passed"],
            "production_release_approved": False,
            "temporary_showcase_counts_as_permission": False,
            "simulated_signoffs_counted": False,
            "boundary_notice": policy["boundary_notice"],
        },
        registry_hash,
    )


def release_gate_status(actor: dict) -> dict:
    _assert_formal(actor)
    result, registry_hash = _evaluate()
    with get_connection() as conn:
        latest = conn.execute(
            "SELECT * FROM therapeutic_assessment_release_gate_runs ORDER BY created_at DESC, id DESC LIMIT 1"
        ).fetchone()
        write_audit_log(
            conn,
            "therapeutic_assessment_release_gate_viewed",
            str(actor["id"]),
            "therapeutic_assessment_release_gate",
            "current",
            {"status": result["status"], "registry_hash": registry_hash},
        )
        conn.commit()
    result["registry_hash"] = registry_hash
    result["latest_run"] = row_to_dict(latest)
    return result


def evaluate_release_gate(actor: dict, idempotency_key: str) -> tuple[dict, int]:
    if str(actor.get("role") or "") not in REVIEW_ROLES:
        raise TherapeuticAssessmentError("forbidden", "生产门禁评估需要督导或管理员。", 403)
    key = _idempotency(idempotency_key)
    result, registry_hash = _evaluate()
    timestamp = now_iso()
    with get_connection() as conn:
        replay = conn.execute(
            "SELECT * FROM therapeutic_assessment_release_gate_runs WHERE evaluated_by = ? AND idempotency_key = ?",
            (str(actor["id"]), key),
        ).fetchone()
        if replay is not None:
            run = row_to_dict(replay)
            return {**result, "run": run, "already_processed": True}, 200
        run_id = new_id("ta_release_gate")
        conn.execute(
            """
            INSERT INTO therapeutic_assessment_release_gate_runs (
                id, policy_version, registry_hash, status, engineering_ready,
                human_evidence_ready, workforce_ready, privacy_recovery_ready,
                infrastructure_ready, production_release_approved,
                evaluated_by, idempotency_key, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?, ?)
            """,
            (
                run_id,
                result["policy_version"],
                registry_hash,
                result["status"],
                int(result["engineering_ready"]),
                int(result["human_evidence_ready"]),
                int(result["workforce_ready"]),
                int(result["privacy_recovery_ready"]),
                int(result["infrastructure_ready"]),
                str(actor["id"]),
                key,
                timestamp,
            ),
        )
        for gate_name in _policy()["gate_order"]:
            check = result["checks"][gate_name]
            conn.execute(
                """
                INSERT INTO therapeutic_assessment_release_gate_checks (
                    id, run_id, gate_name, decision, missing_json,
                    evidence_ids_json, checked_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    new_id("ta_release_check"),
                    run_id,
                    gate_name,
                    "passed" if check["passed"] else "blocked",
                    json_dumps(check["missing"]),
                    json_dumps(check["evidence_ids"]),
                    timestamp,
                ),
            )
        write_audit_log(
            conn,
            "therapeutic_assessment_release_gate_evaluated",
            str(actor["id"]),
            "therapeutic_assessment_release_gate",
            run_id,
            {
                "status": result["status"],
                "registry_hash": registry_hash,
                "production_release_approved": False,
            },
        )
        conn.commit()
        run = row_to_dict(
            conn.execute(
                "SELECT * FROM therapeutic_assessment_release_gate_runs WHERE id = ?",
                (run_id,),
            ).fetchone()
        )
    return {**result, "run": run, "already_processed": False}, 201
