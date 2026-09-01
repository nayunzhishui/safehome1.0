"""Plan, apply, or verify RC0810 migrations on an isolated restored MySQL database.

This command intentionally refuses the original production database ``safehome``.
It is only for a CloudBase restore rehearsal whose database name is supplied and
confirmed exactly by the operator.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


BACKEND = Path(__file__).resolve().parents[1]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

import database  # noqa: E402
from config import Config  # noqa: E402
from services.schema_migration_service import (  # noqa: E402
    MIGRATIONS,
    apply_pending_schema_migrations,
)


ORIGINAL_PRODUCTION_DATABASE = "safehome"
ISOLATED_DATABASE_PATTERN = re.compile(r"^safehome-[0-9]{12,14}$")
CRITICAL_COUNT_TABLES = ("users", "emotion_diaries", "consent_records", "audit_logs")


def validate_expected_database(expected_database: str) -> str:
    normalized = str(expected_database or "").strip()
    if normalized == ORIGINAL_PRODUCTION_DATABASE:
        raise ValueError("original_production_database_forbidden")
    if not ISOLATED_DATABASE_PATTERN.fullmatch(normalized):
        raise ValueError("isolated_database_name_invalid")
    return normalized


def required_confirmation(expected_database: str) -> str:
    normalized = validate_expected_database(expected_database)
    suffix = re.sub(r"[^A-Za-z0-9]+", "_", normalized).strip("_").upper()
    return f"APPLY_RC0810_ISOLATED_{suffix}"


def validate_confirmation(expected_database: str, confirmation: str) -> None:
    if confirmation != required_confirmation(expected_database):
        raise ValueError("apply_confirmation_mismatch")


def assert_connected_database(conn, expected_database: str) -> str:
    expected = validate_expected_database(expected_database)
    row = conn.execute("SELECT DATABASE() AS database_name").fetchone()
    actual = str((row or {}).get("database_name") or "").strip()
    if actual != expected:
        raise ValueError("connected_database_mismatch")
    return actual


def _applied_explicit_versions(conn, tables: set[str]) -> set[str]:
    if "explicit_schema_migrations" not in tables:
        return set()
    rows = conn.execute(
        "SELECT version FROM explicit_schema_migrations ORDER BY version"
    ).fetchall()
    return {str(row["version"]) for row in rows}


def _latest_version(conn, table: str, tables: set[str]) -> str | None:
    if table not in tables:
        return None
    row = conn.execute(
        f"SELECT version FROM {table} ORDER BY version DESC LIMIT 1"
    ).fetchone()
    return str(row["version"]) if row else None


def _snapshot(conn, database_name: str) -> dict:
    tables = {str(row["name"]) for row in database.list_database_tables(conn)}
    applied = _applied_explicit_versions(conn, tables)
    known_versions = [migration.version for migration in MIGRATIONS]
    return {
        "database": database_name,
        "table_count": len(tables),
        "legacy_schema_version": _latest_version(conn, "schema_migrations", tables),
        "explicit_migration_head": _latest_version(
            conn, "explicit_schema_migrations", tables
        ),
        "pending_explicit_migrations": [version for version in known_versions if version not in applied],
        "critical_row_counts": {
            table: database.get_table_count(conn, table)
            for table in CRITICAL_COUNT_TABLES
            if table in tables
        },
    }


def _apply_candidate_schema(conn) -> list[str]:
    for statement in database.SCHEMA_SQL:
        conn.execute(database.mysqlize_schema_statement(statement))
    database.ensure_mysql_index_columns(conn)
    database.ensure_mysql_content_text_capacity(conn)
    database.ensure_schema_columns(conn)
    for statement in database.INDEX_SQL:
        database.create_index(conn, statement)
    identity_status = database.check_identity_uniqueness(conn)
    if identity_status["ok"]:
        for statement in database.IDENTITY_UNIQUE_INDEX_SQL:
            database.create_index(conn, statement)
    database.sync_training_cards(conn)
    database.sync_assessment_worksheets(conn)
    database.record_schema_migration(conn)
    applied = apply_pending_schema_migrations(conn)
    conn.commit()
    return applied


def _verification_ok(snapshot: dict) -> bool:
    return bool(
        snapshot["legacy_schema_version"] == database.CURRENT_SCHEMA_VERSION
        and snapshot["explicit_migration_head"] == MIGRATIONS[-1].version
        and not snapshot["pending_explicit_migrations"]
    )


def run(action: str, expected_database: str, confirmation: str = "") -> tuple[dict, int]:
    expected = validate_expected_database(expected_database)
    if Config.DB_PROVIDER != "mysql":
        raise ValueError("mysql_provider_required")
    if str(Config.MYSQL_DATABASE or "").strip() != expected:
        raise ValueError("configured_database_mismatch")
    if action == "apply":
        validate_confirmation(expected, confirmation)

    with database.get_connection() as conn:
        actual = assert_connected_database(conn, expected)
        before = _snapshot(conn, actual)
        if action == "plan":
            return {
                "ok": True,
                "action": action,
                "mutated": False,
                "snapshot": before,
                "required_confirmation": required_confirmation(expected),
            }, 0

        applied: list[str] = []
        if action == "apply":
            applied = _apply_candidate_schema(conn)
        after = _snapshot(conn, actual)
        ok = _verification_ok(after)
        return {
            "ok": ok,
            "action": action,
            "mutated": action == "apply",
            "applied_explicit_migrations": applied,
            "before": before if action == "apply" else None,
            "snapshot": after,
            "expected_heads": {
                "legacy_schema_version": database.CURRENT_SCHEMA_VERSION,
                "explicit_migration_head": MIGRATIONS[-1].version,
            },
        }, 0 if ok else 1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("plan", "apply", "verify"))
    parser.add_argument("--expected-database", required=True)
    parser.add_argument("--confirm", default="")
    args = parser.parse_args()

    try:
        result, exit_code = run(args.action, args.expected_database, args.confirm)
    except ValueError as exc:
        result = {"ok": False, "action": args.action, "error_code": str(exc)}
        exit_code = 2
    except Exception:
        result = {"ok": False, "action": args.action, "error_code": "migration_operation_failed"}
        exit_code = 1
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
