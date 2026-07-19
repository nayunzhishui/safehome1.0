"""Participant feedback ledger endpoints."""

from flask import Blueprint, request

from routes.auth_utils import AuthError, auth_error_response, require_login, require_role
from routes.utils import fail, ok
from services.feedback_ledger_service import (
    FeedbackLedgerError,
    create_feedback_entry,
    list_feedback_entries,
    researcher_feedback_summary,
)


bp = Blueprint("feedback_ledger", __name__, url_prefix="/api/feedback-ledger")


def _service_error(exc: FeedbackLedgerError):
    return fail(exc.code, exc.message, status=exc.status)


@bp.post("")
def create_entry():
    try:
        actor = require_login(allow_legacy_admin=False)
        if actor.get("role") not in {"parent", "student"}:
            raise AuthError("当前接口只供参与者本人使用", status=403)
        item, status = create_feedback_entry(
            str(actor["id"]),
            request.get_json(silent=True) or {},
            request.headers.get("Idempotency-Key", ""),
        )
    except AuthError as exc:
        return auth_error_response(exc)
    except FeedbackLedgerError as exc:
        return _service_error(exc)
    return ok(item, status=status)


@bp.get("")
def list_entries():
    try:
        actor = require_login(allow_legacy_admin=False)
        if actor.get("role") not in {"parent", "student"}:
            raise AuthError("当前接口只供参与者本人使用", status=403)
        items = list_feedback_entries(
            str(actor["id"]),
            str(request.args.get("source_type") or "").strip(),
            str(request.args.get("source_id") or "").strip(),
        )
    except AuthError as exc:
        return auth_error_response(exc)
    return ok({"items": items, "count": len(items)})


@bp.get("/summary")
def summary():
    try:
        actor = require_role("researcher", "supervisor", "admin", allow_legacy_admin=True)
        data = researcher_feedback_summary(actor, str(request.args.get("user_id") or "").strip())
    except AuthError as exc:
        return auth_error_response(exc)
    except FeedbackLedgerError as exc:
        return _service_error(exc)
    return ok(data)
