"""Human-led, non-diagnostic therapeutic-assessment collaboration workflow."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass

from database import (
    get_connection,
    json_dumps,
    json_loads,
    load_content_json,
    new_id,
    now_iso,
    row_to_dict,
    rows_to_dicts,
    write_audit_log,
)
from services.risk_service import check_text_risk
from services.risk_review_service import create_risk_review_record
from services.therapeutic_assessment_level_service import level as service_level


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


def _feedback_policy() -> dict:
    return load_content_json("therapeutic_assessment_feedback_policy.json")


def _action_policy() -> dict:
    return load_content_json("therapeutic_assessment_action_policy.json")


def _feedback_fields(case: dict, payload: dict) -> dict:
    policy = _feedback_policy()
    source = str(payload.get("source") or "human")
    if source not in {"human", "ai_draft"}:
        raise TherapeuticAssessmentError("validation_error", "反馈来源不受支持。")
    layer = str(payload.get("feedback_layer") or "layer_1")
    if layer in set(policy.get("offline_only_layers") or []):
        raise TherapeuticAssessmentError(
            "challenge_layer_offline_only",
            "挑战性内容不进入数字自动流程，需要线下人工协作。",
            409,
        )
    if layer not in set(policy.get("digital_layers") or []):
        raise TherapeuticAssessmentError("validation_error", "反馈层级不受支持。")
    recipient = str(payload.get("recipient_user_id") or case["participant_user_id"])
    if recipient != str(case["participant_user_id"]):
        raise TherapeuticAssessmentError("recipient_scope_error", "反馈接收者必须是该协作记录的参与者。", 422)
    uncertainty = _required_text(payload, "uncertainty", 1000)
    next_step = _required_text(payload, "next_step", 1000)
    participant_content = _required_text(payload, "participant_content", 3000)
    letter_title = str(payload.get("letter_title") or "给你的阶段性反馈").strip()[:120]
    evidence = payload.get("evidence")
    if not isinstance(evidence, list) or not any(str(item).strip() for item in evidence):
        raise TherapeuticAssessmentError("evidence_required", "反馈必须至少给出一条可核对的依据。", 422)
    observations = payload.get("observations") or []
    alternatives = payload.get("alternatives") or []
    if observations and not any(str(item).strip() for item in alternatives):
        raise TherapeuticAssessmentError(
            "alternatives_required",
            "给出观察时，请同时给出至少一种其它可能的理解。",
            422,
        )
    checked_text = "\n".join((letter_title, participant_content, next_step))
    matched = [phrase for phrase in policy.get("blocked_phrases") or [] if phrase in checked_text]
    if matched:
        raise TherapeuticAssessmentError(
            "feedback_language_blocked",
            "反馈包含诊断、责备、保证或读心式表达，不能进入发送流程。",
            422,
            {"matched_rule_count": len(matched)},
        )
    return {
        "source": source,
        "feedback_layer": layer,
        "recipient_user_id": recipient,
        "letter_title": letter_title,
        "observations": observations,
        "evidence": evidence,
        "alternatives": alternatives,
        "uncertainty": uncertainty,
        "next_step": next_step,
        "human_discussion": payload.get("human_discussion") or [],
        "participant_content": participant_content,
    }


def _assert_feedback_evidence_authorized(
    conn,
    actor: dict,
    case: dict,
    evidence: list,
) -> None:
    data_item_ids = [
        str(item).split(":", 1)[1].strip()
        for item in evidence
        if str(item).startswith("data-item:")
    ]
    if not data_item_ids:
        return
    from services.therapeutic_assessment_consent_service import _can_read, _expired

    for item_id in data_item_ids:
        row = conn.execute(
            "SELECT * FROM therapeutic_assessment_data_items WHERE id = ?",
            (item_id,),
        ).fetchone()
        item = row_to_dict(row) if row is not None else None
        if (
            not item
            or str(item["case_id"]) != str(case["id"])
            or item["status"] != "active"
            or _expired(item)
            or not _can_read(conn, actor, item)
        ):
            raise TherapeuticAssessmentError(
                "evidence_scope_error",
                "反馈引用了当前研究者未获授权的资料。",
                403,
            )


def _insert_feedback_version(
    conn,
    case: dict,
    actor: dict,
    fields: dict,
    *,
    supersedes_feedback_id: str | None = None,
) -> dict:
    version_no = int(
        conn.execute(
            "SELECT COALESCE(MAX(version_no), 0) + 1 AS n FROM therapeutic_assessment_feedback_versions WHERE case_id = ?",
            (case["id"],),
        ).fetchone()["n"]
    )
    feedback_id = new_id("ta_feedback")
    timestamp = now_iso()
    conn.execute(
        """
        INSERT INTO therapeutic_assessment_feedback_versions (
            id, case_id, version_no, author_id, source, status,
            feedback_layer, recipient_user_id, letter_title,
            observations_json, evidence_json, alternatives_json, uncertainty,
            next_step, human_discussion_json, participant_content,
            supersedes_feedback_id, created_at
        ) VALUES (?, ?, ?, ?, ?, 'draft', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            feedback_id,
            case["id"],
            version_no,
            str(actor["id"]),
            fields["source"],
            fields["feedback_layer"],
            fields["recipient_user_id"],
            fields["letter_title"],
            json_dumps(fields["observations"]),
            json_dumps(fields["evidence"]),
            json_dumps(fields["alternatives"]),
            fields["uncertainty"],
            fields["next_step"],
            json_dumps(fields["human_discussion"]),
            fields["participant_content"],
            supersedes_feedback_id,
            timestamp,
        ),
    )
    return row_to_dict(
        conn.execute(
            "SELECT * FROM therapeutic_assessment_feedback_versions WHERE id = ?",
            (feedback_id,),
        ).fetchone()
    )


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
    except sqlite3.IntegrityError as exc:
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
    item["question_candidates"] = json_loads(item.pop("question_candidates_json", None), [])
    item["question_quality"] = json_loads(item.pop("question_quality_json", None), {})
    item["best_guess_notice"] = "最好猜测不是结论，可以随新资料修订或删除。"
    item["service_level"] = service_level(str(item.get("readiness_level") or "L0"))
    feedback = rows_to_dicts(
        conn.execute(
            "SELECT * FROM therapeutic_assessment_feedback_versions WHERE case_id = ? ORDER BY version_no",
            (item["id"],),
        ).fetchall()
    )
    for version in feedback:
        for field in ("observations", "evidence", "alternatives", "human_discussion"):
            version[field] = json_loads(version.pop(f"{field}_json", None), [])
    deliveries = rows_to_dicts(
        conn.execute(
            "SELECT * FROM therapeutic_assessment_feedback_deliveries WHERE case_id = ? ORDER BY sent_at",
            (item["id"],),
        ).fetchall()
    )
    responses = rows_to_dicts(
        conn.execute(
            "SELECT * FROM therapeutic_assessment_feedback_responses WHERE case_id = ? ORDER BY created_at",
            (item["id"],),
        ).fetchall()
    )
    for version in feedback:
        version["deliveries"] = [entry for entry in deliveries if entry["feedback_id"] == version["id"]]
        version["participant_responses"] = [entry for entry in responses if entry["feedback_id"] == version["id"]]
    item["feedback_versions"] = feedback
    item["actions"] = rows_to_dicts(
        conn.execute(
            "SELECT * FROM therapeutic_assessment_actions WHERE case_id = ? ORDER BY created_at",
            (item["id"],),
        ).fetchall()
    )
    for action in item["actions"]:
        action["stop_conditions"] = json_loads(action.pop("stop_conditions_json", None), [])
    item["boundary_notice"] = BOUNDARY_NOTICE
    item["efficacy_score"] = None
    return item


def _present_case(conn, case: dict, actor: dict) -> dict:
    item = _expand_case(conn, case)
    if str(actor.get("role") or "") in {"parent", "student"}:
        item["feedback_versions"] = [
            {
                "id": version["id"],
                "case_id": version["case_id"],
                "version_no": version["version_no"],
                "status": version["status"],
                "feedback_layer": version["feedback_layer"],
                "letter_title": version["letter_title"],
                "participant_content": version["participant_content"],
                "participant_response": (
                    version["participant_responses"][-1] if version["participant_responses"] else None
                ),
                "delivery_count": len(
                    [entry for entry in version["deliveries"] if entry["status"] == "sent"]
                ),
                "sent_at": version.get("sent_at"),
                "created_at": version["created_at"],
            }
            for version in item["feedback_versions"]
            if version["status"] == "sent"
        ]
        for field in ("qualification_evidence_ref", "supervision_evidence_ref", "ethics_evidence_ref"):
            item.pop(field, None)
        item.pop("risk_level", None)
        item["support_signal"] = (
            "needs_human_understanding"
            if item.get("status") == "support_required"
            or item.get("safety_state") in {"needs_human_review", "safety_path"}
            else "ordinary_flow"
        )
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
                working_question,
                shared_scope_json, consent_status, status, risk_level,
                workflow_state, hypothesis_state, safety_state,
                complexity_scope, readiness_level, assigned_researcher_id,
                version, created_by, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, 'active', ?, ?, 'submitted', 'observations_only', ?,
                      ?, 'L0', ?, 1, ?, ?, ?)
            """,
            (
                # assigned_researcher_id 固定为 NULL：参与者不能自选研究者，
                # 研究者只能由督导/管理员通过 assign_case 分配，避免绕过分配门授予读权限。
                case_id, str(actor["id"]), payload.get("enrollment_id"), question, question,
                json_dumps(scope), status, risk["risk_level"],
                "needs_human_review" if risk["requires_review"] else "low_risk",
                complexity,
                None, str(actor["id"]), timestamp, timestamp,
            ),
        )
        _event(
            conn,
            case_id,
            actor,
            "case_created",
            key,
            None,
            1,
            {
                "risk_level": risk["risk_level"],
                "shared_scope": scope,
                "workflow_state": "submitted",
                "hypothesis_state": "observations_only",
                "safety_state": "needs_human_review" if risk["requires_review"] else "low_risk",
            },
        )
        write_audit_log(conn, "therapeutic_assessment_case_created", str(actor["id"]), "therapeutic_assessment_case", case_id, {"risk_level": risk["risk_level"], "consent_status": "active"})
        if risk["requires_review"]:
            create_risk_review_record(
                conn,
                str(actor["id"]),
                "therapeutic_assessment_case",
                case_id,
                risk,
            )
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
        expected = payload.get("expected_version")
        if expected is not None and int(expected) != before:
            raise TherapeuticAssessmentError("version_conflict", "记录已更新，请刷新后重试。", 409)
        note = str(payload.get("note") or "").strip()[:1000]
        if action == "disagree" and not note:
            raise TherapeuticAssessmentError("validation_error", "请简要说明不同意见。")
        status = "withdrawn" if action == "withdraw" else case["status"]
        consent = "withdrawn" if action == "withdraw" else case["consent_status"]
        workflow = (
            "withdrawn"
            if action == "withdraw"
            else "revision_requested"
            if case.get("workflow_state") == "participant_check"
            else case.get("workflow_state")
        )
        timestamp = now_iso()
        cursor = conn.execute(
            """
            UPDATE therapeutic_assessment_cases
            SET status = ?, consent_status = ?, workflow_state = ?, disagreement_note = ?,
                withdrawn_at = ?, version = version + 1, updated_at = ?
            WHERE id = ? AND version = ?
            """,
            (
                status,
                consent,
                workflow,
                note if action == "disagree" else case.get("disagreement_note"),
                timestamp if action == "withdraw" else case.get("withdrawn_at"),
                timestamp,
                case_id,
                before,
            ),
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
    with get_connection() as conn:
        case = _case_row(conn, case_id)
        _assert_researcher(actor, case)
        from services.therapeutic_assessment_safety_service import assert_normal_flow_allowed

        assert_normal_flow_allowed(conn, case)
        if case["status"] in {"withdrawn", "support_required"} or case["consent_status"] != "active":
            raise TherapeuticAssessmentError("invalid_state", "当前记录不能创建普通反馈。", 409)
        fields = _feedback_fields(case, payload)
        _assert_feedback_evidence_authorized(conn, actor, case, fields["evidence"])
    risk = check_text_risk(
        [fields["participant_content"], fields["next_step"]],
        source="therapeutic_assessment_feedback",
    )
    if risk["requires_review"]:
        with get_connection() as conn:
            case = _case_row(conn, case_id)
            create_risk_review_record(
                conn,
                str(case["participant_user_id"]),
                "therapeutic_assessment_feedback_attempt",
                case_id,
                risk,
            )
            write_audit_log(
                conn,
                "therapeutic_assessment_feedback_risk_queued",
                str(actor["id"]),
                "therapeutic_assessment_case",
                case_id,
                {"risk_level": risk["risk_level"]},
            )
            conn.commit()
        raise TherapeuticAssessmentError("risk_review_required", "反馈文本触发安全复核，不能进入普通发送流程。", 409)
    with get_connection() as conn:
        case = _case_row(conn, case_id)
        existing = conn.execute("SELECT * FROM therapeutic_assessment_events WHERE actor_id = ? AND idempotency_key = ?", (str(actor["id"]), key)).fetchone()
        if existing:
            version = conn.execute("SELECT * FROM therapeutic_assessment_feedback_versions WHERE id = ?", (json_loads(existing["metadata_json"], {}).get("feedback_id"),)).fetchone()
            if version:
                return row_to_dict(version), 200
        result = _insert_feedback_version(conn, case, actor, fields)
        _event(conn, case_id, actor, "feedback_drafted", key, case["version"], case["version"], {"feedback_id": result["id"], "source": fields["source"], "layer": fields["feedback_layer"]})
        write_audit_log(conn, "therapeutic_assessment_feedback_drafted", str(actor["id"]), "therapeutic_assessment_feedback", result["id"], {"case_id": case_id, "source": fields["source"], "layer": fields["feedback_layer"]})
        conn.commit()
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
        existing = conn.execute(
            "SELECT 1 FROM therapeutic_assessment_events WHERE actor_id = ? AND idempotency_key = ? AND action IN ('feedback_approved', 'feedback_changes_requested')",
            (str(actor["id"]), key),
        ).fetchone()
        if existing:
            return feedback
        from services.therapeutic_assessment_safety_service import assert_normal_flow_allowed

        assert_normal_flow_allowed(conn, case)
        if case["readiness_level"] != "L2":
            raise TherapeuticAssessmentError("readiness_gate", "L0/L1记录不能进入人工确认和发送。", 409)
        if feedback["status"] != "draft":
            raise TherapeuticAssessmentError("invalid_state", "只有草稿版本可以复核；如需修改，请新建版本。", 409)
        if case["consent_status"] != "active" or case["status"] == "withdrawn":
            raise TherapeuticAssessmentError("consent_withdrawn", "参与者已撤回，不能复核。", 409)
        if str(feedback["author_id"]) == str(actor["id"]):
            raise TherapeuticAssessmentError("self_review_forbidden", "起草人不能复核自己撰写的反馈。", 403)
        status = "reviewed" if decision == "approved" else "draft"
        conn.execute("UPDATE therapeutic_assessment_feedback_versions SET status = ?, reviewed_by = ?, reviewed_at = ? WHERE id = ?", (status, str(actor["id"]), now_iso(), feedback_id))
        _event(conn, case["id"], actor, f"feedback_{decision}", key, case["version"], case["version"], {"feedback_id": feedback_id})
        write_audit_log(conn, f"therapeutic_assessment_feedback_{decision}", str(actor["id"]), "therapeutic_assessment_feedback", feedback_id, {"case_id": case["id"]})
        conn.commit()
        return row_to_dict(conn.execute("SELECT * FROM therapeutic_assessment_feedback_versions WHERE id = ?", (feedback_id,)).fetchone())


def _insert_feedback_delivery(conn, feedback: dict, case: dict, actor: dict, key: str) -> dict:
    timestamp = now_iso()
    sequence = int(
        conn.execute(
            "SELECT COALESCE(MAX(sequence_no), 0) + 1 AS n FROM therapeutic_assessment_feedback_deliveries WHERE feedback_id = ?",
            (feedback["id"],),
        ).fetchone()["n"]
    )
    delivery_id = new_id("ta_delivery")
    conn.execute(
        """
        INSERT INTO therapeutic_assessment_feedback_deliveries (
            id, feedback_id, case_id, recipient_user_id, sequence_no, status,
            sent_by, sent_at, idempotency_key, created_at
        ) VALUES (?, ?, ?, ?, ?, 'sent', ?, ?, ?, ?)
        """,
        (
            delivery_id,
            feedback["id"],
            case["id"],
            feedback.get("recipient_user_id") or case["participant_user_id"],
            sequence,
            str(actor["id"]),
            timestamp,
            key,
            timestamp,
        ),
    )
    return row_to_dict(
        conn.execute(
            "SELECT * FROM therapeutic_assessment_feedback_deliveries WHERE id = ?",
            (delivery_id,),
        ).fetchone()
    )


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
        existing = conn.execute(
            "SELECT 1 FROM therapeutic_assessment_events WHERE actor_id = ? AND idempotency_key = ? AND action = 'feedback_sent'",
            (str(actor["id"]), key),
        ).fetchone()
        if existing:
            return feedback
        from services.therapeutic_assessment_safety_service import assert_normal_flow_allowed

        assert_normal_flow_allowed(conn, case)
        if feedback["status"] != "reviewed" or case["readiness_level"] != "L2":
            raise TherapeuticAssessmentError("human_review_required", "反馈尚未完成人工复核。", 409)
        if case["consent_status"] != "active" or case["status"] == "withdrawn":
            raise TherapeuticAssessmentError("consent_withdrawn", "参与者已撤回，不能发送。", 409)
        timestamp = now_iso()
        _insert_feedback_delivery(conn, feedback, case, actor, key)
        conn.execute("UPDATE therapeutic_assessment_feedback_versions SET status = 'sent', sent_at = ? WHERE id = ?", (timestamp, feedback_id))
        conn.execute("UPDATE therapeutic_assessment_cases SET status = 'feedback_sent', updated_at = ? WHERE id = ?", (timestamp, case["id"]))
        _event(conn, case["id"], actor, "feedback_sent", key, case["version"], case["version"], {"feedback_id": feedback_id})
        write_audit_log(conn, "therapeutic_assessment_feedback_sent", str(actor["id"]), "therapeutic_assessment_feedback", feedback_id, {"case_id": case["id"], "human_reviewed": True})
        conn.commit()
        return row_to_dict(conn.execute("SELECT * FROM therapeutic_assessment_feedback_versions WHERE id = ?", (feedback_id,)).fetchone())


def submit_feedback_response(actor: dict, feedback_id: str, payload: dict, idempotency_key: str) -> tuple[dict, int]:
    key = _idempotency(idempotency_key)
    recognition = str(payload.get("recognition") or "")
    if recognition not in set(_feedback_policy().get("recognition_options") or []):
        raise TherapeuticAssessmentError("validation_error", "反馈核对选项不受支持。")
    disagreement = str(payload.get("disagreement_note") or "").strip()[:2000]
    if recognition == "not_like" and not disagreement:
        raise TherapeuticAssessmentError("disagreement_note_required", "选择“不像”时，请写下不一致之处。", 422)
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM therapeutic_assessment_feedback_versions WHERE id = ?",
            (feedback_id,),
        ).fetchone()
        if row is None:
            raise TherapeuticAssessmentError("not_found", "没有找到反馈版本。", 404)
        feedback = row_to_dict(row)
        case = _case_row(conn, feedback["case_id"])
        _assert_participant(actor, case)
        if feedback["status"] != "sent" or feedback.get("withdrawn_at"):
            raise TherapeuticAssessmentError("feedback_not_available", "这份反馈当前不能核对。", 409)
        existing = conn.execute(
            "SELECT * FROM therapeutic_assessment_feedback_responses WHERE participant_user_id = ? AND idempotency_key = ?",
            (str(actor["id"]), key),
        ).fetchone()
        if existing:
            return row_to_dict(existing), 200
        latest = conn.execute(
            "SELECT id FROM therapeutic_assessment_feedback_responses WHERE feedback_id = ? AND participant_user_id = ? ORDER BY created_at DESC LIMIT 1",
            (feedback_id, str(actor["id"])),
        ).fetchone()
        response_id = new_id("ta_response")
        timestamp = now_iso()
        conn.execute(
            """
            INSERT INTO therapeutic_assessment_feedback_responses (
                id, feedback_id, case_id, participant_user_id, recognition,
                disagreement_note, supersedes_response_id, idempotency_key, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                response_id,
                feedback_id,
                case["id"],
                str(actor["id"]),
                recognition,
                disagreement or None,
                latest["id"] if latest else None,
                key,
                timestamp,
            ),
        )
        next_workflow = "revision_requested" if recognition in {"partly_like", "not_like"} else "participant_check"
        conn.execute(
            """
            UPDATE therapeutic_assessment_cases
            SET workflow_state = ?, disagreement_note = CASE WHEN ? = '' THEN disagreement_note ELSE ? END,
                version = version + 1, updated_at = ?
            WHERE id = ?
            """,
            (next_workflow, disagreement, disagreement, timestamp, case["id"]),
        )
        _event(conn, case["id"], actor, "feedback_response_recorded", key, case["version"], int(case["version"]) + 1, {"feedback_id": feedback_id, "recognition": recognition})
        write_audit_log(conn, "therapeutic_assessment_feedback_response_recorded", str(actor["id"]), "therapeutic_assessment_feedback", feedback_id, {"case_id": case["id"], "recognition": recognition, "disagreement_present": bool(disagreement)})
        conn.commit()
        return row_to_dict(
            conn.execute(
                "SELECT * FROM therapeutic_assessment_feedback_responses WHERE id = ?",
                (response_id,),
            ).fetchone()
        ), 201


def revise_feedback(actor: dict, feedback_id: str, payload: dict, idempotency_key: str) -> tuple[dict, int]:
    key = _idempotency(idempotency_key)
    reason = _required_text(payload, "revision_reason", 1000)
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM therapeutic_assessment_feedback_versions WHERE id = ?",
            (feedback_id,),
        ).fetchone()
        if row is None:
            raise TherapeuticAssessmentError("not_found", "没有找到反馈版本。", 404)
        previous = row_to_dict(row)
        case = _case_row(conn, previous["case_id"])
        _assert_researcher(actor, case)
        expected = int(payload.get("expected_lifecycle_version", -1))
        if expected != int(previous.get("lifecycle_version") or 1):
            raise TherapeuticAssessmentError("version_conflict", "反馈版本已变化，请重新读取。", 409)
        existing = conn.execute(
            "SELECT * FROM therapeutic_assessment_events WHERE actor_id = ? AND idempotency_key = ? AND action = 'feedback_revised'",
            (str(actor["id"]), key),
        ).fetchone()
        if existing:
            replay_id = json_loads(existing["metadata_json"], {}).get("feedback_id")
            return row_to_dict(conn.execute("SELECT * FROM therapeutic_assessment_feedback_versions WHERE id = ?", (replay_id,)).fetchone()), 200
        merged = {
            "source": "human",
            "feedback_layer": payload.get("feedback_layer") or previous["feedback_layer"],
            "recipient_user_id": previous.get("recipient_user_id") or case["participant_user_id"],
            "letter_title": payload.get("letter_title") or previous["letter_title"],
            "observations": payload.get("observations", json_loads(previous["observations_json"], [])),
            "evidence": payload.get("evidence", json_loads(previous["evidence_json"], [])),
            "alternatives": payload.get("alternatives", json_loads(previous["alternatives_json"], [])),
            "uncertainty": payload.get("uncertainty") or previous["uncertainty"],
            "next_step": payload.get("next_step") or previous["next_step"],
            "human_discussion": payload.get("human_discussion", json_loads(previous["human_discussion_json"], [])),
            "participant_content": payload.get("participant_content") or previous["participant_content"],
        }
        fields = _feedback_fields(case, merged)
        _assert_feedback_evidence_authorized(conn, actor, case, fields["evidence"])
        revised = _insert_feedback_version(conn, case, actor, fields, supersedes_feedback_id=feedback_id)
        _event(conn, case["id"], actor, "feedback_revised", key, case["version"], case["version"], {"feedback_id": revised["id"], "supersedes_feedback_id": feedback_id, "revision_reason_present": bool(reason)})
        write_audit_log(conn, "therapeutic_assessment_feedback_revised", str(actor["id"]), "therapeutic_assessment_feedback", revised["id"], {"case_id": case["id"], "supersedes_feedback_id": feedback_id})
        conn.commit()
        return revised, 201


def withdraw_feedback(actor: dict, feedback_id: str, payload: dict, idempotency_key: str) -> dict:
    key = _idempotency(idempotency_key)
    reason = _required_text(payload, "reason", 1000)
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM therapeutic_assessment_feedback_versions WHERE id = ?", (feedback_id,)).fetchone()
        if row is None:
            raise TherapeuticAssessmentError("not_found", "没有找到反馈版本。", 404)
        feedback = row_to_dict(row)
        case = _case_row(conn, feedback["case_id"])
        _assert_researcher(actor, case)
        existing = conn.execute(
            "SELECT 1 FROM therapeutic_assessment_events WHERE actor_id = ? AND idempotency_key = ? AND action = 'feedback_withdrawn'",
            (str(actor["id"]), key),
        ).fetchone()
        if existing:
            return feedback
        if feedback["status"] == "sent" and str(actor.get("role") or "") not in REVIEW_ROLES:
            raise TherapeuticAssessmentError("forbidden", "已发送反馈只能由督导或管理员撤回。", 403)
        expected = int(payload.get("expected_lifecycle_version", -1))
        current = int(feedback.get("lifecycle_version") or 1)
        if expected != current:
            raise TherapeuticAssessmentError("version_conflict", "反馈版本已变化，请重新读取。", 409)
        if feedback["status"] == "withdrawn":
            return feedback
        timestamp = now_iso()
        conn.execute(
            "UPDATE therapeutic_assessment_feedback_versions SET status = 'withdrawn', withdrawn_at = ?, withdrawal_reason = ?, lifecycle_version = lifecycle_version + 1 WHERE id = ?",
            (timestamp, reason, feedback_id),
        )
        conn.execute(
            "UPDATE therapeutic_assessment_feedback_deliveries SET status = 'withdrawn', withdrawn_by = ?, withdrawn_at = ?, withdrawal_reason = ? WHERE feedback_id = ? AND status = 'sent'",
            (str(actor["id"]), timestamp, reason, feedback_id),
        )
        _event(conn, case["id"], actor, "feedback_withdrawn", key, current, current + 1, {"feedback_id": feedback_id})
        write_audit_log(conn, "therapeutic_assessment_feedback_withdrawn", str(actor["id"]), "therapeutic_assessment_feedback", feedback_id, {"case_id": case["id"], "reason_present": True})
        conn.commit()
        return row_to_dict(conn.execute("SELECT * FROM therapeutic_assessment_feedback_versions WHERE id = ?", (feedback_id,)).fetchone())


def resend_feedback(actor: dict, feedback_id: str, idempotency_key: str) -> dict:
    key = _idempotency(idempotency_key)
    if str(actor.get("role") or "") not in REVIEW_ROLES:
        raise TherapeuticAssessmentError("forbidden", "只有督导或管理员可以重新发送反馈。", 403)
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM therapeutic_assessment_feedback_versions WHERE id = ?", (feedback_id,)).fetchone()
        if row is None:
            raise TherapeuticAssessmentError("not_found", "没有找到反馈版本。", 404)
        feedback = row_to_dict(row)
        case = _case_row(conn, feedback["case_id"])
        if feedback["status"] != "sent" or feedback.get("withdrawn_at"):
            raise TherapeuticAssessmentError("invalid_state", "只有仍有效的已发送反馈可以重发。", 409)
        existing = conn.execute(
            "SELECT * FROM therapeutic_assessment_feedback_deliveries WHERE sent_by = ? AND idempotency_key = ?",
            (str(actor["id"]), key),
        ).fetchone()
        if existing:
            return row_to_dict(existing)
        from services.therapeutic_assessment_safety_service import assert_normal_flow_allowed

        assert_normal_flow_allowed(conn, case)
        delivery = _insert_feedback_delivery(conn, feedback, case, actor, key)
        _event(conn, case["id"], actor, "feedback_resent", key, feedback.get("lifecycle_version"), feedback.get("lifecycle_version"), {"feedback_id": feedback_id, "delivery_id": delivery["id"], "sequence_no": delivery["sequence_no"]})
        write_audit_log(conn, "therapeutic_assessment_feedback_resent", str(actor["id"]), "therapeutic_assessment_feedback", feedback_id, {"case_id": case["id"], "sequence_no": delivery["sequence_no"]})
        conn.commit()
        return delivery


def create_action(actor: dict, case_id: str, payload: dict, idempotency_key: str) -> tuple[dict, int]:
    key = _idempotency(idempotency_key)
    action_text = _required_text(payload, "action_text", 500)
    purpose_text = _required_text(payload, "purpose_text", 500)
    planned_date = str(payload.get("planned_date") or "").strip()
    if planned_date and (
        len(planned_date) != 10
        or planned_date[4] != "-"
        or planned_date[7] != "-"
        or not planned_date.replace("-", "").isdigit()
    ):
        raise TherapeuticAssessmentError("validation_error", "计划日期需使用YYYY-MM-DD格式。")
    policy = _action_policy()
    if not all(payload.get(field) is True for field in policy["required_confirmations"]):
        raise TherapeuticAssessmentError(
            "action_safety_confirmation_required",
            "行动必须由参与者自愿选择，并确认可逆、可停止。",
            422,
        )
    reminder_mode = str(payload.get("reminder_mode") or "none")
    reminder_privacy = str(payload.get("reminder_privacy") or "generic_preview")
    if reminder_mode not in set(policy["reminder_modes"]):
        raise TherapeuticAssessmentError("validation_error", "提醒方式不受支持。")
    if reminder_privacy not in set(policy["reminder_privacy_options"]):
        raise TherapeuticAssessmentError("validation_error", "提醒隐私方式不受支持。")
    stop_conditions = payload.get("stop_conditions")
    if not isinstance(stop_conditions, list) or not any(str(item).strip() for item in stop_conditions):
        raise TherapeuticAssessmentError("validation_error", "至少需要一条停止条件。")
    stop_conditions = [str(item).strip()[:300] for item in stop_conditions if str(item).strip()][:10]
    setback_plan = _required_text(payload, "setback_plan", 800)
    training_card_id = str(payload.get("training_card_id") or "").strip()[:128] or None
    if training_card_id:
        card_ids = {
            str(item.get("id") or "")
            for item in load_content_json("training_cards.json").get("cards", [])
            if isinstance(item, dict)
        }
        if training_card_id not in card_ids:
            raise TherapeuticAssessmentError("validation_error", "关联训练卡不存在。", 422)
    with get_connection() as conn:
        case = _case_row(conn, case_id)
        _assert_participant(actor, case)
        from services.therapeutic_assessment_safety_service import assert_normal_flow_allowed

        assert_normal_flow_allowed(conn, case)
        if case["status"] == "withdrawn" or case["consent_status"] == "withdrawn":
            raise TherapeuticAssessmentError("withdrawn", "该协作已经撤回，不能再选择下一小步。", 409)
        if (
            case["risk_level"] != policy["allowed_case_scope"]["risk_level"]
            or case["complexity_scope"] != policy["allowed_case_scope"]["complexity_scope"]
            or case["readiness_level"] not in set(policy["allowed_case_scope"]["readiness_levels"])
        ):
            raise TherapeuticAssessmentError(
                "action_scope_blocked",
                "当前记录不进入普通行动推荐，请等待人工支持。",
                409,
            )
        existing = conn.execute(
            "SELECT * FROM therapeutic_assessment_events WHERE actor_id = ? AND idempotency_key = ? AND action = 'action_chosen'",
            (str(actor["id"]), key),
        ).fetchone()
        if existing:
            action_id = json_loads(existing["metadata_json"], {}).get("action_id")
            result = row_to_dict(
                conn.execute(
                    "SELECT * FROM therapeutic_assessment_actions WHERE id = ?",
                    (action_id,),
                ).fetchone()
            )
            result["stop_conditions"] = json_loads(result.pop("stop_conditions_json", None), [])
            return result, 200
        if not conn.execute("SELECT 1 FROM therapeutic_assessment_feedback_versions WHERE case_id = ? AND status = 'sent'", (case_id,)).fetchone():
            raise TherapeuticAssessmentError("feedback_not_sent", "收到经人工复核的反馈后才能选择下一小步。", 409)
        feedback_version_id = payload.get("feedback_version_id")
        if feedback_version_id and not conn.execute(
            "SELECT 1 FROM therapeutic_assessment_feedback_versions WHERE id = ? AND case_id = ?",
            (feedback_version_id, case_id),
        ).fetchone():
            raise TherapeuticAssessmentError("validation_error", "引用的反馈版本不属于该协作记录。", 422)
        action_id = new_id("ta_action")
        timestamp = now_iso()
        conn.execute(
            """
            INSERT INTO therapeutic_assessment_actions (
                id, case_id, participant_user_id, feedback_version_id, action_text,
                purpose_text, planned_date, reminder_mode, reminder_privacy,
                stop_conditions_json, setback_plan, training_card_id,
                status, version, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'chosen', 1, ?, ?)
            """,
            (
                action_id,
                case_id,
                str(actor["id"]),
                feedback_version_id,
                action_text,
                purpose_text,
                planned_date or None,
                reminder_mode,
                reminder_privacy,
                json_dumps(stop_conditions),
                setback_plan,
                training_card_id,
                timestamp,
                timestamp,
            ),
        )
        _event(conn, case_id, actor, "action_chosen", key, case["version"], case["version"], {"action_id": action_id})
        write_audit_log(conn, "therapeutic_assessment_action_chosen", str(actor["id"]), "therapeutic_assessment_action", action_id, {"case_id": case_id})
        conn.commit()
        result = row_to_dict(conn.execute("SELECT * FROM therapeutic_assessment_actions WHERE id = ?", (action_id,)).fetchone())
        result["stop_conditions"] = json_loads(result.pop("stop_conditions_json", None), [])
        return result, 201


def update_action(actor: dict, action_id: str, payload: dict, idempotency_key: str) -> dict:
    key = _idempotency(idempotency_key)
    status = str(payload.get("status") or "")
    if status not in {"completed", "declined", "stopped"}:
        raise TherapeuticAssessmentError("validation_error", "动作状态不受支持。")
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM therapeutic_assessment_actions WHERE id = ?", (action_id,)).fetchone()
        if row is None:
            raise TherapeuticAssessmentError("not_found", "没有找到该行动记录。", 404)
        action = row_to_dict(row)
        if str(action["participant_user_id"]) != str(actor["id"]):
            raise TherapeuticAssessmentError("forbidden", "只能更新自己的行动记录。", 403)
        replay = conn.execute(
            "SELECT 1 FROM therapeutic_assessment_events WHERE actor_id = ? AND idempotency_key = ? AND action = ?",
            (str(actor["id"]), key, f"action_{status}"),
        ).fetchone()
        if replay:
            action["stop_conditions"] = json_loads(action.pop("stop_conditions_json", None), [])
            return action
        expected = payload.get("expected_version")
        if not isinstance(expected, int) or expected != int(action.get("version") or 1):
            raise TherapeuticAssessmentError("version_conflict", "行动记录已变化，请重新读取。", 409)
        note = str(payload.get("followup_note") or "").strip()[:1000]
        linked_checkin_id = str(payload.get("linked_checkin_id") or "").strip() or None
        if linked_checkin_id and not conn.execute(
            "SELECT 1 FROM checkins WHERE id = ? AND user_id = ?",
            (linked_checkin_id, str(actor["id"])),
        ).fetchone():
            raise TherapeuticAssessmentError("validation_error", "关联打卡不属于当前参与者。", 422)
        timestamp = now_iso()
        cursor = conn.execute(
            """
            UPDATE therapeutic_assessment_actions
            SET status = ?, followup_note = ?, linked_checkin_id = COALESCE(?, linked_checkin_id),
                version = version + 1, completed_at = ?, updated_at = ?
            WHERE id = ? AND version = ?
            """,
            (
                status,
                note or None,
                linked_checkin_id,
                timestamp if status == "completed" else action.get("completed_at"),
                timestamp,
                action_id,
                expected,
            ),
        )
        if cursor.rowcount != 1:
            raise TherapeuticAssessmentError("version_conflict", "行动记录已变化，请重新读取。", 409)
        _event(conn, action["case_id"], actor, f"action_{status}", key, None, None, {"action_id": action_id, "followup_present": bool(note)})
        write_audit_log(conn, f"therapeutic_assessment_action_{status}", str(actor["id"]), "therapeutic_assessment_action", action_id, {"case_id": action["case_id"]})
        conn.commit()
        result = row_to_dict(conn.execute("SELECT * FROM therapeutic_assessment_actions WHERE id = ?", (action_id,)).fetchone())
        result["stop_conditions"] = json_loads(result.pop("stop_conditions_json", None), [])
        return result
