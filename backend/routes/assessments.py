"""Assessment worksheet endpoints."""

import json

from flask import Blueprint, request

from database import get_connection, json_loads, load_content_json, row_to_dict, rows_to_dicts
from routes.auth_utils import AuthError, auth_error_response, resolve_actor_user_id
from routes.utils import fail, ok, parse_int, require_fields
from services.assessment_execution_service import AssessmentSubmissionError, submit_assessment
from services.assessment_profile_service import ProfilePositionUnavailable, build_assessment_profile_position

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

    submitted_answers = payload.get("answers")

    try:
        user_id = resolve_actor_user_id(payload=payload)
    except AuthError as exc:
        return auth_error_response(exc)
    try:
        result = submit_assessment(
            worksheet,
            submitted_answers,
            user_id=user_id,
            nickname=payload.get("nickname"),
            result_summary=payload.get("result_summary"),
        )
    except AssessmentSubmissionError as exc:
        return fail(exc.code, exc.message)
    return ok(result, status=201)


@bp.get("/assessment-results")
def list_assessment_results():
    try:
        user_id = resolve_actor_user_id(request.args.get("user_id"))
    except AuthError as exc:
        return auth_error_response(exc)
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
        user_id = resolve_actor_user_id(request.args.get("user_id"))
    except AuthError as exc:
        return auth_error_response(exc)

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
