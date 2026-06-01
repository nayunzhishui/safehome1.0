"""Admin export endpoints for MVP data review."""

import csv
import hashlib
import json
from io import StringIO

from flask import Blueprint, Response, current_app, request

from database import get_connection
from routes.utils import fail

bp = Blueprint("admin", __name__, url_prefix="/api/admin")

EXPORT_TABLES = {
    "goals": "goals",
    "diaries": "emotion_diaries",
    "feedback": "feedback_results",
    "checkins": "checkins",
    "assessments": "assessment_results",
    "reports": "weekly_reports",
    "supervision": "supervision_requests",
    "cards": "training_cards",
}


def _anonymous_id(user_id: str) -> str:
    digest = hashlib.sha256(user_id.encode("utf-8")).hexdigest()[:12]
    return f"anon_{digest}"


def _profile_export_rows(rows) -> list[dict]:
    export_rows = []
    for row in rows:
        item = dict(row)
        try:
            scores = json.loads(item.get("scores_json") or "{}")
        except json.JSONDecodeError:
            scores = {}
        dimensions = scores.get("dimensions") or []
        dimension_summary = "；".join(
            f"{dimension.get('label')}: {dimension.get('level')}"
            for dimension in dimensions
            if isinstance(dimension, dict)
        )
        export_rows.append(
            {
                "id": item.get("id"),
                "anonymous_id": _anonymous_id(item.get("user_id") or ""),
                "worksheet_id": item.get("worksheet_id"),
                "profile_code": scores.get("profile_code"),
                "profile_name": scores.get("profile_name"),
                "confidence": scores.get("confidence"),
                "risk_level": scores.get("risk_level"),
                "requires_review": scores.get("requires_review"),
                "allow_auto_feedback": scores.get("allow_auto_feedback"),
                "dimension_summary": dimension_summary,
                "recommended_card_ids": ",".join(scores.get("recommended_card_ids") or []),
                "model_version": scores.get("model_version"),
                "rules_version": scores.get("rules_version"),
                "created_at": item.get("created_at"),
            }
        )
    return export_rows


@bp.get("/export")
def export_csv():
    admin_token = current_app.config.get("ADMIN_EXPORT_TOKEN")
    request_token = request.headers.get("X-Admin-Token", "")
    if not admin_token or request_token != admin_token:
        return fail("unauthorized", "导出数据需要后台导出令牌", status=401)

    export_type = request.args.get("type", "diaries")
    table = "assessment_results" if export_type == "profile" else EXPORT_TABLES.get(export_type)
    if table is None:
        return fail("invalid_export_type", "支持的 type：goals, diaries, feedback, checkins, assessments, profile, reports, supervision, cards")

    user_id = request.args.get("user_id")
    with get_connection() as conn:
        if export_type == "profile":
            if user_id:
                rows = conn.execute(
                    """
                    SELECT * FROM assessment_results
                    WHERE user_id = ? AND (worksheet_id = 'student_profile_v1' OR category = '学生画像')
                    ORDER BY created_at DESC
                    """,
                    (user_id,),
                ).fetchall()
            else:
                rows = conn.execute(
                    """
                    SELECT * FROM assessment_results
                    WHERE worksheet_id = 'student_profile_v1' OR category = '学生画像'
                    ORDER BY created_at DESC
                    """
                ).fetchall()
        elif user_id and table != "training_cards":
            rows = conn.execute(
                f"SELECT * FROM {table} WHERE user_id = ? ORDER BY created_at DESC",
                (user_id,),
            ).fetchall()
        else:
            rows = conn.execute(f"SELECT * FROM {table} ORDER BY created_at DESC").fetchall()

    output = StringIO()
    if export_type == "profile":
        rows = _profile_export_rows(rows)
    if rows:
        first_row = rows[0]
        writer = csv.DictWriter(output, fieldnames=first_row.keys())
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
