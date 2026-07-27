"""Report module for generation, review, delivery and collaborative hypothesis checks."""

from __future__ import annotations

from database import get_connection, json_dumps, new_id, now_iso, row_to_dict, rows_to_dicts, write_audit_log
from services.message_service import create_message
from services.risk_service import check_text_risk
from services.relationship_pilot_common import (
    BOUNDARY,
    RESEARCH_ROLES,
    REPORT_VERSION,
    RelationshipPilotError,
    ServiceResult,
    enrollment_by_id,
    ensure_researcher_assignment,
    ensure_researcher_access,
    expand_enrollment,
    expand_report,
    four_layer_profile,
    own_or_researcher,
    public_report_payload,
)


def create_report(actor: dict, enrollment_id: str) -> ServiceResult:
    with get_connection() as conn:
        enrollment = enrollment_by_id(conn, enrollment_id)
        if not enrollment:
            raise RelationshipPilotError("not_found", "没有找到报名记录。", 404)
        if not own_or_researcher(actor, enrollment["user_id"]):
            raise RelationshipPilotError("forbidden", "无权生成该报告。", 403)
        existing = conn.execute(
            "SELECT * FROM relationship_screening_reports WHERE enrollment_id = ? AND version = ? LIMIT 1",
            (enrollment_id, REPORT_VERSION),
        ).fetchone()
        if existing:
            ensure_researcher_access(actor, enrollment)
            return ServiceResult(expand_report(row_to_dict(existing)))
        if actor.get("role") == "researcher":
            enrollment = ensure_researcher_assignment(conn, actor, enrollment)
        expanded = expand_enrollment(enrollment)
        profile = expanded["profile"]
        report_payload = {
            "title": "关系健康初筛报告",
            "worksheet_id": expanded["worksheet_id"],
            "assessment_result_id": expanded["assessment_result_id"],
            "dimensions": expanded["dimensions"],
            "radar_features": expanded["radar_features"],
            "profile_name": profile.get("profile_name") or "阶段性关系探索位置",
            "profile_description": profile.get("profile_description") or "本次结果暂只作为位置参考。",
            "confidence": profile.get("confidence"),
            "interpretation_status": profile.get("interpretation_status"),
            "personalized_interpretation": "请把维度、画像和现实体验放在一起讨论，不用追求一次得到固定结论。",
            "suggested_assessment_questions": profile.get("suggested_assessment_questions", []),
            "recommended_project_tasks": profile.get("recommended_project_tasks", []),
            "four_layer_profile": four_layer_profile(expanded),
            "boundary_notice": profile.get("boundary_notice") or BOUNDARY,
            "generated_at": now_iso(),
            "version": REPORT_VERSION,
        }
        report_id = new_id("rel_report")
        timestamp = now_iso()
        try:
            conn.execute(
                """
                INSERT INTO relationship_screening_reports (
                    id, enrollment_id, user_id, assessment_result_id, status, version, report_json,
                    confirmed_by, confirmed_at, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, NULL, NULL, ?, ?)
                """,
                (report_id, enrollment_id, enrollment["user_id"], enrollment["assessment_result_id"], enrollment["review_status"], REPORT_VERSION, json_dumps(report_payload), timestamp, timestamp),
            )
        except Exception:
            existing = conn.execute(
                "SELECT * FROM relationship_screening_reports WHERE enrollment_id = ? AND version = ? LIMIT 1",
                (enrollment_id, REPORT_VERSION),
            ).fetchone()
            if existing:
                return ServiceResult(expand_report(row_to_dict(existing)))
            raise
        write_audit_log(conn, "relationship_report_generated", actor["id"], "relationship_screening_report", report_id, {"enrollment_id": enrollment_id, "status": enrollment["review_status"]})
        conn.commit()
        row = conn.execute("SELECT * FROM relationship_screening_reports WHERE id = ?", (report_id,)).fetchone()
    return ServiceResult(expand_report(row_to_dict(row)), 201)


def get_report(actor: dict, report_id: str, download: bool = False) -> ServiceResult:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM relationship_screening_reports WHERE id = ?", (report_id,)).fetchone()
        if not row:
            raise RelationshipPilotError("not_found", "没有找到报告。", 404)
        item = expand_report(row_to_dict(row))
        if not own_or_researcher(actor, item["user_id"]):
            raise RelationshipPilotError("forbidden", "无权查看该报告。", 403)
        enrollment = enrollment_by_id(conn, item["enrollment_id"])
        ensure_researcher_access(actor, enrollment)
        is_researcher = actor.get("role") in RESEARCH_ROLES
        if not is_researcher and item["status"] != "sent":
            if download:
                raise RelationshipPilotError("report_not_delivered", "报告尚未完成人工确认和发送。", 409)
            write_audit_log(
                conn,
                "relationship_report_pending_viewed",
                actor["id"],
                "relationship_screening_report",
                report_id,
                {"status": item["status"]},
            )
            conn.commit()
            return ServiceResult(
                {
                    "id": item["id"],
                    "enrollment_id": item["enrollment_id"],
                    "user_id": item["user_id"],
                    "status": item["status"],
                    "version": item["version"],
                    "delivery_pending": True,
                    "report": {
                        "title": "阶段性报告正在人工复核",
                        "boundary_notice": BOUNDARY,
                    },
                    "hypothesis_feedback": [],
                    "sent_at": None,
                }
            )
        sent_row = conn.execute(
            "SELECT created_at FROM messages WHERE user_id = ? AND source_type = 'relationship_screening_report' AND source_id = ? ORDER BY created_at DESC LIMIT 1",
            (item["user_id"], report_id),
        ).fetchone()
        item["sent_at"] = sent_row["created_at"] if sent_row else None
        item["hypothesis_feedback"] = rows_to_dicts(
            conn.execute(
                "SELECT hypothesis_index, response, updated_at FROM relationship_hypothesis_feedback WHERE report_id = ? AND user_id = ? ORDER BY hypothesis_index",
                (report_id, item["user_id"]),
            ).fetchall()
        )
        write_audit_log(conn, "relationship_report_viewed", actor["id"], "relationship_screening_report", report_id, {"download": download})
        conn.commit()
    return ServiceResult(public_report_payload(item) if download else item)


def save_hypothesis_feedback(actor: dict, report_id: str, hypothesis_index: int, response: str) -> ServiceResult:
    if response not in {"matches", "does_not_match", "uncertain"}:
        raise RelationshipPilotError("validation_error", "请选择符合、不符合或不确定。")
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM relationship_screening_reports WHERE id = ?", (report_id,)).fetchone()
        if not row:
            raise RelationshipPilotError("not_found", "没有找到报告。", 404)
        item = expand_report(row_to_dict(row))
        if str(actor["id"]) != str(item["user_id"]):
            raise RelationshipPilotError("forbidden", "只能核对自己的阶段性假设。", 403)
        if item["status"] != "sent":
            raise RelationshipPilotError("report_not_delivered", "报告完成人工确认并发送后才能核对。", 409)
        hypotheses = (((item.get("report") or {}).get("four_layer_profile") or {}).get("mechanism") or {}).get("hypotheses") or []
        if hypothesis_index < 0 or hypothesis_index >= len(hypotheses):
            raise RelationshipPilotError("validation_error", "没有找到这条待核对假设。")
        timestamp = now_iso()
        existing = conn.execute(
            "SELECT id FROM relationship_hypothesis_feedback WHERE report_id = ? AND user_id = ? AND hypothesis_index = ?",
            (report_id, item["user_id"], hypothesis_index),
        ).fetchone()
        if existing:
            feedback_id = existing["id"]
            conn.execute("UPDATE relationship_hypothesis_feedback SET response = ?, updated_at = ? WHERE id = ?", (response, timestamp, feedback_id))
        else:
            feedback_id = new_id("rel_hyp")
            try:
                conn.execute(
                    "INSERT INTO relationship_hypothesis_feedback (id, report_id, enrollment_id, user_id, hypothesis_index, response, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (feedback_id, report_id, item["enrollment_id"], item["user_id"], hypothesis_index, response, timestamp, timestamp),
                )
            except Exception:
                existing = conn.execute(
                    "SELECT id FROM relationship_hypothesis_feedback WHERE report_id = ? AND user_id = ? AND hypothesis_index = ?",
                    (report_id, item["user_id"], hypothesis_index),
                ).fetchone()
                if not existing:
                    raise
                feedback_id = existing["id"]
                conn.execute("UPDATE relationship_hypothesis_feedback SET response = ?, updated_at = ? WHERE id = ?", (response, timestamp, feedback_id))
        write_audit_log(conn, "relationship_hypothesis_feedback_saved", actor["id"], "relationship_screening_report", report_id, {"hypothesis_index": hypothesis_index, "response": response})
        conn.commit()
    return ServiceResult({"hypothesis_index": hypothesis_index, "response": response, "updated_at": timestamp})


def confirm_report(actor: dict, report_id: str) -> ServiceResult:
    timestamp = now_iso()
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM relationship_screening_reports WHERE id = ?", (report_id,)).fetchone()
        if not row:
            raise RelationshipPilotError("not_found", "没有找到报告。", 404)
        enrollment = enrollment_by_id(conn, row["enrollment_id"])
        ensure_researcher_assignment(conn, actor, enrollment)
        if row["status"] in {"sent", "updated"}:
            conn.commit()
            return ServiceResult(expand_report(row_to_dict(row)))
        conn.execute("UPDATE relationship_screening_reports SET status = 'confirmed', confirmed_by = ?, confirmed_at = ?, updated_at = ? WHERE id = ?", (actor["id"], timestamp, timestamp, report_id))
        write_audit_log(conn, "relationship_report_confirmed", actor["id"], "relationship_screening_report", report_id)
        conn.commit()
        updated = conn.execute("SELECT * FROM relationship_screening_reports WHERE id = ?", (report_id,)).fetchone()
    return ServiceResult(expand_report(row_to_dict(updated)))


def update_report(actor: dict, report_id: str, payload: dict) -> ServiceResult:
    allowed_fields = {
        "profile_description",
        "personalized_interpretation",
        "suggested_assessment_questions",
        "recommended_project_tasks",
    }
    version = str(payload.get("version") or "").strip()
    changes = {key: payload[key] for key in allowed_fields if key in payload}
    if not version or len(version) > 120:
        raise RelationshipPilotError("validation_error", "更新报告时需要提供新的版本号。")
    if not changes:
        raise RelationshipPilotError("validation_error", "没有可更新的用户可见报告内容。")
    for key in {"profile_description", "personalized_interpretation"} & changes.keys():
        value = changes[key]
        if not isinstance(value, str) or not value.strip() or len(value.strip()) > 2000:
            raise RelationshipPilotError("validation_error", "报告文字内容需为1至2000个字符。")
        changes[key] = value.strip()
    for key in {"suggested_assessment_questions", "recommended_project_tasks"} & changes.keys():
        value = changes[key]
        if (
            not isinstance(value, list)
            or len(value) > 20
            or any(not isinstance(item, str) or not item.strip() or len(item.strip()) > 500 for item in value)
        ):
            raise RelationshipPilotError("validation_error", "报告问题和任务必须使用文字列表。")
        changes[key] = [item.strip() for item in value]
    risk = check_text_risk(
        [value for value in changes.values() if isinstance(value, str)]
        + [item for value in changes.values() if isinstance(value, list) for item in value],
        source="relationship_stage_feedback",
    )
    if risk.get("risk_level") == "high" and actor.get("role") == "researcher":
        raise RelationshipPilotError("report_requires_supervisor_review", "阶段性反馈包含需要督导复核的高风险表述。", 409)
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM relationship_screening_reports WHERE id = ?", (report_id,)).fetchone()
        if not row:
            raise RelationshipPilotError("not_found", "没有找到报告。", 404)
        if row["status"] not in {"confirmed", "sent", "updated"}:
            raise RelationshipPilotError("report_not_confirmed", "报告需先完成人工确认才能更新。", 409)
        enrollment = enrollment_by_id(conn, row["enrollment_id"])
        ensure_researcher_assignment(conn, actor, enrollment)
        if version == row["version"]:
            raise RelationshipPilotError("version_conflict", "请使用新的报告版本号。", 409)
        report = expand_report(row_to_dict(row))["report"]
        report.update(changes)
        report["version"] = version
        timestamp = now_iso()
        updated_report_id = new_id("rel_report")
        try:
            conn.execute(
                """
                INSERT INTO relationship_screening_reports (
                    id, enrollment_id, user_id, assessment_result_id, status, version, report_json,
                    confirmed_by, confirmed_at, created_at, updated_at
                ) VALUES (?, ?, ?, ?, 'updated', ?, ?, ?, ?, ?, ?)
                """,
                (
                    updated_report_id,
                    row["enrollment_id"],
                    row["user_id"],
                    row["assessment_result_id"],
                    version,
                    json_dumps(report),
                    actor["id"],
                    timestamp,
                    timestamp,
                    timestamp,
                ),
            )
        except Exception as exc:
            raise RelationshipPilotError("version_conflict", "同一报名记录下的报告版本不能重复。", 409) from exc
        write_audit_log(
            conn,
            "relationship_report_updated",
            actor["id"],
            "relationship_screening_report",
            updated_report_id,
            {"base_report_id": report_id, "version": version, "updated_fields": sorted(changes), "risk_level": risk.get("risk_level")},
        )
        conn.commit()
        updated = conn.execute("SELECT * FROM relationship_screening_reports WHERE id = ?", (updated_report_id,)).fetchone()
    return ServiceResult(expand_report(row_to_dict(updated)))


def send_report(actor: dict, report_id: str) -> ServiceResult:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM relationship_screening_reports WHERE id = ?", (report_id,)).fetchone()
        if not row:
            raise RelationshipPilotError("not_found", "没有找到报告。", 404)
        enrollment = enrollment_by_id(conn, row["enrollment_id"])
        ensure_researcher_assignment(conn, actor, enrollment)
        existing = conn.execute(
            "SELECT * FROM messages WHERE user_id = ? AND source_type = 'relationship_screening_report' AND source_id = ? ORDER BY created_at DESC LIMIT 1",
            (row["user_id"], report_id),
        ).fetchone()
        if existing and row["status"] != "updated":
            if row["status"] != "sent":
                conn.execute("UPDATE relationship_screening_reports SET status = 'sent', updated_at = ? WHERE id = ?", (now_iso(), report_id))
                conn.commit()
            item = row_to_dict(existing)
            item["already_sent"] = True
            conn.commit()
            return ServiceResult(item)
        if row["status"] not in {"confirmed", "updated"}:
            raise RelationshipPilotError("report_not_confirmed", "报告需人工确认后才能发送。", 409)
        is_stage_feedback = row["status"] == "updated"
        message = create_message(
            conn,
            row["user_id"],
            "阶段性反馈已送达" if is_stage_feedback else "关系健康初筛报告已送达",
            (f"报告版本 {row['version']} 已补充研究者阶段性反馈，请在小程序内查看。" if is_stage_feedback else f"报告版本 {row['version']} 已由研究者确认。请在小程序内查看报告摘要、评估问题和边界说明。"),
            "relationship_stage_feedback" if is_stage_feedback else "relationship_report",
            "relationship_screening_report",
            report_id,
            sender_id=str(actor["id"]),
            sender_role=str(actor.get("role") or "researcher"),
            idempotency_key=f"relationship-report:{report_id}:{row['version']}",
        )
        conn.execute("UPDATE relationship_screening_reports SET status = 'sent', updated_at = ? WHERE id = ?", (now_iso(), report_id))
        write_audit_log(conn, "relationship_report_sent", actor["id"], "relationship_screening_report", report_id, {"recipient_user_id": row["user_id"], "message_id": message["id"]})
        conn.commit()
    return ServiceResult(message, 201)
