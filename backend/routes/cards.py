"""Training card endpoints."""

from flask import Blueprint, request

from routes.auth_utils import AuthError, auth_error_response, require_role
from routes.utils import ok, parse_bool, parse_int
from services.card_service import list_cards, recommend_cards

bp = Blueprint("cards", __name__, url_prefix="/api/cards")


@bp.get("")
def get_cards():
    include_unapproved = parse_bool(request.args.get("include_unapproved"), False)
    if include_unapproved:
        try:
            require_role("researcher", "supervisor", "admin")
        except AuthError as exc:
            return auth_error_response(exc)
    return ok({"items": list_cards(enabled_only=True, include_unapproved=include_unapproved), "preview_mode": include_unapproved})


@bp.get("/recommend")
def recommend():
    raw_tags = request.args.get("tags", "")
    tags = [tag.strip() for tag in raw_tags.split(",") if tag.strip()]
    limit = parse_int(request.args.get("limit"), 3)
    return ok({"items": recommend_cards(tags=tags, limit=limit), "matched_tags": tags})
