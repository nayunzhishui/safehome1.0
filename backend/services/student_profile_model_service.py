"""KMeans/PCA student profile service migrated from ReadFeedback."""

from __future__ import annotations

from typing import Any

from database import now_iso
from services.content_loader import (
    load_sandplay_tasks,
    load_student_profile_model,
    load_student_profile_rules_kmeans,
    load_student_scales,
    load_training_cards,
)
from services.risk_service import check_text_risk

PROFILE_MODEL_TYPE = "readfeedback-kmeans-pca"

PROFILE_NAME_OVERRIDES = {
    "high_iu_low_sc": "不确定压力与自我支持发展画像",
    "self_critical_perfection": "高标准与自我支持压力画像",
    "low_erf_high_ta": "调节策略发展画像",
    "middle_uncertain": "中等波动待收束画像",
    "stable_resource": "资源稳定画像",
}

PROFILE_CARD_MAP = {
    "high_iu_low_sc": ["self_support_statement", "sandplay_expression_01"],
    "self_critical_perfection": ["cbt_auto_thought_student", "self_support_statement"],
    "low_erf_high_ta": ["student_emotion_naming", "sandplay_expression_01"],
    "middle_uncertain": ["student_emotion_naming", "cbt_auto_thought_student"],
    "stable_resource": ["student_emotion_naming", "sandplay_expression_01"],
}


class ProfileInputError(ValueError):
    """Raised when profile input is missing required answers or scores."""

    def __init__(self, missing_fields: list[str]) -> None:
        super().__init__(f"缺少画像生成所需字段：{', '.join(missing_fields)}")
        self.missing_fields = missing_fields


def _as_number(value) -> float | None:
    try:
        if value in (None, ""):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _student_items(scales_payload: dict) -> dict[str, dict[str, Any]]:
    items: dict[str, dict[str, Any]] = {}
    for scale in scales_payload.get("scales", []):
        for item in scale.get("items", []):
            item_code = item.get("item_code")
            if item_code:
                items[item_code] = {
                    **item,
                    "scale_code": scale.get("scale_code"),
                    "scale_name": scale.get("name"),
                    "scale_short_name": scale.get("short_name"),
                }
    return items


def _normalise_answers(payload: dict, item_codes: set[str]) -> dict[str, str]:
    raw_answers = payload.get("answers")
    if isinstance(raw_answers, list):
        answers = {}
        for answer in raw_answers:
            if isinstance(answer, dict):
                code = answer.get("item_code") or answer.get("question_id") or answer.get("id")
                if code:
                    answers[str(code)] = str(answer.get("value", "")).strip()
        raw_answers = answers
    if isinstance(raw_answers, dict):
        return {code: str(raw_answers.get(code, "")).strip() for code in item_codes}
    return {}


def _normalise_text_answers(payload: dict, scales_payload: dict) -> dict[str, str]:
    text_answers: dict[str, str] = {}
    raw = payload.get("text_answers") if isinstance(payload.get("text_answers"), dict) else {}
    for question in scales_payload.get("open_questions", []):
        code = question.get("item_code")
        if not code:
            continue
        value = raw.get(code)
        if value is None and code == "TEXT01":
            value = payload.get("free_text")
        if value is None and code == "TEXT02":
            value = payload.get("followup_text")
        max_length = int(question.get("max_length") or 600)
        text_answers[code] = str(value or "").strip()[:max_length]
    if payload.get("free_text") and not text_answers:
        text_answers["free_text"] = str(payload.get("free_text")).strip()[:600]
    return text_answers


def _likert_values(scales_payload: dict) -> list[int]:
    values = [
        int(float(option["value"]))
        for option in scales_payload.get("likert", [])
        if isinstance(option, dict) and _as_number(option.get("value")) is not None
    ]
    return sorted(set(values)) or [1, 2, 3, 4, 5]


def _validate_answers(answers: dict[str, str], item_codes: set[str], allowed_values: set[str]) -> list[str]:
    errors: list[str] = []
    for code in sorted(item_codes):
        value = answers.get(code, "")
        if value not in allowed_values:
            errors.append(code)
    return errors


def _reverse_score(raw: int, likert_values: list[int]) -> int:
    return min(likert_values) + max(likert_values) - raw


def _mean(values: list[float]) -> float:
    return round(sum(values) / len(values), 4) if values else 0.0


def score_student_answers(answers: dict[str, str]) -> dict[str, Any]:
    scales_payload = load_student_scales()
    items = _student_items(scales_payload)
    likert_values = _likert_values(scales_payload)
    allowed_values = {str(value) for value in likert_values}
    missing = _validate_answers(answers, set(items), allowed_values)
    if missing:
        raise ProfileInputError(missing)

    model = load_student_profile_model()
    feature_acc: dict[str, list[float]] = {feature: [] for feature in model.get("features", [])}
    scale_acc: dict[str, list[float]] = {}
    dimension_acc: dict[str, dict[str, list[float]]] = {}
    item_scores: dict[str, dict[str, Any]] = {}

    for item_code, item in items.items():
        raw = int(answers[item_code])
        scored = _reverse_score(raw, likert_values) if item.get("reverse_scored") else raw
        scale_code = item.get("scale_code")
        dimension = item.get("dimension")
        feature = item.get("feature")
        scale_acc.setdefault(scale_code, []).append(scored)
        dimension_acc.setdefault(scale_code, {}).setdefault(dimension, []).append(scored)

        if scale_code == "SCS":
            feature_acc["self_compassion"].append(scored)
            if dimension == "self_criticism":
                feature_acc["self_criticism_raw"].append(raw)
        elif scale_code == "IUS":
            feature_acc["iu_total"].append(scored)
        elif scale_code == "ERF" and feature:
            feature_acc[feature].append(scored)
        elif scale_code == "TA":
            feature_acc["test_anxiety"].append(scored)
            if feature:
                feature_acc[feature].append(scored)

        item_scores[item_code] = {
            "raw": raw,
            "scored": scored,
            "dimension": dimension,
            "scale_code": scale_code,
            "reverse_scored": bool(item.get("reverse_scored")),
        }

    scales = {}
    scale_lookup = {scale.get("scale_code"): scale for scale in scales_payload.get("scales", [])}
    for scale_code, values in scale_acc.items():
        scale = scale_lookup.get(scale_code, {})
        scales[scale_code] = {
            "name": scale.get("name"),
            "short_name": scale.get("short_name"),
            "mean": round(sum(values) / len(values), 3) if values else 0,
            "total": sum(values),
            "dimensions": {
                dimension: {
                    "mean": round(sum(dimension_values) / len(dimension_values), 3),
                    "total": sum(dimension_values),
                    "count": len(dimension_values),
                }
                for dimension, dimension_values in dimension_acc.get(scale_code, {}).items()
            },
        }

    return {
        "version": scales_payload.get("version"),
        "scales": scales,
        "features": {feature: _mean(values) for feature, values in feature_acc.items()},
        "item_scores": item_scores,
        "data_quality": "full_scale_answers",
    }


def _compat_scores(payload: dict) -> dict[str, Any]:
    model = load_student_profile_model()
    raw_scores = payload.get("scores") if isinstance(payload.get("scores"), dict) else payload
    means = model.get("feature_means", {})
    required = {
        "test_anxiety": raw_scores.get("test_anxiety"),
        "iu_total": raw_scores.get("iu_total", raw_scores.get("iu_score")),
        "self_compassion": raw_scores.get("self_compassion"),
    }
    missing = [key for key, value in required.items() if _as_number(value) is None]
    if missing:
        raise ProfileInputError(missing)

    features = {feature: float(means.get(feature, 0)) for feature in model.get("features", [])}
    features["iu_total"] = float(required["iu_total"])
    features["self_compassion"] = float(required["self_compassion"])
    features["test_anxiety"] = float(required["test_anxiety"])
    features["test_anxiety_worry"] = float(raw_scores.get("test_anxiety_worry") or features["test_anxiety"])
    features["test_anxiety_emotionality"] = float(raw_scores.get("test_anxiety_emotionality") or features["test_anxiety"])

    for feature in ["erf_evaluation", "erf_expression", "erf_strategy_flex", "self_criticism_raw"]:
        value = _as_number(raw_scores.get(feature))
        if value is not None:
            features[feature] = value

    return {
        "version": "aggregate-scores-adapter",
        "scales": {},
        "features": {key: round(value, 4) for key, value in features.items()},
        "item_scores": {},
        "data_quality": "aggregate_scores_adapter",
    }


def _project_pc(z_values: list[float], model: dict) -> tuple[float, float]:
    components = model.get("pca_components", [[0], [0]])
    pc1 = sum(z_values[index] * float(components[0][index]) for index in range(len(z_values)))
    pc2 = sum(z_values[index] * float(components[1][index]) for index in range(len(z_values)))
    return pc1, pc2


def _soft_profile_name(profile_id: str, fallback: str) -> str:
    return PROFILE_NAME_OVERRIDES.get(profile_id, fallback.replace("型", "画像"))


def classify_student_profile(features: dict[str, float]) -> dict[str, Any]:
    model = load_student_profile_model()
    rules = load_student_profile_rules_kmeans().get("profiles", {})
    feature_names = model.get("features", [])
    z_values = []
    for feature in feature_names:
        mean = float(model.get("feature_means", {}).get(feature, 0))
        std = float(model.get("feature_stds", {}).get(feature, 1)) or 1.0
        z_values.append((float(features.get(feature, mean)) - mean) / std)

    distances = []
    for cluster in model.get("clusters", []):
        center = [float(value) for value in cluster.get("center", [])]
        distance = sum((z_values[index] - center[index]) ** 2 for index in range(len(feature_names))) ** 0.5
        distances.append(float(distance))

    if not distances:
        raise ProfileInputError(["student_profile_model.clusters"])

    order = sorted(range(len(distances)), key=lambda index: distances[index])
    cluster = model["clusters"][order[0]]
    second_distance = distances[order[1]] if len(order) > 1 else distances[order[0]]
    confidence = max(0.0, min(1.0, (second_distance - distances[order[0]]) / (second_distance + 1e-9)))
    pc1, pc2 = _project_pc(z_values, model)
    profile_id = cluster.get("profile_id")
    rule = rules.get(profile_id, {})

    return {
        "cluster_id": cluster.get("cluster_id"),
        "profile_code": profile_id,
        "profile_id": profile_id,
        "profile_name": _soft_profile_name(profile_id, cluster.get("profile_name", "阶段性支持画像")),
        "original_profile_name": cluster.get("profile_name"),
        "confidence": round(confidence, 3),
        "nearest_distance": round(distances[order[0]], 4),
        "second_distance": round(second_distance, 4),
        "pc1": round(pc1, 4),
        "pc2": round(pc2, 4),
        "summary": rule.get("summary", "本次结果用于支持性理解，不构成诊断。"),
        "mechanism": rule.get("mechanism", "可结合场景、情绪、身体反应和可用支持继续观察。"),
        "first_task": rule.get("first_task") or cluster.get("first_task") or "先完成一次情绪命名练习。",
        "integrative_path": rule.get("integrative_path", {}),
        "next_questions": rule.get("next_questions", []),
        "escalation": rule.get("escalation", "如出现持续失眠、惊恐或伤害自己的想法，请及时联系可信成年人或专业支持资源。"),
    }


def _level(value: float, high: float = 3.5, low: float = 2.5, reverse_positive: bool = False) -> str:
    if reverse_positive:
        if value >= high:
            return "available"
        if value <= low:
            return "needs_support"
        return "developing"
    if value >= high:
        return "high"
    if value <= low:
        return "low"
    return "medium"


def _dimensions(features: dict[str, float]) -> list[dict[str, Any]]:
    erf = (features.get("erf_evaluation", 0) + features.get("erf_expression", 0) + features.get("erf_strategy_flex", 0)) / 3
    return [
        {
            "key": "test_anxiety",
            "label": "考试压力反应",
            "value": round(features.get("test_anxiety", 0), 2),
            "level": _level(features.get("test_anxiety", 0)),
            "summary": "用于观察考试相关担心、身体紧张和发挥受影响程度。",
        },
        {
            "key": "iu_total",
            "label": "不确定性耐受",
            "value": round(features.get("iu_total", 0), 2),
            "level": _level(features.get("iu_total", 0)),
            "summary": "用于观察结果未定、信息不足时的压力放大程度。",
        },
        {
            "key": "self_compassion",
            "label": "自我支持资源",
            "value": round(features.get("self_compassion", 0), 2),
            "level": _level(features.get("self_compassion", 0), reverse_positive=True),
            "summary": "用于观察能否用具体、温和的方式支持自己。",
        },
        {
            "key": "erf",
            "label": "情绪调节灵活性",
            "value": round(erf, 2),
            "level": _level(erf, reverse_positive=True),
            "summary": "用于观察能否根据情境切换理解、表达和应对策略。",
        },
    ]


def extract_keywords(text: str) -> list[dict[str, Any]]:
    lexicon = ["焦虑", "担心", "紧张", "害怕", "失败", "比较", "父母", "成绩", "复习", "拖延", "失眠", "放松", "支持", "计划", "努力", "进步"]
    counts = [{"word": word, "count": text.count(word)} for word in lexicon if text.count(word)]
    counts.sort(key=lambda item: item["count"], reverse=True)
    return counts[:8]


def _valid_card_ids() -> set[str]:
    return {card.get("id") for card in load_training_cards().get("cards", []) if card.get("id")}


def _recommended_cards(profile_code: str) -> list[str]:
    valid = _valid_card_ids()
    return [card_id for card_id in PROFILE_CARD_MAP.get(profile_code, ["student_emotion_naming"]) if card_id in valid]


def _sandplay_task(profile_code: str) -> dict[str, Any]:
    payload = load_sandplay_tasks()
    task = dict(payload.get("default", {}))
    task.update(payload.get("profiles", {}).get(profile_code, {}))
    return {**task, "symbols": payload.get("symbols", [])}


def build_student_visuals(scores: dict[str, Any], profile_result: dict[str, Any], followups: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    model = load_student_profile_model()
    features = scores.get("features", {})
    erf = (features.get("erf_evaluation", 0) + features.get("erf_expression", 0) + features.get("erf_strategy_flex", 0)) / 3
    trends = [
        {
            "round": 0,
            "label": "初测",
            "state_score": round(features.get("test_anxiety", 0), 2),
            "profile_confidence": profile_result.get("confidence"),
        }
    ]
    for followup in followups or []:
        trends.append(
            {
                "round": followup.get("round_no"),
                "label": f"第{followup.get('round_no')}轮",
                "state_score": followup.get("state_score"),
                "profile_confidence": profile_result.get("confidence"),
            }
        )
    return {
        "radar": [
            {"label": "IU", "value": round(features.get("iu_total", 0), 2), "max": 5},
            {"label": "ERF", "value": round(erf, 2), "max": 5},
            {"label": "自我支持", "value": round(features.get("self_compassion", 0), 2), "max": 5},
            {"label": "考试压力", "value": round(features.get("test_anxiety", 0), 2), "max": 5},
        ],
        "pca": {
            "user": {
                "pc1": profile_result.get("pc1"),
                "pc2": profile_result.get("pc2"),
                "cluster_id": profile_result.get("cluster_id"),
                "profile_code": profile_result.get("profile_code"),
            },
            "points": model.get("training_points", []),
            "clusters": [
                {
                    **cluster,
                    "profile_name": _soft_profile_name(cluster.get("profile_id"), cluster.get("profile_name", "")),
                }
                for cluster in model.get("clusters", [])
            ],
        },
        "trends": trends,
    }


def _high_risk_profile(scores: dict[str, Any], risk_result: dict, text_answers: dict[str, str]) -> dict[str, Any]:
    profile_result = {
        "cluster_id": None,
        "profile_code": "requires_review",
        "profile_id": "requires_review",
        "profile_name": "需要人工关注的支持提示",
        "confidence": 0,
        "nearest_distance": None,
        "second_distance": None,
        "pc1": None,
        "pc2": None,
        "summary": risk_result.get("safe_response"),
        "mechanism": "当前文本包含需要人工优先查看的线索，系统不自动给出画像解释。",
        "first_task": "请先联系现实中的可信成年人、学校老师、专业机构或当地紧急服务。",
        "integrative_path": {},
        "next_questions": [],
        "escalation": risk_result.get("safe_response"),
    }
    return _build_response(scores, profile_result, text_answers, risk_result, "high_risk_review")


def _build_response(scores: dict[str, Any], profile_result: dict[str, Any], text_answers: dict[str, str], risk_result: dict, data_quality: str) -> dict[str, Any]:
    model = load_student_profile_model()
    rules = load_student_profile_rules_kmeans()
    profile_code = profile_result.get("profile_code")
    text = " ".join(text_answers.values())
    dimensions = _dimensions(scores.get("features", {}))
    if risk_result.get("allow_recommended_training_cards") is False or risk_result.get("risk_level") == "high":
        recommended_card_ids = []
    else:
        recommended_card_ids = _recommended_cards(profile_code)
    sandplay_task = _sandplay_task(profile_code)
    report = {
        "role": profile_result.get("profile_name"),
        "summary": profile_result.get("summary"),
        "mechanism": profile_result.get("mechanism"),
        "first_task": profile_result.get("first_task"),
        "integrative_path": profile_result.get("integrative_path", {}),
        "next_questions": profile_result.get("next_questions", []),
        "escalation": profile_result.get("escalation"),
        "metrics": [
            {"label": "画像置信度", "value": f"{float(profile_result.get('confidence') or 0):.2f}"},
            {"label": "考试压力均分", "value": f"{scores.get('features', {}).get('test_anxiety', 0):.2f}"},
            {"label": "不确定性不耐受", "value": f"{scores.get('features', {}).get('iu_total', 0):.2f}"},
            {"label": "自我支持资源", "value": f"{scores.get('features', {}).get('self_compassion', 0):.2f}"},
        ],
        "keywords": extract_keywords(text),
        "sandplay_task": sandplay_task,
    }
    visuals = build_student_visuals(scores, profile_result)
    boundary_notice = "本画像来自研究聚类模型，只用于阶段性支持理解和练习推荐，不构成临床诊断，也不代表固定人格。"
    return {
        "profile_code": profile_code,
        "profile_name": profile_result.get("profile_name"),
        "original_profile_name": profile_result.get("original_profile_name"),
        "confidence": profile_result.get("confidence"),
        "cluster_id": profile_result.get("cluster_id"),
        "pc1": profile_result.get("pc1"),
        "pc2": profile_result.get("pc2"),
        "nearest_distance": profile_result.get("nearest_distance"),
        "second_distance": profile_result.get("second_distance"),
        "dimensions": dimensions,
        "supportive_explanation": profile_result.get("summary"),
        "strength_note": "你愿意完成这次整理，本身就是把模糊压力变具体的一步。",
        "small_step": profile_result.get("first_task"),
        "recommended_card_ids": recommended_card_ids,
        "risk_level": risk_result.get("risk_level", "low"),
        "requires_review": bool(risk_result.get("requires_review") or risk_result.get("risk_level") == "high"),
        "allow_auto_feedback": bool(risk_result.get("allow_auto_feedback", True)) and risk_result.get("risk_level") != "high",
        "model_version": model.get("version"),
        "model_type": PROFILE_MODEL_TYPE,
        "rules_version": rules.get("version"),
        "boundary_notice": boundary_notice,
        "scores": scores,
        "text_answers": text_answers,
        "text_features": {
            "free_text_present": bool(text.strip()),
            "free_text_length": len(text),
            "keywords": report["keywords"],
        },
        "profile_result": profile_result,
        "report": report,
        "visuals": visuals,
        "sandplay_task": sandplay_task,
        "data_quality": data_quality,
        "created_at": now_iso(),
    }


def generate_student_profile(payload: dict) -> dict:
    """Generate a student profile using the migrated ReadFeedback KMeans/PCA model."""

    scales_payload = load_student_scales()
    items = _student_items(scales_payload)
    answers = _normalise_answers(payload, set(items))
    text_answers = _normalise_text_answers(payload, scales_payload)
    if answers:
        scores = score_student_answers(answers)
    else:
        scores = _compat_scores(payload)

    free_text = " ".join(text_answers.values()).strip()
    risk_result = check_text_risk(free_text, source="student_profile")
    if risk_result.get("risk_level") == "high":
        return _high_risk_profile(scores, risk_result, text_answers)

    profile_result = classify_student_profile(scores.get("features", {}))
    return _build_response(scores, profile_result, text_answers, risk_result, scores.get("data_quality", "valid"))


def get_student_assessment_payload() -> dict:
    payload = load_student_scales()
    return {
        **payload,
        "model_version": load_student_profile_model().get("version"),
        "boundary_notice": "学生测评只用于阶段性支持画像和练习推荐，不构成诊断。",
    }


def get_model_info_payload() -> dict:
    model = load_student_profile_model()
    rules = load_student_profile_rules_kmeans()
    return {
        "model_version": model.get("version"),
        "model_type": PROFILE_MODEL_TYPE,
        "rules_version": rules.get("version"),
        "n_cases": model.get("n_cases"),
        "features": model.get("features", []),
        "available_profiles": [
            {
                "profile_code": cluster.get("profile_id"),
                "profile_name": _soft_profile_name(cluster.get("profile_id"), cluster.get("profile_name", "")),
                "original_profile_name": cluster.get("profile_name"),
                "cluster_id": cluster.get("cluster_id"),
                "enabled": True,
                "risk_level": "low",
            }
            for cluster in model.get("clusters", [])
        ],
        "boundary_notice": "学生画像只用于支持性理解和练习推荐，不构成临床诊断。",
    }
