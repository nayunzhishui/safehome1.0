"""Weekly report endpoints."""

from flask import Blueprint, request

from database import get_connection, json_dumps, new_id, now_iso
from routes.auth_utils import AuthError, auth_error_response, resolve_actor_user_id
from routes.utils import ok
from services.report_service import build_weekly_report

bp = Blueprint("reports", __name__, url_prefix="/api")


@bp.get("/weekly-report")
def weekly_report():
    try:
        user_id = resolve_actor_user_id(request.args.get("user_id"))
    except AuthError as exc:
        return auth_error_response(exc)
    week_start = request.args.get("week_start")
    report = build_weekly_report(user_id=user_id, week_start=week_start)
    report_id = new_id("weekly")

    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO weekly_reports (
                id, user_id, week_start, week_end, frequent_scenes_json,
                frequent_emotions_json, common_patterns_json,
                completed_cards_json, assessment_summary_json,
                thermometer_summary_json, training_effectiveness_summary_json,
                next_week_suggestion, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                json_dumps(report.get("assessment_summary", {})),
                json_dumps(report.get("thermometer_summary", {})),
                json_dumps(report.get("training_effectiveness_summary", {})),
                report["next_week_suggestion"],
                now_iso(),
            ),
        )
        conn.commit()

    return ok({"id": report_id, **report})
