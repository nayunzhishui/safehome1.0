"""Unified fail-closed stop, evidence, recovery and rollback controls for T38-F24."""

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


OPEN_STATUSES = {"open", "recovery_pending"}


def _policy() -> dict:
    path = (
        Path(current_app.config["CONTENT_DIR"])
        / "therapeutic_assessment_stop_recovery_policy.json"
    )
    return json.loads(path.read_text(encoding="utf-8"))


def _trigger_map(policy: dict) -> dict[str, dict]:
    return {item["id"]: item for item in policy["immediate_pause_triggers"]}


def _assert_formal(actor: dict) -> None:
    if str(actor.get("role") or "") not in FORMAL_ROLES:
        raise TherapeuticAssessmentError(
            "forbidden",
            "停止与恢复内部账本只向正式研究角色开放。",
            403,
        )


def _assert_reviewer(actor: dict) -> None:
    if str(actor.get("role") or "") not in REVIEW_ROLES:
        raise TherapeuticAssessmentError(
            "forbidden",
            "证据核验和恢复需要督导或管理员。",
            403,
        )


def _runtime(conn) -> dict:
    row = conn.execute(
        "SELECT * FROM therapeutic_assessment_runtime_control WHERE id = 'global'"
    ).fetchone()
    if row is None:
        timestamp = now_iso()
        conn.execute(
            """
            INSERT INTO therapeutic_assessment_runtime_control
            (id, killed, reason, changed_by, changed_at)
            VALUES ('global', 0, NULL, 'system', ?)
            """,
            (timestamp,),
        )
        row = conn.execute(
            "SELECT * FROM therapeutic_assessment_runtime_control WHERE id = 'global'"
        ).fetchone()
    return row_to_dict(row)


def _present_incident(item: dict) -> dict:
    result = dict(item)
    result["scopes"] = json_loads(result.pop("scope_json", None), [])
    result["reason_text_stored"] = False
    return result


def stop_recovery_status(actor: dict) -> dict:
    policy = _policy()
    formal = str(actor.get("role") or "") in FORMAL_ROLES
    with get_connection() as conn:
        runtime = _runtime(conn)
        result = {
            "ordinary_flow_enabled": not bool(runtime["killed"]),
            "participant_message": (
                policy["pause_behavior"]["participant_message"]
                if runtime["killed"]
                else "普通流程当前可用；需要真人处理的内容仍由人工负责。"
            ),
            "reactivation_requires_all_human_gates": True,
            "internal_reason_exposed": False,
        }
        if formal:
            incidents = [
                _present_incident(item)
                for item in rows_to_dicts(
                    conn.execute(
                        """
                        SELECT * FROM therapeutic_assessment_stop_incidents
                        ORDER BY created_at DESC, id DESC
                        """
                    ).fetchall()
                )
            ]
            result.update(
                {
                    "policy_version": policy["version"],
                    "runtime_reason": runtime.get("reason"),
                    "incidents": incidents,
                    "recovery_gates": policy["recovery_gates"],
                    "rollback_matrix": policy["rollback_matrix"],
                    "production_release_approved": False,
                    "temporary_showcase_counts_as_recovery": False,
                }
            )
        write_audit_log(
            conn,
            "therapeutic_assessment_stop_recovery_status_viewed",
            str(actor["id"]),
            "therapeutic_assessment_runtime",
            "global",
            {"formal_view": formal, "ordinary_flow_enabled": result["ordinary_flow_enabled"]},
        )
        conn.commit()
    return result


def report_stop_incident(
    actor: dict,
    payload: dict,
    idempotency_key: str,
) -> tuple[dict, int]:
    _assert_formal(actor)
    key = _idempotency(idempotency_key)
    policy = _policy()
    trigger_code = str(payload.get("trigger_code") or "").strip()
    trigger = _trigger_map(policy).get(trigger_code)
    if trigger is None:
        raise TherapeuticAssessmentError(
            "validation_error", "不支持的立即暂停条件。", 422
        )
    reason = str(payload.get("reason_summary") or "").strip()
    if not reason or len(reason) > 2000:
        raise TherapeuticAssessmentError(
            "validation_error", "需要不超过2000字的内部原因摘要。", 422
        )
    scopes = payload.get("scopes")
    if scopes is None:
        scopes = trigger["default_scopes"]
    if (
        not isinstance(scopes, list)
        or not scopes
        or len(scopes) > 20
        or any(not isinstance(item, str) or not item.strip() for item in scopes)
    ):
        raise TherapeuticAssessmentError(
            "validation_error", "暂停范围必须是有效字符串列表。", 422
        )
    actor_id = str(actor["id"])
    reason_digest = hashlib.sha256(reason.encode("utf-8")).hexdigest()
    normalized_scopes = sorted(set(item.strip() for item in scopes))
    timestamp = now_iso()
    with get_connection() as conn:
        replay = conn.execute(
            """
            SELECT * FROM therapeutic_assessment_stop_incidents
            WHERE detected_by = ? AND idempotency_key = ?
            """,
            (actor_id, key),
        ).fetchone()
        if replay is not None:
            item = row_to_dict(replay)
            if (
                item["trigger_code"] != trigger_code
                or item["reason_digest"] != reason_digest
                or json_loads(item.get("scope_json"), []) != normalized_scopes
            ):
                raise TherapeuticAssessmentError(
                    "idempotency_conflict",
                    "该提交标识已用于其它停止事件。",
                    409,
                )
            return _present_incident(item), 200
        incident_id = new_id("ta_stop")
        conn.execute(
            """
            INSERT INTO therapeutic_assessment_stop_incidents (
                id, trigger_code, severity, scope_json, status, reason_digest,
                detected_by, version, idempotency_key, created_at, updated_at
            ) VALUES (?, ?, ?, ?, 'open', ?, ?, 1, ?, ?, ?)
            """,
            (
                incident_id,
                trigger_code,
                trigger["severity"],
                json_dumps(normalized_scopes),
                reason_digest,
                actor_id,
                key,
                timestamp,
                timestamp,
            ),
        )
        _runtime(conn)
        conn.execute(
            """
            UPDATE therapeutic_assessment_runtime_control
            SET killed = 1, reason = ?, changed_by = ?, changed_at = ?
            WHERE id = 'global'
            """,
            (trigger_code, actor_id, timestamp),
        )
        write_audit_log(
            conn,
            "therapeutic_assessment_stop_incident_reported",
            actor_id,
            "therapeutic_assessment_stop_incident",
            incident_id,
            {
                "trigger_code": trigger_code,
                "severity": trigger["severity"],
                "scopes": normalized_scopes,
                "reason_digest": reason_digest,
                "raw_reason_stored": False,
            },
        )
        conn.commit()
        item = row_to_dict(
            conn.execute(
                "SELECT * FROM therapeutic_assessment_stop_incidents WHERE id = ?",
                (incident_id,),
            ).fetchone()
        )
    return _present_incident(item), 201


def record_recovery_evidence(
    actor: dict,
    incident_id: str,
    payload: dict,
    idempotency_key: str,
) -> tuple[dict, int]:
    _assert_formal(actor)
    key = _idempotency(idempotency_key)
    policy = _policy()
    evidence_type = str(payload.get("evidence_type") or "").strip()
    artifact_ref = str(payload.get("artifact_ref") or "").strip()
    artifact_sha256 = str(payload.get("artifact_sha256") or "").strip().lower()
    if evidence_type not in set(policy["recovery_gates"]):
        raise TherapeuticAssessmentError(
            "validation_error", "不支持的恢复证据类型。", 422
        )
    if not artifact_ref or len(artifact_ref) > 500:
        raise TherapeuticAssessmentError(
            "validation_error", "证据引用不能为空且不能超过500字。", 422
        )
    if len(artifact_sha256) != 64 or any(
        char not in "0123456789abcdef" for char in artifact_sha256
    ):
        raise TherapeuticAssessmentError(
            "validation_error", "恢复证据必须提供64位SHA-256。", 422
        )
    actor_id = str(actor["id"])
    timestamp = now_iso()
    with get_connection() as conn:
        incident = conn.execute(
            "SELECT * FROM therapeutic_assessment_stop_incidents WHERE id = ?",
            (incident_id,),
        ).fetchone()
        if incident is None:
            raise TherapeuticAssessmentError(
                "not_found", "没有找到停止事件。", 404
            )
        if incident["status"] not in OPEN_STATUSES:
            raise TherapeuticAssessmentError(
                "incident_closed", "已恢复的事件不能追加证据。", 409
            )
        replay = conn.execute(
            """
            SELECT * FROM therapeutic_assessment_recovery_evidence
            WHERE recorded_by = ? AND idempotency_key = ?
            """,
            (actor_id, key),
        ).fetchone()
        if replay is not None:
            item = row_to_dict(replay)
            if (
                item["incident_id"] != incident_id
                or item["evidence_type"] != evidence_type
                or item["artifact_ref"] != artifact_ref
                or item["artifact_sha256"] != artifact_sha256
            ):
                raise TherapeuticAssessmentError(
                    "idempotency_conflict",
                    "该提交标识已用于其它恢复证据。",
                    409,
                )
            return item, 200
        evidence_id = new_id("ta_recovery")
        conn.execute(
            """
            INSERT INTO therapeutic_assessment_recovery_evidence (
                id, incident_id, evidence_type, artifact_ref, artifact_sha256,
                status, recorded_by, version, idempotency_key, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, 'pending', ?, 1, ?, ?, ?)
            """,
            (
                evidence_id,
                incident_id,
                evidence_type,
                artifact_ref,
                artifact_sha256,
                actor_id,
                key,
                timestamp,
                timestamp,
            ),
        )
        conn.execute(
            """
            UPDATE therapeutic_assessment_stop_incidents
            SET status = 'recovery_pending', updated_at = ?
            WHERE id = ? AND status = 'open'
            """,
            (timestamp, incident_id),
        )
        write_audit_log(
            conn,
            "therapeutic_assessment_recovery_evidence_recorded",
            actor_id,
            "therapeutic_assessment_stop_incident",
            incident_id,
            {
                "evidence_id": evidence_id,
                "evidence_type": evidence_type,
                "artifact_sha256": artifact_sha256,
            },
        )
        conn.commit()
        item = row_to_dict(
            conn.execute(
                "SELECT * FROM therapeutic_assessment_recovery_evidence WHERE id = ?",
                (evidence_id,),
            ).fetchone()
        )
    return item, 201


def verify_recovery_evidence(
    actor: dict,
    evidence_id: str,
    payload: dict,
    idempotency_key: str,
) -> dict:
    _assert_reviewer(actor)
    key = _idempotency(idempotency_key)
    decision = str(payload.get("decision") or "").strip()
    expected_version = payload.get("expected_version")
    if decision not in {"verified", "rejected"} or not isinstance(
        expected_version, int
    ):
        raise TherapeuticAssessmentError(
            "validation_error",
            "需要有效decision和expected_version。",
            422,
        )
    actor_id = str(actor["id"])
    with get_connection() as conn:
        replay = conn.execute(
            """
            SELECT * FROM therapeutic_assessment_recovery_evidence
            WHERE verified_by = ? AND verification_idempotency_key = ?
            """,
            (actor_id, key),
        ).fetchone()
        if replay is not None:
            if replay["id"] != evidence_id:
                raise TherapeuticAssessmentError(
                    "idempotency_conflict",
                    "该提交标识已用于其它证据核验。",
                    409,
                )
            return row_to_dict(replay)
        row = conn.execute(
            "SELECT * FROM therapeutic_assessment_recovery_evidence WHERE id = ?",
            (evidence_id,),
        ).fetchone()
        if row is None:
            raise TherapeuticAssessmentError(
                "not_found", "没有找到恢复证据。", 404
            )
        if row["status"] != "pending":
            raise TherapeuticAssessmentError(
                "evidence_already_reviewed",
                "该恢复证据已经核验；如需更正请新增证据。",
                409,
            )
        if row["recorded_by"] == actor_id:
            raise TherapeuticAssessmentError(
                "self_verification_forbidden",
                "证据记录人不能核验自己的证据。",
                403,
            )
        if int(row["version"]) != expected_version:
            raise TherapeuticAssessmentError(
                "version_conflict", "证据版本已变化。", 409
            )
        timestamp = now_iso()
        updated = conn.execute(
            """
            UPDATE therapeutic_assessment_recovery_evidence
            SET status = ?, verified_by = ?, verified_at = ?,
                verification_idempotency_key = ?, version = version + 1,
                updated_at = ?
            WHERE id = ? AND version = ?
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
        if updated.rowcount != 1:
            raise TherapeuticAssessmentError(
                "version_conflict", "证据版本已变化。", 409
            )
        write_audit_log(
            conn,
            "therapeutic_assessment_recovery_evidence_verified",
            actor_id,
            "therapeutic_assessment_recovery_evidence",
            evidence_id,
            {"decision": decision, "incident_id": row["incident_id"]},
        )
        conn.commit()
        return row_to_dict(
            conn.execute(
                "SELECT * FROM therapeutic_assessment_recovery_evidence WHERE id = ?",
                (evidence_id,),
            ).fetchone()
        )


def restore_after_incident(
    actor: dict,
    incident_id: str,
    payload: dict,
    idempotency_key: str,
) -> dict:
    _assert_reviewer(actor)
    key = _idempotency(idempotency_key)
    expected_version = payload.get("expected_version")
    if not isinstance(expected_version, int):
        raise TherapeuticAssessmentError(
            "validation_error", "恢复必须提供expected_version。", 422
        )
    policy = _policy()
    actor_id = str(actor["id"])
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM therapeutic_assessment_stop_incidents WHERE id = ?",
            (incident_id,),
        ).fetchone()
        if row is None:
            raise TherapeuticAssessmentError(
                "not_found", "没有找到停止事件。", 404
            )
        incident = row_to_dict(row)
        if incident["status"] == "restored":
            if incident.get("restore_idempotency_key") == key:
                return _present_incident(incident)
            raise TherapeuticAssessmentError(
                "incident_closed", "该停止事件已经恢复。", 409
            )
        if int(incident["version"]) != expected_version:
            raise TherapeuticAssessmentError(
                "version_conflict", "停止事件版本已变化。", 409
            )
        evidence = rows_to_dicts(
            conn.execute(
                """
                SELECT * FROM therapeutic_assessment_recovery_evidence
                WHERE incident_id = ? AND status = 'verified'
                  AND verified_by IS NOT NULL AND verified_by != recorded_by
                """,
                (incident_id,),
            ).fetchall()
        )
        verified_types = {item["evidence_type"] for item in evidence}
        missing = [
            item for item in policy["recovery_gates"] if item not in verified_types
        ]
        if missing:
            raise TherapeuticAssessmentError(
                "recovery_evidence_incomplete",
                "恢复证据尚未齐全。",
                409,
                details={"missing": missing},
            )
        other_open = int(
            conn.execute(
                """
                SELECT COUNT(*) AS c FROM therapeutic_assessment_stop_incidents
                WHERE id != ? AND status IN ('open', 'recovery_pending')
                """,
                (incident_id,),
            ).fetchone()["c"]
        )
        if other_open:
            raise TherapeuticAssessmentError(
                "other_open_incidents",
                "仍有其它未关闭事件，不能恢复全局流程。",
                409,
            )
        timestamp = now_iso()
        updated = conn.execute(
            """
            UPDATE therapeutic_assessment_stop_incidents
            SET status = 'restored', restore_idempotency_key = ?, restored_by = ?,
                restored_at = ?, version = version + 1, updated_at = ?
            WHERE id = ? AND version = ?
            """,
            (
                key,
                actor_id,
                timestamp,
                timestamp,
                incident_id,
                expected_version,
            ),
        )
        if updated.rowcount != 1:
            raise TherapeuticAssessmentError(
                "version_conflict", "停止事件版本已变化。", 409
            )
        _runtime(conn)
        conn.execute(
            """
            UPDATE therapeutic_assessment_runtime_control
            SET killed = 0, reason = NULL, changed_by = ?, changed_at = ?,
                restoration_evidence_ref = ?
            WHERE id = 'global'
            """,
            (
                actor_id,
                timestamp,
                f"incident:{incident_id}:verified-gates:{len(verified_types)}",
            ),
        )
        write_audit_log(
            conn,
            "therapeutic_assessment_stop_incident_restored",
            actor_id,
            "therapeutic_assessment_stop_incident",
            incident_id,
            {
                "verified_gates": sorted(verified_types),
                "independent_evidence_only": True,
                "temporary_showcase_counted": False,
            },
        )
        conn.commit()
        restored = row_to_dict(
            conn.execute(
                "SELECT * FROM therapeutic_assessment_stop_incidents WHERE id = ?",
                (incident_id,),
            ).fetchone()
        )
    return _present_incident(restored)
