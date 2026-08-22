"""Internal Task 31 security, privacy, and abuse-control endpoints."""

import hmac
import json
import os

from flask import Blueprint, current_app, request

from routes.auth_utils import route_actor as _actor
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
INTERNAL_HEALTH_TOKEN_ENV = "INTERNAL_HEALTH_TOKEN"
INTERNAL_HEALTH_HEADER = "X-Internal-Health-Token"


def _production() -> bool:
    return str(current_app.config.get("APP_ENV") or "").strip().lower() == "production"


def _valid_internal_health_token() -> bool:
    expected = str(os.environ.get(INTERNAL_HEALTH_TOKEN_ENV) or "").strip()
    supplied = str(request.headers.get(INTERNAL_HEALTH_HEADER) or "").strip()
    return bool(expected and supplied and hmac.compare_digest(expected, supplied))


@bp.before_app_request
def protect_deep_health_details():
    """Keep deep operational readiness details off the anonymous production edge.

    `/readyz` remains available to infrastructure probes but is redacted by the
    after-request hook below. `/healthz/deep` exposes its detailed payload only
    to a deployment-injected internal health token. Development/testing retain
    the existing detailed behavior for diagnostics and tests.
    """

    if not _production() or request.path != "/healthz/deep":
        return None
    if _valid_internal_health_token():
        return None
    return fail(
        "not_found",
        "没有找到对应接口。",
        status=404,
    )


@bp.after_app_request
def redact_public_production_readiness(response):
    """Expose only readiness truth, not database/content/backlog internals."""

    if not _production() or request.path != "/readyz":
        return response
    payload = response.get_json(silent=True)
    if not isinstance(payload, dict):
        return response
    minimal = {
        "ok": bool(payload.get("ok")),
        "service": payload.get("service") or "safehome-backend",
        "version": payload.get("version"),
    }
    response.set_data(json.dumps(minimal, ensure_ascii=False, separators=(",", ":")))
    response.headers["Content-Type"] = "application/json; charset=utf-8"
    response.headers["Cache-Control"] = "no-store"
    return response


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
