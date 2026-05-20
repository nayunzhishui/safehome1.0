"""Rule-based feedback endpoints."""

from flask import Blueprint, request

from database import get_connection, json_dumps, new_id, now_iso, row_to_dict
from routes.utils import fail, ok
from services.feedback_service import generate_feedback

bp = Blueprint("feedback", __name__, url_prefix="/api/feedback")


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
            source_payload.update(row_to_dict(diary))

        result = generate_feedback(source_payload)
        feedback_id = new_id("feedback")
        user_id = source_payload.get("user_id") or "demo-parent"
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
        conn.commit()

    return ok({"id": feedback_id, "diary_id": diary_id, **result}, status=201)
