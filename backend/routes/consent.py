"""Consent record endpoints for user agreement and research authorization."""

from flask import Blueprint, request

from database import get_connection, row_to_dict, rows_to_dicts
from routes.auth_utils import AuthError, auth_error_response, require_capability, require_login
from routes.utils import fail, ok, parse_bool
from services.consent_service import (
    ConsentError,
    append_consent_event,
    create_consent_annotation,
    latest_consent_event,
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
    "ai_assistance",
    "relationship_analysis",
    "secondary_research",
}

DEFAULT_CONSENT_VERSION = "2026.07-consent-v2"


def get_latest_consent(conn, user_id: str, consent_type: str) -> dict | None:
    return latest_consent_event(conn, user_id, consent_type)


@bp.post("")
def create_consent_record():
    payload = request.get_json(silent=True) or {}
    try:
        actor = require_login(allow_legacy_admin=False)
    except AuthError as exc:
        return auth_error_response(exc)

    user_id = str(payload.get("user_id") or payload.get("subject_id") or actor["id"]).strip()
    if user_id != str(actor["id"]):
        return fail("consent_self_only", "普通同意接口只能记录本人决定。", status=403)

    consent_type = str(payload.get("consent_type") or "").strip()
    if consent_type not in ALLOWED_CONSENT_TYPES:
        return fail("validation_error", "consent_type 不在支持范围内")

    if "agreed" not in payload:
        return fail("validation_error", "缺少 agreed 字段")

    agreed = parse_bool(payload.get("agreed"), False)
    consent_version = str(payload.get("consent_version") or DEFAULT_CONSENT_VERSION).strip()
    if not consent_version or len(consent_version) > 120:
        return fail("validation_error", "consent_version 无效")

    try:
        with get_connection() as conn:
            item, created = append_consent_event(
                conn,
                actor_id=str(actor["id"]),
                subject_id=str(actor["id"]),
                consent_type=consent_type,
                consent_version=consent_version,
                agreed=agreed,
                purpose=payload.get("purpose"),
                processor=str(payload.get("processor") or "safehome"),
                text_hash=payload.get("text_hash"),
                source="participant_self",
                reason=payload.get("reason"),
                evidence_ref=payload.get("evidence_ref"),
                expected_latest_id=payload.get("expected_latest_id"),
                require_latest_guard=True,
            )
            conn.commit()
    except ConsentError as exc:
        return fail(exc.code, str(exc), status=exc.status)
    return ok(item, status=201 if created else 200)


@bp.get("")
def list_consent_records():
    try:
        actor = require_login(allow_legacy_admin=False)
    except AuthError as exc:
        return auth_error_response(exc)
    user_id = str(request.args.get("user_id") or actor["id"]).strip()
    if user_id != str(actor["id"]):
        return fail("consent_self_only", "只能查看本人的同意记录。", status=403)

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


@bp.post("/<consent_record_id>/annotations")
def add_consent_annotation(consent_record_id: str):
    payload = request.get_json(silent=True) or {}
    try:
        actor = require_capability("privacy.consent.annotate", allow_legacy_admin=False)
        with get_connection() as conn:
            item = create_consent_annotation(
                conn,
                actor_id=str(actor["id"]),
                consent_record_id=consent_record_id,
                annotation_type=str(payload.get("annotation_type") or "").strip(),
                reason=str(payload.get("reason") or ""),
                evidence_ref=str(payload.get("evidence_ref") or ""),
                supersedes_id=payload.get("supersedes_id"),
            )
            conn.commit()
    except AuthError as exc:
        return auth_error_response(exc)
    except ConsentError as exc:
        return fail(exc.code, str(exc), status=exc.status)
    return ok(item, status=201)
