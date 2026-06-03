"""Parent dual-scale assessment endpoints."""

import hashlib

from flask import Blueprint, request

from database import ensure_user, get_connection, json_dumps, json_loads, new_id, now_iso, row_to_dict, rows_to_dicts
from routes.utils import fail, ok, parse_bool
from services.content_loader import ContentLoadError
from services.parent_assessment_service import (
    ParentAssessmentInputError,
    create_parent_assessment_result,
    get_parent_assessment_payload,
)

bp = Blueprint("parent_assessments", __name__, url_prefix="/api")


def _anonymous_id(user_id: str) -> str:
    digest = hashlib.sha256(user_id.encode("utf-8")).hexdigest()[:12]
    return f"anon_{digest}"


def _expand_parent_row(item: dict | None) -> dict | None:
    if item is None:
        return None
    item["answers"] = json_loads(item.get("answers_json"), {})
    item["scores"] = json_loads(item.get("scores_json"), {})
    item["report"] = json_loads(item.get("report_json"), {})
    item["quality_flags"] = json_loads(item.get("quality_flags_json"), {})
    return item


@bp.get("/parent-assessment")
def get_parent_assessment():
    try:
        return ok(get_parent_assessment_payload())
    except ContentLoadError as exc:
        return fail("content_load_error", str(exc), status=500)


@bp.post("/parent-assessments")
def create_parent_assessment():
    payload = request.get_json(silent=True) or {}
    try:
        result = create_parent_assessment_result(payload)
    except ParentAssessmentInputError as exc:
        return fail("missing_parent_assessment_answers", str(exc), status=400)
    except ContentLoadError as exc:
        return fail("content_load_error", str(exc), status=500)

    user_id = payload.get("user_id") or "demo-parent"
    submission_id = new_id("parent")
    timestamp = now_iso()
    completed_at = payload.get("completed_at") or timestamp

    with get_connection() as conn:
        ensure_user(conn, user_id, payload.get("nickname"))
        conn.execute(
            """
            INSERT INTO parent_assessment_submissions (
                id, user_id, anonymous_id, participant_code, research_consent,
                study_batch, source_channel, questionnaire_version, scoring_version,
                answers_json, scores_json, profile_key, report_json,
                started_at, completed_at, duration_seconds, quality_flags_json,
                export_allowed, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                submission_id,
                user_id,
                _anonymous_id(user_id),
                str(payload.get("participant_code") or "").strip()[:120],
                1 if parse_bool(payload.get("research_consent"), True) else 0,
                str(payload.get("study_batch") or "").strip()[:120],
                str(payload.get("source_channel") or "safehome-web").strip()[:120],
                result.get("questionnaire_version"),
                result.get("scoring_version"),
                json_dumps({"scale_answers": result.get("answers"), "question_answers": result.get("question_answers")}),
                json_dumps({"scale_scores": result.get("scores"), "question_scores": result.get("question_scores")}),
                result.get("profile_key"),
                json_dumps(result.get("report")),
                payload.get("started_at"),
                completed_at,
                result.get("duration_seconds", 0),
                json_dumps(result.get("quality_flags", {})),
                1,
                timestamp,
                timestamp,
            ),
        )
        conn.execute(
            """
            INSERT INTO records (
                id, user_id, module_type, source_id, data_json,
                created_at, updated_at, export_allowed
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                new_id("record"),
                user_id,
                "parent_assessment",
                submission_id,
                json_dumps(
                    {
                        "anonymous_id": _anonymous_id(user_id),
                        "profile_key": result.get("profile_key"),
                        "report_role": result.get("report", {}).get("role"),
                        "duration_seconds": result.get("duration_seconds", 0),
                        "quality_flags": result.get("quality_flags", {}).get("flags", []),
                    }
                ),
                timestamp,
                timestamp,
                1,
            ),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM parent_assessment_submissions WHERE id = ?", (submission_id,)).fetchone()

    item = _expand_parent_row(row_to_dict(row))
    item["report_url"] = f"/assessment/report/{submission_id}"
    return ok(item, status=201)


@bp.get("/parent-assessments")
def list_parent_assessments():
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT * FROM parent_assessment_submissions
            ORDER BY created_at DESC
            LIMIT 100
            """
        ).fetchall()
    items = rows_to_dicts(rows)
    for item in items:
        _expand_parent_row(item)
    return ok({"items": items})


@bp.get("/parent-assessments/<submission_id>")
def get_parent_assessment_result(submission_id: str):
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM parent_assessment_submissions WHERE id = ?", (submission_id,)).fetchone()
    if row is None:
        return fail("not_found", "没有找到对应的家长测评报告", status=404)
    return ok(_expand_parent_row(row_to_dict(row)))


@bp.post("/parent-assessments/<submission_id>/actions")
def create_parent_report_action(submission_id: str):
    payload = request.get_json(silent=True) or {}
    action_key = str(payload.get("action_key") or "").strip()
    if not action_key:
        return fail("missing_action_key", "请提供行动反馈类型", status=400)
    action_id = new_id("parent_action")
    timestamp = now_iso()
    with get_connection() as conn:
        row = conn.execute("SELECT id FROM parent_assessment_submissions WHERE id = ?", (submission_id,)).fetchone()
        if row is None:
            return fail("not_found", "没有找到对应的家长测评报告", status=404)
        conn.execute(
            """
            INSERT INTO parent_report_actions (id, submission_id, action_key, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (action_id, submission_id, action_key[:120], timestamp),
        )
        conn.commit()
        action = conn.execute("SELECT * FROM parent_report_actions WHERE id = ?", (action_id,)).fetchone()
    return ok(row_to_dict(action), status=201)
