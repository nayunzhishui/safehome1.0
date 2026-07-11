"""Structured course content and progress endpoints."""

import json

from flask import Blueprint, request

from database import ensure_user, get_connection, json_loads, load_content_json, new_id, now_iso, row_to_dict
from routes.auth_utils import AuthError, auth_error_response, resolve_actor_user_id
from routes.utils import fail, ok, parse_int


bp = Blueprint("courses", __name__, url_prefix="/api/courses")


def _load_courses_payload() -> dict:
    return load_content_json("courses.json")


def _course_summary(course: dict) -> dict:
    sections = course.get("sections") or []
    return {
        "id": course.get("id"),
        "title": course.get("title"),
        "theme": course.get("theme"),
        "scene": course.get("scene"),
        "duration_minutes": course.get("duration_minutes"),
        "section_count": len(sections),
        "first_section_title": (sections or [{}])[0].get("title"),
        "curriculum_node": course.get("curriculum_node"),
        "learning_objectives": course.get("learning_objectives", []),
        "review_status": course.get("review_status"),
        "relation_to_cards_or_programs": course.get("relation_to_cards_or_programs", []),
        "boundary_notice": course.get("boundary_notice"),
    }


@bp.get("")
def list_courses():
    payload = _load_courses_payload()
    courses = [item for item in payload.get("courses", []) if item.get("enabled", True)]
    return ok(
        {
            "version": payload.get("version"),
            "boundary_notice": payload.get("boundary_notice"),
            "pathways": payload.get("pathways", []),
            "items": [_course_summary(course) for course in courses],
        }
    )


@bp.get("/pathways")
def list_course_pathways():
    payload = _load_courses_payload()
    return ok(
        {
            "version": payload.get("version"),
            "boundary_notice": payload.get("boundary_notice"),
            "items": payload.get("pathways", []),
        }
    )


@bp.get("/progress")
def list_course_progress():
    try:
        user_id = resolve_actor_user_id(request.args.get("user_id"))
    except AuthError as exc:
        return auth_error_response(exc)
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT * FROM records
            WHERE user_id = ? AND module_type = 'course_progress'
            ORDER BY created_at DESC
            """,
            (user_id,),
        ).fetchall()
    latest = {}
    for row in rows:
        item = row_to_dict(row)
        if item["source_id"] in latest:
            continue
        item["progress"] = json_loads(item.get("data_json"), {})
        latest[item["source_id"]] = item
    return ok({"user_id": user_id, "items": list(latest.values())})


@bp.get("/<course_id>/progress")
def get_course_progress(course_id: str):
    try:
        user_id = resolve_actor_user_id(request.args.get("user_id"))
    except AuthError as exc:
        return auth_error_response(exc)
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT * FROM records
            WHERE user_id = ? AND module_type = 'course_progress' AND source_id = ?
            ORDER BY created_at DESC LIMIT 1
            """,
            (user_id, course_id),
        ).fetchone()
    if not row:
        return ok({"user_id": user_id, "course_id": course_id, "progress": None})
    item = row_to_dict(row)
    item["progress"] = json_loads(item.get("data_json"), {})
    return ok({"user_id": user_id, "course_id": course_id, "record": item, "progress": item["progress"]})


@bp.post("/<course_id>/progress")
def save_course_progress(course_id: str):
    body = request.get_json(silent=True) or {}
    try:
        user_id = resolve_actor_user_id(payload=body)
    except AuthError as exc:
        return auth_error_response(exc)
    courses_payload = _load_courses_payload()
    course = next((item for item in courses_payload.get("courses", []) if item.get("id") == course_id and item.get("enabled", True)), None)
    if not course:
        return fail("not_found", "未找到对应课程内容。", status=404)
    status = str(body.get("status") or "in_progress")
    if status not in {"in_progress", "completed", "skipped"}:
        return fail("invalid_course_progress_status", "课程进度状态不在允许范围内。", status=400)
    completed_sections = parse_int(body.get("completed_section_count"), None)
    if completed_sections is None:
        return fail("invalid_completed_section_count", "完成章节数必须是整数。", status=400)
    if not 0 <= completed_sections <= len(course.get("sections", [])):
        return fail("invalid_completed_section_count", "完成章节数不符合课程结构。", status=400)
    raw_check_ids = body.get("knowledge_check_completed_ids", [])
    if not isinstance(raw_check_ids, list):
        return fail("invalid_knowledge_check", "理解检查必须是ID列表。", status=400)
    check_ids = [str(item) for item in raw_check_ids if str(item)]
    valid_check_ids = {str(item.get("id")) for item in course.get("knowledge_checks", []) if isinstance(item, dict)}
    if any(item not in valid_check_ids for item in check_ids):
        return fail("invalid_knowledge_check", "理解检查不属于当前课程版本。", status=400)
    linked_card_id = body.get("linked_card_id")
    if linked_card_id and linked_card_id not in (course.get("relation_to_cards_or_programs") or []):
        return fail("invalid_linked_card", "关联训练卡不属于当前课程。", status=400)
    progress = {
        "course_id": course_id,
        "course_version": courses_payload.get("version"),
        "status": status,
        "completed_section_count": completed_sections,
        "knowledge_check_completed_ids": list(dict.fromkeys(check_ids)),
        "transfer_task_status": str(body.get("transfer_task_status") or "not_started"),
        "linked_card_id": linked_card_id,
        "completion_note": "完成表示已浏览结构内容并尝试理解检查；不代表掌握、疗效或心理状态改善。",
    }
    if progress["transfer_task_status"] not in {"not_started", "planned", "attempted", "skipped"}:
        return fail("invalid_transfer_task_status", "迁移任务状态不在允许范围内。", status=400)
    timestamp = now_iso()
    with get_connection() as conn:
        ensure_user(conn, user_id, body.get("nickname"))
        conn.execute(
            """
            INSERT INTO records (id, user_id, module_type, source_id, data_json, created_at, updated_at, export_allowed)
            VALUES (?, ?, 'course_progress', ?, ?, ?, ?, 0)
            """,
            (new_id("record"), user_id, course_id, json.dumps(progress, ensure_ascii=False), timestamp, timestamp),
        )
        conn.commit()
        row = conn.execute(
            "SELECT * FROM records WHERE user_id = ? AND module_type = 'course_progress' AND source_id = ? ORDER BY created_at DESC LIMIT 1",
            (user_id, course_id),
        ).fetchone()
    item = row_to_dict(row)
    item["progress"] = progress
    return ok({"record": item, "progress": progress}, status=201)


@bp.get("/<course_id>")
def get_course(course_id: str):
    payload = _load_courses_payload()
    for course in payload.get("courses", []):
        if course.get("id") == course_id and course.get("enabled", True):
            return ok({"version": payload.get("version"), "course": course})
    return fail("not_found", "未找到对应课程内容。", status=404)
