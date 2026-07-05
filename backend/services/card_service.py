"""Training card loading and recommendation service."""

from database import load_content_json


def list_cards(enabled_only: bool = True) -> list[dict]:
    payload = load_content_json("training_cards.json")
    cards = payload.get("cards", [])
    if enabled_only:
        cards = [card for card in cards if card.get("enabled", True)]
    return cards


def recommend_cards(tags: list[str] | None = None, limit: int = 3) -> list[dict]:
    tags = [tag for tag in (tags or []) if tag]
    cards = list_cards(enabled_only=True)
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
