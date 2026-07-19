"""Participant journey endpoints."""

from flask import Blueprint, request

from routes.auth_utils import AuthError, auth_error_response, require_login
from routes.utils import ok
from services.participant_action_planner import build_today_journey


bp = Blueprint("journey", __name__, url_prefix="/api/journey")


@bp.get("/today")
def get_today_journey():
    try:
        actor = require_login(allow_legacy_admin=False)
        if actor.get("role") not in {"parent", "student"}:
            raise AuthError("当前接口只供参与者本人使用", status=403)
        user_id = str(actor["id"])
        requested_user_id = str(request.args.get("user_id") or "").strip()
        if requested_user_id and requested_user_id != user_id:
            raise AuthError("只能查看自己的今日安排", status=403)
    except AuthError as exc:
        return auth_error_response(exc)
    return ok(build_today_journey(user_id))
