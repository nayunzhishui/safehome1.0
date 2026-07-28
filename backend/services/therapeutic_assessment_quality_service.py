from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone

from database import (
    get_connection,
    json_dumps,
    json_loads,
    load_content_json,
    new_id,
    now_iso,
    row_to_dict,
    rows_to_dicts,
    write_audit_log,
)
from services.message_service import create_message
from services.therapeutic_assessment_service import (
    FORMAL_ROLES,
    REVIEW_ROLES,
    TherapeuticAssessmentError,
    _assert_read,
    _case_row,
    _idempotency,
)


OPEN_REVIEW_STATUSES = {"pending", "in_review"}
OPEN_INCIDENT_STATUSES = {"reported", "independent_review"}


def _policy() -> dict:
    return load_content_json("therapeutic_assessment_quality_policy.json")


def _present_review(row: dict) -> dict:
    item = dict(row)
    item["dimensions"] = json_loads(item.pop("dimensions_json", None), {})
    item["overdue"] = item.get("status") in OPEN_REVIEW_STATUSES and str(item.get("due_at") or "") <= now_iso()
    return item


def _present_incident(row: dict) -> dict:
    item = dict(row)
    item["impact_analysis"] = json_loads(item.pop("impact_analysis_json", None), {})
    return item


def _quality_event(
    conn,
    *,
    entity_type: str,
    entity_id: str,
    actor_id: str,
    action: str,
    idempotency_key: str,
    before_version: int | None,
    after_version: int | None,
    metadata: dict,
) -> None:
    conn.execute(
        """
        INSERT INTO therapeutic_assessment_quality_events (
            id, entity_type, entity_id, actor_id, action, before_version,
            after_version, metadata_json, idempotency_key, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            new_id("ta_quality_evt"),
            entity_type,
            entity_id,
            actor_id,
            action,
            before_version,
            after_version,
            json_dumps(metadata),
            idempotency_key,
            now_iso(),
        ),
    )


def quality_runtime_status() -> dict:
    policy = _policy()
    limits = policy["queue_pause"]
    timestamp = now_iso()
    with get_connection() as conn:
        pending_count = int(
            conn.execute(
                "SELECT COUNT(*) AS count FROM therapeutic_assessment_quality_reviews WHERE status IN ('pending', 'in_review')"
            ).fetchone()["count"]
        )
        overdue_count = int(
            conn.execute(
                """
                SELECT COUNT(*) AS count
                FROM therapeutic_assessment_quality_reviews
                WHERE status IN ('pending', 'in_review') AND due_at <= ?
                """,
                (timestamp,),
            ).fetchone()["count"]
        )
        paused = pending_count >= int(limits["max_pending"]) or overdue_count >= int(limits["max_overdue"])
        reason = "quality_queue_sla_exceeded" if paused else None
        current = conn.execute(
            "SELECT * FROM therapeutic_assessment_quality_runtime WHERE id = 'quality-runtime'"
        ).fetchone()
        version = int(current["version"]) + 1 if current else 1
        runtime_values = (
            int(paused),
            reason,
            pending_count,
            overdue_count,
            str(policy["version"]),
            version,
            timestamp,
        )
        if current is None:
            conn.execute(
                """
                INSERT INTO therapeutic_assessment_quality_runtime (
                    id, paused, reason, pending_count, overdue_count,
                    policy_version, version, updated_at
                ) VALUES ('quality-runtime', ?, ?, ?, ?, ?, ?, ?)
                """,
                runtime_values,
            )
        else:
            conn.execute(
                """
                UPDATE therapeutic_assessment_quality_runtime
                SET paused = ?, reason = ?, pending_count = ?, overdue_count = ?,
                    policy_version = ?, version = ?, updated_at = ?
                WHERE id = 'quality-runtime'
                """,
                runtime_values,
            )
        if current is None or bool(current["paused"]) != paused:
            write_audit_log(
                conn,
                "therapeutic_assessment_quality_runtime_changed",
                None,
                "therapeutic_assessment_quality_runtime",
                "quality-runtime",
                {
                    "paused": paused,
                    "pending_count": pending_count,
                    "overdue_count": overdue_count,
                    "reason": reason,
                },
            )
        conn.commit()
    return {
        "paused": paused,
        "reason": reason,
        "pending_count": pending_count,
        "overdue_count": overdue_count,
        "policy_version": str(policy["version"]),
        "new_case_intake_enabled": not paused,
    }


def assert_new_case_intake_allowed() -> None:
    status = quality_runtime_status()
    if status["paused"]:
        raise TherapeuticAssessmentError(
            "quality_queue_paused",
            "当前人工质量队列已超过承诺时限，新的协作记录暂时暂停进入。",
            503,
            {
                "pending_count": status["pending_count"],
                "overdue_count": status["overdue_count"],
            },
        )


def enqueue_quality_review(conn, feedback: dict, case: dict) -> dict | None:
    existing = conn.execute(
        "SELECT * FROM therapeutic_assessment_quality_reviews WHERE feedback_id = ?",
        (feedback["id"],),
    ).fetchone()
    if existing is not None:
        return _present_review(row_to_dict(existing))
    policy = _policy()
    level = str(case.get("readiness_level") or "L0")
    level_policy = policy["service_levels"].get(level, policy["service_levels"]["L0"])
    sample_rate = float(level_policy["sample_rate"])
    bucket = int(hashlib.sha256(str(feedback["id"]).encode("utf-8")).hexdigest()[:8], 16) / 0xFFFFFFFF
    mandatory = level in {"L2", "L3"}
    if not mandatory and bucket >= sample_rate:
        return None
    timestamp = datetime.now(timezone.utc)
    review_id = new_id("ta_quality_review")
    reason = f"mandatory_{level.lower()}" if mandatory else "deterministic_sample"
    conn.execute(
        """
        INSERT INTO therapeutic_assessment_quality_reviews (
            id, case_id, feedback_id, service_level, sample_reason,
            status, due_at, version, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, 'pending', ?, 1, ?, ?)
        """,
        (
            review_id,
            case["id"],
            feedback["id"],
            level,
            reason,
            (timestamp + timedelta(hours=int(level_policy["queue_sla_hours"]))).isoformat(),
            timestamp.isoformat(),
            timestamp.isoformat(),
        ),
    )
    write_audit_log(
        conn,
        "therapeutic_assessment_quality_review_enqueued",
        None,
        "therapeutic_assessment_quality_review",
        review_id,
        {"case_id": case["id"], "feedback_id": feedback["id"], "sample_reason": reason},
    )
    return _present_review(
        row_to_dict(
            conn.execute(
                "SELECT * FROM therapeutic_assessment_quality_reviews WHERE id = ?",
                (review_id,),
            ).fetchone()
        )
    )


def list_quality_queue(actor: dict, params: dict) -> dict:
    if str(actor.get("role") or "") not in REVIEW_ROLES:
        raise TherapeuticAssessmentError("forbidden", "只有督导或管理员可以查看质量队列。", 403)
    page = max(1, int(params.get("page") or 1))
    page_size = min(100, max(1, int(params.get("page_size") or 20)))
    status = str(params.get("status") or "").strip()
    where = []
    values: list[object] = []
    if status:
        if status not in OPEN_REVIEW_STATUSES | {"passed", "remediation_required"}:
            raise TherapeuticAssessmentError("validation_error", "质量复核状态无效。")
        where.append("q.status = ?")
        values.append(status)
    clause = f"WHERE {' AND '.join(where)}" if where else ""
    with get_connection() as conn:
        rows = rows_to_dicts(
            conn.execute(
                f"""
                SELECT q.*, f.author_id AS feedback_created_by,
                       c.assessment_question, c.participant_user_id,
                       c.complexity_scope, c.readiness_level
                FROM therapeutic_assessment_quality_reviews q
                JOIN therapeutic_assessment_feedback_versions f ON f.id = q.feedback_id
                JOIN therapeutic_assessment_cases c ON c.id = q.case_id
                {clause}
                ORDER BY CASE WHEN q.status IN ('pending', 'in_review') THEN 0 ELSE 1 END,
                         q.due_at, q.created_at
                """,
                tuple(values),
            ).fetchall()
        )
        from services.therapeutic_assessment_competency_service import assert_task_authorized

        visible_rows: list[dict] = []
        for row in rows:
            try:
                assert_task_authorized(
                    conn,
                    actor,
                    {
                        "id": row["case_id"],
                        "complexity_scope": row["complexity_scope"],
                        "readiness_level": row["readiness_level"],
                    },
                    "quality_review",
                )
            except TherapeuticAssessmentError as exc:
                if exc.code != "competency_authorization_required":
                    raise
                continue
            row.pop("complexity_scope", None)
            row.pop("readiness_level", None)
            visible_rows.append(row)
        total = len(visible_rows)
        rows = visible_rows[(page - 1) * page_size : page * page_size]
        write_audit_log(
            conn,
            "therapeutic_assessment_quality_queue_viewed",
            str(actor["id"]),
            "therapeutic_assessment_quality_queue",
            "quality-queue",
            {"page": page, "page_size": page_size, "status": status, "count": len(rows)},
        )
        conn.commit()
    return {
        "items": [_present_review(row) for row in rows],
        "total": total,
        "page": page,
        "page_size": page_size,
        "runtime": quality_runtime_status(),
        "policy": {
            "version": _policy()["version"],
            "review_dimensions": _policy()["review_dimensions"],
        },
    }


def claim_quality_review(
    actor: dict,
    review_id: str,
    payload: dict,
    idempotency_key: str,
) -> dict:
    key = _idempotency(idempotency_key)
    if str(actor.get("role") or "") not in REVIEW_ROLES:
        raise TherapeuticAssessmentError("forbidden", "只有督导或管理员可以认领质量复核。", 403)
    with get_connection() as conn:
        replay = conn.execute(
            "SELECT entity_id FROM therapeutic_assessment_quality_events WHERE actor_id = ? AND idempotency_key = ?",
            (str(actor["id"]), key),
        ).fetchone()
        if replay:
            row = conn.execute(
                "SELECT * FROM therapeutic_assessment_quality_reviews WHERE id = ?",
                (replay["entity_id"],),
            ).fetchone()
            return _present_review(row_to_dict(row))
        row = conn.execute(
            """
            SELECT q.*, f.author_id AS feedback_created_by,
                   c.complexity_scope, c.readiness_level
            FROM therapeutic_assessment_quality_reviews q
            JOIN therapeutic_assessment_feedback_versions f ON f.id = q.feedback_id
            JOIN therapeutic_assessment_cases c ON c.id = q.case_id
            WHERE q.id = ?
            """,
            (review_id,),
        ).fetchone()
        if row is None:
            raise TherapeuticAssessmentError("not_found", "没有找到质量复核任务。", 404)
        item = row_to_dict(row)
        from services.therapeutic_assessment_competency_service import assert_task_authorized

        assert_task_authorized(
            conn,
            actor,
            {
                "id": item["case_id"],
                "complexity_scope": item["complexity_scope"],
                "readiness_level": item["readiness_level"],
            },
            "quality_review",
        )
        if str(item["feedback_created_by"]) == str(actor["id"]):
            raise TherapeuticAssessmentError("independent_review_required", "起草者不能最终复核自己的反馈。", 409)
        expected = int(payload.get("expected_version", -1))
        if item["status"] != "pending":
            raise TherapeuticAssessmentError("invalid_state", "该质量任务当前不能认领。", 409)
        if expected != int(item["version"]):
            raise TherapeuticAssessmentError("version_conflict", "质量任务已变化，请重新读取。", 409)
        timestamp = now_iso()
        changed = conn.execute(
            """
            UPDATE therapeutic_assessment_quality_reviews
            SET status = 'in_review', claimed_by = ?, claimed_at = ?,
                version = version + 1, updated_at = ?
            WHERE id = ? AND version = ? AND status = 'pending'
            """,
            (str(actor["id"]), timestamp, timestamp, review_id, expected),
        )
        if int(changed.rowcount or 0) != 1:
            raise TherapeuticAssessmentError("version_conflict", "质量任务已被其他人认领。", 409)
        _quality_event(
            conn,
            entity_type="quality_review",
            entity_id=review_id,
            actor_id=str(actor["id"]),
            action="claimed",
            idempotency_key=key,
            before_version=expected,
            after_version=expected + 1,
            metadata={},
        )
        write_audit_log(
            conn,
            "therapeutic_assessment_quality_review_claimed",
            str(actor["id"]),
            "therapeutic_assessment_quality_review",
            review_id,
            {"case_id": item["case_id"], "feedback_id": item["feedback_id"]},
        )
        conn.commit()
        return _present_review(
            row_to_dict(
                conn.execute(
                    "SELECT * FROM therapeutic_assessment_quality_reviews WHERE id = ?",
                    (review_id,),
                ).fetchone()
            )
        )


def _validate_dimensions(payload: dict) -> tuple[dict, str, str]:
    policy = _policy()
    dimensions = payload.get("dimensions")
    if not isinstance(dimensions, dict):
        raise TherapeuticAssessmentError("validation_error", "请完整填写六项质量复核。")
    normalized: dict[str, dict[str, str]] = {}
    statuses = set(policy["dimension_statuses"])
    for name in policy["review_dimensions"]:
        entry = dimensions.get(name)
        if not isinstance(entry, dict) or str(entry.get("status") or "") not in statuses:
            raise TherapeuticAssessmentError("validation_error", f"质量维度{name}缺少有效结论。")
        status = str(entry["status"])
        note = str(entry.get("note") or "").strip()[:1000]
        evidence_ref = str(entry.get("evidence_ref") or "").strip()[:500]
        if status == "concern" and (not note or not evidence_ref):
            raise TherapeuticAssessmentError("validation_error", f"质量维度{name}标记关注时必须给出说明和依据。")
        normalized[name] = {"status": status, "note": note, "evidence_ref": evidence_ref}
    decision = str(payload.get("decision") or "")
    if decision not in set(policy["decisions"]):
        raise TherapeuticAssessmentError("validation_error", "质量复核结论无效。")
    has_concern = any(entry["status"] == "concern" for entry in normalized.values())
    if has_concern != (decision == "remediation_required"):
        raise TherapeuticAssessmentError("validation_error", "关注项与质量复核结论不一致。")
    remediation_summary = str(payload.get("remediation_summary") or "").strip()[:2000]
    if decision == "remediation_required" and not remediation_summary:
        raise TherapeuticAssessmentError("validation_error", "需要修复时必须写明问题和修复方向。")
    return normalized, decision, remediation_summary


def complete_quality_review(
    actor: dict,
    review_id: str,
    payload: dict,
    idempotency_key: str,
) -> dict:
    key = _idempotency(idempotency_key)
    dimensions, decision, remediation_summary = _validate_dimensions(payload)
    if str(actor.get("role") or "") not in REVIEW_ROLES:
        raise TherapeuticAssessmentError("forbidden", "只有督导或管理员可以完成质量复核。", 403)
    with get_connection() as conn:
        replay = conn.execute(
            "SELECT entity_id FROM therapeutic_assessment_quality_events WHERE actor_id = ? AND idempotency_key = ?",
            (str(actor["id"]), key),
        ).fetchone()
        if replay:
            row = conn.execute(
                "SELECT * FROM therapeutic_assessment_quality_reviews WHERE id = ?",
                (replay["entity_id"],),
            ).fetchone()
            return _present_review(row_to_dict(row))
        row = conn.execute(
            """
            SELECT q.*, f.author_id AS feedback_created_by,
                   c.complexity_scope, c.readiness_level
            FROM therapeutic_assessment_quality_reviews q
            JOIN therapeutic_assessment_feedback_versions f ON f.id = q.feedback_id
            JOIN therapeutic_assessment_cases c ON c.id = q.case_id
            WHERE q.id = ?
            """,
            (review_id,),
        ).fetchone()
        if row is None:
            raise TherapeuticAssessmentError("not_found", "没有找到质量复核任务。", 404)
        item = row_to_dict(row)
        from services.therapeutic_assessment_competency_service import assert_task_authorized

        assert_task_authorized(
            conn,
            actor,
            {
                "id": item["case_id"],
                "complexity_scope": item["complexity_scope"],
                "readiness_level": item["readiness_level"],
            },
            "quality_review",
        )
        if str(item["feedback_created_by"]) == str(actor["id"]):
            raise TherapeuticAssessmentError("independent_review_required", "起草者不能最终复核自己的反馈。", 409)
        expected = int(payload.get("expected_version", -1))
        if item["status"] != "in_review" or str(item.get("claimed_by") or "") != str(actor["id"]):
            raise TherapeuticAssessmentError("invalid_state", "请先由当前账号认领该质量任务。", 409)
        if expected != int(item["version"]):
            raise TherapeuticAssessmentError("version_conflict", "质量任务已变化，请重新读取。", 409)
        timestamp = now_iso()
        conn.execute(
            """
            UPDATE therapeutic_assessment_quality_reviews
            SET status = ?, decision = ?, dimensions_json = ?,
                remediation_summary = ?, completed_by = ?, completed_at = ?,
                version = version + 1, updated_at = ?
            WHERE id = ? AND version = ?
            """,
            (
                "passed" if decision == "pass" else "remediation_required",
                decision,
                json_dumps(dimensions),
                remediation_summary or None,
                str(actor["id"]),
                timestamp,
                timestamp,
                review_id,
                expected,
            ),
        )
        incident_id = None
        if decision == "remediation_required":
            incident_id = new_id("ta_quality_incident")
            conn.execute(
                """
                INSERT INTO therapeutic_assessment_quality_incidents (
                    id, case_id, feedback_id, quality_review_id, reporter_user_id,
                    source_type, category, description, requested_resolution,
                    status, idempotency_key, version, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, 'quality_sample', 'quality_review', ?,
                          '请完成影响分析、修复、通知与独立复核', 'reported', ?, 1, ?, ?)
                """,
                (
                    incident_id,
                    item["case_id"],
                    item["feedback_id"],
                    review_id,
                    str(actor["id"]),
                    remediation_summary,
                    f"{key}:incident",
                    timestamp,
                    timestamp,
                ),
            )
        _quality_event(
            conn,
            entity_type="quality_review",
            entity_id=review_id,
            actor_id=str(actor["id"]),
            action="completed",
            idempotency_key=key,
            before_version=expected,
            after_version=expected + 1,
            metadata={"decision": decision, "incident_id": incident_id},
        )
        write_audit_log(
            conn,
            "therapeutic_assessment_quality_review_completed",
            str(actor["id"]),
            "therapeutic_assessment_quality_review",
            review_id,
            {"decision": decision, "incident_id": incident_id},
        )
        conn.commit()
        result = _present_review(
            row_to_dict(
                conn.execute(
                    "SELECT * FROM therapeutic_assessment_quality_reviews WHERE id = ?",
                    (review_id,),
                ).fetchone()
            )
        )
        result["incident_id"] = incident_id
        return result


def create_quality_incident(
    actor: dict,
    case_id: str,
    payload: dict,
    idempotency_key: str,
) -> tuple[dict, int]:
    key = _idempotency(idempotency_key)
    policy = _policy()
    category = str(payload.get("category") or "")
    if category not in set(policy["incident_categories"]) - {"quality_review"}:
        raise TherapeuticAssessmentError("validation_error", "问题类型无效。")
    description = str(payload.get("description") or "").strip()
    requested_resolution = str(payload.get("requested_resolution") or "").strip()
    if not description or len(description) > 4000 or not requested_resolution or len(requested_resolution) > 1000:
        raise TherapeuticAssessmentError("validation_error", "请完整填写问题说明和希望的处理方式。")
    feedback_id = str(payload.get("feedback_id") or "").strip() or None
    with get_connection() as conn:
        replay = conn.execute(
            """
            SELECT * FROM therapeutic_assessment_quality_incidents
            WHERE reporter_user_id = ? AND idempotency_key = ?
            """,
            (str(actor["id"]), key),
        ).fetchone()
        if replay:
            return _present_incident(row_to_dict(replay)), 200
        case = _case_row(conn, case_id)
        _assert_read(actor, case)
        if str(actor.get("role") or "") in {"parent", "student"} and str(actor["id"]) != str(case["participant_user_id"]):
            raise TherapeuticAssessmentError("forbidden", "只能为自己的协作记录提交更正或投诉。", 403)
        if feedback_id:
            feedback = conn.execute(
                "SELECT id FROM therapeutic_assessment_feedback_versions WHERE id = ? AND case_id = ?",
                (feedback_id, case_id),
            ).fetchone()
            if feedback is None:
                raise TherapeuticAssessmentError("validation_error", "所选反馈不属于本次协作记录。", 422)
        incident_id = new_id("ta_quality_incident")
        timestamp = now_iso()
        source_type = "participant_report" if str(actor.get("role") or "") in {"parent", "student"} else "staff_report"
        conn.execute(
            """
            INSERT INTO therapeutic_assessment_quality_incidents (
                id, case_id, feedback_id, reporter_user_id, source_type,
                category, description, requested_resolution, status,
                idempotency_key, version, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'reported', ?, 1, ?, ?)
            """,
            (
                incident_id,
                case_id,
                feedback_id,
                str(actor["id"]),
                source_type,
                category,
                description,
                requested_resolution,
                key,
                timestamp,
                timestamp,
            ),
        )
        _quality_event(
            conn,
            entity_type="quality_incident",
            entity_id=incident_id,
            actor_id=str(actor["id"]),
            action="reported",
            idempotency_key=key,
            before_version=None,
            after_version=1,
            metadata={"category": category, "feedback_id": feedback_id},
        )
        write_audit_log(
            conn,
            "therapeutic_assessment_quality_incident_reported",
            str(actor["id"]),
            "therapeutic_assessment_quality_incident",
            incident_id,
            {"case_id": case_id, "category": category, "source_type": source_type},
        )
        conn.commit()
        row = conn.execute(
            "SELECT * FROM therapeutic_assessment_quality_incidents WHERE id = ?",
            (incident_id,),
        ).fetchone()
        return _present_incident(row_to_dict(row)), 201


def list_quality_incidents(actor: dict, params: dict) -> dict:
    case_id = str(params.get("case_id") or "").strip()
    status = str(params.get("status") or "").strip()
    where: list[str] = []
    values: list[object] = []
    role = str(actor.get("role") or "")
    if role in {"parent", "student"}:
        where.append("c.participant_user_id = ?")
        values.append(str(actor["id"]))
    elif role == "researcher":
        where.append("c.assigned_researcher_id = ?")
        values.append(str(actor["id"]))
    elif role not in REVIEW_ROLES:
        raise TherapeuticAssessmentError("forbidden", "当前账号不能查看质量事件。", 403)
    if case_id:
        where.append("i.case_id = ?")
        values.append(case_id)
    if status:
        if status not in OPEN_INCIDENT_STATUSES | {"resolved"}:
            raise TherapeuticAssessmentError("validation_error", "质量事件状态无效。")
        where.append("i.status = ?")
        values.append(status)
    clause = " AND ".join(where) if where else "1 = 1"
    with get_connection() as conn:
        rows = rows_to_dicts(
            conn.execute(
                f"""
                SELECT i.*, c.complexity_scope, c.readiness_level
                FROM therapeutic_assessment_quality_incidents i
                JOIN therapeutic_assessment_cases c ON c.id = i.case_id
                WHERE {clause}
                ORDER BY CASE WHEN i.status = 'resolved' THEN 1 ELSE 0 END, i.created_at DESC
                """,
                tuple(values),
            ).fetchall()
        )
        if role in REVIEW_ROLES:
            from services.therapeutic_assessment_competency_service import assert_task_authorized

            visible_rows: list[dict] = []
            for row in rows:
                authorized = False
                for task_code in ("quality_incident_analysis", "quality_incident_resolution"):
                    try:
                        assert_task_authorized(
                            conn,
                            actor,
                            {
                                "id": row["case_id"],
                                "complexity_scope": row["complexity_scope"],
                                "readiness_level": row["readiness_level"],
                            },
                            task_code,
                        )
                        authorized = True
                        break
                    except TherapeuticAssessmentError as exc:
                        if exc.code != "competency_authorization_required":
                            raise
                if authorized:
                    row.pop("complexity_scope", None)
                    row.pop("readiness_level", None)
                    visible_rows.append(row)
            rows = visible_rows
        write_audit_log(
            conn,
            "therapeutic_assessment_quality_incidents_viewed",
            str(actor["id"]),
            "therapeutic_assessment_quality_incident",
            case_id or "quality-incidents",
            {"count": len(rows), "status": status},
        )
        conn.commit()
    return {"items": [_present_incident(row) for row in rows], "count": len(rows)}


def analyze_quality_incident(
    actor: dict,
    incident_id: str,
    payload: dict,
    idempotency_key: str,
) -> dict:
    key = _idempotency(idempotency_key)
    if str(actor.get("role") or "") not in REVIEW_ROLES:
        raise TherapeuticAssessmentError("forbidden", "只有督导或管理员可以完成影响分析。", 403)
    analysis = payload.get("impact_analysis")
    required = {"severity", "affected_scope", "affected_participant_count", "immediate_action", "evidence_refs"}
    if not isinstance(analysis, dict) or not required.issubset(analysis):
        raise TherapeuticAssessmentError("validation_error", "影响分析必须包含严重度、影响范围、人数、立即措施和依据。")
    if str(analysis.get("severity") or "") not in {"low", "medium", "high", "critical"}:
        raise TherapeuticAssessmentError("validation_error", "影响严重度无效。")
    if not isinstance(analysis.get("evidence_refs"), list) or not analysis["evidence_refs"]:
        raise TherapeuticAssessmentError("validation_error", "影响分析至少需要一条依据。")
    with get_connection() as conn:
        replay = conn.execute(
            "SELECT entity_id FROM therapeutic_assessment_quality_events WHERE actor_id = ? AND idempotency_key = ?",
            (str(actor["id"]), key),
        ).fetchone()
        if replay:
            row = conn.execute(
                "SELECT * FROM therapeutic_assessment_quality_incidents WHERE id = ?",
                (replay["entity_id"],),
            ).fetchone()
            return _present_incident(row_to_dict(row))
        row = conn.execute(
            """
            SELECT i.*, c.participant_user_id, c.complexity_scope,
                   c.readiness_level, f.author_id AS feedback_created_by
            FROM therapeutic_assessment_quality_incidents i
            JOIN therapeutic_assessment_cases c ON c.id = i.case_id
            LEFT JOIN therapeutic_assessment_feedback_versions f ON f.id = i.feedback_id
            WHERE i.id = ?
            """,
            (incident_id,),
        ).fetchone()
        if row is None:
            raise TherapeuticAssessmentError("not_found", "没有找到质量事件。", 404)
        item = row_to_dict(row)
        from services.therapeutic_assessment_competency_service import assert_task_authorized

        assert_task_authorized(
            conn,
            actor,
            {
                "id": item["case_id"],
                "complexity_scope": item["complexity_scope"],
                "readiness_level": item["readiness_level"],
            },
            "quality_incident_analysis",
        )
        if str(item.get("feedback_created_by") or "") == str(actor["id"]):
            raise TherapeuticAssessmentError("independent_review_required", "反馈起草者不能分析自己的质量事件。", 409)
        expected = int(payload.get("expected_version", -1))
        if item["status"] != "reported":
            raise TherapeuticAssessmentError("invalid_state", "该事件当前不能重复分析。", 409)
        if expected != int(item["version"]):
            raise TherapeuticAssessmentError("version_conflict", "质量事件已变化，请重新读取。", 409)
        timestamp = now_iso()
        conn.execute(
            """
            UPDATE therapeutic_assessment_quality_incidents
            SET status = 'independent_review', impact_analysis_json = ?,
                analyzed_by = ?, analyzed_at = ?, version = version + 1,
                updated_at = ?
            WHERE id = ? AND version = ?
            """,
            (json_dumps(analysis), str(actor["id"]), timestamp, timestamp, incident_id, expected),
        )
        _quality_event(
            conn,
            entity_type="quality_incident",
            entity_id=incident_id,
            actor_id=str(actor["id"]),
            action="impact_analyzed",
            idempotency_key=key,
            before_version=expected,
            after_version=expected + 1,
            metadata={"severity": analysis["severity"]},
        )
        write_audit_log(
            conn,
            "therapeutic_assessment_quality_incident_analyzed",
            str(actor["id"]),
            "therapeutic_assessment_quality_incident",
            incident_id,
            {"severity": analysis["severity"], "affected_participant_count": analysis["affected_participant_count"]},
        )
        conn.commit()
        return _present_incident(
            row_to_dict(
                conn.execute(
                    "SELECT * FROM therapeutic_assessment_quality_incidents WHERE id = ?",
                    (incident_id,),
                ).fetchone()
            )
        )


def resolve_quality_incident(
    actor: dict,
    incident_id: str,
    payload: dict,
    idempotency_key: str,
) -> dict:
    key = _idempotency(idempotency_key)
    policy = _policy()
    action = str(payload.get("resolution_action") or "")
    if action not in set(policy["resolution_actions"]):
        raise TherapeuticAssessmentError("validation_error", "修复动作无效。")
    summary = str(payload.get("resolution_summary") or "").strip()
    if not summary or len(summary) > 2000:
        raise TherapeuticAssessmentError("validation_error", "请填写不超过2000字的处理说明。")
    blocked = [
        phrase
        for phrase in load_content_json("therapeutic_assessment_feedback_policy.json").get("blocked_phrases") or []
        if phrase in summary
    ]
    if blocked:
        raise TherapeuticAssessmentError("feedback_language_blocked", "处理说明包含不适合直接展示的表达。", 422)
    replacement_feedback_id = str(payload.get("replacement_feedback_id") or "").strip() or None
    with get_connection() as conn:
        replay = conn.execute(
            "SELECT entity_id FROM therapeutic_assessment_quality_events WHERE actor_id = ? AND idempotency_key = ?",
            (str(actor["id"]), key),
        ).fetchone()
        if replay:
            row = conn.execute(
                "SELECT * FROM therapeutic_assessment_quality_incidents WHERE id = ?",
                (replay["entity_id"],),
            ).fetchone()
            return _present_incident(row_to_dict(row))
        row = conn.execute(
            """
            SELECT i.*, c.participant_user_id, c.complexity_scope,
                   c.readiness_level, f.author_id AS feedback_created_by,
                   f.status AS feedback_status, f.lifecycle_version AS feedback_lifecycle_version
            FROM therapeutic_assessment_quality_incidents i
            JOIN therapeutic_assessment_cases c ON c.id = i.case_id
            LEFT JOIN therapeutic_assessment_feedback_versions f ON f.id = i.feedback_id
            WHERE i.id = ?
            """,
            (incident_id,),
        ).fetchone()
        if row is None:
            raise TherapeuticAssessmentError("not_found", "没有找到质量事件。", 404)
        item = row_to_dict(row)
        if str(actor.get("role") or "") not in REVIEW_ROLES:
            raise TherapeuticAssessmentError("forbidden", "只有督导或管理员可以完成独立复核。", 403)
        from services.therapeutic_assessment_competency_service import assert_task_authorized

        assert_task_authorized(
            conn,
            actor,
            {
                "id": item["case_id"],
                "complexity_scope": item["complexity_scope"],
                "readiness_level": item["readiness_level"],
            },
            "quality_incident_resolution",
        )
        if str(actor["id"]) in {
            str(item["reporter_user_id"]),
            str(item.get("feedback_created_by") or ""),
            str(item.get("analyzed_by") or ""),
        }:
            raise TherapeuticAssessmentError("independent_review_required", "最终复核者必须独立于报告、起草和影响分析人员。", 409)
        expected = int(payload.get("expected_version", -1))
        if item["status"] != "independent_review":
            raise TherapeuticAssessmentError("invalid_state", "该事件尚未完成影响分析或已经关闭。", 409)
        if expected != int(item["version"]):
            raise TherapeuticAssessmentError("version_conflict", "质量事件已变化，请重新读取。", 409)
        if action == "correct":
            replacement = conn.execute(
                """
                SELECT id FROM therapeutic_assessment_feedback_versions
                WHERE id = ? AND case_id = ? AND supersedes_feedback_id = ? AND status = 'sent'
                """,
                (replacement_feedback_id, item["case_id"], item.get("feedback_id")),
            ).fetchone()
            if replacement is None:
                raise TherapeuticAssessmentError(
                    "replacement_feedback_required",
                    "更正完成前必须先发送一份明确承接原版本的修订反馈。",
                    409,
                )
        timestamp = now_iso()
        if action == "withdraw" and item.get("feedback_id"):
            conn.execute(
                """
                UPDATE therapeutic_assessment_feedback_versions
                SET status = 'withdrawn', participant_status = 'withdrawn',
                    withdrawn_at = ?, withdrawal_reason = ?,
                    lifecycle_version = lifecycle_version + 1
                WHERE id = ? AND status != 'withdrawn'
                """,
                (timestamp, summary, item["feedback_id"]),
            )
            conn.execute(
                """
                UPDATE therapeutic_assessment_feedback_deliveries
                SET status = 'withdrawn', withdrawn_by = ?, withdrawn_at = ?,
                    withdrawal_reason = ?
                WHERE feedback_id = ? AND status = 'sent'
                """,
                (str(actor["id"]), timestamp, summary, item["feedback_id"]),
            )
        conn.execute(
            """
            UPDATE therapeutic_assessment_quality_incidents
            SET status = 'resolved', resolution_action = ?,
                replacement_feedback_id = ?, notification_status = 'sent',
                notified_at = ?, independent_reviewer_id = ?,
                resolution_summary = ?, version = version + 1, updated_at = ?
            WHERE id = ? AND version = ?
            """,
            (
                action,
                replacement_feedback_id,
                timestamp,
                str(actor["id"]),
                summary,
                timestamp,
                incident_id,
                expected,
            ),
        )
        create_message(
            conn,
            str(item["participant_user_id"]),
            "你提交的更正或投诉已有处理结果",
            "处理记录已更新。你可以在本次协作的“更正与投诉”中查看，也可以继续提出异议。",
            message_type="therapeutic_assessment_quality",
            source_type="therapeutic_assessment_quality_incident",
            source_id=incident_id,
            sender_id=str(actor["id"]),
            sender_role=str(actor.get("role") or ""),
            idempotency_key=f"quality-resolution:{incident_id}:{expected + 1}",
        )
        _quality_event(
            conn,
            entity_type="quality_incident",
            entity_id=incident_id,
            actor_id=str(actor["id"]),
            action="resolved",
            idempotency_key=key,
            before_version=expected,
            after_version=expected + 1,
            metadata={"resolution_action": action, "replacement_feedback_id": replacement_feedback_id},
        )
        write_audit_log(
            conn,
            "therapeutic_assessment_quality_incident_resolved",
            str(actor["id"]),
            "therapeutic_assessment_quality_incident",
            incident_id,
            {
                "resolution_action": action,
                "participant_notified": True,
                "original_history_preserved": True,
            },
        )
        conn.commit()
        return _present_incident(
            row_to_dict(
                conn.execute(
                    "SELECT * FROM therapeutic_assessment_quality_incidents WHERE id = ?",
                    (incident_id,),
                ).fetchone()
            )
        )
