"""Task 29 idempotent migration audit and non-destructive rollback plan."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from database import CURRENT_SCHEMA_VERSION, get_connection, init_db, list_database_tables  # noqa: E402


TABLES = (
    "offline_dataset_cards",
    "offline_benchmark_runs",
    "offline_benchmark_annotations",
    "offline_benchmark_reviews",
    "offline_benchmark_runtime_control",
)


def audit() -> dict:
    with get_connection() as conn:
        existing = {row["name"] for row in list_database_tables(conn)}
        counts = {table: int(conn.execute(f"SELECT COUNT(*) AS count FROM {table}").fetchone()["count"]) if table in existing else None for table in TABLES}
        migration = conn.execute("SELECT version, name, applied_at FROM schema_migrations WHERE version = ?", (CURRENT_SCHEMA_VERSION,)).fetchone()
    return {"ok": all(table in existing for table in TABLES) and migration is not None, "schema_version": CURRENT_SCHEMA_VERSION, "tables": counts, "migration_recorded": dict(migration) if migration else None}


def rollback_plan() -> dict:
    return {
        "automatic_rollback_executed": False,
        "safe_rollback_steps": [
            "设置 OFFLINE_BENCHMARK_ENABLED=0",
            "保持 OFFLINE_EXTERNAL_INGEST_ENABLED=0 和 OFFLINE_PRODUCTION_REPLACEMENT_ALLOWED=0",
            "管理员触发只允许停用的运行控制",
            "移除 Web 内部工作台和 API 路由注册",
            "保留数据集卡、运行、标注、复核和审计表只读",
            "若未来批准过外部数据，按数据集卡 deletion_method 删除源工件和派生运行",
        ],
        "destructive_step_requires_human_approval": True,
        "public_dataset_permission_inferred": False,
        "production_rule_replacement_inferred": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--rollback-plan", action="store_true")
    args = parser.parse_args()
    if args.apply:
        init_db()
    result = rollback_plan() if args.rollback_plan else audit()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if args.rollback_plan or result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
