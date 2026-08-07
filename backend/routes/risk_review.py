"""Risk review queue endpoints."""

from flask import Blueprint, request

from database import get_connection
from routes.auth_utils import AuthError, auth_error_response, require_role
from routes.utils import fail, ok, parse_int
from services.input_validation_service import InputValidationError, validate_review_fields
from services.risk_review_service import list_risk_review_records, update_risk_review_record

bp = Blueprint("risk_review", __name__, url_prefix="/api/risk-review")


@bp.get("")
def list_reviews():
    try:
        require_role("supervisor", "admin", allow_legacy_admin=True)
    except AuthError as exc:
        return auth_error_response(exc)

    status = request.args.get("status")
    limit = max(1, min(parse_int(request.args.get("limit"), 50) or 50, 200))
    try:
        with get_connection() as conn:
            return ok(list_risk_review_records(conn, status=status, limit=limit))
    except ValueError as exc:
        return fail("validation_error", str(exc), status=400)


@bp.post("/<review_id>/review")
def update_review(review_id: str):
    try:
        actor = require_role("supervisor", "admin", allow_legacy_admin=True)
    except AuthError as exc:
        return auth_error_response(exc)

    raw_payload = request.get_json(silent=True) or {}
    # Security invariant: the reviewer/audit actor always comes from the
    # authenticated session. A client-supplied reviewer_id can never select
    # the audit identity. Keep a strict compatibility check so stale clients
    # fail visibly instead of silently attributing work to another person.
    supplied_reviewer_id = str(raw_payload.get("reviewer_id") or "").strip()
    authenticated_reviewer_id = str(actor["id"])
    if supplied_reviewer_id and supplied_reviewer_id != authenticated_reviewer_id:
        return fail(
            "reviewer_identity_mismatch",
            "复核人身份必须与当前登录账号一致。",
            status=403,
        )

    try:
        payload = validate_review_fields(
            {
                **raw_payload,
                "review_note": raw_payload.get("review_note") or raw_payload.get("note"),
            }
        )
    except InputValidationError as exc:
        return fail(exc.code, exc.message, status=400, details={"field": exc.field})

    review_status = str(payload.get("review_status") or "reviewed")
    review_note = payload.get("review_note")
    action_taken = payload.get("action_taken")
    closed_reason = payload.get("closed_reason")

    try:
        with get_connection() as conn:
            row = update_risk_review_record(
                conn,
                review_id=review_id,
                reviewer_id=authenticated_reviewer_id,
                reviewer_role=str(actor.get("role") or "supervisor"),
                review_status=review_status,
                review_note=review_note,
                action_taken=action_taken,
                closed_reason=closed_reason,
            )
            if row is None:
                return fail("not_found", "没有找到对应的风险复核记录", status=404)
            conn.commit()
    except ValueError as exc:
        return fail("validation_error", str(exc), status=400)

    return ok(row)
