"""Auditable draft-preview-confirm-send workflow for researcher deliveries."""

from __future__ import annotations

import hashlib
import json

from database import get_connection, json_dumps, json_loads, new_id, now_iso, row_to_dict, rows_to_dicts, write_audit_log
from services.message_service import create_message, public_message
from services.relationship_pilot_common import BOUNDARY
from services.research_access_service import ResearchAccessError, require_object_scope
from services.risk_service import check_text_risk


DELIVERY_TYPES = {"stage_feedback", "participant_message"}
ACTIVE_STATUSES = {"draft", "previewed", "confirmed", "sent"}


class ResearchDeliveryError(ValueError):
    def __init__(self, code: str, message: str, status: int = 400) -> None:
        super().__init__(message)
        self.code = code
        self.status = status


def _hash_payload(title: str, content: dict) -> str:
    encoded = json.dumps({"title": title, "content": content}, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _validate_content(delivery_type: str, title: str, content: dict) -> dict:
    title = str(title or "").strip()
    if not title or len(title) > 60:
        raise ResearchDeliveryError("validation_error", "标题需为1至60个字符。")
    if not isinstance(content, dict):
        raise ResearchDeliveryError("validation_error", "内容格式不正确。")
    if delivery_type == "participant_message":
        body = str(content.get("body") or "").strip()
        if not body or len(body) > 2000:
            raise ResearchDeliveryError("validation_error", "消息正文需为1至2000个字符。")
        return {"body": body}
    observation = str(content.get("observation") or "").strip()
    evidence = str(content.get("evidence") or "").strip()
    next_step = str(content.get("next_step") or "").strip()
    open_question = str(content.get("open_question") or "").strip()
    if not observation or not next_step:
        raise ResearchDeliveryError("validation_error", "阶段性反馈需要填写近期观察和下一小步。")
    if any(len(value) > limit for value, limit in ((observation, 600), (evidence, 600), (next_step, 600), (open_question, 400))):
        raise ResearchDeliveryError("validation_error", "阶段性反馈内容超过长度限制。")
    return {
        "observation": observation,
        "evidence": evidence,
        "next_step": next_step,
        "open_question": open_question,
    }


def _render_content(delivery_type: str, content: dict) -> str:
    if delivery_type == "participant_message":
        return str(content.get("body") or "")
    sections = [
        f"近期可观察到的变化：{content['observation']}",
        f"可供共同核对的依据：{content['evidence']}" if content.get("evidence") else "",
        f"可以先尝试的一小步：{content['next_step']}",
        f"后续可继续讨论：{content['open_question']}" if content.get("open_question") else "",
    ]
    return "\n\n".join(item for item in sections if item)


def _event_replay(conn, actor_id: str, idempotency_key: str, workflow_id: str, action: str) -> dict | None:
    if not idempotency_key or len(idempotency_key) > 120:
        raise ResearchDeliveryError("validation_error", "每一步都需要有效的幂等键。")
    row = conn.execute(
        "SELECT * FROM research_delivery_events WHERE actor_id = ? AND idempotency_key = ?",
        (actor_id, idempotency_key),
    ).fetchone()
    if row is None:
        return None
    item = row_to_dict(row)
    if item["workflow_id"] != workflow_id or item["action"] != action:
        raise ResearchDeliveryError("idempotency_conflict", "该幂等键已用于其他交付操作。", 409)
    result = get_workflow_in_connection(conn, workflow_id)
    result["idempotency_replayed"] = True
    if action == "send":
        result["already_sent"] = True
    return result


def _record_event(conn, workflow: dict, actor: dict, action: str, from_status: str | None, to_status: str, idempotency_key: str, metadata: dict | None = None) -> None:
    conn.execute(
        """
        INSERT INTO research_delivery_events (
            id, workflow_id, actor_id, action, from_status, to_status,
            metadata_json, idempotency_key, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            new_id("delivery_evt"),
            workflow["id"],
            str(actor["id"]),
            action,
            from_status,
            to_status,
            json_dumps(metadata or {}),
            idempotency_key,
            now_iso(),
        ),
    )


def _authorized_workflow(conn, actor: dict, workflow_id: str, *, require_active_enrollment: bool = True) -> tuple[dict, dict]:
    row = conn.execute("SELECT * FROM research_delivery_workflows WHERE id = ?", (workflow_id,)).fetchone()
    if row is None:
        raise ResearchDeliveryError("not_found", "没有找到这份交付草稿。", 404)
    workflow = row_to_dict(row)
    enrollment_row = conn.execute("SELECT * FROM relationship_pilot_enrollments WHERE id = ?", (workflow["enrollment_id"],)).fetchone()
    if enrollment_row is None:
        raise ResearchDeliveryError("not_found", "没有找到对应参与者报名。", 404)
    enrollment = row_to_dict(enrollment_row)
    try:
        require_object_scope(conn, actor, enrollment, "research.feedback.write")
    except ResearchAccessError as exc:
        raise ResearchDeliveryError(exc.code, str(exc), exc.status) from exc
    if require_active_enrollment and enrollment.get("status") != "enrolled":
        raise ResearchDeliveryError("enrollment_not_active", "参与者当前不在项目中，不能继续交付。", 409)
    return workflow, enrollment


def _check_expected_version(workflow: dict, expected_version) -> int:
    try:
        expected = int(expected_version)
    except (TypeError, ValueError) as exc:
        raise ResearchDeliveryError("validation_error", "expected_version必须是非负整数。") from exc
    if expected < 0:
        raise ResearchDeliveryError("validation_error", "expected_version必须是非负整数。")
    if expected != int(workflow["version"]):
        raise ResearchDeliveryError("version_conflict", "草稿已在其他位置更新，请刷新后重试。", 409)
    return expected


def _active_version(conn, workflow: dict) -> dict | None:
    if not workflow.get("active_version_id"):
        return None
    row = conn.execute("SELECT * FROM research_delivery_versions WHERE id = ?", (workflow["active_version_id"],)).fetchone()
    if row is None:
        return None
    item = row_to_dict(row)
    item["content"] = json_loads(item.pop("content_json"), {})
    return item


def _queue_delivery_risk_review(conn, actor: dict, workflow: dict, risk: dict) -> str:
    existing = conn.execute(
        """
        SELECT id FROM risk_review_records
        WHERE source_type = 'research_delivery_workflow' AND source_id = ?
          AND review_status IN ('pending', 'priority_review')
        ORDER BY created_at DESC LIMIT 1
        """,
        (workflow["id"],),
    ).fetchone()
    if existing:
        return str(existing["id"])
    review_id = new_id("risk_review")
    timestamp = now_iso()
    conn.execute(
        """
        INSERT INTO risk_review_records (
            id, user_id, source_type, source_id, risk_level, matched_categories_json,
            review_status, reviewer_id, review_note, action_taken, closed_reason,
            reviewed_at, created_at, updated_at
        ) VALUES (?, ?, 'research_delivery_workflow', ?, ?, ?, 'priority_review',
                  NULL, NULL, NULL, NULL, NULL, ?, ?)
        """,
        (
            review_id,
            workflow["user_id"],
            workflow["id"],
            str(risk.get("risk_level") or "high"),
            json_dumps(risk.get("matched_categories") or []),
            timestamp,
            timestamp,
        ),
    )
    write_audit_log(
        conn,
        "research_delivery_risk_queued",
        actor["id"],
        "risk_review_record",
        review_id,
        {"workflow_id": workflow["id"], "risk_level": risk.get("risk_level")},
    )
    return review_id


def get_workflow_in_connection(conn, workflow_id: str) -> dict:
    workflow = row_to_dict(conn.execute("SELECT * FROM research_delivery_workflows WHERE id = ?", (workflow_id,)).fetchone())
    if workflow is None:
        raise ResearchDeliveryError("not_found", "没有找到这份交付草稿。", 404)
    workflow["content"] = json_loads(workflow.pop("draft_json"), {})
    workflow["active_version"] = _active_version(conn, workflow)
    workflow["message"] = None
    if workflow.get("message_id"):
        message = conn.execute("SELECT * FROM messages WHERE id = ?", (workflow["message_id"],)).fetchone()
        workflow["message"] = public_message(row_to_dict(message)) if message else None
    workflow["preview"] = {
        "title": workflow["title"],
        "body": _render_content(workflow["delivery_type"], workflow["content"]),
        "boundary_notice": BOUNDARY,
    }
    workflow["events"] = rows_to_dicts(
        conn.execute(
            "SELECT action, from_status, to_status, created_at FROM research_delivery_events WHERE workflow_id = ? ORDER BY created_at ASC",
            (workflow_id,),
        ).fetchall()
    )
    return workflow


def create_delivery(actor: dict, payload: dict, idempotency_key: str) -> tuple[dict, int]:
    enrollment_id = str(payload.get("enrollment_id") or "").strip()
    delivery_type = str(payload.get("delivery_type") or "").strip()
    if delivery_type not in DELIVERY_TYPES:
        raise ResearchDeliveryError("validation_error", "delivery_type不受支持。")
    if not enrollment_id:
        raise ResearchDeliveryError("validation_error", "请选择参与者。")
    title = str(payload.get("title") or "").strip()
    content = _validate_content(delivery_type, title, payload.get("content") or {})
    if not idempotency_key or len(idempotency_key) > 120:
        raise ResearchDeliveryError("validation_error", "创建草稿需要有效的幂等键。")
    with get_connection() as conn:
        existing = conn.execute(
            "SELECT * FROM research_delivery_workflows WHERE actor_id = ? AND create_idempotency_key = ?",
            (str(actor["id"]), idempotency_key),
        ).fetchone()
        if existing:
            item = row_to_dict(existing)
            if item["enrollment_id"] != enrollment_id or item["delivery_type"] != delivery_type or item["title"] != title or json_loads(item["draft_json"], {}) != content:
                raise ResearchDeliveryError("idempotency_conflict", "该幂等键已用于另一份草稿。", 409)
            result = get_workflow_in_connection(conn, item["id"])
            result["idempotency_replayed"] = True
            return result, 200
        enrollment_row = conn.execute("SELECT * FROM relationship_pilot_enrollments WHERE id = ?", (enrollment_id,)).fetchone()
        if enrollment_row is None:
            raise ResearchDeliveryError("not_found", "没有找到对应参与者报名。", 404)
        enrollment = row_to_dict(enrollment_row)
        try:
            require_object_scope(conn, actor, enrollment, "research.feedback.write")
        except ResearchAccessError as exc:
            raise ResearchDeliveryError(exc.code, str(exc), exc.status) from exc
        if enrollment.get("status") != "enrolled":
            raise ResearchDeliveryError("enrollment_not_active", "参与者当前不在项目中，不能创建交付草稿。", 409)
        workflow_id = new_id("delivery")
        timestamp = now_iso()
        conn.execute(
            """
            INSERT INTO research_delivery_workflows (
                id, enrollment_id, user_id, actor_id, delivery_type, status, title,
                draft_json, active_version_id, source_report_id, message_id, version,
                create_idempotency_key, confirmed_at, sent_at, withdrawn_at, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, 'draft', ?, ?, NULL, NULL, NULL, 0, ?, NULL, NULL, NULL, ?, ?)
            """,
            (workflow_id, enrollment_id, enrollment["user_id"], str(actor["id"]), delivery_type, title, json_dumps(content), idempotency_key, timestamp, timestamp),
        )
        workflow = {"id": workflow_id}
        _record_event(conn, workflow, actor, "create", None, "draft", idempotency_key)
        write_audit_log(conn, "research_delivery_draft_created", actor["id"], "research_delivery_workflow", workflow_id, {"delivery_type": delivery_type, "enrollment_id": enrollment_id})
        conn.commit()
        return get_workflow_in_connection(conn, workflow_id), 201


def list_deliveries(actor: dict, enrollment_id: str, page: int, page_size: int) -> dict:
    offset = (page - 1) * page_size
    with get_connection() as conn:
        enrollment_row = conn.execute("SELECT * FROM relationship_pilot_enrollments WHERE id = ?", (enrollment_id,)).fetchone()
        if enrollment_row is None:
            raise ResearchDeliveryError("not_found", "没有找到对应参与者报名。", 404)
        try:
            ensure_researcher_assignment(conn, actor, row_to_dict(enrollment_row))
        except RelationshipPilotError as exc:
            raise ResearchDeliveryError(exc.code, exc.message, exc.status) from exc
        total = int(conn.execute("SELECT COUNT(*) AS count FROM research_delivery_workflows WHERE enrollment_id = ?", (enrollment_id,)).fetchone()["count"])
        rows = conn.execute(
            "SELECT id FROM research_delivery_workflows WHERE enrollment_id = ? ORDER BY updated_at DESC LIMIT ? OFFSET ?",
            (enrollment_id, page_size, offset),
        ).fetchall()
        items = [get_workflow_in_connection(conn, row["id"]) for row in rows]
        write_audit_log(conn, "research_deliveries_viewed", actor["id"], "relationship_pilot_enrollment", enrollment_id, {"count": len(items), "page": page})
        conn.commit()
    return {"items": items, "count": len(items), "total": total, "page": page, "page_size": page_size, "has_more": offset + len(items) < total}


def get_delivery(actor: dict, workflow_id: str) -> dict:
    with get_connection() as conn:
        _authorized_workflow(conn, actor, workflow_id, require_active_enrollment=False)
        result = get_workflow_in_connection(conn, workflow_id)
        write_audit_log(conn, "research_delivery_viewed", actor["id"], "research_delivery_workflow", workflow_id, {"status": result["status"]})
        conn.commit()
    return result


def save_draft(actor: dict, workflow_id: str, payload: dict, idempotency_key: str) -> dict:
    with get_connection() as conn:
        replay = _event_replay(conn, str(actor["id"]), idempotency_key, workflow_id, "save_draft")
        if replay:
            return replay
        workflow, _enrollment = _authorized_workflow(conn, actor, workflow_id)
        _check_expected_version(workflow, payload.get("expected_version"))
        if workflow["status"] in {"sent", "withdrawn"}:
            raise ResearchDeliveryError("delivery_locked", "已发送或已撤回的内容不能覆盖，请新建版本。", 409)
        title = str(payload.get("title") or workflow["title"]).strip()
        content = _validate_content(workflow["delivery_type"], title, payload.get("content") or json_loads(workflow["draft_json"], {}))
        next_version = int(workflow["version"]) + 1
        conn.execute(
            "UPDATE research_delivery_workflows SET status = 'draft', title = ?, draft_json = ?, active_version_id = NULL, version = ?, updated_at = ? WHERE id = ? AND version = ?",
            (title, json_dumps(content), next_version, now_iso(), workflow_id, workflow["version"]),
        )
        _record_event(conn, workflow, actor, "save_draft", workflow["status"], "draft", idempotency_key)
        write_audit_log(conn, "research_delivery_draft_saved", actor["id"], "research_delivery_workflow", workflow_id, {"delivery_type": workflow["delivery_type"]})
        conn.commit()
        return get_workflow_in_connection(conn, workflow_id)


def preview_delivery(actor: dict, workflow_id: str, payload: dict, idempotency_key: str) -> dict:
    with get_connection() as conn:
        replay = _event_replay(conn, str(actor["id"]), idempotency_key, workflow_id, "preview")
        if replay:
            return replay
        workflow, _enrollment = _authorized_workflow(conn, actor, workflow_id)
        _check_expected_version(workflow, payload.get("expected_version"))
        if workflow["status"] not in {"draft", "previewed"}:
            raise ResearchDeliveryError("delivery_not_editable", "只有草稿可以重新预览。", 409)
        content = _validate_content(workflow["delivery_type"], workflow["title"], json_loads(workflow["draft_json"], {}))
        body = _render_content(workflow["delivery_type"], content)
        risk = check_text_risk([workflow["title"], body], source=f"research_delivery_{workflow['delivery_type']}")
        if risk.get("risk_level") == "high" and actor.get("role") == "researcher":
            _queue_delivery_risk_review(conn, actor, workflow, risk)
            conn.commit()
            raise ResearchDeliveryError("delivery_requires_supervisor_review", "内容包含需要督导复核的高风险表述。", 409)
        version_no = int(conn.execute("SELECT COALESCE(MAX(version_no), 0) AS max_version FROM research_delivery_versions WHERE workflow_id = ?", (workflow_id,)).fetchone()["max_version"]) + 1
        version_id = new_id("delivery_ver")
        timestamp = now_iso()
        conn.execute(
            "INSERT INTO research_delivery_versions (id, workflow_id, version_no, title, content_json, content_hash, risk_level, created_by, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (version_id, workflow_id, version_no, workflow["title"], json_dumps(content), _hash_payload(workflow["title"], content), str(risk.get("risk_level") or "low"), str(actor["id"]), timestamp),
        )
        next_version = int(workflow["version"]) + 1
        conn.execute(
            "UPDATE research_delivery_workflows SET status = 'previewed', active_version_id = ?, version = ?, updated_at = ? WHERE id = ? AND version = ?",
            (version_id, next_version, timestamp, workflow_id, workflow["version"]),
        )
        _record_event(conn, workflow, actor, "preview", workflow["status"], "previewed", idempotency_key, {"delivery_version": version_no, "risk_level": risk.get("risk_level")})
        write_audit_log(conn, "research_delivery_previewed", actor["id"], "research_delivery_workflow", workflow_id, {"delivery_version": version_no, "risk_level": risk.get("risk_level")})
        conn.commit()
        return get_workflow_in_connection(conn, workflow_id)


def confirm_delivery(actor: dict, workflow_id: str, payload: dict, idempotency_key: str) -> dict:
    with get_connection() as conn:
        replay = _event_replay(conn, str(actor["id"]), idempotency_key, workflow_id, "confirm")
        if replay:
            return replay
        workflow, _enrollment = _authorized_workflow(conn, actor, workflow_id)
        _check_expected_version(workflow, payload.get("expected_version"))
        if workflow["status"] != "previewed" or not workflow.get("active_version_id"):
            raise ResearchDeliveryError("delivery_not_previewed", "请先预览并核对内容。", 409)
        timestamp = now_iso()
        next_version = int(workflow["version"]) + 1
        conn.execute(
            "UPDATE research_delivery_workflows SET status = 'confirmed', confirmed_at = ?, version = ?, updated_at = ? WHERE id = ? AND version = ?",
            (timestamp, next_version, timestamp, workflow_id, workflow["version"]),
        )
        _record_event(conn, workflow, actor, "confirm", "previewed", "confirmed", idempotency_key)
        write_audit_log(conn, "research_delivery_confirmed", actor["id"], "research_delivery_workflow", workflow_id)
        conn.commit()
        return get_workflow_in_connection(conn, workflow_id)


def _create_stage_report(conn, actor: dict, workflow: dict, delivery_version: dict) -> str:
    latest = conn.execute(
        "SELECT * FROM relationship_screening_reports WHERE enrollment_id = ? ORDER BY created_at DESC LIMIT 1",
        (workflow["enrollment_id"],),
    ).fetchone()
    report = json_loads(latest["report_json"], {}) if latest else {}
    content = delivery_version["content"]
    report.update(
        {
            "title": "阶段性反馈",
            "personalized_interpretation": _render_content("stage_feedback", content),
            "stage_feedback": content,
            "boundary_notice": report.get("boundary_notice") or BOUNDARY,
            "version": f"delivery-{workflow['id']}-v{delivery_version['version_no']}",
            "generated_at": now_iso(),
        }
    )
    report_id = new_id("rel_report")
    timestamp = now_iso()
    assessment_result_id = latest["assessment_result_id"] if latest else conn.execute(
        "SELECT assessment_result_id FROM relationship_pilot_enrollments WHERE id = ?",
        (workflow["enrollment_id"],),
    ).fetchone()["assessment_result_id"]
    conn.execute(
        """
        INSERT INTO relationship_screening_reports (
            id, enrollment_id, user_id, assessment_result_id, status, version, report_json,
            confirmed_by, confirmed_at, created_at, updated_at
        ) VALUES (?, ?, ?, ?, 'sent', ?, ?, ?, ?, ?, ?)
        """,
        (report_id, workflow["enrollment_id"], workflow["user_id"], assessment_result_id, report["version"], json_dumps(report), str(actor["id"]), timestamp, timestamp, timestamp),
    )
    return report_id


def send_delivery(actor: dict, workflow_id: str, payload: dict, idempotency_key: str) -> tuple[dict, int]:
    with get_connection() as conn:
        replay = _event_replay(conn, str(actor["id"]), idempotency_key, workflow_id, "send")
        if replay:
            return replay, 200
        workflow, _enrollment = _authorized_workflow(conn, actor, workflow_id)
        _check_expected_version(workflow, payload.get("expected_version"))
        if workflow["status"] != "confirmed":
            raise ResearchDeliveryError("delivery_not_confirmed", "请先预览并确认内容，再执行发送。", 409)
        delivery_version = _active_version(conn, workflow)
        if not delivery_version:
            raise ResearchDeliveryError("delivery_version_missing", "没有找到已确认的内容版本。", 409)
        report_id = None
        message_type = "researcher_message"
        source_type = "research_delivery_version"
        source_id = delivery_version["id"]
        if workflow["delivery_type"] == "stage_feedback":
            report_id = _create_stage_report(conn, actor, workflow, delivery_version)
            message_type = "relationship_stage_feedback"
            source_type = "relationship_screening_report"
            source_id = report_id
        message = create_message(
            conn,
            workflow["user_id"],
            workflow["title"],
            _render_content(workflow["delivery_type"], delivery_version["content"]),
            message_type,
            source_type,
            source_id,
            sender_id=str(actor["id"]),
            sender_role=str(actor.get("role") or "researcher"),
            idempotency_key=f"research-delivery:{workflow_id}:v{delivery_version['version_no']}",
            delivery_id=workflow_id,
            delivery_version=int(delivery_version["version_no"]),
        )
        timestamp = now_iso()
        next_version = int(workflow["version"]) + 1
        conn.execute(
            "UPDATE research_delivery_workflows SET status = 'sent', source_report_id = ?, message_id = ?, sent_at = ?, version = ?, updated_at = ? WHERE id = ? AND version = ?",
            (report_id, message["id"], timestamp, next_version, timestamp, workflow_id, workflow["version"]),
        )
        _record_event(conn, workflow, actor, "send", "confirmed", "sent", idempotency_key, {"message_id": message["id"], "report_id": report_id, "delivery_version": delivery_version["version_no"]})
        write_audit_log(conn, "research_delivery_sent", actor["id"], "research_delivery_workflow", workflow_id, {"message_id": message["id"], "report_id": report_id, "recipient_user_id": workflow["user_id"], "delivery_version": delivery_version["version_no"]})
        conn.commit()
        result = get_workflow_in_connection(conn, workflow_id)
        result["report_id"] = report_id
        return result, 201


def withdraw_delivery(actor: dict, workflow_id: str, payload: dict, idempotency_key: str) -> dict:
    reason = str(payload.get("reason") or "").strip()
    if not reason or len(reason) > 500:
        raise ResearchDeliveryError("validation_error", "撤回时需要填写1至500个字符的原因。")
    with get_connection() as conn:
        replay = _event_replay(conn, str(actor["id"]), idempotency_key, workflow_id, "withdraw")
        if replay:
            return replay
        workflow, _enrollment = _authorized_workflow(conn, actor, workflow_id, require_active_enrollment=False)
        _check_expected_version(workflow, payload.get("expected_version"))
        if workflow["status"] != "sent":
            raise ResearchDeliveryError("delivery_not_sent", "只有已发送内容可以撤回。", 409)
        timestamp = now_iso()
        conn.execute("UPDATE messages SET status = 'withdrawn', withdrawn_at = ? WHERE id = ?", (timestamp, workflow["message_id"]))
        if workflow.get("source_report_id"):
            conn.execute("UPDATE relationship_screening_reports SET status = 'withdrawn', updated_at = ? WHERE id = ?", (timestamp, workflow["source_report_id"]))
        next_version = int(workflow["version"]) + 1
        conn.execute(
            "UPDATE research_delivery_workflows SET status = 'withdrawn', withdrawn_at = ?, version = ?, updated_at = ? WHERE id = ? AND version = ?",
            (timestamp, next_version, timestamp, workflow_id, workflow["version"]),
        )
        _record_event(conn, workflow, actor, "withdraw", "sent", "withdrawn", idempotency_key, {"reason": reason[:120]})
        write_audit_log(conn, "research_delivery_withdrawn", actor["id"], "research_delivery_workflow", workflow_id, {"message_id": workflow["message_id"], "reason_length": len(reason)})
        conn.commit()
        return get_workflow_in_connection(conn, workflow_id)
