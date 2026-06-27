"""Rule-based feedback endpoints."""

from flask import Blueprint, request

from database import get_connection, json_dumps, load_content_json, new_id, now_iso, row_to_dict
from routes.utils import auth_error_response, fail, ok, require_admin_or_owner, require_user_id
from services.feedback_service import generate_feedback
from services.risk_review_service import create_risk_review_record
from services.risk_service import check_text_risk

bp = Blueprint("feedback", __name__, url_prefix="/api/feedback")

RISK_ORDER = {"low": 0, "medium": 1, "high": 2}


def _highest_risk_level(*levels: str | None) -> str:
    valid_levels = [level for level in levels if level]
    if not valid_levels:
        return "low"
    return max(valid_levels, key=lambda level: RISK_ORDER.get(level, 0))


def _feedback_risk_text(source_payload: dict) -> list[str | None]:
    return [
        source_payload.get("event_description"),
        source_payload.get("automatic_thought"),
        source_payload.get("behavior"),
        source_payload.get("free_text"),
        source_payload.get("raw_text"),
    ]


def _high_risk_feedback_result(risk_result: dict) -> dict:
    return {
        "tags": [],
        "labels": [],
        "trigger_summary": "本次记录包含需要优先人工关注的安全提示。",
        "pattern_summary": "此时系统不会继续生成普通互动模式反馈或训练卡建议。",
        "supportive_feedback": risk_result["safe_response"],
        "alternative_response": risk_result["boundary_notice"],
        "recommended_card_ids": [],
        "training_recommendation_rules": [],
        "risk_level": risk_result["risk_level"],
        "risk": risk_result,
    }


def _matches_diary_training_rule(rule: dict, feedback_result: dict) -> bool:
    condition = rule.get("trigger_condition", {})
    expected_feedback_rule = condition.get("feedback_rule_id")
    expected_risk_level = condition.get("risk_level")
    tags = set(feedback_result.get("tags") or [])
    risk_level = feedback_result.get("risk_level", "low")

    if rule.get("source_type") != "diary":
        return False
    if expected_feedback_rule and expected_feedback_rule not in tags:
        return False
    if expected_risk_level and expected_risk_level != risk_level:
        return False
    return True


def _match_diary_training_rules(feedback_result: dict) -> list[dict]:
    if feedback_result.get("risk_level") == "high":
        return []

    rules_payload = load_content_json("diary_training_map.json")
    matched_rules = []
    for rule in rules_payload.get("rules", []):
        if _matches_diary_training_rule(rule, feedback_result):
            matched_rules.append(rule)

    return matched_rules[:1]


@bp.post("/generate")
def generate():
    payload = request.get_json(silent=True) or {}
    diary_id = payload.get("diary_id")

    with get_connection() as conn:
        source_payload = dict(payload)
        if diary_id:
            diary = conn.execute("SELECT * FROM emotion_diaries WHERE id = ?", (diary_id,)).fetchone()
            if diary is None:
                return fail("not_found", "未找到对应的情绪事件记录", status=404)
            try:
                require_admin_or_owner(diary["user_id"])
            except ValueError as exc:
                return auth_error_response(exc)
            source_payload.update(row_to_dict(diary))

        risk_result = check_text_risk(_feedback_risk_text(source_payload), source="feedback")
        if risk_result["allow_auto_feedback"] is False:
            result = _high_risk_feedback_result(risk_result)
        else:
            result = generate_feedback(source_payload)
            result["risk_level"] = _highest_risk_level(result.get("risk_level"), risk_result.get("risk_level"))
            result["risk"] = risk_result
            result["training_recommendation_rules"] = (
                _match_diary_training_rules(result)
                if risk_result.get("allow_recommended_training_cards") is not False
                else []
            )

        feedback_id = new_id("feedback")
        try:
            user_id = require_user_id(source_payload)
        except ValueError as exc:
            return fail("validation_error", str(exc), status=400)
        timestamp = now_iso()
        conn.execute(
            """
            INSERT INTO feedback_results (
                id, user_id, diary_id, tags_json, trigger_summary,
                pattern_summary, supportive_feedback, alternative_response,
                recommended_card_ids_json, risk_level, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                feedback_id,
                user_id,
                diary_id,
                json_dumps(result["tags"]),
                result["trigger_summary"],
                result["pattern_summary"],
                result["supportive_feedback"],
                result["alternative_response"],
                json_dumps(result["recommended_card_ids"]),
                result["risk_level"],
                timestamp,
            ),
        )
        create_risk_review_record(conn, user_id, "feedback", feedback_id, risk_result)
        conn.commit()

    return ok({"id": feedback_id, "diary_id": diary_id, **result}, status=201)
