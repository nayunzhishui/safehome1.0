"""Risk review queue endpoints."""

from flask import Blueprint, request

from database import get_connection
from routes.auth_utils import AuthError, auth_error_response, require_role
from routes.utils import fail, ok, parse_int
from services.risk_review_service import list_risk_review_records, update_risk_review_record

bp = Blueprint("risk_review", __name__, url_prefix="/api/risk-review")


@bp.get("")
def list_reviews():
    try:
        require_role("supervisor", "admin", allow_legacy_admin=True)
    except AuthError as exc:
        return auth_error_response(exc)

    status = request.args.get("status")
    limit = parse_int(request.args.get("limit"), 50) or 50
    with get_connection() as conn:
        return ok(list_risk_review_records(conn, status=status, limit=limit))


@bp.post("/<review_id>/review")
def update_review(review_id: str):
    try:
        actor = require_role("supervisor", "admin", allow_legacy_admin=True)
    except AuthError as exc:
        return auth_error_response(exc)

    payload = request.get_json(silent=True) or {}
    reviewer_id = str(payload.get("reviewer_id") or actor["id"])
    review_status = str(payload.get("review_status") or "reviewed")
    review_note = payload.get("review_note") or payload.get("note")
    action_taken = payload.get("action_taken")
    closed_reason = payload.get("closed_reason")

    try:
        with get_connection() as conn:
            row = update_risk_review_record(
                conn,
                review_id=review_id,
                reviewer_id=reviewer_id,
                review_status=review_status,
                review_note=review_note,
                action_taken=action_taken,
                closed_reason=closed_reason,
            )
            if row is None:
                return fail("not_found", "没有找到对应的风险复核记录", status=404)
            conn.commit()
    except ValueError as exc:
        return fail("validation_error", str(exc))

    return ok(row)
