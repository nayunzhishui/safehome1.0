"""HTTP adapter for the task-36 researcher capability and scope contract."""

from flask import Blueprint, request

from routes.auth_utils import AuthError, auth_error_response, elevate_actor_for_showcase_researcher_platform, require_login
from routes.utils import fail, ok, parse_int
from services.research_access_service import (
    ResearchAccessError,
    capability_summary,
    claim_enrollment,
    create_assignment,
    list_assignments,
    update_assignment,
)
from services.research_sensitive_access_service import (
    list_authorized_assessment_summaries,
    list_authorized_participants,
)


bp = Blueprint("research_access", __name__, url_prefix="/api/research/access")


def _actor():
    try:
        return elevate_actor_for_showcase_researcher_platform(require_login(allow_legacy_admin=True)), None
    except AuthError as exc:
        return None, auth_error_response(exc)


def _respond(callable_, *args):
    try:
        result = callable_(*args)
    except ResearchAccessError as exc:
        return fail(exc.code, exc.message, status=exc.status, details=exc.details or None)
    if isinstance(result, tuple):
        data, status = result
        return ok(data, status=status)
    return ok(result)


@bp.get("/capabilities")
def capabilities_route():
    actor, error = _actor()
    if error:
        return error
    return _respond(capability_summary, actor)


@bp.get("/assignments")
def assignments_route():
    actor, error = _actor()
    if error:
        return error
    return _respond(list_assignments, actor, str(request.args.get("enrollment_id") or "").strip())


@bp.post("/assignments")
def create_assignment_route():
    actor, error = _actor()
    if error:
        return error
    return _respond(
        create_assignment,
        actor,
        request.get_json(silent=True) or {},
        request.headers.get("Idempotency-Key", ""),
    )


@bp.patch("/assignments/<assignment_id>")
def update_assignment_route(assignment_id: str):
    actor, error = _actor()
    if error:
        return error
    return _respond(
        update_assignment,
        actor,
        assignment_id,
        request.get_json(silent=True) or {},
        request.headers.get("Idempotency-Key", ""),
    )


@bp.post("/enrollments/<enrollment_id>/claim")
def claim_enrollment_route(enrollment_id: str):
    actor, error = _actor()
    if error:
        return error
    return _respond(
        claim_enrollment,
        actor,
        enrollment_id,
        request.headers.get("Idempotency-Key", ""),
    )


@bp.get("/participants")
def authorized_participants_route():
    """List only assigned participants with current explicit research opt-in."""

    actor, error = _actor()
    if error:
        return error
    limit = parse_int(request.args.get("limit"), 100)
    limit = 100 if limit is None else max(1, min(limit, 200))
    return _respond(list_authorized_participants, actor, limit)


@bp.get("/enrollments/<enrollment_id>/assessment-summaries")
def authorized_assessment_summaries_route(enrollment_id: str):
    """Read minimized assessment summaries through capability + scope + opt-in."""

    actor, error = _actor()
    if error:
        return error
    limit = parse_int(request.args.get("limit"), 100)
    limit = 100 if limit is None else max(1, min(limit, 200))
    return _respond(list_authorized_assessment_summaries, actor, enrollment_id, limit)
