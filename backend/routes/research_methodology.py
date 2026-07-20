"""Research-methodology pre-freeze workbench endpoints.

These endpoints produce machine evidence and synthetic feasibility checks only.
They never record a human signature, formal freeze, or outcome-analysis approval.
"""

from flask import Blueprint, request

from routes.auth_utils import AuthError, auth_error_response, require_role
from routes.utils import fail, ok
from services.research_methodology_service import (
    ResearchMethodologyError,
    create_evidence_package,
    disable_runtime,
    get_config,
    get_public_status,
    get_registry,
    list_evidence,
    list_versions,
    run_machine_checks,
    run_simulation,
    sync_registry,
)


bp = Blueprint("research_methodology", __name__, url_prefix="/api/research/methodology")


def _actor(*roles: str):
    try:
        return require_role(*roles, allow_legacy_admin=True), None
    except AuthError as exc:
        return None, auth_error_response(exc)


def _response(callback):
    try:
        return ok(callback())
    except ResearchMethodologyError as exc:
        return fail(exc.code, str(exc), status=exc.status, details=exc.details or None)


@bp.get("/public-status")
def public_status():
    return _response(get_public_status)


@bp.get("/config")
def config():
    actor, error = _actor("researcher", "supervisor", "admin")
    if error:
        return error
    return _response(get_config)


@bp.get("/registry")
def registry():
    actor, error = _actor("researcher", "supervisor", "admin")
    if error:
        return error
    return _response(get_registry)


@bp.get("/versions")
def versions():
    actor, error = _actor("researcher", "supervisor", "admin")
    if error:
        return error
    return _response(lambda: {"items": list_versions()})


@bp.post("/versions/sync")
def versions_sync():
    actor, error = _actor("admin")
    if error:
        return error
    return _response(lambda: sync_registry(actor))


@bp.post("/checks/run")
def checks_run():
    actor, error = _actor("researcher", "supervisor", "admin")
    if error:
        return error
    payload = request.get_json(silent=True) or {}
    return _response(lambda: run_machine_checks(actor, payload.get("version_id")))


@bp.post("/simulations/run")
def simulations_run():
    actor, error = _actor("researcher", "supervisor", "admin")
    if error:
        return error
    payload = request.get_json(silent=True) or {}
    return _response(lambda: run_simulation(actor, payload.get("version_id")))


@bp.get("/evidence")
def evidence():
    actor, error = _actor("researcher", "supervisor", "admin")
    if error:
        return error
    return _response(list_evidence)


@bp.post("/evidence-packages")
def evidence_packages():
    actor, error = _actor("supervisor", "admin")
    if error:
        return error
    payload = request.get_json(silent=True) or {}
    return _response(lambda: create_evidence_package(actor, payload.get("version_id")))


@bp.post("/disable")
def disable():
    actor, error = _actor("admin")
    if error:
        return error
    payload = request.get_json(silent=True) or {}
    return _response(lambda: disable_runtime(actor, payload))
