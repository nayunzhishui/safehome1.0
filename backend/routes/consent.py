"""Consent record endpoints for user agreement and research authorization."""

from flask import Blueprint, request

from database import get_connection, new_id, now_iso, row_to_dict, rows_to_dicts
from routes.auth_utils import AuthError, auth_error_response, require_login
from routes.utils import fail, ok, parse_bool, require_user_id
from services.participant_safeguard_service import (
    ParticipantSafeguardError,
    get_participant_safeguard_status,
    record_age_confirmation,
    record_guardian_processing_consent,
    record_minor_assent,
)

bp = Blueprint("consent", __name__, url_prefix="/api/consent")

ALLOWED_CONSENT_TYPES = {
    "user_agreement",
    "privacy_policy",
    "non_diagnostic_notice",
    "research_authorization",
    "anonymous_research",
    "contact_permission",
    "service_data",
    "quality_evaluation",
    "model_training",
    "secondary_research",
}

DEFAULT_CONSENT_VERSION = "2026.06-consent-v1"


def get_latest_consent(conn, user_id: str, consent_type: str) -> dict | None:
    row = conn.execute(
        """
        SELECT * FROM consent_records
        WHERE user_id = ? AND consent_type = ?
        ORDER BY created_at DESC
        LIMIT 1
        """,
        (user_id, consent_type),
    ).fetchone()
    return row_to_dict(row)


def _safeguard_error(exc: ParticipantSafeguardError):
    return fail(exc.code, str(exc), status=exc.status, details=exc.details)


@bp.post("/age-confirmation")
def age_confirmation():
    try:
        actor = require_login(allow_legacy_admin=False)
    except AuthError as exc:
        return auth_error_response(exc)
    payload = request.get_json(silent=True) or {}
    try:
        return ok(record_age_confirmation(actor, payload.get("age_band")), status=201)
    except ParticipantSafeguardError as exc:
        return _safeguard_error(exc)


@bp.post("/guardian-sensitive-processing")
def guardian_sensitive_processing():
    try:
        actor = require_login(allow_legacy_admin=False)
    except AuthError as exc:
        return auth_error_response(exc)
    payload = request.get_json(silent=True) or {}
    if "agreed" not in payload:
        return fail("validation_error", "缺少 agreed 字段")
    try:
        return ok(
            record_guardian_processing_consent(
                actor,
                str(payload.get("child_user_id") or ""),
                parse_bool(payload.get("agreed"), False),
            ),
            status=201,
        )
    except ParticipantSafeguardError as exc:
        return _safeguard_error(exc)


@bp.post("/minor-assent")
def minor_assent():
    try:
        actor = require_login(allow_legacy_admin=False)
    except AuthError as exc:
        return auth_error_response(exc)
    payload = request.get_json(silent=True) or {}
    if "agreed" not in payload:
        return fail("validation_error", "缺少 agreed 字段")
    try:
        return ok(record_minor_assent(actor, parse_bool(payload.get("agreed"), False)), status=201)
    except ParticipantSafeguardError as exc:
        return _safeguard_error(exc)


@bp.get("/participant-safeguards")
def participant_safeguards():
    try:
        actor = require_login(allow_legacy_admin=False)
    except AuthError as exc:
        return auth_error_response(exc)
    role = str(actor.get("role") or "")
    requested = str(request.args.get("user_id") or "").strip()
    if role == "student":
        user_id = str(actor["id"])
    elif role in {"admin", "supervisor", "researcher"} and requested:
        user_id = requested
    else:
        return fail("forbidden", "只能查看自己的保护状态，后台角色需显式指定 user_id。", status=403)
    try:
        return ok(get_participant_safeguard_status(user_id))
    except ParticipantSafeguardError as exc:
        return _safeguard_error(exc)


@bp.post("")
def create_consent_record():
    payload = request.get_json(silent=True) or {}
    try:
        user_id = require_user_id(payload)
    except ValueError as exc:
        return fail("validation_error", str(exc))

    consent_type = str(payload.get("consent_type") or "").strip()
    if consent_type not in ALLOWED_CONSENT_TYPES:
        return fail("validation_error", "consent_type 不在支持范围内")

    if "agreed" not in payload:
        return fail("validation_error", "缺少 agreed 字段")

    agreed = parse_bool(payload.get("agreed"), False)
    consent_version = str(payload.get("consent_version") or DEFAULT_CONSENT_VERSION).strip()
    if not consent_version:
        return fail("validation_error", "缺少 consent_version 字段")

    timestamp = now_iso()
    record_id = new_id("consent")
    revoked_at = timestamp if not agreed else None

    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO consent_records (
                id, user_id, consent_type, consent_version, agreed,
                agreed_at, revoked_at, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record_id,
                user_id,
                consent_type,
                consent_version,
                1 if agreed else 0,
                timestamp,
                revoked_at,
                timestamp,
            ),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM consent_records WHERE id = ?", (record_id,)).fetchone()

    return ok(row_to_dict(row), status=201)


@bp.get("")
def list_consent_records():
    try:
        user_id = require_user_id({"user_id": request.args.get("user_id")})
    except ValueError as exc:
        return fail("validation_error", str(exc))

    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT * FROM consent_records
            WHERE user_id = ?
            ORDER BY created_at DESC
            """,
            (user_id,),
        ).fetchall()

    return ok({"items": rows_to_dicts(rows), "count": len(rows)})
