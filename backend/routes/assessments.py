"""Assessment worksheet endpoints."""

from flask import Blueprint, request

from database import ensure_user, get_connection, json_dumps, load_content_json, new_id, now_iso, row_to_dict, rows_to_dicts
from routes.utils import fail, ok, parse_int, require_fields, require_user_id, resolve_user_id_for_query

bp = Blueprint("assessments", __name__, url_prefix="/api")


def _load_payload() -> dict:
    return load_content_json("assessment_worksheets.json")


def _load_assessment_training_map() -> dict:
    return load_content_json("assessment_training_map.json")


def _worksheets() -> list[dict]:
    return _load_payload().get("worksheets", [])


def _find_worksheet(worksheet_id: str) -> dict | None:
    for worksheet in _worksheets():
        if worksheet.get("id") == worksheet_id:
            return worksheet
    return None


def _summarize_worksheet(worksheet: dict) -> dict:
    return {
        "id": worksheet.get("id"),
        "source_file": worksheet.get("source_file"),
        "source_title": worksheet.get("source_title"),
        "display_title": worksheet.get("display_title"),
        "category": worksheet.get("category"),
        "pages": worksheet.get("pages"),
        "instructions": worksheet.get("instructions"),
        "source_version": worksheet.get("source_version"),
        "source_type": worksheet.get("source_type"),
        "review_status": worksheet.get("review_status"),
        "enabled_for_user": worksheet.get("enabled_for_user", True),
        "review_note": worksheet.get("review_note"),
        "question_count": len(worksheet.get("questions", [])),
        "is_reference": worksheet.get("category") == "示例参考",
    }


def _score_answers(worksheet: dict, answers: list[dict]) -> tuple[dict, int | None]:
    question_map = {question.get("id"): question for question in worksheet.get("questions", [])}
    total = 0
    has_score = False

    for answer in answers:
        question = question_map.get(answer.get("question_id"))
        selected_value = answer.get("value")
        score = answer.get("score")
        if score is None and question:
            for option in question.get("options", []):
                if str(option.get("value")) == str(selected_value):
                    score = option.get("score")
                    break
        if isinstance(score, (int, float)):
            answer["score"] = score
            total += int(score)
            has_score = True

    return {"total_score": total if has_score else None}, total if has_score else None


def _training_rules_for_worksheet(worksheet_id: str) -> list[dict]:
    try:
        payload = _load_assessment_training_map()
    except FileNotFoundError:
        return []

    matched_rules = []
    for rule in payload.get("rules", []):
        if not isinstance(rule, dict):
            continue
        condition = rule.get("trigger_condition") or {}
        if condition.get("worksheet_id") == worksheet_id or condition.get("scale_id") == worksheet_id:
            matched_rules.append(rule)
    return matched_rules


@bp.get("/assessments")
def list_assessments():
    payload = _load_payload()
    category = request.args.get("category")
    items = [_summarize_worksheet(item) for item in payload.get("worksheets", [])]
    if category:
        items = [item for item in items if item.get("category") == category]
    return ok({"version": payload.get("version"), "boundary_notice": payload.get("boundary_notice"), "items": items})


@bp.get("/assessments/<worksheet_id>")
def get_assessment(worksheet_id: str):
    worksheet = _find_worksheet(worksheet_id)
    if worksheet is None:
        return fail("not_found", "没有找到对应的测一测内容", status=404)
    payload = _load_payload()
    return ok(
        {
            **worksheet,
            "boundary_notice": payload.get("boundary_notice"),
            "training_recommendation_rules": _training_rules_for_worksheet(worksheet_id),
        }
    )


@bp.post("/assessment-results")
def create_assessment_result():
    payload = request.get_json(silent=True) or {}
    missing = require_fields(payload, ["worksheet_id", "answers"])
    if missing:
        return fail("missing_fields", f"缺少必填字段：{', '.join(missing)}")

    worksheet = _find_worksheet(payload["worksheet_id"])
    if worksheet is None:
        return fail("not_found", "没有找到对应的测一测内容", status=404)
    if worksheet.get("enabled_for_user") is False:
        return fail("assessment_not_enabled", "这份测一测内容仍在人工审核中，暂不开放填写。", status=400)

    answers = payload.get("answers")
    if not isinstance(answers, list):
        return fail("invalid_answers", "answers 必须是数组")

    try:
        user_id = require_user_id(payload)
    except ValueError as exc:
        return fail("validation_error", str(exc), status=400)
    scores, total_score = _score_answers(worksheet, answers)
    timestamp = now_iso()
    result_id = new_id("assessment")
    result_summary = payload.get("result_summary") or "本次内容已保存。结果仅用于自我观察和练习记录，不构成诊断。"

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
                worksheet["id"],
                worksheet.get("display_title") or worksheet.get("source_title") or worksheet["id"],
                worksheet.get("category"),
                json_dumps(answers),
                json_dumps(scores),
                total_score,
                result_summary,
                timestamp,
            ),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM assessment_results WHERE id = ?", (result_id,)).fetchone()

    result = row_to_dict(row)
    result["answers"] = answers
    result["scores"] = scores
    result["recommended_card_ids"] = worksheet.get("recommended_card_ids", [])
    return ok(result, status=201)


@bp.get("/assessment-results")
def list_assessment_results():
    try:
        user_id = resolve_user_id_for_query(request.args.get("user_id"))
    except ValueError as exc:
        return fail("validation_error", str(exc), status=400)
    limit = parse_int(request.args.get("limit"), 50)

    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT * FROM assessment_results
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (user_id, limit),
        ).fetchall()

    return ok({"items": rows_to_dicts(rows)})
