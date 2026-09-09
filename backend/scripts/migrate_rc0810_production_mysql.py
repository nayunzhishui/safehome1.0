"""Plan, apply, or verify RC0810 migrations on the production MySQL database.

This entry point is intentionally separate from the isolated restore rehearsal.
It requires the exact production database name and an action-specific confirmation
before applying additive schema changes.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


BACKEND = Path(__file__).resolve().parents[1]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

import database  # noqa: E402
from config import Config  # noqa: E402
from scripts.migrate_rc0810_isolated_mysql import (  # noqa: E402
    MIGRATIONS,
    MigrationStageError,
    _apply_candidate_schema,
    _snapshot,
    _verification_ok,
)


PRODUCTION_DATABASE = "safehome"
PRODUCTION_CONFIRMATION = "APPLY_RC0810_PRODUCTION_SAFEHOME"


def _validate_target(expected_database: str) -> str:
    expected = str(expected_database or "").strip()
    if expected != PRODUCTION_DATABASE:
        raise ValueError("production_database_name_mismatch")
    if Config.DB_PROVIDER != "mysql":
        raise ValueError("mysql_provider_required")
    if str(Config.MYSQL_DATABASE or "").strip() != expected:
        raise ValueError("configured_database_mismatch")
    return expected


def _assert_connected_database(conn, expected_database: str) -> str:
    row = conn.execute("SELECT DATABASE() AS database_name").fetchone()
    actual = str((row or {}).get("database_name") or "").strip()
    if actual != expected_database:
        raise ValueError("connected_database_mismatch")
    return actual


def _critical_counts_unchanged(before: dict, after: dict) -> bool:
    return before.get("critical_row_counts") == after.get("critical_row_counts")


def run(action: str, expected_database: str, confirmation: str = "") -> tuple[dict, int]:
    expected = _validate_target(expected_database)
    if action == "apply" and confirmation != PRODUCTION_CONFIRMATION:
        raise ValueError("production_apply_confirmation_mismatch")

    try:
        with database.get_connection() as conn:
            actual = _assert_connected_database(conn, expected)
            before = _snapshot(conn, actual)
            if action == "plan":
                return {
                    "ok": True,
                    "action": action,
                    "mutated": False,
                    "snapshot": before,
                    "required_confirmation": PRODUCTION_CONFIRMATION,
                }, 0

            applied: list[str] = []
            if action == "apply":
                applied = _apply_candidate_schema(conn)
            after = _snapshot(conn, actual)
            counts_unchanged = _critical_counts_unchanged(before, after)
            ok = _verification_ok(after) and counts_unchanged
            return {
                "ok": ok,
                "action": action,
                "mutated": action == "apply",
                "applied_explicit_migrations": applied,
                "before": before if action == "apply" else None,
                "snapshot": after,
                "critical_row_counts_unchanged": counts_unchanged,
                "expected_heads": {
                    "legacy_schema_version": database.CURRENT_SCHEMA_VERSION,
                    "explicit_migration_head": MIGRATIONS[-1].version,
                },
            }, 0 if ok else 1
    except MigrationStageError as exc:
        result = {
            "ok": False,
            "action": action,
            "error_code": "migration_operation_failed",
            "failure_stage": exc.stage,
        }
        if exc.database_errno is not None:
            result["database_errno"] = exc.database_errno
        return result, 1


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
        result = {
            "ok": False,
            "action": args.action,
            "error_code": "migration_operation_failed",
        }
        exit_code = 1
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
