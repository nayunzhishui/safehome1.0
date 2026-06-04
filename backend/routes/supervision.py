"""Human supervision request endpoints."""

from flask import Blueprint, request

from database import ensure_user, get_connection, new_id, now_iso, row_to_dict
from routes.utils import fail, ok, require_fields, require_user_id
from services.risk_review_service import create_risk_review_record
from services.risk_service import check_text_risk

bp = Blueprint("supervision", __name__, url_prefix="/api/supervision")


@bp.post("")
def create_supervision_request():
    payload = request.get_json(silent=True) or {}
    missing = require_fields(payload, ["message"])
    if missing:
        return fail("missing_fields", f"缺少必填字段：{', '.join(missing)}")

    try:
        user_id = require_user_id(payload)
    except ValueError as exc:
        return fail("validation_error", str(exc), status=400)
    timestamp = now_iso()
    request_id = new_id("supervision")
    risk_result = check_text_risk([payload.get("message"), payload.get("risk_hint")], source="supervision")
    stored_risk_level = risk_result.get("risk_level", "low")
    if stored_risk_level == "low":
        stored_risk_level = payload.get("risk_level", "low")

    with get_connection() as conn:
        ensure_user(conn, user_id, payload.get("nickname"))
        conn.execute(
            """
            INSERT INTO supervision_requests (
                id, user_id, diary_id, message, contact, risk_hint,
                risk_level, status, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, 'pending', ?)
            """,
            (
                request_id,
                user_id,
                payload.get("diary_id"),
                payload["message"],
                payload.get("contact"),
                payload.get("risk_hint"),
                stored_risk_level,
                timestamp,
            ),
        )
        create_risk_review_record(conn, user_id, "supervision", request_id, risk_result)
        conn.commit()
        row = conn.execute(
            "SELECT * FROM supervision_requests WHERE id = ?", (request_id,)
        ).fetchone()

    item = row_to_dict(row)
    item["risk"] = risk_result
    item["boundary_notice"] = risk_result.get("boundary_notice")
    return ok(item, status=201)
