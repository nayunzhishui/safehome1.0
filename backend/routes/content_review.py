"""Local content review status endpoints."""

import json
from pathlib import Path

from flask import Blueprint, current_app, request

from routes.utils import admin_token_error_response, fail, ok, require_admin_token

bp = Blueprint("content_review", __name__, url_prefix="/api/content-review")

REVIEW_STATUSES = {"draft", "pending_review", "reviewed", "trial_enabled", "enabled", "disabled", "metadata_only", "pilot_ready"}

CONTENT_TARGETS = {
    "scale": {
        "filename": "scales_catalog.json",
        "list_field": "scales",
        "id_field": "id",
        "enabled_field": "enabled",
    },
    "training_card": {
        "filename": "training_cards.json",
        "list_field": "cards",
        "id_field": "id",
        "enabled_field": "enabled",
    },
    "feedback_rule": {
        "filename": "feedback_rules.json",
        "list_field": "rules",
        "id_field": "id",
        "enabled_field": "enabled",
    },
    "student_profile_rule": {
        "filename": "student_profile_rules.json",
        "list_field": "rules",
        "id_field": "id",
        "enabled_field": "enabled",
    },
    "assessment_training_rule": {
        "filename": "assessment_training_map.json",
        "list_field": "rules",
        "id_field": "rule_id",
        "enabled_field": None,
    },
    "diary_training_rule": {
        "filename": "diary_training_map.json",
        "list_field": "rules",
        "id_field": "rule_id",
        "enabled_field": None,
    },
}


def _load_content(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_content(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


@bp.post("/update")
def update_content_review():
    try:
        require_admin_token()
    except ValueError as exc:
        return admin_token_error_response(exc)

    payload = request.get_json(silent=True) or {}
    content_type = str(payload.get("content_type") or "").strip()
    item_id = str(payload.get("item_id") or "").strip()
    review_status = str(payload.get("review_status") or "").strip()
    enabled_for_user = payload.get("enabled_for_user")

    target = CONTENT_TARGETS.get(content_type)
    if not target:
        return fail("validation_error", "不支持的内容类型", status=400)
    if not item_id:
        return fail("validation_error", "缺少 item_id", status=400)
    if review_status and review_status not in REVIEW_STATUSES:
        return fail("validation_error", "review_status 不在允许枚举中", status=400)
    if enabled_for_user is True:
        return fail(
            "manual_confirmation_required",
            "开启用户端开放状态需要用户单独确认；本接口不会自动开放真实量表或内容。",
            status=409,
        )

    path = current_app.config["CONTENT_DIR"] / target["filename"]
    content = _load_content(path)
    items = content.get(target["list_field"], [])
    matched_item = next((item for item in items if str(item.get(target["id_field"])) == item_id), None)
    if matched_item is None:
        return fail("not_found", "未找到对应内容项", status=404)

    if review_status:
        matched_item["review_status"] = review_status
    enabled_field = target.get("enabled_field")
    if enabled_field and isinstance(enabled_for_user, bool):
        matched_item[enabled_field] = enabled_for_user
    if enabled_for_user is False:
        matched_item["enabled_for_user"] = False

    _write_content(path, content)

    return ok(
        {
            "content_type": content_type,
            "item_id": item_id,
            "review_status": matched_item.get("review_status"),
            "enabled_for_user": matched_item.get(enabled_field) if enabled_field else matched_item.get("enabled_for_user"),
            "filename": target["filename"],
        }
    )
