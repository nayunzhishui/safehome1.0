"""Research queue source adapters and paginated work-item projection."""

from __future__ import annotations

from datetime import datetime, timezone

from database import get_connection, rows_to_dicts, write_audit_log
from services.research_work_item_service import WORK_ITEM_STATUSES, WorkItemError, ensure_work_item, reconcile_resolved_work_items


QUEUE_CONFIG = {
    "notification_failed": {"table": "notification_deliveries", "where": "status = 'failed'", "status_column": "status", "title": "订阅消息发送失败", "extra": "error_code, attempt_count, retry_category, next_attempt_at, max_attempts, dead_lettered_at"},
    "stage_feedback": {"table": "relationship_screening_reports", "where": "status IN ('pending_review', 'ready', 'confirmed', 'updated')", "status_column": "status", "title": "阶段性反馈待处理", "extra": "enrollment_id", "requires_research_authorization": True},
    "supervision": {"table": "supervision_requests", "where": "status = 'pending'", "status_column": "status", "title": "人工支持待处理", "extra": "source_type, source_id, risk_level"},
    "risk_review": {"table": "risk_review_records", "where": "review_status IN ('pending', 'priority_review')", "status_column": "review_status", "title": "风险信号待复核", "extra": "source_type, source_id, risk_level"},
    "feedback_review": {"table": "feedback_ledger", "where": "review_status = 'pending_review' AND status = 'active'", "status_column": "review_status", "title": "参与者不适反馈待复核", "extra": "source_type, source_id, evaluation", "requires_research_authorization": True},
    "privacy_request": {"table": "privacy_requests", "where": "status IN ('pending', 'processing')", "status_column": "status", "title": "隐私申请待处理", "extra": "request_type, version", "roles": {"supervisor", "admin"}},
}
ACTIVE_WORK_ITEM_STATUSES = {"open", "claimed", "processing", "waiting", "dead_letter"}


def _wait_minutes(created_at: object) -> int:
    try:
        created = datetime.fromisoformat(str(created_at).replace("Z", "+00:00"))
        if created.tzinfo is None:
            created = created.replace(tzinfo=timezone.utc)
        return max(0, int((datetime.now(timezone.utc) - created).total_seconds() // 60))
    except (TypeError, ValueError):
        return 0


def _scoped_user_column(actor: dict, column: str) -> tuple[str, list[str]]:
    if actor.get("role") != "researcher":
        return "1 = 1", []
    return f"{column} IN (SELECT user_id FROM relationship_pilot_enrollments WHERE assigned_researcher_id = ?)", [str(actor["id"])]


def _research_authorized_column(column: str) -> str:
    return f"""NOT EXISTS (
        SELECT 1 FROM consent_records consent_latest
        WHERE consent_latest.user_id = {column}
          AND consent_latest.consent_type IN ('anonymous_research', 'research_authorization')
          AND consent_latest.created_at = (
              SELECT MAX(consent_inner.created_at) FROM consent_records consent_inner
              WHERE consent_inner.user_id = consent_latest.user_id
                AND consent_inner.consent_type = consent_latest.consent_type
          ) AND consent_latest.agreed = 0
    )"""


def sync_all_work_item_sources(conn, actor: dict) -> dict[str, bool]:
    truncation: dict[str, bool] = {}
    for queue_name, config in QUEUE_CONFIG.items():
        if config.get("roles") and actor.get("role") not in config["roles"]:
            continue
        scope_clause, params = _scoped_user_column(actor, "user_id")
        where = f"({scope_clause}) AND ({config['where']})"
        if config.get("requires_research_authorization"):
            where += f" AND ({_research_authorized_column('user_id')})"
        rows = conn.execute(f"SELECT id, user_id, {config['status_column']} AS status, created_at, {config['extra']} FROM {config['table']} WHERE {where} ORDER BY created_at ASC, id ASC LIMIT 5001", tuple(params)).fetchall()
        sources = rows_to_dicts(rows[:5000])
        truncation[queue_name] = len(rows) > 5000
        for source in sources:
            ensure_work_item(conn, queue_name, config["table"], source)
        if not truncation[queue_name]:
            reconcile_resolved_work_items(conn, queue_name, actor, [str(source["id"]) for source in sources])
    return truncation


def list_research_queue(actor: dict, *, queue_name: str, page: int, page_size: int, requested_status: str) -> dict:
    config = QUEUE_CONFIG.get(queue_name)
    if config is None:
        raise WorkItemError("validation_error", "不支持的队列类型。", 400)
    if config.get("roles") and actor.get("role") not in config["roles"]:
        raise WorkItemError("forbidden", "当前角色不能查看该队列。", 403)
    offset = (page - 1) * page_size
    scope_clause, params = _scoped_user_column(actor, "user_id")
    where = f"({scope_clause}) AND ({config['where']})"
    if config.get("requires_research_authorization"):
        where += f" AND ({_research_authorized_column('user_id')})"
    with get_connection() as conn:
        source_rows = conn.execute(f"SELECT id, user_id, {config['status_column']} AS status, created_at, {config['extra']} FROM {config['table']} WHERE {where} ORDER BY created_at ASC, id ASC LIMIT 5001", tuple(params)).fetchall()
        sync_truncated = len(source_rows) > 5000
        sources = rows_to_dicts(source_rows[:5000])
        source_by_id = {str(source["id"]): source for source in sources}
        work_item_ids = [ensure_work_item(conn, queue_name, config["table"], source)["id"] for source in sources]
        if not sync_truncated:
            reconcile_resolved_work_items(conn, queue_name, actor, list(source_by_id))
        item_where = ["queue_type = ?"]
        item_params: list = [queue_name]
        if actor.get("role") == "researcher":
            item_where.append("user_id IN (SELECT user_id FROM relationship_pilot_enrollments WHERE assigned_researcher_id = ?)")
            item_params.append(str(actor["id"]))
        if requested_status == "active":
            placeholders = ",".join("?" for _ in ACTIVE_WORK_ITEM_STATUSES)
            item_where.append(f"status IN ({placeholders})")
            item_params.extend(sorted(ACTIVE_WORK_ITEM_STATUSES))
        elif requested_status != "all":
            if requested_status not in WORK_ITEM_STATUSES:
                raise WorkItemError("validation_error", "工作项状态不在允许范围内。", 400)
            item_where.append("status = ?")
            item_params.append(requested_status)
        if work_item_ids:
            placeholders = ",".join("?" for _ in work_item_ids)
            item_where.append(f"id IN ({placeholders})")
            item_params.extend(work_item_ids)
        else:
            item_where.append("1 = 0")
        total_row = conn.execute(f"SELECT COUNT(*) AS count FROM research_work_items WHERE {' AND '.join(item_where)}", tuple(item_params)).fetchone()
        work_rows = conn.execute(f"SELECT * FROM research_work_items WHERE {' AND '.join(item_where)} ORDER BY CASE priority WHEN 'urgent' THEN 0 WHEN 'attention' THEN 1 ELSE 2 END, created_at ASC, id ASC LIMIT ? OFFSET ?", tuple([*item_params, page_size, offset])).fetchall()
        items = []
        for work_item in rows_to_dicts(work_rows):
            source = source_by_id.get(str(work_item["source_id"]), {})
            safe_source = {key: value for key, value in source.items() if key not in {"id", "user_id", "status", "created_at", "error_message"}}
            items.append({**safe_source, "id": work_item["id"], "work_item_id": work_item["id"], "user_id": work_item["user_id"], "source_record_id": work_item["source_id"], "source_type": work_item["source_type"], "source_id": work_item["source_id"], "priority": work_item["priority"], "status": work_item["status"], "assignee_id": work_item.get("assignee_id"), "lease_expires_at": work_item.get("lease_expires_at"), "due_at": work_item.get("due_at"), "version": int(work_item.get("version") or 0), "resolution_code": work_item.get("resolution_code"), "created_at": work_item["created_at"]})
        write_audit_log(conn, "research_queue_viewed", actor["id"], "research_queue", queue_name, {"page": page, "page_size": page_size})
        conn.commit()
    items = [{**item, "title": config["title"], "wait_minutes": _wait_minutes(item.get("created_at"))} for item in items]
    total = int(total_row["count"] if total_row else 0)
    return {"queue": queue_name, "items": items, "page": page, "page_size": page_size, "total": total, "has_more": offset + len(items) < total, "sync_truncated": sync_truncated, "scope": "assigned_participants" if actor.get("role") == "researcher" else "all_participants", "boundary_notice": "队列只返回必要状态和来源标识，不返回填写原文、消息正文或内部复核备注。"}
