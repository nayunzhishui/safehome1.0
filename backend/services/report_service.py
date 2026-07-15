"""Weekly report service for the MVP backend."""

from collections import Counter
from datetime import date, datetime, timedelta

from database import get_connection, json_loads, rows_to_dicts
from services.progress_summary_service import build_training_effectiveness


def _parse_date(value: str | None) -> date:
    if not value:
        today = date.today()
        return today - timedelta(days=today.weekday())
    return datetime.fromisoformat(value).date()


def _direction(delta: float | None) -> str:
    if delta is None:
        return "暂无变化"
    if abs(delta) < 0.01:
        return "变化不大"
    return "上升" if delta > 0 else "下降"


def _build_assessment_summary(assessments: list[dict]) -> dict:
    worksheet_counts = Counter(item.get("worksheet_title") for item in assessments if item.get("worksheet_title"))
    dimension_history: dict[tuple[str, str], list[dict]] = {}
    recommended_card_ids: list[str] = []
    requires_review_count = 0
    for item in assessments:
        scores = json_loads(item.get("scores_json"), {})
        if not isinstance(scores, dict):
            continue
        risk = scores.get("risk") or {}
        if scores.get("requires_review") or risk.get("requires_review"):
            requires_review_count += 1
        for card_id in scores.get("recommended_card_ids") or []:
            if card_id not in recommended_card_ids:
                recommended_card_ids.append(card_id)
        for dimension in scores.get("dimensions", []):
            if not isinstance(dimension, dict):
                continue
            key = dimension.get("key") or dimension.get("label")
            score = dimension.get("score")
            if not key or not isinstance(score, (int, float)):
                continue
            worksheet_id = str(item.get("worksheet_id") or "unknown")
            dimension_history.setdefault((worksheet_id, str(key)), []).append(
                {
                    "label": dimension.get("label") or key,
                    "worksheet_id": worksheet_id,
                    "worksheet_title": item.get("worksheet_title") or worksheet_id,
                    "score": float(score),
                    "created_at": item.get("created_at"),
                }
            )
    dimension_summaries = []
    for (worksheet_id, key), items in dimension_history.items():
        newest = items[0]
        oldest = items[-1]
        delta = round(newest["score"] - oldest["score"], 2) if len(items) >= 2 else None
        dimension_summaries.append(
            {
                "key": key,
                "label": newest["label"],
                "worksheet_id": worksheet_id,
                "worksheet_title": newest["worksheet_title"],
                "count": len(items),
                "latest_score": newest["score"],
                "previous_score": oldest["score"] if len(items) >= 2 else None,
                "score_delta": delta,
                "direction": _direction(delta),
            }
        )
    dimension_summaries.sort(key=lambda item: (item["worksheet_title"], item["label"]))
    return {
        "count": len(assessments),
        "worksheet_names": worksheet_counts.most_common(),
        "dimension_summaries": dimension_summaries,
        "profile_position_count": sum(1 for item in assessments if item.get("profile_cluster_id") is not None),
        "requires_review_count": requires_review_count,
        "recommended_card_ids": recommended_card_ids[:8],
    }


def _avg(values: list[int]) -> float | None:
    return round(sum(values) / len(values), 2) if values else None


def _build_thermometer_summary(thermometers: list[dict]) -> dict:
    intensity = [int(item["intensity_level"]) for item in thermometers if item.get("intensity_level") is not None]
    valence = [int(item["valence_level"]) for item in thermometers if item.get("valence_level") is not None]
    arousal = [int(item["arousal_level"]) for item in thermometers if item.get("arousal_level") is not None]
    control = [int(item["control_level"]) for item in thermometers if item.get("control_level") is not None]
    trend_text = "本周还没有情绪温度计记录。"
    intensity_trend = "none"
    if len(intensity) >= 2:
        delta = intensity[-1] - intensity[0]
        if abs(delta) <= 1:
            trend_text = "本周情绪温度整体变化不大，可以继续观察高频场景。"
            intensity_trend = "steady"
        elif delta > 1:
            trend_text = "本周后段情绪温度比前段更高，建议优先选择短暂停顿类练习。"
            intensity_trend = "up"
        else:
            trend_text = "本周后段情绪温度比前段更低，可以记录哪些练习或场景可能有帮助。"
            intensity_trend = "down"
    elif len(intensity) == 1:
        trend_text = "本周已有 1 次情绪温度记录，继续记录后才能看趋势。"
        intensity_trend = "single"
    return {
        "count": len(thermometers),
        "avg_intensity": _avg(intensity),
        "min_intensity": min(intensity) if intensity else None,
        "max_intensity": max(intensity) if intensity else None,
        "avg_valence": _avg(valence),
        "avg_arousal": _avg(arousal),
        "avg_control": _avg(control),
        "intensity_trend": intensity_trend,
        "trend_text": trend_text,
    }


def build_weekly_report(user_id: str, week_start: str | None = None) -> dict:
    start = _parse_date(week_start)
    end = start + timedelta(days=6)
    start_iso = start.isoformat()
    end_iso = end.isoformat()

    with get_connection() as conn:
        diary_rows = conn.execute(
            """
            SELECT * FROM emotion_diaries
            WHERE user_id = ? AND substr(created_at, 1, 10) BETWEEN ? AND ?
            ORDER BY created_at DESC
            """,
            (user_id, start_iso, end_iso),
        ).fetchall()
        checkin_rows = conn.execute(
            """
            SELECT * FROM checkins
            WHERE user_id = ? AND substr(created_at, 1, 10) BETWEEN ? AND ?
            ORDER BY created_at DESC
            """,
            (user_id, start_iso, end_iso),
        ).fetchall()
        feedback_rows = conn.execute(
            """
            SELECT * FROM feedback_results
            WHERE user_id = ? AND substr(created_at, 1, 10) BETWEEN ? AND ?
            ORDER BY created_at DESC
            """,
            (user_id, start_iso, end_iso),
        ).fetchall()
        profile_rows = conn.execute(
            """
            SELECT * FROM student_profiles
            WHERE user_id = ? AND substr(created_at, 1, 10) BETWEEN ? AND ?
            ORDER BY created_at DESC
            """,
            (user_id, start_iso, end_iso),
        ).fetchall()
        assessment_rows = conn.execute(
            """
            SELECT * FROM assessment_results
            WHERE user_id = ? AND substr(created_at, 1, 10) BETWEEN ? AND ?
            ORDER BY created_at DESC
            """,
            (user_id, start_iso, end_iso),
        ).fetchall()
        thermometer_rows = conn.execute(
            """
            SELECT * FROM emotion_thermometer
            WHERE user_id = ? AND substr(created_at, 1, 10) BETWEEN ? AND ?
            ORDER BY created_at ASC
            """,
            (user_id, start_iso, end_iso),
        ).fetchall()

    diaries = rows_to_dicts(diary_rows)
    checkins = rows_to_dicts(checkin_rows)
    feedback = rows_to_dicts(feedback_rows)
    profiles = rows_to_dicts(profile_rows)
    assessments = rows_to_dicts(assessment_rows)
    thermometers = rows_to_dicts(thermometer_rows)

    scene_counts = Counter(item.get("scene") for item in diaries if item.get("scene"))
    emotion_counts = Counter(item.get("parent_emotion") for item in diaries if item.get("parent_emotion"))
    profile_counts = Counter(item.get("profile_name") for item in profiles if item.get("profile_name"))
    pattern_counts = Counter()
    for item in feedback:
        for tag in json_loads(item.get("tags_json"), []):
            pattern_counts[tag] += 1

    completed_cards = [item["card_id"] for item in checkins if item.get("completed")]
    assessment_summary = _build_assessment_summary(assessments)
    thermometer_summary = _build_thermometer_summary(thermometers)
    training_effectiveness = build_training_effectiveness(user_id, "30d")
    training_effectiveness_summary = {
        "checkins": training_effectiveness.get("checkins", {}),
        "per_card_effectiveness": training_effectiveness.get("per_card_effectiveness", []),
        "next_action": training_effectiveness.get("next_action"),
    }
    review_count = sum(1 for item in profiles if item.get("requires_review"))
    high_risk_count = sum(1 for item in profiles if item.get("risk_level") == "high")
    latest_profile_round = max((int(item.get("round") or 0) for item in profiles), default=0)

    if high_risk_count > 0 or review_count > 0:
        suggestion = "下周优先安排人工关注和现实支持确认，暂不把高风险个案推入普通自动训练。"
    elif assessment_summary.get("recommended_card_ids"):
        suggestion = "下周可以从本周测评推荐的一张训练卡开始，先做一次最小练习。"
    elif completed_cards:
        suggestion = "下周继续保留一张最容易完成的训练卡，观察练习前后感受是否有轻微变化。"
    elif profiles:
        suggestion = "下周可以从画像推荐的一张训练卡开始，先完成一次 3-5 分钟小练习。"
    elif diaries:
        suggestion = "下周建议继续选择一个高频场景，优先练习一张最容易执行的训练卡。"
    else:
        suggestion = "本周记录较少。下周可以先从记录一次具体亲子互动场景开始。"

    return {
        "user_id": user_id,
        "week_start": start_iso,
        "week_end": end_iso,
        "frequent_scenes": scene_counts.most_common(5),
        "frequent_emotions": emotion_counts.most_common(5),
        "common_patterns": pattern_counts.most_common(5),
        "completed_cards": completed_cards,
        "profile_trend": {
            "profile_count": len(profiles),
            "latest_round": latest_profile_round,
            "profile_names": profile_counts.most_common(5),
            "requires_review_count": review_count,
            "high_risk_count": high_risk_count,
        },
        "assessment_trend": {
            "assessment_count": assessment_summary["count"],
            "worksheet_names": assessment_summary["worksheet_names"],
            "dimension_names": [(item["label"], item["count"]) for item in assessment_summary["dimension_summaries"]],
        },
        "assessment_summary": assessment_summary,
        "thermometer_trend": {"record_count": thermometer_summary["count"], **thermometer_summary},
        "thermometer_summary": thermometer_summary,
        "training_effectiveness_summary": training_effectiveness_summary,
        "next_week_suggestion": suggestion,
    }
