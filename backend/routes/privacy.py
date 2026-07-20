"""Privacy center endpoints for consent withdrawal and data requests."""

from flask import Blueprint, current_app, request

from routes.consent import DEFAULT_CONSENT_VERSION
from routes.auth_utils import AuthError, auth_error_response, get_current_actor, require_login, require_role
from routes.utils import fail, ok, parse_int
from services.privacy_request_service import (
    PrivacyRequestError,
    appeal_participant_request,
    approve_privacy_execution,
    cancel_participant_request,
    create_participant_delete_request,
    execute_privacy_request,
    export_participant_privacy_summary,
    get_participant_consent_status,
    get_deletion_verification,
    get_reviewer_request,
    list_reviewer_requests,
    preview_privacy_request,
    research_revoked_filter,
    revoke_research_consent,
    list_participant_requests,
    transition_reviewer_request,
)

bp = Blueprint("privacy", __name__, url_prefix="/api/privacy")

def resolve_privacy_owner(requested_user_id: str | None) -> tuple[str, dict]:
    user_id = str(requested_user_id or "").strip()
    actor = get_current_actor(allow_legacy_admin=False)
    if actor is not None:
        if user_id and actor["id"] != user_id:
            raise AuthError("只能操作自己的隐私数据", status=403)
        return str(actor["id"]), actor
    if str(current_app.config.get("APP_ENV", "development")).lower() == "production":
        raise AuthError("隐私中心需要先登录", status=401)
    if not user_id:
        raise ValueError("请提供匿名 user_id")
    return user_id, {"id": user_id, "role": "anonymous", "source": "anonymous_trial"}

@bp.get("/consent-status")
def consent_status():
    try:
        user_id, _actor = resolve_privacy_owner(request.args.get("user_id"))
    except AuthError as exc:
        return auth_error_response(exc)
    except ValueError as exc:
        return fail("validation_error", str(exc), status=400)

    return ok(get_participant_consent_status(user_id))


@bp.post("/revoke-consent")
def revoke_consent():
    payload = request.get_json(silent=True) or {}
    try:
        user_id, actor = resolve_privacy_owner(payload.get("user_id"))
    except AuthError as exc:
        return auth_error_response(exc)
    except ValueError as exc:
        return fail("validation_error", str(exc), status=400)

    try:
        return ok(revoke_research_consent(user_id, actor, payload, default_version=DEFAULT_CONSENT_VERSION))
    except PrivacyRequestError as exc:
        return fail(exc.code, str(exc), status=exc.status)


@bp.post("/delete-my-data")
def delete_my_data():
    payload = request.get_json(silent=True) or {}
    try:
        user_id, actor = resolve_privacy_owner(payload.get("user_id"))
    except AuthError as exc:
        return auth_error_response(exc)
    except ValueError as exc:
        return fail("validation_error", str(exc), status=400)

    reason = str(payload.get("reason") or "").strip()[:500]
    item, status = create_participant_delete_request(user_id, actor, reason)
    return ok(item, status=status)


@bp.get("/requests")
def list_privacy_requests():
    try:
        user_id, _actor = resolve_privacy_owner(request.args.get("user_id"))
    except AuthError as exc:
        return auth_error_response(exc)
    except ValueError as exc:
        return fail("validation_error", str(exc), status=400)

    page = max(1, parse_int(request.args.get("page"), 1) or 1)
    page_size = max(1, min(parse_int(request.args.get("page_size"), 20) or 20, 100))
    return ok(list_participant_requests(user_id, page=page, page_size=page_size))


@bp.post("/requests/<request_id>/appeal")
def appeal_privacy_request(request_id: str):
    try:
        actor = require_login(allow_legacy_admin=False)
        item = appeal_participant_request(
            request_id,
            actor,
            str(request.headers.get("Idempotency-Key") or "").strip(),
            str((request.get_json(silent=True) or {}).get("reason") or "").strip(),
        )
    except AuthError as exc:
        return auth_error_response(exc)
    except PrivacyRequestError as exc:
        return fail(exc.code, str(exc), status=exc.status)
    return ok(item)


@bp.post("/requests/<request_id>/cancel")
def cancel_privacy_request(request_id: str):
    try:
        actor = require_login(allow_legacy_admin=False)
        item = cancel_participant_request(
            request_id,
            actor,
            str(request.headers.get("Idempotency-Key") or "").strip(),
            str((request.get_json(silent=True) or {}).get("reason") or "").strip()[:300],
        )
    except AuthError as exc:
        return auth_error_response(exc)
    except PrivacyRequestError as exc:
        return fail(exc.code, str(exc), status=exc.status)
    return ok(item)


def _privacy_reviewer():
    try:
        return require_role("supervisor", "admin", allow_legacy_admin=True), None
    except AuthError as exc:
        return None, auth_error_response(exc)


@bp.get("/admin/requests")
def list_privacy_requests_for_review():
    actor, error = _privacy_reviewer()
    if error:
        return error
    raw_page = parse_int(request.args.get("page"), 1) or 1
    raw_page_size = parse_int(request.args.get("page_size"), 20) or 20
    if raw_page < 1 or raw_page_size < 1 or raw_page_size > 100:
        return fail("validation_error", "page需大于等于1，page_size需为1至100。", status=400)
    try:
        data = list_reviewer_requests(
            actor,
            status=str(request.args.get("status") or "").strip(),
            page=raw_page,
            page_size=raw_page_size,
        )
    except PrivacyRequestError as exc:
        return fail(exc.code, str(exc), status=exc.status)
    return ok(data)


@bp.get("/admin/requests/<request_id>")
def get_privacy_request_for_review(request_id: str):
    actor, error = _privacy_reviewer()
    if error:
        return error
    try:
        data = get_reviewer_request(request_id, actor)
    except PrivacyRequestError as exc:
        return fail(exc.code, str(exc), status=exc.status)
    return ok(data)


@bp.post("/admin/requests/<request_id>/transition")
def transition_privacy_request_for_review(request_id: str):
    actor, error = _privacy_reviewer()
    if error:
        return error
    payload = request.get_json(silent=True) or {}
    try:
        data = transition_reviewer_request(
            request_id,
            actor,
            action=str(payload.get("action") or "").strip(),
            scope=payload.get("scope"),
            note=str(payload.get("note") or "").strip(),
            idempotency_key=str(request.headers.get("Idempotency-Key") or payload.get("idempotency_key") or "").strip(),
        )
    except PrivacyRequestError as exc:
        return fail(exc.code, str(exc), status=exc.status)
    return ok(data)


@bp.get("/admin/requests/<request_id>/preview")
def preview_privacy_request_for_review(request_id: str):
    actor, error = _privacy_reviewer()
    if error:
        return error
    try:
        return ok(preview_privacy_request(request_id, actor))
    except PrivacyRequestError as exc:
        return fail(exc.code, str(exc), status=exc.status)


@bp.post("/admin/requests/<request_id>/approvals")
def approve_privacy_request_execution(request_id: str):
    actor, error = _privacy_reviewer()
    if error:
        return error
    payload = request.get_json(silent=True) or {}
    try:
        data = approve_privacy_execution(
            request_id,
            actor,
            str(payload.get("scope_hash") or "").strip(),
            str(payload.get("policy_version") or "").strip(),
            str(request.headers.get("Idempotency-Key") or payload.get("idempotency_key") or "").strip(),
        )
    except PrivacyRequestError as exc:
        return fail(exc.code, str(exc), status=exc.status)
    return ok(data, status=201)


@bp.post("/admin/requests/<request_id>/execute")
def execute_privacy_request_for_review(request_id: str):
    actor, error = _privacy_reviewer()
    if error:
        return error
    payload = request.get_json(silent=True) or {}
    dry_run = payload.get("dry_run")
    if not isinstance(dry_run, bool):
        return fail("validation_error", "dry_run必须为布尔值。", status=400)
    expected_version = payload.get("expected_version")
    if expected_version is not None and (isinstance(expected_version, bool) or not isinstance(expected_version, int)):
        return fail("validation_error", "expected_version必须为整数。", status=400)
    try:
        data = execute_privacy_request(
            request_id,
            actor,
            dry_run=dry_run,
            expected_version=expected_version,
            idempotency_key=str(request.headers.get("Idempotency-Key") or payload.get("idempotency_key") or "").strip(),
        )
    except PrivacyRequestError as exc:
        return fail(exc.code, str(exc), status=exc.status)
    return ok(data)


@bp.get("/admin/requests/<request_id>/verification")
def get_privacy_deletion_verification(request_id: str):
    actor, error = _privacy_reviewer()
    if error:
        return error
    try:
        return ok(get_deletion_verification(request_id, actor))
    except PrivacyRequestError as exc:
        return fail(exc.code, str(exc), status=exc.status)


@bp.get("/export-my-data")
def export_my_data():
    try:
        user_id, _actor = resolve_privacy_owner(request.args.get("user_id"))
    except AuthError as exc:
        return auth_error_response(exc)
    except ValueError as exc:
        return fail("validation_error", str(exc), status=400)

    return ok(export_participant_privacy_summary(user_id))
