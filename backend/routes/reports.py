"""Weekly report endpoints."""

from flask import Blueprint, request

from database import get_connection, json_dumps, new_id, now_iso
from routes.utils import ok
from services.report_service import build_weekly_report

bp = Blueprint("reports", __name__, url_prefix="/api")


@bp.get("/weekly-report")
def weekly_report():
    user_id = request.args.get("user_id") or "demo-parent"
    week_start = request.args.get("week_start")
    report = build_weekly_report(user_id=user_id, week_start=week_start)
    report_id = new_id("weekly")

    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO weekly_reports (
                id, user_id, week_start, week_end, frequent_scenes_json,
                frequent_emotions_json, common_patterns_json,
                completed_cards_json, next_week_suggestion, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                report_id,
                user_id,
                report["week_start"],
                report["week_end"],
                json_dumps(report["frequent_scenes"]),
                json_dumps(report["frequent_emotions"]),
                json_dumps(report["common_patterns"]),
                json_dumps(report["completed_cards"]),
                report["next_week_suggestion"],
                now_iso(),
            ),
        )
        conn.commit()

    return ok({"id": report_id, **report})
