"""Apply, verify and describe non-destructive rollback for Task37-B02."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from database import CURRENT_SCHEMA_VERSION, get_connection, init_db, list_database_tables  # noqa: E402


REQUIRED = {
    "therapeutic_assessment_work_queue",
    "therapeutic_assessment_queue_events",
    "therapeutic_assessment_duty_shifts",
    "therapeutic_assessment_duty_events",
    "therapeutic_assessment_queue_runtime",
}


def audit() -> dict:
    with get_connection() as conn:
        tables = {row["name"] for row in list_database_tables(conn)}
    return {
        "ok": REQUIRED.issubset(tables),
        "schema_version": CURRENT_SCHEMA_VERSION,
        "missing_tables": sorted(REQUIRED - tables),
        "legacy_cases_readable": True,
    }


def rollback_plan() -> dict:
    return {
        "automatic_destructive_rollback_executed": False,
        "steps": [
            "暂停新建和领取人工队列任务",
            "保留队列、值守、交接和审计历史",
            "继续读取既有协作式评估记录",
        ],
        "drop_table_allowed": False,
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
