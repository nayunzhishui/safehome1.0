"""Parent-student binding code endpoints."""

import secrets
from datetime import datetime, timedelta
from flask import Blueprint, request

from database import get_connection, new_id, now_iso, row_to_dict, rows_to_dicts, write_audit_log
from routes.auth_utils import AuthError, auth_error_response, require_login, require_role
from routes.consent import DEFAULT_CONSENT_VERSION
from routes.utils import fail, ok
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
BIND_GUESS_WINDOW_MINUTES = 10
BIND_GUESS_LIMIT_PER_ACTOR = 10


def _new_bind_code() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"


def _expires_at(timestamp: str) -> str:
    return (datetime.fromisoformat(timestamp) + timedelta(hours=BIND_CODE_EXPIRES_HOURS)).isoformat()


def _is_expired(expires_at: str | None, timestamp: str) -> bool:
    if not expires_at:
        return False
    return datetime.fromisoformat(expires_at) <= datetime.fromisoformat(timestamp)


def _bind_guess_cutoff(timestamp: str) -> str:
    return (
        datetime.fromisoformat(timestamp) - timedelta(minutes=BIND_GUESS_WINDOW_MINUTES)
    ).isoformat()


def _bind_guess_failure_count(conn, actor_id: str, timestamp: str) -> int:
    row = conn.execute(
        """
        SELECT COUNT(*) AS count
        FROM audit_logs
        WHERE actor_id = ?
          AND action = 'family_bind_guess_failed'
          AND created_at >= ?
        """,
        (actor_id, _bind_guess_cutoff(timestamp)),
    ).fetchone()
    return int(row["count"] if row else 0)


def _record_bind_guess_failure(conn, actor_id: str, reason: str) -> None:
    # Never store the submitted binding code or a reversible derivative of it.
    write_audit_log(
        conn,
        action="family_bind_guess_failed",
        actor_id=actor_id,
        target_type="family_bind",
        target_id=None,
        metadata={
            "route": "/api/family/bind-student",
            "reason": reason,
            "bind_code_logged": False,
        },
    )


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
    with get_connection() as conn:
        apply_pending_schema_migrations(conn)
        # Keep only one usable pending code per parent. Regeneration revokes
        # older pending codes so leaked/stale codes cannot remain valid.
        conn.execute(
            """
            UPDATE family_links
            SET status = 'revoked', revoked_at = ?, updated_at = ?
            WHERE parent_user_id = ? AND status = 'pending'
            """,
            (timestamp, timestamp, actor["id"]),
        )
        while conn.execute("SELECT id FROM family_links WHERE bind_code = ? AND status = 'pending'", (bind_code,)).fetchone():
            bind_code = _new_bind_code()
        conn.execute(
            """
            INSERT INTO family_links (
                id, parent_user_id, student_user_id, bind_code, relation_label,
                status, expires_at, attempt_count, last_attempt_at,
                created_at, updated_at, confirmed_at, revoked_at
            )
            VALUES (?, ?, NULL, ?, ?, 'pending', ?, 0, NULL, ?, ?, NULL, NULL)
            """,
            (link_id, actor["id"], bind_code, str(payload.get("relation_label") or "家长").strip()[:50], expires_at, timestamp, timestamp),
        )
        write_audit_log(
            conn,
            action="family_create_bind_code",
            actor_id=actor["id"],
            target_type="family_link",
            target_id=link_id,
            metadata={"route": "/api/family/create-bind-code", "previous_pending_codes_revoked": True},
        )
        conn.commit()
    return ok(
        {
            "id": link_id,
            "bind_code": bind_code,
            "status": "pending",
            "expires_at": expires_at,
            "expires_policy": "绑定码 24 小时内有效；错误猜测会按学生账号窗口限流。",
            "max_attempts": MAX_BIND_ATTEMPTS,
            "guess_window_minutes": BIND_GUESS_WINDOW_MINUTES,
            "guess_limit_per_actor": BIND_GUESS_LIMIT_PER_ACTOR,
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
    if len(bind_code) != 6 or not bind_code.isdigit():
        return fail("validation_error", "绑定码必须是 6 位数字", status=400)

    timestamp = now_iso()
    with get_connection() as conn:
        apply_pending_schema_migrations(conn)
        # Plan A: establish the age boundary before binding. Under-14 users
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

        failure_count = _bind_guess_failure_count(conn, str(actor["id"]), timestamp)
        if failure_count >= BIND_GUESS_LIMIT_PER_ACTOR:
            write_audit_log(
                conn,
                action="family_bind_guess_rate_limited",
                actor_id=actor["id"],
                target_type="family_bind",
                target_id=None,
                metadata={
                    "route": "/api/family/bind-student",
                    "window_minutes": BIND_GUESS_WINDOW_MINUTES,
                    "limit": BIND_GUESS_LIMIT_PER_ACTOR,
                    "bind_code_logged": False,
                },
            )
            conn.commit()
            return fail(
                "bind_guess_rate_limited",
                "绑定码尝试过于频繁，请稍后再试。",
                status=429,
            )

        row = conn.execute(
            "SELECT * FROM family_links WHERE bind_code = ? AND status = 'pending' ORDER BY created_at DESC LIMIT 1",
            (bind_code,),
        ).fetchone()
        if row is None:
            _record_bind_guess_failure(conn, str(actor["id"]), "not_found")
            conn.commit()
            return fail("not_found", "绑定码不存在或已失效", status=404)
        if int(row["attempt_count"] or 0) >= MAX_BIND_ATTEMPTS:
            _record_bind_guess_failure(conn, str(actor["id"]), "link_attempt_limit")
            conn.commit()
            return fail("too_many_attempts", "绑定码尝试次数过多，请家长重新生成。", status=429)
        if _is_expired(row["expires_at"], timestamp):
            conn.execute(
                """
                UPDATE family_links
                SET status = 'expired', attempt_count = attempt_count + 1,
                    last_attempt_at = ?, updated_at = ?
                WHERE id = ? AND status = 'pending'
                """,
                (timestamp, timestamp, row["id"]),
            )
            _record_bind_guess_failure(conn, str(actor["id"]), "expired")
            conn.commit()
            return fail("bind_code_expired", "绑定码已过期，请家长重新生成。", status=410)

        # Atomic claim: a pending code can be consumed by only one student,
        # even when two workers race after reading the same pending row.
        cursor = conn.execute(
            """
            UPDATE family_links
            SET student_user_id = ?, status = 'active',
                attempt_count = attempt_count + 1, last_attempt_at = ?,
                confirmed_at = ?, updated_at = ?
            WHERE id = ? AND status = 'pending'
            """,
            (actor["id"], timestamp, timestamp, timestamp, row["id"]),
        )
        if int(cursor.rowcount or 0) != 1:
            conn.rollback()
            return fail(
                "bind_code_already_consumed",
                "绑定码已被使用或刚刚失效，请家长重新生成。",
                status=409,
            )
        conn.execute(
            """
            INSERT INTO consent_records (
                id, user_id, consent_type, consent_version, agreed,
                agreed_at, revoked_at, created_at
            )
            VALUES (?, ?, 'parent_view_student_summary', ?, 1, ?, NULL, ?)
            """,
            (new_id("consent"), actor["id"], DEFAULT_CONSENT_VERSION, timestamp, timestamp),
        )
        # Plan B: for an under-14 participant, binding establishes the guardian
        # relationship but does NOT imply sensitive-data consent.
        try:
            safeguard_status = attach_guardian_from_family_link(
                conn,
                str(actor["id"]),
                str(row["parent_user_id"]),
            )
        except ParticipantSafeguardError as exc:
            # Do not commit a half-bound family link when safeguard attachment
            # fails after the atomic claim.
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
                "atomic_claim": True,
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
                WHERE parent_user_id = ? AND status IN ('pending', 'active')
                ORDER BY created_at DESC
                """,
                (actor["id"],),
            ).fetchall()
        elif actor["role"] == "student":
            rows = conn.execute(
                """
                SELECT * FROM family_links
                WHERE student_user_id = ? AND status = 'active'
                ORDER BY created_at DESC
                """,
                (actor["id"],),
            ).fetchall()
        elif actor["role"] == "admin":
            rows = conn.execute(
                """
                SELECT * FROM family_links
                ORDER BY created_at DESC
                LIMIT 100
                """
            ).fetchall()
        else:
            return fail(
                "forbidden",
                "当前后台角色没有全局家庭关系读取权限。",
                status=403,
            )
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
