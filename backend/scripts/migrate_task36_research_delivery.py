"""Plan, apply, verify or safely roll back the Task36-F06 delivery schema.

Production mutation requires an explicit human gate. Rollback is deliberately
additive and never drops delivery tables, message columns or historical rows.
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
from database import CURRENT_SCHEMA_VERSION, get_connection, init_db, list_database_columns, list_database_tables


TABLES = ["research_delivery_workflows", "research_delivery_versions", "research_delivery_events"]
MESSAGE_COLUMNS = ["delivery_id", "delivery_version", "withdrawn_at"]
PRODUCTION_CONFIRMATION = "APPLY_TASK36_F06_RESEARCH_DELIVERY_SCHEMA"


def assert_environment_allowed(action: str, allow_production: bool, confirmation: str) -> None:
    if str(Config.APP_ENV).lower() != "production" or action in {"plan", "verify"}:
        return
    if not allow_production or confirmation != PRODUCTION_CONFIRMATION:
        raise RuntimeError("生产迁移或回滚已阻断：需要人工批准和精确确认短语。")


def inspect() -> dict:
    with get_connection() as conn:
        tables = {str(row["name"]) for row in list_database_tables(conn)}
        message_columns = {str(row["name"]) for row in list_database_columns(conn, "messages")} if "messages" in tables else set()
        row_counts = {
            table: int(conn.execute(f"SELECT COUNT(*) AS count FROM {table}").fetchone()["count"])
            for table in TABLES
            if table in tables
        }
    missing_tables = [table for table in TABLES if table not in tables]
    missing_columns = [column for column in MESSAGE_COLUMNS if column not in message_columns]
    return {
        "schema_version": CURRENT_SCHEMA_VERSION,
        "missing_tables": missing_tables,
        "missing_message_columns": missing_columns,
        "row_counts": row_counts,
        "ok": not missing_tables and not missing_columns,
    }


def apply() -> dict:
    init_db()
    return {"action": "apply", **inspect()}


def rollback() -> dict:
    snapshot = inspect()
    return {
        "action": "rollback",
        "schema_preserved": True,
        "row_counts": snapshot["row_counts"],
        "application_rollback_compatible": True,
        "message_delivery_columns_preserved": True,
        "message_and_report_history_preserved": True,
        "operator_note": "回退应用版本即可；新增表列为向后兼容的加法迁移，不执行DROP。",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["plan", "apply", "verify", "rollback"])
    parser.add_argument("--allow-production", action="store_true")
    parser.add_argument("--confirmation", default="")
    args = parser.parse_args()
    assert_environment_allowed(args.action, args.allow_production, args.confirmation)
    if args.action == "plan":
        result = {"action": "plan", **inspect(), "production_mutation": False}
    elif args.action == "apply":
        result = apply()
    elif args.action == "verify":
        result = {"action": "verify", **inspect()}
    else:
        result = rollback()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("ok", True) else 1


if __name__ == "__main__":
    raise SystemExit(main())
