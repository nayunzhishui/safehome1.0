"""Task 34 content, data and model operations-governance endpoints."""

from flask import Blueprint, request

from routes.auth_utils import AuthError, auth_error_response, require_role
from routes.utils import fail, ok
from services.operations_governance_service import (
    OperationsGovernanceError,
    approve_package,
    change_package_state,
    create_evidence_package,
    create_monitor_snapshot,
    create_package,
    get_registry,
    package_detail,
    public_status,
    record_postmortem,
    release_package,
    report_incident,
    review_package,
    rollback_runtime,
    run_replay,
    submit_package,
    update_notification,
    workbench,
)


bp = Blueprint("operations_governance", __name__, url_prefix="/api/operations-governance")


def _actor(*roles: str):
    try:
        return require_role(*roles, allow_legacy_admin=True), None
    except AuthError as exc:
        return None, auth_error_response(exc)


def _response(callback, *, created: bool = False):
    try:
        return ok(callback(), status=201 if created else 200)
    except OperationsGovernanceError as exc:
        return fail(exc.code, str(exc), status=exc.status, details=exc.details or None)


@bp.get("/public-status")
def get_public_status():
    return _response(public_status)


@bp.get("/registry")
def get_operations_registry():
    actor, error = _actor("researcher", "supervisor", "admin")
    if error:
        return error
    return _response(get_registry)


@bp.get("/workbench")
def get_operations_workbench():
    actor, error = _actor("researcher", "supervisor", "admin")
    if error:
        return error
    return _response(workbench)


@bp.post("/packages")
def post_package():
    actor, error = _actor("researcher", "supervisor", "admin")
    if error:
        return error
    payload = request.get_json(silent=True) or {}
    return _response(lambda: create_package(actor, payload), created=True)


@bp.get("/packages/<package_id>")
def get_package(package_id: str):
    actor, error = _actor("researcher", "supervisor", "admin")
    if error:
        return error
    return _response(lambda: package_detail(package_id))


@bp.post("/packages/<package_id>/replay")
def post_package_replay(package_id: str):
    actor, error = _actor("researcher", "supervisor", "admin")
    if error:
        return error
    return _response(lambda: run_replay(actor, package_id))


@bp.post("/packages/<package_id>/submit")
def post_package_submit(package_id: str):
    actor, error = _actor("researcher", "supervisor", "admin")
    if error:
        return error
    return _response(lambda: submit_package(actor, package_id))


@bp.post("/packages/<package_id>/reviews")
def post_package_review(package_id: str):
    actor, error = _actor("researcher", "supervisor", "admin")
    if error:
        return error
    payload = request.get_json(silent=True) or {}
    return _response(lambda: review_package(actor, package_id, payload))


@bp.post("/packages/<package_id>/approvals")
def post_package_approval(package_id: str):
    actor, error = _actor("researcher", "supervisor", "admin")
    if error:
        return error
    payload = request.get_json(silent=True) or {}
    return _response(lambda: approve_package(actor, package_id, payload))


@bp.post("/packages/<package_id>/release")
def post_package_release(package_id: str):
    actor, error = _actor("admin")
    if error:
        return error
    payload = request.get_json(silent=True) or {}
    return _response(lambda: release_package(actor, package_id, payload))


@bp.post("/packages/<package_id>/<action>")
def post_package_action(package_id: str, action: str):
    actor, error = _actor("admin")
    if error:
        return error
    payload = request.get_json(silent=True) or {}
    return _response(lambda: change_package_state(actor, package_id, action, payload))


@bp.post("/runtime/rollback")
def post_runtime_rollback():
    actor, error = _actor("admin")
    if error:
        return error
    payload = request.get_json(silent=True) or {}
    return _response(lambda: rollback_runtime(actor, payload))


@bp.post("/monitoring/snapshots")
def post_monitoring_snapshot():
    actor, error = _actor("researcher", "supervisor", "admin")
    if error:
        return error
    payload = request.get_json(silent=True) or {}
    return _response(lambda: create_monitor_snapshot(actor, payload), created=True)


@bp.post("/incidents")
def post_incident():
    actor, error = _actor("researcher", "supervisor", "admin")
    if error:
        return error
    payload = request.get_json(silent=True) or {}
    return _response(lambda: report_incident(actor, payload), created=True)


@bp.post("/incidents/<incident_id>/postmortem")
def post_incident_postmortem(incident_id: str):
    actor, error = _actor("supervisor", "admin")
    if error:
        return error
    payload = request.get_json(silent=True) or {}
    return _response(lambda: record_postmortem(actor, incident_id, payload))


@bp.post("/incidents/<incident_id>/notifications/<notification_id>/<action>")
def post_incident_notification(incident_id: str, notification_id: str, action: str):
    actor, error = _actor("admin")
    if error:
        return error
    payload = request.get_json(silent=True) or {}
    return _response(lambda: update_notification(actor, incident_id, notification_id, action, payload))


@bp.post("/evidence-packages")
def post_evidence_package():
    actor, error = _actor("supervisor", "admin")
    if error:
        return error
    return _response(lambda: create_evidence_package(actor), created=True)
