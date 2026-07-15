"""Training card loading and recommendation service."""

from flask import current_app, has_app_context

from database import load_content_json
from services.showcase_access_service import showcase_training_cards_open


APPROVED_REVIEW_STATUSES = {"pilot_approved", "production_approved", "enabled", "trial_enabled"}


def _is_production() -> bool:
    return has_app_context() and str(current_app.config.get("APP_ENV", "development")).lower() == "production"


def list_cards(enabled_only: bool = True, include_unapproved: bool = False) -> list[dict]:
    payload = load_content_json("training_cards.json")
    cards = payload.get("cards", [])
    if enabled_only:
        cards = [card for card in cards if card.get("enabled", True)]
    if _is_production() and not include_unapproved and not showcase_training_cards_open():
        cards = [card for card in cards if card.get("review_status") in APPROVED_REVIEW_STATUSES]
    return cards


def recommend_cards(tags: list[str] | None = None, limit: int = 3) -> list[dict]:
    tags = [tag for tag in (tags or []) if tag]
    cards = [
        card
        for card in list_cards(enabled_only=True)
        if card.get("release_policy", "shared_choice_candidate") == "shared_choice_candidate"
    ]
    if not tags:
        return cards[:limit]

    tag_set = set(tags)

    def score(card: dict) -> int:
        return len(tag_set.intersection(card.get("tags", [])))

    ranked = sorted(cards, key=lambda card: (score(card), card.get("id", "")), reverse=True)
    matched = [card for card in ranked if score(card) > 0]
    if matched:
        return matched[:limit]

    cards_by_type: dict[str, list[dict]] = {}
    for card in cards:
        cards_by_type.setdefault(card.get("type") or "general", []).append(card)
    diverse_cards = [type_cards[0] for type_cards in cards_by_type.values()]
    return diverse_cards[:limit]


def get_card_ids(cards: list[dict]) -> list[str]:
    return [card["id"] for card in cards if "id" in card]
