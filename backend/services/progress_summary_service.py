"""Supportive progress summary built from existing user records."""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from math import sqrt

from database import get_connection, json_loads, rows_to_dicts


RANGE_DAYS = {"7d": 7, "14d": 14, "30d": 30}
BOUNDARY_NOTICE = "阶段性反馈只用于整理近期记录和练习线索，不构成诊断、筛查、治疗评价或人格判断。"
MIN_SIGNAL_COUNT = 3
MIN_SERIES_POINTS = 3
STABLE_CV_THRESHOLD = 0.18
FLUCTUATING_CV_THRESHOLD = 0.35
STABLE_RANGE_THRESHOLD = 2
FLUCTUATING_RANGE_THRESHOLD = 5


def _date_window(range_key: str) -> tuple[str, str, int]:
    days = RANGE_DAYS.get(range_key, 7)
    now = datetime.now(timezone.utc)
    start = now - timedelta(days=days - 1)
    return start.date().isoformat(), now.date().isoformat(), days


def _parse_score_dimensions(scores_json: str | None) -> list[dict]:
    scores = json_loads(scores_json, {}) or {}
    dimensions = scores.get("dimensions") or []
    return [item for item in dimensions if isinstance(item, dict)]


def _assessment_summary(rows: list[dict]) -> dict:
    by_worksheet: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        by_worksheet[str(row.get("worksheet_id"))].append(row)

    repeated = []
    latest = rows[0] if rows else None
    for worksheet_id, items in by_worksheet.items():
        if len(items) < 2:
            continue
        newest = items[0]
        oldest = items[-1]
        delta = None
        if newest.get("total_score") is not None and oldest.get("total_score") is not None:
            delta = float(newest["total_score"]) - float(oldest["total_score"])
        repeated.append(
            {
                "worksheet_id": worksheet_id,
                "title": newest.get("worksheet_title") or worksheet_id,
                "count": len(items),
                "latest_score": newest.get("total_score"),
                "previous_score": oldest.get("total_score"),
                "score_delta": delta,
                "dimension_trends": _dimension_trends(items),
            }
        )

    return {
        "count": len(rows),
        "latest": {
            "id": latest.get("id"),
            "title": latest.get("worksheet_title"),
            "created_at": latest.get("created_at"),
        }
        if latest
        else None,
        "repeated_worksheets": repeated[:3],
    }


def _dimension_trends(items: list[dict]) -> list[dict]:
    newest_dimensions = {item.get("key"): item for item in _parse_score_dimensions(items[0].get("scores_json"))}
    oldest_dimensions = {item.get("key"): item for item in _parse_score_dimensions(items[-1].get("scores_json"))}
    trends = []
    for key, newest in newest_dimensions.items():
        oldest = oldest_dimensions.get(key)
        if not key or not oldest:
            continue
        latest_score = newest.get("score")
        previous_score = oldest.get("score")
        if not isinstance(latest_score, (int, float)) or not isinstance(previous_score, (int, float)):
            continue
        trends.append(
            {
                "key": key,
                "label": newest.get("label") or key,
                "latest_score": latest_score,
                "previous_score": previous_score,
                "score_delta": round(float(latest_score) - float(previous_score), 2),
            }
        )
    return trends[:5]


def _thermometer_summary(rows: list[dict]) -> dict:
    levels = [int(item["intensity_level"]) for item in rows if item.get("intensity_level") is not None]
    if not levels:
        return {
            "count": 0,
            "avg": None,
            "min": None,
            "max": None,
            "range": None,
            "stddev": None,
            "cv": None,
            "trend_text": "还没有情绪温度计记录。",
        }
    avg = round(sum(levels) / len(levels), 2)
    variance = sum((value - avg) ** 2 for value in levels) / len(levels)
    stddev = round(sqrt(variance), 2)
    cv = round(stddev / avg, 3) if avg else None
    level_range = max(levels) - min(levels)
    if len(levels) >= 2:
        delta = levels[-1] - levels[0]
        if abs(delta) <= 1:
            trend_text = "情绪强度近期变化不大，可以继续观察。"
        elif delta > 1:
            trend_text = "近期情绪强度有上升迹象，建议先选更短、更容易完成的小练习。"
        else:
            trend_text = "近期情绪强度有下降迹象，可以保留已经能完成的小练习。"
    else:
        trend_text = "已有一次情绪温度记录，继续记录后会更容易看出变化。"
    return {
        "count": len(levels),
        "avg": avg,
        "min": min(levels),
        "max": max(levels),
        "range": level_range,
        "stddev": stddev,
        "cv": cv,
        "trend_text": trend_text,
    }


def _checkin_summary(rows: list[dict]) -> dict:
    completed = [item for item in rows if item.get("completed")]
    card_counts = Counter(item.get("card_id") for item in completed if item.get("card_id"))
    emotion_pairs = [
        (item.get("emotion_before"), item.get("emotion_after"))
        for item in completed
        if item.get("emotion_before") is not None and item.get("emotion_after") is not None
    ]
    average_delta = None
    if emotion_pairs:
        deltas = [int(after) - int(before) for before, after in emotion_pairs]
        average_delta = round(sum(deltas) / len(deltas), 2)
    helpfulness_counts = Counter(item.get("helpfulness_rating") for item in rows if item.get("helpfulness_rating"))
    skip_reasons = [item.get("skip_reason") for item in rows if item.get("skip_reason")]
    if not rows:
        effectiveness_text = "还没有训练打卡记录。"
    elif helpfulness_counts.get("helpful", 0) >= 1:
        effectiveness_text = "已有训练被标记为有帮助，可以优先保留这些更容易执行的小动作。"
    elif helpfulness_counts.get("not_helpful_yet", 0) >= 1:
        effectiveness_text = "有训练暂时没有帮助，建议降低难度或换一张更短的训练卡。"
    else:
        effectiveness_text = "已有训练记录，但帮助程度还需要继续观察。"
    return {
        "count": len(rows),
        "completed_count": len(completed),
        "top_cards": card_counts.most_common(3),
        "average_emotion_delta": average_delta,
        "helpfulness_counts": helpfulness_counts.most_common(),
        "skip_reasons": skip_reasons[:3],
        "effectiveness_text": effectiveness_text,
    }


def _diary_summary(rows: list[dict]) -> dict:
    scenes = Counter(item.get("scene") for item in rows if item.get("scene"))
    emotions = Counter(item.get("parent_emotion") for item in rows if item.get("parent_emotion"))
    return {
        "count": len(rows),
        "frequent_scenes": scenes.most_common(3),
        "frequent_emotions": emotions.most_common(3),
    }


def _assessment_delta_signal(assessment_summary: dict) -> float | None:
    deltas: list[float] = []
    for item in assessment_summary.get("repeated_worksheets") or []:
        if isinstance(item.get("score_delta"), (int, float)):
            deltas.append(abs(float(item["score_delta"])))
        for dimension in item.get("dimension_trends") or []:
            if isinstance(dimension.get("score_delta"), (int, float)):
                deltas.append(abs(float(dimension["score_delta"])))
    if not deltas:
        return None
    return max(deltas)


def _status(assessment: dict, checkin: dict, thermometer: dict) -> str:
    total = int(assessment.get("count") or 0) + int(checkin.get("completed_count") or 0) + int(thermometer.get("count") or 0)
    if total < MIN_SIGNAL_COUNT:
        return "insufficient"

    thermometer_count = int(thermometer.get("count") or 0)
    thermometer_cv = thermometer.get("cv")
    thermometer_range = thermometer.get("range")
    assessment_delta = _assessment_delta_signal(assessment)
    has_repeated_assessment = bool(assessment.get("repeated_worksheets"))

    if thermometer_count < MIN_SERIES_POINTS and not has_repeated_assessment:
        return "low_confidence"

    is_fluctuating_temperature = (
        thermometer_count >= MIN_SERIES_POINTS
        and (
            (isinstance(thermometer_cv, (int, float)) and thermometer_cv >= FLUCTUATING_CV_THRESHOLD)
            or (isinstance(thermometer_range, (int, float)) and thermometer_range >= FLUCTUATING_RANGE_THRESHOLD)
        )
    )
    is_large_assessment_shift = isinstance(assessment_delta, (int, float)) and assessment_delta >= 3
    if is_fluctuating_temperature or is_large_assessment_shift:
        return "fluctuating"

    is_stable_temperature = (
        thermometer_count >= MIN_SERIES_POINTS
        and isinstance(thermometer_cv, (int, float))
        and thermometer_cv <= STABLE_CV_THRESHOLD
        and isinstance(thermometer_range, (int, float))
        and thermometer_range <= STABLE_RANGE_THRESHOLD
    )
    is_small_assessment_shift = assessment_delta is None or assessment_delta <= 1
    if is_stable_temperature and is_small_assessment_shift and total >= 4:
        return "stable"

    return "converging"


def _summary_text(status: str, diary_summary: dict, assessment_summary: dict) -> str:
    if status == "insufficient":
        return "记录还不够，先继续完成测评和练习。"
    if status == "low_confidence":
        return "已有一些记录，但来源还不够稳定，暂时只把它当作观察线索。"
    if status == "fluctuating":
        return "近期结果仍在波动中，暂不做明确归纳。"
    if status == "stable":
        return "近期记录的波动较小，可以继续保留已经容易完成的小练习。"
    scene = diary_summary.get("frequent_scenes", [[None]])[0][0] if diary_summary.get("frequent_scenes") else None
    repeated = assessment_summary.get("repeated_worksheets") or []
    if repeated:
        return f"近期已有重复测评记录，可以先观察“{repeated[0]['title']}”的变化。"
    if scene:
        return f"近期记录显示“{scene}”出现较多，可以继续从这个场景选择一张容易完成的训练卡。"
    return "近期记录显示某些模式较稳定，可继续观察。"


def build_progress_summary(user_id: str, range_key: str = "7d") -> dict:
    start_iso, end_iso, days = _date_window(range_key)
    with get_connection() as conn:
        assessment_rows = conn.execute(
            """
            SELECT id, worksheet_id, worksheet_title, scores_json, total_score,
                   profile_model_id, profile_cluster_id, profile_confidence, created_at
            FROM assessment_results
            WHERE user_id = ? AND substr(created_at, 1, 10) BETWEEN ? AND ?
            ORDER BY created_at DESC
            """,
            (user_id, start_iso, end_iso),
        ).fetchall()
        checkin_rows = conn.execute(
            """
            SELECT id, card_id, completed, emotion_before, emotion_after,
                   reflection, helpfulness_rating, skip_reason, created_at
            FROM checkins
            WHERE user_id = ? AND substr(created_at, 1, 10) BETWEEN ? AND ?
            ORDER BY created_at DESC
            """,
            (user_id, start_iso, end_iso),
        ).fetchall()
        thermometer_rows = conn.execute(
            """
            SELECT id, intensity_level, brief_text, created_at
            FROM emotion_thermometer
            WHERE user_id = ? AND substr(created_at, 1, 10) BETWEEN ? AND ?
            ORDER BY created_at ASC
            """,
            (user_id, start_iso, end_iso),
        ).fetchall()
        diary_rows = conn.execute(
            """
            SELECT id, scene, parent_emotion, parent_emotion_intensity, created_at
            FROM emotion_diaries
            WHERE user_id = ? AND substr(created_at, 1, 10) BETWEEN ? AND ?
            ORDER BY created_at DESC
            """,
            (user_id, start_iso, end_iso),
        ).fetchall()

    assessments = rows_to_dicts(assessment_rows)
    checkins = rows_to_dicts(checkin_rows)
    thermometers = rows_to_dicts(thermometer_rows)
    diaries = rows_to_dicts(diary_rows)
    assessment = _assessment_summary(assessments)
    thermometer = _thermometer_summary(thermometers)
    checkin = _checkin_summary(checkins)
    diary = _diary_summary(diaries)
    status = _status(assessment, checkin, thermometer)

    next_action = "先完成一次测一测或一张训练卡，阶段性反馈会随着记录逐步清晰。"
    if status != "insufficient":
        next_action = "下次可以继续选择一张最容易完成的训练卡，并记录练习前后的情绪变化。"
    if diary.get("frequent_scenes"):
        next_action = f"下次可以围绕“{diary['frequent_scenes'][0][0]}”场景，先选一张最短的练习卡。"

    return {
        "user_id": user_id,
        "range": range_key,
        "days": days,
        "start_date": start_iso,
        "end_date": end_iso,
        "stability_status": status,
        "summary_text": _summary_text(status, diary, assessment),
        "assessment": assessment,
        "thermometer": thermometer,
        "checkins": checkin,
        "diaries": diary,
        "next_action": next_action,
        "boundary_notice": BOUNDARY_NOTICE,
    }


def build_training_effectiveness(user_id: str, range_key: str = "30d") -> dict:
    start_iso, end_iso, days = _date_window(range_key)
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT c.id, c.card_id, c.completed, c.emotion_before, c.emotion_after,
                   c.reflection, c.helpfulness_rating, c.skip_reason,
                   c.before_thermometer_id, c.after_thermometer_id, c.created_at,
                   before_t.intensity_level AS before_intensity_level,
                   after_t.intensity_level AS after_intensity_level
            FROM checkins c
            LEFT JOIN emotion_thermometer before_t
              ON before_t.id = c.before_thermometer_id AND before_t.user_id = c.user_id
            LEFT JOIN emotion_thermometer after_t
              ON after_t.id = c.after_thermometer_id AND after_t.user_id = c.user_id
            WHERE c.user_id = ? AND substr(c.created_at, 1, 10) BETWEEN ? AND ?
            ORDER BY c.created_at DESC
            """,
            (user_id, start_iso, end_iso),
        ).fetchall()
    checkins = rows_to_dicts(rows)
    summary = _checkin_summary(checkins)
    per_card = _training_effectiveness_by_card(checkins)
    next_action = "先完成一张容易执行的训练卡，再记录一点练习后感受。"
    if per_card:
        best = per_card[0]
        delta = best.get("average_intensity_delta")
        if isinstance(delta, (int, float)) and delta < 0:
            next_action = f"可以优先复盘“{best['card_id']}”，近期练习后强度平均下降 {abs(delta)} 分；这只是个人记录线索。"
        else:
            next_action = "优先复盘最近完成过的训练卡，观察哪类小练习更容易坚持。"
    elif summary.get("completed_count"):
        next_action = "优先复盘最近完成过的训练卡，观察哪类小练习更容易坚持。"
    return {
        "user_id": user_id,
        "range": range_key,
        "days": days,
        "start_date": start_iso,
        "end_date": end_iso,
        "training_effectiveness": summary,
        "per_card_effectiveness": per_card,
        "checkins": summary,
        "next_action": next_action,
        "boundary_notice": BOUNDARY_NOTICE,
    }


def _training_effectiveness_by_card(rows: list[dict]) -> list[dict]:
    buckets: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        card_id = row.get("card_id")
        if not card_id:
            continue
        before = row.get("before_intensity_level")
        after = row.get("after_intensity_level")
        source = "thermometer"
        if before is None or after is None:
            before = row.get("emotion_before")
            after = row.get("emotion_after")
            source = "checkin_slider"
        if before is None or after is None:
            continue
        buckets[str(card_id)].append(
            {
                "before": int(before),
                "after": int(after),
                "delta": int(after) - int(before),
                "helpfulness_rating": row.get("helpfulness_rating"),
                "source": source,
            }
        )
    summaries = []
    for card_id, items in buckets.items():
        deltas = [item["delta"] for item in items]
        helpful_count = sum(1 for item in items if item.get("helpfulness_rating") == "helpful")
        thermometer_count = sum(1 for item in items if item.get("source") == "thermometer")
        average_delta = round(sum(deltas) / len(deltas), 2)
        summaries.append(
            {
                "card_id": card_id,
                "sample_count": len(items),
                "thermometer_pair_count": thermometer_count,
                "average_intensity_delta": average_delta,
                "helpful_rate": round(helpful_count / len(items), 2) if items else 0,
                "sample_note": "样本偏小，仅供参考。" if len(items) < 3 else "来自近期多次练习记录，仅作个人复盘线索。",
            }
        )
    return sorted(summaries, key=lambda item: (item["average_intensity_delta"], -item["sample_count"]))[:8]


def build_profile_convergence(user_id: str, worksheet_id: str | None = None) -> dict:
    params: list[str] = [user_id]
    where = "WHERE user_id = ?"
    if worksheet_id:
        where += " AND worksheet_id = ?"
        params.append(worksheet_id)
    with get_connection() as conn:
        rows = conn.execute(
            f"""
            SELECT id, worksheet_id, worksheet_title, profile_cluster_id,
                   profile_confidence, total_score, created_at
            FROM assessment_results
            {where}
            ORDER BY created_at DESC
            LIMIT 10
            """,
            tuple(params),
        ).fetchall()
    items = rows_to_dicts(rows)
    clusters = [item.get("profile_cluster_id") for item in items if item.get("profile_cluster_id") is not None]
    cluster_counts = Counter(clusters).most_common()
    status = "insufficient"
    if len(items) >= 3 and cluster_counts:
        status = "stable" if cluster_counts[0][1] >= 2 else "fluctuating"
    elif len(items) >= 2:
        status = "converging"
    return {
        "user_id": user_id,
        "worksheet_id": worksheet_id,
        "record_count": len(items),
        "stability_status": status,
        "cluster_counts": cluster_counts,
        "latest": items[0] if items else None,
        "boundary_notice": BOUNDARY_NOTICE,
    }
