"""Keyword-based safety risk checks for profile and text flows."""

from services.content_loader import load_risk_keywords

RISK_ORDER = {"low": 0, "medium": 1, "high": 2}

DEFAULT_LOW_RISK_RESPONSE = "当前文本未命中高风险关键词。该结果只用于初步提示，不代表安全评估结论。"


def _combine_text(value: str | list[str] | None) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        return "\n".join(str(item) for item in value if item)
    return str(value)


def _highest_risk(levels: list[str]) -> str:
    if not levels:
        return "low"
    return max(levels, key=lambda level: RISK_ORDER.get(level, 0))


def _handling_for_level(payload: dict, risk_level: str) -> dict:
    for rule in payload.get("handling_rules", []):
        if rule.get("risk_level") == risk_level:
            return rule
    return {
        "risk_level": risk_level,
        "requires_review": risk_level in {"medium", "high"},
        "allow_auto_feedback": risk_level != "high",
        "allow_recommended_training_cards": risk_level != "high",
        "export_raw_text_by_default": False,
    }


def check_text_risk(text: str | list[str] | None, source: str = "student_profile") -> dict:
    """Check text against configured risk keywords.

    This is a transparent keyword screen for routing and review. It is not a
    clinical risk assessment and should not be shown as a diagnostic result.
    """

    payload = load_risk_keywords()
    combined_text = _combine_text(text)
    matched_categories = []

    if combined_text:
        for category in payload.get("categories", []):
            keywords = category.get("keywords", [])
            matched_keywords = [keyword for keyword in keywords if keyword and keyword in combined_text]
            if matched_keywords:
                matched_categories.append(
                    {
                        "id": category.get("id"),
                        "label": category.get("label"),
                        "risk_level": category.get("risk_level", "low"),
                        "matched_keywords": matched_keywords,
                        "safe_response": category.get("safe_response"),
                    }
                )

    risk_level = _highest_risk([item.get("risk_level", "low") for item in matched_categories])
    handling = _handling_for_level(payload, risk_level)
    safe_response = DEFAULT_LOW_RISK_RESPONSE
    if matched_categories:
        safe_response = next(
            (item.get("safe_response") for item in matched_categories if item.get("risk_level") == risk_level and item.get("safe_response")),
            matched_categories[0].get("safe_response") or DEFAULT_LOW_RISK_RESPONSE,
        )

    return {
        "source": source,
        "risk_level": risk_level,
        "matched_categories": matched_categories,
        "requires_review": bool(handling.get("requires_review", False)),
        "allow_auto_feedback": bool(handling.get("allow_auto_feedback", risk_level != "high")),
        "allow_recommended_training_cards": bool(handling.get("allow_recommended_training_cards", risk_level != "high")),
        "export_raw_text_by_default": bool(handling.get("export_raw_text_by_default", False)),
        "safe_response": safe_response,
        "boundary_notice": "风险关键词只用于初步提示和人工复核分流，不构成诊断或危机评估结论。",
    }

