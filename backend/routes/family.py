"""Parent-student binding code endpoints."""

from datetime import datetime, timedelta

from flask import Blueprint, request

from database import get_connection, new_id, now_iso, row_to_dict, rows_to_dicts, write_audit_log
from routes.auth_utils import AuthError, auth_error_response, require_login, require_role
from routes.consent import DEFAULT_CONSENT_VERSION
from routes.utils import fail, ok
from services.consent_service import ConsentError, append_consent_event
from services.family_binding_service import (
    FamilyBindingError,
    generate_bind_code,
    hash_bind_code,
    redact_bind_code,
    enforce_redemption_rate_limits,
    redeem_pending_link,
)
from services.participant_safeguard_service import (
    ParticipantSafeguardError,
    attach_guardian_from_family_link,
    public_status,
    safeguards_enforced,
)
from services.schema_migration_service import apply_pending_schema_migrations

bp = Blueprint("family", __name__, url_prefix="/api/family")
MAX_BIND_ATTEMPTS = 5
BIND_CODE_EXPIRES_HOURS = 24


def _new_bind_code() -> str:
    return generate_bind_code()


def _expires_at(timestamp: str) -> str:
    return (datetime.fromisoformat(timestamp) + timedelta(hours=BIND_CODE_EXPIRES_HOURS)).isoformat()


def _public_link(row: dict) -> dict:
    return {
        "id": row["id"],
        "parent_user_id": row["parent_user_id"],
        "student_user_id": row.get("student_user_id"),
        "relation_label": row.get("relation_label"),
        "status": row["status"],
        "created_at": row["created_at"],
        "expires_at": row.get("expires_at"),
        "attempt_count": row.get("attempt_count", 0),
        "confirmed_at": row.get("confirmed_at"),
        "revoked_at": row.get("revoked_at"),
        "summary_boundary": "家长默认只查看授权摘要，不查看学生自由文本原文。",
    }


@bp.post("/create-bind-code")
def create_bind_code():
    try:
        actor = require_role("parent", allow_legacy_admin=False)
    except AuthError as exc:
        return auth_error_response(exc)

    payload = request.get_json(silent=True) or {}
    timestamp = now_iso()
    expires_at = _expires_at(timestamp)
    link_id = new_id("family")
    bind_code = _new_bind_code()
    bind_code_hash = hash_bind_code(bind_code)
    with get_connection() as conn:
        apply_pending_schema_migrations(conn)
        revoked_pending = conn.execute(
            """
            UPDATE family_links
            SET status = 'revoked', revoked_at = ?, updated_at = ?,
                locked_until = NULL, lock_reason = 'regenerated', version = version + 1
            WHERE parent_user_id = ? AND status IN ('pending', 'locked')
            """,
            (timestamp, timestamp, actor["id"]),
        ).rowcount
        while conn.execute(
            "SELECT id FROM family_links WHERE bind_code_hash = ?",
            (bind_code_hash,),
        ).fetchone():
            bind_code = _new_bind_code()
            bind_code_hash = hash_bind_code(bind_code)
        conn.execute(
            """
            INSERT INTO family_links (
                id, parent_user_id, student_user_id, bind_code, bind_code_hash,
                bind_code_tail, relation_label,
                status, expires_at, attempt_count, last_attempt_at,
                version, locked_until, lock_reason,
                created_at, updated_at, confirmed_at, revoked_at
            )
            VALUES (?, ?, NULL, ?, ?, ?, ?, 'pending', ?, 0, NULL, 1, NULL, NULL, ?, ?, NULL, NULL)
            """,
            (
                link_id,
                actor["id"],
                redact_bind_code(bind_code),
                bind_code_hash,
                bind_code[-4:],
                str(payload.get("relation_label") or "家长").strip()[:50],
                expires_at,
                timestamp,
                timestamp,
            ),
        )
        write_audit_log(
            conn,
            action="family_create_bind_code",
            actor_id=actor["id"],
            target_type="family_link",
            target_id=link_id,
            metadata={
                "route": "/api/family/create-bind-code",
                "revoked_prior_pending_count": int(revoked_pending or 0),
            },
        )
        conn.commit()
    return ok(
        {
            "id": link_id,
            "bind_code": bind_code,
            "status": "pending",
            "expires_at": expires_at,
            "expires_policy": "绑定码 24 小时内有效，连续尝试过多会暂时锁定。",
            "max_attempts": MAX_BIND_ATTEMPTS,
        }
    )


@bp.post("/bind-student")
def bind_student():
    try:
        actor = require_role("student", allow_legacy_admin=False)
    except AuthError as exc:
        return auth_error_response(exc)

    payload = request.get_json(silent=True) or {}
    bind_code = str(payload.get("bind_code") or "").strip()
    timestamp = now_iso()
    with get_connection() as conn:
        apply_pending_schema_migrations(conn)
        try:
            enforce_redemption_rate_limits(
                conn,
                actor_id=str(actor["id"]),
                device_id=str(request.headers.get("X-Device-Id") or ""),
                ip_address=str(request.remote_addr or ""),
                bind_code=bind_code,
                timestamp=timestamp,
            )
        except FamilyBindingError as exc:
            if exc.persist:
                conn.commit()
            return fail(exc.code, exc.message, status=exc.status)
        # Plan A: establish the age boundary before binding.  Under-14 users
        # are still allowed to bind because this link is the prerequisite for
        # Plan B guardian consent.
        if safeguards_enforced():
            try:
                age_status = public_status(conn, str(actor["id"]))
            except ParticipantSafeguardError as exc:
                return fail(exc.code, exc.message, status=exc.status, details=exc.details or None)
            if age_status.get("age_verification_required"):
                return fail(
                    "age_verification_required",
                    "绑定家长前需要先完成年龄确认。",
                    status=403,
                    details=age_status,
                )

        try:
            row = redeem_pending_link(
                conn,
                bind_code=bind_code,
                student_user_id=str(actor["id"]),
                timestamp=timestamp,
            )
        except FamilyBindingError as exc:
            if exc.persist:
                conn.commit()
            return fail(exc.code, exc.message, status=exc.status)
        try:
            append_consent_event(
                conn,
                actor_id=str(actor["id"]),
                subject_id=str(actor["id"]),
                consent_type="parent_view_student_summary",
                consent_version=DEFAULT_CONSENT_VERSION,
                agreed=True,
                purpose="parent_view_student_summary",
                source="family_binding",
                event_type="self_agreed",
            )
        except ConsentError as exc:
            conn.rollback()
            return fail(exc.code, str(exc), status=exc.status)
        # Plan B: for an under-14 participant, binding establishes the guardian
        # relationship but does NOT imply sensitive-data consent.
        try:
            safeguard_status = attach_guardian_from_family_link(
                conn,
                str(actor["id"]),
                str(row["parent_user_id"]),
            )
        except ParticipantSafeguardError as exc:
            conn.rollback()
            return fail(exc.code, exc.message, status=exc.status, details=exc.details or None)
        write_audit_log(
            conn,
            action="family_bind_student",
            actor_id=actor["id"],
            target_type="family_link",
            target_id=row["id"],
            metadata={
                "route": "/api/family/bind-student",
                "parent_user_id": row["parent_user_id"],
                "minor_safeguard_status": safeguard_status.get("status"),
            },
        )
        conn.commit()
        updated = conn.execute("SELECT * FROM family_links WHERE id = ?", (row["id"],)).fetchone()
    response = _public_link(row_to_dict(updated))
    response["minor_safeguards"] = safeguard_status
    return ok(response)


@bp.get("/members")
def members():
    try:
        actor = require_login(allow_legacy_admin=False)
    except AuthError as exc:
        return auth_error_response(exc)

    with get_connection() as conn:
        apply_pending_schema_migrations(conn)
        if actor["role"] == "parent":
            rows = conn.execute(
                """
                SELECT * FROM family_links
                WHERE parent_user_id = ? AND status IN ('pending', 'locked', 'consumed')
                ORDER BY created_at DESC
                """,
                (actor["id"],),
            ).fetchall()
        elif actor["role"] == "student":
            rows = conn.execute(
                """
                SELECT * FROM family_links
                WHERE student_user_id = ? AND status = 'consumed'
                ORDER BY created_at DESC
                """,
                (actor["id"],),
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT * FROM family_links
                ORDER BY created_at DESC
                LIMIT 100
                """
            ).fetchall()
    return ok({"items": [_public_link(item) for item in rows_to_dicts(rows)]})


@bp.delete("/unbind")
def unbind():
    try:
        actor = require_login(allow_legacy_admin=False)
    except AuthError as exc:
        return auth_error_response(exc)

    payload = request.get_json(silent=True) or {}
    link_id = str(payload.get("link_id") or "").strip()
    timestamp = now_iso()
    with get_connection() as conn:
        apply_pending_schema_migrations(conn)
        row = conn.execute("SELECT * FROM family_links WHERE id = ?", (link_id,)).fetchone()
        if row is None:
            return fail("not_found", "没有找到对应绑定关系", status=404)
        if actor["role"] not in {"admin"} and actor["id"] not in {row["parent_user_id"], row["student_user_id"]}:
            return fail("forbidden", "只能撤销自己的绑定关系", status=403)
        conn.execute(
            "UPDATE family_links SET status = 'revoked', revoked_at = ?, updated_at = ? WHERE id = ?",
            (timestamp, timestamp, link_id),
        )
        if row["student_user_id"]:
            safeguard = conn.execute(
                "SELECT * FROM participant_minor_safeguards WHERE user_id = ?",
                (row["student_user_id"],),
            ).fetchone()
            if safeguard is not None and safeguard["guardian_user_id"] == row["parent_user_id"]:
                conn.execute(
                    """
                    UPDATE participant_minor_safeguards
                    SET guardian_user_id = NULL,
                        guardian_consent_status = 'withdrawn',
                        status = 'guardian_link_required',
                        version = version + 1,
                        updated_at = ?
                    WHERE user_id = ?
                    """,
                    (timestamp, row["student_user_id"]),
                )
        write_audit_log(
            conn,
            action="family_unbind",
            actor_id=actor["id"],
            target_type="family_link",
            target_id=link_id,
            metadata={"route": "/api/family/unbind", "minor_guardian_permission_revoked": True},
        )
        conn.commit()
        updated = conn.execute("SELECT * FROM family_links WHERE id = ?", (link_id,)).fetchone()
    return ok(_public_link(row_to_dict(updated)))
