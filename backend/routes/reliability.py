"""Task 32 reliability and release-engineering endpoints."""

from flask import Blueprint, request

from routes.auth_utils import AuthError, auth_error_response, require_role
from routes.utils import fail, ok
from services.reliability_service import (
    ReliabilityError,
    claim_job,
    complete_job,
    create_evidence_package,
    create_job,
    create_slo_snapshot,
    fail_job,
    list_feature_flags,
    list_jobs,
    public_status,
    recover_job,
    rollback_feature_flag,
    run_fault_drill,
    update_feature_flag,
    workbench,
)


bp = Blueprint("reliability", __name__, url_prefix="/api/reliability")


def _actor(*roles: str):
    try:
        return require_role(*roles, allow_legacy_admin=True), None
    except AuthError as exc:
        return None, auth_error_response(exc)


def _response(callback, *, created: bool = False):
    try:
        return ok(callback(), status=201 if created else 200)
    except ReliabilityError as exc:
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


@bp.post("/slo-snapshots")
def post_slo_snapshot():
    actor, error = _actor("researcher", "supervisor", "admin")
    if error:
        return error
    payload = request.get_json(silent=True) or {}
    return _response(lambda: create_slo_snapshot(actor, payload))


@bp.get("/jobs")
def get_jobs():
    actor, error = _actor("researcher", "supervisor", "admin")
    if error:
        return error
    return _response(lambda: {"items": list_jobs()})


@bp.post("/jobs")
def post_job():
    actor, error = _actor("admin")
    if error:
        return error
    payload = request.get_json(silent=True) or {}
    try:
        item, created = create_job(actor, payload)
        return ok(item, status=201 if created else 200)
    except ReliabilityError as exc:
        return fail(exc.code, str(exc), status=exc.status, details=exc.details or None)


@bp.post("/jobs/<job_id>/claim")
def post_job_claim(job_id: str):
    actor, error = _actor("admin")
    if error:
        return error
    payload = request.get_json(silent=True) or {}
    return _response(lambda: claim_job(actor, job_id, payload))


@bp.post("/jobs/<job_id>/complete")
def post_job_complete(job_id: str):
    actor, error = _actor("admin")
    if error:
        return error
    return _response(lambda: complete_job(actor, job_id))


@bp.post("/jobs/<job_id>/fail")
def post_job_fail(job_id: str):
    actor, error = _actor("admin")
    if error:
        return error
    payload = request.get_json(silent=True) or {}
    return _response(lambda: fail_job(actor, job_id, payload))


@bp.post("/jobs/<job_id>/recover")
def post_job_recover(job_id: str):
    actor, error = _actor("admin")
    if error:
        return error
    payload = request.get_json(silent=True) or {}
    return _response(lambda: recover_job(actor, job_id, payload))


@bp.get("/feature-flags")
def get_feature_flags():
    actor, error = _actor("researcher", "supervisor", "admin")
    if error:
        return error
    return _response(lambda: {"items": list_feature_flags()})


@bp.patch("/feature-flags/<flag_name>")
def patch_feature_flag(flag_name: str):
    actor, error = _actor("admin")
    if error:
        return error
    payload = request.get_json(silent=True) or {}
    return _response(lambda: update_feature_flag(actor, flag_name, payload))


@bp.post("/feature-flags/<flag_name>/rollback")
def post_feature_flag_rollback(flag_name: str):
    actor, error = _actor("admin")
    if error:
        return error
    payload = request.get_json(silent=True) or {}
    return _response(lambda: rollback_feature_flag(actor, flag_name, payload))


@bp.post("/drills")
def post_drill():
    actor, error = _actor("admin")
    if error:
        return error
    payload = request.get_json(silent=True) or {}
    return _response(lambda: run_fault_drill(actor, payload))


@bp.post("/evidence-packages")
def post_evidence_package():
    actor, error = _actor("supervisor", "admin")
    if error:
        return error
    return _response(lambda: create_evidence_package(actor))
