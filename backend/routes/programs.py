"""Evidence-informed pilot program content endpoints."""

import json

from flask import Blueprint, current_app, request

from database import ensure_user, get_connection, json_loads, load_content_json, new_id, now_iso, row_to_dict, rows_to_dicts
from routes.auth_utils import AuthError, auth_error_response, require_role, resolve_actor_user_id
from routes.utils import fail, ok, parse_bool, parse_int
from services.risk_service import check_text_risk
from services.showcase_access_service import showcase_programs_open


bp = Blueprint("programs", __name__, url_prefix="/api/programs")


def _load_programs_payload() -> dict:
    return load_content_json("programs.json")


def _is_program_available(program: dict) -> bool:
    if not program.get("enabled", True):
        return False
    if showcase_programs_open():
        return True
    is_production = str(current_app.config.get("APP_ENV", "development")).lower() == "production"
    return not is_production or program.get("review_status") == "pilot_approved"


def _reviewer_preview_requested() -> tuple[bool, object | None]:
    if not parse_bool(request.args.get("include_drafts"), False):
        return False, None
    try:
        require_role("researcher", "supervisor", "admin")
    except AuthError as exc:
        return False, auth_error_response(exc)
    return True, None


def _program_summary(program: dict) -> dict:
    measurement_plan = program.get("measurement_plan") or {}
    return {
        "id": program.get("id"),
        "title": program.get("title"),
        "target_constructs": program.get("target_constructs", []),
        "audience": program.get("audience"),
        "theory_source": program.get("theory_source"),
        "review_status": program.get("review_status"),
        "protocol_version": program.get("protocol_version"),
        "preview_only": program.get("review_status") != "pilot_approved" and not showcase_programs_open(),
        "showcase_open": showcase_programs_open(),
        "minimum_dose": program.get("minimum_dose"),
        "completion_definition": program.get("completion_definition"),
        "boundary_notice": program.get("boundary_notice"),
        "session_count": len(program.get("sessions", [])),
        "first_session_title": (program.get("sessions") or [{}])[0].get("title"),
        "measurement_plan": {
            "status": measurement_plan.get("status"),
            "measurement_point_labels": [
                point.get("label")
                for point in measurement_plan.get("measurement_points", [])
                if isinstance(point, dict) and point.get("label")
            ],
            "requires_manual_review": bool(measurement_plan.get("manual_review_items")),
        },
    }


@bp.get("")
def list_programs():
    payload = _load_programs_payload()
    programs = payload.get("programs", [])
    include_drafts, error_response = _reviewer_preview_requested()
    if error_response is not None:
        return error_response
    available = [program for program in programs if include_drafts or _is_program_available(program)]
    pending_count = sum(1 for program in programs if program.get("review_status") == "pilot_draft")
    approved_count = sum(1 for program in programs if program.get("review_status") == "pilot_approved")
    showcase_mode = showcase_programs_open()
    return ok(
        {
            "version": payload.get("version"),
            "boundary_notice": payload.get("boundary_notice"),
            "items": [_program_summary(program) for program in available],
            "availability": {
                "approved_count": approved_count,
                "pending_review_count": pending_count,
                "preview_mode": include_drafts,
                "showcase_mode": showcase_mode,
                "status": "showcase_open" if showcase_mode else "available" if approved_count else "pending_review",
                "message": (
                    "临时展示模式已开启，三个项目方案均可查看和试用；正式发布前仍需恢复审核门禁。"
                    if showcase_mode
                    else "当前项目方案仍在研究、心理和伦理审核中，审核完成后开放。"
                    if not approved_count and pending_count
                    else "仅显示已完成治理审核的项目方案。"
                ),
            },
        }
    )


@bp.get("/<program_id>")
def get_program(program_id: str):
    payload = _load_programs_payload()
    include_drafts, error_response = _reviewer_preview_requested()
    if error_response is not None:
        return error_response
    for program in payload.get("programs", []):
        if program.get("id") == program_id and (include_drafts or _is_program_available(program)):
            return ok(
                {
                    "version": payload.get("version"),
                    "program": {**program, "showcase_open": showcase_programs_open()},
                    "preview_mode": include_drafts,
                }
            )
    return fail("not_found", "未找到对应的项目测试内容", status=404)


@bp.get("/<program_id>/entries")
def list_program_entries(program_id: str):
    try:
        user_id = resolve_actor_user_id(request.args.get("user_id"))
    except AuthError as exc:
        return auth_error_response(exc)
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT id, user_id, source_id, data_json, created_at, updated_at
            FROM records
            WHERE user_id = ? AND module_type = 'program_entry' AND source_id = ?
            ORDER BY created_at DESC
            """,
            (user_id, program_id),
        ).fetchall()
    items = []
    for row in rows_to_dicts(rows):
        data = json_loads(row.pop("data_json", None), {})
        items.append(
            {
                **row,
                "program_id": data.get("program_id"),
                "program_title": data.get("program_title"),
                "session_no": data.get("session_no"),
                "answers": data.get("answers") or {},
                "reflection": data.get("reflection") or "",
                "participation_status": data.get("participation_status"),
                "distress_before": data.get("distress_before"),
                "distress_after": data.get("distress_after"),
                "adverse_response": bool(data.get("adverse_response")),
                "boundary_notice": data.get("boundary_notice"),
            }
        )
    return ok({"items": items, "count": len(items)})


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
    if str(current_app.config.get("APP_ENV", "development")).lower() == "production" and program.get("review_status") != "pilot_approved" and not showcase_programs_open():
        return fail("program_not_approved", "该项目尚未完成研究、心理和伦理审核。", status=409)

    session_no = parse_int(payload.get("session_no"), None)
    answers = payload.get("answers") if isinstance(payload.get("answers"), dict) else {}
    reflection = str(payload.get("reflection") or "").strip()
    analysis_consent = parse_bool(payload.get("analysis_consent"), False)
    boundary_notice = program.get("boundary_notice") or programs_payload.get("boundary_notice") or "项目测试内容只用于陪伴练习和自我观察，不构成诊断、筛查或治疗方案。"
    if not session_no:
        return fail("validation_error", "缺少 session_no", status=400)
    if not any(int(session.get("session_no") or 0) == session_no for session in program.get("sessions", [])):
        return fail("invalid_session", "session_no 不属于当前项目版本", status=400)
    if not answers and not reflection:
        return fail("validation_error", "请先填写草稿或反思内容", status=400)
    if len(reflection) > 2000:
        return fail("reflection_too_long", "反思内容不能超过2000字", status=400)
    distress_before = parse_int(payload.get("distress_before"), None)
    distress_after = parse_int(payload.get("distress_after"), None)
    if any(value is not None and not 0 <= value <= 10 for value in (distress_before, distress_after)):
        return fail("invalid_distress_score", "不适评分必须在0到10之间", status=400)
    participation_status = str(payload.get("participation_status") or "completed")
    if participation_status not in {"completed", "skipped", "paused", "withdrawn"}:
        return fail("invalid_participation_status", "参与状态不在允许范围内", status=400)
    recommendation_source = str(payload.get("recommendation_source") or "user_choice")
    if recommendation_source not in set(program.get("recommendation_sources") or []):
        return fail("invalid_recommendation_source", "推荐来源不在当前方案允许范围内", status=400)
    risk_result = check_text_risk([reflection, json.dumps(answers, ensure_ascii=False)], source="program_entry")

    timestamp = now_iso()
    record_id = new_id("record")
    data = {
        "program_id": program_id,
        "program_title": program.get("title"),
        "protocol_version": program.get("protocol_version"),
        "program_review_status": program.get("review_status"),
        "session_no": session_no,
        "answers": answers,
        "reflection": reflection,
        "analysis_consent": analysis_consent,
        "participation_status": participation_status,
        "recommendation_source": recommendation_source,
        "distress_before": distress_before,
        "distress_after": distress_after,
        "adverse_response": parse_bool(payload.get("adverse_response"), False),
        "risk": risk_result,
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

    return ok(
        {
            "record": row_to_dict(row),
            "protocol_version": program.get("protocol_version"),
            "requires_review": risk_result.get("requires_review", False),
            "risk_safe_response": risk_result.get("safe_response") if risk_result.get("requires_review") else None,
            "boundary_notice": boundary_notice,
        },
        status=201,
    )
