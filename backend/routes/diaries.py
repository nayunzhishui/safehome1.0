"""Emotion diary endpoints."""

from flask import Blueprint, request

from database import ensure_user, get_connection, new_id, now_iso, row_to_dict, rows_to_dicts, write_audit_log
from routes.auth_utils import AuthError, auth_error_response, resolve_actor_user_id
from routes.utils import (
    admin_token_error_response,
    fail,
    ok,
    parse_int,
    require_admin_token,
    require_fields,
)
from services.input_validation_service import InputValidationError, validate_diary_payload
from services.idempotency_service import (
    IdempotencyConflictError,
    IdempotencyValidationError,
    canonical_request_hash,
    public_idempotent_resource,
    reserve_idempotency,
    store_idempotency_response,
)

bp = Blueprint("diaries", __name__, url_prefix="/api/diaries")


@bp.post("")
def create_diary():
    raw_payload = request.get_json(silent=True) or {}
    missing = require_fields(raw_payload, ["scene", "event_description", "parent_emotion"])
    if missing:
        return fail("missing_fields", f"缺少必填字段：{', '.join(missing)}")
    try:
        payload = validate_diary_payload(raw_payload)
    except InputValidationError as exc:
        return fail(exc.code, exc.message, status=400, details={"field": exc.field})

    try:
        user_id = resolve_actor_user_id(payload=payload)
    except AuthError as exc:
        return auth_error_response(exc)
    timestamp = now_iso()
    diary_id = new_id("diary")
    submission_id = str(request.headers.get("Idempotency-Key") or payload.get("client_submission_id") or "").strip()
    if len(submission_id) > 120:
        return fail("validation_error", "提交标识不能超过120个字符。", status=400)
    idempotency_payload = {
        "goal_id": payload.get("goal_id"),
        "event_time": payload.get("event_time"),
        "scene": payload["scene"],
        "event_description": payload["event_description"],
        "parent_emotion": payload["parent_emotion"],
        "parent_emotion_intensity": payload["parent_emotion_intensity"],
        "child_emotion": payload.get("child_emotion"),
        "child_emotion_intensity": payload.get("child_emotion_intensity"),
        "automatic_thought": payload.get("automatic_thought"),
        "body_sensation": payload.get("body_sensation"),
        "behavior": payload.get("behavior"),
        "raw_text": payload.get("raw_text"),
    }
    try:
        request_hash = canonical_request_hash(
            actor_id=user_id,
            endpoint="POST /api/diaries",
            version="v1",
            payload=idempotency_payload,
        ) if submission_id else None
    except IdempotencyValidationError as exc:
        return fail(exc.code, exc.message, status=400)

    with get_connection() as conn:
        ensure_user(conn, user_id, payload.get("nickname"))
        if submission_id:
            try:
                reservation = reserve_idempotency(
                    conn,
                    actor_id=user_id,
                    endpoint="POST /api/diaries",
                    idempotency_key=submission_id,
                    request_hash=request_hash,
                    resource_type="diary",
                    resource_id=diary_id,
                )
            except IdempotencyConflictError:
                return fail("idempotency_conflict", "该提交标识已用于另一份情绪记录。", status=409)
            if not reservation.created:
                if reservation.response is not None:
                    item = public_idempotent_resource(reservation.response)
                    item["idempotency_replayed"] = True
                    return ok(item)
                existing = conn.execute(
                    "SELECT * FROM emotion_diaries WHERE id = ? AND user_id = ?",
                    (reservation.resource_id, user_id),
                ).fetchone()
                if existing is None:
                    return fail("idempotency_state_conflict", "原提交结果不可用。", status=409)
                item = public_idempotent_resource(row_to_dict(existing))
                item["idempotency_replayed"] = True
                return ok(item)
        conn.execute(
            """
            INSERT INTO emotion_diaries (
                id, user_id, goal_id, event_time, scene, event_description,
                parent_emotion, parent_emotion_intensity, child_emotion,
                child_emotion_intensity, automatic_thought, body_sensation,
                behavior, raw_text, client_submission_id, request_hash, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                diary_id,
                user_id,
                payload.get("goal_id"),
                payload.get("event_time"),
                payload["scene"],
                payload["event_description"],
                payload["parent_emotion"],
                payload["parent_emotion_intensity"],
                payload.get("child_emotion"),
                payload.get("child_emotion_intensity"),
                payload.get("automatic_thought"),
                payload.get("body_sensation"),
                payload.get("behavior"),
                payload.get("raw_text"),
                submission_id or None,
                request_hash,
                timestamp,
                timestamp,
            ),
        )
        row = conn.execute("SELECT * FROM emotion_diaries WHERE id = ?", (diary_id,)).fetchone()
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
def list_diaries():
    requested_user_id = request.args.get("user_id")
    admin_actor = None
    if request.headers.get("X-Admin-Token") and not requested_user_id:
        try:
            admin_actor = require_admin_token()
        except ValueError as exc:
            return admin_token_error_response(exc)

    try:
        user_id = None if admin_actor else resolve_actor_user_id(requested_user_id)
    except AuthError as exc:
        return auth_error_response(exc)
    limit = max(1, min(parse_int(request.args.get("limit"), 50) or 50, 200))
    date_filter = str(request.args.get("date") or "").strip()
    if date_filter and (len(date_filter) != 10 or date_filter[4:5] != "-" or date_filter[7:8] != "-"):
        return fail("validation_error", "date 必须使用 YYYY-MM-DD 格式。", status=400)

    with get_connection() as conn:
        if admin_actor:
            if date_filter:
                rows = conn.execute(
                    """
                    SELECT * FROM emotion_diaries
                    WHERE substr(COALESCE(event_time, created_at), 1, 10) = ?
                    ORDER BY created_at DESC
                    LIMIT ?
                    """,
                    (date_filter, limit),
                ).fetchall()
            else:
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
                metadata={"route": "/api/diaries", "limit": limit, "date": date_filter or None, "row_count": len(rows)},
            )
        else:
            if date_filter:
                rows = conn.execute(
                    """
                    SELECT * FROM emotion_diaries
                    WHERE user_id = ?
                      AND substr(COALESCE(event_time, created_at), 1, 10) = ?
                    ORDER BY created_at DESC
                    LIMIT ?
                    """,
                    (user_id, date_filter, limit),
                ).fetchall()
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

    return ok({"items": [public_idempotent_resource(item) for item in rows_to_dicts(rows)]})
