"""Sensitive task and researcher narrative module for the relationship pilot."""

from __future__ import annotations

from database import get_connection, json_dumps, json_loads, new_id, now_iso, row_to_dict, rows_to_dicts, write_audit_log
from services.message_service import create_message
from services.relationship_pilot_common import (
    RESEARCH_ROLES,
    SENTENCE_CONTEXTS,
    RelationshipPilotError,
    ServiceResult,
    enrollment_by_id,
    ensure_researcher_assignment,
    ensure_researcher_access,
    expand_enrollment,
    expand_task,
)
from services.risk_review_service import create_risk_review_record
from services.risk_service import check_text_risk


def create_task(actor: dict, enrollment_id: str, payload: dict, idempotency_key: str = "") -> ServiceResult:
    task_type = str(payload.get("task_type") or "")
    if task_type not in {"relationship_drawing", "sentence_completion"}:
        raise RelationshipPilotError("validation_error", "不支持该任务类型。")
    if payload.get("material_consent") is not True:
        raise RelationshipPilotError("consent_required", "提交叙事材料前需要明确授权。")
    drawing_data = payload.get("drawing_data") or {}
    answers = payload.get("answers") or {}
    narration = str(payload.get("narration") or "").strip()
    if len(json_dumps(drawing_data)) > 200_000:
        raise RelationshipPilotError("payload_too_large", "绘画数据过大，请减少笔画后重试。", 413)
    if task_type == "sentence_completion":
        if not isinstance(answers, dict) or not answers:
            raise RelationshipPilotError("validation_error", "至少完成一个句子。")
        if any(context not in SENTENCE_CONTEXTS for context in answers):
            raise RelationshipPilotError("validation_error", "包含未配置的句子情境。")
    risk = check_text_risk([narration, *[str(value) for value in answers.values()]], source="relationship_pilot_task")
    idempotency_key = str(idempotency_key or "").strip()[:128]
    with get_connection() as conn:
        enrollment = enrollment_by_id(conn, enrollment_id)
        if not enrollment:
            raise RelationshipPilotError("not_found", "没有找到报名记录。", 404)
        if str(actor["id"]) != str(enrollment["user_id"]):
            raise RelationshipPilotError("forbidden", "只能提交自己的项目任务。", 403)
        if idempotency_key:
            existing = conn.execute(
                "SELECT * FROM relationship_pilot_tasks WHERE user_id = ? AND idempotency_key = ?",
                (enrollment["user_id"], idempotency_key),
            ).fetchone()
            if existing:
                existing_item = row_to_dict(existing)
                if existing_item["enrollment_id"] != enrollment_id or existing_item["task_type"] != task_type:
                    raise RelationshipPilotError("idempotency_conflict", "该提交标识已用于其它任务。", 409)
                return ServiceResult(expand_task(existing_item))
        task_id = new_id("rel_task")
        timestamp = now_iso()
        try:
            conn.execute(
                """
                INSERT INTO relationship_pilot_tasks (
                    id, enrollment_id, user_id, task_type, drawing_data_json, narration, answers_json,
                    material_consent, risk_level, review_status, idempotency_key, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?, ?, ?, ?, ?)
                """,
                (task_id, enrollment_id, enrollment["user_id"], task_type, json_dumps(drawing_data), narration or None, json_dumps(answers), risk["risk_level"], "priority_review" if risk["requires_review"] else "pending_review", idempotency_key or None, timestamp, timestamp),
            )
        except Exception:
            if idempotency_key:
                existing = conn.execute(
                    "SELECT * FROM relationship_pilot_tasks WHERE user_id = ? AND idempotency_key = ?",
                    (enrollment["user_id"], idempotency_key),
                ).fetchone()
                if existing:
                    return ServiceResult(expand_task(row_to_dict(existing)))
            raise
        create_risk_review_record(conn, enrollment["user_id"], "relationship_pilot_task", task_id, risk)
        write_audit_log(conn, "relationship_task_submitted", actor["id"], "relationship_pilot_task", task_id, {"task_type": task_type, "risk_level": risk["risk_level"], "contains_sensitive_material": True})
        conn.commit()
        row = conn.execute("SELECT * FROM relationship_pilot_tasks WHERE id = ?", (task_id,)).fetchone()
    item = expand_task(row_to_dict(row))
    item["boundary_notice"] = "绘画和句子只作为叙事材料，系统不自动解释潜意识、人格或关系问题。"
    return ServiceResult(item, 201)


def create_note(actor: dict, enrollment_id: str, note: str) -> ServiceResult:
    note = str(note or "").strip()
    if not note:
        raise RelationshipPilotError("validation_error", "备注不能为空。")
    if any(term in note for term in ["依恋创伤已确定", "人格缺陷", "病理模式"]):
        raise RelationshipPilotError("validation_error", "研究备注不得使用诊断化、人格化或病理化定性。")
    with get_connection() as conn:
        enrollment = enrollment_by_id(conn, enrollment_id)
        if not enrollment:
            raise RelationshipPilotError("not_found", "没有找到报名记录。", 404)
        ensure_researcher_assignment(conn, actor, enrollment)
        note_id = new_id("rel_note")
        timestamp = now_iso()
        conn.execute("INSERT INTO relationship_research_notes (id, enrollment_id, researcher_id, note, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)", (note_id, enrollment_id, actor["id"], note, timestamp, timestamp))
        write_audit_log(conn, "relationship_research_note_created", actor["id"], "relationship_research_note", note_id, {"enrollment_id": enrollment_id})
        conn.commit()
        row = conn.execute("SELECT * FROM relationship_research_notes WHERE id = ?", (note_id,)).fetchone()
    return ServiceResult(row_to_dict(row), 201)


def create_narrative(actor: dict, enrollment_id: str, payload: dict) -> ServiceResult:
    with get_connection() as conn:
        enrollment = enrollment_by_id(conn, enrollment_id)
        if not enrollment:
            raise RelationshipPilotError("not_found", "没有找到报名记录。", 404)
        enrollment = ensure_researcher_assignment(conn, actor, enrollment)
        expanded = expand_enrollment(enrollment)
        tasks = rows_to_dicts(conn.execute("SELECT * FROM relationship_pilot_tasks WHERE enrollment_id = ? ORDER BY created_at", (enrollment_id,)).fetchall())
        notes = rows_to_dicts(conn.execute("SELECT * FROM relationship_research_notes WHERE enrollment_id = ? ORDER BY created_at", (enrollment_id,)).fetchall())
        draft = {
            "starting_profile": expanded["profile"],
            "selected_assessment_questions": expanded["profile"].get("suggested_assessment_questions", []),
            "dimension_clues": expanded["dimensions"],
            "online_task_materials": [{"task_type": task["task_type"], "narration": task.get("narration"), "review_status": task["review_status"]} for task in tasks],
            "researcher_notes": [note["note"] for note in notes],
            "joint_revision": str(payload.get("joint_revision") or ""),
            "next_project_task": str(payload.get("next_project_task") or "先选择一个低压力、可退出的小行动。"),
            "boundary_notice": "这是待共同修订的探索手记草稿，不是诊断结论；用户端仅展示研究者确认后的版本。",
        }
        narrative_id = new_id("rel_narrative")
        timestamp = now_iso()
        conn.execute("INSERT INTO relationship_narratives (id, enrollment_id, user_id, draft_json, status, confirmed_by, confirmed_at, created_at, updated_at) VALUES (?, ?, ?, ?, 'draft', NULL, NULL, ?, ?)", (narrative_id, enrollment_id, enrollment["user_id"], json_dumps(draft), timestamp, timestamp))
        write_audit_log(conn, "relationship_narrative_drafted", actor["id"], "relationship_narrative", narrative_id, {"enrollment_id": enrollment_id})
        conn.commit()
        row = conn.execute("SELECT * FROM relationship_narratives WHERE id = ?", (narrative_id,)).fetchone()
    item = row_to_dict(row)
    item["draft"] = json_loads(item.get("draft_json"), {})
    return ServiceResult(item, 201)


def confirm_narrative(actor: dict, narrative_id: str) -> ServiceResult:
    timestamp = now_iso()
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM relationship_narratives WHERE id = ?", (narrative_id,)).fetchone()
        if not row:
            raise RelationshipPilotError("not_found", "没有找到探索手记。", 404)
        enrollment = enrollment_by_id(conn, row["enrollment_id"])
        ensure_researcher_assignment(conn, actor, enrollment)
        conn.execute("UPDATE relationship_narratives SET status = 'confirmed', confirmed_by = ?, confirmed_at = ?, updated_at = ? WHERE id = ?", (actor["id"], timestamp, timestamp, narrative_id))
        existing_message = conn.execute("SELECT id FROM messages WHERE user_id = ? AND source_type = 'relationship_narrative' AND source_id = ? LIMIT 1", (row["user_id"], narrative_id)).fetchone()
        if not existing_message:
            create_message(conn, row["user_id"], "关系探索手记已确认", "研究者已确认探索手记。你可以在小程序内查看起点画像、共同讨论问题和下一步项目任务。", "relationship_narrative", "relationship_narrative", narrative_id)
        write_audit_log(conn, "relationship_narrative_confirmed", actor["id"], "relationship_narrative", narrative_id)
        conn.commit()
        updated = conn.execute("SELECT * FROM relationship_narratives WHERE id = ?", (narrative_id,)).fetchone()
    item = row_to_dict(updated)
    item["draft"] = json_loads(item.get("draft_json"), {})
    return ServiceResult(item)


def get_narrative(actor: dict, narrative_id: str) -> ServiceResult:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM relationship_narratives WHERE id = ?", (narrative_id,)).fetchone()
        if not row:
            raise RelationshipPilotError("not_found", "没有找到探索手记。", 404)
        item = row_to_dict(row)
        is_researcher = actor.get("role") in RESEARCH_ROLES
        enrollment = enrollment_by_id(conn, item["enrollment_id"])
        ensure_researcher_access(actor, enrollment)
        if not is_researcher and (str(actor["id"]) != str(item["user_id"]) or item["status"] != "confirmed"):
            raise RelationshipPilotError("not_found", "探索手记尚未确认或不存在。", 404)
        write_audit_log(conn, "relationship_narrative_viewed", actor["id"], "relationship_narrative", narrative_id, {"role": actor.get("role")})
        conn.commit()
    item["draft"] = json_loads(item.get("draft_json"), {})
    if actor.get("role") not in RESEARCH_ROLES:
        item["draft"].pop("researcher_notes", None)
        item["audience"] = "participant"
    else:
        item["audience"] = "researcher"
    return ServiceResult(item)
