"""Task 27 idempotent schema migration, verification and non-destructive rollback planning."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from database import CURRENT_SCHEMA_VERSION, get_connection, init_db, list_database_tables  # noqa: E402


TABLES = ("content_governance_versions", "content_governance_reviews", "content_governance_releases")


def audit() -> dict:
    with get_connection() as conn:
        rows = list_database_tables(conn)
        existing = {row["name"] for row in rows}
        counts = {table: int(conn.execute(f"SELECT COUNT(*) AS count FROM {table}").fetchone()["count"]) if table in existing else None for table in TABLES}
        migration = conn.execute("SELECT version, name, applied_at FROM schema_migrations WHERE version = ?", (CURRENT_SCHEMA_VERSION,)).fetchone()
    return {"ok": all(table in existing for table in TABLES) and migration is not None, "schema_version": CURRENT_SCHEMA_VERSION, "tables": counts, "migration_recorded": dict(migration) if migration else None}


def rollback_plan() -> dict:
    return {
        "automatic_rollback_executed": False,
        "reason": "内容版本与审核轨迹属于不可变审计证据，不自动删除表或历史记录。",
        "safe_rollback_steps": [
            "关闭 CONTENT_GOVERNANCE_PUBLISH_ENABLED",
            "将 Web 内容治理入口回退到上一提交",
            "按 content_governance_releases.previous_release_id 选择已验证发布包恢复运行内容",
            "保留三个治理表只读，待人工确认后再决定是否归档",
        ],
        "destructive_step_requires_human_approval": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="执行幂等建表并记录版本")
    parser.add_argument("--rollback-plan", action="store_true", help="仅输出非破坏回滚方案")
    args = parser.parse_args()
    if args.apply:
        init_db()
    result = rollback_plan() if args.rollback_plan else audit()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if args.rollback_plan or result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
