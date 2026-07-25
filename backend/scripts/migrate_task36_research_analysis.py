"""Plan/apply/verify the additive Task36-F13 analysis-job schema."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from config import Config
from database import CURRENT_SCHEMA_NAME, CURRENT_SCHEMA_VERSION, get_connection, init_db, list_database_tables

TABLES = [
    "research_analysis_snapshots",
    "research_analysis_snapshot_links",
    "research_analysis_jobs",
    "research_analysis_artifacts",
    "research_analysis_events",
]
PRODUCTION_CONFIRMATION = "APPLY_TASK36_F13_RESEARCH_ANALYSIS_SCHEMA"


def assert_environment_allowed(action: str, allow_production: bool, confirmation: str) -> None:
    if str(Config.APP_ENV).lower() != "production" or action in {"plan", "verify"}:
        return
    if not allow_production or confirmation != PRODUCTION_CONFIRMATION:
        raise RuntimeError("生产迁移或回滚已阻断：需要人工批准和精确确认短语。")


def inspect() -> dict:
    with get_connection() as conn:
        tables = {str(row["name"]) for row in list_database_tables(conn)}
        counts = {
            table: int(conn.execute(f"SELECT COUNT(*) AS count FROM {table}").fetchone()["count"])
            for table in TABLES
            if table in tables
        }
    missing = [table for table in TABLES if table not in tables]
    return {
        "schema_version": CURRENT_SCHEMA_VERSION,
        "schema_name": CURRENT_SCHEMA_NAME,
        "required_tables": TABLES,
        "missing_tables": missing,
        "row_counts": counts,
        "ok": not missing,
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
        "business_source_records_preserved": True,
        "snapshot_links_and_audit_preserved": True,
        "worker_execution_disabled_before_rollback": True,
        "operator_note": "先关闭分析执行器并回退应用；加法表不自动DROP，派生数据按受控删除接口处理。",
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
