"""Authorized snapshots and asynchronous research-analysis jobs (T36-F13)."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta, timezone

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
from services.research_access_service import assert_capability, has_object_scope, require_object_scope


ANALYSIS_TYPES = {"affect_aggregate", "semantic_network", "family_topology"}
JOB_STATUSES = {"queued", "running", "succeeded", "failed", "canceled", "expired", "suspended"}
SOURCE_TYPES = {
    "emotion_diary",
    "assessment_result",
    "relationship_task",
    "checkin",
    "message_feedback",
    "synthetic_fixture",
}
RECOVERY_REASONS = {"dependency_recovered", "resource_reenabled", "authorization_restored", "operator_retry"}
DELETION_REASONS = {"participant_withdrawal", "retention_expired", "correction", "model_retired"}
PARAMETER_KEYS = {
    "window_days",
    "minimum_count",
    "aggregation_level",
    "dimension_ids",
    "include_unknown",
    "synthetic_sample_size",
}
METRIC_KEYS = {"coverage_rate", "unknown_rate", "sample_size", "quality_status", "result", "warnings"}
FORBIDDEN_KEYS = {"text", "raw_text", "content", "body", "prompt", "answer", "diagnosis", "label"}
BOUNDARY_NOTICE = "结果仅供授权研究者查看，是聚合研究线索，不构成诊断、人格标签、治疗结论或个体自动决策。"


class ResearchAnalysisError(Exception):
    def __init__(self, code: str, message: str, status: int = 400, details: dict | None = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status = status
        self.details = details or {}


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(value: datetime) -> str:
    return value.isoformat()


def _hash(value: object) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _expand(item: dict | None) -> dict | None:
    if not item:
        return item
    result = dict(item)
    for key in ("parameters_json", "metrics_json", "metadata_json"):
        if key in result:
            result[key[:-5]] = json_loads(result.pop(key), {})
    if "shadow_mode" in result:
        result["shadow_mode"] = bool(result["shadow_mode"])
    result.pop("lease_owner", None)
    return result


def _latest_research_consent(conn, user_id: str) -> dict | None:
    rows = rows_to_dicts(
        conn.execute(
            """SELECT * FROM consent_records
               WHERE user_id = ? AND consent_type IN ('research_authorization', 'anonymous_research')
               ORDER BY created_at DESC""",
            (user_id,),
        ).fetchall()
    )
    latest: dict[str, dict] = {}
    for item in rows:
        latest.setdefault(str(item["consent_type"]), item)
    for key in ("research_authorization", "anonymous_research"):
        if key in latest and bool(latest[key]["agreed"]):
            return latest[key]
    return None


def _enrollment(conn, enrollment_id: str, participant_user_id: str) -> dict:
    row = conn.execute(
        "SELECT * FROM relationship_pilot_enrollments WHERE id = ? AND user_id = ?",
        (enrollment_id, participant_user_id),
    ).fetchone()
    if not row:
        raise ResearchAnalysisError("not_found", "没有找到该参与者的项目报名记录。", 404)
    return row_to_dict(row)


def _assert_safe_shape(value: object, allowed: set[str] | None = None) -> None:
    if isinstance(value, dict):
        keys = {str(key) for key in value}
        if allowed is not None and not keys.issubset(allowed):
            raise ResearchAnalysisError(
                "validation_error",
                "只允许提交最小聚合参数。",
                details={"unknown_fields": sorted(keys - allowed)},
            )
        found = {key.lower() for key in keys} & FORBIDDEN_KEYS
        if found:
            raise ResearchAnalysisError(
                "sensitive_payload_rejected",
                "分析任务和结果不得包含参与者原文或诊断标签。",
                details={"forbidden_fields": sorted(found)},
            )
        for child in value.values():
            _assert_safe_shape(child)
    elif isinstance(value, list):
        for child in value:
            _assert_safe_shape(child)


def _snapshot(conn, snapshot_id: str) -> dict:
    row = conn.execute("SELECT * FROM research_analysis_snapshots WHERE id = ?", (snapshot_id,)).fetchone()
    if not row:
        raise ResearchAnalysisError("not_found", "没有找到分析数据快照。", 404)
    return row_to_dict(row)


def _job(conn, job_id: str) -> dict:
    row = conn.execute("SELECT * FROM research_analysis_jobs WHERE id = ?", (job_id,)).fetchone()
    if not row:
        raise ResearchAnalysisError("not_found", "没有找到在线分析任务。", 404)
    return row_to_dict(row)


def _event(
    conn,
    job_id: str,
    actor_id: str,
    action: str,
    before: str,
    after: str,
    *,
    error_code: str | None = None,
    metadata: dict | None = None,
) -> None:
    conn.execute(
        """INSERT INTO research_analysis_events
           (id, job_id, actor_id, action, from_status, to_status, error_code, metadata_json, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            new_id("analysis_event"),
            job_id,
            actor_id,
            action,
            before,
            after,
            error_code,
            json_dumps(metadata or {}),
            now_iso(),
        ),
    )


def _freeze_invalid_snapshot(conn, snapshot: dict) -> None:
    now = _now()
    status = str(snapshot["authorization_status"])
    if status != "active":
        raise ResearchAnalysisError("analysis_suspended", "数据授权已失效，分析任务已冻结。", 409)
    if datetime.fromisoformat(str(snapshot["expires_at"])) <= now:
        timestamp = _iso(now)
        conn.execute(
            "UPDATE research_analysis_snapshots SET authorization_status = 'expired', suspended_at = ? WHERE id = ?",
            (timestamp, snapshot["id"]),
        )
        conn.execute(
            """UPDATE research_analysis_jobs SET status = 'expired', expired_at = ?, updated_at = ?
               WHERE snapshot_id = ? AND status IN ('queued', 'failed', 'suspended')""",
            (timestamp, timestamp, snapshot["id"]),
        )
        conn.execute(
            "UPDATE research_analysis_artifacts SET status = 'suspended', suspended_at = ? WHERE snapshot_id = ? AND status = 'active'",
            (timestamp, snapshot["id"]),
        )
        conn.commit()
        raise ResearchAnalysisError("analysis_expired", "数据快照已过期，任务和派生结果已冻结。", 409)
    consent = _latest_research_consent(conn, str(snapshot["participant_user_id"]))
    if not consent or str(consent["consent_version"]) != str(snapshot["consent_version"]):
        timestamp = _iso(now)
        conn.execute(
            "UPDATE research_analysis_snapshots SET authorization_status = 'suspended', suspended_at = ? WHERE id = ?",
            (timestamp, snapshot["id"]),
        )
        conn.execute(
            """UPDATE research_analysis_jobs SET status = 'suspended', suspended_at = ?, updated_at = ?,
               lease_owner = NULL, lease_expires_at = NULL
               WHERE snapshot_id = ? AND status NOT IN ('canceled', 'expired')""",
            (timestamp, timestamp, snapshot["id"]),
        )
        conn.execute(
            "UPDATE research_analysis_artifacts SET status = 'suspended', suspended_at = ? WHERE snapshot_id = ? AND status = 'active'",
            (timestamp, snapshot["id"]),
        )
        conn.commit()
        raise ResearchAnalysisError(
            "research_authorization_invalid",
            "研究授权已撤回或版本已变化，任务和派生结果已冻结。",
            409,
        )


def create_snapshot(actor: dict, payload: dict) -> tuple[dict, int]:
    assert_capability(actor, "research.analysis.create")
    allowed = {"participant_user_id", "enrollment_id", "purpose_code", "expires_in_days", "source_refs"}
    unknown = set(payload) - allowed
    if unknown:
        raise ResearchAnalysisError("validation_error", "数据快照包含未知字段。", details={"unknown_fields": sorted(unknown)})
    participant_user_id = str(payload.get("participant_user_id") or "").strip()
    enrollment_id = str(payload.get("enrollment_id") or "").strip()
    purpose_code = str(payload.get("purpose_code") or "").strip()
    refs = payload.get("source_refs")
    expires_in_days = int(payload.get("expires_in_days") or 30)
    purposes = {"affect_research", "semantic_network_research", "family_topology_research"}
    if not participant_user_id or not enrollment_id or purpose_code not in purposes:
        raise ResearchAnalysisError("validation_error", "参与者、报名记录或研究用途无效。")
    if not isinstance(refs, list) or not refs or len(refs) > 500 or expires_in_days not in range(1, 91):
        raise ResearchAnalysisError("validation_error", "来源引用或有效期无效。")
    normalized: list[dict] = []
    for ref in refs:
        if not isinstance(ref, dict) or set(ref) - {"source_type", "source_id", "source_version", "source_hash"}:
            raise ResearchAnalysisError("validation_error", "来源只允许类型、ID、版本和内容指纹。")
        source_type = str(ref.get("source_type") or "")
        source_id = str(ref.get("source_id") or "")
        source_hash = str(ref.get("source_hash") or "")
        if source_type not in SOURCE_TYPES or not source_id or len(source_hash) != 64:
            raise ResearchAnalysisError("validation_error", "来源引用类型、ID或SHA256无效。")
        normalized.append(
            {
                "source_type": source_type,
                "source_id": source_id,
                "source_version": str(ref.get("source_version") or ""),
                "source_hash": source_hash.lower(),
            }
        )
    with get_connection() as conn:
        enrollment = _enrollment(conn, enrollment_id, participant_user_id)
        require_object_scope(conn, actor, enrollment, "research.analysis.create")
        consent = _latest_research_consent(conn, participant_user_id)
        if not consent:
            raise ResearchAnalysisError("research_authorization_required", "参与者尚未授权该研究用途。", 409)
        timestamp = now_iso()
        snapshot_id = new_id("analysis_snapshot")
        snapshot_hash = _hash(
            {
                "participant_user_id": participant_user_id,
                "purpose_code": purpose_code,
                "consent_version": consent["consent_version"],
                "source_refs": sorted(normalized, key=lambda item: (item["source_type"], item["source_id"])),
            }
        )
        expires_at = _iso(_now() + timedelta(days=expires_in_days))
        conn.execute(
            """INSERT INTO research_analysis_snapshots
               (id, participant_user_id, enrollment_id, purpose_code, consent_type, consent_version,
                authorization_status, source_count, snapshot_hash, expires_at, created_by, created_at)
               VALUES (?, ?, ?, ?, ?, ?, 'active', ?, ?, ?, ?, ?)""",
            (
                snapshot_id,
                participant_user_id,
                enrollment_id,
                purpose_code,
                consent["consent_type"],
                consent["consent_version"],
                len(normalized),
                snapshot_hash,
                expires_at,
                actor["id"],
                timestamp,
            ),
        )
        for ref in normalized:
            conn.execute(
                """INSERT INTO research_analysis_snapshot_links
                   (id, snapshot_id, source_type, source_id, source_version, source_hash, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    new_id("analysis_link"),
                    snapshot_id,
                    ref["source_type"],
                    ref["source_id"],
                    ref["source_version"] or None,
                    ref["source_hash"],
                    timestamp,
                ),
            )
        write_audit_log(
            conn,
            "research_analysis_snapshot_created",
            actor["id"],
            "research_analysis_snapshot",
            snapshot_id,
            {"purpose_code": purpose_code, "source_count": len(normalized), "raw_text_included": False},
        )
        conn.commit()
        result = _snapshot(conn, snapshot_id)
    result.pop("participant_user_id", None)
    return {**result, "raw_text_included": False}, 201


def enqueue_job(actor: dict, payload: dict, idempotency_key: str) -> tuple[dict, int]:
    assert_capability(actor, "research.analysis.create")
    allowed = {"snapshot_id", "analysis_type", "analysis_version", "resource_hash", "parameters", "max_attempts"}
    unknown = set(payload) - allowed
    if unknown:
        raise ResearchAnalysisError(
            "validation_error",
            "分析任务只接受快照和版本化聚合参数。",
            details={"unknown_fields": sorted(unknown)},
        )
    snapshot_id = str(payload.get("snapshot_id") or "")
    analysis_type = str(payload.get("analysis_type") or "")
    analysis_version = str(payload.get("analysis_version") or "")
    resource_hash = str(payload.get("resource_hash") or "")
    parameters = payload.get("parameters") or {}
    max_attempts = int(payload.get("max_attempts") or 3)
    _assert_safe_shape(parameters, PARAMETER_KEYS)
    if (
        len(idempotency_key) < 4
        or analysis_type not in ANALYSIS_TYPES
        or not analysis_version
        or len(resource_hash) != 64
        or max_attempts not in range(1, 11)
    ):
        raise ResearchAnalysisError("validation_error", "幂等键、分析类型、版本、资源SHA256或重试次数无效。")
    with get_connection() as conn:
        snapshot = _snapshot(conn, snapshot_id)
        enrollment = _enrollment(conn, str(snapshot["enrollment_id"]), str(snapshot["participant_user_id"]))
        require_object_scope(conn, actor, enrollment, "research.analysis.create")
        _freeze_invalid_snapshot(conn, snapshot)
        existing = conn.execute(
            "SELECT * FROM research_analysis_jobs WHERE created_by = ? AND idempotency_key = ?",
            (actor["id"], idempotency_key),
        ).fetchone()
        if existing:
            conn.commit()
            return _expand(row_to_dict(existing)), 200
        timestamp = now_iso()
        job_id = new_id("analysis_job")
        conn.execute(
            """INSERT INTO research_analysis_jobs
               (id, snapshot_id, analysis_type, analysis_version, resource_hash, parameters_json,
                idempotency_key, status, attempt_count, max_attempts, available_at, shadow_mode,
                created_by, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, 'queued', 0, ?, ?, 1, ?, ?, ?)""",
            (
                job_id,
                snapshot_id,
                analysis_type,
                analysis_version,
                resource_hash.lower(),
                json_dumps(parameters),
                idempotency_key,
                max_attempts,
                timestamp,
                actor["id"],
                timestamp,
                timestamp,
            ),
        )
        _event(
            conn,
            job_id,
            actor["id"],
            "enqueue",
            "none",
            "queued",
            metadata={"analysis_type": analysis_type, "raw_text_included": False},
        )
        write_audit_log(
            conn,
            "research_analysis_job_enqueued",
            actor["id"],
            "research_analysis_job",
            job_id,
            {"analysis_type": analysis_type, "snapshot_id": snapshot_id, "shadow_mode": True},
        )
        conn.commit()
        return _expand(_job(conn, job_id)), 201


def list_jobs(actor: dict, status: str = "", limit: int = 50) -> dict:
    assert_capability(actor, "research.analysis.read")
    if status and status not in JOB_STATUSES:
        raise ResearchAnalysisError("validation_error", "任务状态无效。")
    limit = max(1, min(int(limit or 50), 200))
    with get_connection() as conn:
        if status:
            rows = conn.execute(
                "SELECT * FROM research_analysis_jobs WHERE status = ? ORDER BY created_at DESC LIMIT ?",
                (status, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM research_analysis_jobs ORDER BY created_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
        items = []
        for row in rows:
            item = _expand(row_to_dict(row))
            # 逐项按对象范围过滤：researcher/supervisor 只能看到被授权参与者的任务，
            # admin 全量可见；避免列表接口泄漏他人任务参数与指标。
            try:
                snapshot = _snapshot(conn, str(item["snapshot_id"]))
                enrollment = _enrollment(conn, str(snapshot["enrollment_id"]), str(snapshot["participant_user_id"]))
            except ResearchAnalysisError:
                continue
            if not has_object_scope(conn, actor, enrollment):
                continue
            artifact = conn.execute(
                "SELECT * FROM research_analysis_artifacts WHERE job_id = ?",
                (item["id"],),
            ).fetchone()
            item["artifact"] = _expand(row_to_dict(artifact))
            items.append(item)
    return {"items": items, "count": len(items), "raw_text_included": False, "boundary_notice": BOUNDARY_NOTICE}


def get_job(actor: dict, job_id: str) -> dict:
    assert_capability(actor, "research.analysis.read")
    with get_connection() as conn:
        item = _job(conn, job_id)
        snapshot = _snapshot(conn, str(item["snapshot_id"]))
        enrollment = _enrollment(conn, str(snapshot["enrollment_id"]), str(snapshot["participant_user_id"]))
        require_object_scope(conn, actor, enrollment, "research.analysis.read")
        try:
            _freeze_invalid_snapshot(conn, snapshot)
        except ResearchAnalysisError:
            conn.commit()
            item = _job(conn, job_id)
        events = [
            _expand(row_to_dict(row))
            for row in conn.execute(
                "SELECT * FROM research_analysis_events WHERE job_id = ? ORDER BY created_at",
                (job_id,),
            ).fetchall()
        ]
        artifact = conn.execute(
            "SELECT * FROM research_analysis_artifacts WHERE job_id = ?",
            (job_id,),
        ).fetchone()
        write_audit_log(
            conn,
            "research_analysis_job_viewed",
            actor["id"],
            "research_analysis_job",
            job_id,
            {"status": item["status"]},
        )
        conn.commit()
    return {
        **_expand(item),
        "events": events,
        "artifact": _expand(row_to_dict(artifact)),
        "raw_text_included": False,
        "boundary_notice": BOUNDARY_NOTICE,
    }


def claim_job(actor: dict, job_id: str, payload: dict) -> dict:
    assert_capability(actor, "research.analysis.operate")
    if not current_app.config.get("RESEARCH_ANALYSIS_JOB_EXECUTION_ENABLED", False):
        raise ResearchAnalysisError("analysis_execution_disabled", "当前环境未开启在线分析执行器。", 503)
    lease_seconds = max(30, min(int(payload.get("lease_seconds") or 300), 3600))
    force_due = payload.get("force_due") is True
    now = _now()
    with get_connection() as conn:
        item = _job(conn, job_id)
        snapshot = _snapshot(conn, str(item["snapshot_id"]))
        _freeze_invalid_snapshot(conn, snapshot)
        prior_status = str(item["status"])
        prior_lease = item.get("lease_expires_at")
        reclaimed = False
        if item.get("dead_lettered_at"):
            raise ResearchAnalysisError("job_state_conflict", "该任务当前不能领取。", 409)
        if prior_status in {"queued", "failed"}:
            if not force_due and datetime.fromisoformat(str(item["available_at"])) > now:
                raise ResearchAnalysisError("job_not_due", "该任务尚未到重试时间。", 409)
        elif prior_status == "running" and prior_lease and datetime.fromisoformat(str(prior_lease)) < now:
            # 执行器崩溃或超时后租约过期，允许安全重领，避免任务永久卡在 running。
            reclaimed = True
        else:
            raise ResearchAnalysisError("job_state_conflict", "该任务当前不能领取。", 409)
        expires_at = _iso(now + timedelta(seconds=lease_seconds))
        # 乐观锁同时绑定 prior_status 与 prior_lease，防止两个执行器同时新领或同时重领。
        if prior_lease is None:
            updated = conn.execute(
                """UPDATE research_analysis_jobs SET status = 'running', lease_owner = ?, lease_expires_at = ?, updated_at = ?
                   WHERE id = ? AND status = ? AND lease_expires_at IS NULL""",
                (actor["id"], expires_at, _iso(now), job_id, prior_status),
            )
        else:
            updated = conn.execute(
                """UPDATE research_analysis_jobs SET status = 'running', lease_owner = ?, lease_expires_at = ?, updated_at = ?
                   WHERE id = ? AND status = ? AND lease_expires_at = ?""",
                (actor["id"], expires_at, _iso(now), job_id, prior_status, prior_lease),
            )
        if updated.rowcount != 1:
            raise ResearchAnalysisError("job_lease_conflict", "任务已被其他执行器领取。", 409)
        _event(
            conn,
            job_id,
            actor["id"],
            "reclaim" if reclaimed else "claim",
            prior_status,
            "running",
            metadata={"lease_seconds": lease_seconds, "reclaimed_expired_lease": reclaimed},
        )
        conn.commit()
        return _expand(_job(conn, job_id))


def complete_job(actor: dict, job_id: str, payload: dict) -> dict:
    assert_capability(actor, "research.analysis.operate")
    metrics = payload.get("metrics") or {}
    _assert_safe_shape(metrics, METRIC_KEYS)
    coverage = metrics.get("coverage_rate")
    unknown = metrics.get("unknown_rate")
    sample_size = metrics.get("sample_size")
    quality = str(metrics.get("quality_status") or "")
    if (
        not isinstance(coverage, (int, float))
        or not 0 <= coverage <= 1
        or not isinstance(unknown, (int, float))
        or not 0 <= unknown <= 1
        or not isinstance(sample_size, int)
        or sample_size < 0
        or quality not in {"sufficient", "limited", "insufficient"}
    ):
        raise ResearchAnalysisError("validation_error", "结果必须包含合法覆盖率、未知率、样本量和质量状态。")
    timestamp = now_iso()
    with get_connection() as conn:
        item = _job(conn, job_id)
        snapshot = _snapshot(conn, str(item["snapshot_id"]))
        _freeze_invalid_snapshot(conn, snapshot)
        if item["status"] != "running" or item["lease_owner"] != actor["id"]:
            raise ResearchAnalysisError("job_lease_conflict", "只有当前租约持有人可以完成任务。", 409)
        artifact_id = new_id("analysis_artifact")
        artifact_hash = _hash(
            {
                "job_id": job_id,
                "snapshot_hash": snapshot["snapshot_hash"],
                "analysis_version": item["analysis_version"],
                "metrics": metrics,
            }
        )
        conn.execute(
            """INSERT INTO research_analysis_artifacts
               (id, job_id, snapshot_id, analysis_type, analysis_version, metrics_json, artifact_hash,
                quality_status, boundary_notice, visibility, status, created_by, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'researcher_only', 'active', ?, ?)""",
            (
                artifact_id,
                job_id,
                item["snapshot_id"],
                item["analysis_type"],
                item["analysis_version"],
                json_dumps(metrics),
                artifact_hash,
                quality,
                BOUNDARY_NOTICE,
                actor["id"],
                timestamp,
            ),
        )
        conn.execute(
            """UPDATE research_analysis_jobs SET status = 'succeeded', result_artifact_id = ?, completed_at = ?,
               lease_owner = NULL, lease_expires_at = NULL, updated_at = ? WHERE id = ?""",
            (artifact_id, timestamp, timestamp, job_id),
        )
        _event(
            conn,
            job_id,
            actor["id"],
            "complete",
            "running",
            "succeeded",
            metadata={"artifact_hash": artifact_hash, "quality_status": quality},
        )
        write_audit_log(
            conn,
            "research_analysis_job_completed",
            actor["id"],
            "research_analysis_job",
            job_id,
            {"artifact_id": artifact_id, "quality_status": quality, "raw_text_included": False},
        )
        conn.commit()
        return _expand(_job(conn, job_id))


def fail_job(actor: dict, job_id: str, payload: dict) -> dict:
    assert_capability(actor, "research.analysis.operate")
    error_code = str(payload.get("error_code") or "analysis_failed")[:64]
    now = _now()
    with get_connection() as conn:
        item = _job(conn, job_id)
        if item["status"] != "running" or item["lease_owner"] != actor["id"]:
            raise ResearchAnalysisError("job_lease_conflict", "只有当前租约持有人可以记录失败。", 409)
        attempts = int(item["attempt_count"] or 0) + 1
        dead = attempts >= int(item["max_attempts"] or 3)
        backoff = min(3600, 60 * (2 ** max(0, attempts - 1)))
        conn.execute(
            """UPDATE research_analysis_jobs SET status = 'failed', attempt_count = ?, available_at = ?,
               lease_owner = NULL, lease_expires_at = NULL, last_error_code = ?, dead_lettered_at = ?,
               updated_at = ? WHERE id = ?""",
            (
                attempts,
                _iso(now + timedelta(seconds=backoff)),
                error_code,
                _iso(now) if dead else None,
                _iso(now),
                job_id,
            ),
        )
        _event(
            conn,
            job_id,
            actor["id"],
            "fail",
            "running",
            "failed",
            error_code=error_code,
            metadata={"attempt_count": attempts, "dead_letter": dead, "backoff_seconds": backoff},
        )
        write_audit_log(
            conn,
            "research_analysis_job_failed",
            actor["id"],
            "research_analysis_job",
            job_id,
            {"error_code": error_code, "dead_letter": dead},
        )
        conn.commit()
        return _expand(_job(conn, job_id))


def cancel_job(actor: dict, job_id: str) -> dict:
    assert_capability(actor, "research.analysis.create")
    timestamp = now_iso()
    with get_connection() as conn:
        item = _job(conn, job_id)
        if item["status"] not in {"queued", "failed", "running"}:
            raise ResearchAnalysisError("job_state_conflict", "该任务当前不能取消。", 409)
        if actor["role"] != "admin" and str(item["created_by"]) != str(actor["id"]):
            raise ResearchAnalysisError("forbidden", "只能取消本人创建的分析任务。", 403)
        conn.execute(
            """UPDATE research_analysis_jobs SET status = 'canceled', canceled_at = ?,
               lease_owner = NULL, lease_expires_at = NULL, updated_at = ? WHERE id = ?""",
            (timestamp, timestamp, job_id),
        )
        _event(conn, job_id, actor["id"], "cancel", item["status"], "canceled")
        write_audit_log(conn, "research_analysis_job_canceled", actor["id"], "research_analysis_job", job_id, {})
        conn.commit()
        return _expand(_job(conn, job_id))


def recover_job(actor: dict, job_id: str, payload: dict) -> dict:
    assert_capability(actor, "research.analysis.operate")
    reason = str(payload.get("reason_code") or "")
    if reason not in RECOVERY_REASONS:
        raise ResearchAnalysisError("validation_error", "需要选择受控的恢复原因。")
    timestamp = now_iso()
    with get_connection() as conn:
        item = _job(conn, job_id)
        snapshot = _snapshot(conn, str(item["snapshot_id"]))
        _freeze_invalid_snapshot(conn, snapshot)
        if item["status"] not in {"failed", "suspended"}:
            raise ResearchAnalysisError("job_state_conflict", "只有失败或已冻结任务可以人工恢复。", 409)
        conn.execute(
            """UPDATE research_analysis_jobs SET status = 'queued', attempt_count = 0, available_at = ?,
               dead_lettered_at = NULL, last_error_code = NULL, suspended_at = NULL, updated_at = ?
               WHERE id = ?""",
            (timestamp, timestamp, job_id),
        )
        _event(conn, job_id, actor["id"], "recover", item["status"], "queued", metadata={"reason_code": reason})
        write_audit_log(
            conn,
            "research_analysis_job_recovered",
            actor["id"],
            "research_analysis_job",
            job_id,
            {"reason_code": reason},
        )
        conn.commit()
        return _expand(_job(conn, job_id))


def suspend_job(actor: dict, job_id: str, payload: dict) -> dict:
    assert_capability(actor, "research.analysis.operate")
    reason = str(payload.get("reason_code") or "resource_disabled")[:64]
    timestamp = now_iso()
    with get_connection() as conn:
        item = _job(conn, job_id)
        if item["status"] in {"canceled", "expired"}:
            raise ResearchAnalysisError("job_state_conflict", "终止任务不能再冻结。", 409)
        conn.execute(
            """UPDATE research_analysis_jobs SET status = 'suspended', suspended_at = ?,
               lease_owner = NULL, lease_expires_at = NULL, updated_at = ? WHERE id = ?""",
            (timestamp, timestamp, job_id),
        )
        conn.execute(
            "UPDATE research_analysis_artifacts SET status = 'suspended', suspended_at = ? WHERE job_id = ? AND status = 'active'",
            (timestamp, job_id),
        )
        _event(
            conn,
            job_id,
            actor["id"],
            "suspend",
            item["status"],
            "suspended",
            metadata={"reason_code": reason},
        )
        write_audit_log(
            conn,
            "research_analysis_job_suspended",
            actor["id"],
            "research_analysis_job",
            job_id,
            {"reason_code": reason},
        )
        conn.commit()
        return _expand(_job(conn, job_id))


def get_artifact(actor: dict, artifact_id: str) -> dict:
    assert_capability(actor, "research.analysis.read")
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM research_analysis_artifacts WHERE id = ?",
            (artifact_id,),
        ).fetchone()
        if not row:
            raise ResearchAnalysisError("not_found", "没有找到分析结果。", 404)
        item = row_to_dict(row)
        snapshot = _snapshot(conn, str(item["snapshot_id"]))
        enrollment = _enrollment(conn, str(snapshot["enrollment_id"]), str(snapshot["participant_user_id"]))
        require_object_scope(conn, actor, enrollment, "research.analysis.read")
        _freeze_invalid_snapshot(conn, snapshot)
        if item["status"] != "active":
            raise ResearchAnalysisError("artifact_unavailable", "该派生结果已冻结或删除。", 410)
        write_audit_log(
            conn,
            "research_analysis_artifact_viewed",
            actor["id"],
            "research_analysis_artifact",
            artifact_id,
            {"quality_status": item["quality_status"]},
        )
        conn.commit()
    return {**_expand(item), "raw_text_included": False}


def delete_artifact(actor: dict, artifact_id: str, payload: dict) -> dict:
    assert_capability(actor, "research.analysis.operate")
    reason = str(payload.get("reason_code") or "")
    if reason not in DELETION_REASONS:
        raise ResearchAnalysisError("validation_error", "需要选择受控的派生数据删除原因。")
    timestamp = now_iso()
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM research_analysis_artifacts WHERE id = ?",
            (artifact_id,),
        ).fetchone()
        if not row:
            raise ResearchAnalysisError("not_found", "没有找到分析结果。", 404)
        item = row_to_dict(row)
        if item["status"] == "deleted":
            return {
                "id": artifact_id,
                "status": "deleted",
                "deleted_at": item["deleted_at"],
                "idempotent": True,
            }
        conn.execute(
            """UPDATE research_analysis_artifacts SET status = 'deleted', metrics_json = '{}',
               deleted_at = ?, deletion_reason_code = ? WHERE id = ?""",
            (timestamp, reason, artifact_id),
        )
        write_audit_log(
            conn,
            "research_analysis_artifact_deleted",
            actor["id"],
            "research_analysis_artifact",
            artifact_id,
            {"reason_code": reason, "derived_data_only": True},
        )
        conn.commit()
    return {
        "id": artifact_id,
        "status": "deleted",
        "deleted_at": timestamp,
        "derived_data_only": True,
    }
