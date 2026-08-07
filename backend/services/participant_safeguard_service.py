"""General participant age/guardian safeguards for the SafeHome pilot.

This module deliberately sits outside the therapeutic-assessment child workflow.
It protects the ordinary student registration/assessment/research path while
reusing the existing family-link and consent/audit infrastructure.

No diagnostic inference is performed here.  The only age distinction used by
this service is the legal/product boundary required by the project: under 14
versus 14 or over.
"""

from __future__ import annotations

from dataclasses import dataclass

from config import Config
from database import get_connection, new_id, now_iso, row_to_dict, write_audit_log
from services.schema_migration_service import apply_pending_schema_migrations

AGE_BANDS = {"under_14", "14_or_over"}
PROTECTED_CAPABILITIES = {"assessment", "research", "sensitive_text", "profile"}
POLICY_VERSION = "2026.08-participant-minor-safeguards-v1"


class ParticipantSafeguardError(ValueError):
    def __init__(self, code: str, message: str, status: int = 403, details: dict | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status = status
        self.details = details or {}


@dataclass(frozen=True)
class Eligibility:
    allowed: bool
    code: str
    status: dict


def safeguards_enforced() -> bool:
    configured = getattr(Config, "MINOR_SAFEGUARDS_ENFORCED", None)
    if configured is not None:
        return bool(configured)
    return str(getattr(Config, "APP_ENV", "development") or "").strip().lower() in {
        "pilot",
        "production",
    }


def _row(conn, user_id: str) -> dict | None:
    apply_pending_schema_migrations(conn)
    row = conn.execute(
        "SELECT * FROM participant_minor_safeguards WHERE user_id = ?",
        (user_id,),
    ).fetchone()
    return row_to_dict(row)


def _user(conn, user_id: str) -> dict:
    apply_pending_schema_migrations(conn)
    row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    if row is None:
        raise ParticipantSafeguardError("user_not_found", "没有找到对应参与者账号。", 404)
    return row_to_dict(row)


def _derive_status(age_band: str, guardian_id: str | None, guardian_consent: str, child_assent: str) -> str:
    if age_band == "14_or_over":
        return "age_verified"
    if not guardian_id:
        return "guardian_link_required"
    if guardian_consent == "withdrawn" or child_assent in {"refused", "withdrawn"}:
        return "blocked_withdrawn_or_refused"
    if guardian_consent != "active":
        return "guardian_consent_required"
    if child_assent != "assented":
        return "child_assent_required"
    return "active"


def public_status(conn, user_id: str) -> dict:
    user = _user(conn, user_id)
    age_band = str(user.get("age_band") or "")
    item = _row(conn, user_id)
    if user.get("role") != "student":
        return {
            "user_id": user_id,
            "role": user.get("role"),
            "age_verification_required": False,
            "minor_safeguards_required": False,
            "status": "not_applicable",
            "policy_version": POLICY_VERSION,
        }
    if not age_band:
        return {
            "user_id": user_id,
            "role": "student",
            "age_band": None,
            "age_verification_required": True,
            "minor_safeguards_required": None,
            "status": "age_verification_required",
            "policy_version": POLICY_VERSION,
        }
    if age_band == "14_or_over":
        return {
            "user_id": user_id,
            "role": "student",
            "age_band": age_band,
            "age_verification_required": False,
            "minor_safeguards_required": False,
            "status": "age_verified",
            "policy_version": POLICY_VERSION,
        }
    guardian_consent = str((item or {}).get("guardian_consent_status") or "pending")
    child_assent = str((item or {}).get("child_assent_status") or "pending")
    guardian_id = (item or {}).get("guardian_user_id")
    status = _derive_status(age_band, guardian_id, guardian_consent, child_assent)
    return {
        "user_id": user_id,
        "role": "student",
        "age_band": age_band,
        "age_verification_required": False,
        "minor_safeguards_required": True,
        "guardian_linked": bool(guardian_id),
        "guardian_consent_status": guardian_consent,
        "child_assent_status": child_assent,
        "status": status,
        "policy_version": str((item or {}).get("policy_version") or POLICY_VERSION),
        "temporary_showcase_counts_as_permission": False,
    }


def confirm_age_for_user(
    conn,
    user_id: str,
    age_band: str,
    *,
    method: str = "self_declaration",
    actor_id: str | None = None,
    allow_under14_upgrade: bool = False,
) -> dict:
    apply_pending_schema_migrations(conn)
    age_band = str(age_band or "").strip()
    if age_band not in AGE_BANDS:
        raise ParticipantSafeguardError(
            "invalid_age_band",
            "年龄确认只能选择“未满14周岁”或“已满14周岁”。",
            400,
        )
    user = _user(conn, user_id)
    if user.get("role") != "student":
        raise ParticipantSafeguardError("age_not_applicable", "年龄门禁仅适用于学生参与者账号。", 400)
    previous = str(user.get("age_band") or "")
    if previous == "under_14" and age_band == "14_or_over" and not allow_under14_upgrade:
        raise ParticipantSafeguardError(
            "age_change_requires_review",
            "已记录为未满14周岁的账号不能自行改为已满14周岁，请由督导或管理员核验。",
            409,
        )

    timestamp = now_iso()
    conn.execute(
        """
        UPDATE users
        SET age_band = ?, age_verified_at = ?, age_verification_method = ?, updated_at = ?
        WHERE id = ?
        """,
        (age_band, timestamp, str(method or "self_declaration")[:80], timestamp, user_id),
    )

    if age_band == "under_14":
        existing = _row(conn, user_id)
        if existing is None:
            conn.execute(
                """
                INSERT INTO participant_minor_safeguards (
                    id, user_id, age_band, guardian_user_id,
                    guardian_consent_status, child_assent_status, status,
                    policy_version, version, created_at, updated_at
                ) VALUES (?, ?, 'under_14', NULL, 'pending', 'pending',
                          'guardian_link_required', ?, 1, ?, ?)
                """,
                (new_id("minor_guard"), user_id, POLICY_VERSION, timestamp, timestamp),
            )
        else:
            status = _derive_status(
                "under_14",
                existing.get("guardian_user_id"),
                str(existing.get("guardian_consent_status") or "pending"),
                str(existing.get("child_assent_status") or "pending"),
            )
            conn.execute(
                """
                UPDATE participant_minor_safeguards
                SET age_band = 'under_14', status = ?, policy_version = ?,
                    version = version + 1, updated_at = ?
                WHERE user_id = ?
                """,
                (status, POLICY_VERSION, timestamp, user_id),
            )
    else:
        existing = _row(conn, user_id)
        if existing is not None:
            conn.execute(
                """
                UPDATE participant_minor_safeguards
                SET age_band = '14_or_over', status = 'age_verified',
                    policy_version = ?, version = version + 1, updated_at = ?
                WHERE user_id = ?
                """,
                (POLICY_VERSION, timestamp, user_id),
            )

    write_audit_log(
        conn,
        action="participant_age_confirmed",
        actor_id=str(actor_id or user_id),
        target_type="user",
        target_id=user_id,
        metadata={
            "age_band": age_band,
            "method": method,
            "previous_age_band": previous or None,
            "policy_version": POLICY_VERSION,
        },
    )
    return public_status(conn, user_id)


def attach_guardian_from_family_link(conn, child_user_id: str, guardian_user_id: str) -> dict:
    apply_pending_schema_migrations(conn)
    user = _user(conn, child_user_id)
    if user.get("role") != "student" or str(user.get("age_band") or "") != "under_14":
        return public_status(conn, child_user_id)
    parent = _user(conn, guardian_user_id)
    if parent.get("role") != "parent" or parent.get("status") != "active":
        raise ParticipantSafeguardError("invalid_guardian", "监护人账号无效。", 400)
    timestamp = now_iso()
    existing = _row(conn, child_user_id)
    if existing is None:
        conn.execute(
            """
            INSERT INTO participant_minor_safeguards (
                id, user_id, age_band, guardian_user_id,
                guardian_consent_status, child_assent_status, status,
                policy_version, version, created_at, updated_at
            ) VALUES (?, ?, 'under_14', ?, 'pending', 'pending',
                      'guardian_consent_required', ?, 1, ?, ?)
            """,
            (new_id("minor_guard"), child_user_id, guardian_user_id, POLICY_VERSION, timestamp, timestamp),
        )
    else:
        guardian_consent = str(existing.get("guardian_consent_status") or "pending")
        child_assent = str(existing.get("child_assent_status") or "pending")
        status = _derive_status("under_14", guardian_user_id, guardian_consent, child_assent)
        conn.execute(
            """
            UPDATE participant_minor_safeguards
            SET guardian_user_id = ?, status = ?, policy_version = ?,
                version = version + 1, updated_at = ?
            WHERE user_id = ?
            """,
            (guardian_user_id, status, POLICY_VERSION, timestamp, child_user_id),
        )
    write_audit_log(
        conn,
        action="minor_guardian_linked",
        actor_id=guardian_user_id,
        target_type="user",
        target_id=child_user_id,
        metadata={"policy_version": POLICY_VERSION},
    )
    return public_status(conn, child_user_id)


def _assert_active_family_link(conn, parent_user_id: str, child_user_id: str) -> None:
    row = conn.execute(
        """
        SELECT id FROM family_links
        WHERE parent_user_id = ? AND student_user_id = ? AND status = 'active'
        ORDER BY confirmed_at DESC LIMIT 1
        """,
        (parent_user_id, child_user_id),
    ).fetchone()
    if row is None:
        raise ParticipantSafeguardError(
            "guardian_link_required",
            "需要先完成家长与学生账号绑定，才能记录监护人同意。",
            409,
        )


def record_guardian_consent(conn, parent_user_id: str, child_user_id: str, agreed: bool) -> dict:
    apply_pending_schema_migrations(conn)
    _assert_active_family_link(conn, parent_user_id, child_user_id)
    user = _user(conn, child_user_id)
    if str(user.get("age_band") or "") != "under_14":
        raise ParticipantSafeguardError("guardian_consent_not_required", "该账号当前不需要未满14周岁监护人门禁。", 400)
    item = _row(conn, child_user_id)
    if item is None:
        attach_guardian_from_family_link(conn, child_user_id, parent_user_id)
        item = _row(conn, child_user_id) or {}
    elif item.get("guardian_user_id") not in {None, "", parent_user_id}:
        raise ParticipantSafeguardError("guardian_conflict", "当前账号已绑定另一监护人，需要人工复核。", 409)

    timestamp = now_iso()
    consent_status = "active" if agreed else "withdrawn"
    child_assent = str(item.get("child_assent_status") or "pending")
    status = _derive_status("under_14", parent_user_id, consent_status, child_assent)
    consent_id = new_id("consent")
    conn.execute(
        """
        INSERT INTO consent_records (
            id, user_id, consent_type, consent_version, agreed,
            agreed_at, revoked_at, created_at
        ) VALUES (?, ?, 'guardian_sensitive_processing_under14', ?, ?, ?, ?, ?)
        """,
        (
            consent_id,
            child_user_id,
            POLICY_VERSION,
            1 if agreed else 0,
            timestamp,
            None if agreed else timestamp,
            timestamp,
        ),
    )
    conn.execute(
        """
        UPDATE participant_minor_safeguards
        SET guardian_user_id = ?, guardian_consent_status = ?,
            guardian_consent_record_id = ?, status = ?, policy_version = ?,
            version = version + 1, updated_at = ?
        WHERE user_id = ?
        """,
        (parent_user_id, consent_status, consent_id, status, POLICY_VERSION, timestamp, child_user_id),
    )
    write_audit_log(
        conn,
        action="minor_guardian_consent_updated",
        actor_id=parent_user_id,
        target_type="user",
        target_id=child_user_id,
        metadata={"agreed": bool(agreed), "status": status, "policy_version": POLICY_VERSION},
    )
    return public_status(conn, child_user_id)


def record_child_assent(conn, child_user_id: str, assented: bool, *, withdraw: bool = False) -> dict:
    apply_pending_schema_migrations(conn)
    user = _user(conn, child_user_id)
    if user.get("role") != "student" or str(user.get("age_band") or "") != "under_14":
        raise ParticipantSafeguardError("child_assent_not_required", "该账号当前不需要未满14周岁儿童确认。", 400)
    item = _row(conn, child_user_id)
    if item is None:
        raise ParticipantSafeguardError("guardian_link_required", "需要先建立未成年人保护记录。", 409)
    child_status = "withdrawn" if withdraw else ("assented" if assented else "refused")
    guardian_consent = str(item.get("guardian_consent_status") or "pending")
    status = _derive_status("under_14", item.get("guardian_user_id"), guardian_consent, child_status)
    timestamp = now_iso()
    conn.execute(
        """
        UPDATE participant_minor_safeguards
        SET child_assent_status = ?, status = ?, policy_version = ?,
            version = version + 1, updated_at = ?
        WHERE user_id = ?
        """,
        (child_status, status, POLICY_VERSION, timestamp, child_user_id),
    )
    write_audit_log(
        conn,
        action="minor_child_assent_updated",
        actor_id=child_user_id,
        target_type="user",
        target_id=child_user_id,
        metadata={"child_assent_status": child_status, "status": status, "policy_version": POLICY_VERSION},
    )
    return public_status(conn, child_user_id)


def eligibility_for(conn, user_id: str, capability: str) -> Eligibility:
    apply_pending_schema_migrations(conn)
    status = public_status(conn, user_id)
    if status.get("role") != "student" or capability not in PROTECTED_CAPABILITIES:
        return Eligibility(True, "not_applicable", status)
    if not safeguards_enforced():
        return Eligibility(True, "safeguards_not_enforced", status)
    if status.get("age_verification_required"):
        return Eligibility(False, "age_verification_required", status)
    if status.get("age_band") == "14_or_over":
        return Eligibility(True, "age_verified", status)
    if status.get("status") != "active":
        return Eligibility(False, str(status.get("status") or "minor_safeguard_required"), status)
    return Eligibility(True, "minor_safeguards_active", status)


def assert_participant_capability(user_id: str, capability: str) -> dict:
    with get_connection() as conn:
        result = eligibility_for(conn, user_id, capability)
    if result.allowed:
        return result.status
    messages = {
        "age_verification_required": "继续前需要先完成年龄确认。",
        "guardian_link_required": "未满14周岁参与者需要先完成监护人账号绑定。",
        "guardian_consent_required": "未满14周岁参与者需要监护人同意后才能继续。",
        "child_assent_required": "还需要参与者本人确认愿意继续。",
        "blocked_withdrawn_or_refused": "参与者或监护人已拒绝/撤回，本功能已停止。",
    }
    raise ParticipantSafeguardError(
        result.code,
        messages.get(result.code, "当前未成年人保护条件尚未满足。"),
        403,
        details=result.status,
    )
