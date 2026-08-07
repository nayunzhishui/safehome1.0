"""Conservative safety routing for profile and free-text flows.

The engine is intentionally transparent and rule based. It routes text to
human review; it does not estimate suicide probability, diagnose a condition,
or use global risk labels to make treatment/discharge decisions.
"""

from services.content_loader import load_risk_keywords

ENGINE_VERSION = "safehome-safety-routing-v2"
RISK_ORDER = {"low": 0, "medium": 1, "high": 2}

DEFAULT_LOW_RISK_RESPONSE = "当前文本未命中需要人工安全复核的规则。该结果只用于分流，不代表安全评估结论。"

IMMEDIACY_TERMS = (
    "现在",
    "马上",
    "立刻",
    "此刻",
    "今晚",
    "今天就",
    "控制不住",
    "已经准备",
)
PLAN_OR_METHOD_TERMS = (
    "计划",
    "具体方法",
    "怎么死",
    "割腕",
    "跳楼",
    "上吊",
    "服药",
    "吞药",
    "刀",
    "绳",
    "高楼",
)
ACCESS_TERMS = (
    "手边有",
    "已经拿到",
    "就在身边",
    "准备好了",
    "有刀",
    "有药",
)
HISTORICAL_OR_NEGATION_TERMS = (
    "以前",
    "曾经",
    "过去",
    "没有",
    "没想",
    "不再",
    "从未",
    "否认",
)
PROTECTIVE_TERMS = (
    "有人陪",
    "家人在",
    "老师在",
    "已经联系",
    "愿意求助",
    "现在安全",
)


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


def _matched_terms(text: str, terms: tuple[str, ...]) -> list[str]:
    return [term for term in terms if term and term in text]


def _context_flags(text: str) -> dict:
    """Capture context without downgrading a positive safety trigger.

    Negation/history signals are intentionally informational only. A simple
    rules engine cannot safely infer that a phrase such as "以前不想活，现在..."
    removes present concern, so human review remains conservative.
    """

    immediacy = _matched_terms(text, IMMEDIACY_TERMS)
    plan_or_method = _matched_terms(text, PLAN_OR_METHOD_TERMS)
    access = _matched_terms(text, ACCESS_TERMS)
    historical_or_negation = _matched_terms(text, HISTORICAL_OR_NEGATION_TERMS)
    protective = _matched_terms(text, PROTECTIVE_TERMS)
    return {
        "immediacy": immediacy,
        "plan_or_method": plan_or_method,
        "access": access,
        "historical_or_negation": historical_or_negation,
        "protective": protective,
        "urgent_context": bool(immediacy or plan_or_method or access),
    }


def _safety_route(risk_level: str, flags: dict) -> tuple[str, str]:
    if risk_level == "high" and flags.get("urgent_context"):
        return "urgent_human_review", "urgent"
    if risk_level == "high":
        return "human_review", "high"
    if risk_level == "medium":
        return "human_support_review", "normal"
    return "standard", "normal"


def check_text_risk(text: str | list[str] | None, source: str = "student_profile") -> dict:
    """Route text using explicit safety rules.

    ``risk_level`` is retained only for backwards compatibility with existing
    SafeHome clients. New code should use ``safety_route`` and
    ``review_priority``. The engine never returns a clinical risk assessment.
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
    flags = _context_flags(combined_text)
    safety_route, review_priority = _safety_route(risk_level, flags)

    safe_response = DEFAULT_LOW_RISK_RESPONSE
    if matched_categories:
        safe_response = next(
            (
                item.get("safe_response")
                for item in matched_categories
                if item.get("risk_level") == risk_level and item.get("safe_response")
            ),
            matched_categories[0].get("safe_response") or DEFAULT_LOW_RISK_RESPONSE,
        )

    return {
        "source": source,
        "engine_version": ENGINE_VERSION,
        # Compatibility field. Do not present this as a clinical stratification.
        "risk_level": risk_level,
        "safety_route": safety_route,
        "review_priority": review_priority,
        "context_flags": flags,
        "matched_categories": matched_categories,
        "requires_review": bool(handling.get("requires_review", False)),
        "allow_auto_feedback": bool(handling.get("allow_auto_feedback", risk_level != "high")),
        "allow_recommended_training_cards": bool(
            handling.get("allow_recommended_training_cards", risk_level != "high")
        ),
        "export_raw_text_by_default": bool(handling.get("export_raw_text_by_default", False)),
        "safe_response": safe_response,
        "boundary_notice": (
            "安全规则只用于保守分流和人工复核，不构成诊断、危机评估、"
            "自杀概率预测或治疗/处置依据。否定、历史和保护性表达不会由规则引擎自动降级。"
        ),
    }
