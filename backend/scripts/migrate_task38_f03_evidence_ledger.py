"""Plan/apply/verify the additive Task38-F03 evidence ledger."""

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


TABLE = "therapeutic_assessment_evidence_items"
PRODUCTION_CONFIRMATION = "APPLY_TASK38_F03_EVIDENCE_LEDGER"


def _guard(action: str, allow_production: bool, confirmation: str) -> None:
    if str(Config.APP_ENV).lower() != "production" or action in {"plan", "verify", "rollback"}:
        return
    if not allow_production or confirmation != PRODUCTION_CONFIRMATION:
        raise RuntimeError("生产迁移已阻断：需要独立批准和精确确认短语")


def inspect() -> dict:
    with get_connection() as conn:
        tables = {str(row["name"]) for row in list_database_tables(conn)}
        count = int(conn.execute(f"SELECT COUNT(*) AS count FROM {TABLE}").fetchone()["count"]) if TABLE in tables else 0
    return {
        "schema_version": CURRENT_SCHEMA_VERSION,
        "schema_name": CURRENT_SCHEMA_NAME,
        "table": TABLE,
        "table_ok": TABLE in tables,
        "row_count": count,
        "additive_only": True,
        "ok": TABLE in tables,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["plan", "apply", "verify", "rollback"])
    parser.add_argument("--allow-production", action="store_true")
    parser.add_argument("--confirmation", default="")
    args = parser.parse_args()
    _guard(args.action, args.allow_production, args.confirmation)
    if args.action == "apply":
        init_db()
        result = {"action": "apply", **inspect(), "production_mutation": str(Config.APP_ENV).lower() == "production"}
    elif args.action == "rollback":
        result = {
            "action": "rollback",
            "schema_preserved": True,
            "table_dropped": False,
            "production_mutation": False,
            "operator_note": "先关闭证据账本写入并回退应用；证据与审计不自动删除。",
        }
    else:
        result = {"action": args.action, **inspect(), "production_mutation": False}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("ok", True) else 1


if __name__ == "__main__":
    raise SystemExit(main())
