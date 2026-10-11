"""Fail-closed researcher access to participant-derived sensitive data.

This service is the authoritative bridge between researcher capabilities,
object-scope assignments and explicit participant research authorization. It
returns minimized summaries rather than raw participant payloads.
"""

from __future__ import annotations

import hashlib

from database import get_connection, row_to_dict, rows_to_dicts, write_audit_log
from services.participant_safeguard_service import (
    ParticipantSafeguardError,
    public_status,
    safeguards_enforced,
)
from services.research_access_service import (
    ACTIVE_ENROLLMENT_STATUSES,
    ResearchAccessError,
    assert_capability,
    require_object_scope,
)


EXPLICIT_RESEARCH_CONSENT_TYPE = "research_authorization"


def _anonymous_subject_id(user_id: str) -> str:
    return "anon_" + hashlib.sha256(str(user_id).encode("utf-8")).hexdigest()[:12]


def _latest_explicit_research_consent(conn, user_id: str) -> dict | None:
    row = conn.execute(
        """
        SELECT id, user_id, consent_type, consent_version, agreed,
               agreed_at, revoked_at, created_at
        FROM consent_records
        WHERE user_id = ? AND consent_type = ?
        ORDER BY created_at DESC, id DESC
        LIMIT 1
        """,
        (user_id, EXPLICIT_RESEARCH_CONSENT_TYPE),
    ).fetchone()
    return row_to_dict(row)


def require_explicit_research_authorization(conn, user_id: str) -> dict:
    """Require a positive, current opt-in. Missing consent always denies."""

    consent = _latest_explicit_research_consent(conn, user_id)
    if (
        consent is None
        or int(consent.get("agreed") or 0) != 1
        or consent.get("revoked_at")
    ):
        raise ResearchAccessError(
            "research_authorization_required",
            "该参与者没有当前有效的明确研究授权。",
            403,
            {"required_consent_type": EXPLICIT_RESEARCH_CONSENT_TYPE},
        )

    if safeguards_enforced():
        try:
            safeguard = public_status(conn, user_id)
        except ParticipantSafeguardError as exc:
            raise ResearchAccessError(
                exc.code,
                exc.message,
                exc.status,
                exc.details or None,
            ) from exc
        if safeguard.get("age_verification_required"):
            raise ResearchAccessError(
                "age_verification_required",
                "参与者尚未完成年龄确认，不能进入研究读取范围。",
                403,
            )
        if safeguard.get("minor_safeguards_required") and safeguard.get("status") != "active":
            raise ResearchAccessError(
                "minor_safeguards_required",
                "未成年人监护人授权或儿童确认未生效，不能进入研究读取范围。",
                403,
            )

    return consent


def _authorized_enrollment(conn, actor: dict, enrollment_id: str, capability_id: str) -> dict:
    row = conn.execute(
        "SELECT * FROM relationship_pilot_enrollments WHERE id = ?",
        (enrollment_id,),
    ).fetchone()
    if row is None:
        raise ResearchAccessError("not_found", "没有找到可访问的报名记录。", 404)
    enrollment = row_to_dict(row)
    if enrollment.get("status") not in ACTIVE_ENROLLMENT_STATUSES:
        raise ResearchAccessError("enrollment_inactive", "该参与者当前不在有效研究范围内。", 409)
    require_object_scope(conn, actor, enrollment, capability_id)
    require_explicit_research_authorization(conn, str(enrollment["user_id"]))
    return enrollment


def list_authorized_participants(actor: dict, limit: int) -> dict:
    """List only assigned, explicitly opted-in participants using minimal fields."""

    capability_id = "research.participant.read"
    assert_capability(actor, capability_id)
    limit = max(1, min(int(limit), 200))

    with get_connection() as conn:
        if actor.get("role") == "admin":
            rows = conn.execute(
                """
                SELECT e.id, e.user_id, e.status, e.review_status,
                       e.worksheet_id, e.profile_model_id, e.created_at
                FROM relationship_pilot_enrollments e
                WHERE e.status IN ('enrolled', 'active')
                ORDER BY e.created_at DESC, e.id DESC
                LIMIT ?
                """,
                (limit * 3,),
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT e.id, e.user_id, e.status, e.review_status,
                       e.worksheet_id, e.profile_model_id, e.created_at
                FROM relationship_pilot_enrollments e
                JOIN research_scope_assignments a
                  ON a.enrollment_id = e.id
                 AND a.actor_id = ?
                 AND a.status = 'active'
                WHERE e.status IN ('enrolled', 'active')
                ORDER BY e.created_at DESC, e.id DESC
                LIMIT ?
                """,
                (str(actor["id"]), limit * 3),
            ).fetchall()

        items: list[dict] = []
        for raw in rows:
            enrollment = row_to_dict(raw)
            user_id = str(enrollment["user_id"])
            try:
                require_explicit_research_authorization(conn, user_id)
            except ResearchAccessError:
                continue
            items.append(
                {
                    "enrollment_id": enrollment["id"],
                    "anonymous_id": _anonymous_subject_id(user_id),
                    "status": enrollment.get("status"),
                    "review_status": enrollment.get("review_status"),
                    "worksheet_id": enrollment.get("worksheet_id"),
                    "profile_model_id": enrollment.get("profile_model_id"),
                    "created_at": enrollment.get("created_at"),
                }
            )
            if len(items) >= limit:
                break

        write_audit_log(
            conn,
            "research_authorized_participants_viewed",
            str(actor["id"]),
            "research_participant_list",
            "authorized",
            {
                "capability": capability_id,
                "row_count": len(items),
                "explicit_research_authorization_required": True,
                "direct_user_ids_returned": False,
            },
        )
        conn.commit()

    return {
        "items": items,
        "count": len(items),
        "limit": limit,
        "boundary_notice": "仅列出当前分配范围内且已有明确研究授权的参与者，并使用匿名化标识。",
    }


def list_authorized_assessment_summaries(actor: dict, enrollment_id: str, limit: int) -> dict:
    """Return only minimized assessment summaries for an authorized enrollment.

    Raw answers, score payloads, raw scales and other free-form participant data
    are deliberately excluded from the SELECT list.
    """

    capability_id = "research.participant.read"
    assert_capability(actor, capability_id)
    limit = max(1, min(int(limit), 200))

    with get_connection() as conn:
        enrollment = _authorized_enrollment(conn, actor, enrollment_id, capability_id)
        user_id = str(enrollment["user_id"])
        rows = conn.execute(
            """
            SELECT id, worksheet_id, worksheet_title, category,
                   total_score, result_summary, profile_model_id,
                   profile_cluster_id, profile_confidence, created_at
            FROM assessment_results
            WHERE user_id = ?
            ORDER BY created_at DESC, id DESC
            LIMIT ?
            """,
            (user_id, limit),
        ).fetchall()
        items = rows_to_dicts(rows)
        write_audit_log(
            conn,
            "research_assessment_summaries_viewed",
            str(actor["id"]),
            "relationship_pilot_enrollment",
            enrollment_id,
            {
                "capability": capability_id,
                "participant_user_id": user_id,
                "row_count": len(items),
                "raw_answers_returned": False,
                "raw_scores_returned": False,
                "explicit_research_authorization_required": True,
            },
        )
        conn.commit()

    return {
        "enrollment_id": enrollment_id,
        "anonymous_id": _anonymous_subject_id(user_id),
        "anonymous_scope": True,
        "items": items,
        "count": len(items),
        "limit": limit,
        "boundary_notice": "仅返回当前获分配且有明确研究授权参与者的最小化测评摘要；不返回原始答案或原始计分载荷。",
    }
