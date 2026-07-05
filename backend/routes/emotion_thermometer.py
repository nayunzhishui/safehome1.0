"""Emotion thermometer endpoints for lightweight daily mood tracking."""

import re

from flask import Blueprint, request

from database import ensure_user, get_connection, new_id, now_iso, row_to_dict, rows_to_dicts
from routes.utils import fail, ok, require_user_id, resolve_user_id_for_query


bp = Blueprint("emotion_thermometer", __name__, url_prefix="/api/emotion-thermometer")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _today_key() -> str:
    return now_iso()[:10]


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
    if not levels:
        return {"count": 0, "min": None, "max": None, "avg": None}
    return {
        "count": len(levels),
        "min": min(levels),
        "max": max(levels),
        "avg": round(sum(levels) / len(levels), 2),
    }


@bp.post("")
def create_emotion_thermometer_record():
    payload = request.get_json(silent=True) or {}
    try:
        user_id = require_user_id(payload)
    except ValueError as exc:
        return fail("missing_user_id", str(exc), status=400)

    level = _normalize_level(payload.get("intensity_level"))
    if level is None:
        return fail("invalid_intensity_level", "情绪强度必须是 1 到 10 之间的整数", status=400)

    brief_text = str(payload.get("brief_text") or "").strip()
    if len(brief_text) > 200:
        return fail("brief_text_too_long", "简短备注不能超过 200 字", status=400)

    created_at = str(payload.get("created_at") or now_iso())
    record_id = new_id("thermo")
    with get_connection() as conn:
        ensure_user(conn, user_id, payload.get("nickname"))
        conn.execute(
            """
            INSERT INTO emotion_thermometer (
                id, user_id, intensity_level, brief_text, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (record_id, user_id, level, brief_text, created_at, now_iso()),
        )
        row = conn.execute("SELECT * FROM emotion_thermometer WHERE id = ?", (record_id,)).fetchone()
    return ok(row_to_dict(row), status=201)


@bp.get("/day")
def get_emotion_thermometer_day():
    try:
        user_id = resolve_user_id_for_query(request.args.get("user_id"))
    except ValueError as exc:
        return fail("missing_user_id", str(exc), status=400)

    day = request.args.get("date") or _today_key()
    if not DATE_RE.match(day):
        return fail("invalid_date", "date 必须使用 YYYY-MM-DD 格式", status=400)

    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT id, user_id, intensity_level, brief_text, created_at, updated_at
            FROM emotion_thermometer
            WHERE user_id = ? AND substr(created_at, 1, 10) = ?
            ORDER BY created_at ASC
            """,
            (user_id, day),
        ).fetchall()

    items = rows_to_dicts(rows)
    return ok(
        {
            "user_id": user_id,
            "date": day,
            "items": items,
            "summary": _summary(items),
            "boundary_notice": "情绪温度计只用于自我观察和练习提示，不构成诊断或筛查。",
        }
    )
