"""Task 37 A05 model registry migration audit and safe rollback plan."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from database import (  # noqa: E402
    CURRENT_SCHEMA_VERSION,
    get_connection,
    init_db,
    list_database_tables,
)


TABLES = (
    "offline_model_versions",
    "offline_model_shadow_runs",
    "offline_model_review_queue",
)


def audit() -> dict:
    with get_connection() as conn:
        existing = {row["name"] for row in list_database_tables(conn)}
        counts = {
            table: int(
                conn.execute(f"SELECT COUNT(*) AS count FROM {table}").fetchone()[
                    "count"
                ]
            )
            if table in existing
            else None
            for table in TABLES
        }
        migration = conn.execute(
            "SELECT version, name, applied_at FROM schema_migrations WHERE version = ?",
            (CURRENT_SCHEMA_VERSION,),
        ).fetchone()
    return {
        "ok": all(table in existing for table in TABLES) and migration is not None,
        "schema_version": CURRENT_SCHEMA_VERSION,
        "tables": counts,
        "migration_recorded": dict(migration) if migration else None,
    }


def rollback_plan() -> dict:
    return {
        "automatic_destructive_rollback_executed": False,
        "steps": [
            "设置 OFFLINE_BENCHMARK_ENABLED=0 停止新影子运行",
            "保留模型版本、历史运行和复核队列为只读证据",
            "从研究者界面隐藏影子执行入口",
            "确认不影响情绪记录、反馈和训练卡核心链路",
        ],
        "drop_tables_allowed": False,
        "participant_data_touched": False,
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
