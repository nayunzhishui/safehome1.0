"""Compare lineage schema/count/tombstone evidence across SQLite backup restore."""

from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
from pathlib import Path


TABLES = [
    "computation_datasets",
    "computation_authorization_snapshots",
    "computation_lineage_edges",
    "computation_deletion_tombstones",
    "computation_legal_holds",
]


def _snapshot(path: Path) -> dict:
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    try:
        schema_rows = connection.execute(
            "SELECT type, name, sql FROM sqlite_master WHERE type IN ('table','index') ORDER BY type, name"
        ).fetchall()
        schema = "\n".join(str(row["sql"] or "") for row in schema_rows)
        counts = {
            table: int(connection.execute(f"SELECT COUNT(*) AS count FROM {table}").fetchone()["count"])
            for table in TABLES
        }
        tombstones = connection.execute(
            """SELECT subject_hash, root_resource_type, root_resource_id, reason_code,
            affected_resources_json, blocked_by_legal_hold
            FROM computation_deletion_tombstones ORDER BY id"""
        ).fetchall()
        tombstone_hash = hashlib.sha256(
            json.dumps([dict(row) for row in tombstones], sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        version = connection.execute("SELECT version FROM schema_migrations ORDER BY version DESC LIMIT 1").fetchone()
        return {
            "schema_version": version["version"] if version else None,
            "schema_sha256": hashlib.sha256(schema.encode("utf-8")).hexdigest(),
            "row_counts": counts,
            "tombstone_sha256": tombstone_hash,
        }
    finally:
        connection.close()


def compare(source: Path, restored: Path) -> dict:
    source_snapshot = _snapshot(source)
    restored_snapshot = _snapshot(restored)
    return {
        "ok": source_snapshot == restored_snapshot,
        "source": source_snapshot,
        "restored": restored_snapshot,
        "raw_rows_emitted": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--restored", type=Path, required=True)
    args = parser.parse_args()
    result = compare(args.source, args.restored)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
