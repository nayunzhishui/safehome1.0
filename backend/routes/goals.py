"""Goal-setting endpoints."""

from flask import Blueprint, request

from database import ensure_user, get_connection, new_id, now_iso, row_to_dict, rows_to_dicts
from routes.utils import fail, ok, require_fields, require_user_id, resolve_user_id_for_query

bp = Blueprint("goals", __name__, url_prefix="/api/goals")


@bp.post("")
def create_goal():
    payload = request.get_json(silent=True) or {}
    missing = require_fields(payload, ["scene", "smart_goal"])
    if missing:
        return fail("missing_fields", f"缺少必填字段：{', '.join(missing)}")

    try:
        user_id = require_user_id(payload)
    except ValueError as exc:
        return fail("validation_error", str(exc), status=400)
    timestamp = now_iso()
    goal_id = new_id("goal")
    submission_id = str(request.headers.get("Idempotency-Key") or payload.get("client_submission_id") or "").strip()
    if len(submission_id) > 120:
        return fail("validation_error", "提交标识不能超过120个字符。", status=400)

    with get_connection() as conn:
        ensure_user(conn, user_id, payload.get("nickname"))
        if submission_id:
            existing = conn.execute("SELECT * FROM goals WHERE user_id = ? AND client_submission_id = ?", (user_id, submission_id)).fetchone()
            if existing is not None:
                expected = (
                    payload["scene"], payload["smart_goal"], payload.get("motivation"),
                    payload.get("start_date"), payload.get("status", "active"),
                )
                actual = (
                    existing["scene"], existing["smart_goal"], existing["motivation"],
                    existing["start_date"], existing["status"],
                )
                if actual != expected:
                    return fail("idempotency_conflict", "该提交标识已用于另一份目标。", status=409)
                return ok(row_to_dict(existing))
        conn.execute(
            """
            INSERT INTO goals (
                id, user_id, scene, smart_goal, motivation, start_date,
                status, client_submission_id, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                goal_id,
                user_id,
                payload["scene"],
                payload["smart_goal"],
                payload.get("motivation"),
                payload.get("start_date"),
                payload.get("status", "active"),
                submission_id or None,
                timestamp,
                timestamp,
            ),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM goals WHERE id = ?", (goal_id,)).fetchone()

    return ok(row_to_dict(row), status=201)


@bp.get("")
def list_goals():
    try:
        user_id = resolve_user_id_for_query(request.args.get("user_id"))
    except ValueError as exc:
        return fail("validation_error", str(exc), status=400)
    status = request.args.get("status")

    sql = "SELECT * FROM goals WHERE user_id = ?"
    params = [user_id]
    if status:
        sql += " AND status = ?"
        params.append(status)
    sql += " ORDER BY created_at DESC"

    with get_connection() as conn:
        rows = conn.execute(sql, params).fetchall()

    return ok({"items": rows_to_dicts(rows)})
