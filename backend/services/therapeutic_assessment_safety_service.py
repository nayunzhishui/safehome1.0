"""Human responsibility chain and safety pause controls for Task38-F07."""

from __future__ import annotations

from datetime import datetime, timezone

from database import get_connection, new_id, now_iso, row_to_dict, write_audit_log
from services.therapeutic_assessment_service import (
    REVIEW_ROLES,
    TherapeuticAssessmentError,
    _assert_participant,
    _assert_researcher,
    _case_row,
    _idempotency,
)


SIGNAL_TYPES = {
    "self_harm",
    "harm_other",
    "violence",
    "abuse",
    "coercive_control",
    "acute_crisis",
    "other",
}
CHAIN_STATUSES = {"active", "inactive"}
PARTICIPANT_ROLES = {"parent", "student"}


def _runtime_row(conn) -> dict:
    row = conn.execute("SELECT * FROM therapeutic_assessment_runtime_control WHERE id = 'global'").fetchone()
    if row is None:
        timestamp = now_iso()
        conn.execute(
            """INSERT INTO therapeutic_assessment_runtime_control
            (id, killed, reason, changed_by, changed_at)
            VALUES ('global', 0, NULL, 'system', ?)""",
            (timestamp,),
        )
        row = conn.execute("SELECT * FROM therapeutic_assessment_runtime_control WHERE id = 'global'").fetchone()
    return row_to_dict(row)


def _kill(conn, reason: str, actor_id: str = "system") -> None:
    timestamp = now_iso()
    conn.execute(
        """UPDATE therapeutic_assessment_runtime_control
        SET killed = 1, reason = ?, changed_by = ?, changed_at = ? WHERE id = 'global'""",
        (reason[:500], actor_id, timestamp),
    )


def _chain(conn, case_id: str) -> dict | None:
    row = conn.execute(
        "SELECT * FROM therapeutic_assessment_responsibility_chains WHERE case_id = ?",
        (case_id,),
    ).fetchone()
    return row_to_dict(row) if row is not None else None


def _minutes_since(value: str) -> float:
    then = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if then.tzinfo is None:
        then = then.replace(tzinfo=timezone.utc)
    return (datetime.now(timezone.utc) - then.astimezone(timezone.utc)).total_seconds() / 60


def _visible_open_count(conn, actor: dict) -> int:
    role = str(actor.get("role") or "")
    actor_id = str(actor["id"])
    where = ""
    params: tuple[str, ...] = ()
    if role in PARTICIPANT_ROLES:
        where = " AND c.participant_user_id = ?"
        params = (actor_id,)
    elif role == "researcher":
        where = " AND c.assigned_researcher_id = ?"
        params = (actor_id,)
    elif role not in REVIEW_ROLES:
        return 0
    row = conn.execute(
        f"""SELECT COUNT(*) AS c
        FROM therapeutic_assessment_safety_events e
        JOIN therapeutic_assessment_cases c ON c.id = e.case_id
        WHERE e.state IN ('needs_human_understanding', 'safety_paused', 'human_taken_over')
        {where}""",
        params,
    ).fetchone()
    return int(row["c"])


def evaluate_runtime(conn) -> dict:
    runtime = _runtime_row(conn)
    open_events = conn.execute(
        """SELECT * FROM therapeutic_assessment_safety_events
        WHERE state IN ('needs_human_understanding', 'safety_paused', 'human_taken_over')
        ORDER BY created_at"""
    ).fetchall()
    for row in open_events:
        event = row_to_dict(row)
        chain = _chain(conn, str(event["case_id"]))
        if chain is None or chain["status"] != "active":
            _kill(conn, "responsibility_chain_unavailable")
            return _runtime_row(conn)
        if _minutes_since(str(event["created_at"])) > int(chain["queue_timeout_minutes"]):
            _kill(conn, "human_queue_timeout")
            return _runtime_row(conn)
    return runtime


def public_safety_status(actor: dict) -> dict:
    with get_connection() as conn:
        runtime = evaluate_runtime(conn)
        open_count = _visible_open_count(conn, actor)
        write_audit_log(
            conn,
            "therapeutic_assessment_safety_status_viewed",
            str(actor["id"]),
            "therapeutic_assessment_runtime",
            "global",
            {"killed": bool(runtime["killed"]), "open_count": open_count},
        )
        conn.commit()
        result = {
            "ordinary_flow_enabled": not bool(runtime["killed"]),
            "needs_human_understanding_count": open_count,
            "participant_message": (
                "普通反馈和训练暂时暂停，请等待真人支持。"
                if runtime["killed"]
                else "普通流程当前可用；安全信号仍由真人负责处理。"
            ),
            "reactivation_requires_human_evidence": True,
        }
        if str(actor.get("role") or "") in REVIEW_ROLES:
            result["pause_reason"] = runtime.get("reason")
        return result


def configure_responsibility_chain(
    actor: dict,
    case_id: str,
    payload: dict,
    idempotency_key: str,
) -> dict:
    if str(actor.get("role") or "") not in REVIEW_ROLES:
        raise TherapeuticAssessmentError("forbidden", "责任链只能由督导或管理员配置。", 403)
    key = _idempotency(idempotency_key)
    responsible = str(payload.get("responsible_user_id") or "").strip()
    supervisor = str(payload.get("supervisor_user_id") or "").strip()
    channel = str(payload.get("support_channel") or "").strip()[:500]
    evidence = str(payload.get("evidence_ref") or "").strip()[:500]
    status = str(payload.get("status") or "active")
    timeout = payload.get("queue_timeout_minutes", 30)
    expected = payload.get("expected_version", 0)
    if (
        not responsible
        or not supervisor
        or not channel
        or not evidence
        or status not in CHAIN_STATUSES
        or not isinstance(timeout, int)
        or not 5 <= timeout <= 1440
        or not isinstance(expected, int)
    ):
        raise TherapeuticAssessmentError("validation_error", "责任人、督导、支持通道、证据、状态、超时或版本无效。")
    timestamp = now_iso()
    with get_connection() as conn:
        case = _case_row(conn, case_id)
        _assert_researcher(actor, case)
        for user_id in (responsible, supervisor):
            user = conn.execute(
                "SELECT role, status FROM users WHERE id = ?",
                (user_id,),
            ).fetchone()
            if user is None or user["status"] != "active" or user["role"] not in {"researcher", "supervisor", "admin"}:
                raise TherapeuticAssessmentError("validation_error", "责任链人员必须是有效的专业角色。")
        existing = _chain(conn, case_id)
        if existing and existing["idempotency_key"] == key:
            return existing
        current_version = int(existing["version"]) if existing else 0
        if current_version != expected:
            raise TherapeuticAssessmentError("version_conflict", "责任链已更新，请刷新后重试。", 409)
        if existing is None:
            chain_id = new_id("ta_chain")
            conn.execute(
                """INSERT INTO therapeutic_assessment_responsibility_chains
                (id, case_id, responsible_user_id, supervisor_user_id, support_channel,
                 evidence_ref, status, queue_timeout_minutes, version, idempotency_key,
                 created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?, ?)""",
                (chain_id, case_id, responsible, supervisor, channel, evidence, status, timeout, key, timestamp, timestamp),
            )
        else:
            chain_id = str(existing["id"])
            updated = conn.execute(
                """UPDATE therapeutic_assessment_responsibility_chains
                SET responsible_user_id = ?, supervisor_user_id = ?, support_channel = ?,
                    evidence_ref = ?, status = ?, queue_timeout_minutes = ?,
                    version = version + 1, idempotency_key = ?, updated_at = ?
                WHERE id = ? AND version = ?""",
                (responsible, supervisor, channel, evidence, status, timeout, key, timestamp, chain_id, expected),
            )
            if updated.rowcount != 1:
                raise TherapeuticAssessmentError("version_conflict", "责任链已更新，请刷新后重试。", 409)
        if status == "inactive":
            _runtime_row(conn)
            _kill(conn, "responsibility_chain_inactive", str(actor["id"]))
        write_audit_log(
            conn,
            "therapeutic_assessment_responsibility_chain_configured",
            str(actor["id"]),
            "therapeutic_assessment_case",
            case_id,
            {"status": status, "queue_timeout_minutes": timeout},
        )
        conn.commit()
        return row_to_dict(conn.execute(
            "SELECT * FROM therapeutic_assessment_responsibility_chains WHERE id = ?",
            (chain_id,),
        ).fetchone())


def create_safety_signal(actor: dict, case_id: str, payload: dict, idempotency_key: str) -> tuple[dict, int]:
    key = _idempotency(idempotency_key)
    signal_type = str(payload.get("signal_type") or "")
    source_ref = str(payload.get("source_ref") or "").strip()[:500]
    reason = str(payload.get("reason_summary") or "").strip()[:500]
    if signal_type not in SIGNAL_TYPES or not source_ref:
        raise TherapeuticAssessmentError("validation_error", "需要有效的安全信号类型和来源引用。")
    actor_id = str(actor["id"])
    timestamp = now_iso()
    with get_connection() as conn:
        case = _case_row(conn, case_id)
        if str(actor.get("role") or "") in PARTICIPANT_ROLES:
            _assert_participant(actor, case)
        else:
            _assert_researcher(actor, case)
        replay = conn.execute(
            "SELECT * FROM therapeutic_assessment_safety_events WHERE detected_by = ? AND idempotency_key = ?",
            (actor_id, key),
        ).fetchone()
        if replay is not None:
            if str(replay["case_id"]) != case_id:
                raise TherapeuticAssessmentError("idempotency_conflict", "该提交标识已用于其它安全事件。", 409)
            return row_to_dict(replay), 200
        event_id = new_id("ta_safety")
        conn.execute(
            """INSERT INTO therapeutic_assessment_safety_events
            (id, case_id, signal_type, state, source_ref, reason_summary, detected_by,
             idempotency_key, created_at, updated_at)
            VALUES (?, ?, ?, 'needs_human_understanding', ?, ?, ?, ?, ?, ?)""",
            (event_id, case_id, signal_type, source_ref, reason, actor_id, key, timestamp, timestamp),
        )
        conn.execute(
            """UPDATE therapeutic_assessment_cases
            SET safety_state = 'safety_path', workflow_state = 'safety_path',
                status = 'support_required', version = version + 1, updated_at = ?
            WHERE id = ?""",
            (timestamp, case_id),
        )
        _runtime_row(conn)
        chain = _chain(conn, case_id)
        if chain is None or chain["status"] != "active":
            _kill(conn, "responsibility_chain_unavailable")
        write_audit_log(
            conn,
            "therapeutic_assessment_safety_signal_recorded",
            actor_id,
            "therapeutic_assessment_case",
            case_id,
            {"signal_type": signal_type, "ordinary_flow_paused": True},
        )
        conn.commit()
        return row_to_dict(conn.execute(
            "SELECT * FROM therapeutic_assessment_safety_events WHERE id = ?",
            (event_id,),
        ).fetchone()), 201


def resolve_safety_event(actor: dict, event_id: str, payload: dict, idempotency_key: str) -> dict:
    if str(actor.get("role") or "") not in REVIEW_ROLES:
        raise TherapeuticAssessmentError("forbidden", "只有督导或管理员可以解除安全暂停。", 403)
    _idempotency(idempotency_key)
    evidence = str(payload.get("resolution_evidence_ref") or "").strip()[:500]
    if not evidence:
        raise TherapeuticAssessmentError("evidence_required", "解除安全暂停必须提供真人处置证据。", 422)
    timestamp = now_iso()
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM therapeutic_assessment_safety_events WHERE id = ?", (event_id,)).fetchone()
        if row is None:
            raise TherapeuticAssessmentError("not_found", "没有找到该安全事件。", 404)
        event = row_to_dict(row)
        case = _case_row(conn, str(event["case_id"]))
        _assert_researcher(actor, case)
        chain = _chain(conn, str(event["case_id"]))
        if chain is None or chain["status"] != "active":
            raise TherapeuticAssessmentError("human_chain_required", "责任链未生效，不能解除安全暂停。", 409)
        if event["state"] == "resolved_by_human":
            return event
        conn.execute(
            """UPDATE therapeutic_assessment_safety_events
            SET state = 'resolved_by_human', resolution_evidence_ref = ?, resolved_by = ?,
                resolved_at = ?, updated_at = ? WHERE id = ?""",
            (evidence, str(actor["id"]), timestamp, timestamp, event_id),
        )
        remaining = int(conn.execute(
            """SELECT COUNT(*) AS c FROM therapeutic_assessment_safety_events
            WHERE case_id = ? AND state IN ('needs_human_understanding', 'safety_paused', 'human_taken_over')""",
            (event["case_id"],),
        ).fetchone()["c"])
        if remaining == 0:
            conn.execute(
                """UPDATE therapeutic_assessment_cases
                SET safety_state = 'resolved_by_human', workflow_state = 'pending_human_review',
                    status = 'open', version = version + 1, updated_at = ? WHERE id = ?""",
                (timestamp, event["case_id"]),
            )
        write_audit_log(
            conn,
            "therapeutic_assessment_safety_event_resolved",
            str(actor["id"]),
            "therapeutic_assessment_safety_event",
            event_id,
            {"resolution_evidence_ref_recorded": True, "remaining_open": remaining},
        )
        conn.commit()
        return row_to_dict(conn.execute(
            "SELECT * FROM therapeutic_assessment_safety_events WHERE id = ?",
            (event_id,),
        ).fetchone())


def restore_runtime(actor: dict, payload: dict) -> dict:
    if str(actor.get("role") or "") not in REVIEW_ROLES:
        raise TherapeuticAssessmentError("forbidden", "只有督导或管理员可以提交恢复证据。", 403)
    evidence = str(payload.get("restoration_evidence_ref") or "").strip()[:500]
    if not evidence:
        raise TherapeuticAssessmentError("evidence_required", "恢复普通流程必须提供证据。", 422)
    with get_connection() as conn:
        open_count = int(conn.execute(
            """SELECT COUNT(*) AS c FROM therapeutic_assessment_safety_events
            WHERE state IN ('needs_human_understanding', 'safety_paused', 'human_taken_over')"""
        ).fetchone()["c"])
        if open_count:
            raise TherapeuticAssessmentError("open_safety_events", "仍有未完成人工处置的安全事件。", 409)
        timestamp = now_iso()
        _runtime_row(conn)
        conn.execute(
            """UPDATE therapeutic_assessment_runtime_control
            SET killed = 0, reason = NULL, changed_by = ?, changed_at = ?,
                restoration_evidence_ref = ? WHERE id = 'global'""",
            (str(actor["id"]), timestamp, evidence),
        )
        write_audit_log(
            conn,
            "therapeutic_assessment_runtime_restored",
            str(actor["id"]),
            "therapeutic_assessment_runtime",
            "global",
            {"restoration_evidence_ref_recorded": True},
        )
        conn.commit()
        return {
            "ordinary_flow_enabled": True,
            "needs_human_understanding_count": 0,
            "pause_reason": None,
            "participant_message": "普通流程当前可用；安全信号仍由真人负责处理。",
            "reactivation_requires_human_evidence": True,
        }


def assert_normal_flow_allowed(conn, case: dict) -> None:
    runtime = evaluate_runtime(conn)
    if runtime["killed"]:
        raise TherapeuticAssessmentError("safety_kill_switch", "普通反馈和训练暂时暂停，请等待真人支持。", 409)
    if case.get("status") == "support_required" or case.get("safety_state") in {
        "needs_human_review",
        "safety_path",
    }:
        raise TherapeuticAssessmentError("human_support_required", "当前记录需要真人了解，不能进入普通反馈或训练。", 409)
