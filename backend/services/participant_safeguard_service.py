"""Age confirmation and under-14 guardian safeguards for participant data.

This module intentionally reuses ``consent_records``, ``family_links`` and
``audit_logs`` instead of collecting a full date of birth or introducing a new
identity table. The minimum age fact stored is only the confirmed age band.
"""

from __future__ import annotations

from database import get_connection, new_id, now_iso, row_to_dict, write_audit_log

POLICY_VERSION = "2026.08-participant-minor-v1"
AGE_14_PLUS = "participant_age_14_or_older"
AGE_UNDER_14 = "participant_age_under_14"
GUARDIAN_PROCESSING_CONSENT = "guardian_sensitive_processing"
MINOR_ASSENT = "minor_sensitive_processing_assent"
AGE_TYPES = {AGE_14_PLUS, AGE_UNDER_14}


class ParticipantSafeguardError(ValueError):
    def __init__(self, code: str, message: str, status: int = 428, details: dict | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.status = status
        self.details = details or {}


def _latest(conn, user_id: str, consent_type: str) -> dict | None:
    row = conn.execute(
        """
        SELECT * FROM consent_records
        WHERE user_id = ? AND consent_type = ?
        ORDER BY created_at DESC, id DESC
        LIMIT 1
        """,
        (user_id, consent_type),
    ).fetchone()
    return row_to_dict(row)


def _latest_age_confirmation(conn, user_id: str) -> dict | None:
    row = conn.execute(
        """
        SELECT * FROM consent_records
        WHERE user_id = ? AND consent_type IN (?, ?)
        ORDER BY created_at DESC, id DESC
        LIMIT 1
        """,
        (user_id, AGE_14_PLUS, AGE_UNDER_14),
    ).fetchone()
    return row_to_dict(row)


def _insert_consent(conn, user_id: str, consent_type: str, agreed: bool) -> dict:
    timestamp = now_iso()
    record_id = new_id("consent")
    conn.execute(
        """
        INSERT INTO consent_records (
            id, user_id, consent_type, consent_version, agreed,
            agreed_at, revoked_at, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            record_id,
            user_id,
            consent_type,
            POLICY_VERSION,
            1 if agreed else 0,
            timestamp,
            None if agreed else timestamp,
            timestamp,
        ),
    )
    return row_to_dict(conn.execute("SELECT * FROM consent_records WHERE id = ?", (record_id,)).fetchone())


def _active_guardian_link(conn, child_user_id: str, guardian_user_id: str | None = None) -> dict | None:
    params: list[str] = [child_user_id]
    guardian_clause = ""
    if guardian_user_id:
        guardian_clause = " AND parent_user_id = ?"
        params.append(guardian_user_id)
    row = conn.execute(
        f"""
        SELECT * FROM family_links
        WHERE student_user_id = ? AND status = 'active'{guardian_clause}
        ORDER BY confirmed_at DESC, created_at DESC
        LIMIT 1
        """,
        params,
    ).fetchone()
    return row_to_dict(row)


def record_age_confirmation(actor: dict, age_band: str) -> dict:
    if str(actor.get("role") or "") != "student":
        raise ParticipantSafeguardError("student_only", "年龄确认只适用于学生账号。", 403)
    normalized = str(age_band or "").strip()
    consent_type = {
        "14_or_older": AGE_14_PLUS,
        "under_14": AGE_UNDER_14,
    }.get(normalized)
    if not consent_type:
        raise ParticipantSafeguardError(
            "invalid_age_band",
            "age_band 仅支持 14_or_older 或 under_14。",
            422,
        )
    user_id = str(actor["id"])
    with get_connection() as conn:
        record = _insert_consent(conn, user_id, consent_type, True)
        write_audit_log(
            conn,
            "participant_age_band_confirmed",
            user_id,
            "user",
            user_id,
            {
                "age_band": normalized,
                "policy_version": POLICY_VERSION,
                "exact_birth_date_collected": False,
            },
        )
        conn.commit()
    return {"record": record, "safeguard": get_participant_safeguard_status(user_id)}


def record_guardian_processing_consent(actor: dict, child_user_id: str, agreed: bool) -> dict:
    if str(actor.get("role") or "") != "parent":
        raise ParticipantSafeguardError("guardian_only", "只有已绑定家长/监护人账号可以作出该决定。", 403)
    child_user_id = str(child_user_id or "").strip()
    if not child_user_id:
        raise ParticipantSafeguardError("child_required", "缺少学生账号。", 422)
    guardian_id = str(actor["id"])
    with get_connection() as conn:
        age = _latest_age_confirmation(conn, child_user_id)
        if not age or age["consent_type"] != AGE_UNDER_14:
            raise ParticipantSafeguardError("under14_required", "该学生当前不是已确认的未满14岁流程。", 409)
        link = _active_guardian_link(conn, child_user_id, guardian_id)
        if not link:
            raise ParticipantSafeguardError("guardian_link_required", "请先完成有效的家长—学生绑定。", 409)
        record = _insert_consent(conn, child_user_id, GUARDIAN_PROCESSING_CONSENT, bool(agreed))
        write_audit_log(
            conn,
            "guardian_sensitive_processing_consent_updated",
            guardian_id,
            "user",
            child_user_id,
            {
                "agreed": bool(agreed),
                "family_link_id": link["id"],
                "policy_version": POLICY_VERSION,
            },
        )
        conn.commit()
    return {"record": record, "safeguard": get_participant_safeguard_status(child_user_id)}


def record_minor_assent(actor: dict, agreed: bool) -> dict:
    if str(actor.get("role") or "") != "student":
        raise ParticipantSafeguardError("student_only", "学生 assent 只能由学生本人作出。", 403)
    user_id = str(actor["id"])
    with get_connection() as conn:
        age = _latest_age_confirmation(conn, user_id)
        if not age or age["consent_type"] != AGE_UNDER_14:
            raise ParticipantSafeguardError("under14_required", "当前账号不是已确认的未满14岁流程。", 409)
        record = _insert_consent(conn, user_id, MINOR_ASSENT, bool(agreed))
        write_audit_log(
            conn,
            "minor_sensitive_processing_assent_updated",
            user_id,
            "user",
            user_id,
            {"agreed": bool(agreed), "policy_version": POLICY_VERSION},
        )
        conn.commit()
    return {"record": record, "safeguard": get_participant_safeguard_status(user_id)}


def get_participant_safeguard_status(user_id: str) -> dict:
    user_id = str(user_id)
    with get_connection() as conn:
        user = conn.execute("SELECT id, role, status FROM users WHERE id = ?", (user_id,)).fetchone()
        if user is None:
            raise ParticipantSafeguardError("user_not_found", "账号不存在。", 404)
        user = row_to_dict(user)
        if user.get("role") != "student":
            return {
                "policy_version": POLICY_VERSION,
                "role": user.get("role"),
                "age_confirmation_required": False,
                "under_14": False,
                "processing_allowed": True,
                "status": "not_applicable",
            }

        age = _latest_age_confirmation(conn, user_id)
        if not age:
            return {
                "policy_version": POLICY_VERSION,
                "role": "student",
                "age_confirmation_required": True,
                "under_14": None,
                "processing_allowed": False,
                "status": "age_confirmation_required",
                "exact_birth_date_collected": False,
            }
        if age["consent_type"] == AGE_14_PLUS:
            return {
                "policy_version": POLICY_VERSION,
                "role": "student",
                "age_confirmation_required": False,
                "under_14": False,
                "processing_allowed": True,
                "status": "age_14_or_older_confirmed",
                "age_confirmed_at": age["created_at"],
                "exact_birth_date_collected": False,
            }

        guardian_link = _active_guardian_link(conn, user_id)
        guardian_consent = _latest(conn, user_id, GUARDIAN_PROCESSING_CONSENT)
        minor_assent = _latest(conn, user_id, MINOR_ASSENT)
        age_time = str(age["created_at"])
        guardian_consent_active = bool(
            guardian_consent
            and int(guardian_consent.get("agreed") or 0) == 1
            and str(guardian_consent.get("created_at") or "") >= age_time
        )
        minor_assent_active = bool(
            minor_assent
            and int(minor_assent.get("agreed") or 0) == 1
            and str(minor_assent.get("created_at") or "") >= age_time
        )
        guardian_link_active = guardian_link is not None
        processing_allowed = guardian_link_active and guardian_consent_active and minor_assent_active
        if not guardian_link_active:
            status = "guardian_link_required"
        elif not guardian_consent_active:
            status = "guardian_consent_required"
        elif not minor_assent_active:
            status = "minor_assent_required"
        else:
            status = "under14_safeguards_ready"
        return {
            "policy_version": POLICY_VERSION,
            "role": "student",
            "age_confirmation_required": False,
            "under_14": True,
            "processing_allowed": processing_allowed,
            "status": status,
            "age_confirmed_at": age["created_at"],
            "guardian_link_active": guardian_link_active,
            "guardian_consent_active": guardian_consent_active,
            "minor_assent_active": minor_assent_active,
            "exact_birth_date_collected": False,
            "boundary_notice": (
                "未满14岁学生的敏感心理信息处理需要有效家长/监护人绑定、"
                "监护人同意和学生本人 assent；任一撤回后普通心理数据处理重新阻断。"
            ),
        }


def assert_participant_data_access(actor: dict) -> dict:
    if str(actor.get("role") or "") != "student":
        return {"processing_allowed": True, "status": "not_applicable"}
    status = get_participant_safeguard_status(str(actor["id"]))
    if not status["processing_allowed"]:
        raise ParticipantSafeguardError(
            "participant_safeguard_required",
            "请先完成年龄确认；未满14岁时还需完成家长/监护人同意和学生本人 assent。",
            428,
            status,
        )
    return status
