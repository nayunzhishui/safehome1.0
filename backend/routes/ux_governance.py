"""Task 33 experience-governance endpoints."""

from flask import Blueprint, request

from routes.auth_utils import AuthError, auth_error_response, require_role
from routes.utils import fail, ok
from services.ux_governance_service import UXGovernanceError, create_audit_run, create_evidence_package, get_public_status, get_registry, workbench


bp = Blueprint("ux_governance", __name__, url_prefix="/api/ux-governance")


def _actor(*roles: str):
    try:
        return require_role(*roles, allow_legacy_admin=True), None
    except AuthError as exc:
        return None, auth_error_response(exc)


def _response(callback, *, created: bool = False):
    try:
        return ok(callback(), status=201 if created else 200)
    except UXGovernanceError as exc:
        return fail(exc.code, str(exc), status=exc.status, details=exc.details or None)


@bp.get("/public-status")
def public_status():
    return _response(get_public_status)


@bp.get("/registry")
def registry():
    actor, error = _actor("researcher", "supervisor", "admin")
    if error:
        return error
    return _response(get_registry)


@bp.get("/workbench")
def get_workbench():
    actor, error = _actor("researcher", "supervisor", "admin")
    if error:
        return error
    return _response(workbench)


@bp.post("/audits")
def post_audit():
    actor, error = _actor("admin")
    if error:
        return error
    return _response(lambda: create_audit_run(actor, request.get_json(silent=True) or {}), created=True)


@bp.post("/evidence-packages")
def post_evidence_package():
    actor, error = _actor("supervisor", "admin")
    if error:
        return error
    return _response(lambda: create_evidence_package(actor), created=True)
