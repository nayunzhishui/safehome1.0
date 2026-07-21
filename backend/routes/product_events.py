"""Privacy-minimised product events for the relationship pilot experience."""

from flask import Blueprint, request

from database import get_connection, write_audit_log
from routes.auth_utils import AuthError, auth_error_response, require_login
from routes.utils import fail, ok


bp = Blueprint("product_events", __name__, url_prefix="/api/product-events")

ALLOWED_EVENTS = {
    "relationship_entry_clicked",
    "relationship_step_completed",
    "relationship_report_downloaded",
    "relationship_task_save_failed",
    "journey_action_impression",
    "journey_action_clicked",
    "journey_action_completed",
    "journey_action_skipped",
    "journey_action_recovery",
    "feedback_discomfort_recorded",
    "human_support_escalated",
}
ALLOWED_METADATA_VALUES = {
    "action": {
        "assessment", "report", "drawing", "sentences", "growth", "task_submitted", "task_submit", "long_image",
        "read_feedback", "read_message", "training_paused", "training_stage_completed", "today_completed",
        "practice_due", "start_assessment", "start_diary", "set_training_cadence", "training_not_due",
        "continue_relationship_draft", "login_required",
        "withdraw_feedback", "correct_feedback", "request_human_support",
    },
    "stage": {"assessment", "report", "exploration", "feedback", "growth", "journey", "training", "message", "human_support"},
    "status": {"success", "failed", "shown", "clicked", "completed", "skipped", "recovered", "escalated"},
    "source": {"primary_action", "secondary_action", "task_form", "report", "today_journey", "feedback_ledger", "human_support"},
    "recovery_mode": {"manual_retry", "draft_restore", "idempotent_replay"},
}


def _validate_metadata(value) -> tuple[dict | None, str | None]:
    if value is None:
        return {}, None
    if not isinstance(value, dict):
        return None, "metadata 必须是对象"
    unknown = sorted(set(value) - set(ALLOWED_METADATA_VALUES) - {"retryable"})
    if unknown:
        return None, f"metadata 包含未允许字段：{', '.join(unknown)}"

    clean = {}
    for key, item in value.items():
        if key == "retryable":
            if not isinstance(item, bool):
                return None, "metadata.retryable 必须是布尔值"
            clean[key] = item
            continue
        if not isinstance(item, str) or item not in ALLOWED_METADATA_VALUES[key]:
            return None, f"metadata.{key} 不是允许的枚举值"
        clean[key] = item
    return clean, None


@bp.post("")
def create_product_event():
    try:
        actor = require_login(allow_legacy_admin=False)
    except AuthError as exc:
        return auth_error_response(exc)

    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return fail("validation_error", "请求体必须是JSON对象", status=400)
    event_name = str(payload.get("event_name") or "").strip()
    client_event_id = str(payload.get("client_event_id") or "").strip()
    if event_name not in ALLOWED_EVENTS:
        return fail("validation_error", "event_name 不是允许的产品事件", status=400)
    if len(client_event_id) > 120:
        return fail("validation_error", "client_event_id 过长", status=400)
    metadata, metadata_error = _validate_metadata(payload.get("metadata"))
    if metadata_error:
        return fail("validation_error", metadata_error, status=400)

    with get_connection() as conn:
        target_id = client_event_id or event_name
        existing = None
        if client_event_id:
            existing = conn.execute(
                "SELECT id FROM audit_logs WHERE actor_id = ? AND action = ? AND target_type = 'product_event' AND target_id = ? LIMIT 1",
                (actor["id"], f"product_event_{event_name}", target_id),
            ).fetchone()
        if existing:
            return ok({"accepted": True, "duplicate": True, "client_event_id": client_event_id}, status=200)
        write_audit_log(
            conn,
            f"product_event_{event_name}",
            actor["id"],
            "product_event",
            target_id,
            metadata,
        )
        conn.commit()
    return ok({"accepted": True, "duplicate": False, "client_event_id": client_event_id or None}, status=202)
