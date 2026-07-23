"""Role-scoped participant matrix and read-only multi-module dossier."""

from __future__ import annotations

from flask import Blueprint, current_app, request

from database import get_connection, now_iso, rows_to_dicts, write_audit_log
from routes.auth_utils import AuthError, auth_error_response, require_role
from routes.utils import fail, ok, parse_int
from services.research_queue_service import list_research_queue, sync_all_work_item_sources
from services.research_delivery_service import (
    ResearchDeliveryError,
    confirm_delivery,
    create_delivery,
    get_delivery,
    list_deliveries,
    preview_delivery,
    save_draft,
    send_delivery,
    withdraw_delivery,
)
from services.research_work_item_service import WorkItemError, get_work_item_detail, get_work_item_metrics, perform_work_item_action
from services.research_participant_service import anonymous_id, list_module, participant_summary


bp = Blueprint("research_workspace", __name__, url_prefix="/api/research")


def _actor():
    try:
        return require_role("researcher", "supervisor", "admin", allow_legacy_admin=True), None
    except AuthError as exc:
        return None, auth_error_response(exc)


def _delivery_error(exc: ResearchDeliveryError):
    return fail(exc.code, str(exc), status=exc.status)


def _idempotency_key(payload: dict) -> str:
    return str(request.headers.get("Idempotency-Key") or payload.get("idempotency_key") or "").strip()


@bp.get("/deliveries")
def get_research_deliveries():
    actor, error = _actor()
    if error:
        return error
    enrollment_id = str(request.args.get("enrollment_id") or "").strip()
    page = parse_int(request.args.get("page"), 1) or 1
    page_size = parse_int(request.args.get("page_size"), 20) or 20
    if not enrollment_id:
        return fail("validation_error", "请选择参与者。", status=400)
    if page < 1 or page_size < 1 or page_size > 100:
        return fail("validation_error", "page 需大于等于1，page_size 需为1至100。", status=400)
    try:
        return ok(list_deliveries(actor, enrollment_id, page, page_size))
    except ResearchDeliveryError as exc:
        return _delivery_error(exc)


@bp.post("/deliveries")
def create_research_delivery():
    actor, error = _actor()
    if error:
        return error
    payload = request.get_json(silent=True) or {}
    try:
        data, status = create_delivery(actor, payload, _idempotency_key(payload))
        return ok(data, status=status)
    except ResearchDeliveryError as exc:
        return _delivery_error(exc)


@bp.get("/deliveries/<workflow_id>")
def get_research_delivery(workflow_id: str):
    actor, error = _actor()
    if error:
        return error
    try:
        return ok(get_delivery(actor, workflow_id))
    except ResearchDeliveryError as exc:
        return _delivery_error(exc)


@bp.patch("/deliveries/<workflow_id>")
def update_research_delivery(workflow_id: str):
    actor, error = _actor()
    if error:
        return error
    payload = request.get_json(silent=True) or {}
    try:
        return ok(save_draft(actor, workflow_id, payload, _idempotency_key(payload)))
    except ResearchDeliveryError as exc:
        return _delivery_error(exc)


def _delivery_action(workflow_id: str, action):
    actor, error = _actor()
    if error:
        return error
    payload = request.get_json(silent=True) or {}
    try:
        result = action(actor, workflow_id, payload, _idempotency_key(payload))
        if isinstance(result, tuple):
            data, status = result
            return ok(data, status=status)
        return ok(result)
    except ResearchDeliveryError as exc:
        return _delivery_error(exc)


@bp.post("/deliveries/<workflow_id>/preview")
def preview_research_delivery(workflow_id: str):
    return _delivery_action(workflow_id, preview_delivery)


@bp.post("/deliveries/<workflow_id>/confirm")
def confirm_research_delivery(workflow_id: str):
    return _delivery_action(workflow_id, confirm_delivery)


@bp.post("/deliveries/<workflow_id>/send")
def send_research_delivery(workflow_id: str):
    return _delivery_action(workflow_id, send_delivery)


@bp.post("/deliveries/<workflow_id>/withdraw")
def withdraw_research_delivery(workflow_id: str):
    return _delivery_action(workflow_id, withdraw_delivery)


def _allowed_user_clause(actor: dict, alias: str = "u") -> tuple[str, list[str]]:
    consent_clause = f"""NOT EXISTS (
        SELECT 1 FROM consent_records consent_latest
        WHERE consent_latest.user_id = {alias}.id
          AND consent_latest.consent_type IN ('anonymous_research', 'research_authorization')
          AND consent_latest.created_at = (
              SELECT MAX(consent_inner.created_at) FROM consent_records consent_inner
              WHERE consent_inner.user_id = consent_latest.user_id
                AND consent_inner.consent_type = consent_latest.consent_type
          )
          AND consent_latest.agreed = 0
    )"""
    if actor.get("role") != "researcher":
        return consent_clause, []
    return (
        f"""EXISTS (
            SELECT 1 FROM relationship_pilot_enrollments access_e
            WHERE access_e.user_id = {alias}.id AND access_e.assigned_researcher_id = ?
              AND access_e.status NOT IN ('withdrawn', 'deleted')
        ) AND ({consent_clause})""",
        [str(actor["id"])],
    )


def _scoped_user_column(actor: dict, column: str) -> tuple[str, list[str]]:
    if actor.get("role") != "researcher":
        return "1 = 1", []
    return (
        f"{column} IN (SELECT user_id FROM relationship_pilot_enrollments WHERE assigned_researcher_id = ?)",
        [str(actor["id"])],
    )


def _research_authorized_column(column: str) -> str:
    return f"""NOT EXISTS (
        SELECT 1 FROM consent_records consent_latest
        WHERE consent_latest.user_id = {column}
          AND consent_latest.consent_type IN ('anonymous_research', 'research_authorization')
          AND consent_latest.created_at = (
              SELECT MAX(consent_inner.created_at) FROM consent_records consent_inner
              WHERE consent_inner.user_id = consent_latest.user_id
                AND consent_inner.consent_type = consent_latest.consent_type
          )
          AND consent_latest.agreed = 0
    )"""


def _status_counts(conn, table: str, scope_clause: str, params: list[str]) -> dict[str, int]:
    rows = conn.execute(
        f"SELECT status, COUNT(*) AS count FROM {table} WHERE {scope_clause} GROUP BY status",
        tuple(params),
    ).fetchall()
    return {str(row["status"]): int(row["count"]) for row in rows}


@bp.get("/participants")
def list_participants():
    actor, error = _actor()
    if error:
        return error
    query = str(request.args.get("q") or "").strip().lower()
    page = parse_int(request.args.get("page"), 1)
    legacy_limit = parse_int(request.args.get("limit"), 50)
    page_size = parse_int(request.args.get("page_size"), legacy_limit)
    page = 1 if page is None else page
    legacy_limit = 50 if legacy_limit is None else legacy_limit
    page_size = legacy_limit if page_size is None else page_size
    if page < 1 or page_size < 1 or page_size > 100:
        return fail("validation_error", "page 需大于等于1，page_size 需为1至100。", status=400)
    allowed_clause, params = _allowed_user_clause(actor)
    search_clause = ""
    if query:
        search_clause = "AND (LOWER(u.id) LIKE ? OR LOWER(COALESCE(u.nickname, '')) LIKE ?)"
        params.extend([f"%{query}%", f"%{query}%"])
    participant_clause = f"""
        u.role IN ('parent', 'student', 'user')
        AND COALESCE(u.status, 'active') != 'deleted'
        AND ({allowed_clause})
        {search_clause}
        AND (
            EXISTS (SELECT 1 FROM assessment_results a WHERE a.user_id = u.id)
            OR EXISTS (SELECT 1 FROM emotion_diaries d WHERE d.user_id = u.id)
            OR EXISTS (SELECT 1 FROM checkins c WHERE c.user_id = u.id)
            OR EXISTS (SELECT 1 FROM records r WHERE r.user_id = u.id AND r.module_type = 'program_entry')
            OR EXISTS (SELECT 1 FROM relationship_pilot_enrollments e WHERE e.user_id = u.id)
            OR EXISTS (SELECT 1 FROM supervision_requests s WHERE s.user_id = u.id)
        )
    """
    offset = (page - 1) * page_size
    with get_connection() as conn:
        total = int(
            conn.execute(
                f"SELECT COUNT(*) AS count FROM users u WHERE {participant_clause}",
                tuple(params),
            ).fetchone()["count"]
        )
        rows = conn.execute(
            f"""
            SELECT
                u.id AS user_id,
                u.nickname,
                u.role,
                u.updated_at AS last_activity_at,
                (SELECT COUNT(*) FROM assessment_results a WHERE a.user_id = u.id) AS assessment_count,
                (SELECT COUNT(*) FROM emotion_diaries d WHERE d.user_id = u.id) AS diary_count,
                (SELECT COUNT(*) FROM checkins c WHERE c.user_id = u.id) AS checkin_count,
                (SELECT COUNT(*) FROM records r WHERE r.user_id = u.id AND r.module_type = 'program_entry') AS program_count,
                (SELECT COUNT(*) FROM relationship_pilot_enrollments e WHERE e.user_id = u.id) AS relationship_count,
                (SELECT COUNT(*) FROM supervision_requests s WHERE s.user_id = u.id) AS supervision_count,
                (SELECT COUNT(*) FROM messages m WHERE m.user_id = u.id AND m.status = 'unread') AS unread_message_count
            FROM users u
            WHERE {participant_clause}
            ORDER BY u.updated_at DESC, u.id ASC
            LIMIT ? OFFSET ?
            """,
            tuple([*params, page_size, offset]),
        ).fetchall()
        write_audit_log(
            conn,
            "research_participant_matrix_viewed",
            actor["id"],
            "research_participant_matrix",
            "filtered" if query else "all",
            {"result_count": len(rows), "query_used": bool(query), "page": page, "page_size": page_size},
        )
        conn.commit()
    items = rows_to_dicts(rows)
    for item in items:
        item["anonymous_id"] = anonymous_id(str(item["user_id"]))
    return ok(
        {
            "items": items,
            "count": len(rows),
            "total": total,
            "page": page,
            "page_size": page_size,
            "has_more": offset + len(rows) < total,
            "scope": "assigned_participants" if actor.get("role") == "researcher" else "all_participants",
            "boundary_notice": "研究者仅查看获授权范围内的参与者资料；敏感详情访问会写入审计日志。",
        }
    )


@bp.get("/participants/<user_id>")
def get_participant_dossier(user_id: str):
    actor, error = _actor()
    if error:
        return error
    allowed_clause, params = _allowed_user_clause(actor)
    with get_connection() as conn:
        user = conn.execute(
            f"SELECT id FROM users u WHERE u.id = ? AND COALESCE(u.status, 'active') != 'deleted' AND ({allowed_clause})",
            tuple([user_id, *params]),
        ).fetchone()
        if user is None:
            return fail("not_found", "没有找到可访问的参与者档案。", status=404)
        summary = participant_summary(conn, user_id)
        write_audit_log(
            conn,
            "research_participant_summary_viewed",
            actor["id"],
            "user",
            user_id,
            {"module_count": len(summary["modules"]), "raw_text_included": False},
        )
        conn.commit()
    return ok(summary)


@bp.get("/participants/<user_id>/modules/<module_key>")
def get_participant_module(user_id: str, module_key: str):
    actor, error = _actor()
    if error:
        return error
    page = parse_int(request.args.get("page"), 1)
    page_size = parse_int(request.args.get("page_size"), 20)
    page = 1 if page is None else page
    page_size = 20 if page_size is None else page_size
    if page < 1 or page_size < 1 or page_size > 100:
        return fail("validation_error", "page 需大于等于1，page_size 需为1至100。", status=400)
    allowed_clause, params = _allowed_user_clause(actor)
    with get_connection() as conn:
        user = conn.execute(
            f"SELECT id FROM users u WHERE u.id = ? AND COALESCE(u.status, 'active') != 'deleted' AND ({allowed_clause})",
            tuple([user_id, *params]),
        ).fetchone()
        if user is None:
            return fail("not_found", "没有找到可访问的参与者档案。", status=404)
        try:
            payload = list_module(
                conn,
                user_id,
                module_key,
                page=page,
                page_size=page_size,
                date_from=str(request.args.get("date_from") or "").strip(),
                date_to=str(request.args.get("date_to") or "").strip(),
                item_type=str(request.args.get("type") or "").strip(),
                status=str(request.args.get("status") or "").strip(),
                batch=str(request.args.get("batch") or "").strip(),
            )
        except KeyError:
            return fail("validation_error", "未知的参与者档案标签。", status=400)
        write_audit_log(
            conn,
            "research_participant_sensitive_module_viewed" if payload["sensitive"] else "research_participant_timeline_viewed",
            actor["id"],
            f"research_participant_{module_key}",
            user_id,
            {
                "module": module_key,
                "result_count": payload["count"],
                "page": page,
                "page_size": page_size,
                "filter_flags": {
                    "batch": bool(request.args.get("batch")),
                    "date": bool(request.args.get("date_from") or request.args.get("date_to")),
                    "type": bool(request.args.get("type")),
                    "status": bool(request.args.get("status")),
                },
            },
        )
        conn.commit()
    payload["boundary_notice"] = "仅按当前标签读取必要资料；联系方式、登录凭据和无关敏感字段不会返回。"
    return ok(payload)


@bp.get("/operations")
def get_research_operations():
    """Return role-scoped operational counts without participant secrets or raw text."""

    actor, error = _actor()
    if error:
        return error
    scope_clause, params = _scoped_user_column(actor, "user_id")
    timestamp = now_iso()
    with get_connection() as conn:
        preference_rows = conn.execute(
            f"SELECT consent_status, COUNT(*) AS count FROM notification_preferences WHERE {scope_clause} GROUP BY consent_status",
            tuple(params),
        ).fetchall()
        preference_counts = {str(row["consent_status"]): int(row["count"]) for row in preference_rows}
        delivery_counts = _status_counts(conn, "notification_deliveries", scope_clause, params)
        retry_count = conn.execute(
            f"""
            SELECT COUNT(*) AS count FROM notification_deliveries
            WHERE {scope_clause} AND status = 'failed' AND dead_lettered_at IS NULL
              AND attempt_count < max_attempts
              AND COALESCE(retry_category, CASE
                    WHEN error_code IN ('43101', 'user_refuse', 'subscription_refused') THEN 'reauthorization_required'
                    WHEN error_code IN ('40037', 'template_invalid', 'subscription_fields_invalid', 'subscription_fields_missing') THEN 'template_error'
                    WHEN error_code IN ('40003', 'invalid_openid', 'invalid_recipient') THEN 'permanent_failure'
                    ELSE 'retryable' END) = 'retryable'
            """,
            tuple(params),
        ).fetchone()["count"]
        exhausted_count = conn.execute(
            f"SELECT COUNT(*) AS count FROM notification_deliveries WHERE {scope_clause} AND status = 'failed' AND (dead_lettered_at IS NOT NULL OR attempt_count >= max_attempts)",
            tuple(params),
        ).fetchone()["count"]
        overdue_count = conn.execute(
            f"SELECT COUNT(*) AS count FROM notification_deliveries WHERE {scope_clause} AND status = 'pending' AND scheduled_for <= ?",
            tuple([*params, timestamp]),
        ).fetchone()["count"]
        failure_rows = conn.execute(
            f"""
            SELECT COALESCE(error_code, 'unknown') AS error_code,
                   COALESCE(retry_category, 'unclassified') AS retry_category,
                   COUNT(*) AS count
            FROM notification_deliveries
            WHERE {scope_clause} AND status = 'failed'
            GROUP BY COALESCE(error_code, 'unknown'), COALESCE(retry_category, 'unclassified')
            ORDER BY count DESC, error_code ASC
            LIMIT 8
            """,
            tuple(params),
        ).fetchall()
        stage_feedback_count = conn.execute(
            f"""
            SELECT COUNT(*) AS count FROM relationship_screening_reports
            WHERE {scope_clause} AND ({_research_authorized_column('user_id')})
              AND status IN ('pending_review', 'ready', 'confirmed', 'updated')
            """,
            tuple(params),
        ).fetchone()["count"]
        supervision_count = conn.execute(
            f"SELECT COUNT(*) AS count FROM supervision_requests WHERE {scope_clause} AND status = 'pending'",
            tuple(params),
        ).fetchone()["count"]
        risk_review_count = conn.execute(
            f"SELECT COUNT(*) AS count FROM risk_review_records WHERE {scope_clause} AND review_status IN ('pending', 'priority_review')",
            tuple(params),
        ).fetchone()["count"]
        privacy_request_count = 0
        if actor.get("role") in {"admin", "supervisor"}:
            privacy_request_count = conn.execute(
                "SELECT COUNT(*) AS count FROM privacy_requests WHERE status IN ('pending', 'processing')"
            ).fetchone()["count"]
        write_audit_log(
            conn,
            "research_operations_viewed",
            actor["id"],
            "research_operations",
            "assigned" if actor.get("role") == "researcher" else "all",
            {
                "notification_failed": delivery_counts.get("failed", 0),
                "stage_feedback_pending": int(stage_feedback_count),
                "supervision_pending": int(supervision_count),
            },
        )
        conn.commit()

    return ok(
        {
            "scope": "assigned_participants" if actor.get("role") == "researcher" else "all_participants",
            "generated_at": timestamp,
            "notification_preferences": {
                "accepted": preference_counts.get("accepted", 0),
                "rejected": preference_counts.get("rejected", 0),
                "consumed": preference_counts.get("consumed", 0),
                "unknown": preference_counts.get("unknown", 0),
            },
            "notification_deliveries": {
                "pending": delivery_counts.get("pending", 0),
                "sending": delivery_counts.get("sending", 0),
                "sent": delivery_counts.get("sent", 0),
                "failed": delivery_counts.get("failed", 0),
                "retry_queue": int(retry_count),
                "exhausted": int(exhausted_count),
                "overdue": int(overdue_count),
            },
            "failure_reasons": [
                {"error_code": str(row["error_code"]), "retry_category": str(row["retry_category"]), "count": int(row["count"])} for row in failure_rows
            ],
            "backlog": {
                "stage_feedback": int(stage_feedback_count),
                "supervision": int(supervision_count),
                "risk_review": int(risk_review_count),
                "privacy_requests": int(privacy_request_count),
            },
            "privacy_management_available": actor.get("role") in {"admin", "supervisor"},
            "boundary_notice": "仅展示脱敏数量和错误代码，不返回 OpenID、模板密钥、联系方式或填写原文。",
        }
    )


@bp.get("/queues")
def get_research_queue():
    """Thin adapter for the role-scoped queue domain service."""

    actor, error = _actor()
    if error:
        return error
    page = parse_int(request.args.get("page"), 1) or 1
    page_size = parse_int(request.args.get("page_size"), 20) or 20
    if page < 1 or page_size < 1 or page_size > 100:
        return fail("validation_error", "page 需大于等于1，page_size 需为1至100。", status=400)
    try:
        return ok(
            list_research_queue(
                actor,
                queue_name=str(request.args.get("queue") or "").strip(),
                page=page,
                page_size=page_size,
                requested_status=str(request.args.get("status") or "active").strip(),
            )
        )
    except WorkItemError as exc:
        return fail(exc.code, str(exc), status=exc.status)


@bp.post("/work-items/<work_item_id>/actions")
def act_on_research_work_item(work_item_id: str):
    actor, error = _actor()
    if error:
        return error
    if not bool(current_app.config.get("RESEARCH_OPERATIONS_WRITE_ENABLED", False)):
        return fail("operations_write_disabled", "研究运营写操作尚未启用。", status=503)
    payload = request.get_json(silent=True) or {}
    action = str(payload.get("action") or "").strip()
    idempotency_key = str(request.headers.get("Idempotency-Key") or payload.get("idempotency_key") or "").strip()
    expected_version = parse_int(payload.get("expected_version"), None)
    if expected_version is None or expected_version < 0:
        return fail("validation_error", "expected_version 必须是非负整数。", status=400)
    try:
        with get_connection() as conn:
            result = perform_work_item_action(
                conn,
                work_item_id,
                actor,
                action=action,
                expected_version=expected_version,
                idempotency_key=idempotency_key,
                payload=payload,
            )
            conn.commit()
    except WorkItemError as exc:
        return fail(exc.code, str(exc), status=exc.status)
    return ok(result)


@bp.get("/work-items/<work_item_id>")
def get_research_work_item(work_item_id: str):
    actor, error = _actor()
    if error:
        return error
    try:
        with get_connection() as conn:
            detail = get_work_item_detail(conn, work_item_id, actor)
            write_audit_log(
                conn,
                "research_work_item_viewed",
                actor["id"],
                "research_work_item",
                work_item_id,
                {"queue_type": detail["work_item"]["queue_type"]},
            )
            conn.commit()
    except WorkItemError as exc:
        return fail(exc.code, str(exc), status=exc.status)
    return ok(detail)


@bp.get("/work-items/metrics")
def get_research_work_item_metric_snapshot():
    actor, error = _actor()
    if error:
        return error
    window_days = parse_int(request.args.get("window_days"), 7) or 7
    if window_days < 1 or window_days > 90:
        return fail("validation_error", "window_days 需为1至90。", status=400)
    with get_connection() as conn:
        sync_truncation = sync_all_work_item_sources(conn, actor)
        metrics = get_work_item_metrics(conn, actor, window_days)
        metrics["sync_truncation"] = sync_truncation
        write_audit_log(
            conn,
            "research_work_item_metrics_viewed",
            actor["id"],
            "research_work_item_metrics",
            metrics["scope"],
            {"window_days": window_days},
        )
        conn.commit()
    return ok(metrics)
