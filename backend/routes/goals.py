"""Goal-setting endpoints."""

from flask import Blueprint, request

from database import ensure_user, get_connection, new_id, now_iso, row_to_dict, rows_to_dicts
from routes.utils import fail, ok, require_fields, require_user_id, resolve_user_id_for_query
from services.idempotency_service import (
    IdempotencyConflictError,
    IdempotencyValidationError,
    canonical_request_hash,
    public_idempotent_resource,
    reserve_idempotency,
    store_idempotency_response,
)

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
    idempotency_payload = {
        "scene": payload["scene"],
        "smart_goal": payload["smart_goal"],
        "motivation": payload.get("motivation"),
        "start_date": payload.get("start_date"),
        "status": payload.get("status", "active"),
    }
    try:
        request_hash = canonical_request_hash(
            actor_id=user_id,
            endpoint="POST /api/goals",
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
                    endpoint="POST /api/goals",
                    idempotency_key=submission_id,
                    request_hash=request_hash,
                    resource_type="goal",
                    resource_id=goal_id,
                )
            except IdempotencyConflictError:
                return fail("idempotency_conflict", "该提交标识已用于另一份目标。", status=409)
            if not reservation.created:
                if reservation.response is not None:
                    item = public_idempotent_resource(reservation.response)
                    item["idempotency_replayed"] = True
                    return ok(item)
                existing = conn.execute(
                    "SELECT * FROM goals WHERE id = ? AND user_id = ?",
                    (reservation.resource_id, user_id),
                ).fetchone()
                if existing is None:
                    return fail("idempotency_state_conflict", "原提交结果不可用。", status=409)
                item = public_idempotent_resource(row_to_dict(existing))
                item["idempotency_replayed"] = True
                return ok(item)
        conn.execute(
            """
            INSERT INTO goals (
                id, user_id, scene, smart_goal, motivation, start_date,
                status, client_submission_id, request_hash, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                request_hash,
                timestamp,
                timestamp,
            ),
        )
        row = conn.execute("SELECT * FROM goals WHERE id = ?", (goal_id,)).fetchone()
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

    return ok({"items": [public_idempotent_resource(item) for item in rows_to_dicts(rows)]})
