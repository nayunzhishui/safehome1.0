"""Evidence-informed pilot program content endpoints."""

import json

from flask import Blueprint, request

from database import ensure_user, get_connection, load_content_json, new_id, now_iso, row_to_dict
from routes.auth_utils import AuthError, auth_error_response, resolve_actor_user_id
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


@bp.post("/<program_id>/entries")
def create_program_entry(program_id: str):
    payload = request.get_json(silent=True) or {}
    try:
        user_id = resolve_actor_user_id(payload=payload)
    except AuthError as exc:
        return auth_error_response(exc)

    programs_payload = _load_programs_payload()
    program = next(
        (
            item
            for item in programs_payload.get("programs", [])
            if item.get("id") == program_id and item.get("enabled", True)
        ),
        None,
    )
    if not program:
        return fail("not_found", "未找到对应的项目测试内容", status=404)

    session_no = payload.get("session_no")
    answers = payload.get("answers") if isinstance(payload.get("answers"), dict) else {}
    reflection = str(payload.get("reflection") or "").strip()
    analysis_consent = bool(payload.get("analysis_consent"))
    boundary_notice = program.get("boundary_notice") or programs_payload.get("boundary_notice") or "项目测试内容只用于陪伴练习和自我观察，不构成诊断、筛查或治疗方案。"
    if not session_no:
        return fail("validation_error", "缺少 session_no", status=400)
    if not answers and not reflection:
        return fail("validation_error", "请先填写草稿或反思内容", status=400)

    timestamp = now_iso()
    record_id = new_id("record")
    data = {
        "program_id": program_id,
        "program_title": program.get("title"),
        "session_no": session_no,
        "answers": answers,
        "reflection": reflection,
        "analysis_consent": analysis_consent,
        "boundary_notice": boundary_notice,
        "analysis_note": "该记录仅用于陪伴练习、复盘和经授权的脱敏聚合分析，不作为诊断或筛查结论。",
    }

    with get_connection() as conn:
        ensure_user(conn, user_id, payload.get("nickname"))
        conn.execute(
            """
            INSERT INTO records (
                id, user_id, module_type, source_id, data_json,
                created_at, updated_at, export_allowed
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record_id,
                user_id,
                "program_entry",
                program_id,
                json.dumps(data, ensure_ascii=False),
                timestamp,
                timestamp,
                1 if analysis_consent else 0,
            ),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM records WHERE id = ?", (record_id,)).fetchone()

    return ok({"record": row_to_dict(row), "boundary_notice": boundary_notice}, status=201)
