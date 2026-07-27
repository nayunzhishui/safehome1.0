"""Additive Task38-F04 question quality migration."""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path
BACKEND = Path(__file__).resolve().parents[1]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))
from config import Config
from database import CURRENT_SCHEMA_NAME, CURRENT_SCHEMA_VERSION, get_connection, init_db, list_database_columns

COLUMNS = {"working_question", "question_candidates_json", "question_quality_json", "best_guess", "question_status", "candidate_decision", "question_version"}
CONFIRMATION = "APPLY_TASK38_F04_QUESTION_QUALITY"

def inspect():
    with get_connection() as conn:
        present = {row["name"] for row in list_database_columns(conn, "therapeutic_assessment_cases")}
    missing = sorted(COLUMNS - present)
    return {"schema_version": CURRENT_SCHEMA_VERSION, "schema_name": CURRENT_SCHEMA_NAME, "missing_columns": missing, "ok": not missing}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["plan", "apply", "verify", "rollback"])
    parser.add_argument("--allow-production", action="store_true")
    parser.add_argument("--confirmation", default="")
    args = parser.parse_args()
    if str(Config.APP_ENV).lower() == "production" and args.action == "apply" and (not args.allow_production or args.confirmation != CONFIRMATION):
        raise RuntimeError("生产迁移已阻断：需要独立批准和精确确认短语")
    if args.action == "apply":
        init_db()
        result = {"action": "apply", **inspect(), "production_mutation": str(Config.APP_ENV).lower() == "production"}
    elif args.action == "rollback":
        result = {"action": "rollback", "schema_preserved": True, "columns_dropped": False, "production_mutation": False}
    else:
        result = {"action": args.action, **inspect(), "production_mutation": False}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("ok", True) else 1

if __name__ == "__main__":
    raise SystemExit(main())
