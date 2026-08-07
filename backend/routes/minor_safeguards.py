"""Age confirmation and general under-14 participant safeguard endpoints."""

from flask import Blueprint, request

from database import get_connection
from routes.auth_utils import AuthError, auth_error_response, require_login, require_role
from routes.utils import fail, ok
from services.participant_safeguard_service import (
    ParticipantSafeguardError,
    confirm_age_for_user,
    public_status,
    record_child_assent,
    record_guardian_consent,
)
from services.schema_migration_service import apply_pending_schema_migrations

bp = Blueprint("minor_safeguards", __name__, url_prefix="/api/minor-safeguards")


def _error(exc: ParticipantSafeguardError):
    return fail(exc.code, exc.message, status=exc.status, details=exc.details or None)


@bp.get("/status")
def status():
    try:
        actor = require_login(allow_legacy_admin=False)
    except AuthError as exc:
        return auth_error_response(exc)

    requested_child_id = str(request.args.get("child_user_id") or "").strip()
    user_id = str(actor["id"])
    if requested_child_id and requested_child_id != user_id:
        if actor.get("role") not in {"parent", "supervisor", "admin"}:
            return fail("forbidden", "当前账号不能查看其他参与者的年龄保护状态。", status=403)
        user_id = requested_child_id
        if actor.get("role") == "parent":
            with get_connection() as conn:
                apply_pending_schema_migrations(conn)
                link = conn.execute(
                    """
                    SELECT id FROM family_links
                    WHERE parent_user_id = ? AND student_user_id = ? AND status = 'active'
                    LIMIT 1
                    """,
                    (str(actor["id"]), user_id),
                ).fetchone()
                if link is None:
                    return fail("forbidden", "只能查看已绑定学生的保护状态。", status=403)
    try:
        with get_connection() as conn:
            apply_pending_schema_migrations(conn)
            return ok(public_status(conn, user_id))
    except ParticipantSafeguardError as exc:
        return _error(exc)


@bp.post("/age-confirmation")
def confirm_age():
    try:
        actor = require_role("student", allow_legacy_admin=False)
    except AuthError as exc:
        return auth_error_response(exc)

    payload = request.get_json(silent=True) or {}
    age_band = str(payload.get("age_band") or "").strip()
    try:
        with get_connection() as conn:
            apply_pending_schema_migrations(conn)
            result = confirm_age_for_user(
                conn,
                str(actor["id"]),
                age_band,
                method="participant_self_declaration",
                actor_id=str(actor["id"]),
            )
            conn.commit()
            return ok(result)
    except ParticipantSafeguardError as exc:
        return _error(exc)


@bp.post("/guardian-consent")
def guardian_consent():
    try:
        actor = require_role("parent", allow_legacy_admin=False)
    except AuthError as exc:
        return auth_error_response(exc)

    payload = request.get_json(silent=True) or {}
    child_user_id = str(payload.get("child_user_id") or "").strip()
    if not child_user_id or "agreed" not in payload:
        return fail("missing_fields", "需要 child_user_id 和 agreed。", status=400)
    agreed = payload.get("agreed") is True
    try:
        with get_connection() as conn:
            apply_pending_schema_migrations(conn)
            result = record_guardian_consent(conn, str(actor["id"]), child_user_id, agreed)
            conn.commit()
            return ok(result)
    except ParticipantSafeguardError as exc:
        return _error(exc)


@bp.post("/child-assent")
def child_assent():
    try:
        actor = require_role("student", allow_legacy_admin=False)
    except AuthError as exc:
        return auth_error_response(exc)

    payload = request.get_json(silent=True) or {}
    if "assented" not in payload and not payload.get("withdraw"):
        return fail("missing_fields", "需要 assented 或 withdraw。", status=400)
    try:
        with get_connection() as conn:
            apply_pending_schema_migrations(conn)
            result = record_child_assent(
                conn,
                str(actor["id"]),
                bool(payload.get("assented")),
                withdraw=bool(payload.get("withdraw")),
            )
            conn.commit()
            return ok(result)
    except ParticipantSafeguardError as exc:
        return _error(exc)


@bp.post("/age-override")
def supervised_age_override():
    """Allow a supervised correction when an under-14 record needs updating."""
    try:
        actor = require_role("supervisor", "admin", allow_legacy_admin=True)
    except AuthError as exc:
        return auth_error_response(exc)
    payload = request.get_json(silent=True) or {}
    user_id = str(payload.get("user_id") or "").strip()
    age_band = str(payload.get("age_band") or "").strip()
    if not user_id or not age_band:
        return fail("missing_fields", "需要 user_id 和 age_band。", status=400)
    try:
        with get_connection() as conn:
            apply_pending_schema_migrations(conn)
            result = confirm_age_for_user(
                conn,
                user_id,
                age_band,
                method="supervised_age_correction",
                actor_id=str(actor["id"]),
                allow_under14_upgrade=True,
            )
            conn.commit()
            return ok(result)
    except ParticipantSafeguardError as exc:
        return _error(exc)
