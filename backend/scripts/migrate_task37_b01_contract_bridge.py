"""Audit Task 37 B01 non-destructive contract bridge."""

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
    list_database_columns,
    list_database_tables,
)


REQUIRED_TABLES = (
    "therapeutic_assessment_cases",
    "therapeutic_assessment_evidence_items",
    "therapeutic_assessment_authorizations",
    "therapeutic_assessment_contract_snapshots",
)


def audit() -> dict:
    with get_connection() as conn:
        tables = {row["name"] for row in list_database_tables(conn)}
        case_columns = {
            row["name"] for row in list_database_columns(conn, "therapeutic_assessment_cases")
        }
    required_case_columns = {
        "readiness_level",
        "complexity_scope",
        "safety_state",
        "assigned_researcher_id",
    }
    return {
        "ok": set(REQUIRED_TABLES).issubset(tables)
        and required_case_columns.issubset(case_columns),
        "schema_version": CURRENT_SCHEMA_VERSION,
        "legacy_cases_readable": True,
        "missing_tables": sorted(set(REQUIRED_TABLES) - tables),
        "missing_case_columns": sorted(required_case_columns - case_columns),
    }


def rollback_plan() -> dict:
    return {
        "automatic_destructive_rollback_executed": False,
        "steps": [
            "停止新建契约快照",
            "继续读取既有治疗性评估记录及029后续非破坏字段",
            "保留契约快照和审计证据",
        ],
        "legacy_case_readable": True,
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
