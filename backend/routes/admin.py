"""Admin export endpoints for MVP data review."""

import csv
import hashlib
import json
from io import StringIO

from flask import Blueprint, Response, current_app, request

from database import get_connection, json_dumps, new_id, now_iso
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
            dimensions = json.loads(item.get("dimensions_json") or "[]")
        except json.JSONDecodeError:
            dimensions = []
        try:
            recommended_card_ids = json.loads(item.get("recommended_task_ids_json") or "[]")
        except json.JSONDecodeError:
            recommended_card_ids = []
        dimension_summary = "；".join(
            f"{dimension.get('label')}: {dimension.get('level')}"
            for dimension in dimensions
            if isinstance(dimension, dict)
        )
        export_rows.append(
            {
                "id": item.get("id"),
                "anonymous_id": item.get("anonymous_id") or _anonymous_id(item.get("user_id") or ""),
                "assessment_result_id": item.get("assessment_result_id"),
                "profile_code": item.get("profile_code"),
                "profile_name": item.get("profile_name"),
                "confidence": item.get("confidence"),
                "risk_level": item.get("risk_level"),
                "requires_review": item.get("requires_review"),
                "dimension_summary": dimension_summary,
                "recommended_card_ids": ",".join(recommended_card_ids),
                "rules_version": item.get("rules_version"),
                "export_allowed": item.get("export_allowed"),
                "data_quality": item.get("data_quality"),
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
    table = "student_profiles" if export_type == "profile" else EXPORT_TABLES.get(export_type)
    if table is None:
        return fail("invalid_export_type", "支持的 type：goals, diaries, feedback, checkins, assessments, profile, reports, supervision, cards")

    user_id = request.args.get("user_id")
    with get_connection() as conn:
        if export_type == "profile":
            if user_id:
                rows = conn.execute(
                    """
                    SELECT * FROM student_profiles
                    WHERE user_id = ? AND export_allowed = 1
                    ORDER BY created_at DESC
                    """,
                    (user_id,),
                ).fetchall()
            else:
                rows = conn.execute(
                    """
                    SELECT * FROM student_profiles
                    WHERE export_allowed = 1
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
        conn.execute(
            """
            INSERT INTO audit_logs (id, actor_id, action, target_type, target_id, metadata_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                new_id("audit"),
                "admin-token",
                f"export_{export_type}",
                "export",
                export_type,
                json_dumps({"type": export_type, "user_id_filter": user_id, "row_count": len(rows)}),
                now_iso(),
            ),
        )
        conn.commit()

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
