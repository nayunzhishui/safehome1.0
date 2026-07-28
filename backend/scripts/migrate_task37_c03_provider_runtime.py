"""Additive migration and verification for Task37-C03 provider metadata."""

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


TABLE = "ai_qa_provider_events"
REQUIRED_COLUMNS = {
    "provider_request_id",
    "input_tokens",
    "output_tokens",
    "cost_currency",
}
CONFIRMATION = "APPLY_TASK37_C03_PROVIDER_RUNTIME"


def inspect() -> dict:
    with get_connection() as conn:
        tables = {row["name"] for row in list_database_tables(conn)}
        columns = (
            {row["name"] for row in list_database_columns(conn, TABLE)}
            if TABLE in tables
            else set()
        )
    return {
        "ok": TABLE in tables and REQUIRED_COLUMNS.issubset(columns),
        "schema_version": CURRENT_SCHEMA_VERSION,
        "schema_name": CURRENT_SCHEMA_NAME,
        "missing_tables": [] if TABLE in tables else [TABLE],
        "missing_columns": sorted(REQUIRED_COLUMNS - columns),
        "raw_text_columns_present": sorted(
            {"request_text", "response_text"} & columns
        ),
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
            "columns_dropped": False,
            "provider_events_deleted": False,
            "real_provider_enabled": False,
            "application_rollback_required": True,
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
    if result.get("raw_text_columns_present"):
        result["ok"] = False
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
