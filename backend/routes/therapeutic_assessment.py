"""HTTP routes for the Task36-F16 therapeutic-assessment collaboration."""

from flask import Blueprint, request

from routes.auth_utils import AuthError, auth_error_response, require_login
from routes.utils import fail, ok
from services.therapeutic_assessment_service import (
    TherapeuticAssessmentError,
    assign_case,
    create_action,
    create_case,
    create_feedback,
    get_case,
    list_cases,
    participant_transition,
    review_feedback,
    send_feedback,
    set_readiness,
    update_action,
    update_scope,
)
from services.therapeutic_assessment_level_service import public_status as service_level_status
from services.therapeutic_assessment_transition_service import transition_case
from services.therapeutic_assessment_evidence_service import (
    create_evidence,
    list_evidence,
    review_hypothesis,
)
from services.therapeutic_assessment_question_service import update_question


bp = Blueprint("therapeutic_assessment", __name__, url_prefix="/api/therapeutic-assessment")


def _actor():
    try:
        return require_login(allow_legacy_admin=True), None
    except AuthError as exc:
        return None, auth_error_response(exc)


def _respond(callable_, *args):
    try:
        result = callable_(*args)
    except TherapeuticAssessmentError as exc:
        return fail(exc.code, exc.message, status=exc.status, details=exc.details)
    if isinstance(result, tuple):
        data, status = result
        return ok(data, status=status)
    return ok(result)


def _payload():
    return request.get_json(silent=True) or {}


def _key():
    return str(request.headers.get("Idempotency-Key") or "")


@bp.get("/service-levels")
def get_service_levels_route():
    actor, error = _actor()
    return error or ok(service_level_status())


@bp.get("/cases")
def get_cases_route():
    actor, error = _actor()
    return error or _respond(list_cases, actor)


@bp.post("/cases")
def post_case_route():
    actor, error = _actor()
    return error or _respond(create_case, actor, _payload(), _key())


@bp.get("/cases/<case_id>")
def get_case_route(case_id: str):
    actor, error = _actor()
    return error or _respond(get_case, actor, case_id)


@bp.patch("/cases/<case_id>/scope")
def patch_scope_route(case_id: str):
    actor, error = _actor()
    return error or _respond(update_scope, actor, case_id, _payload(), _key())


@bp.patch("/cases/<case_id>/question")
def patch_question_route(case_id: str):
    actor, error = _actor()
    return error or _respond(update_question, actor, case_id, _payload(), _key())


@bp.post("/cases/<case_id>/transitions")
def post_transition_route(case_id: str):
    actor, error = _actor()
    return error or _respond(transition_case, actor, case_id, _payload(), _key())


@bp.get("/cases/<case_id>/evidence")
def get_evidence_route(case_id: str):
    actor, error = _actor()
    return error or _respond(list_evidence, actor, case_id)


@bp.post("/cases/<case_id>/evidence")
def post_evidence_route(case_id: str):
    actor, error = _actor()
    return error or _respond(create_evidence, actor, case_id, _payload(), _key())


@bp.post("/evidence/<evidence_id>/review")
def post_evidence_review_route(evidence_id: str):
    actor, error = _actor()
    return error or _respond(review_hypothesis, actor, evidence_id, _payload(), _key())


@bp.post("/cases/<case_id>/disagree")
def post_disagree_route(case_id: str):
    actor, error = _actor()
    return error or _respond(participant_transition, actor, case_id, _payload(), _key(), "disagree")


@bp.post("/cases/<case_id>/withdraw")
def post_withdraw_route(case_id: str):
    actor, error = _actor()
    return error or _respond(participant_transition, actor, case_id, _payload(), _key(), "withdraw")


@bp.post("/cases/<case_id>/assign")
def post_assign_route(case_id: str):
    actor, error = _actor()
    return error or _respond(assign_case, actor, case_id, _payload(), _key())


@bp.post("/cases/<case_id>/readiness")
def post_readiness_route(case_id: str):
    actor, error = _actor()
    return error or _respond(set_readiness, actor, case_id, _payload(), _key())


@bp.post("/cases/<case_id>/feedback-versions")
def post_feedback_route(case_id: str):
    actor, error = _actor()
    return error or _respond(create_feedback, actor, case_id, _payload(), _key())


@bp.post("/feedback-versions/<feedback_id>/review")
def post_review_route(feedback_id: str):
    actor, error = _actor()
    return error or _respond(review_feedback, actor, feedback_id, _payload(), _key())


@bp.post("/feedback-versions/<feedback_id>/send")
def post_send_route(feedback_id: str):
    actor, error = _actor()
    return error or _respond(send_feedback, actor, feedback_id, _key())


@bp.post("/cases/<case_id>/actions")
def post_action_route(case_id: str):
    actor, error = _actor()
    return error or _respond(create_action, actor, case_id, _payload(), _key())


@bp.patch("/actions/<action_id>")
def patch_action_route(action_id: str):
    actor, error = _actor()
    return error or _respond(update_action, actor, action_id, _payload(), _key())
