"""Practice check-in endpoints."""

from flask import Blueprint, request

from database import ensure_user, get_connection, load_content_json, new_id, now_iso, row_to_dict, rows_to_dicts
from routes.auth_utils import AuthError, auth_error_response, resolve_actor_user_id
from routes.utils import fail, ok, parse_bool, parse_int, require_fields

bp = Blueprint("checkins", __name__, url_prefix="/api/checkins")


@bp.post("")
def create_checkin():
    payload = request.get_json(silent=True) or {}
    missing = require_fields(payload, ["card_id"])
    if missing:
        return fail("missing_fields", f"缺少必填字段：{', '.join(missing)}")

    try:
        user_id = resolve_actor_user_id(payload=payload)
    except AuthError as exc:
        return auth_error_response(exc)
    timestamp = now_iso()
    checkin_id = new_id("checkin")
    submission_id = str(request.headers.get("Idempotency-Key") or payload.get("client_submission_id") or "").strip()
    if len(submission_id) > 120:
        return fail("validation_error", "提交标识不能超过120个字符。", status=400)

    with get_connection() as conn:
        ensure_user(conn, user_id, payload.get("nickname"))
        if submission_id:
            existing = conn.execute(
                "SELECT * FROM checkins WHERE user_id = ? AND client_submission_id = ?",
                (user_id, submission_id),
            ).fetchone()
            if existing is not None:
                expected = (
                    payload["card_id"],
                    payload.get("diary_id"),
                    1 if parse_bool(payload.get("completed"), True) else 0,
                    parse_int(payload.get("emotion_before"), None),
                    parse_int(payload.get("emotion_after"), None),
                    str(payload.get("reflection") or ""),
                    payload.get("helpfulness_rating"),
                    payload.get("skip_reason"),
                    payload.get("source_recommendation_id"),
                    payload.get("before_thermometer_id"),
                    payload.get("after_thermometer_id"),
                )
                actual = (
                    existing["card_id"], existing["diary_id"], existing["completed"],
                    existing["emotion_before"], existing["emotion_after"], str(existing["reflection"] or ""),
                    existing["helpfulness_rating"], existing["skip_reason"], existing["source_recommendation_id"],
                    existing["before_thermometer_id"], existing["after_thermometer_id"],
                )
                if actual != expected:
                    return fail("idempotency_conflict", "该提交标识已用于另一份练习记录。", status=409)
                return ok(row_to_dict(existing))
        conn.execute(
            """
            INSERT INTO checkins (
                id, user_id, card_id, diary_id, completed, emotion_before,
                emotion_after, reflection, helpfulness_rating, skip_reason,
                source_recommendation_id, before_thermometer_id,
                after_thermometer_id, client_submission_id, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                payload.get("helpfulness_rating"),
                payload.get("skip_reason"),
                payload.get("source_recommendation_id"),
                payload.get("before_thermometer_id"),
                payload.get("after_thermometer_id"),
                submission_id or None,
                timestamp,
            ),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM checkins WHERE id = ?", (checkin_id,)).fetchone()

    return ok(row_to_dict(row), status=201)


@bp.get("")
def list_checkins():
    try:
        user_id = resolve_actor_user_id(request.args.get("user_id"))
    except AuthError as exc:
        return auth_error_response(exc)
    page = max(1, parse_int(request.args.get("page"), 1) or 1)
    page_size = parse_int(request.args.get("page_size"), None)
    if page_size is None:
        page_size = parse_int(request.args.get("limit"), 50)
    page_size = max(1, min(page_size or 50, 100))
    offset = (page - 1) * page_size
    completed_arg = request.args.get("completed")
    completed_filter = None if completed_arg is None else (1 if parse_bool(completed_arg, False) else 0)
    where_sql = "user_id = ?"
    query_params: list = [user_id]
    if completed_filter is not None:
        where_sql += " AND completed = ?"
        query_params.append(completed_filter)

    with get_connection() as conn:
        total = conn.execute(
            f"SELECT COUNT(*) FROM checkins WHERE {where_sql}",
            tuple(query_params),
        ).fetchone()[0]
        rows = conn.execute(
            f"""
            SELECT * FROM checkins
            WHERE {where_sql}
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
            """,
            (*query_params, page_size, offset),
        ).fetchall()

    cards = {
        card.get("id"): card
        for card in load_content_json("training_cards.json").get("cards", [])
        if card.get("id")
    }
    items = []
    for row in rows_to_dicts(rows):
        card = cards.get(row.get("card_id"), {})
        items.append(
            {
                **row,
                "card_title": card.get("title") or row.get("card_id"),
                "card_duration_minutes": card.get("duration_minutes"),
                "card_safety_level": card.get("safety_level"),
            }
        )

    return ok(
        {
            "items": items,
            "page": page,
            "page_size": page_size,
            "total": total,
            "has_more": offset + len(items) < total,
        }
    )
