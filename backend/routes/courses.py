"""Lightweight course content endpoints."""

from flask import Blueprint

from database import load_content_json
from routes.utils import fail, ok


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
            "items": [_course_summary(course) for course in courses],
        }
    )


@bp.get("/<course_id>")
def get_course(course_id: str):
    payload = _load_courses_payload()
    for course in payload.get("courses", []):
        if course.get("id") == course_id and course.get("enabled", True):
            return ok({"version": payload.get("version"), "course": course})
    return fail("not_found", "未找到对应课程内容。", status=404)
