"""Admin export endpoints for MVP data review."""

import csv
import hashlib
import json
from io import StringIO

from flask import Blueprint, Response, current_app, request

from database import get_connection, write_audit_log
from routes.utils import fail, parse_bool
from services.content_loader import ContentLoadError, load_parent_scales, load_student_scales

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

PROFILE_EXPORT_TYPES = {"profile", "student_profiles"}


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


def _record_export_rows(rows) -> list[dict]:
    export_rows = []
    for row in rows:
        item = dict(row)
        data = _loads(item.get("data_json"), {})
        export_rows.append(
            {
                "id": item.get("id"),
                "anonymous_id": data.get("anonymous_id") or _anonymous_id(item.get("user_id") or ""),
                "module_type": item.get("module_type"),
                "source_id": item.get("source_id"),
                "data_json": item.get("data_json"),
                "created_at": item.get("created_at"),
                "updated_at": item.get("updated_at"),
                "export_allowed": item.get("export_allowed"),
            }
        )
    return export_rows


def _profile_rows_contain_high_risk(rows) -> bool:
    return any(row["risk_level"] == "high" or bool(row["requires_review"]) for row in rows)


def _record_rows_contain_high_risk(rows) -> bool:
    for row in rows:
        data = _loads(row["data_json"], {})
        if data.get("risk_level") == "high" or bool(data.get("requires_review")):
            return True
    return False


def _loads(value, fallback):
    if not value:
        return fallback
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return fallback


def _student_followup_rows(rows) -> list[dict]:
    return [
        {
            "id": row["id"],
            "profile_id": row["profile_id"],
            "anonymous_id": _anonymous_id(row["user_id"]),
            "round_no": row["round_no"],
            "fit": row["fit"],
            "task_done": row["task_done"],
            "state_score": row["state_score"],
            "text_length": len(row["text"] or ""),
            "keywords_json": row["keywords_json"],
            "created_at": row["created_at"],
        }
        for row in rows
    ]


def _sandplay_rows(rows) -> list[dict]:
    export_rows = []
    for row in rows:
        summary = _loads(row["summary_json"], {})
        scene = _loads(row["scene_json"], {})
        export_rows.append(
            {
                "id": row["id"],
                "profile_id": row["profile_id"],
                "anonymous_id": _anonymous_id(row["user_id"]),
                "task_title": row["task_title"],
                "symbol_count": summary.get("symbol_count"),
                "stress_count": summary.get("stress_count"),
                "resource_count": summary.get("resource_count"),
                "category_counts_json": json.dumps(summary.get("category_counts", {}), ensure_ascii=False),
                "reflection_length": len(row["reflection_text"] or ""),
                "scene_symbol_count": len(scene.get("symbols", [])) if isinstance(scene, dict) else "",
                "created_at": row["created_at"],
            }
        )
    return export_rows


def _parent_export_rows(rows) -> list[dict]:
    export_rows = []
    for row in rows:
        scores = _loads(row["scores_json"], {})
        report = _loads(row["report_json"], {})
        quality = _loads(row["quality_flags_json"], {})
        scale_scores = scores.get("scale_scores", {}).get("scales", {})
        scs = scale_scores.get("SCS_SF_CN_12", {})
        ius = scale_scores.get("IUS_12_CN", {})
        export_rows.append(
            {
                "id": row["id"],
                "anonymous_id": row["anonymous_id"],
                "participant_code": row["participant_code"],
                "research_consent": row["research_consent"],
                "study_batch": row["study_batch"],
                "source_channel": row["source_channel"],
                "profile_key": row["profile_key"],
                "report_role": report.get("role"),
                "SCS_SF_CN_12_total": scs.get("total"),
                "SCS_SF_CN_12_mean": scs.get("mean"),
                "IUS_12_CN_total": ius.get("total"),
                "IUS_12_CN_mean": ius.get("mean"),
                "duration_seconds": row["duration_seconds"],
                "quality_flags": ",".join(quality.get("flags", [])),
                "created_at": row["created_at"],
            }
        )
    return export_rows


def _scale_items(payload: dict, instrument: str) -> list[dict]:
    rows = []
    for scale in payload.get("scales", []):
        for item in scale.get("items", []):
            rows.append(
                {
                    "instrument": instrument,
                    "scale_code": scale.get("scale_code"),
                    "scale_name": scale.get("name"),
                    "item_code": item.get("item_code"),
                    "display_order": item.get("display_order"),
                    "item_text": item.get("text"),
                    "dimension": item.get("dimension"),
                    "feature": item.get("feature"),
                    "reverse_scored": 1 if item.get("reverse_scored") else 0,
                    "source_version": scale.get("source_version", payload.get("version")),
                    "source_item": item.get("source_item", ""),
                }
            )
    return rows


def _codebook_rows() -> list[dict]:
    return _scale_items(load_parent_scales(), "parent_dual_scale") + _scale_items(load_student_scales(), "student_profile")


def _parent_raw_wide_rows(rows) -> list[dict]:
    item_codes = [item["item_code"] for item in _scale_items(load_parent_scales(), "parent_dual_scale")]
    export_rows = []
    for row in rows:
        answers = _loads(row["answers_json"], {}).get("scale_answers", {})
        export_row = {
            "id": row["id"],
            "anonymous_id": row["anonymous_id"],
            "participant_code": row["participant_code"],
            "study_batch": row["study_batch"],
            "source_channel": row["source_channel"],
            "duration_seconds": row["duration_seconds"],
            "quality_flags_json": row["quality_flags_json"],
        }
        for code in item_codes:
            export_row[code] = answers.get(code, "")
        export_rows.append(export_row)
    return export_rows


def _parent_long_rows(rows) -> list[dict]:
    item_lookup = {item["item_code"]: item for item in _scale_items(load_parent_scales(), "parent_dual_scale")}
    export_rows = []
    for row in rows:
        answers = _loads(row["answers_json"], {}).get("scale_answers", {})
        item_scores = _loads(row["scores_json"], {}).get("scale_scores", {}).get("item_scores", {})
        for item_code, item in item_lookup.items():
            score = item_scores.get(item_code, {})
            export_rows.append(
                {
                    "submission_id": row["id"],
                    "anonymous_id": row["anonymous_id"],
                    "participant_code": row["participant_code"],
                    "scale_code": item.get("scale_code"),
                    "item_code": item_code,
                    "dimension": item.get("dimension"),
                    "raw_score": score.get("raw", answers.get(item_code, "")),
                    "scored_value": score.get("scored", ""),
                    "reverse_scored": item.get("reverse_scored"),
                    "created_at": row["created_at"],
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

    user_id = request.args.get("user_id")
    module_type = request.args.get("module_type")
    confirmed_high_risk_export = parse_bool(request.args.get("confirm_high_risk"), False)
    contains_high_risk = False
    try:
        with get_connection() as conn:
            if export_type in PROFILE_EXPORT_TYPES:
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
                contains_high_risk = _profile_rows_contain_high_risk(rows)
                if contains_high_risk and not confirmed_high_risk_export:
                    return fail(
                        "high_risk_export_confirmation_required",
                        "本次导出包含高风险或需复核画像，请确认高风险导出后重试。",
                        status=409,
                    )
                rows = _profile_export_rows(rows)
            elif export_type == "records":
                where_clauses = ["export_allowed = 1"]
                params = []
                if user_id:
                    where_clauses.append("user_id = ?")
                    params.append(user_id)
                if module_type:
                    where_clauses.append("module_type = ?")
                    params.append(module_type)
                rows = conn.execute(
                    f"""
                    SELECT * FROM records
                    WHERE {' AND '.join(where_clauses)}
                    ORDER BY created_at DESC
                    """,
                    params,
                ).fetchall()
                contains_high_risk = _record_rows_contain_high_risk(rows)
                if contains_high_risk and not confirmed_high_risk_export:
                    return fail(
                        "high_risk_export_confirmation_required",
                        "本次导出包含高风险或需复核摘要，请确认高风险导出后重试。",
                        status=409,
                    )
                rows = _record_export_rows(rows)
            elif export_type == "student_followups":
                if user_id:
                    rows = conn.execute(
                        """
                        SELECT * FROM student_profile_followups
                        WHERE user_id = ? AND export_allowed = 1
                        ORDER BY created_at DESC
                        """,
                        (user_id,),
                    ).fetchall()
                else:
                    rows = conn.execute(
                        """
                        SELECT * FROM student_profile_followups
                        WHERE export_allowed = 1
                        ORDER BY created_at DESC
                        """
                    ).fetchall()
                rows = _student_followup_rows(rows)
            elif export_type == "sandplay":
                if user_id:
                    rows = conn.execute(
                        """
                        SELECT * FROM student_sandplay_entries
                        WHERE user_id = ? AND export_allowed = 1
                        ORDER BY created_at DESC
                        """,
                        (user_id,),
                    ).fetchall()
                else:
                    rows = conn.execute(
                        """
                        SELECT * FROM student_sandplay_entries
                        WHERE export_allowed = 1
                        ORDER BY created_at DESC
                        """
                    ).fetchall()
                rows = _sandplay_rows(rows)
            elif export_type == "parent_assessments":
                if user_id:
                    rows = conn.execute(
                        """
                        SELECT * FROM parent_assessment_submissions
                        WHERE user_id = ? AND export_allowed = 1
                        ORDER BY created_at DESC
                        """,
                        (user_id,),
                    ).fetchall()
                else:
                    rows = conn.execute(
                        """
                        SELECT * FROM parent_assessment_submissions
                        WHERE export_allowed = 1
                        ORDER BY created_at DESC
                        """
                    ).fetchall()
                rows = _parent_export_rows(rows)
            elif export_type in {"raw_wide", "long"}:
                rows = conn.execute(
                    """
                    SELECT * FROM parent_assessment_submissions
                    WHERE research_consent = 1 AND export_allowed = 1
                    ORDER BY created_at DESC
                    """
                ).fetchall()
                rows = _parent_raw_wide_rows(rows) if export_type == "raw_wide" else _parent_long_rows(rows)
            elif export_type == "codebook":
                rows = _codebook_rows()
            else:
                table = EXPORT_TABLES.get(export_type)
                if table is None:
                    return fail(
                        "invalid_export_type",
                        "支持的 type：goals, diaries, feedback, checkins, assessments, profile, student_profiles, records, student_followups, sandplay, parent_assessments, raw_wide, long, codebook, reports, supervision, cards",
                    )
                if user_id and table != "training_cards":
                    rows = conn.execute(
                        f"SELECT * FROM {table} WHERE user_id = ? ORDER BY created_at DESC",
                        (user_id,),
                    ).fetchall()
                else:
                    rows = conn.execute(f"SELECT * FROM {table} ORDER BY created_at DESC").fetchall()

            write_audit_log(
                conn,
                action=f"export_{export_type}",
                actor_id="admin-token",
                target_type="export",
                target_id=export_type,
                metadata={
                    "type": export_type,
                    "user_id_filter": user_id,
                    "module_type_filter": module_type,
                    "row_count": len(rows),
                    "contains_high_risk": contains_high_risk,
                    "confirmed_high_risk_export": confirmed_high_risk_export,
                },
            )
            conn.commit()
    except ContentLoadError as exc:
        return fail("content_load_error", str(exc), status=500)

    output = StringIO()
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
