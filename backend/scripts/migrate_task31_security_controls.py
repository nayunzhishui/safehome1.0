"""Task 31 idempotent schema migration and non-destructive rollback plan."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from database import CURRENT_SCHEMA_NAME, CURRENT_SCHEMA_VERSION, get_connection, init_db, list_database_columns, list_database_tables  # noqa: E402


TABLES = ("security_control_runs", "security_events", "privacy_deletion_verifications")


def apply() -> dict:
    init_db()
    with get_connection() as conn:
        tables = {row["name"] for row in list_database_tables(conn)}
        columns = {row["name"] for row in list_database_columns(conn, "users")}
        migration = conn.execute("SELECT * FROM schema_migrations WHERE version = ?", (CURRENT_SCHEMA_VERSION,)).fetchone()
        account_count = conn.execute("SELECT COUNT(*) AS count FROM users").fetchone()
    missing_tables = sorted(set(TABLES) - tables)
    missing_columns = sorted({"auth_epoch", "status_reason"} - columns)
    return {
        "ok": not missing_tables and not missing_columns and migration is not None,
        "schema_version": CURRENT_SCHEMA_VERSION,
        "schema_name": CURRENT_SCHEMA_NAME,
        "missing_tables": missing_tables,
        "missing_user_columns": missing_columns,
        "existing_accounts_preserved": int(account_count["count"] if account_count else 0),
        "existing_tokens_remain_valid_until_rotation": True,
        "temporary_showcase_exception_changed": False,
    }


def rollback_plan() -> dict:
    return {
        "automatic_rollback_executed": False,
        "safe_rollback_steps": [
            "设置 SECURITY_SCAN_EXECUTION_ENABLED=0",
            "隐藏 Web 安全工作台和小程序公开状态入口",
            "保留 auth_epoch，避免旧令牌意外恢复有效",
            "保留安全事件、删除核验证据和审计记录只读",
            "保留 CSV 公式转义和 API 安全响应头",
            "临时展示越权仍按既有开关单独管理，不由本迁移自动关闭",
        ],
        "destructive_schema_rollback_requires_human_approval": True,
        "formal_security_acceptance_inferred": False,
        "production_release_inferred": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--rollback-plan", action="store_true")
    args = parser.parse_args()
    if args.apply == args.rollback_plan:
        parser.error("choose exactly one of --apply or --rollback-plan")
    result = apply() if args.apply else rollback_plan()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("ok", True) else 1


if __name__ == "__main__":
    raise SystemExit(main())
