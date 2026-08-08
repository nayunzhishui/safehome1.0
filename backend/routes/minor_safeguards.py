"""Age confirmation and general under-14 participant safeguard endpoints."""

from flask import Blueprint, request

from database import get_connection
from routes.auth_utils import AuthError, auth_error_response, require_login, require_role
from routes.utils import fail, ok
from services.participant_safeguard_service import (
    ParticipantSafeguardError,
    assert_participant_capability,
    confirm_age_for_user,
    public_status,
    record_child_assent,
    record_guardian_consent,
    safeguards_enforced,
)
from services.schema_migration_service import apply_pending_schema_migrations

bp = Blueprint("minor_safeguards", __name__, url_prefix="/api/minor-safeguards")

DIRECT_PROTECTED_WRITES = {
    ("POST", "/api/diaries"): "sensitive_text",
    ("POST", "/api/profile"): "profile",
}
PROFILE_TEXT_WRITE_SUFFIXES = {"followups", "sandplay"}
BACKEND_TARGET_ROLES = {"admin", "supervisor", "researcher"}


def _error(exc: ParticipantSafeguardError):
    return fail(exc.code, exc.message, status=exc.status, details=exc.details or None)


def _strict_bool_value(value, field: str, *, present: bool = True, default=None):
    if not present:
        return default
    if type(value) is not bool:
        raise ParticipantSafeguardError(
            "invalid_boolean",
            f"{field} 必须是 JSON 布尔值 true 或 false。",
            400,
            {"field": field},
        )
    return value


def _profile_id_from_path(path: str) -> str | None:
    parts = [part for part in path.split("/") if part]
    if len(parts) != 4 or parts[0] != "api" or parts[1] != "profile-results":
        return None
    if parts[3] not in PROFILE_TEXT_WRITE_SUFFIXES:
        return None
    return parts[2]


def _profile_owner(profile_id: str) -> str | None:
    with get_connection() as conn:
        apply_pending_schema_migrations(conn)
        row = conn.execute(
            "SELECT user_id FROM student_profiles WHERE id = ?",
            (profile_id,),
        ).fetchone()
    return str(row["user_id"]) if row is not None else None


def _direct_target_user(actor: dict) -> str:
    if str(actor.get("role") or "") not in BACKEND_TARGET_ROLES:
        return str(actor["id"])
    payload = request.get_json(silent=True) or {}
    return str(payload.get("user_id") or actor["id"])


def _actor_may_access_profile_target(actor: dict, owner_user_id: str) -> bool:
    role = str(actor.get("role") or "")
    return role in BACKEND_TARGET_ROLES or str(actor.get("id") or "") == str(owner_user_id)


@bp.before_app_request
def enforce_general_minor_processing_gate():
    """Protect ordinary sensitive writes while keeping safety/consent exits open.

    This is a defense-in-depth gate above individual feature routes. It applies
    only in pilot/production enforcement mode and deliberately excludes risk
    checks, family binding, consent/withdrawal and human-support endpoints.
    Object authorization always happens before a profile owner's safeguard
    status is evaluated so unauthorized callers cannot infer age/consent state
    from different safeguard error codes.
    """

    if not safeguards_enforced():
        return None

    capability = DIRECT_PROTECTED_WRITES.get((request.method, request.path))
    target_user_id = None
    if capability:
        try:
            actor = require_login(allow_legacy_admin=False)
        except AuthError as exc:
            return auth_error_response(exc)
        target_user_id = _direct_target_user(actor)
    elif request.method == "POST":
        profile_id = _profile_id_from_path(request.path)
        if profile_id:
            try:
                actor = require_login(allow_legacy_admin=False)
            except AuthError as exc:
                return auth_error_response(exc)
            target_user_id = _profile_owner(profile_id)
            if target_user_id and not _actor_may_access_profile_target(actor, target_user_id):
                # Preserve the profile route's normal authorization response.
                # Do not inspect or expose the target's minor-safeguard state.
                return None
            if target_user_id:
                capability = "sensitive_text"

    if not capability or not target_user_id:
        return None
    try:
        assert_participant_capability(target_user_id, capability)
    except ParticipantSafeguardError as exc:
        return _error(exc)
    return None


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
    try:
        agreed = _strict_bool_value(
            payload.get("agreed"),
            "agreed",
            present="agreed" in payload,
        )
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
    try:
        assented = _strict_bool_value(
            payload.get("assented"),
            "assented",
            present="assented" in payload,
        )
        withdraw = _strict_bool_value(
            payload.get("withdraw"),
            "withdraw",
            present="withdraw" in payload,
            default=False,
        )
        if not withdraw and assented is None:
            return fail("missing_fields", "需要 assented 或 withdraw=true。", status=400)
        with get_connection() as conn:
            apply_pending_schema_migrations(conn)
            if assented is True and not withdraw:
                current = public_status(conn, str(actor["id"]))
                if not current.get("guardian_linked"):
                    return fail("guardian_link_required", "未满14岁参与者需要先完成监护人绑定。", status=403)
                if current.get("guardian_consent_status") != "active":
                    return fail("guardian_consent_required", "需要监护人先完成单独同意。", status=403)
            result = record_child_assent(
                conn,
                str(actor["id"]),
                bool(assented) if assented is not None else False,
                withdraw=withdraw,
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
