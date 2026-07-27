"""Emotion thermometer endpoints for lightweight daily mood tracking."""

import re
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from flask import Blueprint, request

from database import ensure_user, get_connection, new_id, now_iso, row_to_dict, rows_to_dicts
from routes.auth_utils import AuthError, auth_error_response, resolve_actor_user_id
from routes.utils import fail, ok


bp = Blueprint("emotion_thermometer", __name__, url_prefix="/api/emotion-thermometer")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
LOCAL_TZ = ZoneInfo("Asia/Shanghai")


def _today_key() -> str:
    return datetime.now(LOCAL_TZ).date().isoformat()


def _local_datetime(value: str) -> datetime:
    normalized = str(value or "").strip().replace("Z", "+00:00")
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=LOCAL_TZ)
    return parsed.astimezone(LOCAL_TZ)


def _local_day_key(value: str) -> str:
    return _local_datetime(value).date().isoformat()


def _normalize_level(value) -> int | None:
    try:
        level = int(value)
    except (TypeError, ValueError):
        return None
    if level < 1 or level > 10:
        return None
    return level


def _summary(items: list[dict]) -> dict:
    levels = [int(item["intensity_level"]) for item in items]
    valence_levels = [int(item["valence_level"]) for item in items if item.get("valence_level") is not None]
    arousal_levels = [int(item["arousal_level"]) for item in items if item.get("arousal_level") is not None]
    control_levels = [int(item["control_level"]) for item in items if item.get("control_level") is not None]
    if not levels:
        return {
            "count": 0,
            "min": None,
            "max": None,
            "avg": None,
            "valence_avg": None,
            "arousal_avg": None,
            "control_avg": None,
        }
    def avg(values: list[int]) -> float | None:
        return round(sum(values) / len(values), 2) if values else None

    return {
        "count": len(levels),
        "min": min(levels),
        "max": max(levels),
        "avg": round(sum(levels) / len(levels), 2),
        "valence_avg": avg(valence_levels),
        "arousal_avg": avg(arousal_levels),
        "control_avg": avg(control_levels),
    }


def _build_receipt(conn, user_id: str, record: dict) -> dict:
    """生成非评判、描述性的记录回执；不推断好坏或疗效。"""
    record_day = _local_datetime(str(record["created_at"])).date()
    rows = conn.execute(
        """
        SELECT intensity_level, control_level, created_at
        FROM emotion_thermometer
        WHERE user_id = ?
        ORDER BY created_at ASC
        """,
        (user_id,),
    ).fetchall()
    today_rows = [row for row in rows if _local_datetime(str(row["created_at"])).date() == record_day]
    previous_week_rows = [
        row
        for row in rows
        if record_day - timedelta(days=7)
        <= _local_datetime(str(row["created_at"])).date()
        < record_day
    ]

    today_levels = [int(row["intensity_level"]) for row in today_rows]
    week_levels = [int(row["intensity_level"]) for row in previous_week_rows]
    today_average = round(sum(today_levels) / len(today_levels), 1)
    week_average = round(sum(week_levels) / len(week_levels), 1) if week_levels else None
    sequence = len(today_rows)
    level = int(record["intensity_level"])

    messages = [f"这是你今天的第 {sequence} 次记录。"]
    if sequence > 1:
        messages.append(f"今天记录的强度平均在 {today_average} 左右。")
    elif week_average is None:
        messages.append("继续记录几次后，可以在今日曲线里看看自己的变化。")
    if week_average is not None:
        difference = round(level - week_average, 1)
        if abs(difference) < 0.5:
            messages.append(f"这次和近七天平均值（约 {week_average}）比较接近。")
        elif difference > 0:
            messages.append(f"这次比近七天平均值（约 {week_average}）高一些；单次记录不代表趋势。")
        else:
            messages.append(f"这次比近七天平均值（约 {week_average}）低一些；单次记录不代表趋势。")

    return {
        "sequence_today": sequence,
        "local_date": record_day.isoformat(),
        "today_intensity_avg": today_average,
        "recent_week_intensity_avg": week_average,
        "messages": messages,
        "practice_available": True,
        "boundary_notice": "这是对你所记录内容的描述性回顾，不评价好坏，也不构成诊断或疗效判断。",
    }


@bp.post("")
def create_emotion_thermometer_record():
    payload = request.get_json(silent=True) or {}
    try:
        user_id = resolve_actor_user_id(payload=payload)
    except AuthError as exc:
        return auth_error_response(exc)

    level = _normalize_level(payload.get("intensity_level"))
    if level is None:
        return fail("invalid_intensity_level", "情绪强度必须是 1 到 10 之间的整数", status=400)
    valence_level = _normalize_level(payload.get("valence_level")) if payload.get("valence_level") is not None else None
    arousal_level = _normalize_level(payload.get("arousal_level")) if payload.get("arousal_level") is not None else None
    control_level = _normalize_level(payload.get("control_level")) if payload.get("control_level") is not None else None
    if payload.get("valence_level") is not None and valence_level is None:
        return fail("invalid_valence_level", "情绪愉悦度必须是 1 到 10 之间的整数", status=400)
    if payload.get("arousal_level") is not None and arousal_level is None:
        return fail("invalid_arousal_level", "身体唤起程度必须是 1 到 10 之间的整数", status=400)
    if payload.get("control_level") is not None and control_level is None:
        return fail("invalid_control_level", "可控感必须是 1 到 10 之间的整数", status=400)

    emotion_label = str(payload.get("emotion_label") or "").strip()
    if len(emotion_label) > 40:
        return fail("emotion_label_too_long", "情绪名称不能超过 40 字", status=400)

    brief_text = str(payload.get("brief_text") or "").strip()
    if len(brief_text) > 200:
        return fail("brief_text_too_long", "简短备注不能超过 200 字", status=400)

    created_at = str(payload.get("created_at") or now_iso())
    try:
        _local_datetime(created_at)
    except (TypeError, ValueError):
        return fail("invalid_created_at", "created_at 必须是有效的ISO时间", status=400)
    record_id = new_id("thermo")
    with get_connection() as conn:
        ensure_user(conn, user_id, payload.get("nickname"))
        conn.execute(
            """
            INSERT INTO emotion_thermometer (
                id, user_id, intensity_level, valence_level, arousal_level,
                control_level, emotion_label, brief_text, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record_id,
                user_id,
                level,
                valence_level,
                arousal_level,
                control_level,
                emotion_label,
                brief_text,
                created_at,
                now_iso(),
            ),
        )
        row = conn.execute("SELECT * FROM emotion_thermometer WHERE id = ?", (record_id,)).fetchone()
        record = row_to_dict(row)
        record["receipt"] = _build_receipt(conn, user_id, record)
    return ok(record, status=201)


@bp.get("/day")
def get_emotion_thermometer_day():
    try:
        user_id = resolve_actor_user_id(request.args.get("user_id"))
    except AuthError as exc:
        return auth_error_response(exc)

    day = request.args.get("date") or _today_key()
    if not DATE_RE.match(day):
        return fail("invalid_date", "date 必须使用 YYYY-MM-DD 格式", status=400)

    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT id, user_id, intensity_level, valence_level, arousal_level,
                   control_level, emotion_label, brief_text, created_at, updated_at
            FROM emotion_thermometer
            WHERE user_id = ?
            ORDER BY created_at ASC
            """,
            (user_id,),
        ).fetchall()

    items = [
        item
        for item in rows_to_dicts(rows)
        if _local_day_key(str(item["created_at"])) == day
    ]
    return ok(
        {
            "user_id": user_id,
            "date": day,
            "items": items,
            "summary": _summary(items),
            "boundary_notice": "情绪温度计只用于自我观察和练习提示，不构成诊断或筛查。",
        }
    )
