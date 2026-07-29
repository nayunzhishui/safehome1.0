"""Additive Task38-F24 stop, recovery evidence and rollback migration."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from config import Config
from database import (
    CURRENT_SCHEMA_NAME,
    CURRENT_SCHEMA_VERSION,
    get_connection,
    init_db,
    list_database_tables,
)

TABLES = {
    "therapeutic_assessment_stop_incidents",
    "therapeutic_assessment_recovery_evidence",
}
INDEXES = {
    "idx_therapeutic_stop_incidents_status_created",
    "idx_therapeutic_recovery_evidence_incident_status",
    "idx_therapeutic_recovery_verifier_idempotency",
}
CONFIRMATION = "APPLY_TASK38_F24_STOP_RECOVERY"


def _content_ready() -> bool:
    try:
        policy = json.loads(
            (
                Path(Config.CONTENT_DIR)
                / "therapeutic_assessment_stop_recovery_policy.json"
            ).read_text(encoding="utf-8")
        )
    except (OSError, json.JSONDecodeError):
        return False
    return bool(
        len(policy.get("immediate_pause_triggers") or []) == 7
        and len(policy.get("recovery_gates") or []) == 7
        and len(policy.get("rollback_matrix") or []) == 8
        and policy.get("production_release_approved") is False
    )


def inspect() -> dict:
    with get_connection() as conn:
        existing_tables = {row["name"] for row in list_database_tables(conn)}
        existing_indexes = {
            row["name"]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'index'"
            ).fetchall()
        }
    missing_tables = sorted(TABLES - existing_tables)
    missing_indexes = sorted(INDEXES - existing_indexes)
    content_ready = _content_ready()
    return {
        "ok": not missing_tables and not missing_indexes and content_ready,
        "schema_version": CURRENT_SCHEMA_VERSION,
        "schema_name": CURRENT_SCHEMA_NAME,
        "missing_tables": missing_tables,
        "missing_indexes": missing_indexes,
        "content_ready": content_ready,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["plan", "apply", "verify", "rollback"])
    parser.add_argument("--database-path", default="")
    parser.add_argument("--allow-production", action="store_true")
    parser.add_argument("--confirmation", default="")
    args = parser.parse_args()
    if args.database_path:
        Config.DATABASE_PATH = Path(args.database_path).resolve()
    production = str(Config.APP_ENV).lower() == "production"
    if production and args.action == "apply" and (
        not args.allow_production or args.confirmation != CONFIRMATION
    ):
        raise RuntimeError("生产迁移已阻断：需要独立批准和精确确认短语")
    if args.action == "apply":
        init_db()
        result = {"action": "apply", **inspect(), "production_mutation": production}
    elif args.action == "verify":
        result = {"action": "verify", **inspect(), "production_mutation": False}
    elif args.action == "rollback":
        result = {
            "action": "rollback",
            "ok": True,
            "schema_preserved": True,
            "tables_dropped": False,
            "incident_history_deleted": False,
            "recovery_evidence_deleted": False,
            "runtime_reactivated": False,
            "production_mutation": False,
        }
    else:
        current = inspect()
        result = {
            "action": "plan",
            "ok": True,
            "already_applied": current["ok"],
            "current_state": current,
            "additive_only": True,
            "production_mutation": False,
        }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
