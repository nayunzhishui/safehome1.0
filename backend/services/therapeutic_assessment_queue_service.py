"""Scoped human queue, duty coverage and fail-closed monitoring for Task37-B02."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

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
from services.therapeutic_assessment_competency_service import assert_task_authorized
from services.therapeutic_assessment_service import (
    FORMAL_ROLES,
    REVIEW_ROLES,
    TherapeuticAssessmentError,
    _case_row,
    _idempotency,
)


OPEN_STATUSES = {"open", "claimed", "handoff_required"}


def _policy() -> dict:
    return load_content_json("therapeutic_assessment_queue_policy.json")


def _parse_time(value: object, field: str) -> str:
    text = str(value or "").strip()
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise TherapeuticAssessmentError("validation_error", f"{field}必须是ISO时间。") from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc).isoformat()


def _present_queue(row: dict) -> dict:
    item = dict(row)
    item["scope_snapshot"] = json_loads(item.pop("scope_snapshot_json", None), {})
    item["overdue"] = item["status"] in OPEN_STATUSES and str(item["due_at"]) < now_iso()
    return item


def _present_shift(row: dict) -> dict:
    item = dict(row)
    item["queue_types"] = json_loads(item.pop("queue_types_json", None), [])
    item["scope"] = json_loads(item.pop("scope_json", None), {})
    item["effective"] = (
        item["status"] == "active"
        and str(item["starts_at"]) <= now_iso()
        and str(item["expires_at"]) > now_iso()
    )
    return item


def _runtime(conn) -> dict:
    row = conn.execute(
        "SELECT * FROM therapeutic_assessment_queue_runtime WHERE id = 'global'"
    ).fetchone()
    if row is None:
        policy = _policy()
        conn.execute(
            """
            INSERT INTO therapeutic_assessment_queue_runtime (
                id, paused, reason, pending_count, overdue_count,
                unattended_urgent_count, policy_version, version, updated_at
            ) VALUES ('global', 0, NULL, 0, 0, 0, ?, 1, ?)
            """,
            (policy["version"], now_iso()),
        )
        row = conn.execute(
            "SELECT * FROM therapeutic_assessment_queue_runtime WHERE id = 'global'"
        ).fetchone()
    return row_to_dict(row)


def _assert_review_role(actor: dict) -> None:
    if str(actor.get("role") or "") not in REVIEW_ROLES:
        raise TherapeuticAssessmentError(
            "forbidden", "只有督导或管理员可以配置人工队列和值守。", 403
        )


def _scope_matches(scope: dict, case: dict) -> bool:
    case_ids = {str(item) for item in scope.get("case_ids") or []}
    complexity_scopes = {str(item) for item in scope.get("complexity_scopes") or []}
    readiness_levels = {str(item) for item in scope.get("readiness_levels") or []}
    return (
        (not case_ids or str(case["id"]) in case_ids)
        and (
            not complexity_scopes
            or str(case["complexity_scope"]) in complexity_scopes
        )
        and (
            not readiness_levels
            or str(case["readiness_level"]) in readiness_levels
        )
    )


def _active_shift(conn, actor_id: str, queue_type: str, case: dict) -> dict | None:
    rows = rows_to_dicts(
        conn.execute(
            """
            SELECT * FROM therapeutic_assessment_duty_shifts
            WHERE user_id = ? AND status = 'active'
              AND starts_at <= ? AND expires_at > ?
            ORDER BY expires_at DESC
            """,
            (actor_id, now_iso(), now_iso()),
        ).fetchall()
    )
    for row in rows:
        shift = _present_shift(row)
        if queue_type in set(shift["queue_types"]) and _scope_matches(
            shift["scope"], case
        ):
            return shift
    return None


def create_duty_shift(
    actor: dict, payload: dict, idempotency_key: str
) -> tuple[dict, int]:
    _assert_review_role(actor)
    key = _idempotency(idempotency_key)
    user_id = str(payload.get("user_id") or "").strip()
    supervisor_id = str(payload.get("supervisor_user_id") or "").strip()
    evidence_ref = str(payload.get("evidence_ref") or "").strip()
    queue_types = payload.get("queue_types")
    scope = payload.get("scope")
    policy = _policy()
    allowed_types = set(policy["queue_types"])
    if (
        not isinstance(queue_types, list)
        or not queue_types
        or not set(queue_types).issubset(allowed_types)
        or not isinstance(scope, dict)
        or not scope
    ):
        raise TherapeuticAssessmentError(
            "validation_error", "值守队列类型和对象范围必须明确。"
        )
    starts_at = _parse_time(payload.get("starts_at") or now_iso(), "starts_at")
    expires_at = _parse_time(payload.get("expires_at"), "expires_at")
    if expires_at <= starts_at or not user_id or not supervisor_id or not evidence_ref:
        raise TherapeuticAssessmentError(
            "validation_error", "值守人员、督导、证据和有效期必须完整。"
        )
    with get_connection() as conn:
        replay = conn.execute(
            """
            SELECT s.* FROM therapeutic_assessment_duty_events e
            JOIN therapeutic_assessment_duty_shifts s ON s.id = e.duty_shift_id
            WHERE e.actor_id = ? AND e.idempotency_key = ?
            """,
            (str(actor["id"]), key),
        ).fetchone()
        if replay:
            return _present_shift(row_to_dict(replay)), 200
        target = conn.execute(
            "SELECT role, status FROM users WHERE id = ?", (user_id,)
        ).fetchone()
        supervisor = conn.execute(
            "SELECT role, status FROM users WHERE id = ?", (supervisor_id,)
        ).fetchone()
        if (
            target is None
            or str(target["role"]) not in FORMAL_ROLES
            or str(target["status"]) != "active"
            or supervisor is None
            or str(supervisor["role"]) not in REVIEW_ROLES
            or str(supervisor["status"]) != "active"
        ):
            raise TherapeuticAssessmentError(
                "validation_error", "值守人员和督导必须是有效正式角色。", 422
            )
        shift_id = new_id("ta_duty")
        timestamp = now_iso()
        conn.execute(
            """
            INSERT INTO therapeutic_assessment_duty_shifts (
                id, user_id, supervisor_user_id, queue_types_json, scope_json,
                starts_at, expires_at, status, version, evidence_ref,
                created_by, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, 'active', 1, ?, ?, ?, ?)
            """,
            (
                shift_id,
                user_id,
                supervisor_id,
                json_dumps(list(dict.fromkeys(queue_types))),
                json_dumps(scope),
                starts_at,
                expires_at,
                evidence_ref,
                str(actor["id"]),
                timestamp,
                timestamp,
            ),
        )
        conn.execute(
            """
            INSERT INTO therapeutic_assessment_duty_events (
                id, duty_shift_id, actor_id, action, metadata_json,
                idempotency_key, created_at
            ) VALUES (?, ?, ?, 'created', ?, ?, ?)
            """,
            (
                new_id("ta_duty_evt"),
                shift_id,
                str(actor["id"]),
                json_dumps({"queue_types": queue_types}),
                key,
                timestamp,
            ),
        )
        write_audit_log(
            conn,
            "therapeutic_assessment_duty_created",
            str(actor["id"]),
            "therapeutic_assessment_duty_shift",
            shift_id,
            {"user_id": user_id, "queue_types": queue_types},
        )
        conn.commit()
        row = conn.execute(
            "SELECT * FROM therapeutic_assessment_duty_shifts WHERE id = ?",
            (shift_id,),
        ).fetchone()
    return _present_shift(row_to_dict(row)), 201


def list_duty_shifts(actor: dict, params: dict) -> dict:
    if str(actor.get("role") or "") not in FORMAL_ROLES:
        raise TherapeuticAssessmentError("forbidden", "当前账号不能查看值守状态。", 403)
    requested = str(params.get("user_id") or "").strip()
    if not requested and str(actor.get("role")) not in REVIEW_ROLES:
        requested = str(actor["id"])
    if requested and requested != str(actor["id"]) and str(actor.get("role")) not in REVIEW_ROLES:
        raise TherapeuticAssessmentError("forbidden", "只能查看自己的值守状态。", 403)
    with get_connection() as conn:
        if requested:
            rows = rows_to_dicts(
                conn.execute(
                    "SELECT * FROM therapeutic_assessment_duty_shifts WHERE user_id = ? ORDER BY created_at DESC",
                    (requested,),
                ).fetchall()
            )
        else:
            rows = rows_to_dicts(
                conn.execute(
                    "SELECT * FROM therapeutic_assessment_duty_shifts ORDER BY created_at DESC"
                ).fetchall()
            )
    return {"items": [_present_shift(row) for row in rows], "count": len(rows)}


def create_work_item(
    actor: dict, case_id: str, payload: dict, idempotency_key: str
) -> tuple[dict, int]:
    _assert_review_role(actor)
    key = _idempotency(idempotency_key)
    queue_type = str(payload.get("queue_type") or "").strip()
    policy = _policy()
    queue_config = policy["queue_types"].get(queue_type)
    if not queue_config:
        raise TherapeuticAssessmentError("validation_error", "人工队列类型无效。")
    with get_connection() as conn:
        case = _case_row(conn, case_id)
        replay = conn.execute(
            """
            SELECT q.* FROM therapeutic_assessment_queue_events e
            JOIN therapeutic_assessment_work_queue q ON q.id = e.queue_item_id
            WHERE e.actor_id = ? AND e.idempotency_key = ?
            """,
            (str(actor["id"]), key),
        ).fetchone()
        if replay:
            return _present_queue(row_to_dict(replay)), 200
        timestamp = now_iso()
        due_at = (
            datetime.now(timezone.utc)
            + timedelta(hours=int(queue_config["sla_hours"]))
        ).isoformat()
        item_id = new_id("ta_queue")
        snapshot = {
            "case_id": case["id"],
            "complexity_scope": case["complexity_scope"],
            "readiness_level": case["readiness_level"],
            "safety_state": case["safety_state"],
        }
        conn.execute(
            """
            INSERT INTO therapeutic_assessment_work_queue (
                id, case_id, queue_type, task_code, required_competency,
                priority, status, scope_snapshot_json, drafted_by, due_at,
                version, created_by, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, 'open', ?, ?, ?, 1, ?, ?, ?)
            """,
            (
                item_id,
                case_id,
                queue_type,
                queue_config["task_code"],
                queue_config["required_competency"],
                queue_config["priority"],
                json_dumps(snapshot),
                str(payload.get("drafted_by") or "").strip() or None,
                due_at,
                str(actor["id"]),
                timestamp,
                timestamp,
            ),
        )
        conn.execute(
            """
            INSERT INTO therapeutic_assessment_queue_events (
                id, queue_item_id, actor_id, action, before_version,
                after_version, metadata_json, idempotency_key, created_at
            ) VALUES (?, ?, ?, 'created', NULL, 1, ?, ?, ?)
            """,
            (
                new_id("ta_queue_evt"),
                item_id,
                str(actor["id"]),
                json_dumps(snapshot),
                key,
                timestamp,
            ),
        )
        write_audit_log(
            conn,
            "therapeutic_assessment_queue_item_created",
            str(actor["id"]),
            "therapeutic_assessment_queue_item",
            item_id,
            {"case_id": case_id, "queue_type": queue_type},
        )
        conn.commit()
        row = conn.execute(
            "SELECT * FROM therapeutic_assessment_work_queue WHERE id = ?",
            (item_id,),
        ).fetchone()
    return _present_queue(row_to_dict(row)), 201


def list_work_items(actor: dict, params: dict) -> dict:
    if str(actor.get("role") or "") not in FORMAL_ROLES:
        raise TherapeuticAssessmentError("forbidden", "当前账号不能查看人工队列。", 403)
    status = str(params.get("status") or "").strip()
    with get_connection() as conn:
        if str(actor.get("role")) in REVIEW_ROLES:
            query = "SELECT * FROM therapeutic_assessment_work_queue"
            values: tuple[str, ...] = ()
            if status:
                query += " WHERE status = ?"
                values = (status,)
        else:
            query = (
                "SELECT * FROM therapeutic_assessment_work_queue "
                "WHERE assigned_user_id = ? OR status IN ('open', 'handoff_required')"
            )
            values = (str(actor["id"]),)
            if status:
                query = f"SELECT * FROM ({query}) AS visible_queue WHERE status = ?"
                values += (status,)
        rows = rows_to_dicts(
            conn.execute(query + " ORDER BY due_at ASC, created_at ASC", values).fetchall()
        )
        if str(actor.get("role")) not in REVIEW_ROLES:
            visible = []
            for row in rows:
                if str(row.get("assigned_user_id") or "") == str(actor["id"]):
                    visible.append(row)
                    continue
                case = _case_row(conn, row["case_id"])
                if _active_shift(conn, str(actor["id"]), row["queue_type"], case) is None:
                    continue
                try:
                    assert_task_authorized(conn, actor, case, row["task_code"])
                except TherapeuticAssessmentError:
                    continue
                visible.append(row)
            rows = visible
    return {"items": [_present_queue(row) for row in rows], "count": len(rows)}


def claim_work_item(
    actor: dict, item_id: str, payload: dict, idempotency_key: str
) -> dict:
    key = _idempotency(idempotency_key)
    expected = payload.get("expected_version")
    if str(actor.get("role") or "") not in FORMAL_ROLES or not isinstance(expected, int):
        raise TherapeuticAssessmentError(
            "validation_error", "领取者必须是正式角色并提供expected_version。"
        )
    with get_connection() as conn:
        runtime = _runtime(conn)
        if int(runtime["paused"]):
            raise TherapeuticAssessmentError(
                "queue_runtime_paused", "人工队列已暂停，请先完成值守或积压修复。", 409
            )
        row = conn.execute(
            "SELECT * FROM therapeutic_assessment_work_queue WHERE id = ?", (item_id,)
        ).fetchone()
        if row is None:
            raise TherapeuticAssessmentError("not_found", "没有找到人工队列任务。", 404)
        item = row_to_dict(row)
        replay = conn.execute(
            "SELECT 1 FROM therapeutic_assessment_queue_events WHERE actor_id = ? AND idempotency_key = ?",
            (str(actor["id"]), key),
        ).fetchone()
        if replay:
            return _present_queue(item)
        if item["status"] not in {"open", "handoff_required"}:
            raise TherapeuticAssessmentError("invalid_state", "该任务当前不能领取。", 409)
        if int(item["version"]) != expected:
            raise TherapeuticAssessmentError("version_conflict", "队列任务已变化，请重新读取。", 409)
        case = _case_row(conn, item["case_id"])
        snapshot = json_loads(item["scope_snapshot_json"], {})
        if any(
            str(snapshot.get(field) or "") != str(case[field])
            for field in ("complexity_scope", "readiness_level", "safety_state")
        ):
            raise TherapeuticAssessmentError(
                "object_scope_changed", "对象范围已变化，需要重新建队列任务。", 409
            )
        if _active_shift(conn, str(actor["id"]), item["queue_type"], case) is None:
            raise TherapeuticAssessmentError(
                "duty_coverage_required", "当前账号没有覆盖该对象和队列的有效值守班次。", 403
            )
        assert_task_authorized(conn, actor, case, item["task_code"])
        queue_config = _policy()["queue_types"][item["queue_type"]]
        if (
            queue_config["draft_reviewer_separation"]
            and str(item.get("drafted_by") or "") == str(actor["id"])
        ):
            raise TherapeuticAssessmentError(
                "independent_reviewer_required", "起草者不能领取最终复核任务。", 409
            )
        timestamp = now_iso()
        cursor = conn.execute(
            """
            UPDATE therapeutic_assessment_work_queue
            SET status = 'claimed', assigned_user_id = ?, claimed_at = ?,
                version = version + 1, updated_at = ?
            WHERE id = ? AND version = ? AND status IN ('open', 'handoff_required')
            """,
            (str(actor["id"]), timestamp, timestamp, item_id, expected),
        )
        if cursor.rowcount != 1:
            raise TherapeuticAssessmentError("version_conflict", "队列任务已被领取。", 409)
        conn.execute(
            """
            INSERT INTO therapeutic_assessment_queue_events (
                id, queue_item_id, actor_id, action, before_version,
                after_version, metadata_json, idempotency_key, created_at
            ) VALUES (?, ?, ?, 'claimed', ?, ?, '{}', ?, ?)
            """,
            (
                new_id("ta_queue_evt"),
                item_id,
                str(actor["id"]),
                expected,
                expected + 1,
                key,
                timestamp,
            ),
        )
        write_audit_log(
            conn,
            "therapeutic_assessment_queue_item_claimed",
            str(actor["id"]),
            "therapeutic_assessment_queue_item",
            item_id,
            {"case_id": item["case_id"]},
        )
        conn.commit()
        return _present_queue(
            row_to_dict(
                conn.execute(
                    "SELECT * FROM therapeutic_assessment_work_queue WHERE id = ?",
                    (item_id,),
                ).fetchone()
            )
        )


def handoff_work_item(
    actor: dict, item_id: str, payload: dict, idempotency_key: str
) -> dict:
    key = _idempotency(idempotency_key)
    expected = payload.get("expected_version")
    reason = str(payload.get("reason") or "").strip()
    if not isinstance(expected, int) or not reason:
        raise TherapeuticAssessmentError(
            "validation_error", "交接原因和expected_version不能为空。"
        )
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM therapeutic_assessment_work_queue WHERE id = ?", (item_id,)
        ).fetchone()
        if row is None:
            raise TherapeuticAssessmentError("not_found", "没有找到人工队列任务。", 404)
        item = row_to_dict(row)
        if (
            str(item.get("assigned_user_id") or "") != str(actor["id"])
            and str(actor.get("role") or "") not in REVIEW_ROLES
        ):
            raise TherapeuticAssessmentError("forbidden", "只能交接自己领取的任务。", 403)
        if item["status"] != "claimed" or int(item["version"]) != expected:
            raise TherapeuticAssessmentError("version_conflict", "任务状态已变化。", 409)
        timestamp = now_iso()
        conn.execute(
            """
            UPDATE therapeutic_assessment_work_queue
            SET status = 'handoff_required', assigned_user_id = NULL,
                claimed_at = NULL, version = version + 1, updated_at = ?
            WHERE id = ? AND version = ?
            """,
            (timestamp, item_id, expected),
        )
        conn.execute(
            """
            INSERT INTO therapeutic_assessment_queue_events (
                id, queue_item_id, actor_id, action, before_version,
                after_version, metadata_json, idempotency_key, created_at
            ) VALUES (?, ?, ?, 'handoff_requested', ?, ?, ?, ?, ?)
            """,
            (
                new_id("ta_queue_evt"),
                item_id,
                str(actor["id"]),
                expected,
                expected + 1,
                json_dumps({"reason": reason[:500]}),
                key,
                timestamp,
            ),
        )
        conn.commit()
        return _present_queue(
            row_to_dict(
                conn.execute(
                    "SELECT * FROM therapeutic_assessment_work_queue WHERE id = ?",
                    (item_id,),
                ).fetchone()
            )
        )


def queue_runtime_status() -> dict:
    with get_connection() as conn:
        return _runtime(conn)


def run_queue_monitor(actor: dict) -> dict:
    _assert_review_role(actor)
    policy = _policy()
    timestamp = now_iso()
    with get_connection() as conn:
        pending_count = int(
            conn.execute(
                "SELECT COUNT(*) AS count FROM therapeutic_assessment_work_queue WHERE status IN ('open', 'claimed', 'handoff_required')"
            ).fetchone()["count"]
        )
        overdue_count = int(
            conn.execute(
                "SELECT COUNT(*) AS count FROM therapeutic_assessment_work_queue WHERE status IN ('open', 'claimed', 'handoff_required') AND due_at < ?",
                (timestamp,),
            ).fetchone()["count"]
        )
        urgent_rows = rows_to_dicts(
            conn.execute(
                "SELECT * FROM therapeutic_assessment_work_queue WHERE priority = 'urgent' AND status IN ('open', 'handoff_required')"
            ).fetchall()
        )
        unattended = 0
        for item in urgent_rows:
            case = _case_row(conn, item["case_id"])
            shifts = rows_to_dicts(
                conn.execute(
                    """
                    SELECT * FROM therapeutic_assessment_duty_shifts
                    WHERE status = 'active' AND starts_at <= ? AND expires_at > ?
                    """,
                    (timestamp, timestamp),
                ).fetchall()
            )
            if not any(
                item["queue_type"] in set(_present_shift(shift)["queue_types"])
                and _scope_matches(_present_shift(shift)["scope"], case)
                for shift in shifts
            ):
                unattended += 1
        limits = policy["runtime_pause"]
        reasons = []
        if pending_count > int(limits["max_pending"]):
            reasons.append("pending_threshold")
        if overdue_count > int(limits["max_overdue"]):
            reasons.append("overdue_threshold")
        if limits["pause_when_urgent_queue_unattended"] and unattended:
            reasons.append("urgent_queue_unattended")
        runtime = _runtime(conn)
        paused = bool(reasons)
        conn.execute(
            """
            UPDATE therapeutic_assessment_queue_runtime
            SET paused = ?, reason = ?, pending_count = ?, overdue_count = ?,
                unattended_urgent_count = ?, policy_version = ?,
                version = version + 1, updated_at = ?
            WHERE id = 'global'
            """,
            (
                int(paused),
                ",".join(reasons) or None,
                pending_count,
                overdue_count,
                unattended,
                policy["version"],
                timestamp,
            ),
        )
        write_audit_log(
            conn,
            "therapeutic_assessment_queue_monitored",
            str(actor["id"]),
            "therapeutic_assessment_queue_runtime",
            "global",
            {
                "paused": paused,
                "reasons": reasons,
                "before_version": runtime["version"],
            },
        )
        conn.commit()
        return _runtime(conn)
