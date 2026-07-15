"""Personalized training plan endpoints built from assessments and profile clusters."""

import json
from pathlib import Path
import re

from flask import Blueprint, current_app, request

from database import (
    get_connection,
    json_dumps,
    json_loads,
    load_content_json,
    new_id,
    now_iso,
    row_to_dict,
    rows_to_dicts,
    write_audit_log,
)
from routes.auth_utils import AuthError, auth_error_response, resolve_actor_user_id
from routes.utils import fail, ok
from services.training_recommendation_service import evaluate_training_rules, flatten_card_ids


bp = Blueprint("training_plan", __name__, url_prefix="/api/training-plan")
ASSIGNMENT_MODULE_TYPE = "training_plan_assignment"
ASSIGNMENT_SOURCE_ID = "current"
ASSIGNMENT_PHASES = {"start", "practice", "consolidate"}
ASSIGNMENT_CADENCES = {"daily", "every_other_day", "three_per_week", "weekly"}
ASSIGNMENT_STATUSES = {"active", "paused", "completed"}
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _worksheet_map() -> dict[str, dict]:
    payload = load_content_json("assessment_worksheets.json")
    return {item.get("id"): item for item in payload.get("worksheets", []) if item.get("id")}


def _card_map() -> dict[str, dict]:
    payload = load_content_json("training_cards.json")
    return {item.get("id"): item for item in payload.get("cards", []) if item.get("id")}


def _compact_cards(card_ids: list[str], cards_by_id: dict[str, dict]) -> list[dict]:
    cards = []
    for card_id in card_ids[:3]:
        card = cards_by_id.get(card_id)
        cards.append(
            {
                "id": card_id,
                "title": card.get("title", card_id) if card else card_id,
                "type": card.get("type") if card else None,
                "duration_minutes": card.get("duration_minutes") if card else None,
                "mechanism_code": card.get("mechanism_code") if card else None,
                "safety_level": card.get("safety_level") if card else None,
                "release_policy": card.get("release_policy") if card else None,
            }
        )
    return cards


def _worksheet_ref(row: dict, worksheet: dict) -> dict:
    worksheet_id = row.get("worksheet_id")
    worksheet_title = row.get("worksheet_title") or worksheet.get("display_title") or worksheet_id
    return {
        "id": worksheet_id,
        "title": worksheet_title,
    }


def _recent_checkin_state(user_id: str) -> dict:
    with get_connection() as conn:
        recent_rows = conn.execute(
            """
            SELECT card_id, completed, created_at
            FROM checkins
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT 20
            """,
            (user_id,),
        ).fetchall()
        completed_rows = conn.execute(
            """
            SELECT card_id, MAX(created_at) AS latest_completed_at
            FROM checkins
            WHERE user_id = ? AND completed = 1 AND card_id IS NOT NULL
            GROUP BY card_id
            ORDER BY latest_completed_at DESC
            """,
            (user_id,),
        ).fetchall()
    checkins = rows_to_dicts(recent_rows)
    completed = [row.get("card_id") for row in rows_to_dicts(completed_rows) if row.get("card_id")]
    return {
        "has_recent_checkin": bool(checkins),
        "last_completed_card_ids": list(dict.fromkeys(completed))[:5],
        "completed_card_ids": list(dict.fromkeys(completed)),
    }


def _exclude_completed_cards(plan_items: list[dict], completed_card_ids: list[str]) -> list[dict]:
    completed = set(completed_card_ids)
    if not completed:
        return plan_items
    available_items = []
    for item in plan_items:
        card_ids = [card_id for card_id in item.get("card_ids", []) if card_id not in completed]
        if not card_ids:
            continue
        cards = [card for card in item.get("cards", []) if card.get("id") in card_ids]
        available_items.append({**item, "card_ids": card_ids, "cards": cards})
    return available_items


def _latest_assignment(user_id: str) -> dict | None:
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT id, user_id, data_json, created_at, updated_at
            FROM records
            WHERE user_id = ? AND module_type = ? AND source_id = ?
            ORDER BY updated_at DESC
            LIMIT 1
            """,
            (user_id, ASSIGNMENT_MODULE_TYPE, ASSIGNMENT_SOURCE_ID),
        ).fetchone()
    if row is None:
        return None
    item = row_to_dict(row)
    data = json_loads(item.pop("data_json", None), {})
    return {**item, **data}


def _normalize_assignment(payload: dict) -> tuple[dict | None, tuple[str, str] | None]:
    phase = str(payload.get("phase") or "").strip()
    cadence = str(payload.get("cadence") or "").strip()
    status = str(payload.get("status") or "active").strip()
    start_date = str(payload.get("start_date") or "").strip()
    goal_text = str(payload.get("goal_text") or "").strip()
    if phase not in ASSIGNMENT_PHASES:
        return None, ("invalid_training_phase", "训练阶段不在允许范围内")
    if cadence not in ASSIGNMENT_CADENCES:
        return None, ("invalid_training_cadence", "练习频率不在允许范围内")
    if status not in ASSIGNMENT_STATUSES:
        return None, ("invalid_training_status", "训练计划状态不在允许范围内")
    if not DATE_RE.match(start_date):
        return None, ("invalid_start_date", "开始日期必须使用 YYYY-MM-DD 格式")
    if len(goal_text) > 200:
        return None, ("training_goal_too_long", "训练目标不能超过 200 字")
    return {
        "phase": phase,
        "cadence": cadence,
        "status": status,
        "start_date": start_date,
        "goal_text": goal_text,
        "agreement_status": "self_selected",
        "boundary_notice": "练习节奏由用户自行设置，研究者共同确认前不代表正式干预安排。",
    }, None


def _load_profile_models() -> dict[str, dict]:
    profile_dir = Path(current_app.config["CONTENT_DIR"]) / "profiles"
    models: dict[str, dict] = {}
    if not profile_dir.exists():
        return models
    for path in profile_dir.glob("*.json"):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        model_id = payload.get("model_id")
        if model_id:
            models[model_id] = payload
    return models


def _cluster_plan_item(row: dict, worksheet: dict, cards_by_id: dict[str, dict], models: dict[str, dict]) -> dict | None:
    model_id = row.get("profile_model_id")
    cluster_id = row.get("profile_cluster_id")
    if model_id in (None, "") or cluster_id in (None, ""):
        return None
    model = models.get(str(model_id))
    if not model:
        return None
    cluster = None
    for item in model.get("clusters", []):
        if str(item.get("cluster_id")) == str(cluster_id):
            cluster = item
            break
    if not cluster:
        return None
    card_ids = [card_id for card_id in cluster.get("recommended_card_ids", []) if card_id in cards_by_id]
    if not card_ids:
        return None
    worksheet_ref = _worksheet_ref(row, worksheet)
    cluster_name = cluster.get("profile_name")
    reason = cluster.get("card_reason") or f"根据最近一次“{worksheet_ref['title']}”的阶段性画像，优先推荐这些小练习。"
    return {
        "source_type": "profile_cluster",
        "source_result_id": row.get("id"),
        "source_worksheet": worksheet_ref,
        "source_worksheet_id": worksheet_ref["id"],
        "source_worksheet_title": worksheet_ref["title"],
        "source_dimension": None,
        "source_profile_name": cluster_name,
        "cluster_id": cluster.get("cluster_id"),
        "cluster_name": cluster_name,
        "card_ids": card_ids[:3],
        "cards": _compact_cards(card_ids, cards_by_id),
        "reason": reason,
        "recommendation_reason": reason,
        "next_step": "先选一张最容易完成的训练卡，做完后简单打卡。",
        "evidence_summary": f"来源于最近一次支持性测评的阶段性画像：{cluster_name or '未命名画像'}。",
        "boundary_notice": "画像推荐只表示当前更接近某类练习线索，不代表固定类型或诊断。",
    }


def _assessment_plan_items(row: dict, worksheet: dict, cards_by_id: dict[str, dict], user_id: str) -> list[dict]:
    scores = json_loads(row.get("scores_json"), fallback={})
    rules = evaluate_training_rules(str(row.get("worksheet_id")), scores, worksheet=worksheet, user_id=user_id)
    items = []
    for rule in rules:
        card_ids = [card_id for card_id in flatten_card_ids([rule]) if card_id in cards_by_id]
        if not card_ids:
            continue
        trigger_dimension = (rule.get("trigger_condition") or {}).get("dimension")
        worksheet_ref = _worksheet_ref(row, worksheet)
        reason = rule.get("reason") or f"根据最近一次“{worksheet_ref['title']}”的支持性测评结果生成。"
        items.append(
            {
                "source_type": "assessment_dimension",
                "source_result_id": row.get("id"),
                "source_worksheet": worksheet_ref,
                "source_worksheet_id": worksheet_ref["id"],
                "source_worksheet_title": worksheet_ref["title"],
                "source_dimension": trigger_dimension,
                "source_profile_name": None,
                "dimension": trigger_dimension,
                "card_ids": card_ids[:3],
                "cards": _compact_cards(card_ids, cards_by_id),
                "reason": reason,
                "recommendation_reason": rule.get("recommendation_reason") or reason,
                "next_step": rule.get("today_suggestion") or "先完成一个 1 到 5 分钟的小练习，再记录一点感受。",
                "evidence_summary": f"来源于“{worksheet_ref['title']}”的维度线索：{trigger_dimension or '整体结果'}。",
                "boundary_notice": rule.get("boundary_notice")
                or "训练推荐只用于自我练习参考，不构成诊断或治疗建议。",
            }
        )
    return items


def _dedupe_plan_items(items: list[dict], limit: int = 8) -> list[dict]:
    seen = set()
    deduped = []
    for item in items:
        key = (
            item.get("source_result_id"),
            item.get("source_type"),
            item.get("dimension"),
            item.get("cluster_id"),
            tuple(item.get("card_ids", [])),
        )
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)
        if len(deduped) >= limit:
            break
    return deduped


@bp.get("")
def get_training_plan():
    try:
        user_id = resolve_actor_user_id(request.args.get("user_id"))
    except AuthError as exc:
        return auth_error_response(exc)

    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT id, user_id, worksheet_id, worksheet_title, scores_json, total_score,
                   profile_model_id, profile_cluster_id, profile_confidence, created_at
            FROM assessment_results
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT 8
            """,
            (user_id,),
        ).fetchall()

    results = rows_to_dicts(rows)
    worksheets = _worksheet_map()
    cards_by_id = _card_map()
    profile_models = _load_profile_models()
    plan_items: list[dict] = []
    for row in results:
        worksheet = worksheets.get(row.get("worksheet_id"), {})
        plan_items.extend(_assessment_plan_items(row, worksheet, cards_by_id, user_id))
        cluster_item = _cluster_plan_item(row, worksheet, cards_by_id, profile_models)
        if cluster_item:
            plan_items.append(cluster_item)

    checkin_state = _recent_checkin_state(user_id)
    plan_items = _exclude_completed_cards(_dedupe_plan_items(plan_items), checkin_state["completed_card_ids"])
    empty_state = None
    if not results:
        empty_state = {
            "title": "先完成一次测一测",
            "description": "完成支持性测评后，这里会按结果推荐更合适的小练习。",
            "url": "/pages/assessment/index",
        }
    elif not plan_items:
        empty_state = {
            "title": "暂时没有匹配到训练推荐",
            "description": "可以先从训练中心选择一张容易完成的训练卡，后续测评记录更多后再生成推荐。",
            "url": "/pages/training/index",
        }
    return ok(
        {
            "user_id": user_id,
            "has_assessment": bool(results),
            "has_recent_checkin": checkin_state["has_recent_checkin"],
            "last_completed_card_ids": checkin_state["last_completed_card_ids"],
            "completed_card_ids": checkin_state["completed_card_ids"],
            "assignment": _latest_assignment(user_id),
            "latest_result": row_to_dict(results[0]) if results else None,
            "plan_items": plan_items,
            "empty_state": empty_state,
            "next_action": empty_state,
            "boundary_notice": "个性化训练计划只用于阶段性练习建议，不构成诊断、筛查或治疗方案。",
        }
    )


@bp.post("/assignment")
def save_training_plan_assignment():
    payload = request.get_json(silent=True) or {}
    try:
        user_id = resolve_actor_user_id(payload=payload)
    except AuthError as exc:
        return auth_error_response(exc)

    assignment, error = _normalize_assignment(payload)
    if error:
        return fail(error[0], error[1], status=400)

    timestamp = now_iso()
    with get_connection() as conn:
        existing = conn.execute(
            """
            SELECT id FROM records
            WHERE user_id = ? AND module_type = ? AND source_id = ?
            ORDER BY updated_at DESC
            LIMIT 1
            """,
            (user_id, ASSIGNMENT_MODULE_TYPE, ASSIGNMENT_SOURCE_ID),
        ).fetchone()
        if existing:
            record_id = existing["id"]
            conn.execute(
                "UPDATE records SET data_json = ?, updated_at = ?, export_allowed = 0 WHERE id = ?",
                (json_dumps(assignment), timestamp, record_id),
            )
        else:
            record_id = new_id("record")
            conn.execute(
                """
                INSERT INTO records (
                    id, user_id, module_type, source_id, data_json,
                    created_at, updated_at, export_allowed
                ) VALUES (?, ?, ?, ?, ?, ?, ?, 0)
                """,
                (
                    record_id,
                    user_id,
                    ASSIGNMENT_MODULE_TYPE,
                    ASSIGNMENT_SOURCE_ID,
                    json_dumps(assignment),
                    timestamp,
                    timestamp,
                ),
            )
        write_audit_log(
            conn,
            action="training_plan_assignment_saved",
            actor_id=user_id,
            target_type=ASSIGNMENT_MODULE_TYPE,
            target_id=record_id,
            metadata={
                "phase": assignment["phase"],
                "cadence": assignment["cadence"],
                "status": assignment["status"],
                "has_goal_text": bool(assignment["goal_text"]),
            },
        )
        conn.commit()

    return ok({"id": record_id, "user_id": user_id, **assignment, "updated_at": timestamp})
