"""Local content review status endpoints."""

import json
from pathlib import Path

from flask import Blueprint, current_app, request

from database import get_connection, write_audit_log
from routes.auth_utils import AuthError, auth_error_response, require_role
from routes.utils import admin_token_error_response, fail, ok, require_admin_token
from services.content_governance_service import (
    GovernanceError,
    change_release_state,
    create_draft,
    diff_version,
    get_active_descriptor,
    get_version,
    list_inventory,
    list_versions,
    publish_version,
    register_inventory,
    review_version,
    run_synthetic_replay,
    submit_version,
)

bp = Blueprint("content_review", __name__, url_prefix="/api/content-review")

REVIEW_STATUSES = {"draft", "pending_review", "reviewed", "trial_enabled", "enabled", "disabled", "metadata_only", "pilot_ready", "draft_requires_psychology_review", "pilot_draft", "pilot_approved", "paused", "completed"}
RELEASE_STATUSES = {"trial_enabled", "enabled", "pilot_approved"}
EVIDENCE_GOVERNED_TYPES = {"scale", "training_card", "course"}
PROGRAM_TRANSITIONS = {
    "pilot_draft": {"pilot_approved"},
    "pilot_approved": {"paused", "completed"},
    "paused": {"pilot_approved", "completed"},
    "completed": set(),
}

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
    "program": {
        "filename": "programs.json",
        "list_field": "programs",
        "id_field": "id",
        "enabled_field": "enabled",
    },
    "course": {
        "filename": "courses.json",
        "list_field": "courses",
        "id_field": "id",
        "enabled_field": "enabled",
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

    if current_app.config.get("CONTENT_GOVERNANCE_ENFORCED", False):
        return fail("legacy_content_update_disabled", "当前环境已启用完整内容治理，请通过版本、审核和发布接口操作。", status=409)

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
        if content_type == "program" and review_status != matched_item.get("review_status"):
            current_status = str(matched_item.get("review_status") or "")
            if review_status not in PROGRAM_TRANSITIONS.get(current_status, set()):
                return fail("invalid_program_transition", "项目状态迁移不符合治理顺序。", status=409)
            if review_status == "pilot_approved":
                approval = matched_item.get("approval") or {}
                approval_complete = all(
                    isinstance(approval.get(role), dict)
                    and approval[role].get("status") == "approved"
                    and approval[role].get("reviewer")
                    and approval[role].get("reviewed_at")
                    and approval[role].get("evidence_path")
                    for role in ("research", "psychology", "ethics")
                )
                if not approval_complete:
                    return fail("program_approval_incomplete", "研究、心理和伦理三方签字不完整。", status=409)
        if content_type in EVIDENCE_GOVERNED_TYPES and review_status in RELEASE_STATUSES:
            approval = payload.get("approval") or {}
            approval_complete = all(str(approval.get(field) or "").strip() for field in ("reviewer", "reviewed_at", "evidence_path"))
            if not approval_complete:
                return fail(
                    "content_approval_evidence_incomplete",
                    "最终批准需要审核人、日期和证据路径。",
                    status=409,
                )
            matched_item["approval"] = {
                "reviewer": str(approval["reviewer"]).strip(),
                "reviewed_at": str(approval["reviewed_at"]).strip(),
                "evidence_path": str(approval["evidence_path"]).strip(),
                "scope": str(approval.get("scope") or "pilot_release").strip(),
            }
        matched_item["review_status"] = review_status
    enabled_field = target.get("enabled_field")
    if enabled_field and isinstance(enabled_for_user, bool):
        matched_item[enabled_field] = enabled_for_user
    if enabled_for_user is False:
        matched_item["enabled_for_user"] = False

    _write_content(path, content)
    with get_connection() as conn:
        write_audit_log(conn, "legacy_content_review_updated", "admin-token", content_type, item_id, {"review_status": review_status, "enabled_for_user": enabled_for_user, "governance_bypassed": True})
        conn.commit()

    return ok(
        {
            "content_type": content_type,
            "item_id": item_id,
            "review_status": matched_item.get("review_status"),
            "enabled_for_user": matched_item.get(enabled_field) if enabled_field else matched_item.get("enabled_for_user"),
            "filename": target["filename"],
        }
    )


def _actor(*roles: str):
    try:
        return require_role(*roles, allow_legacy_admin=True), None
    except AuthError as exc:
        return None, auth_error_response(exc)


def _governance_response(callback):
    try:
        return ok(callback())
    except GovernanceError as exc:
        return fail(exc.code, str(exc), details=exc.details or None, status=exc.status)


@bp.get("/inventory")
def content_inventory():
    _current_actor, error = _actor("researcher", "supervisor", "admin")
    if error:
        return error
    return _governance_response(list_inventory)


@bp.get("/active/<content_type>/<item_id>")
def content_active_descriptor(content_type: str, item_id: str):
    return _governance_response(lambda: get_active_descriptor(content_type, item_id))


@bp.post("/inventory/register")
def content_inventory_register():
    current_actor, error = _actor("admin")
    if error:
        return error
    return _governance_response(lambda: register_inventory(current_actor))


@bp.get("/versions")
def content_versions():
    _current_actor, error = _actor("researcher", "supervisor", "admin")
    if error:
        return error
    return _governance_response(lambda: {"items": list_versions(request.args.get("content_type"), request.args.get("item_id"))})


@bp.post("/versions")
def content_version_create():
    current_actor, error = _actor("researcher", "supervisor", "admin")
    if error:
        return error
    payload = request.get_json(silent=True) or {}
    return _governance_response(lambda: create_draft(current_actor, payload))


@bp.get("/versions/<version_id>")
def content_version_detail(version_id: str):
    _current_actor, error = _actor("researcher", "supervisor", "admin")
    if error:
        return error
    return _governance_response(lambda: get_version(version_id))


@bp.get("/versions/<version_id>/diff")
def content_version_diff(version_id: str):
    _current_actor, error = _actor("researcher", "supervisor", "admin")
    if error:
        return error
    return _governance_response(lambda: diff_version(version_id))


@bp.post("/versions/<version_id>/submit")
def content_version_submit(version_id: str):
    current_actor, error = _actor("researcher", "supervisor", "admin")
    if error:
        return error
    return _governance_response(lambda: submit_version(current_actor, version_id))


@bp.post("/versions/<version_id>/reviews")
def content_version_review(version_id: str):
    current_actor, error = _actor("researcher", "supervisor", "admin")
    if error:
        return error
    payload = request.get_json(silent=True) or {}
    return _governance_response(lambda: review_version(current_actor, version_id, payload))


@bp.post("/versions/<version_id>/publish")
def content_version_publish(version_id: str):
    current_actor, error = _actor("admin")
    if error:
        return error
    payload = request.get_json(silent=True) or {}
    return _governance_response(lambda: publish_version(current_actor, version_id, payload))


@bp.post("/releases/<release_id>/<action>")
def content_release_action(release_id: str, action: str):
    current_actor, error = _actor("admin")
    if error:
        return error
    payload = request.get_json(silent=True) or {}
    return _governance_response(lambda: change_release_state(current_actor, release_id, action, payload))


@bp.post("/replay")
def content_synthetic_replay():
    current_actor, error = _actor("researcher", "supervisor", "admin")
    if error:
        return error
    payload = request.get_json(silent=True) or {}
    return _governance_response(lambda: run_synthetic_replay(current_actor, payload.get("cases")))
