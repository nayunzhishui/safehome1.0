"""Plan/apply/verify the additive Task36-F16 therapeutic-assessment schema."""

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
    "therapeutic_assessment_cases",
    "therapeutic_assessment_feedback_versions",
    "therapeutic_assessment_actions",
    "therapeutic_assessment_events",
]
PRODUCTION_CONFIRMATION = "APPLY_TASK36_F16_THERAPEUTIC_ASSESSMENT_SCHEMA"


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
        "additive_only": True,
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
        "participant_questions_preserved": True,
        "feedback_versions_and_audit_preserved": True,
        "operator_note": "先停用治疗性评估入口并回退应用；加法表不自动DROP，数据删除走隐私受控执行器。",
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
