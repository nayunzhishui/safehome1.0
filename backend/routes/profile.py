"""Student profile and risk-check endpoints."""

import hashlib
from datetime import datetime, timedelta, timezone

from flask import Blueprint, request

from database import ensure_user, get_connection, json_dumps, json_loads, new_id, now_iso, row_to_dict, rows_to_dicts
from services.content_loader import ContentLoadError
from services.risk_review_service import create_risk_review_record
from services.risk_service import check_text_risk
from services.sandplay_service import SandplayInputError, summarize_sandplay_scene, validate_sandplay_scene
from services.student_profile_model_service import (
    PROFILE_MODEL_TYPE,
    ProfileInputError,
    build_student_visuals,
    extract_keywords,
    generate_student_profile,
    get_model_info_payload,
    get_student_assessment_payload,
)
from routes.utils import (
    admin_token_error_response,
    auth_error_response,
    fail,
    ok,
    parse_bool,
    parse_int,
    require_admin_or_owner,
    require_admin_token,
    require_user_id,
    resolve_user_id_for_query,
)
from routes.consent import get_latest_consent

bp = Blueprint("profile", __name__, url_prefix="/api")


class ProfileIdempotencyConflict(ValueError):
    """The same client submission key was reused with different profile answers."""


PROFILE_WORKSHEET_ID = "student_profile_v1"
PROFILE_WORKSHEET_TITLE = "学生支持性画像测评"


def _date_key(value: str | None) -> str | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).date().isoformat()
    except ValueError:
        return str(value)[:10] or None


def _week_bounds() -> tuple[str, str]:
    today = datetime.now(timezone.utc).date()
    start = today - timedelta(days=today.weekday())
    end = start + timedelta(days=7)
    return start.isoformat(), end.isoformat()


def _streak_from_dates(date_keys: set[str]) -> int:
    today = datetime.now(timezone.utc).date()
    streak = 0
    current = today
    while current.isoformat() in date_keys:
        streak += 1
        current -= timedelta(days=1)
    return streak


def _anonymous_id(user_id: str) -> str:
    digest = hashlib.sha256(user_id.encode("utf-8")).hexdigest()[:12]
    return f"anon_{digest}"


def _input_scores(payload: dict) -> dict:
    raw_scores = payload.get("scores") if isinstance(payload.get("scores"), dict) else payload
    fields = [
        "test_anxiety",
        "test_anxiety_worry",
        "test_anxiety_emotionality",
        "iu_score",
        "iu_total",
        "erf_evaluation",
        "erf_expression",
        "erf_strategy_flex",
        "self_compassion",
        "self_criticism_raw",
        "fear_score",
        "f_score",
    ]
    return {field: raw_scores.get(field) for field in fields if raw_scores.get(field) is not None}


def _latest_reviews_by_profile(conn, profile_ids: list[str]) -> dict[str, dict]:
    if not profile_ids:
        return {}
    placeholders = ",".join("?" for _ in profile_ids)
    rows = conn.execute(
        f"""
        SELECT * FROM profile_reviews
        WHERE profile_id IN ({placeholders})
        ORDER BY created_at DESC
        """,
        profile_ids,
    ).fetchall()
    latest: dict[str, dict] = {}
    for row in rows:
        item = row_to_dict(row)
        profile_id = item.get("profile_id")
        if profile_id and profile_id not in latest:
            latest[profile_id] = item
    return latest


def _expand_profile_row(item: dict | None) -> dict | None:
    if item is None:
        return None
    item["scores"] = json_loads(item.get("scores_json"), {})
    item["text_features"] = json_loads(item.get("text_features_json"), {})
    item["dimensions"] = json_loads(item.get("dimensions_json"), [])
    item["recommended_task_ids"] = json_loads(item.get("recommended_task_ids_json"), [])
    item["report"] = json_loads(item.get("report_json"), {})
    item["visuals"] = json_loads(item.get("visuals_json"), {})
    return item


def _assessment_answers(payload: dict, result: dict) -> dict:
    text_answers = result.get("text_answers", {})
    free_text_length = sum(len(str(value or "")) for value in text_answers.values())
    return {
        "answers": payload.get("answers"),
        "aggregate_scores": _input_scores(payload),
        "text_answers_summary": {
            "present": bool(free_text_length),
            "total_length": free_text_length,
            "risk_level": result.get("risk_level", "low"),
            "note": "默认不在导出中展示自由文本原文。",
        },
    }


def _consent_summary(conn, user_id: str) -> dict:
    summary = {}
    for consent_type in ["user_agreement", "privacy_policy", "non_diagnostic_notice", "research_authorization"]:
        latest = get_latest_consent(conn, user_id, consent_type)
        summary[consent_type] = {
            "status": "agreed" if latest and latest.get("agreed") else "missing_or_declined",
            "version": latest.get("consent_version") if latest else None,
            "recorded_at": latest.get("agreed_at") if latest and latest.get("agreed") else latest.get("created_at") if latest else None,
        }
    return summary


@bp.get("/profile/stats")
def get_profile_stats():
    try:
        user_id = resolve_user_id_for_query(request.args.get("user_id"))
    except ValueError as exc:
        return fail("validation_error", str(exc), status=400)

    week_start, week_end = _week_bounds()
    with get_connection() as conn:
        diary_rows = conn.execute(
            """
            SELECT id, event_time, created_at
            FROM emotion_diaries
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT 120
            """,
            (user_id,),
        ).fetchall()
        checkin_rows = conn.execute(
            """
            SELECT id, created_at
            FROM checkins
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT 120
            """,
            (user_id,),
        ).fetchall()
        assessment_rows = conn.execute(
            """
            SELECT worksheet_id, created_at
            FROM assessment_results
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT 120
            """,
            (user_id,),
        ).fetchall()
        worksheet_row = conn.execute(
            "SELECT COUNT(*) AS count FROM assessment_worksheets WHERE enabled_for_user = 1"
        ).fetchone()
        unread_row = conn.execute(
            "SELECT COUNT(*) AS count FROM messages WHERE user_id = ? AND status = 'unread'",
            (user_id,),
        ).fetchone()

    diary_dates = {_date_key(row["event_time"] or row["created_at"]) for row in diary_rows}
    checkin_dates = {_date_key(row["created_at"]) for row in checkin_rows}
    active_dates = {date for date in diary_dates.union(checkin_dates) if date}
    weekly_diaries = sum(1 for row in diary_rows if week_start <= (_date_key(row["event_time"] or row["created_at"]) or "") < week_end)
    weekly_checkins = sum(1 for row in checkin_rows if week_start <= (_date_key(row["created_at"]) or "") < week_end)
    weekly_assessments = sum(1 for row in assessment_rows if week_start <= (_date_key(row["created_at"]) or "") < week_end)
    completed_worksheets = {row["worksheet_id"] for row in assessment_rows if row["worksheet_id"]}
    enabled_worksheet_count = int(worksheet_row["count"] if worksheet_row else 0)

    return ok(
        {
            "user_id": user_id,
            "streak_days": _streak_from_dates(active_dates),
            "weekly_record_count": weekly_diaries + weekly_checkins,
            "weekly_diary_count": weekly_diaries,
            "weekly_checkin_count": weekly_checkins,
            "weekly_assessment_count": weekly_assessments,
            "assessment_completed_count": len(completed_worksheets),
            "unfinished_assessment_count": max(enabled_worksheet_count - len(completed_worksheets), 0),
            "unread_message_count": int(unread_row["count"] if unread_row else 0),
            "week_start": week_start,
            "week_end": (datetime.fromisoformat(week_end) - timedelta(days=1)).date().isoformat(),
            "boundary_notice": "这些统计只用于回顾记录和练习进展，不代表诊断、评价或能力判断。",
        }
    )


def _save_profile_result(payload: dict, result: dict, client_submission_id: str | None = None) -> dict:
    user_id = require_user_id(payload)
    result_id = new_id("assessment")
    profile_id = new_id("profile")
    timestamp = now_iso()
    answers = _assessment_answers(payload, result)
    model_scores = result.get("scores", {})
    model_features = model_scores.get("features", {})
    text_features = result.get("text_features", {})
    recommended_card_ids = result.get("recommended_card_ids", [])
    scores = {
        "model_scores": model_scores,
        "model_features": model_features,
        "profile_code": result.get("profile_code"),
        "profile_name": result.get("profile_name"),
        "original_profile_name": result.get("original_profile_name"),
        "confidence": result.get("confidence"),
        "cluster_id": result.get("cluster_id"),
        "pc1": result.get("pc1"),
        "pc2": result.get("pc2"),
        "risk_level": result.get("risk_level"),
        "requires_review": result.get("requires_review"),
        "allow_auto_feedback": result.get("allow_auto_feedback"),
        "dimensions": result.get("dimensions", []),
        "supportive_explanation": result.get("supportive_explanation"),
        "strength_note": result.get("strength_note"),
        "small_step": result.get("small_step"),
        "boundary_notice": result.get("boundary_notice"),
        "model_version": result.get("model_version"),
        "model_type": result.get("model_type"),
        "rules_version": result.get("rules_version"),
        "recommended_card_ids": recommended_card_ids,
    }
    result_summary = f"{result.get('profile_name')}：{result.get('supportive_explanation')}"

    with get_connection() as conn:
        ensure_user(conn, user_id, payload.get("nickname"))
        consent_summary = _consent_summary(conn, user_id)
        if client_submission_id:
            existing = conn.execute(
                "SELECT * FROM assessment_results WHERE user_id = ? AND client_submission_id = ?",
                (user_id, client_submission_id),
            ).fetchone()
            if existing is not None:
                if existing["worksheet_id"] != PROFILE_WORKSHEET_ID or json_loads(existing["answers_json"], {}) != answers:
                    raise ProfileIdempotencyConflict("该提交标识已用于另一份支持性测评。")
                profile = conn.execute(
                    "SELECT id FROM student_profiles WHERE assessment_result_id = ? LIMIT 1",
                    (existing["id"],),
                ).fetchone()
                saved = row_to_dict(existing) or {}
                saved["student_profile_id"] = profile["id"] if profile else None
                saved["answers"] = answers
                saved["scores"] = json_loads(existing["scores_json"], {})
                saved["consent_summary"] = consent_summary
                saved["idempotency_replayed"] = True
                return saved
        report = dict(result.get("report") or {})
        report["consent_summary"] = consent_summary
        conn.execute(
            """
            INSERT INTO assessment_results (
                id, user_id, worksheet_id, worksheet_title, category,
                answers_json, scores_json, total_score, result_summary, client_submission_id, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                result_id,
                user_id,
                PROFILE_WORKSHEET_ID,
                PROFILE_WORKSHEET_TITLE,
                "学生画像",
                json_dumps(answers),
                json_dumps(scores),
                None,
                result_summary,
                client_submission_id,
                timestamp,
            ),
        )
        conn.execute(
            """
            INSERT INTO student_profiles (
                id, user_id, anonymous_id, assessment_result_id, round, source,
                scores_json, text_features_json, profile_code, profile_name,
                confidence, dimensions_json, recommended_task_ids_json,
                risk_level, requires_review, boundary_notice, rules_version,
                model_version, model_type, cluster_id, pc1, pc2, nearest_distance,
                second_distance, report_json, visuals_json,
                export_allowed, data_quality, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                profile_id,
                user_id,
                _anonymous_id(user_id),
                result_id,
                int(payload.get("round") or 1),
                PROFILE_WORKSHEET_ID,
                json_dumps(model_scores),
                json_dumps(text_features),
                result.get("profile_code"),
                result.get("profile_name"),
                result.get("confidence"),
                json_dumps(result.get("dimensions", [])),
                json_dumps(recommended_card_ids),
                result.get("risk_level", "low"),
                1 if result.get("requires_review") else 0,
                result.get("boundary_notice"),
                result.get("rules_version"),
                result.get("model_version"),
                result.get("model_type", PROFILE_MODEL_TYPE),
                result.get("cluster_id"),
                result.get("pc1"),
                result.get("pc2"),
                result.get("nearest_distance"),
                result.get("second_distance"),
                json_dumps(report),
                json_dumps(result.get("visuals", {})),
                1,
                result.get("data_quality", "valid"),
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
                "student_profile",
                profile_id,
                json_dumps(
                    {
                        "anonymous_id": _anonymous_id(user_id),
                        "assessment_result_id": result_id,
                        "profile_code": result.get("profile_code"),
                        "profile_name": result.get("profile_name"),
                        "confidence": result.get("confidence"),
                        "model_version": result.get("model_version"),
                        "model_type": result.get("model_type", PROFILE_MODEL_TYPE),
                        "cluster_id": result.get("cluster_id"),
                        "pc1": result.get("pc1"),
                        "pc2": result.get("pc2"),
                        "risk_level": result.get("risk_level", "low"),
                        "requires_review": bool(result.get("requires_review")),
                        "consent_summary": consent_summary,
                        "recommended_card_ids": recommended_card_ids,
                        "rules_version": result.get("rules_version"),
                    }
                ),
                timestamp,
                timestamp,
                1,
            ),
        )
        risk_result = check_text_risk(payload.get("free_text") or "", source="student_profile")
        create_risk_review_record(conn, user_id, "student_profile", profile_id, risk_result)
        conn.commit()
        row = conn.execute("SELECT * FROM assessment_results WHERE id = ?", (result_id,)).fetchone()

    saved = row_to_dict(row) or {}
    saved["student_profile_id"] = profile_id
    saved["answers"] = answers
    saved["scores"] = scores
    saved["consent_summary"] = consent_summary
    saved["idempotency_replayed"] = False
    return saved


@bp.post("/profile")
def create_profile():
    payload = request.get_json(silent=True) or {}
    submission_id = str(request.headers.get("Idempotency-Key") or payload.get("client_submission_id") or "").strip()
    if len(submission_id) > 120:
        return fail("validation_error", "提交标识不能超过120个字符。", status=400)
    try:
        require_user_id(payload)
    except ValueError as exc:
        return fail("validation_error", str(exc), status=400)
    try:
        result = generate_student_profile(payload)
    except ProfileInputError as exc:
        return fail("missing_profile_scores", str(exc), status=400)
    except ContentLoadError as exc:
        return fail("content_load_error", str(exc), status=500)
    try:
        saved = _save_profile_result(payload, result, submission_id or None)
    except ProfileIdempotencyConflict as exc:
        return fail("idempotency_conflict", str(exc), status=409)
    if saved.get("idempotency_replayed"):
        persisted = saved.get("scores") or {}
        for key, value in persisted.items():
            if key != "model_scores":
                result[key] = value
    result["assessment_result_id"] = saved.get("id")
    result["student_profile_id"] = saved.get("student_profile_id")
    result["consent_summary"] = saved.get("consent_summary")
    result["saved_to_assessment_results"] = True
    result["saved_to_student_profiles"] = True
    result["idempotency_replayed"] = bool(saved.get("idempotency_replayed"))
    return ok(result, status=200 if result["idempotency_replayed"] else 201)


@bp.get("/student-assessment")
def get_student_assessment():
    try:
        return ok(get_student_assessment_payload())
    except ContentLoadError as exc:
        return fail("content_load_error", str(exc), status=500)


@bp.post("/risk/check")
def check_risk():
    payload = request.get_json(silent=True) or {}
    text = payload.get("text") or payload.get("free_text") or payload.get("raw_text") or ""
    source = payload.get("source") or "student_profile"
    try:
        return ok(check_text_risk(text, source=source))
    except ContentLoadError as exc:
        return fail("content_load_error", str(exc), status=500)


@bp.get("/profile-results")
def list_profile_results():
    try:
        require_admin_token()
    except ValueError as exc:
        return admin_token_error_response(exc)

    user_id = request.args.get("user_id")
    limit = parse_int(request.args.get("limit"), 50)
    round_number = parse_int(request.args.get("round"))

    where_clauses = []
    params: list = []
    if user_id:
        where_clauses.append("user_id = ?")
        params.append(user_id)
    if round_number is not None:
        where_clauses.append("round = ?")
        params.append(round_number)

    where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
    params.append(limit)

    with get_connection() as conn:
        rows = conn.execute(
            f"""
            SELECT * FROM student_profiles
            {where_sql}
            ORDER BY created_at DESC
            LIMIT ?
            """,
            params,
        ).fetchall()
        items = rows_to_dicts(rows)
        latest_reviews = _latest_reviews_by_profile(conn, [item["id"] for item in items])

    for item in items:
        item["latest_review"] = latest_reviews.get(item["id"])
        _expand_profile_row(item)
    return ok({"items": items})


@bp.get("/profile-results/<profile_id>")
def get_profile_result(profile_id: str):
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM student_profiles WHERE id = ?", (profile_id,)).fetchone()
        if row is None:
            return fail("not_found", "没有找到对应的学生画像结果", status=404)
        try:
            actor_id = require_admin_or_owner(row["user_id"])
        except ValueError as exc:
            return auth_error_response(exc)
        latest_review = conn.execute(
            """
            SELECT * FROM profile_reviews
            WHERE profile_id = ?
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (profile_id,),
        ).fetchone()
        conn.execute(
            """
            INSERT INTO audit_logs (id, actor_id, action, target_type, target_id, metadata_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                new_id("audit"),
                actor_id,
                "view_profile",
                "student_profile",
                profile_id,
                json_dumps({"route": "/api/profile-results/<id>"}),
                now_iso(),
            ),
        )
        conn.commit()
    data = row_to_dict(row)
    _expand_profile_row(data)
    data["latest_review"] = row_to_dict(latest_review)
    return ok(data)


@bp.get("/profile-results/<profile_id>/visuals")
def get_profile_visuals(profile_id: str):
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM student_profiles WHERE id = ?", (profile_id,)).fetchone()
        if row is None:
            return fail("not_found", "没有找到对应的学生画像结果", status=404)
        try:
            require_admin_or_owner(row["user_id"])
        except ValueError as exc:
            return auth_error_response(exc)
        followup_rows = conn.execute(
            """
            SELECT * FROM student_profile_followups
            WHERE profile_id = ?
            ORDER BY round_no ASC, created_at ASC
            """,
            (profile_id,),
        ).fetchall()
    item = row_to_dict(row)
    scores = json_loads(item.get("scores_json"), {})
    report = json_loads(item.get("report_json"), {})
    profile_result = {
        "profile_code": item.get("profile_code"),
        "cluster_id": item.get("cluster_id"),
        "confidence": item.get("confidence"),
        "pc1": item.get("pc1"),
        "pc2": item.get("pc2"),
    }
    visuals = build_student_visuals(scores, profile_result, rows_to_dicts(followup_rows))
    visuals["keywords"] = report.get("keywords", [])
    return ok(visuals)


@bp.get("/profile-results/<profile_id>/followups")
def list_profile_followups(profile_id: str):
    with get_connection() as conn:
        profile = conn.execute("SELECT id, user_id FROM student_profiles WHERE id = ?", (profile_id,)).fetchone()
        if profile is None:
            return fail("not_found", "没有找到对应的学生画像结果", status=404)
        try:
            require_admin_or_owner(profile["user_id"])
        except ValueError as exc:
            return auth_error_response(exc)
        rows = conn.execute(
            """
            SELECT * FROM student_profile_followups
            WHERE profile_id = ?
            ORDER BY round_no ASC, created_at ASC
            """,
            (profile_id,),
        ).fetchall()
    return ok({"items": rows_to_dicts(rows)})


@bp.post("/profile-results/<profile_id>/followups")
def create_profile_followup(profile_id: str):
    payload = request.get_json(silent=True) or {}
    round_no = parse_int(payload.get("round_no"), 1) or 1
    state_score = parse_int(payload.get("state_score"))
    text = str(payload.get("text") or "").strip()[:800]
    risk_result = check_text_risk(text, source="student_profile_followup")
    timestamp = now_iso()
    followup_id = new_id("followup")

    with get_connection() as conn:
        profile = conn.execute("SELECT * FROM student_profiles WHERE id = ?", (profile_id,)).fetchone()
        if profile is None:
            return fail("not_found", "没有找到对应的学生画像结果", status=404)
        try:
            require_admin_or_owner(profile["user_id"])
        except ValueError as exc:
            return auth_error_response(exc)
        profile_item = row_to_dict(profile)
        keywords = extract_keywords(text)
        conn.execute(
            """
            INSERT INTO student_profile_followups (
                id, profile_id, user_id, round_no, fit, task_done,
                state_score, text, keywords_json, created_at, export_allowed
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                followup_id,
                profile_id,
                profile_item.get("user_id"),
                round_no,
                str(payload.get("fit") or "").strip()[:80],
                str(payload.get("task_done") or "").strip()[:80],
                state_score,
                text,
                json_dumps(keywords),
                timestamp,
                1,
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
                profile_item.get("user_id"),
                "profile_followup",
                followup_id,
                json_dumps(
                    {
                        "profile_id": profile_id,
                        "round_no": round_no,
                        "state_score": state_score,
                        "keywords": keywords,
                        "risk_level": risk_result.get("risk_level", "low"),
                        "requires_review": bool(risk_result.get("requires_review")),
                    }
                ),
                timestamp,
                timestamp,
                1,
            ),
        )
        create_risk_review_record(conn, profile_item.get("user_id"), "student_profile_followup", followup_id, risk_result)
        conn.commit()
        row = conn.execute("SELECT * FROM student_profile_followups WHERE id = ?", (followup_id,)).fetchone()
    item = row_to_dict(row)
    item["risk"] = risk_result
    item["boundary_notice"] = risk_result.get("boundary_notice")
    return ok(item, status=201)


@bp.get("/profile-results/<profile_id>/sandplay")
def list_profile_sandplay(profile_id: str):
    with get_connection() as conn:
        profile = conn.execute("SELECT id, user_id FROM student_profiles WHERE id = ?", (profile_id,)).fetchone()
        if profile is None:
            return fail("not_found", "没有找到对应的学生画像结果", status=404)
        try:
            require_admin_or_owner(profile["user_id"])
        except ValueError as exc:
            return auth_error_response(exc)
        rows = conn.execute(
            """
            SELECT * FROM student_sandplay_entries
            WHERE profile_id = ?
            ORDER BY created_at DESC
            """,
            (profile_id,),
        ).fetchall()
    items = rows_to_dicts(rows)
    for item in items:
        item["scene"] = json_loads(item.get("scene_json"), {})
        item["summary"] = json_loads(item.get("summary_json"), {})
    return ok({"items": items})


@bp.post("/profile-results/<profile_id>/sandplay")
def create_profile_sandplay(profile_id: str):
    payload = request.get_json(silent=True) or {}
    scene = payload.get("scene")
    if not isinstance(scene, dict):
        return fail("invalid_sandplay_scene", "沙盘场景格式无效", status=400)
    try:
        validate_sandplay_scene(scene)
    except SandplayInputError as exc:
        return fail("invalid_sandplay_scene", str(exc), status=400)

    timestamp = now_iso()
    entry_id = new_id("sandplay")
    summary = summarize_sandplay_scene(scene)
    reflection_text = str(payload.get("reflection_text") or "").strip()[:800]
    risk_result = check_text_risk(reflection_text, source="student_sandplay")

    with get_connection() as conn:
        profile = conn.execute("SELECT * FROM student_profiles WHERE id = ?", (profile_id,)).fetchone()
        if profile is None:
            return fail("not_found", "没有找到对应的学生画像结果", status=404)
        try:
            require_admin_or_owner(profile["user_id"])
        except ValueError as exc:
            return auth_error_response(exc)
        profile_item = row_to_dict(profile)
        report = json_loads(profile_item.get("report_json"), {})
        task_title = str(payload.get("task_title") or report.get("sandplay_task", {}).get("title") or "沙盘式表达任务")
        conn.execute(
            """
            INSERT INTO student_sandplay_entries (
                id, profile_id, user_id, task_title, scene_json,
                reflection_text, summary_json, created_at, export_allowed
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                entry_id,
                profile_id,
                profile_item.get("user_id"),
                task_title[:120],
                json_dumps(scene),
                reflection_text,
                json_dumps(summary),
                timestamp,
                1,
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
                profile_item.get("user_id"),
                "sandplay_task",
                entry_id,
                json_dumps(
                    {
                        "profile_id": profile_id,
                        "task_title": task_title,
                        "summary": summary,
                        "risk_level": risk_result.get("risk_level", "low"),
                        "requires_review": bool(risk_result.get("requires_review")),
                        "note": "沙盘内容只作为表达线索，不做潜意识解释。",
                    }
                ),
                timestamp,
                timestamp,
                1,
            ),
        )
        create_risk_review_record(conn, profile_item.get("user_id"), "student_sandplay", entry_id, risk_result)
        conn.commit()
        row = conn.execute("SELECT * FROM student_sandplay_entries WHERE id = ?", (entry_id,)).fetchone()
    item = row_to_dict(row)
    item["scene"] = json_loads(item.get("scene_json"), {})
    item["summary"] = json_loads(item.get("summary_json"), {})
    item["risk"] = risk_result
    item["boundary_notice"] = risk_result.get("boundary_notice")
    return ok(item, status=201)


@bp.get("/profile-results/<profile_id>/reviews")
def list_profile_reviews(profile_id: str):
    try:
        require_admin_token()
    except ValueError as exc:
        return admin_token_error_response(exc)

    with get_connection() as conn:
        profile = conn.execute("SELECT id FROM student_profiles WHERE id = ?", (profile_id,)).fetchone()
        if profile is None:
            return fail("not_found", "没有找到对应的学生画像结果", status=404)
        rows = conn.execute(
            """
            SELECT * FROM profile_reviews
            WHERE profile_id = ?
            ORDER BY created_at DESC
            """,
            (profile_id,),
        ).fetchall()
    return ok({"items": rows_to_dicts(rows)})


@bp.post("/profile-results/<profile_id>/review")
def create_profile_review(profile_id: str):
    try:
        actor_id = require_admin_token()
    except ValueError as exc:
        return admin_token_error_response(exc)

    payload = request.get_json(silent=True) or {}
    review_status = str(payload.get("review_status") or "reviewed").strip()
    review_decision = str(payload.get("review_decision") or "").strip()
    note = str(payload.get("note") or "").strip()
    action_summary = str(payload.get("action_summary") or "").strip()

    allowed_statuses = {"pending", "in_progress", "reviewed", "escalated", "closed"}
    if review_status not in allowed_statuses:
        return fail("invalid_review_status", "复核状态无效", status=400)
    if not any([review_decision, note, action_summary]):
        return fail("missing_review_content", "请至少填写复核结论、备注或处置摘要", status=400)

    timestamp = now_iso()
    review_id = new_id("review")
    visible_to_student = 1 if parse_bool(payload.get("visible_to_student"), False) else 0

    with get_connection() as conn:
        profile = conn.execute("SELECT id FROM student_profiles WHERE id = ?", (profile_id,)).fetchone()
        if profile is None:
            return fail("not_found", "没有找到对应的学生画像结果", status=404)
        conn.execute(
            """
            INSERT INTO profile_reviews (
                id, profile_id, reviewer_id, review_status, review_decision,
                note, action_summary, visible_to_student, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                review_id,
                profile_id,
                actor_id,
                review_status,
                review_decision or None,
                note or None,
                action_summary or None,
                visible_to_student,
                timestamp,
                timestamp,
            ),
        )
        conn.execute(
            """
            INSERT INTO audit_logs (id, actor_id, action, target_type, target_id, metadata_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                new_id("audit"),
                actor_id,
                "review_profile",
                "student_profile",
                profile_id,
                json_dumps(
                    {
                        "review_id": review_id,
                        "review_status": review_status,
                        "review_decision": review_decision,
                        "visible_to_student": bool(visible_to_student),
                    }
                ),
                timestamp,
            ),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM profile_reviews WHERE id = ?", (review_id,)).fetchone()

    return ok(row_to_dict(row), status=201)


@bp.get("/model/info")
def model_info():
    try:
        payload = get_model_info_payload()
    except ContentLoadError as exc:
        return fail("content_load_error", str(exc), status=500)
    return ok(payload)
