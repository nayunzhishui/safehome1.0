"""Idempotent Task 32 schema migration and conservative rollback plan."""

from __future__ import annotations

import hashlib
import json
import sqlite3
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from config import Config  # noqa: E402
from database import CURRENT_SCHEMA_VERSION, get_connection, get_latest_schema_version, init_db, list_database_tables  # noqa: E402


TASK32_TABLES = [
    "observability_events",
    "reliable_jobs",
    "reliable_job_actions",
    "feature_flag_versions",
    "reliability_slo_snapshots",
    "reliability_drill_runs",
    "reliability_evidence_packages",
]


def apply() -> dict:
    init_db()
    with get_connection() as conn:
        existing = {row["name"] for row in list_database_tables(conn)}
        version = get_latest_schema_version(conn)
    missing = sorted(set(TASK32_TABLES) - existing)
    if missing:
        raise RuntimeError(f"Task 32 migration missing tables: {', '.join(missing)}")
    return {
        "ok": True,
        "status": "applied",
        "schema_version": version or CURRENT_SCHEMA_VERSION,
        "tables": TASK32_TABLES,
        "idempotent": True,
    }


def backup_and_verify(destination: str | Path) -> dict:
    """Create a SQLite backup and verify table counts without participant payload export."""
    source = Path(Config.DATABASE_PATH)
    target = Path(destination)
    target.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(source) as source_conn, sqlite3.connect(target) as target_conn:
        source_conn.backup(target_conn)
    counts = {}
    with sqlite3.connect(target) as conn:
        for table in TASK32_TABLES:
            counts[table] = int(conn.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0])
        integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
    digest = hashlib.sha256(target.read_bytes()).hexdigest()
    return {
        "status": "verified" if integrity == "ok" else "failed",
        "sha256": digest,
        "table_counts": counts,
        "integrity_check": integrity,
        "contains_exported_payload": False,
    }


def rollback_plan() -> dict:
    return {
        "automatic_schema_rollback_executed": False,
        "disable_flags": [
            "RELIABILITY_WORKBENCH_ENABLED",
            "RELIABILITY_JOB_EXECUTION_ENABLED",
            "RELIABILITY_FAULT_INJECTION_ENABLED",
            "RELIABILITY_GRADUAL_RELEASE_ENABLED",
        ],
        "retain_tables": TASK32_TABLES,
        "retain_audit_and_evidence": True,
        "restore_order": [
            "disable runtime writes",
            "capture integrity and count evidence",
            "restore verified backup in isolated environment",
            "run schema and journey checks",
            "obtain human release decision",
        ],
        "production_release_inferred": False,
    }


def main() -> int:
    print(json.dumps({"migration": apply(), "rollback": rollback_plan()}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
