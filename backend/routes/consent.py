"""Consent record endpoints for user agreement and research authorization."""

from flask import Blueprint, request

from database import get_connection, new_id, now_iso, row_to_dict, rows_to_dicts, write_audit_log
from routes.auth_utils import AuthError, auth_error_response, get_current_actor, resolve_actor_user_id
from routes.utils import fail, ok, parse_bool
from services.participant_safeguard_service import (
    ParticipantSafeguardError,
    public_status,
    safeguards_enforced,
)
from services.research_access_service import ResearchAccessError
from services.research_sensitive_access_service import require_explicit_research_authorization

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
LEGACY_RESEARCH_EXPORT_TYPES_REQUIRING_SUBJECT = {
    "profile",
    "student_profiles",
    "records",
    "student_followups",
    "sandplay",
    "parent_assessments",
}
LEGACY_RESEARCH_EXPORT_TYPES_BLOCKED = {"raw_wide", "long"}


def _legacy_research_workspace_path(path: str) -> bool:
    return path == "/api/research/participants" or path.startswith("/api/research/participants/")


@bp.before_app_request
def enforce_sensitive_research_read_boundary():
    """Fail closed legacy research paths that do not enforce explicit opt-in.

    Researchers must use `/api/research/access/*`, where capability, object
    assignment and current `research_authorization` are checked together.
    Admin exports of participant-derived research data are also subject-scoped
    and explicit-opt-in; bulk raw/long legacy exports stay closed until a
    purpose-scoped replacement exists.
    """

    if request.method != "GET":
        return None

    is_admin_raw_results = request.path == "/api/admin/assessment-results"
    is_admin_export = request.path == "/api/admin/export"
    is_legacy_workspace = _legacy_research_workspace_path(request.path)
    if not (is_admin_raw_results or is_admin_export or is_legacy_workspace):
        return None

    try:
        actor = get_current_actor(allow_legacy_admin=True)
    except AuthError as exc:
        return auth_error_response(exc)

    if actor and actor.get("role") == "researcher":
        return fail(
            "researcher_sensitive_read_disabled",
            "旧研究数据读取路径已关闭。请使用 /api/research/access 下经过 capability、分配范围和明确研究授权校验的接口。",
            status=403,
        )

    if not is_admin_export or not actor or actor.get("role") != "admin":
        return None

    export_type = str(request.args.get("type") or "diaries").strip()
    if export_type in LEGACY_RESEARCH_EXPORT_TYPES_BLOCKED:
        return fail(
            "scoped_research_export_required",
            "raw_wide/long 旧批量研究导出已关闭；请迁移到目的限定、参与者范围明确的受控导出流程。",
            status=403,
        )
    if export_type not in LEGACY_RESEARCH_EXPORT_TYPES_REQUIRING_SUBJECT:
        return None

    user_id = str(request.args.get("user_id") or "").strip()
    if not user_id:
        return fail(
            "research_subject_scope_required",
            "参与者衍生研究数据导出必须明确指定 user_id，并通过当前研究授权校验。",
            status=400,
        )
    try:
        with get_connection() as conn:
            require_explicit_research_authorization(conn, user_id)
    except ResearchAccessError as exc:
        return fail(exc.code, exc.message, status=exc.status, details=exc.details or None)
    return None


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


@bp.post("")
def create_consent_record():
    payload = request.get_json(silent=True) or {}
    try:
        # The token actor is authoritative. user_id in a participant payload
        # is compatibility metadata only and cannot impersonate another user.
        user_id = resolve_actor_user_id(payload=payload, allow_legacy_admin=False, allow_dev_fallback=True)
    except AuthError as exc:
        return auth_error_response(exc)

    consent_type = str(payload.get("consent_type") or "").strip()
    if consent_type not in ALLOWED_CONSENT_TYPES:
        return fail("validation_error", "consent_type 不在支持范围内")

    if "agreed" not in payload:
        return fail("validation_error", "缺少 agreed 字段")

    agreed = parse_bool(payload.get("agreed"), False)
    consent_version = str(payload.get("consent_version") or DEFAULT_CONSENT_VERSION).strip()
    if not consent_version or len(consent_version) > 120:
        return fail("validation_error", "consent_version 无效")

    # AI consent is not sufficient by itself for an under-14 participant.
    # In enforced environments, the guardian relationship, guardian consent
    # and child assent must already be active before affirmative AI consent.
    if consent_type == "ai_assistance" and agreed and safeguards_enforced():
        try:
            with get_connection() as conn:
                safeguard_status = public_status(conn, str(user_id))
        except ParticipantSafeguardError as exc:
            return fail(exc.code, exc.message, status=exc.status, details=exc.details or None)
        if safeguard_status.get("age_verification_required"):
            return fail(
                "age_verification_required",
                "同意 AI 辅助处理前需要先完成年龄确认。",
                status=403,
                details=safeguard_status,
            )
        if safeguard_status.get("minor_safeguards_required") and safeguard_status.get("status") != "active":
            return fail(
                "minor_safeguards_required",
                "未满14周岁参与者需要先完成监护人授权和儿童确认，才能同意 AI 辅助处理。",
                status=403,
                details=safeguard_status,
            )

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
        write_audit_log(
            conn,
            action="consent_recorded",
            actor_id=user_id,
            target_type="consent_record",
            target_id=record_id,
            metadata={"consent_type": consent_type, "agreed": bool(agreed), "consent_version": consent_version},
        )
        conn.commit()
        row = conn.execute("SELECT * FROM consent_records WHERE id = ?", (record_id,)).fetchone()

    return ok(row_to_dict(row), status=201)


@bp.get("")
def list_consent_records():
    try:
        user_id = resolve_actor_user_id(
            requested_user_id=request.args.get("user_id"),
            allow_legacy_admin=False,
            allow_dev_fallback=True,
        )
    except AuthError as exc:
        return auth_error_response(exc)

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
