"""Admin export endpoints for MVP data review."""

import csv
from io import StringIO

from flask import Blueprint, Response, request

from database import get_connection
from routes.utils import fail

bp = Blueprint("admin", __name__, url_prefix="/api/admin")

EXPORT_TABLES = {
    "goals": "goals",
    "diaries": "emotion_diaries",
    "feedback": "feedback_results",
    "checkins": "checkins",
    "reports": "weekly_reports",
    "supervision": "supervision_requests",
    "cards": "training_cards",
}


@bp.get("/export")
def export_csv():
    export_type = request.args.get("type", "diaries")
    table = EXPORT_TABLES.get(export_type)
    if table is None:
        return fail("invalid_export_type", "支持的 type：goals, diaries, feedback, checkins, reports, supervision, cards")

    user_id = request.args.get("user_id")
    with get_connection() as conn:
        if user_id and table != "training_cards":
            rows = conn.execute(
                f"SELECT * FROM {table} WHERE user_id = ? ORDER BY created_at DESC",
                (user_id,),
            ).fetchall()
        else:
            rows = conn.execute(f"SELECT * FROM {table} ORDER BY created_at DESC").fetchall()

    output = StringIO()
    if rows:
        writer = csv.DictWriter(output, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows([dict(row) for row in rows])
    else:
        output.write("empty\n")

    csv_text = "\ufeff" + output.getvalue()
    return Response(
        csv_text,
        mimetype="text/csv; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename=safehome_{export_type}.csv"},
    )
