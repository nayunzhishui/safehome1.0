"""Plan/apply/verify the additive Task38-F02 three-track state schema."""

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
    list_database_columns,
)


TABLE = "therapeutic_assessment_cases"
COLUMNS = {"workflow_state", "hypothesis_state", "safety_state"}
PRODUCTION_CONFIRMATION = "APPLY_TASK38_F02_STATE_MACHINE"


def _guard(action: str, allow_production: bool, confirmation: str) -> None:
    if str(Config.APP_ENV).lower() != "production" or action in {"plan", "verify", "rollback"}:
        return
    if not allow_production or confirmation != PRODUCTION_CONFIRMATION:
        raise RuntimeError("生产迁移已阻断：需要独立批准和精确确认短语")


def inspect() -> dict:
    with get_connection() as conn:
        columns = {str(row["name"]) for row in list_database_columns(conn, TABLE)}
        row_count = int(conn.execute(f"SELECT COUNT(*) AS count FROM {TABLE}").fetchone()["count"])
        invalid = int(
            conn.execute(
                f"""
                SELECT COUNT(*) AS count FROM {TABLE}
                WHERE workflow_state IS NULL OR workflow_state = ''
                   OR hypothesis_state IS NULL OR hypothesis_state = ''
                   OR safety_state IS NULL OR safety_state = ''
                """
            ).fetchone()["count"]
        ) if COLUMNS.issubset(columns) else row_count
    missing = sorted(COLUMNS - columns)
    return {
        "schema_version": CURRENT_SCHEMA_VERSION,
        "schema_name": CURRENT_SCHEMA_NAME,
        "table": TABLE,
        "missing_columns": missing,
        "columns_ok": not missing,
        "row_count": row_count,
        "invalid_state_rows": invalid,
        "additive_only": True,
        "ok": not missing and invalid == 0,
    }


def apply() -> dict:
    init_db()
    return {
        "action": "apply",
        **inspect(),
        "production_mutation": str(Config.APP_ENV).lower() == "production",
    }


def rollback() -> dict:
    return {
        "action": "rollback",
        "schema_preserved": True,
        "columns_dropped": False,
        "production_mutation": False,
        "operator_note": "先关闭三轨状态写入并回退应用；加法字段和审计事件不自动删除。",
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
