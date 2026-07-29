"""Task38-F17 readiness check for the governed method library."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
ROOT = BACKEND.parent
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from config import Config
from database import (
    CURRENT_SCHEMA_NAME,
    CURRENT_SCHEMA_VERSION,
    get_connection,
    init_db,
    list_database_tables,
)

TABLES = {
    "content_governance_versions",
    "content_governance_reviews",
    "content_governance_releases",
}
CONFIRMATION = "APPLY_TASK38_F17_METHOD_LIBRARY"


def inspect() -> dict:
    with get_connection() as conn:
        existing = {row["name"] for row in list_database_tables(conn)}
    content_path = (
        Path(Config.CONTENT_DIR) / "therapeutic_assessment_method_library.json"
    )
    content_ok = False
    item_count = 0
    if content_path.exists():
        try:
            payload = json.loads(content_path.read_text(encoding="utf-8"))
            item_count = len(payload.get("items") or [])
            content_ok = (
                payload.get("schema")
                == "safehome.therapeutic-assessment.method-library.v1"
                and item_count >= 9
            )
        except (OSError, json.JSONDecodeError):
            content_ok = False
    missing = sorted(TABLES - existing)
    return {
        "ok": not missing and content_ok,
        "schema_version": CURRENT_SCHEMA_VERSION,
        "schema_name": CURRENT_SCHEMA_NAME,
        "reused_governance_tables": sorted(TABLES),
        "missing_tables": missing,
        "content_ok": content_ok,
        "item_count": item_count,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["plan", "apply", "verify", "rollback"])
    parser.add_argument("--database-path", default="")
    parser.add_argument("--allow-production", action="store_true")
    parser.add_argument("--confirmation", default="")
    args = parser.parse_args()
    if args.database_path:
        Config.DATABASE_PATH = Path(args.database_path).resolve()
    production = str(Config.APP_ENV).lower() == "production"
    if production and args.action == "apply" and (
        not args.allow_production or args.confirmation != CONFIRMATION
    ):
        raise RuntimeError("生产检查已阻断：需要独立批准和精确确认短语")
    if args.action == "apply":
        init_db()
        result = {"action": "apply", **inspect(), "production_mutation": production}
    elif args.action == "verify":
        result = {"action": "verify", **inspect(), "production_mutation": False}
    elif args.action == "rollback":
        result = {
            "action": "rollback",
            "ok": True,
            "schema_preserved": True,
            "tables_dropped": False,
            "history_deleted": False,
            "content_release_changed": False,
            "production_mutation": False,
        }
    else:
        current = inspect()
        result = {
            "action": "plan",
            "ok": True,
            "already_ready": current["ok"],
            "current_state": current,
            "additive_only": True,
            "schema_change_required": False,
            "production_mutation": False,
        }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
