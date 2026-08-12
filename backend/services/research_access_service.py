"""Versioned researcher capabilities and participant object-scope assignments."""

from __future__ import annotations

import hashlib
import json

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
from services.showcase_access_service import allow_showcase_researcher_platform_full_access


REGISTRY_FILE = "researcher_capability_registry.json"
ACTIVE_ENROLLMENT_STATUSES = {"enrolled", "active"}
ASSIGNMENT_ROLES = {"researcher", "supervisor"}


class ResearchAccessError(Exception):
    def __init__(self, code: str, message: str, status: int = 400, details: dict | None = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status = status
        self.details = details or {}


def registry() -> dict:
    return load_content_json(REGISTRY_FILE)


def capability(capability_id: str) -> dict:
    item = next(
        (row for row in registry().get("capabilities", []) if row.get("id") == capability_id),
        None,
    )
    if not item:
        raise RuntimeError(f"unknown researcher capability: {capability_id}")
    return item


def capability_ids_for_role(role: str) -> list[str]:
    return [
        item["id"]
        for item in registry().get("capabilities", [])
        if role in set(item.get("roles") or [])
    ]


def assert_capability(actor: dict, capability_id: str) -> None:
    item = capability(capability_id)
    role = str(actor.get("original_role") or actor.get("role") or "")
    effective_role = str(actor.get("role") or "")
    development_exception = bool(
        actor.get("showcase_full_access")
        and allow_showcase_researcher_platform_full_access()
        and item.get("development_exception")
    )
    if effective_role in set(item.get("roles") or []) or development_exception:
        return
    raise ResearchAccessError(
        "forbidden",
        "当前账号没有执行该研究操作的权限。",
        403,
        {"required_capability": capability_id, "formal_role": role or "unknown"},
    )


def capability_summary(actor: dict) -> dict:
    formal_role = str(actor.get("original_role") or actor.get("role") or "")
    development_exception_active = bool(
        actor.get("showcase_full_access")
        and allow_showcase_researcher_platform_full_access()
    )
    capability_ids = capability_ids_for_role(formal_role)
    if development_exception_active:
        capability_ids = sorted(
            set(capability_ids)
            | {
                item["id"]
                for item in registry().get("capabilities", [])
                if item.get("development_exception")
            }
        )
    return {
        "registry_version": registry().get("version"),
        "formal_role": formal_role,
        "effective_role": actor.get("role"),
        "development_exception_active": development_exception_active,
        "development_exception_is_formal_evidence": False,
        "capability_ids": capability_ids,
    }


def active_assignment(conn, enrollment_id: str, actor_id: str, assignment_role: str) -> dict | None:
    row = conn.execute(
        """
        SELECT * FROM research_scope_assignments
        WHERE enrollment_id = ? AND actor_id = ? AND assignment_role = ? AND status = 'active'
        ORDER BY updated_at DESC LIMIT 1
        """,
        (enrollment_id, actor_id, assignment_role),
    ).fetchone()
    return row_to_dict(row)


def has_object_scope(conn, actor: dict, enrollment: dict) -> bool:
    role = str(actor.get("role") or "")
    if role == "admin":
        return True
    if role not in ASSIGNMENT_ROLES:
        return str(actor.get("id")) == str(enrollment.get("user_id"))
    actor_id = str(actor.get("id") or "")
    if role == "researcher" and str(enrollment.get("assigned_researcher_id") or "") == actor_id:
        return True
    return bool(active_assignment(conn, str(enrollment["id"]), actor_id, role))


def require_object_scope(conn, actor: dict, enrollment: dict, capability_id: str) -> None:
    if has_object_scope(conn, actor, enrollment):
        return
    raise ResearchAccessError(
        "forbidden",
        "当前账号没有访问该参与者资料的范围权限。",
        403,
        {"required_capability": capability_id},
    )


def _enrollment(conn, enrollment_id: str) -> dict:
    row = conn.execute(
        "SELECT * FROM relationship_pilot_enrollments WHERE id = ?", (enrollment_id,)
    ).fetchone()
    if not row:
        raise ResearchAccessError("not_found", "没有找到可操作的报名记录。", 404)
    return row_to_dict(row)


def _validate_assignee(conn, actor_id: str, assignment_role: str) -> None:
    if assignment_role not in ASSIGNMENT_ROLES:
        raise ResearchAccessError("validation_error", "分配角色只支持 researcher 或 supervisor。")
    row = conn.execute("SELECT role, status FROM users WHERE id = ?", (actor_id,)).fetchone()
    if not row or row["status"] != "active" or row["role"] != assignment_role:
        raise ResearchAccessError("validation_error", "目标账号不存在、已停用或角色不匹配。")


def _insert_assignment(
    conn,
    enrollment_id: str,
    actor_id: str,
    assignment_role: str,
    assigned_by: str,
    idempotency_key: str,
) -> dict:
    timestamp = now_iso()
    assignment_id = new_id("research_scope")
    conn.execute(
        """
        INSERT INTO research_scope_assignments (
            id, enrollment_id, actor_id, assignment_role, status, version,
            idempotency_key, assigned_by, created_at, updated_at
        ) VALUES (?, ?, ?, ?, 'active', 1, ?, ?, ?, ?)
        """,
        (
            assignment_id,
            enrollment_id,
            actor_id,
            assignment_role,
            idempotency_key or None,
            assigned_by,
            timestamp,
            timestamp,
        ),
    )
    if assignment_role == "researcher":
        conn.execute(
            "UPDATE relationship_pilot_enrollments SET assigned_researcher_id = ?, updated_at = ? WHERE id = ?",
            (actor_id, timestamp, enrollment_id),
        )
    row = conn.execute("SELECT * FROM research_scope_assignments WHERE id = ?", (assignment_id,)).fetchone()
    return row_to_dict(row)


def _action_request_hash(assignment_id: str, payload: dict) -> str:
    canonical = json.dumps(
        {"assignment_id": assignment_id, "payload": payload},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _action_replay(conn, actor_id: str, idempotency_key: str, request_hash: str) -> dict | None:
    row = conn.execute(
        "SELECT * FROM research_scope_assignment_actions WHERE actor_id = ? AND idempotency_key = ?",
        (actor_id, idempotency_key),
    ).fetchone()
    if not row:
        return None
    if row["request_hash"] != request_hash:
        raise ResearchAccessError("idempotency_conflict", "该提交标识已用于其他分配操作。", 409)
    return json_loads(row["result_json"], {})


def _record_action(
    conn,
    *,
    assignment_id: str,
    actor_id: str,
    action: str,
    idempotency_key: str,
    request_hash: str,
    result: dict,
) -> None:
    conn.execute(
        """
        INSERT INTO research_scope_assignment_actions (
            id, assignment_id, actor_id, action, idempotency_key,
            request_hash, result_json, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            new_id("research_scope_action"),
            assignment_id,
            actor_id,
            action,
            idempotency_key,
            request_hash,
            json_dumps(result),
            now_iso(),
        ),
    )


def create_assignment(actor: dict, payload: dict, idempotency_key: str) -> tuple[dict, int]:
    assert_capability(actor, "research.assignment.manage")
    enrollment_id = str(payload.get("enrollment_id") or "").strip()
    target_actor_id = str(payload.get("actor_id") or "").strip()
    assignment_role = str(payload.get("assignment_role") or "researcher").strip()
    idempotency_key = str(idempotency_key or "").strip()[:128]
    if not enrollment_id or not target_actor_id or not idempotency_key:
        raise ResearchAccessError("validation_error", "enrollment_id、actor_id 和 Idempotency-Key 不能为空。")
    with get_connection() as conn:
        enrollment = _enrollment(conn, enrollment_id)
        if enrollment.get("status") not in ACTIVE_ENROLLMENT_STATUSES:
            raise ResearchAccessError("enrollment_inactive", "停用报名不能新增研究分配。", 409)
        _validate_assignee(conn, target_actor_id, assignment_role)
        repeated = conn.execute(
            "SELECT * FROM research_scope_assignments WHERE assigned_by = ? AND idempotency_key = ? ORDER BY created_at DESC LIMIT 1",
            (actor["id"], idempotency_key),
        ).fetchone()
        if repeated:
            item = row_to_dict(repeated)
            if (
                item["enrollment_id"] != enrollment_id
                or item["actor_id"] != target_actor_id
                or item["assignment_role"] != assignment_role
            ):
                raise ResearchAccessError("idempotency_conflict", "该提交标识已用于其他分配。", 409)
            return item, 200
        existing = conn.execute(
            """
            SELECT * FROM research_scope_assignments
            WHERE enrollment_id = ? AND assignment_role = ? AND status = 'active'
            ORDER BY updated_at DESC LIMIT 1
            """,
            (enrollment_id, assignment_role),
        ).fetchone()
        if existing:
            existing_item = row_to_dict(existing)
            if existing_item["actor_id"] == target_actor_id:
                return existing_item, 200
            raise ResearchAccessError("assignment_conflict", "该报名已有有效分配，请使用转交操作。", 409)
        if assignment_role == "researcher":
            legacy_actor = str(enrollment.get("assigned_researcher_id") or "")
            if legacy_actor and legacy_actor != target_actor_id:
                raise ResearchAccessError("assignment_conflict", "该报名已有有效分配，请先完成迁移或转交。", 409)
        item = _insert_assignment(
            conn, enrollment_id, target_actor_id, assignment_role, str(actor["id"]), idempotency_key
        )
        write_audit_log(
            conn,
            "research_scope_assigned",
            str(actor["id"]),
            "research_scope_assignment",
            item["id"],
            {"enrollment_id": enrollment_id, "actor_id": target_actor_id, "assignment_role": assignment_role},
        )
        conn.commit()
        return item, 201


def claim_enrollment(actor: dict, enrollment_id: str, idempotency_key: str) -> tuple[dict, int]:
    assert_capability(actor, "research.assignment.claim")
    idempotency_key = str(idempotency_key or "").strip()[:128]
    if not idempotency_key:
        raise ResearchAccessError("validation_error", "Idempotency-Key 不能为空。")
    actor_id = str(actor["id"])
    with get_connection() as conn:
        enrollment = _enrollment(conn, enrollment_id)
        if enrollment.get("status") not in ACTIVE_ENROLLMENT_STATUSES:
            raise ResearchAccessError("enrollment_inactive", "停用报名不能领取。", 409)
        repeated = conn.execute(
            "SELECT * FROM research_scope_assignments WHERE actor_id = ? AND idempotency_key = ? LIMIT 1",
            (actor_id, idempotency_key),
        ).fetchone()
        if repeated:
            item = row_to_dict(repeated)
            if item["enrollment_id"] != enrollment_id:
                raise ResearchAccessError("idempotency_conflict", "该提交标识已用于其他领取。", 409)
            return item, 200
        legacy_actor = str(enrollment.get("assigned_researcher_id") or "")
        active = conn.execute(
            """
            SELECT * FROM research_scope_assignments
            WHERE enrollment_id = ? AND assignment_role = 'researcher' AND status = 'active'
            ORDER BY updated_at DESC LIMIT 1
            """,
            (enrollment_id,),
        ).fetchone()
        if (legacy_actor and legacy_actor != actor_id) or (active and active["actor_id"] != actor_id):
            raise ResearchAccessError(
                "forbidden", "该报名当前不可领取。", 403, {"required_capability": "research.assignment.claim"}
            )
        if active:
            return row_to_dict(active), 200
        claim_cursor = conn.execute(
            """
            UPDATE relationship_pilot_enrollments
            SET assigned_researcher_id = ?, updated_at = ?
            WHERE id = ? AND (assigned_researcher_id IS NULL OR assigned_researcher_id = '' OR assigned_researcher_id = ?)
            """,
            (actor_id, now_iso(), enrollment_id, actor_id),
        )
        if claim_cursor.rowcount != 1:
            raise ResearchAccessError(
                "assignment_conflict", "该报名已被其他研究者领取，请刷新后重试。", 409
            )
        item = _insert_assignment(
            conn, enrollment_id, actor_id, "researcher", actor_id, idempotency_key
        )
        write_audit_log(
            conn,
            "research_scope_claimed",
            actor_id,
            "research_scope_assignment",
            item["id"],
            {"enrollment_id": enrollment_id},
        )
        write_audit_log(
            conn,
            "relationship_researcher_assigned",
            actor_id,
            "relationship_pilot_enrollment",
            enrollment_id,
            {"assigned_researcher_id": actor_id, "source": "research_scope_assignment"},
        )
        conn.commit()
        return item, 201


def update_assignment(actor: dict, assignment_id: str, payload: dict, idempotency_key: str) -> dict:
    assert_capability(actor, "research.assignment.manage")
    idempotency_key = str(idempotency_key or "").strip()[:128]
    if not idempotency_key:
        raise ResearchAccessError("validation_error", "Idempotency-Key 不能为空。")
    actor_id = str(actor["id"])
    request_hash = _action_request_hash(assignment_id, payload)
    with get_connection() as conn:
        replay = _action_replay(conn, actor_id, idempotency_key, request_hash)
        if replay is not None:
            return replay
        row = conn.execute("SELECT * FROM research_scope_assignments WHERE id = ?", (assignment_id,)).fetchone()
        if not row:
            raise ResearchAccessError("not_found", "没有找到可操作的分配记录。", 404)
        item = row_to_dict(row)
        try:
            expected_version = int(payload.get("expected_version"))
        except (TypeError, ValueError) as exc:
            raise ResearchAccessError("validation_error", "expected_version 必须是整数。") from exc
        if expected_version != int(item["version"]):
            raise ResearchAccessError("version_conflict", "分配记录已更新，请刷新后重试。", 409)
        timestamp = now_iso()
        action = str(payload.get("action") or "").strip()
        if action == "transfer":
            target_actor_id = str(payload.get("target_actor_id") or "").strip()
            _validate_assignee(conn, target_actor_id, item["assignment_role"])
            revoked_cursor = conn.execute(
                "UPDATE research_scope_assignments SET status = 'revoked', version = version + 1, revoked_at = ?, updated_at = ? WHERE id = ? AND version = ?",
                (timestamp, timestamp, assignment_id, expected_version),
            )
            if revoked_cursor.rowcount != 1:
                raise ResearchAccessError("version_conflict", "分配记录已更新，请刷新后重试。", 409)
            if item["assignment_role"] == "researcher":
                transfer_cursor = conn.execute(
                    """
                    UPDATE relationship_pilot_enrollments
                    SET assigned_researcher_id = ?, updated_at = ?
                    WHERE id = ? AND assigned_researcher_id = ?
                    """,
                    (target_actor_id, timestamp, item["enrollment_id"], item["actor_id"]),
                )
                if transfer_cursor.rowcount != 1:
                    raise ResearchAccessError(
                        "assignment_conflict", "报名分配状态已变化，请刷新后重试。", 409
                    )
            active = _insert_assignment(
                conn,
                item["enrollment_id"],
                target_actor_id,
                item["assignment_role"],
                str(actor["id"]),
                idempotency_key,
            )
            result = {"revoked_assignment_id": assignment_id, "active_assignment": active}
            audit_action = "research_scope_transferred"
        else:
            status = str(payload.get("status") or "").strip()
            if status != "revoked":
                raise ResearchAccessError("validation_error", "当前只支持 revoked 或 transfer。")
            revoked_cursor = conn.execute(
                "UPDATE research_scope_assignments SET status = 'revoked', version = version + 1, revoked_at = ?, updated_at = ? WHERE id = ? AND version = ?",
                (timestamp, timestamp, assignment_id, expected_version),
            )
            if revoked_cursor.rowcount != 1:
                raise ResearchAccessError("version_conflict", "分配记录已更新，请刷新后重试。", 409)
            if item["assignment_role"] == "researcher":
                conn.execute(
                    "UPDATE relationship_pilot_enrollments SET assigned_researcher_id = NULL, updated_at = ? WHERE id = ? AND assigned_researcher_id = ?",
                    (timestamp, item["enrollment_id"], item["actor_id"]),
                )
            refreshed = conn.execute("SELECT * FROM research_scope_assignments WHERE id = ?", (assignment_id,)).fetchone()
            result = row_to_dict(refreshed)
            audit_action = "research_scope_revoked"
        _record_action(
            conn,
            assignment_id=assignment_id,
            actor_id=actor_id,
            action="transfer" if action == "transfer" else "revoke",
            idempotency_key=idempotency_key,
            request_hash=request_hash,
            result=result,
        )
        write_audit_log(
            conn,
            audit_action,
            actor_id,
            "research_scope_assignment",
            assignment_id,
            {"idempotency_key": idempotency_key, "expected_version": expected_version},
        )
        conn.commit()
        return result


def list_assignments(actor: dict, enrollment_id: str = "") -> dict:
    assert_capability(actor, "research.assignment.read")
    role = str(actor.get("role") or "")
    where = []
    params: list[str] = []
    if role != "admin":
        where.append("actor_id = ?")
        params.append(str(actor["id"]))
    if enrollment_id:
        where.append("enrollment_id = ?")
        params.append(enrollment_id)
    query = "SELECT * FROM research_scope_assignments"
    if where:
        query += " WHERE " + " AND ".join(where)
    query += " ORDER BY updated_at DESC"
    with get_connection() as conn:
        items = rows_to_dicts(conn.execute(query, params).fetchall())
        write_audit_log(
            conn,
            "research_scope_assignments_viewed",
            str(actor["id"]),
            "research_scope_assignment",
            enrollment_id or "self_scope",
            {"count": len(items), "role": role},
        )
        conn.commit()
    return {"items": items, "count": len(items)}
