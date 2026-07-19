"""Persistent, role-scoped operational work items for researcher workflows."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from database import json_dumps, new_id, now_iso, row_to_dict, write_audit_log


LEASE_MINUTES = 15
WORK_ITEM_STATUSES = {"open", "claimed", "processing", "waiting", "completed", "closed", "dead_letter"}
PRIORITIES = {"routine", "attention", "urgent"}


class WorkItemError(RuntimeError):
    def __init__(self, code: str, message: str, status: int = 400) -> None:
        super().__init__(message)
        self.code = code
        self.status = status


def _iso_after(minutes: int) -> str:
    return (datetime.now(timezone.utc) + timedelta(minutes=minutes)).isoformat()


def _priority_for(queue_type: str, source: dict) -> str:
    if queue_type == "risk_review" and source.get("risk_level") == "high":
        return "urgent"
    if queue_type in {"risk_review", "feedback_review", "notification_failed"}:
        return "attention"
    return "routine"


def ensure_work_item(conn, queue_type: str, source_type: str, source: dict) -> dict:
    """Create the operational shell once, without copying participant raw text."""

    existing = conn.execute(
        "SELECT * FROM research_work_items WHERE queue_type = ? AND source_type = ? AND source_id = ?",
        (queue_type, source_type, source["id"]),
    ).fetchone()
    if existing:
        return row_to_dict(existing) or {}
    timestamp = now_iso()
    work_item_id = new_id("work_item")
    initial_status = "dead_letter" if queue_type == "notification_failed" and source.get("dead_lettered_at") else "open"
    conn.execute(
        """
        INSERT INTO research_work_items (
            id, queue_type, source_type, source_id, user_id, priority, status,
            assignee_id, lease_expires_at, due_at, version, resolution_code,
            closed_at, last_action_at, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, NULL, NULL, ?, 0, NULL, NULL, NULL, ?, ?)
        """,
        (
            work_item_id,
            queue_type,
            source_type,
            source["id"],
            source["user_id"],
            _priority_for(queue_type, source),
            initial_status,
            source.get("due_at") or source.get("scheduled_for"),
            source.get("created_at") or timestamp,
            timestamp,
        ),
    )
    return row_to_dict(conn.execute("SELECT * FROM research_work_items WHERE id = ?", (work_item_id,)).fetchone()) or {}


def _load_accessible(conn, work_item_id: str, actor: dict) -> dict:
    row = conn.execute("SELECT * FROM research_work_items WHERE id = ?", (work_item_id,)).fetchone()
    item = row_to_dict(row)
    if not item:
        raise WorkItemError("not_found", "没有找到该工作项。", 404)
    role = str(actor.get("role") or "")
    if role == "researcher":
        assigned = conn.execute(
            """
            SELECT 1 FROM relationship_pilot_enrollments
            WHERE user_id = ? AND assigned_researcher_id = ? LIMIT 1
            """,
            (item["user_id"], actor["id"]),
        ).fetchone()
        if not assigned:
            raise WorkItemError("forbidden", "该工作项不在你的参与者范围内。", 403)
    elif role not in {"supervisor", "admin"}:
        raise WorkItemError("forbidden", "当前角色不能处理研究运营工作项。", 403)
    return item


def perform_work_item_action(
    conn,
    work_item_id: str,
    actor: dict,
    *,
    action: str,
    expected_version: int,
    idempotency_key: str,
    payload: dict | None = None,
) -> dict:
    payload = payload or {}
    if not idempotency_key or len(idempotency_key) > 120:
        raise WorkItemError("validation_error", "请提供不超过120字符的幂等键。", 400)
    previous = conn.execute(
        "SELECT work_item_id FROM research_work_item_actions WHERE actor_id = ? AND idempotency_key = ?",
        (actor["id"], idempotency_key),
    ).fetchone()
    if previous:
        if previous["work_item_id"] != work_item_id:
            raise WorkItemError("idempotency_conflict", "该幂等键已用于另一工作项。", 409)
        replay = _load_accessible(conn, work_item_id, actor)
        return {"work_item": replay, "already_processed": True}

    item = _load_accessible(conn, work_item_id, actor)
    if int(item.get("version") or 0) != expected_version:
        raise WorkItemError("work_item_conflict", "工作项已被其他处理人更新，请刷新后重试。", 409)
    now = now_iso()
    role = str(actor.get("role") or "")
    privileged = role in {"supervisor", "admin"}
    old_status = str(item["status"])
    new_status = old_status
    assignee_id = item.get("assignee_id")
    lease_expires_at = item.get("lease_expires_at")
    resolution_code = item.get("resolution_code")
    closed_at = item.get("closed_at")
    note_type = None
    note_content = ""
    message_id = None
    metadata: dict = {}

    if item["queue_type"] == "risk_review" and not privileged:
        raise WorkItemError("forbidden", "风险复核仅由督导或管理员处理。", 403)
    if item["queue_type"] == "privacy_request" and not privileged:
        raise WorkItemError("forbidden", "隐私申请仅由督导或管理员处理。", 403)

    if action == "claim":
        if assignee_id and lease_expires_at and str(lease_expires_at) > now and assignee_id != actor["id"]:
            raise WorkItemError("work_item_claimed", "该工作项已由其他处理人领取。", 409)
        if old_status in {"completed", "closed", "dead_letter"}:
            raise WorkItemError("invalid_work_item_transition", "当前状态不能领取。", 409)
        new_status = "claimed"
        assignee_id = actor["id"]
        lease_expires_at = _iso_after(LEASE_MINUTES)
    elif action == "renew":
        if assignee_id != actor["id"] and not privileged:
            raise WorkItemError("forbidden", "只能续租自己领取的工作项。", 403)
        if old_status not in {"claimed", "processing", "waiting"}:
            raise WorkItemError("invalid_work_item_transition", "当前状态不能续租。", 409)
        assignee_id = assignee_id or actor["id"]
        lease_expires_at = _iso_after(LEASE_MINUTES)
    elif action == "return":
        if assignee_id != actor["id"] and not privileged:
            raise WorkItemError("forbidden", "只能退回自己领取的工作项。", 403)
        if old_status not in {"claimed", "processing", "waiting"}:
            raise WorkItemError("invalid_work_item_transition", "当前状态不能退回。", 409)
        new_status = "open"
        assignee_id = None
        lease_expires_at = None
    elif action == "transfer":
        if not privileged:
            raise WorkItemError("forbidden", "转交工作项需要督导或管理员权限。", 403)
        target = str(payload.get("assignee_id") or "").strip()
        target_row = conn.execute("SELECT id, role, status FROM users WHERE id = ?", (target,)).fetchone()
        if not target_row or target_row["status"] != "active" or target_row["role"] not in {"researcher", "supervisor", "admin"}:
            raise WorkItemError("validation_error", "请选择有效的研究处理人员。", 400)
        if target_row["role"] == "researcher":
            assigned = conn.execute(
                "SELECT 1 FROM relationship_pilot_enrollments WHERE user_id = ? AND assigned_researcher_id = ? LIMIT 1",
                (item["user_id"], target),
            ).fetchone()
            if not assigned:
                raise WorkItemError("forbidden", "目标研究者未获该参与者授权。", 403)
        new_status = "claimed"
        assignee_id = target
        lease_expires_at = _iso_after(LEASE_MINUTES)
        metadata["transferred_to"] = target
    elif action in {"start_processing", "wait"}:
        if assignee_id != actor["id"] and not privileged:
            raise WorkItemError("forbidden", "请先领取该工作项。", 403)
        if old_status not in {"claimed", "processing", "waiting"}:
            raise WorkItemError("invalid_work_item_transition", "当前状态不能进入处理流程。", 409)
        new_status = "processing" if action == "start_processing" else "waiting"
        lease_expires_at = _iso_after(LEASE_MINUTES)
    elif action == "add_note":
        if assignee_id != actor["id"] and not privileged:
            raise WorkItemError("forbidden", "请先领取该工作项再补充说明。", 403)
        note_content = str(payload.get("note") or "").strip()
        if not note_content or len(note_content) > 2000:
            raise WorkItemError("validation_error", "内部备注需为1至2000个字符。", 400)
        note_type = "internal"
    elif action == "send_participant_message":
        if item["queue_type"] not in {"stage_feedback", "supervision", "feedback_review"}:
            raise WorkItemError("invalid_work_item_transition", "该队列不能直接发送参与者消息。", 409)
        if assignee_id != actor["id"] and not privileged:
            raise WorkItemError("forbidden", "请先领取该工作项再发送消息。", 403)
        title = str(payload.get("title") or "").strip()
        body = str(payload.get("body") or "").strip()
        if not title or len(title) > 60 or not body or len(body) > 2000:
            raise WorkItemError("validation_error", "消息标题需为1至60字，正文需为1至2000字。", 400)
        from services.risk_service import check_text_risk

        risk = check_text_risk([title, body], source="research_work_item_message")
        if risk.get("risk_level") == "high" and not privileged:
            raise WorkItemError("message_requires_supervisor_review", "该消息需先由督导复核。", 409)
        from services.message_service import create_message

        message = create_message(
            conn,
            item["user_id"],
            title,
            body,
            "researcher_message",
            "research_work_item",
            work_item_id,
            sender_id=str(actor["id"]),
            sender_role=role,
            idempotency_key=idempotency_key,
        )
        message_id = message["id"]
        metadata["message_id"] = message_id
        metadata["risk_level"] = risk.get("risk_level")
    elif action in {"retry_notification", "recover_notification"}:
        if not privileged:
            raise WorkItemError("forbidden", "通知恢复需要督导或管理员权限。", 403)
        if item["queue_type"] != "notification_failed":
            raise WorkItemError("invalid_work_item_transition", "该动作只适用于通知失败工作项。", 409)
        delivery = conn.execute(
            """
            SELECT id, retry_category, error_code, attempt_count, max_attempts, dead_lettered_at
            FROM notification_deliveries WHERE id = ?
            """,
            (item["source_id"],),
        ).fetchone()
        if not delivery:
            raise WorkItemError("not_found", "没有找到对应通知投递记录。", 404)
        from services.notification_service import classify_notification_error

        category = str(delivery["retry_category"] or classify_notification_error(str(delivery["error_code"] or "")))
        if action == "retry_notification":
            error_by_category = {
                "reauthorization_required": ("notification_reauthorization_required", "需要参与者重新授权，不能自动重试。"),
                "template_error": ("notification_template_error", "订阅模板配置错误，修复配置后再恢复。"),
                "permanent_failure": ("notification_permanent_failure", "该失败不可自动重试。"),
            }
            if category in error_by_category:
                code, message = error_by_category[category]
                raise WorkItemError(code, message, 409)
            if delivery["dead_lettered_at"] or int(delivery["attempt_count"] or 0) >= int(delivery["max_attempts"] or 3):
                raise WorkItemError("notification_dead_letter", "重试次数已用尽，请执行人工恢复。", 409)
            conn.execute(
                """
                UPDATE notification_deliveries
                SET retry_category = 'retryable', next_attempt_at = ?, updated_at = ?
                WHERE id = ?
                """,
                (now, now, item["source_id"]),
            )
        else:
            if not delivery["dead_lettered_at"] and int(delivery["attempt_count"] or 0) < int(delivery["max_attempts"] or 3):
                raise WorkItemError("invalid_work_item_transition", "该通知尚未进入死信，无需人工恢复。", 409)
            note_content = str(payload.get("note") or "").strip()
            if not note_content or len(note_content) > 2000:
                raise WorkItemError("validation_error", "人工恢复时需填写1至2000字说明。", 400)
            note_type = "handling"
            conn.execute(
                """
                UPDATE notification_deliveries
                SET status = 'failed', attempt_count = 0, retry_category = 'retryable',
                    next_attempt_at = ?, dead_lettered_at = NULL, updated_at = ?
                WHERE id = ?
                """,
                (now, now, item["source_id"]),
            )
        new_status = "open"
        assignee_id = None
        lease_expires_at = None
        resolution_code = None
        closed_at = None
        metadata["retry_category"] = "retryable"
    elif action == "complete":
        if assignee_id != actor["id"] and not privileged:
            raise WorkItemError("forbidden", "只能完成自己领取的工作项。", 403)
        if old_status not in {"claimed", "processing", "waiting"}:
            raise WorkItemError("invalid_work_item_transition", "当前状态不能标记完成。", 409)
        resolution_code = str(payload.get("resolution_code") or "").strip()
        if not resolution_code or len(resolution_code) > 80:
            raise WorkItemError("validation_error", "完成工作项时需填写有效的处理结果代码。", 400)
        new_status = "completed"
        lease_expires_at = None
        note_content = str(payload.get("note") or "").strip()
        if len(note_content) > 2000:
            raise WorkItemError("validation_error", "处理说明不能超过2000个字符。", 400)
        note_type = "handling" if note_content else None
        metadata["resolution_code"] = resolution_code
    elif action == "close":
        if not privileged:
            raise WorkItemError("forbidden", "关闭工作项需要督导或管理员权限。", 403)
        if old_status != "completed":
            raise WorkItemError("invalid_work_item_transition", "只有已完成工作项可以关闭。", 409)
        resolution_code = str(payload.get("resolution_code") or resolution_code or "").strip()
        if not resolution_code or len(resolution_code) > 80:
            raise WorkItemError("validation_error", "关闭工作项时需填写关闭原因代码。", 400)
        new_status = "closed"
        closed_at = now
        assignee_id = None
        lease_expires_at = None
        note_content = str(payload.get("note") or "").strip()
        if len(note_content) > 2000:
            raise WorkItemError("validation_error", "关闭说明不能超过2000个字符。", 400)
        note_type = "handling" if note_content else None
        metadata["resolution_code"] = resolution_code
    elif action == "reopen":
        if not privileged:
            raise WorkItemError("forbidden", "重新打开工作项需要督导或管理员权限。", 403)
        if old_status not in {"completed", "closed"}:
            raise WorkItemError("invalid_work_item_transition", "当前状态不能重新打开。", 409)
        new_status = "open"
        assignee_id = None
        lease_expires_at = None
        resolution_code = None
        closed_at = None
        note_content = str(payload.get("note") or "").strip()
        if not note_content or len(note_content) > 2000:
            raise WorkItemError("validation_error", "重新打开时需填写1至2000字原因。", 400)
        note_type = "handling"
    else:
        raise WorkItemError("unsupported_action", "不支持的工作项动作。", 400)

    cursor = conn.execute(
        """
        UPDATE research_work_items
        SET status = ?, assignee_id = ?, lease_expires_at = ?, resolution_code = ?,
            closed_at = ?, last_action_at = ?, updated_at = ?, version = version + 1
        WHERE id = ? AND version = ?
        """,
        (
            new_status, assignee_id, lease_expires_at, resolution_code, closed_at,
            now, now, work_item_id, expected_version,
        ),
    )
    if int(cursor.rowcount or 0) != 1:
        raise WorkItemError("work_item_conflict", "工作项已被其他处理人更新，请刷新后重试。", 409)
    updated = row_to_dict(conn.execute("SELECT * FROM research_work_items WHERE id = ?", (work_item_id,)).fetchone()) or {}
    if note_type:
        conn.execute(
            """
            INSERT INTO research_work_item_notes (id, work_item_id, actor_id, actor_role, note_type, content, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (new_id("work_note"), work_item_id, actor["id"], role, note_type, note_content, now),
        )
    conn.execute(
        """
        INSERT INTO research_work_item_actions (
            id, work_item_id, actor_id, actor_role, action, from_status, to_status,
            metadata_json, idempotency_key, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            new_id("work_action"), work_item_id, actor["id"], actor.get("role") or "researcher",
            action, item["status"], updated["status"], json_dumps({**metadata, "version": updated["version"]}),
            idempotency_key, now,
        ),
    )
    write_audit_log(
        conn,
        "research_work_item_action",
        actor["id"],
        "research_work_item",
        work_item_id,
        {"queue_type": item["queue_type"], "action": action, "from_status": item["status"], "to_status": updated["status"]},
    )
    result = {"work_item": updated, "already_processed": False}
    if message_id:
        result["message_id"] = message_id
    return result


def get_work_item_detail(conn, work_item_id: str, actor: dict) -> dict:
    item = _load_accessible(conn, work_item_id, actor)
    notes = [dict(row) for row in conn.execute(
        """
        SELECT id, actor_id, actor_role, note_type, content, created_at
        FROM research_work_item_notes WHERE work_item_id = ? ORDER BY created_at ASC, id ASC
        """,
        (work_item_id,),
    ).fetchall()]
    actions = [dict(row) for row in conn.execute(
        """
        SELECT id, actor_id, actor_role, action, from_status, to_status, created_at
        FROM research_work_item_actions WHERE work_item_id = ? ORDER BY created_at ASC, id ASC
        """,
        (work_item_id,),
    ).fetchall()]
    return {
        "work_item": item,
        "source": {
            "source_type": item["source_type"],
            "source_id": item["source_id"],
            "user_id": item["user_id"],
            "read_only": True,
        },
        "notes": notes,
        "actions": actions,
        "boundary_notice": "原始参与者内容保持只读；内部备注与参与者可见消息分开保存。",
    }


def get_work_item_metrics(conn, actor: dict, window_days: int = 7) -> dict:
    now = datetime.now(timezone.utc)
    start = (now - timedelta(days=window_days)).isoformat()
    scope = "1 = 1"
    params: list = []
    if actor.get("role") == "researcher":
        scope = "user_id IN (SELECT user_id FROM relationship_pilot_enrollments WHERE assigned_researcher_id = ?)"
        params.append(str(actor["id"]))
    status_rows = conn.execute(
        f"SELECT status, COUNT(*) AS count FROM research_work_items WHERE {scope} GROUP BY status",
        tuple(params),
    ).fetchall()
    totals = {status: 0 for status in sorted(WORK_ITEM_STATUSES)}
    for row in status_rows:
        totals[str(row["status"])] = int(row["count"])
    overdue = conn.execute(
        f"""
        SELECT COUNT(*) AS count FROM research_work_items
        WHERE {scope} AND status IN ('open', 'claimed', 'processing', 'waiting', 'dead_letter')
          AND due_at IS NOT NULL AND due_at <= ?
        """,
        tuple([*params, now.isoformat()]),
    ).fetchone()["count"]
    expired_leases = conn.execute(
        f"""
        SELECT COUNT(*) AS count FROM research_work_items
        WHERE {scope} AND status IN ('claimed', 'processing', 'waiting')
          AND lease_expires_at IS NOT NULL AND lease_expires_at <= ?
        """,
        tuple([*params, now.isoformat()]),
    ).fetchone()["count"]
    close_rows = conn.execute(
        f"""
        SELECT COALESCE(resolution_code, 'unspecified') AS resolution_code, COUNT(*) AS count
        FROM research_work_items WHERE {scope} AND status = 'closed'
        GROUP BY COALESCE(resolution_code, 'unspecified') ORDER BY count DESC, resolution_code ASC
        """,
        tuple(params),
    ).fetchall()
    opened_rows = conn.execute(
        f"""
        SELECT DATE(created_at) AS day, COUNT(*) AS count FROM research_work_items
        WHERE {scope} AND created_at >= ? GROUP BY DATE(created_at) ORDER BY day ASC
        """,
        tuple([*params, start]),
    ).fetchall()
    closed_rows = conn.execute(
        f"""
        SELECT DATE(closed_at) AS day, COUNT(*) AS count FROM research_work_items
        WHERE {scope} AND closed_at IS NOT NULL AND closed_at >= ?
        GROUP BY DATE(closed_at) ORDER BY day ASC
        """,
        tuple([*params, start]),
    ).fetchall()
    trend_by_day: dict[str, dict] = {}
    for row in opened_rows:
        trend_by_day[str(row["day"])] = {"day": str(row["day"]), "opened": int(row["count"]), "closed": 0}
    for row in closed_rows:
        trend_by_day.setdefault(str(row["day"]), {"day": str(row["day"]), "opened": 0, "closed": 0})["closed"] = int(row["count"])
    action_scope = "w.user_id IN (SELECT user_id FROM relationship_pilot_enrollments WHERE assigned_researcher_id = ?)" if actor.get("role") == "researcher" else "1 = 1"
    workload_rows = conn.execute(
        f"""
        SELECT a.actor_id, a.actor_role, a.action, COUNT(*) AS count
        FROM research_work_item_actions a
        JOIN research_work_items w ON w.id = a.work_item_id
        WHERE {action_scope} AND a.created_at >= ?
        GROUP BY a.actor_id, a.actor_role, a.action
        ORDER BY a.actor_id, a.action
        """,
        tuple([*params, start]),
    ).fetchall()
    return {
        "scope": "assigned_participants" if actor.get("role") == "researcher" else "all_participants",
        "generated_at": now.isoformat(),
        "window_days": window_days,
        "totals": totals,
        "sla": {"overdue": int(overdue), "expired_leases": int(expired_leases)},
        "close_reasons": [{"resolution_code": str(row["resolution_code"]), "count": int(row["count"])} for row in close_rows],
        "workload": [dict(row) for row in workload_rows],
        "trend": [trend_by_day[key] for key in sorted(trend_by_day)],
        "quality_boundary": "工作量和等待时间只用于安排运营，不用于评价心理支持质量或参与者变化。",
    }


def reconcile_resolved_work_items(conn, queue_type: str, actor: dict, active_source_ids: list[str]) -> int:
    """Close operational shells whose source adapter no longer reports pending work."""

    where = ["queue_type = ?", "status IN ('open', 'claimed', 'processing', 'waiting', 'dead_letter')"]
    params: list = [queue_type]
    if actor.get("role") == "researcher":
        where.append("user_id IN (SELECT user_id FROM relationship_pilot_enrollments WHERE assigned_researcher_id = ?)")
        params.append(str(actor["id"]))
    if active_source_ids:
        placeholders = ",".join("?" for _ in active_source_ids)
        where.append(f"source_id NOT IN ({placeholders})")
        params.extend(active_source_ids)
    rows = conn.execute(
        f"SELECT * FROM research_work_items WHERE {' AND '.join(where)}",
        tuple(params),
    ).fetchall()
    timestamp = now_iso()
    changed = 0
    for row in rows:
        item = row_to_dict(row) or {}
        cursor = conn.execute(
            """
            UPDATE research_work_items
            SET status = 'completed', assignee_id = NULL, lease_expires_at = NULL,
                resolution_code = 'source_resolved', last_action_at = ?, updated_at = ?, version = version + 1
            WHERE id = ? AND version = ?
            """,
            (timestamp, timestamp, item["id"], item["version"]),
        )
        if int(cursor.rowcount or 0) != 1:
            continue
        conn.execute(
            """
            INSERT INTO research_work_item_actions (
                id, work_item_id, actor_id, actor_role, action, from_status, to_status,
                metadata_json, idempotency_key, created_at
            ) VALUES (?, ?, 'system', 'system', 'complete', ?, 'completed', ?, ?, ?)
            """,
            (
                new_id("work_action"), item["id"], item["status"],
                json_dumps({"reason": "source_resolved"}),
                f"source_resolved:{item['id']}:{item['version']}", timestamp,
            ),
        )
        changed += 1
    if changed:
        write_audit_log(
            conn,
            "research_work_items_source_reconciled",
            "system",
            "research_work_item_queue",
            queue_type,
            {"completed_count": changed},
        )
    return changed
