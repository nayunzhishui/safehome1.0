"""Rule-based non-diagnostic feedback generation."""

from database import load_content_json
from services.card_service import get_card_ids, recommend_cards

RISK_ORDER = {"low": 0, "medium": 1, "high": 2}


def _combine_text(payload: dict) -> str:
    parts = [
        payload.get("event_description"),
        payload.get("automatic_thought"),
        payload.get("behavior"),
        payload.get("raw_text"),
    ]
    return "\n".join(str(part) for part in parts if part)


def _highest_risk(levels: list[str]) -> str:
    if not levels:
        return "low"
    return max(levels, key=lambda level: RISK_ORDER.get(level, 0))


def generate_feedback(payload: dict) -> dict:
    """Generate supportive feedback from content/feedback_rules.json.

    This function deliberately uses transparent rules instead of AI calls.
    Feedback stays non-diagnostic and focuses on observable language/patterns.
    """

    rules_payload = load_content_json("feedback_rules.json")
    text = _combine_text(payload)
    matched_rules = []

    for rule in rules_payload.get("rules", []):
        keywords = rule.get("match_keywords", [])
        if any(keyword and keyword in text for keyword in keywords):
            matched_rules.append(rule)

    if not matched_rules:
        matched_rules = [
            {
                "id": "general_support",
                "label": "一般情绪记录",
                "explanation": "这次记录提供了一个观察亲子互动的入口。第一步不是判断谁对谁错，而是看见当时的情绪、想法和行为。",
                "supportive_feedback": "你愿意把这个场景记录下来，已经是在为关系创造新的可能。可以先从命名情绪和暂停 3 秒开始。",
                "alternative_response": "先说出一个观察句，例如：我看到这件事让我们都有些着急，我们先把第一步找出来。",
                "recommended_card_ids": ["emotion_naming", "three_second_pause"],
                "risk_level": "low",
            }
        ]

    tags = [rule["id"] for rule in matched_rules]
    labels = [rule.get("label", rule["id"]) for rule in matched_rules]
    recommended_ids = []
    for rule in matched_rules:
        recommended_ids.extend(rule.get("recommended_card_ids", []))
    if not recommended_ids:
        recommended_ids = get_card_ids(recommend_cards(tags))

    recommended_ids = list(dict.fromkeys(recommended_ids))

    return {
        "tags": tags,
        "labels": labels,
        "trigger_summary": "本次记录中可先关注：" + "、".join(labels) + "。",
        "pattern_summary": "这些标签只描述本次互动中可观察到的语言或行为模式，不代表对家长或孩子的诊断。",
        "supportive_feedback": matched_rules[0]["supportive_feedback"],
        "alternative_response": matched_rules[0].get("alternative_response", ""),
        "recommended_card_ids": recommended_ids,
        "risk_level": _highest_risk([rule.get("risk_level", "low") for rule in matched_rules]),
    }
