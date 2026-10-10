"""Item-level safety triggers declared on assessment questions.

Some validated questionnaires contain single items whose answer alone needs a
safety route (for example a question about thoughts of self-harm).  The total
score cannot carry that signal, so a question may declare `safety_trigger`:

    {"min_score": 1, "risk_level": "high", "safety_route": "human_review",
     "urgent_min_score": 2, "reason_code": "...", "participant_message": "..."}

The result has the same shape as `risk_service.check_text_risk` so existing
review records, card suppression and result-page notices keep working.  It is a
routing signal for human attention, not a diagnosis or risk prediction.
"""

from __future__ import annotations

RISK_ORDER = {"low": 0, "medium": 1, "high": 2}
ROUTE_ORDER = {"standard": 0, "human_review": 1, "urgent_human_review": 2}
DEFAULT_ITEM_MESSAGE = "本次填写中有一道题需要优先关注。请联系身边可信的人或专业机构；需要时可在“紧急求助”页面找到热线。"
BOUNDARY_NOTICE = "题目级安全提示只用于人工复核分流，不构成诊断、危机评估或风险概率。"


def _numeric(value) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value)


def evaluate_item_safety(worksheet: dict, answers: list[dict]) -> dict | None:
    """Return a risk result for answers that reach a question's declared trigger."""

    questions = {
        question.get("id"): question
        for question in worksheet.get("questions", [])
        if isinstance(question, dict) and question.get("id")
    }
    hits = []
    for answer in answers:
        question = questions.get(answer.get("question_id"))
        trigger = (question or {}).get("safety_trigger")
        score = _numeric(answer.get("score"))
        minimum = _numeric((trigger or {}).get("min_score")) if isinstance(trigger, dict) else None
        if score is None or minimum is None or score < minimum:
            continue
        risk_level = trigger.get("risk_level") if trigger.get("risk_level") in RISK_ORDER else "high"
        route = trigger.get("safety_route") if trigger.get("safety_route") in ROUTE_ORDER else "human_review"
        urgent_minimum = _numeric(trigger.get("urgent_min_score"))
        if urgent_minimum is not None and score >= urgent_minimum:
            route = "urgent_human_review"
        hits.append(
            {
                "question_id": question["id"],
                "risk_level": risk_level,
                "safety_route": route,
                "reason_code": str(trigger.get("reason_code") or "assessment_item_safety_trigger"),
                "participant_message": str(trigger.get("participant_message") or ""),
            }
        )
    if not hits:
        return None

    top = max(hits, key=lambda hit: (RISK_ORDER[hit["risk_level"]], ROUTE_ORDER[hit["safety_route"]]))
    route = max((hit["safety_route"] for hit in hits), key=ROUTE_ORDER.__getitem__)
    blocks_ordinary = top["risk_level"] == "high" or route == "urgent_human_review"
    message = top["participant_message"] or DEFAULT_ITEM_MESSAGE
    return {
        "source": "assessment_item",
        "risk_level": top["risk_level"],
        "safety_route": route,
        # Only item identifiers and reason codes are kept; answer text is never copied here.
        "matched_categories": [
            {
                "id": f"assessment_item:{hit['question_id']}",
                "label": "题目级安全提示",
                "reason_code": hit["reason_code"],
                "risk_level": hit["risk_level"],
            }
            for hit in hits
        ],
        "requires_review": True,
        "allow_auto_feedback": not blocks_ordinary,
        "allow_recommended_training_cards": not blocks_ordinary,
        "export_raw_text_by_default": False,
        "safe_response": message,
        "participant_message": message,
        "boundary_notice": BOUNDARY_NOTICE,
    }


def merge_risk_results(text_risk: dict | None, item_risk: dict | None) -> dict | None:
    """Combine text and item routes, keeping the most protective setting of each field."""

    if not text_risk:
        return item_risk
    if not item_risk:
        return text_risk
    primary, secondary = (
        (item_risk, text_risk)
        if RISK_ORDER.get(item_risk.get("risk_level"), 0) >= RISK_ORDER.get(text_risk.get("risk_level"), 0)
        else (text_risk, item_risk)
    )
    merged = dict(primary)
    merged["risk_level"] = primary.get("risk_level")
    merged["safety_route"] = max(
        (str(item.get("safety_route") or "standard") for item in (text_risk, item_risk)),
        key=lambda route: ROUTE_ORDER.get(route, 0),
    )
    merged["matched_categories"] = list(text_risk.get("matched_categories") or []) + list(
        item_risk.get("matched_categories") or []
    )
    merged["requires_review"] = bool(text_risk.get("requires_review") or item_risk.get("requires_review"))
    for field in ("allow_auto_feedback", "allow_recommended_training_cards"):
        merged[field] = bool(text_risk.get(field, True) and item_risk.get(field, True))
    if merged["safety_route"] == "urgent_human_review":
        merged["allow_auto_feedback"] = False
        merged["allow_recommended_training_cards"] = False
    merged["participant_message"] = item_risk.get("participant_message") or ""
    merged["safe_response"] = primary.get("safe_response") or secondary.get("safe_response")
    merged["source"] = "assessment"
    return merged
