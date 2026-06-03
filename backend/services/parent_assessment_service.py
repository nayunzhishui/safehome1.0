"""Parent dual-scale assessment service migrated from ReadFeedback."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from services.content_loader import load_parent_questions, load_parent_report_rules, load_parent_scales


class ParentAssessmentInputError(ValueError):
    """Raised when parent assessment input is invalid."""

    def __init__(self, missing_fields: list[str]) -> None:
        super().__init__(f"家长测评提交不完整：{', '.join(missing_fields)}")
        self.missing_fields = missing_fields


def _items(scales_payload: dict) -> dict[str, dict[str, Any]]:
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


def _normalise_answers(raw_answers) -> dict[str, str]:
    if isinstance(raw_answers, list):
        answers = {}
        for answer in raw_answers:
            if isinstance(answer, dict):
                code = answer.get("item_code") or answer.get("question_id") or answer.get("id")
                if code:
                    answers[str(code)] = str(answer.get("value", "")).strip()
        return answers
    if isinstance(raw_answers, dict):
        return {str(key): str(value).strip() for key, value in raw_answers.items()}
    return {}


def _mean(values: list[int]) -> float:
    return round(sum(values) / len(values), 3) if values else 0


def score_parent_scale_answers(answers: dict[str, str]) -> dict[str, Any]:
    scales_payload = load_parent_scales()
    item_map = _items(scales_payload)
    missing = [code for code in item_map if answers.get(code) not in {"1", "2", "3", "4", "5"}]
    if missing:
        raise ParentAssessmentInputError(missing)

    item_scores: dict[str, dict[str, Any]] = {}
    scale_acc: dict[str, list[int]] = {}
    dimension_acc: dict[str, dict[str, list[int]]] = {}
    for item_code, item in item_map.items():
        raw = int(answers[item_code])
        scored = 6 - raw if item.get("reverse_scored") else raw
        scale_code = item.get("scale_code")
        dimension = item.get("dimension")
        scale_acc.setdefault(scale_code, []).append(scored)
        dimension_acc.setdefault(scale_code, {}).setdefault(dimension, []).append(scored)
        item_scores[item_code] = {
            "raw": raw,
            "scored": scored,
            "scale_code": scale_code,
            "dimension": dimension,
            "reverse_scored": bool(item.get("reverse_scored")),
        }

    scale_lookup = {scale.get("scale_code"): scale for scale in scales_payload.get("scales", [])}
    scales = {}
    for scale_code, values in scale_acc.items():
        scale = scale_lookup.get(scale_code, {})
        scales[scale_code] = {
            "name": scale.get("name"),
            "short_name": scale.get("short_name"),
            "total": sum(values),
            "mean": _mean(values),
            "count": len(values),
            "dimensions": {
                dimension: {
                    "total": sum(dimension_values),
                    "mean": _mean(dimension_values),
                    "count": len(dimension_values),
                }
                for dimension, dimension_values in dimension_acc.get(scale_code, {}).items()
            },
            "score_direction": scale.get("score_direction"),
        }

    return {
        "version": scales_payload.get("version"),
        "scales": scales,
        "item_scores": item_scores,
    }


def score_parent_questions(question_answers: dict[str, str]) -> dict[str, Any]:
    payload = load_parent_questions()
    totals = {
        "pressure": 0,
        "support": 0,
        "awareness": 0,
        "self_demand": 0,
        "self_compassion": 0,
        "success": 0,
        "willingness": 0,
    }
    selected: dict[str, str] = {}
    for question in payload.get("questions", []):
        question_id = question.get("id")
        value = question_answers.get(question_id)
        if not value:
            continue
        selected[question_id] = value
        for option in question.get("options", []):
            if str(option.get("value")) == str(value):
                for key, score in option.get("scores", {}).items():
                    totals[key] = totals.get(key, 0) + int(score)
                break
    return {"version": payload.get("version"), "totals": totals, "selected": selected}


def choose_parent_profile(scale_scores: dict[str, Any], question_scores: dict[str, Any]) -> str:
    totals = question_scores.get("totals", {})
    scales = scale_scores.get("scales", {})
    scs_mean = float(scales.get("SCS_SF_CN_12", {}).get("mean", 0))
    ius_mean = float(scales.get("IUS_12_CN", {}).get("mean", 0))

    if totals.get("success", 0) >= 2 and totals.get("pressure", 0) <= 2 and scs_mean >= 3.2:
        return "success_willing"
    if totals.get("self_demand", 0) >= 3 or (scs_mean and scs_mean < 2.8):
        return "high_demand_low_compassion"
    if totals.get("pressure", 0) >= 4 or ius_mean >= 3.6:
        return "high_pressure_low_support_aware"
    return "gentle_support"


def _duration_seconds(started_at: str | None, completed_at: str | None) -> int:
    if not started_at or not completed_at:
        return 0
    try:
        started = datetime.fromisoformat(started_at)
        completed = datetime.fromisoformat(completed_at)
        return max(0, int((completed - started).total_seconds()))
    except ValueError:
        return 0


def build_quality_flags(payload: dict, answers: dict[str, str]) -> dict[str, Any]:
    duration = _duration_seconds(payload.get("started_at"), payload.get("completed_at"))
    flags: list[str] = []
    if duration and duration < 60:
        flags.append("too_fast")
    if not str(payload.get("participant_code") or "").strip():
        flags.append("missing_participant_code")
    missing_count = sum(1 for value in answers.values() if value == "")
    if missing_count:
        flags.append("missing_answers")
    return {
        "flags": flags,
        "duration_seconds": duration,
        "missing_count": missing_count,
        "note": "数据质量标记只用于研究数据清洗，不评价填写者。",
    }


def build_parent_report(profile_key: str, scale_scores: dict[str, Any], question_scores: dict[str, Any], quality_flags: dict[str, Any]) -> dict[str, Any]:
    rules = load_parent_report_rules()
    profile = rules.get("profiles", {}).get(profile_key) or rules.get("profiles", {}).get("gentle_support", {})
    scales = scale_scores.get("scales", {})
    scs = scales.get("SCS_SF_CN_12", {})
    ius = scales.get("IUS_12_CN", {})
    return {
        "profile_key": profile_key,
        "role": profile.get("role", "正在靠近自己的照顾者"),
        "summary": profile.get("summary", "本报告只用于自我观察和支持性练习，不构成诊断。"),
        "empathy": profile.get("empathy", "你愿意完成这份测评，已经是在为关系打开一个整理入口。"),
        "strength": profile.get("strength", "你愿意停下来观察自己，这是后续改变的基础。"),
        "action_title": profile.get("action_title", "选择一个小动作"),
        "action": profile.get("action", "今天只选择一个最容易执行的小动作。"),
        "course": profile.get("course", "安心家练习卡"),
        "metrics": [
            {"label": "自我关怀均分", "value": f"{float(scs.get('mean', 0)):.2f}"},
            {"label": "不确定性不耐受均分", "value": f"{float(ius.get('mean', 0)):.2f}"},
            {"label": "数据质量", "value": "需复核" if quality_flags.get("flags") else "正常"},
        ],
        "scale_report": {
            "SCS_SF_CN_12": scs,
            "IUS_12_CN": ius,
        },
        "question_scores": question_scores,
        "quality_flags": quality_flags,
        "boundary_notice": "家长反馈只用于自我理解和亲子沟通练习，不构成临床诊断，也不评价家长或孩子的人格。",
    }


def create_parent_assessment_result(payload: dict) -> dict[str, Any]:
    answers = _normalise_answers(payload.get("answers"))
    question_answers = _normalise_answers(payload.get("question_answers"))
    scale_scores = score_parent_scale_answers(answers)
    question_scores = score_parent_questions(question_answers)
    profile_key = choose_parent_profile(scale_scores, question_scores)
    quality_flags = build_quality_flags(payload, answers)
    report = build_parent_report(profile_key, scale_scores, question_scores, quality_flags)
    return {
        "answers": answers,
        "question_answers": question_answers,
        "scores": scale_scores,
        "question_scores": question_scores,
        "profile_key": profile_key,
        "report": report,
        "quality_flags": quality_flags,
        "duration_seconds": quality_flags.get("duration_seconds", 0),
        "questionnaire_version": load_parent_scales().get("version"),
        "scoring_version": "safehome-parent-dual-scale-v1",
    }


def get_parent_assessment_payload() -> dict[str, Any]:
    return {
        "scales": load_parent_scales(),
        "questions": load_parent_questions(),
        "boundary_notice": "家长测评只用于自我观察、研究数据整理和支持性练习，不构成诊断。",
    }
