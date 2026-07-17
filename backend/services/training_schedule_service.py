"""Shared schedule rules for training plans and notification jobs."""

from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo


CADENCE_LABELS = {
    "daily": "每日",
    "every_other_day": "隔日",
    "three_per_week": "每周3次",
    "weekly": "每周1次",
}


def current_local_day() -> date:
    return datetime.now(ZoneInfo("Asia/Shanghai")).date()


def parse_day(value: str | None) -> date | None:
    text = str(value or "").strip()
    if "T" in text or " " in text:
        try:
            parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
            if parsed.tzinfo is not None:
                parsed = parsed.astimezone(ZoneInfo("Asia/Shanghai"))
            return parsed.date()
        except (TypeError, ValueError):
            pass
    try:
        return datetime.strptime(text[:10], "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return None


def next_three_per_week(base: date) -> date:
    for day_offset in range(1, 8):
        candidate = base + timedelta(days=day_offset)
        if candidate.weekday() in {0, 2, 4}:
            return candidate
    return base + timedelta(days=2)


def assignment_schedule(
    assignment: dict | None,
    latest_completed_at: str | None = None,
    *,
    today: date | None = None,
) -> dict | None:
    if not assignment:
        return None
    current_day = today or current_local_day()
    start_day = parse_day(assignment.get("start_date")) or current_day
    completed_day = parse_day(latest_completed_at)
    cadence = str(assignment.get("cadence") or "daily")
    status = str(assignment.get("status") or "active")
    if completed_day and completed_day >= start_day:
        if cadence == "every_other_day":
            next_day = completed_day + timedelta(days=2)
        elif cadence == "weekly":
            next_day = completed_day + timedelta(days=7)
        elif cadence == "three_per_week":
            next_day = next_three_per_week(completed_day)
        else:
            next_day = completed_day + timedelta(days=1)
    else:
        next_day = start_day
        if cadence == "three_per_week" and next_day.weekday() not in {0, 2, 4}:
            next_day = next_three_per_week(next_day - timedelta(days=1))
    is_due = status == "active" and current_day >= next_day
    if status == "paused":
        reason = "计划已暂缓，恢复后再安排下一次练习。"
    elif status == "completed":
        reason = "这一阶段已完成，可以回看记录或重新设置节奏。"
    elif is_due:
        reason = "今天已到练习时间，先选一张最容易完成的卡。"
    else:
        reason = f"下一次练习安排在 {next_day.isoformat()}。"
    return {
        **assignment,
        "cadence_label": CADENCE_LABELS.get(cadence, "自定节奏"),
        "is_due_today": is_due,
        "next_practice_date": next_day.isoformat() if status == "active" else None,
        "due_reason": reason,
    }
