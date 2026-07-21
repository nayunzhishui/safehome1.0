"""Evaluate assessment-to-training-card recommendation rules."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from config import Config
from database import get_connection, json_dumps, json_loads, load_content_json, new_id, now_iso, row_to_dict, write_audit_log


EVALUATIONS_FOR_RECOMMENDATION = {"matches", "partly_matches", "does_not_match", "uncomfortable"}
LEGACY_STRATEGY_VERSION = "legacy_rule_order_v1"
ADAPTIVE_STRATEGY_VERSION = "feedback_adaptive_v2"
RECOMMENDATION_STRATEGIES = {LEGACY_STRATEGY_VERSION, ADAPTIVE_STRATEGY_VERSION}


def evaluate_training_rules(
    worksheet_id: str,
    scores_json: str | dict,
    worksheet: dict | None = None,
    risk_result: dict | None = None,
    user_id: str | None = None,
    strategy_version: str | None = None,
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
    if not user_id:
        return [_with_strategy_metadata(rule, LEGACY_STRATEGY_VERSION, cold_start=True) for rule in matched]
    selected_strategy = strategy_version or (ADAPTIVE_STRATEGY_VERSION if _adaptive_strategy_enabled() else LEGACY_STRATEGY_VERSION)
    if selected_strategy not in RECOMMENDATION_STRATEGIES:
        selected_strategy = LEGACY_STRATEGY_VERSION
    if selected_strategy == LEGACY_STRATEGY_VERSION:
        return [_with_strategy_metadata(rule, LEGACY_STRATEGY_VERSION) for rule in matched]
    return _apply_user_feedback(matched, user_id)


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
        return [_with_strategy_metadata(rule, ADAPTIVE_STRATEGY_VERSION, cold_start=True) for rule in rules]
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
        ranked_ids = [card_id for _score, card_id, _stats in scored_cards]
        cloned["recommended_card_ids"] = ranked_ids
        cloned["recommendation_reason"] = _feedback_reason(scored_cards)
        cloned["recommendation_strategy"] = ADAPTIVE_STRATEGY_VERSION
        cloned["fallback_strategy_version"] = LEGACY_STRATEGY_VERSION
        cloned["cold_start"] = False
        cloned["replacement_card_ids"] = [card_id for index, card_id in enumerate(ranked_ids) if index < len(card_ids) and card_id != card_ids[index]]
        cloned["ranking_explanation"] = [
            {
                "card_id": card_id,
                "rank": index + 1,
                "feedback_applied": any(int(value or 0) for value in stats.values()),
                "participant_controlled": True,
            }
            for index, (_score, card_id, stats) in enumerate(scored_cards)
        ]
        adjusted.append((sum(score for score, _card_id, _stats in scored_cards), cloned))
    adjusted.sort(key=lambda item: item[0], reverse=True)
    return [rule for _score, rule in adjusted]


def _with_strategy_metadata(rule: dict, strategy_version: str, *, cold_start: bool = False) -> dict:
    cloned = dict(rule)
    card_ids = list(cloned.get("recommended_card_ids") or [])
    cloned["recommendation_strategy"] = strategy_version
    cloned["fallback_strategy_version"] = LEGACY_STRATEGY_VERSION
    cloned["cold_start"] = cold_start
    cloned["replacement_card_ids"] = []
    cloned["ranking_explanation"] = [
        {"card_id": card_id, "rank": index + 1, "feedback_applied": False, "participant_controlled": True}
        for index, card_id in enumerate(card_ids)
    ]
    if cold_start:
        cloned["recommendation_reason"] = "当前还没有可用于排序的练习反馈，先按支持性测评规则展示候选训练卡。"
    else:
        cloned.setdefault("recommendation_reason", "当前沿用已验证的规则顺序，未使用参与者反馈调整排序。")
    return cloned


def _adaptive_strategy_enabled() -> bool:
    try:
        from services.reliability_service import list_feature_flags

        flag = next(
            (item for item in list_feature_flags() if item.get("flag_name") == "training_feedback_adaptive_ranking"),
            None,
        )
        return bool(flag and flag.get("enabled") and int(flag.get("rollout_percent") or 0) > 0)
    except Exception:
        return False


def create_recommendation_snapshot(
    user_id: str,
    *,
    source_result_id: str,
    strategy_version: str,
    rules: list[dict],
    idempotency_key: str,
) -> tuple[dict, int]:
    if strategy_version not in RECOMMENDATION_STRATEGIES:
        raise ValueError("invalid_recommendation_strategy")
    idempotency_key = str(idempotency_key or "").strip()
    if not idempotency_key or len(idempotency_key) > 120:
        raise ValueError("invalid_idempotency_key")
    card_ids = flatten_card_ids(rules)
    reasons = [
        {
            "recommendation_reason": rule.get("recommendation_reason"),
            "ranking_explanation": rule.get("ranking_explanation") or [],
            "replacement_card_ids": rule.get("replacement_card_ids") or [],
        }
        for rule in rules
    ]
    with get_connection() as conn:
        existing = conn.execute(
            "SELECT * FROM recommendation_snapshots WHERE user_id = ? AND idempotency_key = ?",
            (user_id, idempotency_key),
        ).fetchone()
        if existing:
            item = row_to_dict(existing)
            if item.get("source_result_id") != source_result_id or item.get("strategy_version") != strategy_version:
                raise ValueError("idempotency_conflict")
            return _public_snapshot(item, already_recorded=True), 200
        snapshot_id = new_id("recommendation-snapshot")
        timestamp = now_iso()
        previous_strategy = LEGACY_STRATEGY_VERSION if strategy_version == ADAPTIVE_STRATEGY_VERSION else None
        conn.execute(
            """
            INSERT INTO recommendation_snapshots (
                id, user_id, source_result_id, strategy_version, previous_strategy_version,
                recommended_card_ids_json, reasons_json, status, idempotency_key, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, 'active', ?, ?)
            """,
            (
                snapshot_id,
                user_id,
                source_result_id,
                strategy_version,
                previous_strategy,
                json_dumps(card_ids),
                json_dumps(reasons),
                idempotency_key,
                timestamp,
            ),
        )
        write_audit_log(
            conn,
            "recommendation_strategy_replayed",
            user_id,
            "recommendation_snapshot",
            snapshot_id,
            {"strategy_version": strategy_version, "source_result_id": source_result_id, "card_count": len(card_ids)},
        )
        conn.commit()
        item = row_to_dict(conn.execute("SELECT * FROM recommendation_snapshots WHERE id = ?", (snapshot_id,)).fetchone())
    return _public_snapshot(item), 201


def get_recommendation_snapshot(user_id: str, snapshot_id: str) -> dict | None:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM recommendation_snapshots WHERE id = ? AND user_id = ?",
            (snapshot_id, user_id),
        ).fetchone()
    return _public_snapshot(row_to_dict(row)) if row else None


def _public_snapshot(item: dict, *, already_recorded: bool = False) -> dict:
    result = {
        "id": item.get("id"),
        "user_id": item.get("user_id"),
        "source_result_id": item.get("source_result_id"),
        "strategy_version": item.get("strategy_version"),
        "previous_strategy_version": item.get("previous_strategy_version"),
        "recommended_card_ids": json_loads(item.get("recommended_card_ids_json"), []),
        "reasons": json_loads(item.get("reasons_json"), []),
        "status": item.get("status"),
        "created_at": item.get("created_at"),
        "rollback_available": item.get("strategy_version") != LEGACY_STRATEGY_VERSION,
        "boundary_notice": "推荐回放只解释候选训练卡排序，不用于诊断、疗效判断或自动替代人工共同决定。",
    }
    if already_recorded:
        result["already_recorded"] = True
    return result


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
