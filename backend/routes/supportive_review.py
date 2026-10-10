"""L0 supportive self-review (自助整理) for participants.

Only the signed-in participant can read or change their own records; staff
roles and the legacy admin token have no access here.
"""

from flask import Blueprint, request

from routes.auth_utils import AuthError, auth_error_response, require_role
from routes.utils import fail, ok
from services.supportive_review_service import (
    SupportiveReviewError,
    create_review,
    delete_review,
    get_review,
    guide_payload,
    list_reviews,
    update_review,
)


bp = Blueprint("supportive_review", __name__, url_prefix="/api/supportive-review")


def _participant():
    try:
        return require_role("parent", "student", allow_legacy_admin=False), None
    except AuthError as exc:
        return None, auth_error_response(exc)


def _respond(callable_, *args):
    try:
        result = callable_(*args)
    except SupportiveReviewError as exc:
        return fail(exc.code, exc.message, status=exc.status, details=exc.details)
    if isinstance(result, tuple):
        data, status = result
        return ok(data, status=status)
    return ok(result)


@bp.get("/guide")
def get_guide_route():
    actor, error = _participant()
    return error or ok(guide_payload())


@bp.get("/reviews")
def get_reviews_route():
    actor, error = _participant()
    return error or _respond(list_reviews, actor)


@bp.post("/reviews")
def post_review_route():
    actor, error = _participant()
    payload = request.get_json(silent=True) or {}
    idempotency_key = str(request.headers.get("Idempotency-Key") or "")
    return error or _respond(create_review, actor, payload, idempotency_key)


@bp.get("/reviews/<review_id>")
def get_review_route(review_id: str):
    actor, error = _participant()
    return error or _respond(get_review, actor, review_id)


@bp.patch("/reviews/<review_id>")
def patch_review_route(review_id: str):
    actor, error = _participant()
    payload = request.get_json(silent=True) or {}
    return error or _respond(update_review, actor, review_id, payload)


@bp.delete("/reviews/<review_id>")
def delete_review_route(review_id: str):
    actor, error = _participant()
    return error or _respond(delete_review, actor, review_id)
