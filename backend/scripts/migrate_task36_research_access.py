"""Plan, apply, verify or roll back the task-36 F03 assignment backfill.

This script never connects to production unless both --allow-production and
the exact confirmation phrase are supplied. Rollback revokes only rows created
by this backfill and retains the legacy assigned_researcher_id field.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


BACKEND = Path(__file__).resolve().parents[1]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from config import Config
from database import get_connection, new_id, now_iso, row_to_dict


MIGRATION_ACTOR = "migration-task36-f03"
PRODUCTION_CONFIRMATION = "APPLY_TASK36_F03_PRODUCTION_ASSIGNMENT_BACKFILL"


def assert_environment_allowed(allow_production: bool = False, confirmation: str = "") -> None:
    if str(Config.APP_ENV).lower() != "production":
        return
    if not allow_production or confirmation != PRODUCTION_CONFIRMATION:
        raise RuntimeError("生产回填已阻断：需要人工批准和精确确认短语。")


def build_plan(conn) -> dict:
    rows = conn.execute(
        """
        SELECT id, assigned_researcher_id
        FROM relationship_pilot_enrollments
        WHERE assigned_researcher_id IS NOT NULL AND assigned_researcher_id <> ''
        ORDER BY id
        """
    ).fetchall()
    pending = []
    for row in rows:
        existing = conn.execute(
            """
            SELECT id FROM research_scope_assignments
            WHERE enrollment_id = ? AND actor_id = ? AND assignment_role = 'researcher'
              AND status = 'active' LIMIT 1
            """,
            (row["id"], row["assigned_researcher_id"]),
        ).fetchone()
        if not existing:
            pending.append({"enrollment_id": row["id"], "actor_id": row["assigned_researcher_id"]})
    return {"legacy_assigned_count": len(rows), "pending_backfill_count": len(pending), "items": pending}


def apply_backfill(conn) -> dict:
    plan = build_plan(conn)
    timestamp = now_iso()
    created_ids = []
    for item in plan["items"]:
        assignment_id = new_id("research_scope")
        conn.execute(
            """
            INSERT INTO research_scope_assignments (
                id, enrollment_id, actor_id, assignment_role, status, version,
                idempotency_key, assigned_by, created_at, updated_at
            ) VALUES (?, ?, ?, 'researcher', 'active', 1, ?, ?, ?, ?)
            """,
            (
                assignment_id,
                item["enrollment_id"],
                item["actor_id"],
                f"backfill-{item['enrollment_id']}-{item['actor_id']}",
                MIGRATION_ACTOR,
                timestamp,
                timestamp,
            ),
        )
        created_ids.append(assignment_id)
    conn.commit()
    return {"created_count": len(created_ids), "created_ids": created_ids, "post_plan": build_plan(conn)}


def verify(conn) -> dict:
    plan = build_plan(conn)
    invalid = conn.execute(
        """
        SELECT COUNT(*) AS count FROM research_scope_assignments
        WHERE assignment_role NOT IN ('researcher', 'supervisor')
           OR status NOT IN ('active', 'revoked') OR version < 1
        """
    ).fetchone()
    return {
        "ok": plan["pending_backfill_count"] == 0 and int(invalid["count"] or 0) == 0,
        "pending_backfill_count": plan["pending_backfill_count"],
        "invalid_assignment_count": int(invalid["count"] or 0),
    }


def rollback_backfill(conn) -> dict:
    timestamp = now_iso()
    rows = conn.execute(
        "SELECT * FROM research_scope_assignments WHERE assigned_by = ? AND status = 'active'",
        (MIGRATION_ACTOR,),
    ).fetchall()
    for row in rows:
        conn.execute(
            """
            UPDATE research_scope_assignments
            SET status = 'revoked', version = version + 1, revoked_at = ?, updated_at = ?
            WHERE id = ?
            """,
            (timestamp, timestamp, row["id"]),
        )
    conn.commit()
    return {"revoked_count": len(rows), "legacy_fields_preserved": True}


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
