"""Additive Task37-A02 annotation rights, adjudication and grouped split migration."""

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
    list_database_tables,
)


TABLES = {
    "offline_annotation_adjudications",
    "offline_annotation_group_splits",
}
ANNOTATION_COLUMNS = {
    "emotion_labels_json",
    "intensity",
    "polarity_status",
    "evidence_excerpt",
    "rationale",
    "needs_human_understanding",
    "human_review_reason",
    "manual_version",
    "group_hash",
    "data_split",
}
CONFIRMATION = "APPLY_TASK37_A02_ANNOTATION_GOVERNANCE"


def inspect() -> dict:
    with get_connection() as conn:
        existing = {row["name"] for row in list_database_tables(conn)}
        columns = {
            row["name"] for row in list_database_columns(conn, "offline_benchmark_annotations")
        }
    missing_tables = sorted(TABLES - existing)
    missing_columns = sorted(ANNOTATION_COLUMNS - columns)
    return {
        "schema_version": CURRENT_SCHEMA_VERSION,
        "schema_name": CURRENT_SCHEMA_NAME,
        "missing_tables": missing_tables,
        "missing_columns": missing_columns,
        "ok": not missing_tables and not missing_columns,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["plan", "apply", "verify", "rollback"])
    parser.add_argument("--allow-production", action="store_true")
    parser.add_argument("--confirmation", default="")
    args = parser.parse_args()
    production = str(Config.APP_ENV).lower() == "production"
    if production and args.action == "apply" and (
        not args.allow_production or args.confirmation != CONFIRMATION
    ):
        raise RuntimeError("生产迁移已阻断：需要独立备份恢复证据和精确确认短语")
    if args.action == "apply":
        init_db()
        result = {"action": "apply", **inspect(), "production_mutation": production}
    elif args.action == "rollback":
        result = {
            "action": "rollback",
            "schema_preserved": True,
            "tables_dropped": False,
            "history_deleted": False,
            "production_mutation": False,
        }
    else:
        result = {"action": args.action, **inspect(), "production_mutation": False}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("ok", True) else 1


if __name__ == "__main__":
    raise SystemExit(main())
