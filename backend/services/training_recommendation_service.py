"""Evaluate assessment-to-training-card recommendation rules."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from config import Config
from database import json_loads, load_content_json


def evaluate_training_rules(
    worksheet_id: str,
    scores_json: str | dict,
    worksheet: dict | None = None,
    risk_result: dict | None = None,
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
    return matched


def flatten_card_ids(rules: list[dict]) -> list[str]:
    ids: list[str] = []
    for rule in rules:
        for card_id in rule.get("recommended_card_ids", []):
            if card_id and card_id not in ids:
                ids.append(card_id)
    return ids


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
