"""Emotion diary endpoints."""

from flask import Blueprint, request

from database import ensure_user, get_connection, new_id, now_iso, row_to_dict, rows_to_dicts
from routes.utils import fail, ok, parse_int, require_fields

bp = Blueprint("diaries", __name__, url_prefix="/api/diaries")


@bp.post("")
def create_diary():
    payload = request.get_json(silent=True) or {}
    missing = require_fields(payload, ["scene", "event_description", "parent_emotion"])
    if missing:
        return fail("missing_fields", f"缺少必填字段：{', '.join(missing)}")

    user_id = payload.get("user_id") or "demo-parent"
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
    user_id = request.args.get("user_id") or "demo-parent"
    limit = parse_int(request.args.get("limit"), 50)

    with get_connection() as conn:
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
