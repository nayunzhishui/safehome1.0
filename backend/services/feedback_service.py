"""Rule-based non-diagnostic feedback generation."""

from database import load_content_json
from services.card_service import get_card_ids, recommend_cards

RISK_ORDER = {"low": 0, "medium": 1, "high": 2}


def _combine_text(payload: dict) -> str:
    parts = [
        payload.get("scene"),
        payload.get("event_description"),
        payload.get("parent_emotion"),
        payload.get("child_emotion"),
        payload.get("automatic_thought"),
        payload.get("body_sensation"),
        payload.get("behavior"),
        payload.get("raw_text"),
    ]
    return "\n".join(str(part) for part in parts if part)


def _highest_risk(levels: list[str]) -> str:
    if not levels:
        return "low"
    return max(levels, key=lambda level: RISK_ORDER.get(level, 0))


def _intensity_text(value) -> str:
    try:
        level = int(value)
    except (TypeError, ValueError):
        return "未记录"
    if level >= 8:
        return "较强"
    if level >= 4:
        return "中等"
    return "较轻"


def _emotion_overview(payload: dict) -> dict:
    primary_emotion = str(payload.get("parent_emotion") or payload.get("child_emotion") or "").strip()
    scene = str(payload.get("scene") or "").strip()
    intensity = payload.get("parent_emotion_intensity")
    if intensity is None:
        intensity = payload.get("child_emotion_intensity")
    return {
        "primary_emotion": primary_emotion or "这次记录中的感受",
        "intensity_level": intensity,
        "intensity_text": _intensity_text(intensity),
        "scene": scene or "这次互动",
    }


def _trigger_summary(payload: dict, overview: dict) -> str:
    scene = overview["scene"]
    emotion = overview["primary_emotion"]
    return f"这次记录发生在“{scene}”场景，当时较明显的感受是“{emotion}”。可以继续观察它从哪一刻开始升高。"


def _pattern_summary(payload: dict, labels: list[str]) -> str:
    behavior = str(payload.get("behavior") or "").strip()
    thought = str(payload.get("automatic_thought") or "").strip()
    if behavior and thought:
        return f"当时先出现了“{thought}”这样的想法，随后记录到的回应是“{behavior}”。可以观察两者是否相互推动。"
    if behavior:
        return f"这次记录到的回应是“{behavior}”。可以回看它出现前，情绪或身体感受发生了什么变化。"
    if thought:
        return f"这次记录到的自动想法是“{thought}”。可以把它和可观察事实分开看一看。"
    visible_labels = [label for label in labels if label != "一般情绪记录"]
    if visible_labels:
        return "这次记录中可以继续观察：" + "、".join(visible_labels) + "。这些只是本次互动线索，不代表固定评价。"
    return "这次暂时没有记录具体想法或回应方式，可以在下一次补充“我当时想了什么、随后做了什么”。"


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
    overview = _emotion_overview(payload)

    return {
        "tags": tags,
        "labels": labels,
        "emotion_overview": overview,
        "trigger_summary": _trigger_summary(payload, overview),
        "pattern_summary": _pattern_summary(payload, labels),
        "supportive_feedback": matched_rules[0]["supportive_feedback"],
        "alternative_response": matched_rules[0].get("alternative_response", ""),
        "recommended_card_ids": recommended_ids,
        "risk_level": _highest_risk([rule.get("risk_level", "low") for rule in matched_rules]),
    }
