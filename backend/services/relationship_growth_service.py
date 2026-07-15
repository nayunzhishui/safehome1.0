"""Longitudinal growth module for relationship-pilot records, curves and researcher queues."""

from __future__ import annotations

from database import get_connection, json_dumps, json_loads, new_id, now_iso, row_to_dict, rows_to_dicts, write_audit_log
from services.relationship_pilot_common import (
    RelationshipPilotError,
    ServiceResult,
    dimension_lookup,
    enrollment_by_id,
    expand_enrollment,
    ensure_researcher_access,
    four_layer_profile,
)
from services.risk_review_service import create_risk_review_record
from services.risk_service import check_text_risk


def create_longitudinal_entry(actor: dict, enrollment_id: str, payload: dict, idempotency_key: str = "") -> ServiceResult:
    entry_type = str(payload.get("entry_type") or "weekly_supplement")
    if entry_type not in {"weekly_supplement", "key_event"}:
        raise RelationshipPilotError("validation_error", "不支持该连续记录类型。")
    measures = payload.get("measures") or {}
    narratives = payload.get("narratives") or {}
    if entry_type == "weekly_supplement":
        required = {"active_social_count", "authentic_expression_count", "setback_coping", "approach_willingness", "worry_intensity"}
        if not required <= set(measures):
            raise RelationshipPilotError("validation_error", "补充测量字段不完整。")
        try:
            social_count = int(measures["active_social_count"])
            expression_count = int(measures["authentic_expression_count"])
            willingness = int(measures["approach_willingness"])
            worry = int(measures["worry_intensity"])
        except (TypeError, ValueError) as exc:
            raise RelationshipPilotError("validation_error", "补充测量必须使用有效数字。") from exc
        if social_count < 0 or expression_count < 0 or willingness not in range(1, 6) or worry not in range(1, 6):
            raise RelationshipPilotError("validation_error", "次数不能为负，意愿和担忧强度需为1到5。")
        measures = {**measures, "active_social_count": social_count, "authentic_expression_count": expression_count, "approach_willingness": willingness, "worry_intensity": worry}
    elif not str(narratives.get("event_summary") or "").strip():
        raise RelationshipPilotError("validation_error", "关键事件记录不能为空。")
    text_values = [str(value) for value in narratives.values()] + [str(measures.get("setback_coping") or "")]
    risk = check_text_risk(text_values, source="relationship_longitudinal")
    idempotency_key = str(idempotency_key or "").strip()[:128]
    with get_connection() as conn:
        enrollment = enrollment_by_id(conn, enrollment_id)
        if not enrollment:
            raise RelationshipPilotError("not_found", "没有找到报名记录。", 404)
        if str(actor["id"]) != str(enrollment["user_id"]):
            raise RelationshipPilotError("forbidden", "只能保存自己的连续记录。", 403)
        if idempotency_key:
            existing = conn.execute(
                "SELECT * FROM relationship_longitudinal_entries WHERE user_id = ? AND idempotency_key = ?",
                (enrollment["user_id"], idempotency_key),
            ).fetchone()
            if existing:
                item = row_to_dict(existing)
                if item["enrollment_id"] != enrollment_id or item["entry_type"] != entry_type:
                    raise RelationshipPilotError("idempotency_conflict", "该提交标识已用于其它记录。", 409)
                item["measures"] = json_loads(item.get("measures_json"), {})
                item["narratives"] = json_loads(item.get("narratives_json"), {})
                return ServiceResult(item)
        entry_id = new_id("rel_long")
        timestamp = now_iso()
        try:
            conn.execute(
                """
                INSERT INTO relationship_longitudinal_entries (
                    id, enrollment_id, user_id, entry_type, measures_json, narratives_json,
                    event_at, risk_level, review_status, idempotency_key, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (entry_id, enrollment_id, enrollment["user_id"], entry_type, json_dumps(measures), json_dumps(narratives), payload.get("event_at") or timestamp, risk["risk_level"], "priority_review" if risk["requires_review"] else "recorded", idempotency_key or None, timestamp, timestamp),
            )
        except Exception:
            if idempotency_key:
                existing = conn.execute(
                    "SELECT * FROM relationship_longitudinal_entries WHERE user_id = ? AND idempotency_key = ?",
                    (enrollment["user_id"], idempotency_key),
                ).fetchone()
                if existing:
                    item = row_to_dict(existing)
                    item["measures"] = json_loads(item.get("measures_json"), {})
                    item["narratives"] = json_loads(item.get("narratives_json"), {})
                    return ServiceResult(item)
            raise
        create_risk_review_record(conn, enrollment["user_id"], "relationship_longitudinal_entry", entry_id, risk)
        write_audit_log(conn, "relationship_longitudinal_recorded", actor["id"], "relationship_longitudinal_entry", entry_id, {"entry_type": entry_type, "risk_level": risk["risk_level"]})
        conn.commit()
        row = conn.execute("SELECT * FROM relationship_longitudinal_entries WHERE id = ?", (entry_id,)).fetchone()
    item = row_to_dict(row)
    item["measures"] = json_loads(item.get("measures_json"), {})
    item["narratives"] = json_loads(item.get("narratives_json"), {})
    item["boundary_notice"] = "连续记录只用于观察变化和探索线索，不构成风险评估或疗效证明。"
    return ServiceResult(item, 201)


def get_growth(actor: dict, requested_user_id: str = "") -> ServiceResult:
    if actor.get("role") in {"researcher", "admin", "supervisor"} and requested_user_id:
        user_id = requested_user_id
    else:
        user_id = str(actor["id"])
    with get_connection() as conn:
        enrollment_rows = rows_to_dicts(conn.execute("SELECT * FROM relationship_pilot_enrollments WHERE user_id = ? ORDER BY created_at", (user_id,)).fetchall())
        for enrollment in enrollment_rows:
            ensure_researcher_access(actor, enrollment)
        task_rows = rows_to_dicts(conn.execute("SELECT id, enrollment_id, task_type, risk_level, review_status, created_at FROM relationship_pilot_tasks WHERE user_id = ? ORDER BY created_at", (user_id,)).fetchall())
        report_rows = rows_to_dicts(conn.execute("SELECT id, enrollment_id, status, version, created_at FROM relationship_screening_reports WHERE user_id = ? ORDER BY created_at", (user_id,)).fetchall())
        long_rows = rows_to_dicts(conn.execute("SELECT * FROM relationship_longitudinal_entries WHERE user_id = ? ORDER BY event_at, created_at", (user_id,)).fetchall())
        message_rows = rows_to_dicts(conn.execute("SELECT id, source_id, title, body, message_type, created_at FROM messages WHERE user_id = ? AND message_type = 'relationship_stage_feedback' ORDER BY created_at", (user_id,)).fetchall())
        if enrollment_rows:
            write_audit_log(conn, "relationship_growth_viewed", actor["id"], "relationship_growth", user_id, {"rounds": len(enrollment_rows)})
            conn.commit()
    timeline = []
    curves: dict[str, list[dict]] = {}
    for round_no, enrollment in enumerate(enrollment_rows, 1):
        expanded = expand_enrollment(enrollment)
        timeline.append({"id": enrollment["id"], "type": "assessment", "title": f"第{round_no}次关系探索测评", "created_at": enrollment["created_at"], "summary": expanded["profile"].get("profile_name")})
        for key, value in dimension_lookup(expanded["dimensions"]).items():
            curves.setdefault(key, []).append({"round": round_no, "value": value, "created_at": enrollment["created_at"]})
    for task in task_rows:
        timeline.append({"id": task["id"], "type": "project_task", "title": "关系绘画" if task["task_type"] == "relationship_drawing" else "句子补全", "created_at": task["created_at"], "summary": task["review_status"]})
    for report in report_rows:
        timeline.append({"id": report["id"], "type": "report", "title": "关系健康初筛报告", "created_at": report["created_at"], "summary": report["status"]})
    for row in long_rows:
        measures = json_loads(row.get("measures_json"), {})
        timeline.append({
            "id": row["id"],
            "type": row["entry_type"],
            "title": "每周补充测量" if row["entry_type"] == "weekly_supplement" else "关键关系事件",
            "created_at": row.get("event_at") or row["created_at"],
            "summary": "已完成本周补充记录" if row["entry_type"] == "weekly_supplement" else "已记录一条关键事件",
            "risk_level": row["risk_level"],
        })
        for key in ["active_social_count", "authentic_expression_count", "approach_willingness", "worry_intensity"]:
            if isinstance(measures.get(key), (int, float)):
                curves.setdefault(key, []).append({"round": len(curves.get(key, [])) + 1, "value": measures[key], "created_at": row.get("event_at") or row["created_at"]})
    for message in message_rows:
        timeline.append({"id": message["id"], "type": "researcher_feedback", "title": message["title"], "created_at": message["created_at"], "summary": message.get("body") or "研究者已发送阶段性反馈"})
    timeline.sort(key=lambda row: row.get("created_at") or "")
    changes = []
    for key, points in curves.items():
        if len(points) >= 2:
            changes.append({"dimension": key, "from": points[0]["value"], "to": points[-1]["value"], "change": round(points[-1]["value"] - points[0]["value"], 2)})
    if enrollment_rows:
        four_layer = four_layer_profile(enrollment_rows[-1], len(enrollment_rows), changes)
    else:
        four_layer = {"basic": {}, "tension": {"clues": []}, "mechanism": {"hypotheses": []}, "dynamic": {"rounds_count": 0, "changes": []}}
    growth_report = {
        "change_summary": "已有多次记录，可结合曲线讨论变化。" if changes else "目前记录较少，先保留起点，不急于判断趋势。",
        "important_events": [item for item in timeline if item["type"] in {"key_event", "weekly_supplement", "project_task"}][-5:],
        "self_narratives": [{"entry_type": row["entry_type"], "created_at": row.get("event_at") or row["created_at"], "content": json_loads(row.get("narratives_json"), {})} for row in long_rows][-5:],
        "researcher_confirmations": [{"id": row["id"], "title": row["title"], "created_at": row["created_at"]} for row in message_rows][-5:],
        "next_step": "选择一个用户愿意、低压力且可退出的小行动，并在下一次记录中复盘。",
        "four_layer_profile": four_layer,
        "boundary_notice": "成长报告只记录变化和探索线索，不构成诊断或关系能力评价，也不构成疗效证明。",
    }
    latest_enrollment_id = enrollment_rows[-1]["id"] if enrollment_rows else None
    return ServiceResult(
        {
            "user_id": user_id,
            "latest_enrollment_id": latest_enrollment_id,
            "can_record": latest_enrollment_id is not None,
            "curves": curves,
            "timeline": timeline,
            "growth_report": growth_report,
        }
    )


def researcher_dashboard(actor: dict) -> ServiceResult:
    with get_connection() as conn:
        where_clause = ""
        params: tuple = ()
        if actor.get("role") == "researcher":
            where_clause = "WHERE e.assigned_researcher_id IS NULL OR e.assigned_researcher_id = ?"
            params = (str(actor["id"]),)
        rows = conn.execute(
            f"""
            SELECT e.*, u.nickname,
                   (SELECT COUNT(*) FROM relationship_pilot_tasks t WHERE t.enrollment_id = e.id) AS tasks_count,
                   (SELECT id FROM relationship_screening_reports r WHERE r.enrollment_id = e.id ORDER BY created_at DESC LIMIT 1) AS report_id,
                   (SELECT status FROM relationship_screening_reports r WHERE r.enrollment_id = e.id ORDER BY created_at DESC LIMIT 1) AS report_status,
                   (SELECT COUNT(*) FROM relationship_research_notes n WHERE n.enrollment_id = e.id) AS notes_count,
                   (SELECT MAX(CASE WHEN t.risk_level IN ('medium', 'high') THEN 1 ELSE 0 END) FROM relationship_pilot_tasks t WHERE t.enrollment_id = e.id) AS has_priority_risk
            FROM relationship_pilot_enrollments e
            LEFT JOIN users u ON u.id = e.user_id
            {where_clause}
            ORDER BY e.created_at DESC
            """,
            params,
        ).fetchall()
        write_audit_log(conn, "relationship_research_dashboard_viewed", actor["id"], "relationship_pilot_dashboard", "all", {"records_count": len(rows)})
        conn.commit()
    items = [expand_enrollment(item) for item in rows_to_dicts(rows)]
    return ServiceResult({"items": items, "count": len(items), "boundary_notice": "洞察提示只作为访谈探索线索，不构成诊断或人格判断。"})
