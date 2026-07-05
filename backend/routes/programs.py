"""Evidence-informed pilot program content endpoints."""

from flask import Blueprint

from database import load_content_json
from routes.utils import fail, ok


bp = Blueprint("programs", __name__, url_prefix="/api/programs")


def _load_programs_payload() -> dict:
    return load_content_json("programs.json")


def _program_summary(program: dict) -> dict:
    return {
        "id": program.get("id"),
        "title": program.get("title"),
        "target_constructs": program.get("target_constructs", []),
        "audience": program.get("audience"),
        "theory_source": program.get("theory_source"),
        "review_status": program.get("review_status"),
        "boundary_notice": program.get("boundary_notice"),
        "session_count": len(program.get("sessions", [])),
        "first_session_title": (program.get("sessions") or [{}])[0].get("title"),
    }


@bp.get("")
def list_programs():
    payload = _load_programs_payload()
    programs = payload.get("programs", [])
    return ok(
        {
            "version": payload.get("version"),
            "boundary_notice": payload.get("boundary_notice"),
            "items": [_program_summary(program) for program in programs if program.get("enabled", True)],
        }
    )


@bp.get("/<program_id>")
def get_program(program_id: str):
    payload = _load_programs_payload()
    for program in payload.get("programs", []):
        if program.get("id") == program_id and program.get("enabled", True):
            return ok({"version": payload.get("version"), "program": program})
    return fail("not_found", "未找到对应的项目测试内容", status=404)
