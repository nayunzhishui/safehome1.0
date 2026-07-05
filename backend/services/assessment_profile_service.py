"""Assessment result to aggregate profile-position matching."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

from config import Config
from database import json_loads

LOW_CONFIDENCE_THRESHOLD = 0.15
OUTLIER_DISTANCE_FACTOR = 1.75


class ProfilePositionUnavailable(ValueError):
    """Raised when a saved assessment result cannot be matched to a profile model."""

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


def _profile_dir() -> Path:
    return Config.CONTENT_DIR / "profiles"


def _load_models() -> list[dict[str, Any]]:
    directory = _profile_dir()
    if not directory.exists():
        return []
    models: list[dict[str, Any]] = []
    for path in sorted(directory.glob("*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if payload.get("schema_version") == "2026.06-profile-model-v1":
            models.append(payload)
    return models


def _is_connectable_model(model: dict[str, Any]) -> bool:
    return model.get("worksheet_link_status") != "manual_review_required"


def _choose_model(worksheet: dict[str, Any], requested_model_id: str | None = None) -> dict[str, Any] | None:
    models = [model for model in _load_models() if _is_connectable_model(model)]
    worksheet_id = worksheet.get("id")
    if requested_model_id:
        for model in models:
            if requested_model_id in {model.get("model_id"), model.get("group_id")}:
                if model.get("worksheet_id") == worksheet_id or model.get("scale_id") == worksheet_id:
                    return model
                return None
        return None

    worksheet_model_id = worksheet.get("profile_model_id")
    if worksheet_model_id:
        for model in models:
            if worksheet_model_id in {model.get("model_id"), model.get("group_id")}:
                return model

    candidates = [model for model in models if model.get("worksheet_id") == worksheet_id or model.get("scale_id") == worksheet_id]
    if not candidates:
        return None
    return sorted(candidates, key=lambda model: (int(model.get("n_cases") or 0), model.get("model_id") or ""), reverse=True)[0]


def _answers_by_question(result: dict[str, Any]) -> dict[str, dict[str, Any]]:
    answers = result.get("answers")
    if answers is None:
        answers = json_loads(result.get("answers_json"), [])
    if not isinstance(answers, list):
        return {}
    return {str(answer.get("question_id")): answer for answer in answers if isinstance(answer, dict) and answer.get("question_id")}


def _question_map(worksheet: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(question.get("id")): question
        for question in worksheet.get("questions", [])
        if isinstance(question, dict) and question.get("id")
    }


def _score_bounds(question: dict[str, Any] | None, feature: dict[str, Any]) -> tuple[float, float] | None:
    min_value = feature.get("score_min")
    max_value = feature.get("score_max")
    if isinstance(min_value, (int, float)) and isinstance(max_value, (int, float)):
        return float(min_value), float(max_value)
    if not question:
        return None
    scores = [option.get("score") for option in question.get("options", []) if isinstance(option.get("score"), (int, float))]
    if not scores:
        return None
    return float(min(scores)), float(max(scores))


def _answer_score(answer: dict[str, Any] | None, question: dict[str, Any] | None) -> float | None:
    if not answer:
        return None
    score = answer.get("score")
    if isinstance(score, (int, float)):
        return float(score)
    value = answer.get("value")
    if question:
        for option in question.get("options", []):
            if str(option.get("value")) == str(value) and isinstance(option.get("score"), (int, float)):
                return float(option["score"])
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _feature_value(
    feature: dict[str, Any],
    answers: dict[str, dict[str, Any]],
    questions: dict[str, dict[str, Any]],
) -> tuple[float | None, bool]:
    question_id = feature.get("worksheet_question_id") or feature.get("feature_id")
    answer = answers.get(str(question_id))
    question = questions.get(str(question_id))
    value = _answer_score(answer, question)
    if value is None:
        return None, True
    if feature.get("reverse_scored"):
        bounds = _score_bounds(question, feature)
        if bounds:
            low, high = bounds
            value = low + high - value
    return value, False


def _pca_position(model: dict[str, Any], z_values: list[float]) -> dict[str, float | None]:
    components = model.get("pca", {}).get("components") or []
    if len(components) < 2:
        return {"pc1": None, "pc2": None}

    coords = []
    for component in components[:2]:
        if len(component) != len(z_values):
            coords.append(None)
        else:
            coords.append(round(float(sum(float(weight) * value for weight, value in zip(component, z_values))), 4))
    return {"pc1": coords[0], "pc2": coords[1]}


def _distance_to_center(cluster: dict[str, Any], feature_ids: list[str], z_lookup: dict[str, float]) -> float:
    center = cluster.get("center_z") or {}
    total = 0.0
    count = 0
    for feature_id in feature_ids:
        if feature_id not in center:
            continue
        diff = z_lookup[feature_id] - float(center[feature_id])
        total += diff * diff
        count += 1
    if count == 0:
        return math.inf
    return math.sqrt(total)


def _confidence(nearest: float, second: float | None) -> float:
    if second is None or not math.isfinite(second):
        return 1.0
    denominator = nearest + second
    if denominator <= 0:
        return 1.0
    return round(max(0.0, min(1.0, (second - nearest) / denominator)), 3)


def _interpretation_guard(nearest: float, confidence: float, feature_count: int) -> dict[str, Any]:
    distance_threshold = math.sqrt(max(feature_count, 1)) * OUTLIER_DISTANCE_FACTOR
    if nearest > distance_threshold:
        return {
            "status": "outlier",
            "can_use_interpretation": False,
            "message": "本次填写结果距离既往样本的主要画像中心较远，因此不做明确画像解释，只保留位置参考。",
            "distance_threshold": round(float(distance_threshold), 4),
        }
    if confidence < LOW_CONFIDENCE_THRESHOLD:
        return {
            "status": "low_confidence",
            "can_use_interpretation": False,
            "message": "本次填写结果和多个画像中心的距离接近，因此不做明确画像判断，只作为阶段性观察线索。",
            "distance_threshold": round(float(distance_threshold), 4),
        }
    return {
        "status": "usable",
        "can_use_interpretation": True,
        "message": "本次画像匹配达到最低解释条件。",
        "distance_threshold": round(float(distance_threshold), 4),
    }


def build_assessment_profile_position(
    result: dict[str, Any],
    worksheet: dict[str, Any],
    requested_model_id: str | None = None,
) -> dict[str, Any]:
    """Match one saved assessment result to the closest aggregate profile cluster."""

    model = _choose_model(worksheet, requested_model_id)
    if not model:
        raise ProfilePositionUnavailable("这份测评暂未接入可用的既往数据聚类画像模型。")

    features = [feature for feature in model.get("features", []) if isinstance(feature, dict)]
    if not features:
        raise ProfilePositionUnavailable("画像模型缺少可用于匹配的特征。")

    answers = _answers_by_question(result)
    questions = _question_map(worksheet)
    z_lookup: dict[str, float] = {}
    raw_scores: dict[str, float | None] = {}
    missing_features: list[str] = []

    for feature in features:
        feature_id = str(feature.get("feature_id"))
        value, missing = _feature_value(feature, answers, questions)
        if missing:
            missing_features.append(feature_id)
            value = float(feature.get("mean") or 0)
        raw_scores[feature_id] = value
        mean = float(feature.get("mean") or 0)
        std = float(feature.get("std") or 1) or 1
        z_lookup[feature_id] = (float(value) - mean) / std

    answered_count = len(features) - len(missing_features)
    if answered_count < max(2, math.ceil(len(features) * 0.6)):
        raise ProfilePositionUnavailable("本次填写可用于画像匹配的题项不足。")

    feature_ids = [str(feature.get("feature_id")) for feature in features]
    z_values = [z_lookup[feature_id] for feature_id in feature_ids]
    cluster_distances = [
        (_distance_to_center(cluster, feature_ids, z_lookup), cluster)
        for cluster in model.get("clusters", [])
        if isinstance(cluster, dict)
    ]
    cluster_distances = sorted(cluster_distances, key=lambda item: item[0])
    if not cluster_distances:
        raise ProfilePositionUnavailable("画像模型缺少可比较的聚类中心。")

    nearest_distance, nearest_cluster = cluster_distances[0]
    second_distance = cluster_distances[1][0] if len(cluster_distances) > 1 else None
    pca = _pca_position(model, z_values)
    confidence = _confidence(nearest_distance, second_distance)
    interpretation_guard = _interpretation_guard(nearest_distance, confidence, len(features))
    profile_name = nearest_cluster.get("profile_name") or f"画像{nearest_cluster.get('cluster_id', '')}"
    if interpretation_guard["can_use_interpretation"]:
        explanation = (
            f"您当前的填写结果在本研究组中更接近「{profile_name}」。"
            "这个位置表示与既往样本题项组合的相对接近程度，只用于支持性理解和后续练习参考，不代表诊断或固定标签。"
        )
    else:
        explanation = interpretation_guard["message"]

    return {
        "available": True,
        "model_id": model.get("model_id"),
        "group_id": model.get("group_id"),
        "standard_scale_name": model.get("standard_scale_name"),
        "scale_id": model.get("scale_id"),
        "worksheet_id": worksheet.get("id"),
        "research_dir": model.get("research_dir"),
        "source_dataset": model.get("source_dataset"),
        "n_cases": model.get("n_cases"),
        "n_features": model.get("n_features"),
        "chosen_k": model.get("chosen_k"),
        "position": {
            "pc1": pca["pc1"],
            "pc2": pca["pc2"],
            "cluster_id": nearest_cluster.get("cluster_id"),
            "profile_id": nearest_cluster.get("profile_id"),
            "profile_name": profile_name,
            "display_name": nearest_cluster.get("display_name"),
            "nearest_distance": round(float(nearest_distance), 4),
            "second_distance": round(float(second_distance), 4) if second_distance is not None else None,
            "confidence": confidence,
            "interpretation_status": interpretation_guard["status"],
            "can_use_interpretation": interpretation_guard["can_use_interpretation"],
        },
        "interpretation": interpretation_guard,
        "clusters": [
            {
                "cluster_id": cluster.get("cluster_id"),
                "profile_id": cluster.get("profile_id"),
                "profile_name": cluster.get("profile_name"),
                "display_name": cluster.get("display_name"),
                "n": cluster.get("n"),
                "percent": cluster.get("percent"),
                "pca_centroid": cluster.get("pca_centroid"),
                "supportive_explanation": cluster.get("supportive_explanation"),
                "recommended_card_ids": cluster.get("recommended_card_ids", []),
                "card_reason": cluster.get("card_reason", ""),
            }
            for cluster in model.get("clusters", [])
            if isinstance(cluster, dict)
        ],
        "feature_summary": {
            "answered_features": answered_count,
            "missing_features": len(missing_features),
            "total_features": len(features),
            "missing_feature_ids": missing_features[:20],
            "data_quality": "partial" if missing_features else "complete",
        },
        "raw_scores": {key: round(value, 4) if isinstance(value, (int, float)) else None for key, value in raw_scores.items()},
        "z_scores": {key: round(value, 4) for key, value in z_lookup.items()},
        "feature_profile": [
            {
                "feature_id": str(feature.get("feature_id")),
                "label": str(feature.get("label") or feature.get("feature_id")),
                "raw_score": round(raw_scores[str(feature.get("feature_id"))], 4)
                if isinstance(raw_scores.get(str(feature.get("feature_id"))), (int, float))
                else None,
                "z_score": round(z_lookup[str(feature.get("feature_id"))], 4),
            }
            for feature in features
            if str(feature.get("feature_id")) in z_lookup
        ],
        "explanation": (nearest_cluster.get("product_explanation") or explanation)
        if interpretation_guard["can_use_interpretation"]
        else explanation,
        "strength_note": (nearest_cluster.get("strength_note") or "") if interpretation_guard["can_use_interpretation"] else "",
        "small_step": (nearest_cluster.get("small_step") or "") if interpretation_guard["can_use_interpretation"] else "",
        "boundary_notice": model.get("boundary_notice")
        or "画像位置只用于群体参照和支持性解释，不构成诊断、筛查、治疗建议或人格标签。",
    }
