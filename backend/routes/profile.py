"""Student profile and risk-check endpoints."""

import hashlib

from flask import Blueprint, request

from database import ensure_user, get_connection, json_dumps, new_id, now_iso, row_to_dict, rows_to_dicts
from services.content_loader import ContentLoadError, load_student_profile_rules
from services.profile_service import PROFILE_MODEL_VERSION, ProfileInputError, generate_student_profile
from services.risk_service import check_text_risk
from routes.utils import fail, ok, parse_int

bp = Blueprint("profile", __name__, url_prefix="/api")


PROFILE_WORKSHEET_ID = "student_profile_v1"
PROFILE_WORKSHEET_TITLE = "学生支持性画像测评"


def _anonymous_id(user_id: str) -> str:
    digest = hashlib.sha256(user_id.encode("utf-8")).hexdigest()[:12]
    return f"anon_{digest}"


def _input_scores(payload: dict) -> dict:
    raw_scores = payload.get("scores") if isinstance(payload.get("scores"), dict) else payload
    fields = ["test_anxiety", "iu_score", "fear_score", "f_score", "self_compassion"]
    return {field: raw_scores.get(field) for field in fields if raw_scores.get(field) is not None}


def _profile_answers(payload: dict, result: dict) -> list[dict]:
    score_labels = {
        "test_anxiety": "考试、作业或学习评价相关紧张程度",
        "iu_score": "不确定情境下的放松困难程度",
        "fear_score": "压力信号下的担心/失望预期",
        "f_score": "情绪调节灵活性或恐惧倾向相关分数",
        "self_compassion": "自我支持程度",
    }
    answers = [
        {
            "question_id": field,
            "prompt": label,
            "value": str(value),
            "score": value,
        }
        for field, label in score_labels.items()
        for value in [_input_scores(payload).get(field)]
        if value is not None
    ]

    if payload.get("support_resource"):
        answers.append(
            {
                "question_id": "support_resource",
                "prompt": "最近可用支持资源",
                "value": str(payload.get("support_resource")),
            }
        )

    free_text = str(payload.get("free_text") or "")
    if free_text:
        answers.append(
            {
                "question_id": "free_text_summary",
                "prompt": "自由文本摘要",
                "value": f"已脱敏保存：原文长度 {len(free_text)} 字；风险等级 {result.get('risk_level', 'low')}；不默认保存自由文本原文。",
            }
        )

    return answers


def _save_profile_result(payload: dict, result: dict) -> dict:
    user_id = payload.get("user_id") or "demo-parent"
    result_id = new_id("assessment")
    profile_id = new_id("profile")
    timestamp = now_iso()
    answers = _profile_answers(payload, result)
    input_scores = _input_scores(payload)
    scores = {
        "input_scores": input_scores,
        "profile_code": result.get("profile_code"),
        "profile_name": result.get("profile_name"),
        "confidence": result.get("confidence"),
        "risk_level": result.get("risk_level"),
        "requires_review": result.get("requires_review"),
        "allow_auto_feedback": result.get("allow_auto_feedback"),
        "dimensions": result.get("dimensions", []),
        "supportive_explanation": result.get("supportive_explanation"),
        "strength_note": result.get("strength_note"),
        "small_step": result.get("small_step"),
        "boundary_notice": result.get("boundary_notice"),
        "model_version": result.get("model_version"),
        "rules_version": result.get("rules_version"),
        "recommended_card_ids": result.get("recommended_card_ids", []),
    }
    result_summary = f"{result.get('profile_name')}：{result.get('supportive_explanation')}"
    text_features = {
        "free_text_present": bool(payload.get("free_text")),
        "free_text_length": len(str(payload.get("free_text") or "")),
        "support_resource_present": bool(payload.get("support_resource")),
    }

    with get_connection() as conn:
        ensure_user(conn, user_id, payload.get("nickname"))
        conn.execute(
            """
            INSERT INTO assessment_results (
                id, user_id, worksheet_id, worksheet_title, category,
                answers_json, scores_json, total_score, result_summary, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                export_allowed, data_quality, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                profile_id,
                user_id,
                _anonymous_id(user_id),
                result_id,
                int(payload.get("round") or 1),
                PROFILE_WORKSHEET_ID,
                json_dumps(input_scores),
                json_dumps(text_features),
                result.get("profile_code"),
                result.get("profile_name"),
                result.get("confidence"),
                json_dumps(result.get("dimensions", [])),
                json_dumps(result.get("recommended_card_ids", [])),
                result.get("risk_level", "low"),
                1 if result.get("requires_review") else 0,
                result.get("boundary_notice"),
                result.get("rules_version"),
                1,
                "valid",
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
                        "risk_level": result.get("risk_level", "low"),
                        "requires_review": bool(result.get("requires_review")),
                        "recommended_card_ids": result.get("recommended_card_ids", []),
                        "rules_version": result.get("rules_version"),
                    }
                ),
                timestamp,
                timestamp,
                1,
            ),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM assessment_results WHERE id = ?", (result_id,)).fetchone()

    saved = row_to_dict(row) or {}
    saved["student_profile_id"] = profile_id
    saved["answers"] = answers
    saved["scores"] = scores
    return saved


@bp.post("/profile")
def create_profile():
    payload = request.get_json(silent=True) or {}
    try:
        result = generate_student_profile(payload)
    except ProfileInputError as exc:
        return fail("missing_profile_scores", str(exc), status=400)
    except ContentLoadError as exc:
        return fail("content_load_error", str(exc), status=500)
    saved = _save_profile_result(payload, result)
    result["assessment_result_id"] = saved.get("id")
    result["student_profile_id"] = saved.get("student_profile_id")
    result["saved_to_assessment_results"] = True
    result["saved_to_student_profiles"] = True
    return ok(result, status=201)


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

    return ok({"items": rows_to_dicts(rows)})


@bp.get("/profile-results/<profile_id>")
def get_profile_result(profile_id: str):
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM student_profiles WHERE id = ?", (profile_id,)).fetchone()
        if row is not None:
            conn.execute(
                """
                INSERT INTO audit_logs (id, actor_id, action, target_type, target_id, metadata_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    new_id("audit"),
                    "admin-token" if request.headers.get("X-Admin-Token") else "web-admin",
                    "view_profile",
                    "student_profile",
                    profile_id,
                    json_dumps({"route": "/api/profile-results/<id>"}),
                    now_iso(),
                ),
            )
            conn.commit()
    if row is None:
        return fail("not_found", "没有找到对应的学生画像结果", status=404)
    return ok(row_to_dict(row))


@bp.get("/model/info")
def model_info():
    try:
        rules_payload = load_student_profile_rules()
    except ContentLoadError as exc:
        return fail("content_load_error", str(exc), status=500)

    available_profiles = [
        {
            "profile_code": rule.get("profile_code"),
            "profile_name": rule.get("profile_name"),
            "enabled": rule.get("enabled", True),
            "risk_level": rule.get("risk_level", "low"),
        }
        for rule in rules_payload.get("rules", [])
    ]

    return ok(
        {
            "model_version": PROFILE_MODEL_VERSION,
            "rules_version": rules_payload.get("version"),
            "available_profiles": available_profiles,
            "boundary_notice": "学生画像只用于支持性理解和练习推荐，不构成临床诊断。",
        }
    )
