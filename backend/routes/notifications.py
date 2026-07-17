"""Participant consent and controlled scheduler endpoints for WeChat reminders."""

import hmac

from flask import Blueprint, current_app, request

from routes.auth_utils import AuthError, auth_error_response, require_role, resolve_actor_user_id
from routes.utils import fail, ok
from services.notification_service import (
    NotificationError,
    get_preference,
    record_consent,
    run_due_notifications,
    subscription_capability,
)


bp = Blueprint("notifications", __name__, url_prefix="/api/notifications")


def _notification_error(exc: NotificationError):
    return fail(exc.code, str(exc), status=exc.status)


@bp.get("/config")
def get_notification_config():
    try:
        user_id = resolve_actor_user_id(request.args.get("user_id"))
    except AuthError as exc:
        return auth_error_response(exc)
    return ok({**subscription_capability(), "preference": get_preference(user_id)})


@bp.post("/consent")
def save_notification_consent():
    payload = request.get_json(silent=True) or {}
    try:
        user_id = resolve_actor_user_id(payload=payload)
        preference = record_consent(
            user_id,
            str(payload.get("template_id") or ""),
            str(payload.get("decision") or ""),
        )
    except AuthError as exc:
        return auth_error_response(exc)
    except NotificationError as exc:
        return _notification_error(exc)
    return ok({"preference": preference})


@bp.post("/run-due")
def run_due():
    configured = str(current_app.config.get("NOTIFICATION_SCHEDULER_TOKEN") or "")
    supplied = str(request.headers.get("X-Scheduler-Token") or "")
    scheduler_authorized = bool(configured and supplied and hmac.compare_digest(configured, supplied))
    if not scheduler_authorized:
        try:
            require_role("admin")
        except AuthError as exc:
            return auth_error_response(exc)
    payload = request.get_json(silent=True) or {}
    dry_run = payload.get("dry_run", True) is not False
    try:
        return ok(run_due_notifications(dry_run=dry_run))
    except NotificationError as exc:
        return _notification_error(exc)
