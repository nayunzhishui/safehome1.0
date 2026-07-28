"""Additive migration and verification for Task37-C01 AI use-case scope."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from config import Config  # noqa: E402
from database import (  # noqa: E402
    CURRENT_SCHEMA_NAME,
    CURRENT_SCHEMA_VERSION,
    get_connection,
    init_db,
    list_database_columns,
)


REQUIRED_COLUMNS = {"use_case_id", "use_case_policy_version"}
CONFIRMATION = "APPLY_TASK37_C01_AI_USE_CASE_SCOPE"


def inspect() -> dict:
    with get_connection() as conn:
        columns = {
            row["name"] for row in list_database_columns(conn, "ai_qa_sessions")
        }
    return {
        "ok": REQUIRED_COLUMNS.issubset(columns),
        "schema_version": CURRENT_SCHEMA_VERSION,
        "schema_name": CURRENT_SCHEMA_NAME,
        "missing_columns": sorted(REQUIRED_COLUMNS - columns),
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
    elif args.action == "verify":
        result = {"action": "verify", **inspect(), "production_mutation": False}
    elif args.action == "rollback":
        result = {
            "action": "rollback",
            "ok": True,
            "columns_dropped": False,
            "records_deleted": False,
            "application_rollback_required": True,
            "production_mutation": False,
        }
    else:
        current = inspect()
        result = {
            "action": "plan",
            "ok": True,
            "already_applied": current["ok"],
            "current_state": current,
            "additive_only": True,
            "production_mutation": False,
        }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
