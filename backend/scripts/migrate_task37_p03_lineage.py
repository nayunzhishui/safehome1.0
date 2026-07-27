"""Plan/apply/verify additive Task37-P03 lineage schema."""

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
    "computation_datasets",
    "computation_authorization_snapshots",
    "computation_lineage_edges",
    "computation_deletion_tombstones",
    "computation_legal_holds",
]
PRODUCTION_CONFIRMATION = "APPLY_TASK37_P03_LINEAGE_SCHEMA"


def _guard(action: str, allow_production: bool, confirmation: str) -> None:
    if str(Config.APP_ENV).lower() != "production" or action in {"plan", "verify", "rollback"}:
        return
    if not allow_production or confirmation != PRODUCTION_CONFIRMATION:
        raise RuntimeError("生产迁移已阻断：需要独立批准和精确确认短语")


def inspect() -> dict:
    with get_connection() as conn:
        existing = {row["name"] for row in list_database_tables(conn)}
        counts = {
            table: int(conn.execute(f"SELECT COUNT(*) AS count FROM {table}").fetchone()["count"])
            for table in TABLES
            if table in existing
        }
    missing = [table for table in TABLES if table not in existing]
    return {
        "schema_version": CURRENT_SCHEMA_VERSION,
        "schema_name": CURRENT_SCHEMA_NAME,
        "tables": TABLES,
        "missing_tables": missing,
        "row_counts": counts,
        "ok": not missing,
    }


def apply() -> dict:
    init_db()
    return {"action": "apply", **inspect(), "production_mutation": str(Config.APP_ENV).lower() == "production"}


def rollback() -> dict:
    return {
        "action": "rollback",
        "schema_preserved": True,
        "tables_dropped": False,
        "production_mutation": False,
        "operator_note": "先关闭新写入并回退应用；加法表、血缘、墓碑和审计不自动DROP。",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["plan", "apply", "verify", "rollback"])
    parser.add_argument("--allow-production", action="store_true")
    parser.add_argument("--confirmation", default="")
    args = parser.parse_args()
    _guard(args.action, args.allow_production, args.confirmation)
    if args.action == "apply":
        result = apply()
    elif args.action == "rollback":
        result = rollback()
    else:
        result = {"action": args.action, **inspect(), "production_mutation": False}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("ok", True) else 1


if __name__ == "__main__":
    raise SystemExit(main())
