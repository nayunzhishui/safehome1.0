"""Evaluate assessment-to-training-card recommendation rules."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from config import Config
from database import get_connection, json_loads, load_content_json


EVALUATIONS_FOR_RECOMMENDATION = {"matches", "partly_matches", "does_not_match", "uncomfortable"}


def evaluate_training_rules(
    worksheet_id: str,
    scores_json: str | dict,
    worksheet: dict | None = None,
    risk_result: dict | None = None,
    user_id: str | None = None,
) -> list[dict]:
    """Return assessment training rules whose dimension conditions match scores."""

    if risk_result and risk_result.get("risk_level") == "high":
        return []
    if isinstance(scores_json, str):
        scores = json_loads(scores_json, {}) or {}
    else:
        scores = scores_json or {}
    if (scores.get("risk") or {}).get("risk_level") == "high":
        return []

    dim_map = {
        str(item.get("key")): item.get("score")
        for item in scores.get("dimensions", [])
        if isinstance(item, dict) and item.get("key") and isinstance(item.get("score"), (int, float))
    }
    model = _find_profile_model(worksheet_id, worksheet)
    matched = []
    for rule in _load_rules():
        condition = rule.get("trigger_condition") or {}
        if not _matches_worksheet(condition, worksheet_id):
            continue
        if _evaluate_condition(condition, dim_map, model, worksheet, worksheet_id):
            matched.append(rule)
    if user_id:
        matched = _apply_user_feedback(matched, user_id)
    return matched


def flatten_card_ids(rules: list[dict]) -> list[str]:
    try:
        cards = {
            card.get("id"): card
            for card in load_content_json("training_cards.json").get("cards", [])
            if isinstance(card, dict) and card.get("id")
        }
    except FileNotFoundError:
        cards = {}
    ids: list[str] = []
    for rule in rules:
        for card_id in rule.get("recommended_card_ids", []):
            card = cards.get(card_id, {})
            is_allowed = card.get("release_policy", "shared_choice_candidate") == "shared_choice_candidate"
            if card_id and is_allowed and card_id not in ids:
                ids.append(card_id)
    return ids


def _apply_user_feedback(rules: list[dict], user_id: str) -> list[dict]:
    feedback = _load_card_feedback(user_id)
    if not feedback:
        return rules
    adjusted = []
    for rule_index, rule in enumerate(rules):
        cloned = dict(rule)
        card_ids = list(cloned.get("recommended_card_ids") or [])
        scored_cards = []
        for index, card_id in enumerate(card_ids):
            score = 100 - rule_index * 5 - index
            stats = feedback.get(card_id, {})
            score += int(stats.get("helpful", 0)) * 8
            score += int(stats.get("neutral", 0)) * 1
            score -= int(stats.get("not_helpful_yet", 0)) * 10
            score -= int(stats.get("skipped", 0)) * 6
            score += int(stats.get("matches", 0)) * 8
            score += int(stats.get("partly_matches", 0))
            score -= int(stats.get("does_not_match", 0)) * 20
            score -= int(stats.get("uncomfortable", 0)) * 100
            score += min(int(stats.get("completed", 0)), 5)
            scored_cards.append((score, card_id, stats))
        scored_cards.sort(key=lambda item: item[0], reverse=True)
        cloned["recommended_card_ids"] = [card_id for _score, card_id, _stats in scored_cards]
        cloned["recommendation_reason"] = _feedback_reason(scored_cards)
        adjusted.append((sum(score for score, _card_id, _stats in scored_cards), cloned))
    adjusted.sort(key=lambda item: item[0], reverse=True)
    return [rule for _score, rule in adjusted]


def _feedback_reason(scored_cards: list[tuple[float, str, dict]]) -> str:
    helpful = [card_id for _score, card_id, stats in scored_cards if int(stats.get("helpful", 0)) > 0]
    not_helpful = [
        card_id
        for _score, card_id, stats in scored_cards
        if int(stats.get("not_helpful_yet", 0)) > 0
        or int(stats.get("skipped", 0)) > 0
        or int(stats.get("does_not_match", 0)) > 0
        or int(stats.get("uncomfortable", 0)) > 0
    ]
    if helpful:
        return "已结合你之前标记为有帮助的训练卡，优先保留更容易执行的小练习。"
    if not_helpful:
        return "已结合你之前暂时没有帮助或跳过的训练反馈，降低相似训练卡的优先级。"
    return "已结合近期训练完成情况做轻量排序。"


def _load_card_feedback(user_id: str) -> dict[str, dict[str, int]]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT card_id, completed, helpfulness_rating, skip_reason
            FROM checkins
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT 50
            """,
            (user_id,),
        ).fetchall()
        ledger_rows = conn.execute(
            """
            SELECT source_id AS card_id, evaluation
            FROM feedback_ledger
            WHERE user_id = ? AND source_type = 'training_recommendation' AND status = 'active'
            ORDER BY created_at DESC
            LIMIT 50
            """,
            (user_id,),
        ).fetchall()
    feedback: dict[str, dict[str, int]] = {}
    for row in rows:
        card_id = row["card_id"]
        if not card_id:
            continue
        stats = feedback.setdefault(card_id, {"completed": 0, "helpful": 0, "neutral": 0, "not_helpful_yet": 0, "skipped": 0, "matches": 0, "partly_matches": 0, "does_not_match": 0, "uncomfortable": 0})
        if row["completed"]:
            stats["completed"] += 1
        helpfulness = row["helpfulness_rating"]
        if helpfulness in stats:
            stats[helpfulness] += 1
        if row["skip_reason"]:
            stats["skipped"] += 1
    for row in ledger_rows:
        card_id = row["card_id"]
        evaluation = row["evaluation"]
        if not card_id or evaluation not in EVALUATIONS_FOR_RECOMMENDATION:
            continue
        stats = feedback.setdefault(card_id, {"completed": 0, "helpful": 0, "neutral": 0, "not_helpful_yet": 0, "skipped": 0, "matches": 0, "partly_matches": 0, "does_not_match": 0, "uncomfortable": 0})
        stats[evaluation] += 1
    return feedback


def _load_rules() -> list[dict]:
    try:
        payload = load_content_json("assessment_training_map.json")
    except FileNotFoundError:
        return []
    return [rule for rule in payload.get("rules", []) if isinstance(rule, dict)]


def _matches_worksheet(condition: dict, worksheet_id: str) -> bool:
    return condition.get("worksheet_id") == worksheet_id or condition.get("scale_id") == worksheet_id


def _evaluate_condition(
    condition: dict,
    dim_map: dict[str, float],
    model: dict | None,
    worksheet: dict | None,
    worksheet_id: str,
) -> bool:
    dimension = condition.get("dimension")
    level = condition.get("level")
    if not dimension:
        return True
    score = dim_map.get(str(dimension))
    if score is None:
        return False
    threshold = _get_threshold(str(dimension), model, worksheet, worksheet_id)
    if not threshold:
        return False
    return _check_level(str(level or ""), float(score), threshold)


def _check_level(level: str, score: float, threshold: dict[str, float]) -> bool:
    support_below = threshold["support_below"]
    high_above = threshold["high_above"]
    if level == "needs_support":
        return score < support_below
    if level == "high":
        return score > high_above
    if level == "low":
        return score < support_below
    if level == "high_or_needs_support":
        return score < support_below or score > high_above
    return True


def _get_threshold(dimension: str, model: dict | None, worksheet: dict | None, worksheet_id: str) -> dict[str, float] | None:
    model_threshold = _threshold_from_model(dimension, model)
    if model_threshold:
        return model_threshold
    return _threshold_from_worksheet(dimension, worksheet, worksheet_id)


def _threshold_from_model(dimension: str, model: dict | None) -> dict[str, float] | None:
    if not model:
        return None
    for feature in model.get("features", []):
        if not isinstance(feature, dict):
            continue
        feature_id = str(feature.get("feature_id") or "")
        label = str(feature.get("label") or "")
        if dimension not in {feature_id, label}:
            continue
        mean = feature.get("mean")
        std = feature.get("std") or 1
        if isinstance(mean, (int, float)):
            return {"support_below": float(mean) - 0.5 * float(std), "high_above": float(mean) + 0.5 * float(std)}
    return None


def _threshold_from_worksheet(dimension: str, worksheet: dict | None, worksheet_id: str) -> dict[str, float] | None:
    if not worksheet:
        worksheet = _find_worksheet_in_content(worksheet_id=worksheet_id)
    if not worksheet:
        return {"support_below": 3.5, "high_above": 4.5}
    scores: list[float] = []
    for question in worksheet.get("questions", []):
        if not isinstance(question, dict) or question.get("dimension") != dimension:
            continue
        option_scores = [option.get("score") for option in question.get("options", []) if isinstance(option.get("score"), (int, float))]
        if option_scores:
            scores.extend([min(option_scores), max(option_scores)])
    if not scores:
        return {"support_below": 3.5, "high_above": 4.5}
    low = min(scores)
    high = max(scores)
    midpoint = (float(low) + float(high)) / 2
    return {"support_below": midpoint, "high_above": midpoint}


def _find_worksheet_in_content(worksheet_id: str) -> dict | None:
    try:
        worksheets = load_content_json("assessment_worksheets.json").get("worksheets", [])
    except FileNotFoundError:
        return None
    for worksheet in worksheets:
        if not worksheet_id or worksheet.get("id") == worksheet_id:
            return worksheet
    return None


def _find_profile_model(worksheet_id: str, worksheet: dict | None = None) -> dict | None:
    model_id = (worksheet or {}).get("profile_model_id")
    directory = Config.CONTENT_DIR / "profiles"
    if not directory.exists():
        return None
    candidates: list[dict[str, Any]] = []
    for path in sorted(Path(directory).glob("*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if model_id and model_id in {payload.get("model_id"), payload.get("group_id")}:
            return payload
        if payload.get("worksheet_id") == worksheet_id:
            candidates.append(payload)
    if not candidates:
        return None
    return sorted(candidates, key=lambda item: int(item.get("n_cases") or 0), reverse=True)[0]
