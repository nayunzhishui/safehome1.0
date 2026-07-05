"""Assessment worksheet endpoints."""

import json

from flask import Blueprint, request

from database import ensure_user, get_connection, json_dumps, json_loads, load_content_json, new_id, now_iso, row_to_dict, rows_to_dicts
from routes.utils import fail, ok, parse_int, require_fields, require_user_id, resolve_user_id_for_query
from services.assessment_profile_service import ProfilePositionUnavailable, build_assessment_profile_position
from services.risk_review_service import create_risk_review_record
from services.risk_service import check_text_risk
from services.training_recommendation_service import evaluate_training_rules, flatten_card_ids

bp = Blueprint("assessments", __name__, url_prefix="/api")


def _load_payload() -> dict:
    return load_content_json("assessment_worksheets.json")


def _load_assessment_training_map() -> dict:
    return load_content_json("assessment_training_map.json")


def _worksheets() -> list[dict]:
    try:
        with get_connection() as conn:
            worksheets = _worksheets_from_db(conn)
            if worksheets:
                return worksheets
    except Exception:
        pass
    return _load_payload().get("worksheets", [])


def _worksheets_from_db(conn, include_disabled: bool = True) -> list[dict]:
    where = "" if include_disabled else "WHERE enabled_for_user = 1"
    try:
        rows = conn.execute(
            f"""
            SELECT * FROM assessment_worksheets
            {where}
            ORDER BY display_title
            """
        ).fetchall()
    except Exception:
        return []
    return [_db_row_to_worksheet(row_to_dict(row)) for row in rows]


def _json_field(row: dict, key: str, fallback):
    try:
        return json_loads(row.get(key), fallback)
    except (TypeError, json.JSONDecodeError):
        return fallback


def _db_row_to_worksheet(row: dict) -> dict:
    return {
        "id": row.get("id"),
        "display_title": row.get("display_title"),
        "source_title": row.get("source_title"),
        "source_file": row.get("source_file"),
        "category": row.get("category"),
        "audience_class": row.get("audience_class"),
        "reflex_node": row.get("reflex_node"),
        "questions": _json_field(row, "questions_json", []),
        "dimensions": _json_field(row, "dimensions_json", []),
        "dimension_score_method": row.get("dimension_score_method") or "sum",
        "scoring_notes": _json_field(row, "scoring_notes_json", {}),
        "search_keywords": _json_field(row, "search_keywords_json", []),
        "boundary_notice": row.get("boundary_notice"),
        "result_disclaimer": row.get("result_disclaimer"),
        "instructions": row.get("instructions"),
        "sensitive_category": row.get("sensitive_category") or "none",
        "profile_model_id": row.get("profile_model_id"),
        "enabled_for_user": bool(row.get("enabled_for_user", 1)),
        "review_status": row.get("review_status"),
        "review_note": row.get("review_note"),
        "source_version": row.get("source_version"),
        "source_type": row.get("source_type"),
        "audience": row.get("audience"),
        "audience_class_detail": row.get("audience_class_detail"),
        "recommended_card_ids": _json_field(row, "recommended_card_ids_json", []),
        "sections": _json_field(row, "sections_json", []),
        "scoring": row.get("scoring"),
        "pages": row.get("pages"),
        "_meta": _json_field(row, "_meta_json", {}),
    }


def _active_worksheet_ids() -> list[str]:
    return [worksheet["id"] for worksheet in _worksheets() if worksheet.get("id") and worksheet.get("enabled_for_user", True)]


def _profile_cluster_value(position: dict | None) -> int | None:
    cluster_id = (position or {}).get("cluster_id")
    if cluster_id is None or cluster_id == "":
        return None
    try:
        return int(cluster_id)
    except (TypeError, ValueError):
        return None


def _expand_result_row(row: dict) -> dict:
    row["answers"] = json_loads(row.get("answers_json"), [])
    row["scores"] = json_loads(row.get("scores_json"), {})
    row["profile_cluster_id"] = _profile_cluster_value({"cluster_id": row.get("profile_cluster_id")})
    return row


def _backfill_profile_position(conn, result_id: str, position: dict) -> None:
    position_data = position.get("position") or {}
    conn.execute(
        """
        UPDATE assessment_results SET
            profile_model_id = ?,
            profile_cluster_id = ?,
            profile_pc1 = ?,
            profile_pc2 = ?,
            profile_confidence = ?
        WHERE id = ?
        """,
        (
            position.get("model_id"),
            _profile_cluster_value(position_data),
            position_data.get("pc1"),
            position_data.get("pc2"),
            position_data.get("confidence"),
            result_id,
        ),
    )


def _find_worksheet(worksheet_id: str, include_disabled: bool = False) -> dict | None:
    for worksheet in _worksheets():
        if worksheet.get("id") == worksheet_id:
            if not include_disabled and not worksheet.get("enabled_for_user", True):
                return None
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
        "audience": worksheet.get("audience"),
        "audience_class": worksheet.get("audience_class"),
        "reflex_node": worksheet.get("reflex_node"),
        "search_keywords": worksheet.get("search_keywords", []),
        "sensitive_category": worksheet.get("sensitive_category", "none"),
        "result_disclaimer": worksheet.get("result_disclaimer"),
        "boundary_notice": worksheet.get("boundary_notice"),
        "profile_model_id": worksheet.get("profile_model_id"),
        "review_status": worksheet.get("review_status"),
        "enabled_for_user": worksheet.get("enabled_for_user", True),
        "review_note": worksheet.get("review_note"),
        "question_count": len(worksheet.get("questions", [])),
        "is_reference": worksheet.get("category") == "示例参考",
    }


def _option_score_bounds(question: dict) -> tuple[int, int] | None:
    scores = [option.get("score") for option in question.get("options", []) if isinstance(option.get("score"), (int, float))]
    if not scores:
        return None
    return int(min(scores)), int(max(scores))


def _effective_score(question: dict | None, score: int) -> int:
    # 反向计分题（如 PRFQ11、PRFQ18）按量表上下界翻转：effective = (min + max) - 原分。
    if question and question.get("reverse_scored"):
        bounds = _option_score_bounds(question)
        if bounds:
            low, high = bounds
            return low + high - score
    return score


def _score_answers(worksheet: dict, answers: list[dict]) -> tuple[dict, int | None]:
    question_map = {question.get("id"): question for question in worksheet.get("questions", [])}
    score_method = worksheet.get("dimension_score_method", "sum")
    total = 0
    has_score = False
    dimension_totals: dict[str, dict] = {}

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
            # answer 里保留用户实际选择的原始分，便于审计；维度和总分用反向计分后的有效分。
            answer["score"] = int(score)
            effective = _effective_score(question, int(score))
            total += effective
            has_score = True
            dimension = question.get("dimension") if question else None
            if dimension:
                bucket = dimension_totals.setdefault(dimension, {"score": 0, "item_count": 0})
                bucket["score"] += effective
                bucket["item_count"] += 1

    dimension_labels = _dimension_labels(worksheet)
    dimensions = []
    for dimension, bucket in dimension_totals.items():
        item_count = bucket["item_count"]
        if score_method == "mean" and item_count:
            value: int | float = round(bucket["score"] / item_count, 2)
        else:
            value = bucket["score"]
        dimensions.append(
            {
                "key": dimension,
                "label": dimension_labels.get(dimension, dimension),
                "score": value,
                "item_count": item_count,
                "score_method": score_method,
            }
        )

    scores: dict = {"total_score": total if has_score else None}
    # 维度分单独保存供结果页、画像候选和导出使用；总分不替代维度解释。
    if dimensions:
        scores["dimensions"] = dimensions

    return scores, total if has_score else None


def _dimension_labels(worksheet: dict) -> dict[str, str]:
    labels: dict[str, str] = {}
    for dimension in worksheet.get("dimensions", []) or []:
        if isinstance(dimension, dict):
            code = dimension.get("code") or dimension.get("key")
            label = dimension.get("label")
            if code and label:
                labels[code] = label
    return labels


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
    audience_class = request.args.get("audience_class")
    reflex_node = request.args.get("reflex_node")
    enabled = request.args.get("enabled")
    query = (request.args.get("q") or request.args.get("query") or "").strip().lower()
    items = [_summarize_worksheet(item) for item in _worksheets()]
    if category:
        items = [item for item in items if item.get("category") == category]
    if audience_class:
        items = [item for item in items if item.get("audience_class") == audience_class]
    if reflex_node:
        items = [item for item in items if item.get("reflex_node") == reflex_node]
    items = [item for item in items if bool(item.get("enabled_for_user", True))]
    if query:
        items = [
            item
            for item in items
            if query
            in " ".join(
                str(part)
                for part in [
                    item.get("id"),
                    item.get("display_title"),
                    item.get("source_title"),
                    item.get("category"),
                    item.get("audience_class"),
                    item.get("reflex_node"),
                    " ".join(item.get("search_keywords", [])),
                ]
            ).lower()
        ]
    groups: dict[str, dict] = {}
    for item in items:
        group_key = item.get("audience_class") or "uncategorized"
        node_key = item.get("reflex_node") or "uncategorized"
        group = groups.setdefault(group_key, {"key": group_key, "count": 0, "nodes": {}})
        group["count"] += 1
        node = group["nodes"].setdefault(node_key, {"key": node_key, "count": 0})
        node["count"] += 1
    group_items = [
        {**group, "nodes": list(group["nodes"].values())}
        for group in groups.values()
    ]
    return ok(
        {
            "version": payload.get("version"),
            "boundary_notice": payload.get("boundary_notice"),
            "items": items,
            "groups": group_items,
        }
    )


@bp.get("/assessments/<worksheet_id>")
def get_assessment(worksheet_id: str):
    worksheet = _find_worksheet(worksheet_id)
    if worksheet is None:
        return fail("not_found", "没有找到对应的测一测内容", status=404)
    payload = _load_payload()
    return ok(
        {
            **worksheet,
            "boundary_notice": worksheet.get("boundary_notice") or payload.get("boundary_notice"),
            "result_disclaimer": worksheet.get("result_disclaimer") or payload.get("boundary_notice"),
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
    text_values = [
        str(answer.get("value", "")).strip()
        for answer in answers
        if str(answer.get("value", "")).strip()
        and not isinstance(answer.get("score"), (int, float))
    ]
    risk_result = check_text_risk(text_values, source="assessment") if text_values else None
    if risk_result:
        scores["risk"] = {
            "risk_level": risk_result.get("risk_level"),
            "requires_review": risk_result.get("requires_review"),
            "allow_recommended_training_cards": risk_result.get("allow_recommended_training_cards"),
        }
    timestamp = now_iso()
    result_id = new_id("assessment")
    result_summary = payload.get("result_summary") or worksheet.get("result_disclaimer") or "本次内容已保存。结果仅用于自我观察和练习记录，不构成诊断。"
    if risk_result and not risk_result.get("allow_auto_feedback", True):
        result_summary = risk_result.get("safe_response") or result_summary

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
        create_risk_review_record(conn, user_id, "assessment_result", result_id, risk_result)
        conn.commit()
        row = conn.execute("SELECT * FROM assessment_results WHERE id = ?", (result_id,)).fetchone()
        result_row = row_to_dict(row)
        if result_row:
            result_row["answers"] = answers
            try:
                position = build_assessment_profile_position(result_row, worksheet)
                _backfill_profile_position(conn, result_id, position)
                conn.commit()
                row = conn.execute("SELECT * FROM assessment_results WHERE id = ?", (result_id,)).fetchone()
            except ProfilePositionUnavailable:
                pass

    result = row_to_dict(row)
    result["answers"] = answers
    result["scores"] = scores
    training_rules = evaluate_training_rules(worksheet["id"], scores, worksheet=worksheet, risk_result=risk_result)
    recommended_card_ids = flatten_card_ids(training_rules) or worksheet.get("recommended_card_ids", [])
    if risk_result and not risk_result.get("allow_recommended_training_cards", True):
        recommended_card_ids = []
        training_rules = []
    result["recommended_card_ids"] = recommended_card_ids
    result["training_recommendation_rules"] = training_rules
    result["risk"] = risk_result
    result["boundary_notice"] = worksheet.get("boundary_notice")
    result["result_disclaimer"] = worksheet.get("result_disclaimer")
    return ok(result, status=201)


@bp.get("/assessment-results")
def list_assessment_results():
    try:
        user_id = resolve_user_id_for_query(request.args.get("user_id"))
    except ValueError as exc:
        return fail("validation_error", str(exc), status=400)
    limit = parse_int(request.args.get("limit"), 50)
    active_worksheet_ids = _active_worksheet_ids()
    if not active_worksheet_ids:
        return ok({"items": []})
    placeholders = ", ".join("?" for _ in active_worksheet_ids)

    with get_connection() as conn:
        rows = conn.execute(
            f"""
            SELECT * FROM assessment_results
            WHERE user_id = ?
              AND worksheet_id IN ({placeholders})
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (user_id, *active_worksheet_ids, limit),
        ).fetchall()

    return ok({"items": [_expand_result_row(row) for row in rows_to_dicts(rows)]})


@bp.get("/assessment-results/<result_id>/profile-position")
def get_assessment_profile_position(result_id: str):
    try:
        user_id = resolve_user_id_for_query(request.args.get("user_id"))
    except ValueError as exc:
        return fail("validation_error", str(exc), status=400)

    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT * FROM assessment_results
            WHERE id = ? AND user_id = ?
            """,
            (result_id, user_id),
        ).fetchone()

        if row is None:
            return fail("not_found", "没有找到对应的测一测结果", status=404)

        result = row_to_dict(row)
        worksheet = _find_worksheet(result.get("worksheet_id"))
        if worksheet is None:
            return ok(
                {
                    "available": False,
                    "reason": "这条结果对应的测评内容已不在当前内容库中。",
                }
            )

        try:
            position = build_assessment_profile_position(
                result,
                worksheet,
                requested_model_id=request.args.get("model_id"),
            )
            _backfill_profile_position(conn, result_id, position)
            conn.commit()
        except ProfilePositionUnavailable as exc:
            return ok({"available": False, "reason": exc.reason})

    return ok(position)
