"""Task 37 A07 schema audit and non-destructive rollback plan."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from database import CURRENT_SCHEMA_VERSION, get_connection, init_db, list_database_tables  # noqa: E402


TABLES = ("offline_model_release_gate_runs", "offline_model_release_evidence")


def audit() -> dict:
    with get_connection() as conn:
        existing = {row["name"] for row in list_database_tables(conn)}
        migration = conn.execute(
            "SELECT version, name, applied_at FROM schema_migrations WHERE version = ?",
            (CURRENT_SCHEMA_VERSION,),
        ).fetchone()
    return {
        "ok": set(TABLES).issubset(existing) and migration is not None,
        "schema_version": CURRENT_SCHEMA_VERSION,
        "tables": list(TABLES),
        "migration_recorded": dict(migration) if migration else None,
    }


def rollback_plan() -> dict:
    return {
        "automatic_destructive_rollback_executed": False,
        "steps": [
            "保持offline_model_runtime_controls为off或shadow",
            "保留发布门禁运行和外部证据哈希作为审计记录",
            "关闭发布门禁写入口但保留只读证据包",
        ],
        "runtime_activation_allowed": False,
        "drop_tables_allowed": False,
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
