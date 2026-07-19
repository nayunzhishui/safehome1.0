"""Controlled AI QA synthetic research sandbox endpoints."""

from flask import Blueprint, request

from routes.auth_utils import AuthError, auth_error_response, require_role
from routes.utils import fail, ok
from services.ai_qa_service import (
    AiQaError,
    activate_kill_switch,
    create_session,
    delete_session,
    get_config_status,
    get_session,
    list_review_evidence,
    list_sessions,
    review_evaluation,
    run_evaluation,
    save_feedback,
    send_message,
)


bp = Blueprint("ai_qa", __name__, url_prefix="/api/ai-qa")


def _actor(*roles: str):
    try:
        return require_role(*roles, allow_legacy_admin=True), None
    except AuthError as exc:
        return None, auth_error_response(exc)


def _response(callback):
    try:
        return ok(callback())
    except AiQaError as exc:
        return fail(exc.code, str(exc), status=exc.status, details=exc.details or None)


@bp.get("/config")
def ai_qa_config():
    return _response(get_config_status)


@bp.get("/sessions")
def ai_qa_sessions():
    actor, error = _actor("researcher", "admin")
    if error:
        return error
    return _response(lambda: {"items": list_sessions(actor)})


@bp.post("/sessions")
def ai_qa_session_create():
    actor, error = _actor("researcher", "admin")
    if error:
        return error
    payload = request.get_json(silent=True) or {}
    return _response(lambda: create_session(actor, payload))


@bp.get("/sessions/<session_id>")
def ai_qa_session_detail(session_id: str):
    actor, error = _actor("researcher", "admin")
    if error:
        return error
    return _response(lambda: get_session(actor, session_id))


@bp.delete("/sessions/<session_id>")
def ai_qa_session_delete(session_id: str):
    actor, error = _actor("researcher", "admin")
    if error:
        return error
    return _response(lambda: delete_session(actor, session_id))


@bp.post("/sessions/<session_id>/messages")
def ai_qa_message_create(session_id: str):
    actor, error = _actor("researcher", "admin")
    if error:
        return error
    payload = request.get_json(silent=True) or {}
    return _response(lambda: send_message(actor, session_id, payload))


@bp.post("/messages/<message_id>/feedback")
def ai_qa_message_feedback(message_id: str):
    actor, error = _actor("researcher", "admin")
    if error:
        return error
    payload = request.get_json(silent=True) or {}
    return _response(lambda: save_feedback(actor, message_id, payload))


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
