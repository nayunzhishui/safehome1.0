"""Additive migration and verification for Task37-C07 AI review workbench."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from config import Config  # noqa: E402
from database import (  # noqa: E402
    CURRENT_SCHEMA_NAME,
    CURRENT_SCHEMA_VERSION,
    get_connection,
    init_db,
    list_database_columns,
    list_database_tables,
)


REQUIRED_COLUMNS = {
    "ai_qa_review_cases": {
        "id",
        "message_id",
        "candidate_sha256",
        "citations_json",
        "scope_json",
        "source_snapshot_hash",
        "required_task_code",
        "required_competency",
        "formal_feedback_written",
        "version",
    },
    "ai_qa_review_actions": {
        "id",
        "review_case_id",
        "actor_id",
        "decision",
        "before_version",
        "after_version",
        "request_sha256",
        "idempotency_key",
    },
}
CONFIRMATION = "APPLY_TASK37_C07_AI_REVIEW_WORKBENCH"


def inspect() -> dict:
    with get_connection() as conn:
        tables = {row["name"] for row in list_database_tables(conn)}
        missing_columns = {}
        for table, expected in REQUIRED_COLUMNS.items():
            actual = (
                {
                    row["name"]
                    for row in list_database_columns(conn, table)
                }
                if table in tables
                else set()
            )
            missing = sorted(expected - actual)
            if missing:
                missing_columns[table] = missing
    missing_tables = sorted(set(REQUIRED_COLUMNS) - tables)
    return {
        "ok": not missing_tables and not missing_columns,
        "schema_version": CURRENT_SCHEMA_VERSION,
        "schema_name": CURRENT_SCHEMA_NAME,
        "missing_tables": missing_tables,
        "missing_columns": missing_columns,
        "additive_only": True,
        "formal_feedback_write_enabled": False,
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
        result = {
            "action": "apply",
            **inspect(),
            "production_mutation": production,
        }
    elif args.action == "verify":
        result = {
            "action": "verify",
            **inspect(),
            "production_mutation": False,
        }
    elif args.action == "rollback":
        result = {
            "action": "rollback",
            "ok": True,
            "tables_dropped": False,
            "review_data_deleted": False,
            "disable_review_routes_required": True,
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
