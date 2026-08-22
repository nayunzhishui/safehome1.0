"""Controlled AI QA synthetic research sandbox endpoints."""

from flask import Blueprint, current_app, request

from database import get_connection
from routes.auth_utils import route_actor as _actor
from routes.utils import fail, ok
from services.participant_safeguard_service import (
    ParticipantSafeguardError,
    public_status,
    safeguards_enforced,
)
from services.ai_participant_delivery_service import (
    get_participant_delivery_session,
    send_participant_delivery_message,
)
from services.ai_provider_governance_service import (
    list_provider_candidates,
    list_provider_evidence,
    record_provider_evidence,
    verify_provider_evidence,
)
from services.ai_qa_service import (
    AiQaError,
    activate_kill_switch,
    create_session,
    delete_session,
    get_config_status,
    get_use_case_catalog,
    list_review_evidence,
    list_sessions,
    purge_expired_synthetic_data,
    review_evaluation,
    run_evaluation,
    save_feedback,
)
from services.ai_qa_retrieval_service import (
    KnowledgeError,
    list_knowledge,
    register_public_candidate,
    retrieve_published_content,
    run_retrieval_evaluation,
    sync_approved_knowledge,
)
from services.ai_qa_review_service import (
    AiQaReviewError,
    decide_review_case,
    get_review_case,
    list_review_cases,
)
from services.ai_qa_release_service import (
    AiQaReleaseError,
    create_release_evidence_package,
    release_status,
    rollback_release,
    transition_release,
)


bp = Blueprint("ai_qa", __name__, url_prefix="/api/ai-qa")


def _session_actor():
    roles = ["researcher", "supervisor", "admin"]
    if current_app.config.get("AI_QA_ENABLED", False):
        roles = ["parent", "student", *roles]
    actor, error = _actor(*roles)
    if error or not actor:
        return actor, error
    if actor.get("role") == "student" and safeguards_enforced():
        try:
            with get_connection() as conn:
                status = public_status(conn, str(actor["id"]))
        except ParticipantSafeguardError as exc:
            return None, fail(exc.code, exc.message, status=exc.status, details=exc.details or None)
        if status.get("age_verification_required"):
            return None, fail(
                "age_verification_required",
                "使用支持性问答前需要先完成年龄确认。",
                status=403,
                details=status,
            )
        if status.get("minor_safeguards_required") and status.get("status") != "active":
            return None, fail(
                "minor_safeguards_required",
                "未满14周岁参与者需要先完成监护人授权和儿童确认，才能使用支持性问答。",
                status=403,
                details=status,
            )
    return actor, None


def _response(callback):
    try:
        result = callback()
        if (
            isinstance(result, tuple)
            and len(result) == 2
            and isinstance(result[1], int)
        ):
            return ok(result[0], status=result[1])
        return ok(result)
    except (
        AiQaError,
        KnowledgeError,
        AiQaReviewError,
        AiQaReleaseError,
    ) as exc:
        return fail(exc.code, str(exc), status=exc.status, details=exc.details or None)


@bp.get("/config")
def ai_qa_config():
    return _response(get_config_status)


@bp.get("/use-cases")
def ai_qa_use_cases():
    return _response(get_use_case_catalog)


@bp.get("/providers")
def ai_qa_providers():
    actor, error = _actor("researcher", "supervisor", "admin")
    if error:
        return error
    return _response(lambda: list_provider_candidates(actor))


@bp.get("/knowledge")
def ai_qa_knowledge():
    _current_actor, error = _actor("researcher", "supervisor", "admin")
    if error:
        return error
    return _response(list_knowledge)


@bp.post("/knowledge/rebuild")
def ai_qa_knowledge_rebuild():
    actor, error = _actor("supervisor", "admin")
    if error:
        return error
    return _response(lambda: sync_approved_knowledge(actor))


@bp.get("/knowledge/retrieve")
def ai_qa_knowledge_retrieve():
    _current_actor, error = _actor("researcher", "supervisor", "admin")
    if error:
        return error
    query = str(request.args.get("query") or "")
    method = str(request.args.get("method") or "hybrid")
    audience = str(request.args.get("audience") or "researcher")
    limit = request.args.get("limit", 4)
    try:
        parsed_limit = int(limit)
    except (TypeError, ValueError):
        parsed_limit = 4
    return _response(
        lambda: retrieve_published_content(
            query,
            parsed_limit,
            method=method,
            audience=audience,
        )
    )


@bp.post("/knowledge/candidates")
def ai_qa_knowledge_candidate_create():
    actor, error = _actor("supervisor", "admin")
    if error:
        return error
    payload = request.get_json(silent=True) or {}
    key = str(request.headers.get("Idempotency-Key") or "")
    return _response(lambda: register_public_candidate(actor, payload, key))


@bp.post("/knowledge/evaluation/run")
def ai_qa_knowledge_evaluation_run():
    actor, error = _actor("researcher", "supervisor", "admin")
    if error:
        return error
    payload = request.get_json(silent=True) or {}
    return _response(lambda: run_retrieval_evaluation(actor, payload))


@bp.get("/providers/evidence")
def ai_qa_provider_evidence():
    actor, error = _actor("researcher", "supervisor", "admin")
    if error:
        return error
    return _response(lambda: list_provider_evidence(actor))


@bp.post("/providers/evidence")
def ai_qa_provider_evidence_create():
    actor, error = _actor("supervisor", "admin")
    if error:
        return error
    payload = request.get_json(silent=True) or {}
    key = str(request.headers.get("Idempotency-Key") or "").strip()
    return _response(lambda: record_provider_evidence(actor, payload, key))


@bp.post("/providers/evidence/<evidence_id>/verify")
def ai_qa_provider_evidence_verify(evidence_id: str):
    actor, error = _actor("supervisor", "admin")
    if error:
        return error
    payload = request.get_json(silent=True) or {}
    key = str(request.headers.get("Idempotency-Key") or "").strip()
    return _response(
        lambda: verify_provider_evidence(actor, evidence_id, payload, key)
    )


@bp.get("/sessions")
def ai_qa_sessions():
    actor, error = _session_actor()
    if error:
        return error
    return _response(lambda: {"items": list_sessions(actor)})


@bp.post("/sessions")
def ai_qa_session_create():
    actor, error = _session_actor()
    if error:
        return error
    payload = request.get_json(silent=True) or {}
    return _response(lambda: create_session(actor, payload))


@bp.get("/sessions/<session_id>")
def ai_qa_session_detail(session_id: str):
    actor, error = _session_actor()
    if error:
        return error
    return _response(lambda: get_participant_delivery_session(actor, session_id))


@bp.delete("/sessions/<session_id>")
def ai_qa_session_delete(session_id: str):
    actor, error = _session_actor()
    if error:
        return error
    return _response(lambda: delete_session(actor, session_id))


@bp.post("/sessions/<session_id>/messages")
def ai_qa_message_create(session_id: str):
    actor, error = _session_actor()
    if error:
        return error
    payload = request.get_json(silent=True) or {}
    return _response(lambda: send_participant_delivery_message(actor, session_id, payload))


@bp.post("/messages/<message_id>/feedback")
def ai_qa_message_feedback(message_id: str):
    actor, error = _session_actor()
    if error:
        return error
    payload = request.get_json(silent=True) or {}
    return _response(lambda: save_feedback(actor, message_id, payload))


@bp.get("/review-cases")
def ai_qa_review_cases():
    actor, error = _actor("researcher", "supervisor", "admin")
    if error:
        return error
    return _response(lambda: list_review_cases(actor, request.args))


@bp.get("/review-cases/<case_id>")
def ai_qa_review_case_detail(case_id: str):
    actor, error = _actor("researcher", "supervisor", "admin")
    if error:
        return error
    return _response(lambda: get_review_case(actor, case_id))


@bp.post("/review-cases/<case_id>/decisions")
def ai_qa_review_case_decision(case_id: str):
    actor, error = _actor("researcher", "supervisor", "admin")
    if error:
        return error
    payload = request.get_json(silent=True) or {}
    key = str(request.headers.get("Idempotency-Key") or "")
    return _response(
        lambda: decide_review_case(actor, case_id, payload, key)
    )


@bp.post("/evaluation/run")
def ai_qa_evaluation_run():
    actor, error = _actor("researcher", "supervisor", "admin")
    if error:
        return error
    return _response(lambda: run_evaluation(actor))


@bp.get("/review/evidence")
def ai_qa_review_evidence():
    current_actor, error = _actor("researcher", "supervisor", "admin")
    if error:
        return error
    return _response(lambda: list_review_evidence(current_actor))


@bp.post("/evaluation/<run_id>/reviews")
def ai_qa_evaluation_review(run_id: str):
    actor, error = _actor("supervisor", "admin")
    if error:
        return error
    payload = request.get_json(silent=True) or {}
    return _response(lambda: review_evaluation(actor, run_id, payload))


@bp.post("/kill-switch")
def ai_qa_kill_switch():
    actor, error = _actor("admin")
    if error:
        return error
    payload = request.get_json(silent=True) or {}
    return _response(lambda: activate_kill_switch(actor, payload))


@bp.post("/retention/purge")
def ai_qa_retention_purge():
    actor, error = _actor("admin")
    if error:
        return error
    payload = request.get_json(silent=True) or {}
    return _response(lambda: purge_expired_synthetic_data(actor, payload))


@bp.get("/release/status")
def ai_qa_release_status():
    actor, error = _actor("researcher", "supervisor", "admin")
    if error:
        return error
    return _response(lambda: release_status(actor))


@bp.post("/release/transition")
def ai_qa_release_transition():
    actor, error = _actor("admin")
    if error:
        return error
    payload = request.get_json(silent=True) or {}
    key = str(request.headers.get("Idempotency-Key") or "")
    return _response(lambda: transition_release(actor, payload, key))


@bp.post("/release/rollback")
def ai_qa_release_rollback():
    actor, error = _actor("admin")
    if error:
        return error
    payload = request.get_json(silent=True) or {}
    key = str(request.headers.get("Idempotency-Key") or "")
    return _response(lambda: rollback_release(actor, payload, key))


@bp.post("/release/evidence-packages")
def ai_qa_release_evidence_package():
    actor, error = _actor("supervisor", "admin")
    if error:
        return error
    return _response(lambda: create_release_evidence_package(actor))
