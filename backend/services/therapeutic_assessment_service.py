"""Human-led, non-diagnostic therapeutic-assessment collaboration workflow."""

from __future__ import annotations

from dataclasses import dataclass

from database import (
    get_connection,
    json_dumps,
    json_loads,
    new_id,
    now_iso,
    row_to_dict,
    rows_to_dicts,
    write_audit_log,
)
from services.risk_service import check_text_risk


BOUNDARY_NOTICE = "本功能用于共同理解当前体验和商量下一小步，不构成诊断、治疗承诺或疗效评分。"
FORMAL_ROLES = {"researcher", "supervisor", "admin"}
REVIEW_ROLES = {"supervisor", "admin"}
ALLOWED_COMPLEXITY = {"individual_adult_low_risk", "child", "couple", "multi_person", "diagnostic"}


@dataclass
class TherapeuticAssessmentError(ValueError):
    code: str
    message: str
    status: int = 400
    details: dict | None = None

    def __str__(self) -> str:
        return self.message


def _required_text(payload: dict, key: str, limit: int) -> str:
    value = str(payload.get(key) or "").strip()
    if not value or len(value) > limit:
        raise TherapeuticAssessmentError("validation_error", f"{key}不能为空且不能超过{limit}字。")
    return value


def _idempotency(value: str) -> str:
    normalized = str(value or "").strip()[:128]
    if not normalized:
        raise TherapeuticAssessmentError("validation_error", "写入操作需要 Idempotency-Key。")
    return normalized


def _case_row(conn, case_id: str) -> dict:
    row = conn.execute("SELECT * FROM therapeutic_assessment_cases WHERE id = ?", (case_id,)).fetchone()
    if row is None:
        raise TherapeuticAssessmentError("not_found", "没有找到该协作记录。", 404)
    return row_to_dict(row)


def _can_read(actor: dict, case: dict) -> bool:
    actor_id = str(actor["id"])
    role = str(actor.get("role") or "")
    return (
        actor_id == str(case["participant_user_id"])
        or role in {"admin", "supervisor"}
        or (role == "researcher" and actor_id == str(case.get("assigned_researcher_id") or ""))
    )


def _assert_read(actor: dict, case: dict) -> None:
    if not _can_read(actor, case):
        raise TherapeuticAssessmentError("forbidden", "当前账号没有该记录的对象范围权限。", 403)


def _assert_participant(actor: dict, case: dict) -> None:
    if str(actor["id"]) != str(case["participant_user_id"]):
        raise TherapeuticAssessmentError("forbidden", "只能修改自己的协作记录。", 403)


def _assert_researcher(actor: dict, case: dict) -> None:
    role = str(actor.get("role") or "")
    if role not in FORMAL_ROLES:
        raise TherapeuticAssessmentError("forbidden", "该操作仅向正式研究角色开放。", 403)
    if role == "researcher" and str(actor["id"]) != str(case.get("assigned_researcher_id") or ""):
        raise TherapeuticAssessmentError("forbidden", "研究者只能处理分配给自己的记录。", 403)


def _event(conn, case_id: str, actor: dict, action: str, key: str, before: int | None, after: int | None, metadata: dict) -> None:
    try:
        conn.execute(
            """
            INSERT INTO therapeutic_assessment_events (
                id, case_id, actor_id, action, before_version, after_version,
                idempotency_key, metadata_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (new_id("ta_event"), case_id, str(actor["id"]), action, before, after, key, json_dumps(metadata), now_iso()),
        )
    except Exception as exc:
        existing = conn.execute(
            "SELECT case_id, action FROM therapeutic_assessment_events WHERE actor_id = ? AND idempotency_key = ?",
            (str(actor["id"]), key),
        ).fetchone()
        if existing and existing["case_id"] == case_id and existing["action"] == action:
            raise TherapeuticAssessmentError("already_processed", "该操作已经处理。", 409) from exc
        raise TherapeuticAssessmentError("idempotency_conflict", "该提交标识已用于其它操作。", 409) from exc


def _expand_case(conn, case: dict) -> dict:
    item = dict(case)
    item["shared_scope"] = json_loads(item.pop("shared_scope_json", None), [])
    feedback = rows_to_dicts(
        conn.execute(
            "SELECT * FROM therapeutic_assessment_feedback_versions WHERE case_id = ? ORDER BY version_no",
            (item["id"],),
        ).fetchall()
    )
    for version in feedback:
        for field in ("observations", "evidence", "alternatives", "human_discussion"):
            version[field] = json_loads(version.pop(f"{field}_json", None), [])
    item["feedback_versions"] = feedback
    item["actions"] = rows_to_dicts(
        conn.execute(
            "SELECT * FROM therapeutic_assessment_actions WHERE case_id = ? ORDER BY created_at",
            (item["id"],),
        ).fetchall()
    )
    item["boundary_notice"] = BOUNDARY_NOTICE
    item["efficacy_score"] = None
    return item


def _present_case(conn, case: dict, actor: dict) -> dict:
    item = _expand_case(conn, case)
    if str(actor.get("role") or "") in {"parent", "student"}:
        item["feedback_versions"] = [
            version for version in item["feedback_versions"] if version["status"] == "sent"
        ]
        for field in ("qualification_evidence_ref", "supervision_evidence_ref", "ethics_evidence_ref"):
            item.pop(field, None)
    return item


def create_case(actor: dict, payload: dict, idempotency_key: str) -> tuple[dict, int]:
    key = _idempotency(idempotency_key)
    if str(actor.get("role") or "") not in {"parent", "student"}:
        raise TherapeuticAssessmentError("forbidden", "协作问题由参与者本人发起。", 403)
    if payload.get("consent") is not True:
        raise TherapeuticAssessmentError("consent_required", "需要先同意本次共享范围。", 409)
    question = _required_text(payload, "assessment_question", 1000)
    scope = payload.get("shared_scope")
    if not isinstance(scope, list) or not scope:
        raise TherapeuticAssessmentError("validation_error", "请至少选择一项共享范围。")
    complexity = str(payload.get("complexity_scope") or "individual_adult_low_risk")
    if complexity not in ALLOWED_COMPLEXITY:
        raise TherapeuticAssessmentError("validation_error", "不支持的协作范围。")
    risk = check_text_risk([question], source="therapeutic_assessment")
    timestamp = now_iso()
    with get_connection() as conn:
        existing = conn.execute(
            "SELECT c.* FROM therapeutic_assessment_events e JOIN therapeutic_assessment_cases c ON c.id = e.case_id WHERE e.actor_id = ? AND e.idempotency_key = ?",
            (str(actor["id"]), key),
        ).fetchone()
        if existing:
            return _present_case(conn, row_to_dict(existing), actor), 200
        case_id = new_id("ta_case")
        status = "support_required" if risk["requires_review"] else "open"
        conn.execute(
            """
            INSERT INTO therapeutic_assessment_cases (
                id, participant_user_id, enrollment_id, assessment_question,
                shared_scope_json, consent_status, status, risk_level,
                complexity_scope, readiness_level, assigned_researcher_id,
                version, created_by, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, 'active', ?, ?, ?, 'L0', ?, 1, ?, ?, ?)
            """,
            (
                # assigned_researcher_id 固定为 NULL：参与者不能自选研究者，
                # 研究者只能由督导/管理员通过 assign_case 分配，避免绕过分配门授予读权限。
                case_id, str(actor["id"]), payload.get("enrollment_id"), question,
                json_dumps(scope), status, risk["risk_level"], complexity,
                None, str(actor["id"]), timestamp, timestamp,
            ),
        )
        _event(conn, case_id, actor, "case_created", key, None, 1, {"risk_level": risk["risk_level"], "shared_scope": scope})
        write_audit_log(conn, "therapeutic_assessment_case_created", str(actor["id"]), "therapeutic_assessment_case", case_id, {"risk_level": risk["risk_level"], "consent_status": "active"})
        conn.commit()
        result = _present_case(conn, _case_row(conn, case_id), actor)
    return result, 201


def list_cases(actor: dict) -> dict:
    role = str(actor.get("role") or "")
    with get_connection() as conn:
        if role in {"parent", "student"}:
            rows = conn.execute("SELECT * FROM therapeutic_assessment_cases WHERE participant_user_id = ? ORDER BY created_at DESC", (str(actor["id"]),)).fetchall()
        elif role == "researcher":
            rows = conn.execute("SELECT * FROM therapeutic_assessment_cases WHERE assigned_researcher_id = ? ORDER BY created_at DESC", (str(actor["id"]),)).fetchall()
        elif role in {"supervisor", "admin"}:
            rows = conn.execute("SELECT * FROM therapeutic_assessment_cases ORDER BY created_at DESC LIMIT 200").fetchall()
        else:
            raise TherapeuticAssessmentError("forbidden", "当前角色不能查看协作记录。", 403)
        items = [_present_case(conn, row_to_dict(row), actor) for row in rows]
        write_audit_log(conn, "therapeutic_assessment_cases_viewed", str(actor["id"]), "therapeutic_assessment_case", "list", {"count": len(items)})
        conn.commit()
    return {"items": items, "count": len(items), "boundary_notice": BOUNDARY_NOTICE}


def get_case(actor: dict, case_id: str) -> dict:
    with get_connection() as conn:
        case = _case_row(conn, case_id)
        _assert_read(actor, case)
        write_audit_log(conn, "therapeutic_assessment_case_viewed", str(actor["id"]), "therapeutic_assessment_case", case_id, {})
        conn.commit()
        return _present_case(conn, case, actor)


def update_scope(actor: dict, case_id: str, payload: dict, idempotency_key: str) -> dict:
    key = _idempotency(idempotency_key)
    scope = payload.get("shared_scope")
    if not isinstance(scope, list) or not scope:
        raise TherapeuticAssessmentError("validation_error", "共享范围不能为空。")
    expected = int(payload.get("expected_version") or 0)
    with get_connection() as conn:
        case = _case_row(conn, case_id)
        _assert_participant(actor, case)
        if case["status"] == "withdrawn":
            raise TherapeuticAssessmentError("withdrawn", "该协作已经撤回。", 409)
        if int(case["version"]) != expected:
            raise TherapeuticAssessmentError("version_conflict", "记录已更新，请刷新后重试。", 409)
        updated_at = now_iso()
        cursor = conn.execute(
            "UPDATE therapeutic_assessment_cases SET shared_scope_json = ?, version = version + 1, updated_at = ? WHERE id = ? AND version = ?",
            (json_dumps(scope), updated_at, case_id, expected),
        )
        if cursor.rowcount != 1:
            raise TherapeuticAssessmentError("version_conflict", "记录已更新，请刷新后重试。", 409)
        _event(conn, case_id, actor, "scope_updated", key, expected, expected + 1, {"shared_scope": scope})
        write_audit_log(conn, "therapeutic_assessment_scope_updated", str(actor["id"]), "therapeutic_assessment_case", case_id, {"before_version": expected, "after_version": expected + 1})
        conn.commit()
        return _present_case(conn, _case_row(conn, case_id), actor)


def participant_transition(actor: dict, case_id: str, payload: dict, idempotency_key: str, action: str) -> dict:
    key = _idempotency(idempotency_key)
    with get_connection() as conn:
        case = _case_row(conn, case_id)
        _assert_participant(actor, case)
        before = int(case["version"])
        # 撤回是终态：已撤回的协作不能再撤回或提异议，避免反复流转与版本空转。
        if case["status"] == "withdrawn" or case["consent_status"] == "withdrawn":
            raise TherapeuticAssessmentError("withdrawn", "该协作已经撤回，不能再变更。", 409)
        note = str(payload.get("note") or "").strip()[:1000]
        if action == "disagree" and not note:
            raise TherapeuticAssessmentError("validation_error", "请简要说明不同意见。")
        status = "withdrawn" if action == "withdraw" else case["status"]
        consent = "withdrawn" if action == "withdraw" else case["consent_status"]
        timestamp = now_iso()
        cursor = conn.execute(
            """
            UPDATE therapeutic_assessment_cases
            SET status = ?, consent_status = ?, disagreement_note = ?,
                withdrawn_at = ?, version = version + 1, updated_at = ?
            WHERE id = ? AND version = ?
            """,
            (status, consent, note if action == "disagree" else case.get("disagreement_note"), timestamp if action == "withdraw" else case.get("withdrawn_at"), timestamp, case_id, before),
        )
        if cursor.rowcount != 1:
            raise TherapeuticAssessmentError("version_conflict", "记录已更新，请刷新后重试。", 409)
        _event(conn, case_id, actor, action, key, before, before + 1, {"note_length": len(note)})
        write_audit_log(conn, f"therapeutic_assessment_{action}", str(actor["id"]), "therapeutic_assessment_case", case_id, {"before_version": before, "after_version": before + 1})
        conn.commit()
        return _present_case(conn, _case_row(conn, case_id), actor)


def assign_case(actor: dict, case_id: str, payload: dict, idempotency_key: str) -> dict:
    key = _idempotency(idempotency_key)
    if str(actor.get("role") or "") not in REVIEW_ROLES:
        raise TherapeuticAssessmentError("forbidden", "只有督导或管理员可以分配记录。", 403)
    researcher_id = _required_text(payload, "researcher_id", 128)
    with get_connection() as conn:
        case = _case_row(conn, case_id)
        before = int(case["version"])
        conn.execute("UPDATE therapeutic_assessment_cases SET assigned_researcher_id = ?, version = version + 1, updated_at = ? WHERE id = ?", (researcher_id, now_iso(), case_id))
        _event(conn, case_id, actor, "assigned", key, before, before + 1, {"researcher_id": researcher_id})
        write_audit_log(conn, "therapeutic_assessment_assigned", str(actor["id"]), "therapeutic_assessment_case", case_id, {"researcher_id": researcher_id})
        conn.commit()
        return _present_case(conn, _case_row(conn, case_id), actor)


def set_readiness(actor: dict, case_id: str, payload: dict, idempotency_key: str) -> dict:
    key = _idempotency(idempotency_key)
    if str(actor.get("role") or "") not in REVIEW_ROLES:
        raise TherapeuticAssessmentError("forbidden", "只有督导或管理员可登记人工门禁证据。", 403)
    refs = {name: _required_text(payload, name, 500) for name in ("qualification_evidence_ref", "supervision_evidence_ref", "ethics_evidence_ref")}
    with get_connection() as conn:
        case = _case_row(conn, case_id)
        if case["risk_level"] != "low" or case["complexity_scope"] != "individual_adult_low_risk":
            raise TherapeuticAssessmentError("external_gate_required", "该范围仍需D01-D26资格、督导和伦理门禁，不能进入发送阶段。", 409)
        before = int(case["version"])
        conn.execute(
            """
            UPDATE therapeutic_assessment_cases SET readiness_level = 'L2',
                qualification_evidence_ref = ?, supervision_evidence_ref = ?,
                ethics_evidence_ref = ?, version = version + 1, updated_at = ? WHERE id = ?
            """,
            (refs["qualification_evidence_ref"], refs["supervision_evidence_ref"], refs["ethics_evidence_ref"], now_iso(), case_id),
        )
        _event(conn, case_id, actor, "readiness_confirmed", key, before, before + 1, refs)
        write_audit_log(conn, "therapeutic_assessment_readiness_confirmed", str(actor["id"]), "therapeutic_assessment_case", case_id, {"evidence_refs_recorded": True})
        conn.commit()
        return _present_case(conn, _case_row(conn, case_id), actor)


def create_feedback(actor: dict, case_id: str, payload: dict, idempotency_key: str) -> tuple[dict, int]:
    key = _idempotency(idempotency_key)
    source = str(payload.get("source") or "human")
    if source not in {"human", "ai_draft"}:
        raise TherapeuticAssessmentError("validation_error", "反馈来源不受支持。")
    uncertainty = _required_text(payload, "uncertainty", 1000)
    next_step = _required_text(payload, "next_step", 1000)
    participant_content = _required_text(payload, "participant_content", 3000)
    risk = check_text_risk([participant_content, next_step], source="therapeutic_assessment_feedback")
    if risk["requires_review"]:
        raise TherapeuticAssessmentError("risk_review_required", "反馈文本触发安全复核，不能进入普通发送流程。", 409)
    with get_connection() as conn:
        case = _case_row(conn, case_id)
        _assert_researcher(actor, case)
        if case["status"] in {"withdrawn", "support_required"} or case["consent_status"] != "active":
            raise TherapeuticAssessmentError("invalid_state", "当前记录不能创建普通反馈。", 409)
        existing = conn.execute("SELECT * FROM therapeutic_assessment_events WHERE actor_id = ? AND idempotency_key = ?", (str(actor["id"]), key)).fetchone()
        if existing:
            version = conn.execute("SELECT * FROM therapeutic_assessment_feedback_versions WHERE id = ?", (json_loads(existing["metadata_json"], {}).get("feedback_id"),)).fetchone()
            if version:
                return row_to_dict(version), 200
        version_no = int(conn.execute("SELECT COALESCE(MAX(version_no), 0) + 1 AS n FROM therapeutic_assessment_feedback_versions WHERE case_id = ?", (case_id,)).fetchone()["n"])
        feedback_id = new_id("ta_feedback")
        timestamp = now_iso()
        conn.execute(
            """
            INSERT INTO therapeutic_assessment_feedback_versions (
                id, case_id, version_no, author_id, source, status,
                observations_json, evidence_json, alternatives_json, uncertainty,
                next_step, human_discussion_json, participant_content, created_at
            ) VALUES (?, ?, ?, ?, ?, 'draft', ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                feedback_id, case_id, version_no, str(actor["id"]), source,
                json_dumps(payload.get("observations") or []), json_dumps(payload.get("evidence") or []),
                json_dumps(payload.get("alternatives") or []), uncertainty, next_step,
                json_dumps(payload.get("human_discussion") or []), participant_content, timestamp,
            ),
        )
        _event(conn, case_id, actor, "feedback_drafted", key, case["version"], case["version"], {"feedback_id": feedback_id, "source": source})
        write_audit_log(conn, "therapeutic_assessment_feedback_drafted", str(actor["id"]), "therapeutic_assessment_feedback", feedback_id, {"case_id": case_id, "source": source})
        conn.commit()
        result = row_to_dict(conn.execute("SELECT * FROM therapeutic_assessment_feedback_versions WHERE id = ?", (feedback_id,)).fetchone())
    return result, 201


def review_feedback(actor: dict, feedback_id: str, payload: dict, idempotency_key: str) -> dict:
    key = _idempotency(idempotency_key)
    if str(actor.get("role") or "") not in REVIEW_ROLES:
        raise TherapeuticAssessmentError("forbidden", "发送前必须由督导或管理员人工复核。", 403)
    decision = str(payload.get("decision") or "")
    if decision not in {"approved", "changes_requested"}:
        raise TherapeuticAssessmentError("validation_error", "人工复核结论不受支持。")
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM therapeutic_assessment_feedback_versions WHERE id = ?", (feedback_id,)).fetchone()
        if row is None:
            raise TherapeuticAssessmentError("not_found", "没有找到反馈版本。", 404)
        feedback = row_to_dict(row)
        case = _case_row(conn, feedback["case_id"])
        if case["readiness_level"] != "L2":
            raise TherapeuticAssessmentError("readiness_gate", "L0/L1记录不能进入人工确认和发送。", 409)
        # 已发送的反馈是终态，不能再被复核改回 draft/reviewed；只允许复核 draft 或 reviewed 版本。
        if feedback["status"] not in {"draft", "reviewed"}:
            raise TherapeuticAssessmentError("invalid_state", "该反馈版本已发送或不可复核。", 409)
        status = "reviewed" if decision == "approved" else "draft"
        conn.execute("UPDATE therapeutic_assessment_feedback_versions SET status = ?, reviewed_by = ?, reviewed_at = ? WHERE id = ?", (status, str(actor["id"]), now_iso(), feedback_id))
        _event(conn, case["id"], actor, f"feedback_{decision}", key, case["version"], case["version"], {"feedback_id": feedback_id})
        write_audit_log(conn, f"therapeutic_assessment_feedback_{decision}", str(actor["id"]), "therapeutic_assessment_feedback", feedback_id, {"case_id": case["id"]})
        conn.commit()
        return row_to_dict(conn.execute("SELECT * FROM therapeutic_assessment_feedback_versions WHERE id = ?", (feedback_id,)).fetchone())


def send_feedback(actor: dict, feedback_id: str, idempotency_key: str) -> dict:
    key = _idempotency(idempotency_key)
    if str(actor.get("role") or "") not in REVIEW_ROLES:
        raise TherapeuticAssessmentError("forbidden", "只有人工复核角色可以发送。", 403)
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM therapeutic_assessment_feedback_versions WHERE id = ?", (feedback_id,)).fetchone()
        if row is None:
            raise TherapeuticAssessmentError("not_found", "没有找到反馈版本。", 404)
        feedback = row_to_dict(row)
        case = _case_row(conn, feedback["case_id"])
        if feedback["status"] != "reviewed" or case["readiness_level"] != "L2":
            raise TherapeuticAssessmentError("human_review_required", "反馈尚未完成人工复核。", 409)
        if case["consent_status"] != "active" or case["status"] == "withdrawn":
            raise TherapeuticAssessmentError("consent_withdrawn", "参与者已撤回，不能发送。", 409)
        timestamp = now_iso()
        conn.execute("UPDATE therapeutic_assessment_feedback_versions SET status = 'sent', sent_at = ? WHERE id = ?", (timestamp, feedback_id))
        conn.execute("UPDATE therapeutic_assessment_cases SET status = 'feedback_sent', updated_at = ? WHERE id = ?", (timestamp, case["id"]))
        _event(conn, case["id"], actor, "feedback_sent", key, case["version"], case["version"], {"feedback_id": feedback_id})
        write_audit_log(conn, "therapeutic_assessment_feedback_sent", str(actor["id"]), "therapeutic_assessment_feedback", feedback_id, {"case_id": case["id"], "human_reviewed": True})
        conn.commit()
        return row_to_dict(conn.execute("SELECT * FROM therapeutic_assessment_feedback_versions WHERE id = ?", (feedback_id,)).fetchone())


def create_action(actor: dict, case_id: str, payload: dict, idempotency_key: str) -> tuple[dict, int]:
    key = _idempotency(idempotency_key)
    action_text = _required_text(payload, "action_text", 500)
    with get_connection() as conn:
        case = _case_row(conn, case_id)
        _assert_participant(actor, case)
        if not conn.execute("SELECT 1 FROM therapeutic_assessment_feedback_versions WHERE case_id = ? AND status = 'sent'", (case_id,)).fetchone():
            raise TherapeuticAssessmentError("feedback_not_sent", "收到经人工复核的反馈后才能选择下一小步。", 409)
        action_id = new_id("ta_action")
        timestamp = now_iso()
        conn.execute(
            "INSERT INTO therapeutic_assessment_actions (id, case_id, participant_user_id, feedback_version_id, action_text, status, created_at, updated_at) VALUES (?, ?, ?, ?, ?, 'chosen', ?, ?)",
            (action_id, case_id, str(actor["id"]), payload.get("feedback_version_id"), action_text, timestamp, timestamp),
        )
        _event(conn, case_id, actor, "action_chosen", key, case["version"], case["version"], {"action_id": action_id})
        write_audit_log(conn, "therapeutic_assessment_action_chosen", str(actor["id"]), "therapeutic_assessment_action", action_id, {"case_id": case_id})
        conn.commit()
        return row_to_dict(conn.execute("SELECT * FROM therapeutic_assessment_actions WHERE id = ?", (action_id,)).fetchone()), 201


def update_action(actor: dict, action_id: str, payload: dict, idempotency_key: str) -> dict:
    key = _idempotency(idempotency_key)
    status = str(payload.get("status") or "")
    if status not in {"completed", "declined"}:
        raise TherapeuticAssessmentError("validation_error", "动作状态不受支持。")
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM therapeutic_assessment_actions WHERE id = ?", (action_id,)).fetchone()
        if row is None:
            raise TherapeuticAssessmentError("not_found", "没有找到该行动记录。", 404)
        action = row_to_dict(row)
        if str(action["participant_user_id"]) != str(actor["id"]):
            raise TherapeuticAssessmentError("forbidden", "只能更新自己的行动记录。", 403)
        note = str(payload.get("followup_note") or "").strip()[:1000]
        conn.execute("UPDATE therapeutic_assessment_actions SET status = ?, followup_note = ?, updated_at = ? WHERE id = ?", (status, note or None, now_iso(), action_id))
        _event(conn, action["case_id"], actor, f"action_{status}", key, None, None, {"action_id": action_id, "followup_present": bool(note)})
        write_audit_log(conn, f"therapeutic_assessment_action_{status}", str(actor["id"]), "therapeutic_assessment_action", action_id, {"case_id": action["case_id"]})
        conn.commit()
        return row_to_dict(conn.execute("SELECT * FROM therapeutic_assessment_actions WHERE id = ?", (action_id,)).fetchone())
