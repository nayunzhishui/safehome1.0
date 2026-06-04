"""Consent record endpoints for user agreement and research authorization."""

from flask import Blueprint, request

from database import get_connection, new_id, now_iso, row_to_dict, rows_to_dicts
from routes.utils import fail, ok, parse_bool, require_user_id

bp = Blueprint("consent", __name__, url_prefix="/api/consent")

ALLOWED_CONSENT_TYPES = {
    "user_agreement",
    "privacy_policy",
    "non_diagnostic_notice",
    "research_authorization",
    "contact_permission",
}

DEFAULT_CONSENT_VERSION = "2026.06-consent-v1"


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
