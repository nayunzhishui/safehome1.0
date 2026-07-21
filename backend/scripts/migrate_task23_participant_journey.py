"""Idempotent Task 23 migration and non-destructive behaviour rollback plan."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from database import (  # noqa: E402
    CURRENT_SCHEMA_VERSION,
    get_connection,
    get_latest_schema_version,
    init_db,
    list_database_columns,
    list_database_tables,
)


TASK23_TABLES = ["feedback_ledger_actions", "recommendation_snapshots"]
TASK23_LEDGER_COLUMNS = ["supersedes_id", "participant_status", "withdrawn_at"]


def apply() -> dict:
    init_db()
    with get_connection() as conn:
        tables = {row["name"] for row in list_database_tables(conn)}
        columns = {row["name"] for row in list_database_columns(conn, "feedback_ledger")}
        version = get_latest_schema_version(conn)
    missing_tables = sorted(set(TASK23_TABLES) - tables)
    missing_columns = sorted(set(TASK23_LEDGER_COLUMNS) - columns)
    if missing_tables or missing_columns:
        raise RuntimeError(f"Task 23 migration incomplete: tables={missing_tables}, columns={missing_columns}")
    return {
        "ok": True,
        "schema_version": version or CURRENT_SCHEMA_VERSION,
        "tables": TASK23_TABLES,
        "feedback_ledger_columns": TASK23_LEDGER_COLUMNS,
        "idempotent": True,
    }


def rollback_plan() -> dict:
    return {
        "automatic_schema_rollback_executed": False,
        "feature_flag": "training_feedback_adaptive_ranking",
        "rollback_target": "legacy_rule_order_v1",
        "retain_tables": TASK23_TABLES,
        "retain_append_only_feedback_history": True,
        "destructive_drop_allowed": False,
        "reason": "关闭自适应排序后恢复旧规则顺序；保留修订、撤回和推荐回放审计以避免丢失参与者数据。",
        "production_release_approval_inferred": False,
    }


def main() -> int:
    print(json.dumps({"migration": apply(), "rollback": rollback_plan()}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
