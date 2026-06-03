"""Weekly report service for the MVP backend."""

from collections import Counter
from datetime import date, datetime, timedelta

from database import get_connection, json_loads, rows_to_dicts


def _parse_date(value: str | None) -> date:
    if not value:
        today = date.today()
        return today - timedelta(days=today.weekday())
    return datetime.fromisoformat(value).date()


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

    diaries = rows_to_dicts(diary_rows)
    checkins = rows_to_dicts(checkin_rows)
    feedback = rows_to_dicts(feedback_rows)
    profiles = rows_to_dicts(profile_rows)

    scene_counts = Counter(item.get("scene") for item in diaries if item.get("scene"))
    emotion_counts = Counter(item.get("parent_emotion") for item in diaries if item.get("parent_emotion"))
    profile_counts = Counter(item.get("profile_name") for item in profiles if item.get("profile_name"))
    pattern_counts = Counter()
    for item in feedback:
        for tag in json_loads(item.get("tags_json"), []):
            pattern_counts[tag] += 1

    completed_cards = [item["card_id"] for item in checkins if item.get("completed")]
    review_count = sum(1 for item in profiles if item.get("requires_review"))
    high_risk_count = sum(1 for item in profiles if item.get("risk_level") == "high")
    latest_profile_round = max((int(item.get("round") or 0) for item in profiles), default=0)

    if high_risk_count > 0 or review_count > 0:
        suggestion = "下周优先安排人工关注和现实支持确认，暂不把高风险个案推入普通自动训练。"
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
        "next_week_suggestion": suggestion,
    }
