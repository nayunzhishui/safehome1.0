"""Idempotent Task 33 schema migration and conservative rollback plan."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from database import CURRENT_SCHEMA_VERSION, get_connection, get_latest_schema_version, init_db, list_database_columns, list_database_tables  # noqa: E402


TASK33_TABLES = ["ux_audit_runs", "ux_evidence_packages"]
TASK33_RESILIENT_COLUMNS = {
    "goals": "client_submission_id",
    "emotion_diaries": "client_submission_id",
    "supervision_requests": "client_submission_id",
    "checkins": "client_submission_id",
    "assessment_results": "client_submission_id",
    "parent_assessment_submissions": "client_submission_id",
}


def apply() -> dict:
    init_db()
    with get_connection() as conn:
        existing = {row["name"] for row in list_database_tables(conn)}
        missing_columns = {
            table: column
            for table, column in TASK33_RESILIENT_COLUMNS.items()
            if column not in {row["name"] for row in list_database_columns(conn, table)}
        }
        version = get_latest_schema_version(conn)
    missing = sorted(set(TASK33_TABLES) - existing)
    if missing:
        raise RuntimeError(f"Task 33 migration missing tables: {', '.join(missing)}")
    if missing_columns:
        raise RuntimeError(f"Task 33 migration missing resilient columns: {missing_columns}")
    return {
        "ok": True,
        "schema_version": version or CURRENT_SCHEMA_VERSION,
        "tables": TASK33_TABLES,
        "resilient_columns": TASK33_RESILIENT_COLUMNS,
        "idempotent": True,
    }


def rollback_plan() -> dict:
    return {
        "automatic_schema_rollback_executed": False,
        "disable_flags": ["UX_GOVERNANCE_WORKBENCH_ENABLED"],
        "retain_tables": TASK33_TABLES,
        "retain_resilient_columns": TASK33_RESILIENT_COLUMNS,
        "retain_audit_and_evidence": True,
        "restore_navigation": "remove the /system/experience entry and keep all existing routes",
        "restore_forms": "disable resilient-form hooks without deleting local drafts",
        "release_approval_inferred": False,
    }


def main() -> int:
    print(json.dumps({"migration": apply(), "rollback": rollback_plan()}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
