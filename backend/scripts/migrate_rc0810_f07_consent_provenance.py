"""Backfill unknown provenance without claiming legacy consent was self-recorded."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


BACKEND = Path(__file__).resolve().parents[1]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from config import Config
from database import get_connection, json_loads, now_iso, write_audit_log


MIGRATION_ACTOR = "migration-rc0810-f07"
PRODUCTION_CONFIRMATION = "APPLY_RC0810_F07_CONSENT_PROVENANCE"


def assert_environment_allowed(allow_production: bool = False, confirmation: str = "") -> None:
    if str(Config.APP_ENV).lower() != "production":
        return
    if not allow_production or confirmation != PRODUCTION_CONFIRMATION:
        raise RuntimeError("生产迁移已阻断：需要人工批准和精确确认短语。")


def build_plan(conn) -> dict:
    rows = conn.execute(
        """
        SELECT id FROM consent_records
        WHERE subject_id IS NULL
        ORDER BY user_id, consent_type, created_at, id
        """
    ).fetchall()
    return {
        "pending_count": len(rows),
        "record_ids": [str(row["id"]) for row in rows],
        "backfill_source": "provenance_unknown",
    }


def apply_backfill(conn) -> dict:
    plan = build_plan(conn)
    updated_ids = []
    for record_id in plan["record_ids"]:
        row = conn.execute(
            "SELECT user_id, consent_type, event_version FROM consent_records WHERE id = ?",
            (record_id,),
        ).fetchone()
        if row is None:
            continue
        current_max = conn.execute(
            """
            SELECT MAX(event_version) AS max_version FROM consent_records
            WHERE subject_id = ? AND consent_type = ?
            """,
            (row["user_id"], row["consent_type"]),
        ).fetchone()
        next_version = int(current_max["max_version"] or 0) + 1
        cursor = conn.execute(
            """
            UPDATE consent_records
            SET subject_id = user_id, source = 'provenance_unknown',
                event_type = 'provenance_unknown', event_version = ?
            WHERE id = ? AND subject_id IS NULL
            """,
            (next_version, record_id),
        )
        if cursor.rowcount != 1:
            continue
        write_audit_log(
            conn,
            "consent_provenance_backfilled",
            MIGRATION_ACTOR,
            "consent_record",
            record_id,
            {
                "previous_subject_id": None,
                "previous_event_version": int(row["event_version"] or 1),
                "new_event_version": next_version,
                "source": "provenance_unknown",
                "actor_verified": False,
            },
        )
        updated_ids.append(record_id)
    conn.commit()
    return {
        "updated_count": len(updated_ids),
        "updated_ids": updated_ids,
        "post_plan": build_plan(conn),
    }


def verify(conn) -> dict:
    missing = int(
        conn.execute(
            "SELECT COUNT(*) AS count FROM consent_records WHERE subject_id IS NULL"
        ).fetchone()["count"]
        or 0
    )
    false_self = int(
        conn.execute(
            """
            SELECT COUNT(*) AS count FROM consent_records
            WHERE source = 'provenance_unknown'
              AND (actor_id IS NOT NULL OR event_type IN ('self_agreed', 'self_withdrawn'))
            """
        ).fetchone()["count"]
        or 0
    )
    return {
        "ok": missing == 0 and false_self == 0,
        "missing_subject_count": missing,
        "false_self_provenance_count": false_self,
    }


def rollback_backfill(conn) -> dict:
    rows = conn.execute(
        """
        SELECT id, target_id, metadata_json FROM audit_logs
        WHERE actor_id = ? AND action = 'consent_provenance_backfilled'
        ORDER BY created_at DESC
        """,
        (MIGRATION_ACTOR,),
    ).fetchall()
    restored = []
    for row in rows:
        metadata = json_loads(row["metadata_json"], {})
        if metadata.get("previous_subject_id") is not None:
            continue
        cursor = conn.execute(
            """
            UPDATE consent_records SET subject_id = NULL, event_version = ?
            WHERE id = ? AND source = 'provenance_unknown'
              AND actor_id IS NULL AND event_type = 'provenance_unknown'
            """,
            (int(metadata.get("previous_event_version") or 1), row["target_id"]),
        )
        if cursor.rowcount == 1:
            restored.append(str(row["target_id"]))
        conn.execute("DELETE FROM audit_logs WHERE id = ?", (row["id"],))
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
