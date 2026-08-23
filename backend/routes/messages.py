"""Thin HTTP adapter for user-facing in-app messages."""

from flask import Blueprint, request

from routes.auth_utils import (
    AuthError,
    auth_error_response,
    require_capability,
    require_login,
    resolve_actor_user_id,
)
from routes.utils import fail, ok, parse_int
from services.message_service import (
    MessageServiceError,
    get_user_message,
    list_user_messages,
    mark_all_read,
    mark_one_read,
    send_message_to_participant,
)


bp = Blueprint("messages", __name__, url_prefix="/api/messages")


def _resolve_message_user_id(
    requested_user_id: str | None = None,
) -> tuple[str | None, dict | None, tuple | None]:
    try:
        actor = require_login(allow_legacy_admin=True)
    except AuthError as exc:
        return None, None, auth_error_response(exc)
    try:
        user_id = resolve_actor_user_id(
            requested_user_id=requested_user_id,
            allow_legacy_admin=True,
        )
    except AuthError as exc:
        return None, actor, auth_error_response(exc)
    return user_id, actor, None


def _service_error(exc: MessageServiceError):
    return fail(exc.code, str(exc), status=exc.status)


@bp.get("")
def list_messages():
    user_id, _actor, error = _resolve_message_user_id(request.args.get("user_id"))
    if error:
        return error
    page = max(1, parse_int(request.args.get("page"), 1))
    page_size = max(1, min(parse_int(request.args.get("page_size") or request.args.get("limit"), 50), 100))
    return ok(list_user_messages(user_id, page=page, page_size=page_size, status=str(request.args.get("status") or "").strip(), message_type=str(request.args.get("message_type") or "").strip()))


@bp.post("")
def send_researcher_message():
    try:
        actor = require_capability("research.message.send", allow_legacy_admin=True)
        item, status = send_message_to_participant(
            actor,
            request.get_json(silent=True) or {},
            str(request.headers.get("Idempotency-Key") or (request.get_json(silent=True) or {}).get("idempotency_key") or "").strip(),
        )
    except AuthError as exc:
        return auth_error_response(exc)
    except MessageServiceError as exc:
        return _service_error(exc)
    return ok(item, status=status)


@bp.post("/read-all")
def mark_all_messages_read():
    payload = request.get_json(silent=True) or {}
    user_id, _actor, error = _resolve_message_user_id(payload.get("user_id") or request.args.get("user_id"))
    if error:
        return error
    return ok(mark_all_read(user_id))


@bp.get("/<message_id>")
def get_message(message_id: str):
    user_id, actor, error = _resolve_message_user_id(request.args.get("user_id"))
    if error:
        return error
    try:
        return ok(
            get_user_message(
                user_id,
                message_id,
                mark_read=str(actor["id"]) == str(user_id),
            )
        )
    except MessageServiceError as exc:
        return _service_error(exc)


@bp.post("/<message_id>/read")
def mark_message_read(message_id: str):
    payload = request.get_json(silent=True) or {}
    user_id, _actor, error = _resolve_message_user_id(payload.get("user_id") or request.args.get("user_id"))
    if error:
        return error
    try:
        return ok(mark_one_read(user_id, message_id))
    except MessageServiceError as exc:
        return _service_error(exc)
