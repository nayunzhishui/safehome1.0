"""Assessment result to aggregate profile-position matching."""

from __future__ import annotations

import json
import hashlib
import math
from pathlib import Path
from typing import Any

from config import Config
from database import json_loads

LOW_CONFIDENCE_THRESHOLD = 0.15
OUTLIER_DISTANCE_FACTOR = 1.75
ALLOWED_ADMISSION_STATUSES = {"pilot_approved", "production_approved"}


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


def compute_model_artifact_hash(model: dict[str, Any]) -> str:
    material = {key: value for key, value in model.items() if key != "artifact_hash"}
    canonical = json.dumps(material, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def model_artifact_hash_is_valid(model: dict[str, Any]) -> bool:
    expected = model.get("artifact_hash")
    return isinstance(expected, str) and len(expected) == 64 and expected == compute_model_artifact_hash(model)


def model_is_connectable(model: dict[str, Any]) -> bool:
    """Return whether a governed model may be used for automatic matching."""

    return (
        model.get("admission_status") in ALLOWED_ADMISSION_STATUSES
        and model.get("worksheet_link_status") != "manual_review_required"
        and model_artifact_hash_is_valid(model)
    )


_is_connectable_model = model_is_connectable


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
    _source_value, model_value, missing = _feature_values(feature, answers, questions)
    return model_value, missing


def _feature_values(
    feature: dict[str, Any],
    answers: dict[str, dict[str, Any]],
    questions: dict[str, dict[str, Any]],
) -> tuple[float | None, float | None, bool]:
    question_id = feature.get("worksheet_question_id") or feature.get("feature_id")
    answer = answers.get(str(question_id))
    question = questions.get(str(question_id))
    value = _answer_score(answer, question)
    if value is None:
        return None, None, True
    if feature.get("reverse_scored"):
        bounds = _score_bounds(question, feature)
        if bounds:
            low, high = bounds
            value = low + high - value
    source_value = value
    transform = feature.get("input_transform") or {}
    if transform.get("type") == "linear_range":
        input_min = float(transform.get("input_min"))
        input_max = float(transform.get("input_max"))
        output_min = float(transform.get("output_min"))
        output_max = float(transform.get("output_max"))
        if input_max <= input_min:
            return source_value, None, True
        value = output_min + ((value - input_min) / (input_max - input_min)) * (output_max - output_min)
    return source_value, value, False


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


def _normalized_entropy(probabilities: list[float]) -> float:
    if len(probabilities) <= 1:
        return 0.0
    entropy = -sum(value * math.log(value) for value in probabilities if value > 0)
    return round(max(0.0, min(1.0, entropy / math.log(len(probabilities)))), 4)


def assign_profile_cluster(model: dict[str, Any], feature_ids: list[str], z_lookup: dict[str, float]) -> dict[str, Any]:
    """Assign one standardized vector using the artifact's declared algorithm."""

    clusters = [cluster for cluster in model.get("clusters", []) if isinstance(cluster, dict)]
    if not clusters:
        raise ProfilePositionUnavailable("画像模型缺少可比较的聚类中心。")

    method = model.get("selected_method")
    weights = model.get("mixture_weights") or []
    covariances = model.get("diag_covariances") or []
    if method == "gaussian_mixture" and len(weights) == len(clusters) == len(covariances):
        log_probabilities = []
        mahalanobis_distances = []
        for index, cluster in enumerate(clusters):
            center = cluster.get("center_z") or {}
            covariance = covariances[index]
            if isinstance(covariance, list):
                covariance = dict(zip(feature_ids, covariance))
            mahalanobis_squared = 0.0
            log_determinant = 0.0
            used = 0
            for feature_id in feature_ids:
                if feature_id not in center or feature_id not in covariance:
                    continue
                variance = max(float(covariance[feature_id]), 1e-9)
                difference = float(z_lookup[feature_id]) - float(center[feature_id])
                mahalanobis_squared += difference * difference / variance
                log_determinant += math.log(variance)
                used += 1
            if not used:
                log_probabilities.append(-math.inf)
                mahalanobis_distances.append(math.inf)
                continue
            log_probability = math.log(max(float(weights[index]), 1e-12)) - 0.5 * (
                used * math.log(2 * math.pi) + log_determinant + mahalanobis_squared
            )
            log_probabilities.append(log_probability)
            mahalanobis_distances.append(math.sqrt(mahalanobis_squared))
        maximum = max(log_probabilities)
        exponentials = [math.exp(value - maximum) if math.isfinite(value) else 0.0 for value in log_probabilities]
        total = sum(exponentials)
        probabilities = [value / total for value in exponentials] if total else [1 / len(clusters)] * len(clusters)
        order = sorted(range(len(clusters)), key=lambda index: probabilities[index], reverse=True)
        selected = order[0]
        return {
            "cluster": clusters[selected],
            "posterior": round(probabilities[selected], 6),
            "normalized_entropy": _normalized_entropy(probabilities),
            "mahalanobis_distance": round(mahalanobis_distances[selected], 6),
            "nearest_distance": round(_distance_to_center(clusters[selected], feature_ids, z_lookup), 6),
            "second_distance": round(_distance_to_center(clusters[order[1]], feature_ids, z_lookup), 6) if len(order) > 1 else None,
            "probabilities": [round(value, 6) for value in probabilities],
            "assignment_version": model.get("assignment_version") or "gmm_diag_posterior_v1",
        }

    distances = [(_distance_to_center(cluster, feature_ids, z_lookup), cluster) for cluster in clusters]
    distances.sort(key=lambda item: item[0])
    nearest, cluster = distances[0]
    second = distances[1][0] if len(distances) > 1 else None
    confidence = _confidence(nearest, second)
    return {
        "cluster": cluster,
        "posterior": confidence,
        "normalized_entropy": None,
        "mahalanobis_distance": nearest,
        "nearest_distance": nearest,
        "second_distance": second,
        "probabilities": [],
        "assignment_version": model.get("assignment_version") or "euclidean_center_v1",
    }


def interpretation_guard(model: dict[str, Any], assignment: dict[str, Any]) -> dict[str, Any]:
    approval = model.get("interpretation_approval_status", "pending_researcher_review")
    if approval not in {"pilot_approved", "production_approved"}:
        return {
            "status": "pending_approval",
            "can_use_interpretation": False,
            "message": "该画像解释仍在研究者审核中，本次只显示本人维度位置，不显示画像名称或自动任务建议。",
        }
    thresholds = model.get("assignment_thresholds") or {}
    max_mahalanobis = float(thresholds.get("max_mahalanobis", math.sqrt(max(int(model.get("n_features") or 1), 1)) * OUTLIER_DISTANCE_FACTOR))
    min_posterior = float(thresholds.get("min_posterior", LOW_CONFIDENCE_THRESHOLD))
    max_entropy = float(thresholds.get("max_entropy", 1.0))
    if float(assignment.get("mahalanobis_distance") or 0) > max_mahalanobis:
        return {
            "status": "outlier",
            "can_use_interpretation": False,
            "message": "本次结果与建模样本的常见范围距离较远，因此只保留维度位置，不做画像解释。",
            "max_mahalanobis": max_mahalanobis,
        }
    entropy = assignment.get("normalized_entropy")
    if float(assignment.get("posterior") or 0) < min_posterior or (entropy is not None and float(entropy) > max_entropy):
        return {
            "status": "low_confidence",
            "can_use_interpretation": False,
            "message": "本次结果与多个聚合位置接近，因此只保留维度位置，不做明确画像判断。",
            "min_posterior": min_posterior,
            "max_entropy": max_entropy,
        }
    return {
        "status": "usable",
        "can_use_interpretation": True,
        "message": "本次画像匹配达到当前试点的最低解释条件。",
        "min_posterior": min_posterior,
        "max_entropy": max_entropy,
        "max_mahalanobis": max_mahalanobis,
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
    worksheet_raw_scores: dict[str, float | None] = {}
    model_input_scores: dict[str, float | None] = {}
    missing_features: list[str] = []

    for feature in features:
        feature_id = str(feature.get("feature_id"))
        source_value, value, missing = _feature_values(feature, answers, questions)
        if missing:
            missing_features.append(feature_id)
            value = float(feature.get("mean") or 0)
        worksheet_raw_scores[feature_id] = source_value
        model_input_scores[feature_id] = value
        mean = float(feature.get("mean") or 0)
        std = float(feature.get("std") or 1) or 1
        z_lookup[feature_id] = (float(value) - mean) / std

    answered_count = len(features) - len(missing_features)
    if answered_count < max(2, math.ceil(len(features) * 0.6)):
        raise ProfilePositionUnavailable("本次填写可用于画像匹配的题项不足。")

    feature_ids = [str(feature.get("feature_id")) for feature in features]
    z_values = [z_lookup[feature_id] for feature_id in feature_ids]
    assignment = assign_profile_cluster(model, feature_ids, z_lookup)
    nearest_cluster = assignment["cluster"]
    nearest_distance = assignment["nearest_distance"]
    second_distance = assignment["second_distance"]
    pca = _pca_position(model, z_values)
    confidence = assignment["posterior"]
    guard = interpretation_guard(model, assignment)
    profile_name = nearest_cluster.get("profile_name") or f"画像{nearest_cluster.get('cluster_id', '')}"
    if guard["can_use_interpretation"]:
        explanation = (
            f"您当前的填写结果在本研究组中更接近「{profile_name}」。"
            "这个位置表示与既往样本题项组合的相对接近程度，只用于支持性理解和后续练习参考，不代表诊断或固定标签。"
        )
    else:
        explanation = guard["message"]
    visible_profile_name = profile_name if guard["can_use_interpretation"] else None

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
            "profile_name": visible_profile_name,
            "display_name": nearest_cluster.get("display_name") if guard["can_use_interpretation"] else None,
            "nearest_distance": round(float(nearest_distance), 4),
            "second_distance": round(float(second_distance), 4) if second_distance is not None else None,
            "confidence": confidence,
            "posterior": assignment["posterior"],
            "normalized_entropy": assignment["normalized_entropy"],
            "mahalanobis_distance": assignment["mahalanobis_distance"],
            "assignment_version": assignment["assignment_version"],
            "interpretation_status": guard["status"],
            "can_use_interpretation": guard["can_use_interpretation"],
        },
        "interpretation": guard,
        "radar_support": model.get("radar_support", {}),
        "suggested_assessment_questions": nearest_cluster.get("suggested_assessment_questions", []) if guard["can_use_interpretation"] else [],
        "recommended_project_tasks": nearest_cluster.get("recommended_project_tasks", []) if guard["can_use_interpretation"] else [],
        "clusters": [
            {
                "cluster_id": cluster.get("cluster_id"),
                "profile_id": cluster.get("profile_id"),
                "profile_name": cluster.get("profile_name") if guard["can_use_interpretation"] else None,
                "display_name": cluster.get("display_name") if guard["can_use_interpretation"] else None,
                "n": cluster.get("n"),
                "percent": cluster.get("percent"),
                "pca_centroid": cluster.get("pca_centroid"),
                "supportive_explanation": cluster.get("supportive_explanation") if guard["can_use_interpretation"] else None,
                "dimension_means": cluster.get("dimension_means", {}),
                "dimension_z": cluster.get("dimension_z", {}),
                "suggested_assessment_questions": cluster.get("suggested_assessment_questions", []) if guard["can_use_interpretation"] else [],
                "recommended_project_tasks": cluster.get("recommended_project_tasks", []) if guard["can_use_interpretation"] else [],
                "recommended_card_ids": cluster.get("recommended_card_ids", []) if guard["can_use_interpretation"] else [],
                "card_reason": cluster.get("card_reason", "") if guard["can_use_interpretation"] else "",
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
        "raw_scores": {key: round(value, 4) if isinstance(value, (int, float)) else None for key, value in worksheet_raw_scores.items()},
        "worksheet_raw_scores": {key: round(value, 4) if isinstance(value, (int, float)) else None for key, value in worksheet_raw_scores.items()},
        "model_input_scores": {key: round(value, 4) if isinstance(value, (int, float)) else None for key, value in model_input_scores.items()},
        "score_spaces_separated": True,
        "z_scores": {key: round(value, 4) for key, value in z_lookup.items()},
        "feature_profile": [
            {
                "feature_id": str(feature.get("feature_id")),
                "label": str(feature.get("label") or feature.get("feature_id")),
                "raw_score": round(worksheet_raw_scores[str(feature.get("feature_id"))], 4)
                if isinstance(worksheet_raw_scores.get(str(feature.get("feature_id"))), (int, float))
                else None,
                "model_input_score": round(model_input_scores[str(feature.get("feature_id"))], 4)
                if isinstance(model_input_scores.get(str(feature.get("feature_id"))), (int, float))
                else None,
                "z_score": round(z_lookup[str(feature.get("feature_id"))], 4),
            }
            for feature in features
            if str(feature.get("feature_id")) in z_lookup
        ],
        "explanation": (nearest_cluster.get("product_explanation") or explanation)
        if guard["can_use_interpretation"]
        else explanation,
        "strength_note": (nearest_cluster.get("strength_note") or "") if guard["can_use_interpretation"] else "",
        "small_step": (nearest_cluster.get("small_step") or "") if guard["can_use_interpretation"] else "",
        "boundary_notice": model.get("boundary_notice")
        or "画像位置只用于群体参照和支持性解释，不构成诊断、筛查、治疗建议或人格标签。",
    }
