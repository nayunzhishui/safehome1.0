"""Emotion diary endpoints."""

from flask import Blueprint, request

from database import ensure_user, get_connection, new_id, now_iso, row_to_dict, rows_to_dicts, write_audit_log
from routes.utils import (
    admin_token_error_response,
    fail,
    ok,
    parse_int,
    require_admin_token,
    require_fields,
    require_user_id,
    resolve_user_id_for_query,
)

bp = Blueprint("diaries", __name__, url_prefix="/api/diaries")


@bp.post("")
def create_diary():
    payload = request.get_json(silent=True) or {}
    missing = require_fields(payload, ["scene", "event_description", "parent_emotion"])
    if missing:
        return fail("missing_fields", f"缺少必填字段：{', '.join(missing)}")

    try:
        user_id = require_user_id(payload)
    except ValueError as exc:
        return fail("validation_error", str(exc), status=400)
    timestamp = now_iso()
    diary_id = new_id("diary")

    with get_connection() as conn:
        ensure_user(conn, user_id, payload.get("nickname"))
        conn.execute(
            """
            INSERT INTO emotion_diaries (
                id, user_id, goal_id, event_time, scene, event_description,
                parent_emotion, parent_emotion_intensity, child_emotion,
                child_emotion_intensity, automatic_thought, body_sensation,
                behavior, raw_text, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                diary_id,
                user_id,
                payload.get("goal_id"),
                payload.get("event_time"),
                payload["scene"],
                payload["event_description"],
                payload["parent_emotion"],
                parse_int(payload.get("parent_emotion_intensity"), 5),
                payload.get("child_emotion"),
                parse_int(payload.get("child_emotion_intensity"), None),
                payload.get("automatic_thought"),
                payload.get("body_sensation"),
                payload.get("behavior"),
                payload.get("raw_text"),
                timestamp,
                timestamp,
            ),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM emotion_diaries WHERE id = ?", (diary_id,)).fetchone()

    return ok(row_to_dict(row), status=201)


@bp.get("")
def list_diaries():
    requested_user_id = request.args.get("user_id")
    admin_actor = None
    if request.headers.get("X-Admin-Token") and not requested_user_id:
        try:
            admin_actor = require_admin_token()
        except ValueError as exc:
            return admin_token_error_response(exc)

    try:
        user_id = None if admin_actor else resolve_user_id_for_query(requested_user_id)
    except ValueError as exc:
        return fail("validation_error", str(exc), status=400)
    limit = parse_int(request.args.get("limit"), 50)

    with get_connection() as conn:
        if admin_actor:
            rows = conn.execute(
                """
                SELECT * FROM emotion_diaries
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
            write_audit_log(
                conn,
                action="list_diaries_admin",
                actor_id=admin_actor,
                target_type="emotion_diaries",
                target_id="all",
                metadata={"route": "/api/diaries", "limit": limit, "row_count": len(rows)},
            )
        else:
            rows = conn.execute(
                """
                SELECT * FROM emotion_diaries
                WHERE user_id = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (user_id, limit),
            ).fetchall()

    return ok({"items": rows_to_dicts(rows)})
