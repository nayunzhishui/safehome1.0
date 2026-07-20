"""Internal Task 31 security, privacy, and abuse-control endpoints."""

from flask import Blueprint, request

from routes.auth_utils import AuthError, auth_error_response, require_role
from routes.utils import fail, ok
from services.security_control_service import (
    SecurityControlError,
    public_status,
    resolve_security_event,
    run_security_scan,
    set_account_status,
    workbench,
)


bp = Blueprint("security_controls", __name__, url_prefix="/api/security")


def _actor(*roles: str):
    try:
        return require_role(*roles, allow_legacy_admin=True), None
    except AuthError as exc:
        return None, auth_error_response(exc)


def _response(callback):
    try:
        return ok(callback())
    except SecurityControlError as exc:
        return fail(exc.code, str(exc), status=exc.status, details=exc.details or None)


@bp.get("/public-status")
def get_public_status():
    return _response(public_status)


@bp.get("/workbench")
def get_workbench():
    actor, error = _actor("researcher", "supervisor", "admin")
    if error:
        return error
    return _response(workbench)


@bp.post("/scans")
def create_scan():
    actor, error = _actor("admin")
    if error:
        return error
    return _response(lambda: run_security_scan(actor))


@bp.patch("/accounts/<user_id>/status")
def update_account_status(user_id: str):
    actor, error = _actor("admin")
    if error:
        return error
    payload = request.get_json(silent=True) or {}
    return _response(lambda: set_account_status(actor, user_id, payload))


@bp.post("/events/<event_id>/resolve")
def resolve_event(event_id: str):
    actor, error = _actor("admin")
    if error:
        return error
    return _response(lambda: resolve_security_event(actor, event_id))
