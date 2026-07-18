"""Role-scoped participant matrix and read-only multi-module dossier."""

from __future__ import annotations

from flask import Blueprint, request

from database import get_connection, json_loads, now_iso, rows_to_dicts, write_audit_log
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


def _scoped_user_column(actor: dict, column: str) -> tuple[str, list[str]]:
    if actor.get("role") != "researcher":
        return "1 = 1", []
    return (
        f"{column} IN (SELECT user_id FROM relationship_pilot_enrollments WHERE assigned_researcher_id = ?)",
        [str(actor["id"])],
    )


def _status_counts(conn, table: str, scope_clause: str, params: list[str]) -> dict[str, int]:
    rows = conn.execute(
        f"SELECT status, COUNT(*) AS count FROM {table} WHERE {scope_clause} GROUP BY status",
        tuple(params),
    ).fetchall()
    return {str(row["status"]): int(row["count"]) for row in rows}


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


@bp.get("/operations")
def get_research_operations():
    """Return role-scoped operational counts without participant secrets or raw text."""

    actor, error = _actor()
    if error:
        return error
    scope_clause, params = _scoped_user_column(actor, "user_id")
    timestamp = now_iso()
    with get_connection() as conn:
        preference_rows = conn.execute(
            f"SELECT consent_status, COUNT(*) AS count FROM notification_preferences WHERE {scope_clause} GROUP BY consent_status",
            tuple(params),
        ).fetchall()
        preference_counts = {str(row["consent_status"]): int(row["count"]) for row in preference_rows}
        delivery_counts = _status_counts(conn, "notification_deliveries", scope_clause, params)
        retry_count = conn.execute(
            f"SELECT COUNT(*) AS count FROM notification_deliveries WHERE {scope_clause} AND status = 'failed' AND attempt_count BETWEEN 1 AND 2",
            tuple(params),
        ).fetchone()["count"]
        exhausted_count = conn.execute(
            f"SELECT COUNT(*) AS count FROM notification_deliveries WHERE {scope_clause} AND status = 'failed' AND attempt_count >= 3",
            tuple(params),
        ).fetchone()["count"]
        overdue_count = conn.execute(
            f"SELECT COUNT(*) AS count FROM notification_deliveries WHERE {scope_clause} AND status = 'pending' AND scheduled_for <= ?",
            tuple([*params, timestamp]),
        ).fetchone()["count"]
        failure_rows = conn.execute(
            f"""
            SELECT COALESCE(error_code, 'unknown') AS error_code, COUNT(*) AS count
            FROM notification_deliveries
            WHERE {scope_clause} AND status = 'failed'
            GROUP BY COALESCE(error_code, 'unknown')
            ORDER BY count DESC, error_code ASC
            LIMIT 8
            """,
            tuple(params),
        ).fetchall()
        stage_feedback_count = conn.execute(
            f"""
            SELECT COUNT(*) AS count FROM relationship_screening_reports
            WHERE {scope_clause} AND status IN ('pending_review', 'ready', 'confirmed', 'updated')
            """,
            tuple(params),
        ).fetchone()["count"]
        supervision_count = conn.execute(
            f"SELECT COUNT(*) AS count FROM supervision_requests WHERE {scope_clause} AND status = 'pending'",
            tuple(params),
        ).fetchone()["count"]
        risk_review_count = conn.execute(
            f"SELECT COUNT(*) AS count FROM risk_review_records WHERE {scope_clause} AND review_status IN ('pending', 'priority_review')",
            tuple(params),
        ).fetchone()["count"]
        write_audit_log(
            conn,
            "research_operations_viewed",
            actor["id"],
            "research_operations",
            "assigned" if actor.get("role") == "researcher" else "all",
            {
                "notification_failed": delivery_counts.get("failed", 0),
                "stage_feedback_pending": int(stage_feedback_count),
                "supervision_pending": int(supervision_count),
            },
        )
        conn.commit()

    return ok(
        {
            "scope": "assigned_participants" if actor.get("role") == "researcher" else "all_participants",
            "generated_at": timestamp,
            "notification_preferences": {
                "accepted": preference_counts.get("accepted", 0),
                "rejected": preference_counts.get("rejected", 0),
                "consumed": preference_counts.get("consumed", 0),
                "unknown": preference_counts.get("unknown", 0),
            },
            "notification_deliveries": {
                "pending": delivery_counts.get("pending", 0),
                "sending": delivery_counts.get("sending", 0),
                "sent": delivery_counts.get("sent", 0),
                "failed": delivery_counts.get("failed", 0),
                "retry_queue": int(retry_count),
                "exhausted": int(exhausted_count),
                "overdue": int(overdue_count),
            },
            "failure_reasons": [
                {"error_code": str(row["error_code"]), "count": int(row["count"])} for row in failure_rows
            ],
            "backlog": {
                "stage_feedback": int(stage_feedback_count),
                "supervision": int(supervision_count),
                "risk_review": int(risk_review_count),
            },
            "boundary_notice": "仅展示脱敏数量和错误代码，不返回 OpenID、模板密钥、联系方式或填写原文。",
        }
    )
