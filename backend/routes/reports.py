"""Weekly report endpoints."""

from flask import Blueprint, request

from database import get_connection, json_dumps, new_id, now_iso
from routes.utils import fail, ok, resolve_user_id_for_query
from services.report_service import build_weekly_report

bp = Blueprint("reports", __name__, url_prefix="/api")


@bp.get("/weekly-report")
def weekly_report():
    try:
        user_id = resolve_user_id_for_query(request.args.get("user_id"))
    except ValueError as exc:
        return fail("validation_error", str(exc), status=400)
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
