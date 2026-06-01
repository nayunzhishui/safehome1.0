"""Rule-based student profile generation."""

from database import now_iso
from services.content_loader import load_student_profile_rules, load_training_cards
from services.risk_service import check_text_risk

PROFILE_MODEL_VERSION = "profile-rules-v1"
REQUIRED_SCORE_FIELDS = ["test_anxiety", "iu_score", "self_compassion"]


class ProfileInputError(ValueError):
    """Raised when profile input is missing required scores."""

    def __init__(self, missing_fields: list[str]) -> None:
        super().__init__(f"缺少画像生成所需字段：{', '.join(missing_fields)}")
        self.missing_fields = missing_fields


def _as_number(value) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _extract_scores(payload: dict) -> dict[str, float]:
    raw_scores = payload.get("scores") if isinstance(payload.get("scores"), dict) else payload
    scores = {}
    missing = []

    for field in REQUIRED_SCORE_FIELDS:
        value = _as_number(raw_scores.get(field))
        if value is None:
            missing.append(field)
        else:
            scores[field] = value

    optional_fear = _as_number(raw_scores.get("fear_score") or raw_scores.get("f_score"))
    if optional_fear is not None:
        scores["fear_score"] = optional_fear

    if missing:
        raise ProfileInputError(missing)
    return scores


def _valid_card_ids() -> set[str]:
    return {card.get("id") for card in load_training_cards().get("cards", []) if card.get("id")}


def _filter_card_ids(card_ids: list[str]) -> list[str]:
    valid_ids = _valid_card_ids()
    return [card_id for card_id in card_ids if card_id in valid_ids]


def _keyword_boost(rule: dict, free_text: str) -> float:
    keywords = rule.get("trigger", {}).get("optional_text_keywords", [])
    if not free_text or not keywords:
        return 0
    return 0.06 if any(keyword in free_text for keyword in keywords) else 0


def _pressure_alert_confidence(scores: dict[str, float], rule: dict, free_text: str) -> float:
    confidence = 0.58
    confidence += max(0, scores.get("test_anxiety", 0) - 3.5) * 0.08
    confidence += max(0, scores.get("iu_score", 0) - 3.5) * 0.08
    confidence += max(0, scores.get("fear_score", 0) - 3.0) * 0.04
    confidence += max(0, 3.5 - scores.get("self_compassion", 3.5)) * 0.04
    confidence += _keyword_boost(rule, free_text)
    return min(round(confidence, 2), 0.92)


def _dimension_summary(scores: dict[str, float], rule_dimensions: list[dict]) -> list[dict]:
    summaries = []
    for dimension in rule_dimensions:
        summaries.append(
            {
                "key": dimension.get("key"),
                "label": dimension.get("label"),
                "level": dimension.get("level"),
                "summary": dimension.get("summary"),
            }
        )
    summaries.append(
        {
            "key": "self_compassion_score",
            "label": "自我支持分数",
            "level": "developing" if scores.get("self_compassion", 0) < 3.5 else "available",
            "summary": "该维度用于观察你能否用温和、具体的话支持自己，不用于评价好坏。",
        }
    )
    return summaries


def _high_risk_profile(risk_result: dict) -> dict:
    return {
        "profile_code": "requires_review",
        "profile_name": "需要人工关注的支持提示",
        "confidence": 0,
        "dimensions": [],
        "supportive_explanation": risk_result.get("safe_response"),
        "strength_note": "你愿意表达这些感受本身很重要。接下来更适合优先联系现实中的可信成年人或专业支持资源。",
        "small_step": "请先联系现实中的可信成年人、学校老师、专业机构或当地紧急服务。",
        "recommended_card_ids": [],
        "risk_level": risk_result.get("risk_level", "high"),
        "requires_review": True,
        "allow_auto_feedback": False,
        "model_version": PROFILE_MODEL_VERSION,
        "rules_version": load_student_profile_rules().get("version"),
        "boundary_notice": "该提示不是诊断，也不是危机评估结论；它只表示当前文本需要人工关注。",
        "created_at": now_iso(),
    }


def _general_support_profile(scores: dict[str, float], risk_result: dict) -> dict:
    return {
        "profile_code": "general_support",
        "profile_name": "阶段性支持观察",
        "confidence": 0.46,
        "dimensions": [
            {
                "key": "current_pressure",
                "label": "近期压力反应",
                "level": "mixed",
                "summary": "本次填写暂未形成明确画像，更适合先观察具体场景和可用支持资源。",
            }
        ],
        "supportive_explanation": "本次填写可以作为一次自我观察记录。当前不需要急着给自己下结论，可以先从情绪命名和自我支持练习开始。",
        "strength_note": "你已经完成了一次整理，这有助于把模糊压力变得更具体。",
        "small_step": "先选择一个最近最明显的感受，完成 3 分钟情绪命名练习。",
        "recommended_card_ids": _filter_card_ids(["student_emotion_naming", "self_support_statement"]),
        "risk_level": risk_result.get("risk_level", "low"),
        "requires_review": risk_result.get("requires_review", False),
        "allow_auto_feedback": risk_result.get("allow_auto_feedback", True),
        "model_version": PROFILE_MODEL_VERSION,
        "rules_version": load_student_profile_rules().get("version"),
        "boundary_notice": "这不是诊断，也不代表固定特征；它只是基于本次填写形成的阶段性支持建议。",
        "created_at": now_iso(),
    }


def generate_student_profile(payload: dict) -> dict:
    """Generate a transparent, non-diagnostic student profile result."""

    scores = _extract_scores(payload)
    free_text = str(payload.get("free_text") or "")
    risk_result = check_text_risk(free_text, source="student_profile")
    if risk_result.get("risk_level") == "high":
        return _high_risk_profile(risk_result)

    rules_payload = load_student_profile_rules()
    for rule in rules_payload.get("rules", []):
        if not rule.get("enabled", True):
            continue
        if rule.get("profile_code") != "pressure_alert":
            continue
        if scores.get("test_anxiety", 0) >= 3.5 and scores.get("iu_score", 0) >= 3.5:
            confidence = _pressure_alert_confidence(scores, rule, free_text)
            if confidence < rule.get("trigger", {}).get("confidence_min", 0.7):
                return _general_support_profile(scores, risk_result)
            content = rule.get("content", {})
            return {
                "profile_code": rule.get("profile_code"),
                "profile_name": rule.get("profile_name"),
                "confidence": confidence,
                "dimensions": _dimension_summary(scores, rule.get("dimensions", [])),
                "supportive_explanation": content.get("explanation"),
                "strength_note": content.get("strength_note"),
                "small_step": content.get("small_step"),
                "recommended_card_ids": _filter_card_ids(rule.get("recommended_card_ids", [])),
                "risk_level": risk_result.get("risk_level", rule.get("risk_level", "low")),
                "requires_review": risk_result.get("requires_review", rule.get("requires_review", False)),
                "allow_auto_feedback": risk_result.get("allow_auto_feedback", True),
                "model_version": PROFILE_MODEL_VERSION,
                "rules_version": rules_payload.get("version"),
                "boundary_notice": content.get("boundary_notice"),
                "created_at": now_iso(),
            }

    return _general_support_profile(scores, risk_result)

