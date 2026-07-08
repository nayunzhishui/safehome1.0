"""Progress summary endpoints for staged, non-diagnostic feedback."""

from flask import Blueprint, request

from routes.auth_utils import AuthError, auth_error_response, resolve_actor_user_id
from routes.utils import ok
from services.progress_summary_service import (
    build_profile_convergence,
    build_progress_summary,
    build_training_effectiveness,
)


bp = Blueprint("progress_summary", __name__, url_prefix="/api")


@bp.get("/progress-summary")
def get_progress_summary():
    try:
        user_id = resolve_actor_user_id(request.args.get("user_id"))
    except AuthError as exc:
        return auth_error_response(exc)
    range_key = request.args.get("range") or "7d"
    return ok(build_progress_summary(user_id=user_id, range_key=range_key))


@bp.get("/profile-trend")
def get_profile_trend():
    try:
        user_id = resolve_actor_user_id(request.args.get("user_id"))
    except AuthError as exc:
        return auth_error_response(exc)
    return ok(build_profile_convergence(user_id=user_id, worksheet_id=request.args.get("worksheet_id")))


@bp.get("/training-effectiveness")
def get_training_effectiveness():
    try:
        user_id = resolve_actor_user_id(request.args.get("user_id"))
    except AuthError as exc:
        return auth_error_response(exc)
    range_key = request.args.get("range") or "30d"
    return ok(build_training_effectiveness(user_id=user_id, range_key=range_key))
