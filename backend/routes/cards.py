"""Training card endpoints."""

from flask import Blueprint, request

from routes.utils import ok, parse_int
from services.card_service import list_cards, recommend_cards

bp = Blueprint("cards", __name__, url_prefix="/api/cards")


@bp.get("")
def get_cards():
    return ok({"items": list_cards(enabled_only=True)})


@bp.get("/recommend")
def recommend():
    raw_tags = request.args.get("tags", "")
    tags = [tag.strip() for tag in raw_tags.split(",") if tag.strip()]
    limit = parse_int(request.args.get("limit"), 3)
    return ok({"items": recommend_cards(tags=tags, limit=limit), "matched_tags": tags})
