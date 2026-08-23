"""Admin export endpoints for MVP data review."""

import csv
import hashlib
import json
from io import StringIO

from flask import Blueprint, Response, request

from database import get_connection, json_dumps, json_loads, load_content_json, now_iso, write_audit_log
from routes.auth_utils import AuthError, auth_error_response, require_capability, require_role
from services.privacy_request_service import research_revoked_filter
from routes.utils import fail, ok, parse_bool, parse_int
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
DEFAULT_EXPORT_LIMIT = 1000
MAX_EXPORT_LIMIT = 5000
CSV_FORMULA_PREFIXES = ("=", "+", "-", "@", "\t", "\r")

WORKSHEET_WRITABLE_FIELDS = {
    "display_title",
    "source_title",
    "source_file",
    "category",
    "audience_class",
    "reflex_node",
    "questions",
    "dimensions",
    "dimension_score_method",
    "scoring_notes",
    "search_keywords",
    "boundary_notice",
    "result_disclaimer",
    "instructions",
    "sensitive_category",
    "profile_model_id",
    "enabled_for_user",
    "review_status",
    "review_note",
    "source_version",
    "source_type",
    "audience",
    "audience_class_detail",
    "recommended_card_ids",
    "sections",
    "scoring",
    "pages",
    "_meta",
}


def _csv_safe_cell(value):
    """Prevent spreadsheet formula execution without changing non-string values."""
    if not isinstance(value, str):
        return value
    candidate = value.lstrip(" ")
    if candidate.startswith(CSV_FORMULA_PREFIXES):
        return "'" + value
    return value


def _worksheet_json(value: str | None, fallback):
    try:
        return json_loads(value, fallback)
    except (TypeError, json.JSONDecodeError):
        return fallback


def _worksheet_from_row(row) -> dict:
    item = dict(row)
    return {
        "id": item.get("id"),
        "display_title": item.get("display_title"),
        "source_title": item.get("source_title"),
        "source_file": item.get("source_file"),
        "category": item.get("category"),
        "audience_class": item.get("audience_class"),
        "reflex_node": item.get("reflex_node"),
        "questions": _worksheet_json(item.get("questions_json"), []),
        "dimensions": _worksheet_json(item.get("dimensions_json"), []),
        "dimension_score_method": item.get("dimension_score_method"),
        "scoring_notes": _worksheet_json(item.get("scoring_notes_json"), {}),
        "search_keywords": _worksheet_json(item.get("search_keywords_json"), []),
        "boundary_notice": item.get("boundary_notice"),
        "result_disclaimer": item.get("result_disclaimer"),
        "instructions": item.get("instructions"),
        "sensitive_category": item.get("sensitive_category"),
        "profile_model_id": item.get("profile_model_id"),
        "enabled_for_user": bool(item.get("enabled_for_user", 1)),
        "review_status": item.get("review_status"),
        "review_note": item.get("review_note"),
        "source_version": item.get("source_version"),
        "source_type": item.get("source_type"),
        "audience": item.get("audience"),
        "audience_class_detail": item.get("audience_class_detail"),
        "recommended_card_ids": _worksheet_json(item.get("recommended_card_ids_json"), []),
        "sections": _worksheet_json(item.get("sections_json"), []),
        "scoring": item.get("scoring"),
        "pages": item.get("pages"),
        "_meta": _worksheet_json(item.get("_meta_json"), {}),
        "created_at": item.get("created_at"),
        "updated_at": item.get("updated_at"),
    }


def _worksheet_db_values(payload: dict, timestamp: str, created_at: str | None = None) -> dict:
    return {
        "id": payload["id"],
        "display_title": payload.get("display_title") or payload.get("source_title") or payload["id"],
        "source_title": payload.get("source_title"),
        "source_file": payload.get("source_file"),
        "category": payload.get("category"),
        "audience_class": payload.get("audience_class"),
        "reflex_node": payload.get("reflex_node"),
        "questions_json": json_dumps(payload.get("questions", [])),
        "dimensions_json": json_dumps(payload.get("dimensions", [])),
        "dimension_score_method": payload.get("dimension_score_method") or "sum",
        "scoring_notes_json": json_dumps(payload.get("scoring_notes", {})),
        "search_keywords_json": json_dumps(payload.get("search_keywords", [])),
        "boundary_notice": payload.get("boundary_notice"),
        "result_disclaimer": payload.get("result_disclaimer"),
        "instructions": payload.get("instructions"),
        "sensitive_category": str(payload.get("sensitive_category") or "none"),
        "profile_model_id": payload.get("profile_model_id"),
        "enabled_for_user": 1 if payload.get("enabled_for_user", True) else 0,
        "review_status": payload.get("review_status") or "approved",
        "review_note": payload.get("review_note"),
        "source_version": payload.get("source_version"),
        "source_type": payload.get("source_type"),
        "audience": payload.get("audience"),
        "audience_class_detail": payload.get("audience_class_detail"),
        "recommended_card_ids_json": json_dumps(payload.get("recommended_card_ids", [])),
        "sections_json": json_dumps(payload.get("sections", [])),
        "scoring": payload.get("scoring"),
        "pages": payload.get("pages"),
        "_meta_json": json_dumps(payload.get("_meta", {})),
        "created_at": created_at or timestamp,
        "updated_at": timestamp,
    }


def _save_worksheet(conn, payload: dict, created_at: str | None = None) -> dict:
    timestamp = now_iso()
    row = _worksheet_db_values(payload, timestamp, created_at=created_at)
    columns = list(row.keys())
    placeholders = ", ".join("?" for _ in columns)
    column_sql = ", ".join(columns)
    update_columns = [column for column in columns if column not in {"id", "created_at"}]
    params = [row[column] for column in columns]
    if getattr(conn, "provider", "sqlite") == "mysql":
        updates = ", ".join(f"{column}=VALUES({column})" for column in update_columns)
        conn.execute(
            f"""
            INSERT INTO assessment_worksheets ({column_sql})
            VALUES ({placeholders})
            ON DUPLICATE KEY UPDATE {updates}
            """,
            params,
        )
    else:
        updates = ", ".join(f"{column}=excluded.{column}" for column in update_columns)
        conn.execute(
            f"""
            INSERT INTO assessment_worksheets ({column_sql})
            VALUES ({placeholders})
            ON CONFLICT(id) DO UPDATE SET {updates}
            """,
            params,
        )
    saved = conn.execute("SELECT * FROM assessment_worksheets WHERE id = ?", (payload["id"],)).fetchone()
    return _worksheet_from_row(saved)


def _requested_enabled_true(payload: dict) -> bool:
    if "enabled_for_user" not in payload:
        return False
    value = payload.get("enabled_for_user")
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y", "是", "开放"}
    return bool(value)


def _parse_export_limit(value: str | None) -> tuple[int | None, tuple | None]:
    if value in (None, ""):
        return DEFAULT_EXPORT_LIMIT, None
    try:
        limit = int(value)
    except (TypeError, ValueError):
        return None, fail("invalid_export_limit", "limit 必须是整数", status=400)
    if limit <= 0:
        return None, fail("invalid_export_limit", "limit 必须大于 0", status=400)
    if limit > MAX_EXPORT_LIMIT:
        return None, fail("invalid_export_limit", "limit 不能超过 5000", status=400)
    return limit, None


def _fetch_limited_rows(conn, base_sql: str, params: list | tuple | None, limit: int):
    params = list(params or [])
    count_row = conn.execute(f"SELECT COUNT(*) AS count FROM ({base_sql}) AS export_source", params).fetchone()
    rows = conn.execute(f"{base_sql} LIMIT ?", [*params, limit]).fetchall()
    return rows, count_row["count"]


def _active_assessment_ids() -> list[str]:
    payload = load_content_json("assessment_worksheets.json")
    return [item["id"] for item in payload.get("worksheets", []) if isinstance(item, dict) and item.get("id")]


def _append_research_consent_filter(conn, where_clauses: list[str], params: list, column: str = "user_id") -> None:
    clause, clause_params = research_revoked_filter(conn, column)
    if clause:
        where_clauses.append(clause)
        params.extend(clause_params)


def _anonymous_id(user_id: str) -> str:
    digest = hashlib.sha256(user_id.encode("utf-8")).hexdigest()[:12]
    return f"anon_{digest}"


def _value_hash(value: str | None) -> str:
    if not value:
        return ""
    return hashlib.sha256(str(value).encode("utf-8")).hexdigest()[:12]


def _safe_text_length(value) -> int:
    return len(str(value or ""))


def _json_list_count(value) -> int:
    parsed = _loads(value, [])
    return len(parsed) if isinstance(parsed, list) else 0


def _json_dict_keys(value) -> str:
    parsed = _loads(value, {})
    if not isinstance(parsed, dict):
        return ""
    return ",".join(sorted(str(key) for key in parsed.keys()))


def _goal_export_rows(rows) -> list[dict]:
    return [
        {
            "id": row["id"],
            "anonymous_id": _anonymous_id(row["user_id"]),
            "scene": row["scene"],
            "status": row["status"],
            "smart_goal_length": _safe_text_length(row["smart_goal"]),
            "motivation_length": _safe_text_length(row["motivation"]),
            "start_date": row["start_date"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }
        for row in rows
    ]


def _diary_export_rows(rows) -> list[dict]:
    return [
        {
            "id": row["id"],
            "anonymous_id": _anonymous_id(row["user_id"]),
            "goal_id": row["goal_id"],
            "event_time": row["event_time"],
            "scene": row["scene"],
            "parent_emotion": row["parent_emotion"],
            "parent_emotion_intensity": row["parent_emotion_intensity"],
            "child_emotion": row["child_emotion"],
            "child_emotion_intensity": row["child_emotion_intensity"],
            "event_description_length": _safe_text_length(row["event_description"]),
            "automatic_thought_length": _safe_text_length(row["automatic_thought"]),
            "body_sensation_length": _safe_text_length(row["body_sensation"]),
            "behavior_length": _safe_text_length(row["behavior"]),
            "raw_text_length": _safe_text_length(row["raw_text"]),
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }
        for row in rows
    ]


def _feedback_export_rows(rows) -> list[dict]:
    return [
        {
            "id": row["id"],
            "anonymous_id": _anonymous_id(row["user_id"] or ""),
            "diary_id": row["diary_id"],
            "tags_count": _json_list_count(row["tags_json"]),
            "tags_json": row["tags_json"],
            "trigger_summary_length": _safe_text_length(row["trigger_summary"]),
            "pattern_summary_length": _safe_text_length(row["pattern_summary"]),
            "supportive_feedback_length": _safe_text_length(row["supportive_feedback"]),
            "alternative_response_length": _safe_text_length(row["alternative_response"]),
            "recommended_card_ids_json": row["recommended_card_ids_json"],
            "risk_level": row["risk_level"],
            "created_at": row["created_at"],
        }
        for row in rows
    ]


def _checkin_export_rows(rows) -> list[dict]:
    return [
        {
            "id": row["id"],
            "anonymous_id": _anonymous_id(row["user_id"]),
            "card_id": row["card_id"],
            "diary_id": row["diary_id"],
            "completed": row["completed"],
            "emotion_before": row["emotion_before"],
            "emotion_after": row["emotion_after"],
            "reflection_length": _safe_text_length(row["reflection"]),
            "created_at": row["created_at"],
        }
        for row in rows
    ]


def _assessment_export_rows(rows) -> list[dict]:
    return [
        {
            "id": row["id"],
            "anonymous_id": _anonymous_id(row["user_id"]),
            "worksheet_id": row["worksheet_id"],
            "worksheet_title": row["worksheet_title"],
            "category": row["category"],
            "answers_count": _json_list_count(row["answers_json"]),
            "scores_keys": _json_dict_keys(row["scores_json"]),
            "total_score": row["total_score"],
            "result_summary_length": _safe_text_length(row["result_summary"]),
            "created_at": row["created_at"],
        }
        for row in rows
    ]


def _weekly_report_export_rows(rows) -> list[dict]:
    return [
        {
            "id": row["id"],
            "anonymous_id": _anonymous_id(row["user_id"]),
            "week_start": row["week_start"],
            "week_end": row["week_end"],
            "frequent_scenes_count": _json_list_count(row["frequent_scenes_json"]),
            "frequent_emotions_count": _json_list_count(row["frequent_emotions_json"]),
            "common_patterns_count": _json_list_count(row["common_patterns_json"]),
            "completed_cards_count": _json_list_count(row["completed_cards_json"]),
            "next_week_suggestion_length": _safe_text_length(row["next_week_suggestion"]),
            "created_at": row["created_at"],
        }
        for row in rows
    ]


def _supervision_export_rows(rows) -> list[dict]:
    return [
        {
            "id": row["id"],
            "anonymous_id": _anonymous_id(row["user_id"]),
            "diary_id": row["diary_id"],
            "message_length": _safe_text_length(row["message"]),
            "contact_length": _safe_text_length(row["contact"]),
            "risk_hint_length": _safe_text_length(row["risk_hint"]),
            "risk_level": row["risk_level"],
            "status": row["status"],
            "supervisor_reply_length": _safe_text_length(row["supervisor_reply"]),
            "created_at": row["created_at"],
            "replied_at": row["replied_at"],
        }
        for row in rows
    ]


def _cards_export_rows(rows) -> list[dict]:
    return [
        {
            "id": row["id"],
            "type": row["type"],
            "title": row["title"],
            "tags_json": row["tags_json"],
            "enabled": row["enabled"],
            "version": row["version"],
            "duration_minutes": row["duration_minutes"],
            "steps_count": _json_list_count(row["steps_json"]),
            "purpose_length": _safe_text_length(row["purpose"]),
            "example_length": _safe_text_length(row["example"]),
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }
        for row in rows
    ]


EXPORT_ROW_TRANSFORMS = {
    "goals": _goal_export_rows,
    "diaries": _diary_export_rows,
    "feedback": _feedback_export_rows,
    "checkins": _checkin_export_rows,
    "assessments": _assessment_export_rows,
    "reports": _weekly_report_export_rows,
    "supervision": _supervision_export_rows,
    "cards": _cards_export_rows,
}


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
        report = _loads(item.get("report_json"), {})
        consent_summary = report.get("consent_summary", {}) if isinstance(report, dict) else {}
        research_consent = consent_summary.get("research_authorization", {}) if isinstance(consent_summary, dict) else {}
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
                "research_authorization_status": research_consent.get("status"),
                "consent_summary_json": json.dumps(consent_summary, ensure_ascii=False),
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
        recommended_card_ids = data.get("recommended_card_ids") or data.get("recommended_task_ids") or []
        if not isinstance(recommended_card_ids, list):
            recommended_card_ids = []
        export_rows.append(
            {
                "id": item.get("id"),
                "anonymous_id": data.get("anonymous_id") or _anonymous_id(item.get("user_id") or ""),
                "module_type": item.get("module_type"),
                "source_id": item.get("source_id"),
                "risk_level": data.get("risk_level", ""),
                "requires_review": 1 if data.get("requires_review") else 0,
                "profile_code": data.get("profile_code", ""),
                "profile_name": data.get("profile_name", ""),
                "recommended_card_ids": ",".join(str(card_id) for card_id in recommended_card_ids),
                "data_keys": ",".join(sorted(str(key) for key in data.keys())),
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
                "research_consent_status": "agreed" if row["research_consent"] else "declined",
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


@bp.get("/worksheets")
def list_admin_worksheets():
    try:
        require_role("admin", allow_legacy_admin=True)
    except AuthError as exc:
        return auth_error_response(exc)
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM assessment_worksheets ORDER BY updated_at DESC").fetchall()
    return ok({"items": [_worksheet_from_row(row) for row in rows], "count": len(rows)})


@bp.post("/worksheets")
def create_admin_worksheet():
    try:
        actor = require_role("admin", allow_legacy_admin=True)
    except AuthError as exc:
        return auth_error_response(exc)
    payload = request.get_json(silent=True) or {}
    if not payload.get("id"):
        return fail("missing_fields", "缺少必填字段：id", status=400)
    if _requested_enabled_true(payload):
        return fail(
            "review_required",
            "测评题库管理不能直接开放用户端入口。请先保存为待复核，再通过内容审核流程开放。",
            status=400,
        )
    payload = {**payload, "enabled_for_user": False, "review_status": payload.get("review_status") or "pilot_review_required"}
    with get_connection() as conn:
        existing = conn.execute("SELECT id FROM assessment_worksheets WHERE id = ?", (payload["id"],)).fetchone()
        if existing:
            return fail("worksheet_exists", "该测评 ID 已存在，请改用更新接口。", status=409)
        saved = _save_worksheet(conn, payload)
        write_audit_log(
            conn,
            action="create_assessment_worksheet",
            actor_id=actor["id"],
            target_type="assessment_worksheet",
            target_id=payload["id"],
            metadata={"review_status": saved.get("review_status"), "enabled_for_user": saved.get("enabled_for_user")},
        )
        conn.commit()
    return ok(saved, status=201)


@bp.put("/worksheets/<worksheet_id>")
def update_admin_worksheet(worksheet_id: str):
    try:
        actor = require_role("admin", allow_legacy_admin=True)
    except AuthError as exc:
        return auth_error_response(exc)
    payload = request.get_json(silent=True) or {}
    update_payload = {key: value for key, value in payload.items() if key in WORKSHEET_WRITABLE_FIELDS}
    if not update_payload:
        return fail("missing_fields", "没有可更新的字段", status=400)
    if _requested_enabled_true(update_payload):
        return fail(
            "review_required",
            "测评题库管理不能直接把测评开放到用户端。请通过内容审核流程开放。",
            status=400,
        )
    with get_connection() as conn:
        existing = conn.execute("SELECT * FROM assessment_worksheets WHERE id = ?", (worksheet_id,)).fetchone()
        if existing is None:
            return fail("not_found", "没有找到对应测评。", status=404)
        merged = {**_worksheet_from_row(existing), **update_payload, "id": worksheet_id}
        saved = _save_worksheet(conn, merged, created_at=existing["created_at"])
        write_audit_log(
            conn,
            action="update_assessment_worksheet",
            actor_id=actor["id"],
            target_type="assessment_worksheet",
            target_id=worksheet_id,
            metadata={"fields": sorted(update_payload.keys())},
        )
        conn.commit()
    return ok(saved)


@bp.delete("/worksheets/<worksheet_id>")
def disable_admin_worksheet(worksheet_id: str):
    try:
        actor = require_role("admin", allow_legacy_admin=True)
    except AuthError as exc:
        return auth_error_response(exc)
    timestamp = now_iso()
    with get_connection() as conn:
        existing = conn.execute("SELECT * FROM assessment_worksheets WHERE id = ?", (worksheet_id,)).fetchone()
        if existing is None:
            return fail("not_found", "没有找到对应测评。", status=404)
        conn.execute(
            """
            UPDATE assessment_worksheets
            SET enabled_for_user = 0, review_status = 'disabled', updated_at = ?
            WHERE id = ?
            """,
            (timestamp, worksheet_id),
        )
        write_audit_log(
            conn,
            action="disable_assessment_worksheet",
            actor_id=actor["id"],
            target_type="assessment_worksheet",
            target_id=worksheet_id,
            metadata={"enabled_for_user": False, "review_status": "disabled"},
        )
        conn.commit()
        row = conn.execute("SELECT * FROM assessment_worksheets WHERE id = ?", (worksheet_id,)).fetchone()
    return ok(_worksheet_from_row(row))


def _assessment_result_from_row(row) -> dict:
    item = dict(row)
    item["answers"] = json_loads(item.get("answers_json"), [])
    item["scores"] = json_loads(item.get("scores_json"), {})
    if item.get("profile_cluster_id") in {"", None}:
        item["profile_cluster_id"] = None
    else:
        try:
            item["profile_cluster_id"] = int(item["profile_cluster_id"])
        except (TypeError, ValueError):
            item["profile_cluster_id"] = None
    return item


@bp.get("/assessment-results")
def list_admin_assessment_results():
    try:
        actor = require_capability("research.participant.read", allow_legacy_admin=True)
    except AuthError as exc:
        return auth_error_response(exc)

    limit = min(parse_int(request.args.get("limit"), 100), 500)
    worksheet_id = request.args.get("worksheet_id")
    profile_model_id = request.args.get("profile_model_id")
    where = []
    params: list = []
    if actor.get("role") in {"researcher", "supervisor"}:
        where.append(
            """
            user_id IN (
                SELECT enrollment.user_id
                FROM relationship_pilot_enrollments enrollment
                JOIN research_scope_assignments assignment
                  ON assignment.enrollment_id = enrollment.id
                WHERE assignment.actor_id = ?
                  AND assignment.assignment_role = ?
                  AND assignment.status = 'active'
                  AND (assignment.expires_at IS NULL OR assignment.expires_at > ?)
                  AND enrollment.status IN ('enrolled', 'active')
            )
            """
        )
        params.extend([str(actor["id"]), str(actor["role"]), now_iso()])
    if worksheet_id:
        where.append("worksheet_id = ?")
        params.append(worksheet_id)
    if profile_model_id:
        where.append("profile_model_id = ?")
        params.append(profile_model_id)
    where_sql = f"WHERE {' AND '.join(where)}" if where else ""
    params.append(limit)
    with get_connection() as conn:
        rows = conn.execute(
            f"""
            SELECT * FROM assessment_results
            {where_sql}
            ORDER BY created_at DESC
            LIMIT ?
            """,
            params,
        ).fetchall()
    return ok({"items": [_assessment_result_from_row(row) for row in rows], "count": len(rows)})


def _parent_raw_wide_rows(rows) -> list[dict]:
    item_codes = [item["item_code"] for item in _scale_items(load_parent_scales(), "parent_dual_scale")]
    export_rows = []
    for row in rows:
        answers = _loads(row["answers_json"], {}).get("scale_answers", {})
        export_row = {
            "id": row["id"],
            "anonymous_id": row["anonymous_id"],
            "participant_code_hash": _value_hash(row["participant_code"]),
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
                    "participant_code_hash": _value_hash(row["participant_code"]),
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
    export_type = request.args.get("type", "diaries")
    try:
        actor = require_capability("research.export", allow_legacy_admin=True)
    except AuthError as exc:
        return auth_error_response(exc)
    limit, limit_error = _parse_export_limit(request.args.get("limit"))
    if limit_error:
        return limit_error

    user_id = request.args.get("user_id")
    module_type = request.args.get("module_type")
    confirmed_high_risk_export = parse_bool(request.args.get("confirm_high_risk"), False)
    contains_high_risk = False
    row_count_before_limit = 0
    try:
        with get_connection() as conn:
            if export_type in PROFILE_EXPORT_TYPES:
                where_clauses = ["export_allowed = 1"]
                params = []
                _append_research_consent_filter(conn, where_clauses, params)
                if user_id:
                    where_clauses.append("user_id = ?")
                    params.append(user_id)
                rows, row_count_before_limit = _fetch_limited_rows(
                    conn,
                    f"""
                    SELECT * FROM student_profiles
                    WHERE {' AND '.join(where_clauses)}
                    ORDER BY created_at DESC
                    """,
                    params,
                    limit,
                )
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
                _append_research_consent_filter(conn, where_clauses, params)
                if user_id:
                    where_clauses.append("user_id = ?")
                    params.append(user_id)
                if module_type:
                    where_clauses.append("module_type = ?")
                    params.append(module_type)
                rows, row_count_before_limit = _fetch_limited_rows(
                    conn,
                    f"""
                    SELECT * FROM records
                    WHERE {' AND '.join(where_clauses)}
                    ORDER BY created_at DESC
                    """,
                    params,
                    limit,
                )
                contains_high_risk = _record_rows_contain_high_risk(rows)
                if contains_high_risk and not confirmed_high_risk_export:
                    return fail(
                        "high_risk_export_confirmation_required",
                        "本次导出包含高风险或需复核摘要，请确认高风险导出后重试。",
                        status=409,
                    )
                rows = _record_export_rows(rows)
            elif export_type == "student_followups":
                where_clauses = ["export_allowed = 1"]
                params = []
                _append_research_consent_filter(conn, where_clauses, params)
                if user_id:
                    where_clauses.append("user_id = ?")
                    params.append(user_id)
                rows, row_count_before_limit = _fetch_limited_rows(
                    conn,
                    f"""
                    SELECT * FROM student_profile_followups
                    WHERE {' AND '.join(where_clauses)}
                    ORDER BY created_at DESC
                    """,
                    params,
                    limit,
                )
                rows = _student_followup_rows(rows)
            elif export_type == "sandplay":
                where_clauses = ["export_allowed = 1"]
                params = []
                _append_research_consent_filter(conn, where_clauses, params)
                if user_id:
                    where_clauses.append("user_id = ?")
                    params.append(user_id)
                rows, row_count_before_limit = _fetch_limited_rows(
                    conn,
                    f"""
                    SELECT * FROM student_sandplay_entries
                    WHERE {' AND '.join(where_clauses)}
                    ORDER BY created_at DESC
                    """,
                    params,
                    limit,
                )
                rows = _sandplay_rows(rows)
            elif export_type == "parent_assessments":
                where_clauses = ["export_allowed = 1"]
                params = []
                _append_research_consent_filter(conn, where_clauses, params)
                if user_id:
                    where_clauses.append("user_id = ?")
                    params.append(user_id)
                rows, row_count_before_limit = _fetch_limited_rows(
                    conn,
                    f"""
                    SELECT * FROM parent_assessment_submissions
                    WHERE {' AND '.join(where_clauses)}
                    ORDER BY created_at DESC
                    """,
                    params,
                    limit,
                )
                rows = _parent_export_rows(rows)
            elif export_type in {"raw_wide", "long"}:
                where_clauses = ["research_consent = 1", "export_allowed = 1"]
                params = []
                _append_research_consent_filter(conn, where_clauses, params)
                rows, row_count_before_limit = _fetch_limited_rows(
                    conn,
                    f"""
                    SELECT * FROM parent_assessment_submissions
                    WHERE {' AND '.join(where_clauses)}
                    ORDER BY created_at DESC
                    """,
                    params,
                    limit,
                )
                rows = _parent_raw_wide_rows(rows) if export_type == "raw_wide" else _parent_long_rows(rows)
                if len(rows) > limit:
                    row_count_before_limit = len(rows)
                    rows = rows[:limit]
            elif export_type == "codebook":
                rows = _codebook_rows()
                row_count_before_limit = len(rows)
                rows = rows[:limit]
            else:
                table = EXPORT_TABLES.get(export_type)
                if table is None:
                    return fail(
                        "invalid_export_type",
                        "支持的 type：goals, diaries, feedback, checkins, assessments, profile, student_profiles, records, student_followups, sandplay, parent_assessments, raw_wide, long, codebook, reports, supervision, cards",
                    )
                where_clauses = []
                params = []
                if user_id and table != "training_cards":
                    where_clauses.append("user_id = ?")
                    params.append(user_id)
                if export_type == "assessments":
                    active_assessment_ids = _active_assessment_ids()
                    if not active_assessment_ids:
                        where_clauses.append("1 = 0")
                    else:
                        placeholders = ", ".join("?" for _ in active_assessment_ids)
                        where_clauses.append(f"worksheet_id IN ({placeholders})")
                        params.extend(active_assessment_ids)
                where_sql = f" WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
                if params:
                    rows, row_count_before_limit = _fetch_limited_rows(
                        conn,
                        f"SELECT * FROM {table}{where_sql} ORDER BY created_at DESC",
                        params,
                        limit,
                    )
                elif where_clauses:
                    rows, row_count_before_limit = _fetch_limited_rows(
                        conn,
                        f"SELECT * FROM {table}{where_sql} ORDER BY created_at DESC",
                        [],
                        limit,
                    )
                else:
                    rows, row_count_before_limit = _fetch_limited_rows(
                        conn,
                        f"SELECT * FROM {table} ORDER BY created_at DESC",
                        [],
                        limit,
                    )
                transform = EXPORT_ROW_TRANSFORMS.get(export_type)
                if transform:
                    rows = transform(rows)

            write_audit_log(
                conn,
                action=f"export_{export_type}",
                actor_id=actor["id"],
                target_type="export",
                target_id=export_type,
                metadata={
                    "type": export_type,
                    "user_id_filter": user_id,
                    "module_type_filter": module_type,
                    "row_count": len(rows),
                    "limit": limit,
                    "row_count_before_limit": row_count_before_limit,
                    "row_count_exported": len(rows),
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
        writer.writerows(
            [{key: _csv_safe_cell(value) for key, value in dict(row).items()} for row in rows]
        )
    else:
        output.write("empty\n")

    csv_text = "\ufeff" + output.getvalue()
    return Response(
        csv_text,
        mimetype="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f"attachment; filename=safehome_{export_type}.csv",
            "X-Content-Type-Options": "nosniff",
            "Cache-Control": "no-store",
        },
    )
