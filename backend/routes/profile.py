"""Student profile and risk-check endpoints."""

from flask import Blueprint, request

from database import ensure_user, get_connection, json_dumps, new_id, now_iso, row_to_dict
from services.content_loader import ContentLoadError, load_student_profile_rules
from services.profile_service import PROFILE_MODEL_VERSION, ProfileInputError, generate_student_profile
from services.risk_service import check_text_risk
from routes.utils import fail, ok

bp = Blueprint("profile", __name__, url_prefix="/api")


PROFILE_WORKSHEET_ID = "student_profile_v1"
PROFILE_WORKSHEET_TITLE = "学生支持性画像测评"


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
    timestamp = now_iso()
    answers = _profile_answers(payload, result)
    scores = {
        "input_scores": _input_scores(payload),
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
        conn.commit()
        row = conn.execute("SELECT * FROM assessment_results WHERE id = ?", (result_id,)).fetchone()

    saved = row_to_dict(row) or {}
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
    result["saved_to_assessment_results"] = True
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
