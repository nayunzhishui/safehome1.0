"""HTTP adapter for the T36-F13 research-analysis job framework."""

from flask import Blueprint, request

from routes.auth_utils import (
    AuthError,
    auth_error_response,
    elevate_actor_for_showcase_researcher_platform,
    require_login,
)
from routes.utils import fail, ok
from services.research_access_service import ResearchAccessError
from services.research_analysis_service import (
    ResearchAnalysisError,
    cancel_job,
    claim_job,
    complete_job,
    create_snapshot,
    delete_artifact,
    enqueue_job,
    fail_job,
    get_artifact,
    get_job,
    list_jobs,
    recover_job,
    suspend_job,
)
from services.research_online_analysis_service import execute_synthetic_job, get_catalog


bp = Blueprint("research_analysis", __name__, url_prefix="/api/research/analysis")


def _actor():
    try:
        return elevate_actor_for_showcase_researcher_platform(
            require_login(allow_legacy_admin=True)
        ), None
    except AuthError as exc:
        return None, auth_error_response(exc)


def _respond(callable_, *args):
    try:
        result = callable_(*args)
    except (ResearchAnalysisError, ResearchAccessError) as exc:
        return fail(exc.code, exc.message, status=exc.status, details=exc.details or None)
    if isinstance(result, tuple):
        data, status = result
        return ok(data, status=status)
    return ok(result)


@bp.post("/snapshots")
def post_snapshot():
    actor, error = _actor()
    return error or _respond(create_snapshot, actor, request.get_json(silent=True) or {})


@bp.get("/jobs")
def get_jobs():
    actor, error = _actor()
    return error or _respond(
        list_jobs,
        actor,
        str(request.args.get("status") or ""),
        int(request.args.get("limit") or 50),
    )


@bp.post("/jobs")
def post_job():
    actor, error = _actor()
    return error or _respond(
        enqueue_job,
        actor,
        request.get_json(silent=True) or {},
        str(request.headers.get("Idempotency-Key") or ""),
    )


@bp.get("/jobs/<job_id>")
def get_job_route(job_id: str):
    actor, error = _actor()
    return error or _respond(get_job, actor, job_id)


@bp.post("/jobs/<job_id>/claim")
def post_claim(job_id: str):
    actor, error = _actor()
    return error or _respond(claim_job, actor, job_id, request.get_json(silent=True) or {})


@bp.post("/jobs/<job_id>/complete")
def post_complete(job_id: str):
    actor, error = _actor()
    return error or _respond(complete_job, actor, job_id, request.get_json(silent=True) or {})


@bp.post("/jobs/<job_id>/fail")
def post_fail(job_id: str):
    actor, error = _actor()
    return error or _respond(fail_job, actor, job_id, request.get_json(silent=True) or {})


@bp.post("/jobs/<job_id>/cancel")
def post_cancel(job_id: str):
    actor, error = _actor()
    return error or _respond(cancel_job, actor, job_id)


@bp.post("/jobs/<job_id>/recover")
def post_recover(job_id: str):
    actor, error = _actor()
    return error or _respond(recover_job, actor, job_id, request.get_json(silent=True) or {})


@bp.post("/jobs/<job_id>/suspend")
def post_suspend(job_id: str):
    actor, error = _actor()
    return error or _respond(suspend_job, actor, job_id, request.get_json(silent=True) or {})


@bp.post("/jobs/<job_id>/execute-synthetic")
def post_execute_synthetic(job_id: str):
    actor, error = _actor()
    return error or _respond(execute_synthetic_job, actor, job_id)


@bp.get("/artifacts/<artifact_id>")
def get_artifact_route(artifact_id: str):
    actor, error = _actor()
    return error or _respond(get_artifact, actor, artifact_id)


@bp.delete("/artifacts/<artifact_id>")
def delete_artifact_route(artifact_id: str):
    actor, error = _actor()
    return error or _respond(
        delete_artifact,
        actor,
        artifact_id,
        request.get_json(silent=True) or {},
    )
@bp.get("/catalog")
def get_catalog_route():
    actor, error = _actor()
    return error or _respond(get_catalog, actor)
