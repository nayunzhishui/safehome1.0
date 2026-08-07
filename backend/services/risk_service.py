"""Transparent safety-signal routing for profile and free-text flows.

This module deliberately does not predict suicide/self-harm probability and it
never produces a clinical risk score.  It detects configured safety signals,
adds lightweight context (negated/historical/hypothetical/immediate), and
routes records to human review.
"""

from __future__ import annotations

import re

from services.content_loader import load_risk_keywords

RISK_ORDER = {"low": 0, "medium": 1, "high": 2}
MAX_RISK_TEXT_CHARS = 20_000
DEFAULT_LOW_RISK_RESPONSE = "当前文本未命中需要人工安全复核的配置词。该结果不代表安全评估结论。"
DEFAULT_CONTEXT_WINDOW = 18

# These markers only affect routing context.  They do not prove absence or
# presence of danger.  Contextual high-risk mentions still enter human review.
NEGATION_MARKERS = ("没有", "并没有", "从未", "从没", "不是", "不会", "并不", "否认", "未曾")
HISTORICAL_MARKERS = ("以前", "曾经", "过去", "之前", "小时候", "那时候", "曾有")
HYPOTHETICAL_MARKERS = ("如果", "假如", "比如", "例如", "举例", "新闻", "故事里", "朋友说", "别人说")
IMMEDIACY_MARKERS = ("现在", "马上", "立刻", "今晚", "今天", "此刻", "已经准备", "已经计划", "控制不住")


def _combine_text(value: str | list[str] | None) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        combined = "\n".join(str(item) for item in value if item)
    else:
        combined = str(value)
    return combined[:MAX_RISK_TEXT_CHARS]


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


def _marker_in(text: str, markers: tuple[str, ...]) -> str | None:
    return next((marker for marker in markers if marker and marker in text), None)


def _match_context(text: str, keyword: str, start: int, end: int) -> dict:
    before = text[max(0, start - DEFAULT_CONTEXT_WINDOW) : start]
    after = text[end : min(len(text), end + DEFAULT_CONTEXT_WINDOW)]
    surrounding = before + keyword + after

    # Restrict negation detection to the left side so the "不" inside phrases
    # such as "不想活" is not mistaken for a negating modifier.
    negation = _marker_in(before[-10:], NEGATION_MARKERS)
    historical = _marker_in(surrounding, HISTORICAL_MARKERS)
    hypothetical = _marker_in(surrounding, HYPOTHETICAL_MARKERS)
    immediacy = _marker_in(surrounding, IMMEDIACY_MARKERS)

    if immediacy and not negation and not hypothetical:
        status = "immediate_signal"
    elif negation or historical or hypothetical:
        status = "contextual_signal"
    else:
        status = "direct_signal"
    return {
        "status": status,
        "negation_marker": negation,
        "historical_marker": historical,
        "hypothetical_marker": hypothetical,
        "immediacy_marker": immediacy,
        # Do not return the surrounding raw text.  That would duplicate user
        # free text into operational metadata and increase privacy exposure.
    }


def _keyword_occurrences(text: str, keyword: str) -> list[dict]:
    if not keyword:
        return []
    occurrences: list[dict] = []
    for match in re.finditer(re.escape(keyword), text):
        occurrences.append(
            {
                "keyword": keyword,
                "start": match.start(),
                "context": _match_context(text, keyword, match.start(), match.end()),
            }
        )
    return occurrences


def _category_match(category: dict, text: str) -> dict | None:
    occurrences: list[dict] = []
    for keyword in category.get("keywords", []):
        occurrences.extend(_keyword_occurrences(text, str(keyword or "")))
    if not occurrences:
        return None

    statuses = [item["context"]["status"] for item in occurrences]
    configured_level = str(category.get("risk_level") or "low")
    if configured_level == "high" and all(status == "contextual_signal" for status in statuses):
        effective_level = "medium"
    else:
        effective_level = configured_level

    return {
        "id": category.get("id"),
        "label": category.get("label"),
        "configured_risk_level": configured_level,
        "risk_level": effective_level,
        "matched_keywords": sorted({item["keyword"] for item in occurrences}),
        "signal_contexts": [item["context"] for item in occurrences],
        "has_immediate_signal": any(status == "immediate_signal" for status in statuses),
        "all_contextual": all(status == "contextual_signal" for status in statuses),
        "safe_response": category.get("safe_response"),
    }


def _safety_route(matched_categories: list[dict], risk_level: str) -> str:
    if not matched_categories:
        return "standard"
    if any(item.get("risk_level") == "high" and item.get("has_immediate_signal") for item in matched_categories):
        return "urgent_human_review"
    if risk_level in {"medium", "high"}:
        return "human_review"
    return "standard"


def check_text_risk(text: str | list[str] | None, source: str = "student_profile") -> dict:
    """Detect configured safety signals and return a human-review route.

    The result is intentionally descriptive: it is not a diagnosis, crisis
    assessment, suicide prediction, or low/medium/high clinical stratification.
    `risk_level` remains only as a backwards-compatible field for existing
    callers; new code should use `safety_route`.
    """

    payload = load_risk_keywords()
    combined_text = _combine_text(text)
    matched_categories: list[dict] = []

    if combined_text:
        for category in payload.get("categories", []):
            matched = _category_match(category, combined_text)
            if matched:
                matched_categories.append(matched)

    risk_level = _highest_risk([item.get("risk_level", "low") for item in matched_categories])
    safety_route = _safety_route(matched_categories, risk_level)
    handling = _handling_for_level(payload, risk_level)

    safe_response = DEFAULT_LOW_RISK_RESPONSE
    if matched_categories:
        selected = next(
            (
                item
                for item in matched_categories
                if item.get("risk_level") == risk_level and item.get("safe_response")
            ),
            matched_categories[0],
        )
        safe_response = selected.get("safe_response") or DEFAULT_LOW_RISK_RESPONSE

    # Any non-standard route requires human review.  Context-aware downgrade
    # reduces false crisis escalation but does not discard the signal.
    requires_review = safety_route != "standard" or bool(handling.get("requires_review", False))
    allow_auto_feedback = bool(handling.get("allow_auto_feedback", risk_level != "high"))
    allow_cards = bool(handling.get("allow_recommended_training_cards", risk_level != "high"))
    if safety_route == "urgent_human_review":
        allow_auto_feedback = False
        allow_cards = False

    return {
        "source": source,
        "risk_level": risk_level,
        "safety_route": safety_route,
        "matched_categories": matched_categories,
        "requires_review": requires_review,
        "allow_auto_feedback": allow_auto_feedback,
        "allow_recommended_training_cards": allow_cards,
        "export_raw_text_by_default": False,
        "safe_response": safe_response,
        "context_engine_version": "context-v2",
        "boundary_notice": "安全信号只用于人工复核分流，不构成诊断、危机评估、风险概率或处置结论。",
    }
