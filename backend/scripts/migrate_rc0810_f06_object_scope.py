"""Backfill bounded expiry for RC0810-F06 object-scope assignments."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path


BACKEND = Path(__file__).resolve().parents[1]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from config import Config
from database import get_connection, json_dumps, json_loads, new_id, now_iso


MIGRATION_ACTOR = "migration-rc0810-f06"
PRODUCTION_CONFIRMATION = "APPLY_RC0810_F06_PRODUCTION_OBJECT_SCOPE_EXPIRY"
DEFAULT_EXPIRY_DAYS = 30


def assert_environment_allowed(allow_production: bool = False, confirmation: str = "") -> None:
    if str(Config.APP_ENV).lower() != "production":
        return
    if not allow_production or confirmation != PRODUCTION_CONFIRMATION:
        raise RuntimeError("生产迁移已阻断：需要人工批准和精确确认短语。")


def build_plan(conn) -> dict:
    rows = conn.execute(
        """
        SELECT id FROM research_scope_assignments
        WHERE status = 'active' AND expires_at IS NULL
        ORDER BY id
        """
    ).fetchall()
    return {
        "pending_expiry_count": len(rows),
        "assignment_ids": [str(row["id"]) for row in rows],
        "default_expiry_days": DEFAULT_EXPIRY_DAYS,
    }


def apply_backfill(conn) -> dict:
    plan = build_plan(conn)
    expires_at = (
        datetime.now(timezone.utc) + timedelta(days=DEFAULT_EXPIRY_DAYS)
    ).isoformat()
    updated_ids = []
    for assignment_id in plan["assignment_ids"]:
        cursor = conn.execute(
            """
            UPDATE research_scope_assignments
            SET expires_at = ?, updated_at = ?
            WHERE id = ? AND status = 'active' AND expires_at IS NULL
            """,
            (expires_at, now_iso(), assignment_id),
        )
        if cursor.rowcount != 1:
            continue
        result = {"previous_expires_at": None, "new_expires_at": expires_at}
        conn.execute(
            """
            INSERT INTO research_scope_assignment_actions (
                id, assignment_id, actor_id, action, idempotency_key,
                request_hash, result_json, created_at
            ) VALUES (?, ?, ?, 'expiry_backfill', ?, ?, ?, ?)
            """,
            (
                new_id("research_scope_action"),
                assignment_id,
                MIGRATION_ACTOR,
                f"rc0810-f06-expiry-{assignment_id}",
                hashlib.sha256(assignment_id.encode("utf-8")).hexdigest(),
                json_dumps(result),
                now_iso(),
            ),
        )
        updated_ids.append(assignment_id)
    conn.commit()
    return {
        "updated_count": len(updated_ids),
        "updated_ids": updated_ids,
        "post_plan": build_plan(conn),
    }


def verify(conn) -> dict:
    pending = build_plan(conn)["pending_expiry_count"]
    invalid = conn.execute(
        """
        SELECT COUNT(*) AS count FROM research_scope_assignments
        WHERE assignment_role NOT IN ('researcher', 'supervisor')
           OR status NOT IN ('active', 'revoked') OR version < 1
        """
    ).fetchone()
    return {
        "ok": pending == 0 and int(invalid["count"] or 0) == 0,
        "pending_expiry_count": pending,
        "invalid_assignment_count": int(invalid["count"] or 0),
    }


def rollback_backfill(conn) -> dict:
    rows = conn.execute(
        """
        SELECT id, assignment_id, result_json
        FROM research_scope_assignment_actions
        WHERE actor_id = ? AND action = 'expiry_backfill'
        ORDER BY created_at DESC
        """,
        (MIGRATION_ACTOR,),
    ).fetchall()
    restored = []
    for row in rows:
        result = json_loads(row["result_json"], {})
        cursor = conn.execute(
            """
            UPDATE research_scope_assignments
            SET expires_at = NULL, updated_at = ?
            WHERE id = ? AND expires_at = ?
            """,
            (now_iso(), row["assignment_id"], result.get("new_expires_at")),
        )
        if cursor.rowcount == 1:
            restored.append(str(row["assignment_id"]))
        conn.execute(
            "DELETE FROM research_scope_assignment_actions WHERE id = ?",
            (row["id"],),
        )
    conn.commit()
    return {"restored_count": len(restored), "restored_ids": restored}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["plan", "apply", "verify", "rollback"])
    parser.add_argument("--allow-production", action="store_true")
    parser.add_argument("--confirmation", default="")
    args = parser.parse_args()
    assert_environment_allowed(args.allow_production, args.confirmation)
    with get_connection() as conn:
        if args.action == "plan":
            result = build_plan(conn)
        elif args.action == "apply":
            result = apply_backfill(conn)
        elif args.action == "verify":
            result = verify(conn)
        else:
            result = rollback_backfill(conn)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("ok", True) else 1


if __name__ == "__main__":
    raise SystemExit(main())
