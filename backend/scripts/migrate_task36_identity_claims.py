"""Plan/apply/verify the additive Task36-F12 identity lifecycle schema."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


BACKEND = Path(__file__).resolve().parents[1]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from config import Config
from database import CURRENT_SCHEMA_NAME, CURRENT_SCHEMA_VERSION, get_connection, init_db, list_database_columns, list_database_tables


TABLES = ["identity_merge_workflows", "identity_merge_record_links"]
USER_COLUMNS = ["merged_into_user_id", "merged_at"]
CLAIM_COLUMNS = ["idempotency_key", "version"]
LINK_COLUMNS = ["source_value", "target_value"]
PRODUCTION_CONFIRMATION = "APPLY_TASK36_F12_IDENTITY_LIFECYCLE_SCHEMA"


def assert_environment_allowed(action: str, allow_production: bool, confirmation: str) -> None:
    if str(Config.APP_ENV).lower() != "production" or action in {"plan", "verify"}:
        return
    if not allow_production or confirmation != PRODUCTION_CONFIRMATION:
        raise RuntimeError("生产迁移或回滚已阻断：需要人工批准和精确确认短语。")


def inspect() -> dict:
    with get_connection() as conn:
        tables = {str(row["name"]) for row in list_database_tables(conn)}
        user_columns = {str(row["name"]) for row in list_database_columns(conn, "users")} if "users" in tables else set()
        claim_columns = {str(row["name"]) for row in list_database_columns(conn, "data_claims")} if "data_claims" in tables else set()
        link_columns = {str(row["name"]) for row in list_database_columns(conn, "identity_merge_record_links")} if "identity_merge_record_links" in tables else set()
        counts = {
            table: int(conn.execute(f"SELECT COUNT(*) AS count FROM {table}").fetchone()["count"])
            for table in TABLES
            if table in tables
        }
    missing_tables = [table for table in TABLES if table not in tables]
    missing_user_columns = [column for column in USER_COLUMNS if column not in user_columns]
    missing_claim_columns = [column for column in CLAIM_COLUMNS if column not in claim_columns]
    missing_link_columns = [column for column in LINK_COLUMNS if column not in link_columns]
    return {
        "schema_version": CURRENT_SCHEMA_VERSION,
        "schema_name": CURRENT_SCHEMA_NAME,
        "missing_tables": missing_tables,
        "missing_user_columns": missing_user_columns,
        "missing_claim_columns": missing_claim_columns,
        "missing_link_columns": missing_link_columns,
        "row_counts": counts,
        "ok": not missing_tables and not missing_user_columns and not missing_claim_columns and not missing_link_columns,
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
        "business_records_preserved": True,
        "merge_and_claim_audit_preserved": True,
        "operator_note": "回退应用版本即可；表和列是向后兼容的加法迁移，不自动DROP或删除合并历史。",
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
