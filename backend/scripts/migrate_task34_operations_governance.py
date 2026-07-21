"""Idempotent Task 34 schema migration and conservative rollback plan."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from database import CURRENT_SCHEMA_VERSION, get_connection, get_latest_schema_version, init_db, list_database_tables  # noqa: E402


TASK34_TABLES = [
    "operations_release_packages",
    "operations_package_reviews",
    "operations_replay_runs",
    "operations_runtime_controls",
    "operations_monitor_snapshots",
    "operations_incidents",
    "operations_incident_notifications",
    "operations_evidence_packages",
]


def apply() -> dict:
    init_db()
    with get_connection() as conn:
        existing = {row["name"] for row in list_database_tables(conn)}
        version = get_latest_schema_version(conn)
    missing = sorted(set(TASK34_TABLES) - existing)
    if missing:
        raise RuntimeError(f"Task 34 migration missing tables: {', '.join(missing)}")
    return {"ok": True, "schema_version": version or CURRENT_SCHEMA_VERSION, "tables": TASK34_TABLES, "idempotent": True}


def rollback_plan() -> dict:
    return {
        "automatic_schema_rollback_executed": False,
        "disable_flags": ["OPERATIONS_GOVERNANCE_WORKBENCH_ENABLED", "OPERATIONS_LOCAL_RELEASE_ENABLED", "OPERATIONS_PRODUCTION_RELEASE_ENABLED"],
        "retain_tables": TASK34_TABLES,
        "retain_immutable_packages": True,
        "retain_reviews_replays_incidents_notifications_and_audit": True,
        "runtime_recovery": "pause the active package, verify the target bundle hash, then atomically restore the previous package",
        "destructive_drop_allowed": False,
        "production_release_approval_inferred": False,
    }


def main() -> int:
    print(json.dumps({"migration": apply(), "rollback": rollback_plan()}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
