"""Additive Task38-F10 action-follow-up migration."""

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


COLUMNS = {
    "purpose_text",
    "planned_date",
    "reminder_mode",
    "reminder_privacy",
    "stop_conditions_json",
    "setback_plan",
    "training_card_id",
    "linked_checkin_id",
    "version",
    "completed_at",
}
CONFIRMATION = "APPLY_TASK38_F10_ACTION_FOLLOWUP"


def inspect() -> dict:
    with get_connection() as conn:
        columns = {
            row["name"]
            for row in list_database_columns(conn, "therapeutic_assessment_actions")
        }
    missing_columns = sorted(COLUMNS - columns)
    return {
        "schema_version": CURRENT_SCHEMA_VERSION,
        "schema_name": CURRENT_SCHEMA_NAME,
        "missing_columns": missing_columns,
        "ok": not missing_columns,
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
        raise RuntimeError("生产迁移已阻断：需要独立批准和精确确认短语")
    if args.action == "apply":
        init_db()
        result = {"action": "apply", **inspect(), "production_mutation": production}
    elif args.action == "rollback":
        result = {
            "action": "rollback",
            "schema_preserved": True,
            "columns_dropped": False,
            "history_deleted": False,
            "production_mutation": False,
        }
    else:
        result = {"action": args.action, **inspect(), "production_mutation": False}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("ok", True) else 1


if __name__ == "__main__":
    raise SystemExit(main())
