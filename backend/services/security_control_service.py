"""Task 31 security, privacy, and abuse-control evidence service."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from flask import current_app, g

from database import get_connection, json_dumps, json_loads, new_id, now_iso, row_to_dict, rows_to_dicts, write_audit_log
from scripts.generate_task31_security_registry import build_registry
from scripts.scan_task31_security import run_scan


ROOT = Path(__file__).resolve().parents[2]
TASK36_REGISTRY_PATH = ROOT / "content" / "task36_reliability_security_registry.json"
ALLOWED_ACCOUNT_STATUSES = {"active", "disabled"}
ALLOWED_REASON_CODES = {"security_review", "role_change", "credential_rotation", "account_recovery", "owner_request"}


class SecurityControlError(ValueError):
    def __init__(self, code: str, message: str, status: int = 400, details: dict | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.status = status
        self.details = details or {}


def _registry() -> dict:
    # Authorization matrix is derived from the machine API contract on every
    # load.  The historical JSON remains an offline governance snapshot only.
    return build_registry()


def _task36_registry() -> dict:
    return json.loads(TASK36_REGISTRY_PATH.read_text(encoding="utf-8"))


def _registry_hash(payload: dict) -> str:
    return hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()


def _expand_json(item: dict) -> dict:
    for key in ("summary_json", "metadata_json"):
        if key in item:
            item[key.removesuffix("_json")] = json_loads(item.pop(key), {})
    return item


def _expand_verification(item: dict) -> dict:
    item["verification"] = json_loads(item.pop("verification_json", None), {})
    item.pop("subject_hash", None)
    return item


def record_security_event(
    event_type: str,
    severity: str,
    *,
    actor_id: str | None = None,
    target_type: str | None = None,
    target_id: str | None = None,
    metadata: dict | None = None,
) -> str:
    allowed_metadata = {
        key: value for key, value in (metadata or {}).items()
        if key in {"reason_code", "status", "source", "failure_count", "scope", "operation_id"}
    }
    event_id = new_id("security_event")
    with get_connection() as conn:
        conn.execute(
            """INSERT INTO security_events
               (id, actor_id, event_type, severity, target_type, target_id, request_id,
                metadata_json, status, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'open', ?)""",
            (
                event_id,
                actor_id,
                event_type,
                severity,
                target_type,
                target_id,
                getattr(g, "request_id", None),
                json_dumps(allowed_metadata),
                now_iso(),
            ),
        )
        conn.commit()
    return event_id


def public_status() -> dict:
    registry = _registry()
    summary = registry["authorization_summary"]
    return {
        "status": registry["status"],
        "engineering_controls_ready": True,
        "formal_permission_acceptance_passed": False,
        "temporary_showcase_exception_enabled": bool(registry["temporary_showcase_exception"]["enabled"]),
        "operation_count": summary["operation_count"],
        "participant_ai_enabled": False,
        "boundary_notice": "工程防护不等于正式安全、隐私、伦理或生产批准。临时展示越权仍阻断正式权限验收。",
    }


def workbench() -> dict:
    registry = _registry()
    with get_connection() as conn:
        runs = rows_to_dicts(conn.execute("SELECT * FROM security_control_runs ORDER BY created_at DESC LIMIT 20").fetchall())
        events = rows_to_dicts(conn.execute("SELECT * FROM security_events ORDER BY created_at DESC LIMIT 50").fetchall())
        deletion_verifications = rows_to_dicts(
            conn.execute("SELECT * FROM privacy_deletion_verifications ORDER BY verified_at DESC LIMIT 20").fetchall()
        )
    return {
        "registry": registry,
        "task36_integration": _task36_registry(),
        "registry_hash": _registry_hash(registry),
        "runs": [_expand_json(item) for item in runs],
        "events": [_expand_json(item) for item in events],
        "deletion_verifications": [_expand_verification(item) for item in deletion_verifications],
        "scan_execution_enabled": bool(current_app.config.get("SECURITY_SCAN_EXECUTION_ENABLED", False)),
        "formal_permission_acceptance_passed": False,
    }


def run_security_scan(actor: dict) -> dict:
    if not current_app.config.get("SECURITY_SCAN_EXECUTION_ENABLED", False):
        raise SecurityControlError("security_scan_disabled", "当前环境未开启安全扫描执行；仍可读取已有工程证据。", 503)
    registry = _registry()
    result = run_scan(ROOT)
    run_id = new_id("security_run")
    timestamp = now_iso()
    with get_connection() as conn:
        conn.execute(
            """INSERT INTO security_control_runs
               (id, actor_id, registry_version, registry_hash, mode, status,
                summary_json, artifact_hash, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                run_id,
                actor["id"],
                registry["version"],
                _registry_hash(registry),
                result["mode"],
                "passed" if result["hard_checks_passed"] else "failed",
                json_dumps(result),
                result["artifact_hash"],
                timestamp,
            ),
        )
        write_audit_log(
            conn,
            "security_scan_run",
            actor["id"],
            "security_control_run",
            run_id,
            {"status": "passed" if result["hard_checks_passed"] else "failed", "blocker_count": len(result["blockers"])},
        )
        conn.commit()
    return {"id": run_id, "created_at": timestamp, **result}


def set_account_status(actor: dict, user_id: str, payload: dict) -> dict:
    desired = str(payload.get("status") or "").strip()
    reason_code = str(payload.get("reason_code") or "").strip()
    expected_epoch = payload.get("expected_auth_epoch")
    if desired not in ALLOWED_ACCOUNT_STATUSES:
        raise SecurityControlError("validation_error", "status 只能是 active 或 disabled。")
    if reason_code not in ALLOWED_REASON_CODES:
        raise SecurityControlError("validation_error", "需要选择受控的账号状态原因。")
    if user_id == actor.get("id") and desired == "disabled":
        raise SecurityControlError("self_disable_forbidden", "管理员不能在此处停用自己的账号。", 409)
    timestamp = now_iso()
    with get_connection() as conn:
        row = conn.execute("SELECT id, role, status, auth_epoch FROM users WHERE id = ?", (user_id,)).fetchone()
        if row is None:
            raise SecurityControlError("not_found", "没有找到该账号。", 404)
        item = row_to_dict(row)
        if expected_epoch is not None and int(expected_epoch) != int(item.get("auth_epoch") or 0):
            raise SecurityControlError("state_conflict", "账号状态已变化，请刷新后重试。", 409)
        if item.get("status") == desired:
            return {**item, "already_applied": True, "tokens_revoked": desired == "disabled"}
        conn.execute(
            "UPDATE users SET status = ?, status_reason = ?, auth_epoch = auth_epoch + 1, updated_at = ? WHERE id = ?",
            (desired, reason_code, timestamp, user_id),
        )
        write_audit_log(
            conn,
            "account_status_changed",
            actor["id"],
            "user",
            user_id,
            {"status": desired, "reason_code": reason_code, "tokens_revoked": True},
        )
        conn.commit()
        updated = conn.execute("SELECT id, role, status, auth_epoch, status_reason, updated_at FROM users WHERE id = ?", (user_id,)).fetchone()
    record_security_event(
        "account_disabled" if desired == "disabled" else "account_reactivated",
        "high" if desired == "disabled" else "medium",
        actor_id=actor["id"],
        target_type="user",
        target_id=user_id,
        metadata={"status": desired, "reason_code": reason_code},
    )
    return {**row_to_dict(updated), "already_applied": False, "tokens_revoked": True}


def resolve_security_event(actor: dict, event_id: str) -> dict:
    timestamp = now_iso()
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM security_events WHERE id = ?", (event_id,)).fetchone()
        if row is None:
            raise SecurityControlError("not_found", "没有找到该安全事件。", 404)
        if row["status"] == "resolved":
            return _expand_json(row_to_dict(row))
        conn.execute(
            "UPDATE security_events SET status = 'resolved', resolved_by = ?, resolved_at = ? WHERE id = ?",
            (actor["id"], timestamp, event_id),
        )
        write_audit_log(conn, "security_event_resolved", actor["id"], "security_event", event_id, {})
        conn.commit()
        updated = conn.execute("SELECT * FROM security_events WHERE id = ?", (event_id,)).fetchone()
    return _expand_json(row_to_dict(updated))
