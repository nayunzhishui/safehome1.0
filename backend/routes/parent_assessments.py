"""Parent dual-scale assessment endpoints."""

import hashlib

from flask import Blueprint, request

from database import ensure_user, get_connection, json_dumps, json_loads, new_id, now_iso, row_to_dict, rows_to_dicts
from routes.consent import DEFAULT_CONSENT_VERSION, get_latest_consent
from routes.utils import auth_error_response, fail, ok, parse_bool, require_admin_or_owner, require_admin_token, require_user_id
from services.consent_service import ConsentError, append_consent_event, is_verified_participant_event
from services.content_loader import ContentLoadError
from services.parent_assessment_service import (
    ParentAssessmentInputError,
    create_parent_assessment_result,
    get_parent_assessment_payload,
)
from services.risk_review_service import create_risk_review_record
from services.risk_service import check_text_risk

bp = Blueprint("parent_assessments", __name__, url_prefix="/api")


@bp.errorhandler(ConsentError)
def handle_consent_error(exc: ConsentError):
    return fail(exc.code, str(exc), status=exc.status)


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


def _parent_assessment_open_text(payload: dict) -> list[str]:
    texts: list[str] = []
    for field in ["free_text", "raw_text", "reflection_text"]:
        if payload.get(field):
            texts.append(str(payload.get(field)))

    question_answers = payload.get("question_answers")
    if isinstance(question_answers, dict):
        texts.extend(str(value) for value in question_answers.values() if value)
    elif isinstance(question_answers, list):
        for item in question_answers:
            if isinstance(item, dict) and item.get("value"):
                texts.append(str(item.get("value")))
    return texts


def _apply_high_risk_parent_boundary(result: dict, risk_result: dict) -> None:
    if risk_result.get("allow_auto_feedback") is not False:
        return
    report = dict(result.get("report") or {})
    report["action_title"] = "优先确认现实支持"
    report["action"] = risk_result.get("safe_response")
    report["course"] = "人工关注与现实支持"
    report["boundary_notice"] = risk_result.get("boundary_notice")
    result["report"] = report


def _ensure_research_consent(conn, user_id: str, agreed: bool, consent_version: str, timestamp: str) -> dict:
    latest = get_latest_consent(conn, user_id, "research_authorization")
    if (
        latest
        and is_verified_participant_event(latest, user_id)
        and bool(latest.get("agreed")) == agreed
        and latest.get("consent_version") == consent_version
        and (latest.get("purpose") or latest.get("consent_type")) == "research_authorization"
        and (latest.get("processor") or "safehome") == "safehome"
    ):
        return {
            "research_authorization": "agreed" if agreed else "declined",
            "consent_version": latest.get("consent_version"),
            "record_id": latest.get("id"),
        }

    item, _created = append_consent_event(
        conn,
        actor_id=user_id,
        subject_id=user_id,
        consent_type="research_authorization",
        consent_version=consent_version,
        agreed=agreed,
        purpose="research_authorization",
        source="embedded_parent_assessment",
        event_type="self_agreed" if agreed else "self_withdrawn",
    )
    return {
        "research_authorization": "agreed" if agreed else "declined",
        "consent_version": consent_version,
        "record_id": item["id"],
    }


@bp.get("/parent-assessment")
def get_parent_assessment():
    try:
        return ok(get_parent_assessment_payload())
    except ContentLoadError as exc:
        return fail("content_load_error", str(exc), status=500)


@bp.post("/parent-assessments")
def create_parent_assessment():
    payload = request.get_json(silent=True) or {}
    client_submission_id = str(request.headers.get("Idempotency-Key") or payload.get("client_submission_id") or "").strip()
    if len(client_submission_id) > 120:
        return fail("validation_error", "提交标识不能超过120个字符。", status=400)
    try:
        user_id = require_user_id(payload)
    except ValueError as exc:
        return fail("validation_error", str(exc), status=400)
    try:
        result = create_parent_assessment_result(payload)
    except ParentAssessmentInputError as exc:
        return fail("missing_parent_assessment_answers", str(exc), status=400)
    except ContentLoadError as exc:
        return fail("content_load_error", str(exc), status=500)
    risk_result = check_text_risk(_parent_assessment_open_text(payload), source="parent_assessment")
    _apply_high_risk_parent_boundary(result, risk_result)

    submission_id = new_id("parent")
    timestamp = now_iso()
    completed_at = payload.get("completed_at") or timestamp
    research_consent = parse_bool(payload.get("research_consent"), True)
    consent_version = str(payload.get("consent_version") or DEFAULT_CONSENT_VERSION).strip() or DEFAULT_CONSENT_VERSION

    with get_connection() as conn:
        ensure_user(conn, user_id, payload.get("nickname"))
        if client_submission_id:
            existing = conn.execute(
                "SELECT * FROM parent_assessment_submissions WHERE user_id = ? AND client_submission_id = ?",
                (user_id, client_submission_id),
            ).fetchone()
            if existing is not None:
                expected_answers = {
                    "scale_answers": result.get("answers"),
                    "question_answers": result.get("question_answers"),
                }
                if json_loads(existing["answers_json"], {}) != expected_answers or bool(existing["research_consent"]) != research_consent:
                    return fail("idempotency_conflict", "该提交标识已用于另一份家长测评。", status=409)
                item = _expand_parent_row(row_to_dict(existing))
                item["report_url"] = f"/assessment/report/{existing['id']}"
                item["risk"] = risk_result
                item["boundary_notice"] = risk_result.get("boundary_notice")
                item["consent_summary"] = _ensure_research_consent(conn, user_id, research_consent, consent_version, timestamp)
                item["idempotency_replayed"] = True
                conn.commit()
                return ok(item)
        consent_summary = _ensure_research_consent(conn, user_id, research_consent, consent_version, timestamp)
        conn.execute(
            """
            INSERT INTO parent_assessment_submissions (
                id, user_id, anonymous_id, participant_code, research_consent,
                study_batch, source_channel, questionnaire_version, scoring_version,
                answers_json, scores_json, profile_key, report_json,
                started_at, completed_at, duration_seconds, quality_flags_json,
                client_submission_id, export_allowed, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                submission_id,
                user_id,
                _anonymous_id(user_id),
                str(payload.get("participant_code") or "").strip()[:120],
                1 if research_consent else 0,
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
                client_submission_id or None,
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
                        "risk_level": risk_result.get("risk_level", "low"),
                        "requires_review": bool(risk_result.get("requires_review")),
                        "consent_summary": consent_summary,
                        "duration_seconds": result.get("duration_seconds", 0),
                        "quality_flags": result.get("quality_flags", {}).get("flags", []),
                    }
                ),
                timestamp,
                timestamp,
                1,
            ),
        )
        create_risk_review_record(conn, user_id, "parent_assessment", submission_id, risk_result)
        conn.commit()
        row = conn.execute("SELECT * FROM parent_assessment_submissions WHERE id = ?", (submission_id,)).fetchone()

    item = _expand_parent_row(row_to_dict(row))
    item["report_url"] = f"/assessment/report/{submission_id}"
    item["risk"] = risk_result
    item["boundary_notice"] = risk_result.get("boundary_notice")
    item["consent_summary"] = consent_summary
    return ok(item, status=201)


@bp.get("/parent-assessments")
def list_parent_assessments():
    try:
        require_admin_token()
    except ValueError as exc:
        return auth_error_response(exc)

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
    try:
        require_admin_or_owner(row["user_id"])
    except ValueError as exc:
        return auth_error_response(exc)
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
        row = conn.execute("SELECT id, user_id FROM parent_assessment_submissions WHERE id = ?", (submission_id,)).fetchone()
        if row is None:
            return fail("not_found", "没有找到对应的家长测评报告", status=404)
        try:
            require_admin_or_owner(row["user_id"])
        except ValueError as exc:
            return auth_error_response(exc)
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
