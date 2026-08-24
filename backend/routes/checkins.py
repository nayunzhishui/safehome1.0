"""Practice check-in endpoints."""

from flask import Blueprint, request

from database import ensure_user, get_connection, load_content_json, new_id, now_iso, row_to_dict, rows_to_dicts, write_audit_log
from routes.auth_utils import AuthError, auth_error_response, resolve_actor_user_id
from routes.utils import fail, ok, parse_bool, parse_int, require_fields
from services.idempotency_service import (
    IdempotencyConflictError,
    IdempotencyValidationError,
    canonical_request_hash,
    public_idempotent_resource,
    record_side_effect,
    reserve_idempotency,
    store_idempotency_response,
)

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
    completed = parse_bool(payload.get("completed"), True)
    idempotency_payload = {
        "card_id": payload["card_id"],
        "diary_id": payload.get("diary_id"),
        "completed": completed,
        "emotion_before": parse_int(payload.get("emotion_before"), None),
        "emotion_after": parse_int(payload.get("emotion_after"), None),
        "reflection": str(payload.get("reflection") or ""),
        "helpfulness_rating": payload.get("helpfulness_rating"),
        "skip_reason": payload.get("skip_reason"),
        "source_recommendation_id": payload.get("source_recommendation_id"),
        "before_thermometer_id": payload.get("before_thermometer_id"),
        "after_thermometer_id": payload.get("after_thermometer_id"),
    }
    try:
        request_hash = canonical_request_hash(
            actor_id=user_id,
            endpoint="POST /api/checkins",
            version="v1",
            payload=idempotency_payload,
        ) if submission_id else None
    except IdempotencyValidationError as exc:
        return fail(exc.code, exc.message, status=400)

    with get_connection() as conn:
        ensure_user(conn, user_id, payload.get("nickname"))
        reservation = None
        if submission_id:
            try:
                reservation = reserve_idempotency(
                    conn,
                    actor_id=user_id,
                    endpoint="POST /api/checkins",
                    idempotency_key=submission_id,
                    request_hash=request_hash,
                    resource_type="checkin",
                    resource_id=checkin_id,
                )
            except IdempotencyConflictError:
                return fail("idempotency_conflict", "该提交标识已用于另一份练习记录。", status=409)
            if not reservation.created:
                if reservation.response is not None:
                    item = public_idempotent_resource(reservation.response)
                    item["idempotency_replayed"] = True
                    return ok(item)
                existing = conn.execute(
                    "SELECT * FROM checkins WHERE id = ? AND user_id = ?",
                    (reservation.resource_id, user_id),
                ).fetchone()
                if existing is None:
                    return fail("idempotency_state_conflict", "原提交结果不可用。", status=409)
                item = public_idempotent_resource(row_to_dict(existing))
                item["idempotency_replayed"] = True
                return ok(item)
        conn.execute(
            """
            INSERT INTO checkins (
                id, user_id, card_id, diary_id, completed, emotion_before,
                emotion_after, reflection, helpfulness_rating, skip_reason,
                source_recommendation_id, before_thermometer_id,
                after_thermometer_id, client_submission_id, request_hash, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                checkin_id,
                user_id,
                payload["card_id"],
                payload.get("diary_id"),
                1 if completed else 0,
                parse_int(payload.get("emotion_before"), None),
                parse_int(payload.get("emotion_after"), None),
                payload.get("reflection"),
                payload.get("helpfulness_rating"),
                payload.get("skip_reason"),
                payload.get("source_recommendation_id"),
                payload.get("before_thermometer_id"),
                payload.get("after_thermometer_id"),
                submission_id or None,
                request_hash,
                timestamp,
            ),
        )
        event_name = "journey_action_completed" if completed else "journey_action_skipped"
        should_write_audit = reservation is None or record_side_effect(
            conn,
            idempotency_record_id=reservation.id,
            effect_type="audit",
            effect_key=f"product_event_{event_name}",
            status="committed",
            metadata={"resource_id": checkin_id},
        )
        if should_write_audit:
            write_audit_log(
                conn,
                f"product_event_{event_name}",
                user_id,
                "product_event",
                submission_id or checkin_id,
                {
                    "event_name": event_name,
                    "action": "practice_due",
                    "stage": "training",
                    "status": "completed" if completed else "skipped",
                    "source": "today_journey",
                },
            )
        row = conn.execute("SELECT * FROM checkins WHERE id = ?", (checkin_id,)).fetchone()
        item = public_idempotent_resource(row_to_dict(row))
        item["idempotency_replayed"] = False
        if submission_id:
            store_idempotency_response(
                conn,
                idempotency_record_id=reservation.id,
                response=item,
                response_status=201,
            )
        conn.commit()

    return ok(item, status=201)


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
        total_row = conn.execute(
            f"SELECT COUNT(*) AS count FROM checkins WHERE {where_sql}",
            tuple(query_params),
        ).fetchone()
        total = int(total_row["count"] if total_row else 0)
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
        row = public_idempotent_resource(row)
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
