"""Personalized training plan endpoints built from assessments and profile clusters."""

import json
from pathlib import Path

from flask import Blueprint, current_app, request

from database import get_connection, json_loads, load_content_json, row_to_dict, rows_to_dicts
from routes.utils import fail, ok, resolve_user_id_for_query
from services.training_recommendation_service import evaluate_training_rules, flatten_card_ids


bp = Blueprint("training_plan", __name__, url_prefix="/api/training-plan")


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
            }
        )
    return cards


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
    return {
        "source_type": "profile_cluster",
        "source_result_id": row.get("id"),
        "source_worksheet": {
            "id": row.get("worksheet_id"),
            "title": row.get("worksheet_title") or worksheet.get("display_title"),
        },
        "cluster_id": cluster.get("cluster_id"),
        "cluster_name": cluster.get("profile_name"),
        "card_ids": card_ids[:3],
        "cards": _compact_cards(card_ids, cards_by_id),
        "reason": cluster.get("card_reason")
        or f"根据最近一次“{row.get('worksheet_title') or worksheet.get('display_title')}”的阶段性画像，优先推荐这些小练习。",
        "boundary_notice": "画像推荐只表示当前更接近某类练习线索，不代表固定类型或诊断。",
    }


def _assessment_plan_items(row: dict, worksheet: dict, cards_by_id: dict[str, dict]) -> list[dict]:
    scores = json_loads(row.get("scores_json"), fallback={})
    rules = evaluate_training_rules(str(row.get("worksheet_id")), scores, worksheet=worksheet)
    items = []
    for rule in rules:
        card_ids = [card_id for card_id in flatten_card_ids([rule]) if card_id in cards_by_id]
        if not card_ids:
            continue
        trigger_dimension = (rule.get("trigger_condition") or {}).get("dimension")
        items.append(
            {
                "source_type": "assessment_dimension",
                "source_result_id": row.get("id"),
                "source_worksheet": {
                    "id": row.get("worksheet_id"),
                    "title": row.get("worksheet_title") or worksheet.get("display_title"),
                },
                "dimension": trigger_dimension,
                "card_ids": card_ids[:3],
                "cards": _compact_cards(card_ids, cards_by_id),
                "reason": rule.get("reason")
                or f"根据最近一次“{row.get('worksheet_title') or worksheet.get('display_title')}”的支持性测评结果生成。",
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
        user_id = resolve_user_id_for_query(request.args.get("user_id"))
    except ValueError as exc:
        return fail("missing_user_id", str(exc), status=400)

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
        plan_items.extend(_assessment_plan_items(row, worksheet, cards_by_id))
        cluster_item = _cluster_plan_item(row, worksheet, cards_by_id, profile_models)
        if cluster_item:
            plan_items.append(cluster_item)

    plan_items = _dedupe_plan_items(plan_items)
    return ok(
        {
            "user_id": user_id,
            "has_assessment": bool(results),
            "latest_result": row_to_dict(results[0]) if results else None,
            "plan_items": plan_items,
            "next_action": None
            if results
            else {
                "title": "先完成一次测一测",
                "description": "完成支持性测评后，这里会按结果推荐更合适的小练习。",
                "url": "/pages/assessment/index",
            },
            "boundary_notice": "个性化训练计划只用于阶段性练习建议，不构成诊断、筛查或治疗方案。",
        }
    )
