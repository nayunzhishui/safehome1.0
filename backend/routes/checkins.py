"""Practice check-in endpoints."""

from flask import Blueprint, request

from database import ensure_user, get_connection, new_id, now_iso, row_to_dict, rows_to_dicts
from routes.utils import fail, ok, parse_bool, parse_int, require_fields

bp = Blueprint("checkins", __name__, url_prefix="/api/checkins")


@bp.post("")
def create_checkin():
    payload = request.get_json(silent=True) or {}
    missing = require_fields(payload, ["card_id"])
    if missing:
        return fail("missing_fields", f"缺少必填字段：{', '.join(missing)}")

    user_id = payload.get("user_id") or "demo-parent"
    timestamp = now_iso()
    checkin_id = new_id("checkin")

    with get_connection() as conn:
        ensure_user(conn, user_id, payload.get("nickname"))
        conn.execute(
            """
            INSERT INTO checkins (
                id, user_id, card_id, diary_id, completed, emotion_before,
                emotion_after, reflection, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                checkin_id,
                user_id,
                payload["card_id"],
                payload.get("diary_id"),
                1 if parse_bool(payload.get("completed"), True) else 0,
                parse_int(payload.get("emotion_before"), None),
                parse_int(payload.get("emotion_after"), None),
                payload.get("reflection"),
                timestamp,
            ),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM checkins WHERE id = ?", (checkin_id,)).fetchone()

    return ok(row_to_dict(row), status=201)


@bp.get("")
def list_checkins():
    user_id = request.args.get("user_id") or "demo-parent"
    limit = parse_int(request.args.get("limit"), 50)

    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT * FROM checkins
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (user_id, limit),
        ).fetchall()

    return ok({"items": rows_to_dicts(rows)})
