"""Transparent safety-signal routing for profile and free-text flows.

This module deliberately does not predict suicide/self-harm probability and it
never produces a clinical risk score.  It detects configured safety signals,
adds lightweight context (negated/historical/hypothetical/quoted/immediate),
and routes records to human review.
"""

from __future__ import annotations

import re

from services.content_loader import load_risk_keywords

RISK_ORDER = {"low": 0, "medium": 1, "high": 2}
MAX_RISK_TEXT_CHARS = 20_000
DEFAULT_LOW_RISK_RESPONSE = "当前文本未命中需要人工安全复核的配置词。该结果不代表安全评估结论。"
DEFAULT_CONTEXT_WINDOW = 18
CONTEXT_ENGINE_VERSION = "context-v3"

# Fallbacks for content/risk_keywords.json context_rules, which is the source of
# truth.  These markers only affect routing context.  They do not prove absence
# or presence of danger.  Contextual high-risk mentions still enter human review.
NEGATION_MARKERS = ("没有", "并没有", "从未", "从没", "不是", "不会", "并不", "否认", "未曾")
HISTORICAL_MARKERS = ("以前", "曾经", "过去", "之前", "小时候", "那时候", "曾有")
HYPOTHETICAL_MARKERS = ("如果", "假如", "比如", "例如", "举例", "新闻", "故事里")
# Explicit third-party quotes only.  A parent reporting what the child or the
# other party said ("孩子说", "他说", "她说") is the main way a child's danger
# reaches this product, so reported speech is deliberately not a marker.
QUOTATION_MARKERS = ("引用", "朋友说", "别人说", "同学说")
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


def _context_markers(payload: dict) -> dict:
    rules = payload.get("context_rules")
    rules = rules if isinstance(rules, dict) else {}

    def markers(key: str, default: tuple[str, ...]) -> tuple[str, ...]:
        value = rules.get(key)
        if isinstance(value, list) and all(isinstance(item, str) for item in value):
            return tuple(item for item in value if item)
        return default

    window = rules.get("window_chars")
    return {
        "negation": markers("negation_markers", NEGATION_MARKERS),
        "historical": markers("historical_markers", HISTORICAL_MARKERS),
        "hypothetical": markers("hypothetical_markers", HYPOTHETICAL_MARKERS),
        "quotation": markers("quotation_markers", QUOTATION_MARKERS),
        "immediacy": markers("immediacy_markers", IMMEDIACY_MARKERS),
        "window": window if isinstance(window, int) and 0 < window <= 200 else DEFAULT_CONTEXT_WINDOW,
    }


def _match_context(text: str, keyword: str, start: int, end: int, markers: dict) -> dict:
    window = markers["window"]
    before = text[max(0, start - window) : start]
    after = text[end : min(len(text), end + window)]
    surrounding = before + keyword + after

    # Restrict negation detection to the left side so the "不" inside phrases
    # such as "不想活" is not mistaken for a negating modifier.
    negation = _marker_in(before[-10:], markers["negation"])
    historical = _marker_in(surrounding, markers["historical"])
    hypothetical = _marker_in(surrounding, markers["hypothetical"])
    quotation = _marker_in(surrounding, markers["quotation"])
    immediacy = _marker_in(surrounding, markers["immediacy"])

    # Negated, historical or hypothetical framing keeps a mention contextual even
    # next to immediate wording: "以前曾经有过自残的念头，现在在回顾" reviews the
    # past.  A third-party quote does not: "同学说他今晚就要自杀" still describes
    # someone in immediate danger, so immediacy outranks quotation.
    if negation or historical or hypothetical:
        status = "contextual_signal"
    elif immediacy:
        status = "immediate_signal"
    elif quotation:
        status = "contextual_signal"
    else:
        status = "direct_signal"
    return {
        "status": status,
        "negation_marker": negation,
        "historical_marker": historical,
        "hypothetical_marker": hypothetical,
        "quotation_marker": quotation,
        "immediacy_marker": immediacy,
    }


def _excluded(text: str, start: int, end: int, exclude_phrases: list[str]) -> bool:
    # Exclusions only cover fixed everyday idioms such as "想死你了"; a keyword
    # occurrence is skipped only when an excluded phrase fully contains it.
    for phrase in exclude_phrases:
        for match in re.finditer(re.escape(phrase), text):
            if match.start() <= start and end <= match.end():
                return True
    return False


def _keyword_occurrences(text: str, keyword: str, markers: dict, exclude_phrases: list[str]) -> list[dict]:
    if not keyword:
        return []
    occurrences: list[dict] = []
    for match in re.finditer(re.escape(keyword), text):
        if _excluded(text, match.start(), match.end(), exclude_phrases):
            continue
        occurrences.append(
            {
                "keyword": keyword,
                "start": match.start(),
                "context": _match_context(text, keyword, match.start(), match.end(), markers),
            }
        )
    return occurrences


def _category_match(category: dict, text: str, markers: dict) -> dict | None:
    exclude_phrases = [str(item) for item in category.get("exclude_phrases", []) if item]
    occurrences: list[dict] = []
    for keyword in category.get("keywords", []):
        occurrences.extend(_keyword_occurrences(text, str(keyword or ""), markers, exclude_phrases))
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
    markers = _context_markers(payload)
    combined_text = _combine_text(text)
    matched_categories: list[dict] = []

    if combined_text:
        for category in payload.get("categories", []):
            matched = _category_match(category, combined_text, markers)
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
        "context_engine_version": CONTEXT_ENGINE_VERSION,
        "boundary_notice": "安全信号只用于人工复核分流，不构成诊断、危机评估、风险概率或处置结论。",
    }
