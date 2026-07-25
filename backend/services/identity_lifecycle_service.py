"""Participant identity binding, account merge and reversible ownership transfer."""

from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone

from database import json_dumps, json_loads, new_id, now_iso, row_to_dict, write_audit_log
from services.data_claim_service import USER_ID_TABLES, count_claimable_records, summarized_counts


PARTICIPANT_ROLES = {"parent", "student", "user"}
BACKEND_ROLES = {"admin", "researcher", "supervisor"}
MERGE_ROLLBACK_HOURS = 24


class IdentityLifecycleError(ValueError):
    def __init__(self, code: str, message: str, status: int = 409) -> None:
        super().__init__(message)
        self.code = code
        self.status = status


def _identity_state(value: object, linked: bool = False) -> str:
    if not value:
        return "unbound"
    return "bound_linked" if linked else "bound_direct"


def _linked_identity_rows(conn, target_user_id: str) -> list[dict]:
    return [
        row_to_dict(row)
        for row in conn.execute(
            """
            SELECT id, username, password_hash, wechat_openid, phone_hash
            FROM users
            WHERE merged_into_user_id = ? AND status = 'merged'
            ORDER BY merged_at ASC, id ASC
            """,
            (target_user_id,),
        ).fetchall()
    ]


def identity_status(conn, user_id: str) -> dict:
    row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    if row is None:
        raise IdentityLifecycleError("account_not_found", "没有找到当前账号", 404)
    user = row_to_dict(row)
    linked = _linked_identity_rows(conn, user_id)

    def linked_has(field: str) -> bool:
        return any(bool(item.get(field)) for item in linked)

    username_direct = bool(user.get("username") and user.get("password_hash"))
    wechat_direct = bool(user.get("wechat_openid"))
    phone_direct = bool(user.get("phone_hash"))
    usable = {
        "username": username_direct,
        "wechat": wechat_direct or linked_has("wechat_openid"),
        "phone": phone_direct or linked_has("phone_hash"),
    }
    usable_count = sum(bool(value) for value in usable.values())
    claim = conn.execute(
        """
        SELECT id, status, version FROM data_claims
        WHERE target_user_id = ?
        ORDER BY created_at DESC LIMIT 1
        """,
        (user_id,),
    ).fetchone()
    return {
        "user_id": user_id,
        "role": user.get("role") or "parent",
        "auth_epoch": int(user.get("auth_epoch") or 0),
        "identities": {
            "username": {
                "state": _identity_state(username_direct),
                "can_unbind": False,
            },
            "wechat": {
                "state": _identity_state(wechat_direct or linked_has("wechat_openid"), not wechat_direct),
                "can_unbind": bool(usable["wechat"] and usable_count > 1),
            },
            "phone": {
                "state": _identity_state(phone_direct or linked_has("phone_hash"), not phone_direct),
                "can_unbind": bool(usable["phone"] and usable_count > 1),
            },
            "anonymous": {
                "state": (
                    "claim_pending"
                    if claim is not None and claim["status"] in {"available", "processing"}
                    else "claimed"
                    if claim is not None and claim["status"] == "claimed"
                    else "unbound"
                ),
                "can_unbind": False,
            },
        },
        "linked_account_count": len(linked),
        "privacy_notice": "这里只显示绑定状态，不返回用户名、OpenID、手机号摘要或匿名编号。",
    }


def unbind_identity(
    conn,
    user_id: str,
    identity_type: str,
    expected_auth_epoch: int,
) -> dict:
    if identity_type not in {"wechat", "phone"}:
        raise IdentityLifecycleError("validation_error", "只支持撤销微信或手机号登录绑定", 400)
    status = identity_status(conn, user_id)
    if int(status["auth_epoch"]) != int(expected_auth_epoch):
        raise IdentityLifecycleError("identity_version_conflict", "账号状态已更新，请刷新后重试")
    identity = status["identities"][identity_type]
    if identity["state"] == "unbound":
        return {**status, "already_unbound": True, "sessions_revoked": False}
    if not identity["can_unbind"]:
        raise IdentityLifecycleError("last_login_identity", "请先绑定另一种登录方式，再撤销当前唯一登录方式")

    field = "wechat_openid" if identity_type == "wechat" else "phone_hash"
    timestamp = now_iso()
    direct = conn.execute(f"SELECT {field} FROM users WHERE id = ?", (user_id,)).fetchone()
    if direct is not None and direct[field]:
        if identity_type == "phone":
            conn.execute(
                """
                UPDATE users
                SET phone_hash = NULL, phone_verified_at = NULL, phone_source = NULL, updated_at = ?
                WHERE id = ?
                """,
                (timestamp, user_id),
            )
        else:
            conn.execute(
                "UPDATE users SET wechat_openid = NULL, updated_at = ? WHERE id = ?",
                (timestamp, user_id),
            )
    else:
        linked = conn.execute(
            f"""
            SELECT id FROM users
            WHERE merged_into_user_id = ? AND status = 'merged' AND {field} IS NOT NULL
            ORDER BY merged_at ASC, id ASC LIMIT 1
            """,
            (user_id,),
        ).fetchone()
        if linked is None:
            return {**status, "already_unbound": True, "sessions_revoked": False}
        if identity_type == "phone":
            conn.execute(
                """
                UPDATE users
                SET phone_hash = NULL, phone_verified_at = NULL, phone_source = NULL, updated_at = ?
                WHERE id = ?
                """,
                (timestamp, linked["id"]),
            )
        else:
            conn.execute(
                "UPDATE users SET wechat_openid = NULL, updated_at = ? WHERE id = ?",
                (timestamp, linked["id"]),
            )
    conn.execute(
        "UPDATE users SET auth_epoch = auth_epoch + 1, updated_at = ? WHERE id = ?",
        (timestamp, user_id),
    )
    write_audit_log(
        conn,
        "login_identity_unbound",
        user_id,
        "user",
        user_id,
        {"identity_type": identity_type, "sessions_revoked": True, "business_records_deleted": False},
    )
    result = identity_status(conn, user_id)
    return {**result, "already_unbound": False, "sessions_revoked": True}


def _merge_counts(conn, source_user_id: str) -> dict[str, int]:
    return count_claimable_records(conn, source_user_id)


def _public_workflow(row: dict) -> dict:
    counts = json_loads(row.get("counts_json"), {})
    verification = json_loads(row.get("verification_json"), {})
    return {
        "id": row["id"],
        "source_user_id": row["source_user_id"],
        "target_user_id": row["target_user_id"],
        "status": row["status"],
        "reason_code": row["reason_code"],
        "version": int(row.get("version") or 0),
        "total_records": sum(int(value) for value in counts.values()),
        "modules": summarized_counts(counts),
        "verification": verification,
        "rollback_until": row.get("rollback_until"),
        "confirmed_at": row.get("confirmed_at"),
        "executed_at": row.get("executed_at"),
        "verified_at": row.get("verified_at"),
        "rolled_back_at": row.get("rolled_back_at"),
        "created_at": row.get("created_at"),
        "updated_at": row.get("updated_at"),
    }


def get_merge_workflow(conn, workflow_id: str) -> dict:
    row = conn.execute("SELECT * FROM identity_merge_workflows WHERE id = ?", (workflow_id,)).fetchone()
    if row is None:
        raise IdentityLifecycleError("merge_not_found", "没有找到账号合并流程", 404)
    return _public_workflow(row_to_dict(row))


def create_merge_candidate(
    conn,
    *,
    source_user_id: str,
    target_user_id: str,
    reason_code: str,
    requested_by: str,
    idempotency_key: str,
) -> tuple[dict, bool]:
    existing = conn.execute(
        """
        SELECT * FROM identity_merge_workflows
        WHERE requested_by = ? AND idempotency_key = ?
        """,
        (requested_by, idempotency_key),
    ).fetchone()
    if existing is not None:
        return _public_workflow(row_to_dict(existing)), False
    if not source_user_id or not target_user_id or source_user_id == target_user_id:
        raise IdentityLifecycleError("merge_invalid_accounts", "来源账号和目标账号必须存在且不能相同", 400)
    source = conn.execute("SELECT * FROM users WHERE id = ?", (source_user_id,)).fetchone()
    target = conn.execute("SELECT * FROM users WHERE id = ?", (target_user_id,)).fetchone()
    if source is None or target is None:
        raise IdentityLifecycleError("account_not_found", "没有找到待合并账号", 404)
    if source["role"] not in PARTICIPANT_ROLES or target["role"] not in PARTICIPANT_ROLES:
        raise IdentityLifecycleError("merge_role_forbidden", "后台角色不能进入参与者账号合并流程")
    if source["status"] != "active" or target["status"] != "active":
        raise IdentityLifecycleError("merge_account_inactive", "待合并账号必须处于可用状态")
    active = conn.execute(
        """
        SELECT id FROM identity_merge_workflows
        WHERE (source_user_id = ? OR target_user_id = ? OR source_user_id = ? OR target_user_id = ?)
          AND status IN ('candidate', 'confirmed', 'executed', 'verified')
        LIMIT 1
        """,
        (source_user_id, source_user_id, target_user_id, target_user_id),
    ).fetchone()
    if active is not None:
        raise IdentityLifecycleError("merge_workflow_conflict", "其中一个账号已有未结束的合并流程")

    timestamp = now_iso()
    workflow_id = new_id("identity_merge")
    counts = _merge_counts(conn, source_user_id)
    conn.execute(
        """
        INSERT INTO identity_merge_workflows (
            id, source_user_id, target_user_id, status, reason_code,
            requested_by, confirmed_by, idempotency_key,
            execution_idempotency_key, rollback_idempotency_key,
            counts_json, verification_json, version, rollback_until,
            confirmed_at, executed_at, verified_at, rolled_back_at,
            created_at, updated_at
        ) VALUES (?, ?, ?, 'candidate', ?, ?, NULL, ?, NULL, NULL, ?, '{}', 0, NULL, NULL, NULL, NULL, NULL, ?, ?)
        """,
        (
            workflow_id,
            source_user_id,
            target_user_id,
            reason_code or "identity_conflict",
            requested_by,
            idempotency_key,
            json_dumps(counts),
            timestamp,
            timestamp,
        ),
    )
    write_audit_log(
        conn,
        "identity_merge_candidate_created",
        requested_by,
        "identity_merge",
        workflow_id,
        {"source_user_id": source_user_id, "target_user_id": target_user_id, "record_count": sum(counts.values())},
    )
    return get_merge_workflow(conn, workflow_id), True


def confirm_merge(conn, workflow_id: str, actor_id: str, expected_version: int) -> dict:
    timestamp = now_iso()
    cursor = conn.execute(
        """
        UPDATE identity_merge_workflows
        SET status = 'confirmed', confirmed_by = ?, confirmed_at = ?,
            version = version + 1, updated_at = ?
        WHERE id = ? AND status = 'candidate' AND version = ?
        """,
        (actor_id, timestamp, timestamp, workflow_id, int(expected_version)),
    )
    if cursor.rowcount != 1:
        current = get_merge_workflow(conn, workflow_id)
        if current["status"] == "confirmed":
            return current
        raise IdentityLifecycleError("merge_version_conflict", "合并流程已更新，请刷新后重试")
    write_audit_log(conn, "identity_merge_confirmed", actor_id, "identity_merge", workflow_id, {})
    return get_merge_workflow(conn, workflow_id)


def _record_and_move(conn, workflow: dict) -> int:
    workflow_id = workflow["id"]
    source_user_id = workflow["source_user_id"]
    target_user_id = workflow["target_user_id"]
    timestamp = now_iso()
    moved = 0
    for table, _label in USER_ID_TABLES:
        rows = conn.execute(f"SELECT id FROM {table} WHERE user_id = ?", (source_user_id,)).fetchall()
        for row in rows:
            conn.execute(
                """
                INSERT INTO identity_merge_record_links (
                    id, workflow_id, table_name, record_id, column_name,
                    source_user_id, target_user_id, created_at
                ) VALUES (?, ?, ?, ?, 'user_id', ?, ?, ?)
                """,
                (new_id("merge_link"), workflow_id, table, row["id"], source_user_id, target_user_id, timestamp),
            )
            conn.execute(f"UPDATE {table} SET user_id = ? WHERE id = ? AND user_id = ?", (target_user_id, row["id"], source_user_id))
            moved += 1
    target_anonymous_id = f"anon_{hashlib.sha256(target_user_id.encode('utf-8')).hexdigest()[:12]}"
    for table in ("student_profiles", "parent_assessment_submissions"):
        rows = conn.execute(
            f"SELECT id, anonymous_id FROM {table} WHERE user_id = ? AND anonymous_id <> ?",
            (target_user_id, target_anonymous_id),
        ).fetchall()
        for row in rows:
            conn.execute(
                """
                INSERT INTO identity_merge_record_links (
                    id, workflow_id, table_name, record_id, column_name,
                    source_user_id, target_user_id, source_value, target_value, created_at
                ) VALUES (?, ?, ?, ?, 'anonymous_id', ?, ?, ?, ?, ?)
                """,
                (
                    new_id("merge_link"),
                    workflow_id,
                    table,
                    row["id"],
                    source_user_id,
                    target_user_id,
                    row["anonymous_id"],
                    target_anonymous_id,
                    timestamp,
                ),
            )
            conn.execute(
                f"UPDATE {table} SET anonymous_id = ? WHERE id = ? AND anonymous_id = ?",
                (target_anonymous_id, row["id"], row["anonymous_id"]),
            )
    claim_rows = conn.execute(
        "SELECT id FROM data_claims WHERE target_user_id = ? AND status IN ('available', 'processing')",
        (source_user_id,),
    ).fetchall()
    for row in claim_rows:
        conn.execute(
            """
            INSERT INTO identity_merge_record_links (
                id, workflow_id, table_name, record_id, column_name,
                source_user_id, target_user_id, source_value, target_value, created_at
            ) VALUES (?, ?, 'data_claims', ?, 'target_user_id', ?, ?, ?, ?, ?)
            """,
            (
                new_id("merge_link"),
                workflow_id,
                row["id"],
                source_user_id,
                target_user_id,
                source_user_id,
                target_user_id,
                timestamp,
            ),
        )
        conn.execute(
            "UPDATE data_claims SET target_user_id = ?, updated_at = ? WHERE id = ? AND target_user_id = ?",
            (target_user_id, timestamp, row["id"], source_user_id),
        )
    for column_name in ("parent_user_id", "student_user_id"):
        rows = conn.execute(
            f"SELECT id FROM family_links WHERE {column_name} = ?",
            (source_user_id,),
        ).fetchall()
        for row in rows:
            conn.execute(
                """
                INSERT INTO identity_merge_record_links (
                    id, workflow_id, table_name, record_id, column_name,
                    source_user_id, target_user_id, created_at
                ) VALUES (?, ?, 'family_links', ?, ?, ?, ?, ?)
                """,
                (new_id("merge_link"), workflow_id, row["id"], column_name, source_user_id, target_user_id, timestamp),
            )
            conn.execute(
                f"UPDATE family_links SET {column_name} = ? WHERE id = ? AND {column_name} = ?",
                (target_user_id, row["id"], source_user_id),
            )
            moved += 1
    return moved


def execute_merge(
    conn,
    workflow_id: str,
    actor_id: str,
    expected_version: int,
    idempotency_key: str,
) -> dict:
    row = conn.execute("SELECT * FROM identity_merge_workflows WHERE id = ?", (workflow_id,)).fetchone()
    if row is None:
        raise IdentityLifecycleError("merge_not_found", "没有找到账号合并流程", 404)
    workflow = row_to_dict(row)
    if workflow["status"] in {"executed", "verified"} and workflow.get("execution_idempotency_key") == idempotency_key:
        return _public_workflow(workflow)
    if workflow["status"] != "confirmed":
        raise IdentityLifecycleError("merge_confirmation_required", "账号合并必须先经过人工确认")
    if int(workflow.get("version") or 0) != int(expected_version):
        raise IdentityLifecycleError("merge_version_conflict", "合并流程已更新，请刷新后重试")

    moved = _record_and_move(conn, workflow)
    timestamp = now_iso()
    rollback_until = (datetime.now(timezone.utc) + timedelta(hours=MERGE_ROLLBACK_HOURS)).isoformat()
    conn.execute(
        """
        UPDATE users
        SET status = 'merged', merged_into_user_id = ?, merged_at = ?,
            auth_epoch = auth_epoch + 1, updated_at = ?
        WHERE id = ?
        """,
        (workflow["target_user_id"], timestamp, timestamp, workflow["source_user_id"]),
    )
    cursor = conn.execute(
        """
        UPDATE identity_merge_workflows
        SET status = 'executed', execution_idempotency_key = ?, executed_at = ?,
            rollback_until = ?, version = version + 1, updated_at = ?
        WHERE id = ? AND status = 'confirmed' AND version = ?
        """,
        (idempotency_key, timestamp, rollback_until, timestamp, workflow_id, int(expected_version)),
    )
    if cursor.rowcount != 1:
        raise IdentityLifecycleError("merge_version_conflict", "合并流程已更新，请刷新后重试")
    write_audit_log(
        conn,
        "identity_merge_executed",
        actor_id,
        "identity_merge",
        workflow_id,
        {"moved_record_count": moved, "rollback_until": rollback_until, "target_role_preserved": True},
    )
    return get_merge_workflow(conn, workflow_id)


def verify_merge(conn, workflow_id: str, actor_id: str, expected_version: int) -> dict:
    workflow = get_merge_workflow(conn, workflow_id)
    if workflow["status"] == "verified":
        return workflow
    if workflow["status"] != "executed" or workflow["version"] != int(expected_version):
        raise IdentityLifecycleError("merge_version_conflict", "只有当前已执行版本可以核对")
    remaining = _merge_counts(conn, workflow["source_user_id"])
    source = conn.execute(
        "SELECT status, merged_into_user_id FROM users WHERE id = ?",
        (workflow["source_user_id"],),
    ).fetchone()
    verification = {
        "source_record_count": sum(remaining.values()),
        "source_marked_merged": bool(
            source is not None
            and source["status"] == "merged"
            and source["merged_into_user_id"] == workflow["target_user_id"]
        ),
    }
    if verification["source_record_count"] != 0 or not verification["source_marked_merged"]:
        raise IdentityLifecycleError("merge_verification_failed", "账号合并核对未通过，未改变当前数据")
    timestamp = now_iso()
    conn.execute(
        """
        UPDATE identity_merge_workflows
        SET status = 'verified', verification_json = ?, verified_at = ?,
            version = version + 1, updated_at = ?
        WHERE id = ? AND status = 'executed' AND version = ?
        """,
        (json_dumps(verification), timestamp, timestamp, workflow_id, int(expected_version)),
    )
    write_audit_log(conn, "identity_merge_verified", actor_id, "identity_merge", workflow_id, verification)
    return get_merge_workflow(conn, workflow_id)


def rollback_merge(
    conn,
    workflow_id: str,
    actor_id: str,
    expected_version: int,
    idempotency_key: str,
) -> dict:
    row = conn.execute("SELECT * FROM identity_merge_workflows WHERE id = ?", (workflow_id,)).fetchone()
    if row is None:
        raise IdentityLifecycleError("merge_not_found", "没有找到账号合并流程", 404)
    workflow = row_to_dict(row)
    if workflow["status"] == "rolled_back" and workflow.get("rollback_idempotency_key") == idempotency_key:
        return _public_workflow(workflow)
    if workflow["status"] not in {"executed", "verified"} or int(workflow.get("version") or 0) != int(expected_version):
        raise IdentityLifecycleError("merge_version_conflict", "只有当前已执行或已核对版本可以撤销")
    rollback_until = datetime.fromisoformat(str(workflow["rollback_until"]))
    if rollback_until <= datetime.now(timezone.utc):
        raise IdentityLifecycleError("merge_rollback_expired", "账号合并撤销窗口已结束")

    links = conn.execute(
        """
        SELECT * FROM identity_merge_record_links
        WHERE workflow_id = ? ORDER BY created_at DESC, id DESC
        """,
        (workflow_id,),
    ).fetchall()
    for link in links:
        if link["table_name"] != "data_claims":
            continue
        claim = conn.execute(
            "SELECT status FROM data_claims WHERE id = ?",
            (link["record_id"],),
        ).fetchone()
        if claim is not None and claim["status"] == "claimed":
            raise IdentityLifecycleError(
                "merge_rollback_conflict",
                "合并后已有匿名记录完成认领，需人工核对后处理",
            )
    restored = 0
    for link in links:
        table = link["table_name"]
        column = link["column_name"]
        if table not in {"family_links", "data_claims"} and table not in {item[0] for item in USER_ID_TABLES}:
            raise IdentityLifecycleError("merge_rollback_unsafe", "撤销清单包含未知数据表")
        if column not in {"user_id", "parent_user_id", "student_user_id", "target_user_id", "anonymous_id"}:
            raise IdentityLifecycleError("merge_rollback_unsafe", "撤销清单包含未知归属字段")
        current = conn.execute(f"SELECT {column} FROM {table} WHERE id = ?", (link["record_id"],)).fetchone()
        expected_target = link["target_value"] or link["target_user_id"]
        restore_source = link["source_value"] or link["source_user_id"]
        if current is None or current[column] != expected_target:
            raise IdentityLifecycleError("merge_rollback_conflict", "部分记录归属已再次变化，需人工处理")
        conn.execute(
            f"UPDATE {table} SET {column} = ? WHERE id = ? AND {column} = ?",
            (restore_source, link["record_id"], expected_target),
        )
        restored += 1
    timestamp = now_iso()
    conn.execute(
        """
        UPDATE users
        SET status = 'active', merged_into_user_id = NULL, merged_at = NULL,
            auth_epoch = auth_epoch + 1, updated_at = ?
        WHERE id = ?
        """,
        (timestamp, workflow["source_user_id"]),
    )
    conn.execute(
        """
        UPDATE identity_merge_workflows
        SET status = 'rolled_back', rollback_idempotency_key = ?, rolled_back_at = ?,
            version = version + 1, updated_at = ?
        WHERE id = ? AND version = ?
        """,
        (idempotency_key, timestamp, timestamp, workflow_id, int(expected_version)),
    )
    write_audit_log(
        conn,
        "identity_merge_rolled_back",
        actor_id,
        "identity_merge",
        workflow_id,
        {"restored_record_count": restored, "history_preserved": True},
    )
    return get_merge_workflow(conn, workflow_id)
