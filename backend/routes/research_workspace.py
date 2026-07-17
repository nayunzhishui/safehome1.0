"""Role-scoped participant matrix and read-only multi-module dossier."""

from __future__ import annotations

from flask import Blueprint, request

from database import get_connection, json_loads, rows_to_dicts, write_audit_log
from routes.auth_utils import AuthError, auth_error_response, require_role
from routes.utils import fail, ok, parse_int


bp = Blueprint("research_workspace", __name__, url_prefix="/api/research")


def _actor():
    try:
        return require_role("researcher", "supervisor", "admin", allow_legacy_admin=True), None
    except AuthError as exc:
        return None, auth_error_response(exc)


def _allowed_user_clause(actor: dict, alias: str = "u") -> tuple[str, list[str]]:
    if actor.get("role") != "researcher":
        return "1 = 1", []
    return (
        f"""EXISTS (
            SELECT 1 FROM relationship_pilot_enrollments access_e
            WHERE access_e.user_id = {alias}.id AND access_e.assigned_researcher_id = ?
        )""",
        [str(actor["id"])],
    )


@bp.get("/participants")
def list_participants():
    actor, error = _actor()
    if error:
        return error
    query = str(request.args.get("q") or "").strip().lower()
    limit = min(max(parse_int(request.args.get("limit"), 50), 1), 100)
    allowed_clause, params = _allowed_user_clause(actor)
    search_clause = ""
    if query:
        search_clause = "AND (LOWER(u.id) LIKE ? OR LOWER(COALESCE(u.nickname, '')) LIKE ?)"
        params.extend([f"%{query}%", f"%{query}%"])
    params.append(limit)
    with get_connection() as conn:
        rows = conn.execute(
            f"""
            SELECT
                u.id AS user_id,
                u.nickname,
                u.role,
                u.updated_at AS last_activity_at,
                (SELECT COUNT(*) FROM assessment_results a WHERE a.user_id = u.id) AS assessment_count,
                (SELECT COUNT(*) FROM emotion_diaries d WHERE d.user_id = u.id) AS diary_count,
                (SELECT COUNT(*) FROM checkins c WHERE c.user_id = u.id) AS checkin_count,
                (SELECT COUNT(*) FROM records r WHERE r.user_id = u.id AND r.module_type = 'program_entry') AS program_count,
                (SELECT COUNT(*) FROM relationship_pilot_enrollments e WHERE e.user_id = u.id) AS relationship_count,
                (SELECT COUNT(*) FROM supervision_requests s WHERE s.user_id = u.id) AS supervision_count,
                (SELECT COUNT(*) FROM messages m WHERE m.user_id = u.id AND m.status = 'unread') AS unread_message_count
            FROM users u
            WHERE u.role IN ('parent', 'student', 'user')
              AND ({allowed_clause})
              {search_clause}
              AND (
                EXISTS (SELECT 1 FROM assessment_results a WHERE a.user_id = u.id)
                OR EXISTS (SELECT 1 FROM emotion_diaries d WHERE d.user_id = u.id)
                OR EXISTS (SELECT 1 FROM checkins c WHERE c.user_id = u.id)
                OR EXISTS (SELECT 1 FROM records r WHERE r.user_id = u.id AND r.module_type = 'program_entry')
                OR EXISTS (SELECT 1 FROM relationship_pilot_enrollments e WHERE e.user_id = u.id)
                OR EXISTS (SELECT 1 FROM supervision_requests s WHERE s.user_id = u.id)
              )
            ORDER BY u.updated_at DESC
            LIMIT ?
            """,
            tuple(params),
        ).fetchall()
        write_audit_log(
            conn,
            "research_participant_matrix_viewed",
            actor["id"],
            "research_participant_matrix",
            "filtered" if query else "all",
            {"result_count": len(rows), "query_used": bool(query)},
        )
        conn.commit()
    return ok(
        {
            "items": rows_to_dicts(rows),
            "count": len(rows),
            "scope": "assigned_participants" if actor.get("role") == "researcher" else "all_participants",
            "boundary_notice": "研究者仅查看获授权范围内的参与者资料；敏感详情访问会写入审计日志。",
        }
    )


@bp.get("/participants/<user_id>")
def get_participant_dossier(user_id: str):
    actor, error = _actor()
    if error:
        return error
    allowed_clause, params = _allowed_user_clause(actor)
    with get_connection() as conn:
        user = conn.execute(
            f"SELECT id AS user_id, nickname, role, created_at, updated_at FROM users u WHERE u.id = ? AND ({allowed_clause})",
            tuple([user_id, *params]),
        ).fetchone()
        if user is None:
            return fail("not_found", "没有找到可访问的参与者档案。", status=404)
        assessments = rows_to_dicts(
            conn.execute(
                "SELECT id, worksheet_id, worksheet_title, scores_json, total_score, profile_model_id, profile_cluster_id, profile_confidence, created_at FROM assessment_results WHERE user_id = ? ORDER BY created_at DESC LIMIT 100",
                (user_id,),
            ).fetchall()
        )
        diaries = rows_to_dicts(
            conn.execute(
                "SELECT id, event_time, scene, event_description, parent_emotion, parent_emotion_intensity, child_emotion, child_emotion_intensity, automatic_thought, body_sensation, behavior, created_at FROM emotion_diaries WHERE user_id = ? ORDER BY created_at DESC LIMIT 100",
                (user_id,),
            ).fetchall()
        )
        checkins = rows_to_dicts(
            conn.execute(
                "SELECT id, card_id, completed, emotion_before, emotion_after, helpfulness_rating, skip_reason, created_at FROM checkins WHERE user_id = ? ORDER BY created_at DESC LIMIT 100",
                (user_id,),
            ).fetchall()
        )
        program_rows = rows_to_dicts(
            conn.execute(
                "SELECT id, source_id, data_json, created_at FROM records WHERE user_id = ? AND module_type = 'program_entry' ORDER BY created_at DESC LIMIT 100",
                (user_id,),
            ).fetchall()
        )
        programs = []
        for row in program_rows:
            data = json_loads(row.pop("data_json", None), {})
            programs.append({**row, **data})
        relationships = rows_to_dicts(
            conn.execute(
                "SELECT id, worksheet_id, status, review_status, profile_json, dimensions_json, created_at FROM relationship_pilot_enrollments WHERE user_id = ? ORDER BY created_at DESC",
                (user_id,),
            ).fetchall()
        )
        relationship_tasks = rows_to_dicts(
            conn.execute(
                "SELECT id, enrollment_id, task_type, narration, answers_json, risk_level, review_status, created_at FROM relationship_pilot_tasks WHERE user_id = ? ORDER BY created_at DESC LIMIT 100",
                (user_id,),
            ).fetchall()
        )
        relationship_reports = rows_to_dicts(
            conn.execute(
                "SELECT id, enrollment_id, version, status, report_json, confirmed_at, created_at FROM relationship_screening_reports WHERE user_id = ? ORDER BY created_at DESC LIMIT 100",
                (user_id,),
            ).fetchall()
        )
        supervision = rows_to_dicts(
            conn.execute(
                "SELECT id, source_type, source_id, source_title, message, risk_hint, risk_level, status, supervisor_reply, created_at, replied_at FROM supervision_requests WHERE user_id = ? ORDER BY created_at DESC LIMIT 100",
                (user_id,),
            ).fetchall()
        )
        messages = rows_to_dicts(
            conn.execute(
                "SELECT id, sender_role, message_type, title, body, source_type, source_id, status, created_at, read_at FROM messages WHERE user_id = ? ORDER BY created_at DESC LIMIT 100",
                (user_id,),
            ).fetchall()
        )
        audit_count = conn.execute(
            "SELECT COUNT(*) AS count FROM audit_logs WHERE target_id = ? OR actor_id = ?",
            (user_id, user_id),
        ).fetchone()["count"]
        write_audit_log(
            conn,
            "research_participant_dossier_viewed",
            actor["id"],
            "user",
            user_id,
            {
                "assessment_count": len(assessments),
                "diary_count": len(diaries),
                "program_count": len(programs),
                "relationship_count": len(relationships),
            },
        )
        conn.commit()
    return ok(
        {
            "participant": dict(user),
            "modules": {
                "assessments": assessments,
                "diaries": diaries,
                "checkins": checkins,
                "program_entries": programs,
                "relationship_enrollments": relationships,
                "relationship_tasks": relationship_tasks,
                "relationship_reports": relationship_reports,
                "supervision_requests": supervision,
                "messages": messages,
            },
            "audit_summary": {"related_event_count": audit_count},
            "boundary_notice": "原始填写仅供授权研究审阅，不得直接改写；研究者备注与反馈应另存并保留审计。",
        }
    )
