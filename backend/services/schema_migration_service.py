"""Explicit additive schema migrations introduced after the legacy ensure_column era.

The historical `schema_migrations` table is also used by SafeHome readiness
checks as a single legacy schema-version marker.  New migrations therefore use
`explicit_schema_migrations` so adding a migration cannot accidentally make an
otherwise healthy deployment fail `/readyz` merely because the legacy marker
has not been bumped in `database.py`.

Migrations are additive, idempotent and carry a reviewed rollback plan.
Rollbacks are never executed automatically on startup.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from database import ensure_column, mysqlize_schema_statement, now_iso

MYSQL_MIGRATION_LOCK_NAME = "safehome_explicit_schema_migrations"
MYSQL_MIGRATION_LOCK_TIMEOUT_SECONDS = 15


@dataclass(frozen=True)
class Migration:
    version: str
    name: str
    apply: Callable
    rollback_notes: tuple[str, ...]


def _provider(conn) -> str:
    return getattr(conn, "provider", "sqlite")


def _execute_schema(conn, statement: str) -> None:
    conn.execute(mysqlize_schema_statement(statement) if _provider(conn) == "mysql" else statement)


def _ensure_registry(conn) -> None:
    _execute_schema(
        conn,
        """
        CREATE TABLE IF NOT EXISTS explicit_schema_migrations (
            version TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            rollback_notes_json TEXT NOT NULL DEFAULT '[]',
            applied_at TEXT NOT NULL
        )
        """,
    )


def _applied(conn, version: str) -> bool:
    _ensure_registry(conn)
    row = conn.execute(
        "SELECT version FROM explicit_schema_migrations WHERE version = ?",
        (version,),
    ).fetchone()
    return row is not None


def _record(conn, migration: Migration) -> None:
    import json

    _ensure_registry(conn)
    rollback_json = json.dumps(list(migration.rollback_notes), ensure_ascii=False)
    if _provider(conn) == "mysql":
        conn.execute(
            """
            INSERT INTO explicit_schema_migrations (version, name, rollback_notes_json, applied_at)
            VALUES (?, ?, ?, ?)
            ON DUPLICATE KEY UPDATE
                name = VALUES(name), rollback_notes_json = VALUES(rollback_notes_json)
            """,
            (migration.version, migration.name, rollback_json, now_iso()),
        )
    else:
        conn.execute(
            """
            INSERT INTO explicit_schema_migrations (version, name, rollback_notes_json, applied_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(version) DO UPDATE SET
                name = excluded.name,
                rollback_notes_json = excluded.rollback_notes_json
            """,
            (migration.version, migration.name, rollback_json, now_iso()),
        )


def _acquire_mysql_migration_lock(conn) -> None:
    row = conn.execute(
        "SELECT GET_LOCK(?, ?) AS acquired",
        (MYSQL_MIGRATION_LOCK_NAME, MYSQL_MIGRATION_LOCK_TIMEOUT_SECONDS),
    ).fetchone()
    acquired = row["acquired"] if row is not None else None
    if acquired not in {1, True, "1"}:
        raise RuntimeError(
            "Could not acquire the SafeHome MySQL schema migration lock within "
            f"{MYSQL_MIGRATION_LOCK_TIMEOUT_SECONDS} seconds."
        )


def _release_mysql_migration_lock(conn) -> None:
    conn.execute(
        "SELECT RELEASE_LOCK(?) AS released",
        (MYSQL_MIGRATION_LOCK_NAME,),
    ).fetchone()


def _apply_2026_08_07_062(conn) -> None:
    # Age confirmation is intentionally minimal-data: SafeHome stores the age
    # band used by the legal/product gate, not date of birth.
    for column, definition in {
        "age_band": "TEXT",
        "age_verified_at": "TEXT",
        "age_verification_method": "TEXT",
    }.items():
        ensure_column(conn, "users", column, definition)

    _execute_schema(
        conn,
        """
        CREATE TABLE IF NOT EXISTS participant_minor_safeguards (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL UNIQUE,
            age_band TEXT NOT NULL,
            guardian_user_id TEXT,
            guardian_consent_status TEXT NOT NULL DEFAULT 'pending',
            guardian_consent_record_id TEXT,
            child_assent_status TEXT NOT NULL DEFAULT 'pending',
            status TEXT NOT NULL DEFAULT 'guardian_link_required',
            policy_version TEXT NOT NULL,
            version INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """,
    )

    for column, definition in {
        "safety_route": "TEXT NOT NULL DEFAULT 'standard'",
        "priority": "TEXT NOT NULL DEFAULT 'normal'",
        "due_at": "TEXT",
        "escalated_at": "TEXT",
        "last_actor_id": "TEXT",
        "review_version": "INTEGER NOT NULL DEFAULT 0",
    }.items():
        ensure_column(conn, "risk_review_records", column, definition)

    for column, definition in {
        "priority": "TEXT NOT NULL DEFAULT 'normal'",
        "due_at": "TEXT",
        "acknowledged_at": "TEXT",
        "acknowledged_by": "TEXT",
        "resolved_at": "TEXT",
        "resolved_by": "TEXT",
        "resolution_code": "TEXT",
        "last_actor_id": "TEXT",
    }.items():
        ensure_column(conn, "supervision_requests", column, definition)

    _execute_schema(
        conn,
        """
        CREATE TABLE IF NOT EXISTS supervision_request_events (
            id TEXT PRIMARY KEY,
            request_id TEXT NOT NULL,
            actor_id TEXT NOT NULL,
            actor_role TEXT NOT NULL,
            action TEXT NOT NULL,
            from_status TEXT,
            to_status TEXT NOT NULL,
            metadata_json TEXT NOT NULL DEFAULT '{}',
            created_at TEXT NOT NULL
        )
        """,
    )

    index_specs = [
        ("idx_minor_safeguards_user", "participant_minor_safeguards", "user_id"),
        ("idx_minor_safeguards_guardian", "participant_minor_safeguards", "guardian_user_id"),
        ("idx_risk_review_due", "risk_review_records", "review_status, due_at"),
        ("idx_supervision_due", "supervision_requests", "status, due_at"),
        ("idx_supervision_events_request", "supervision_request_events", "request_id, created_at"),
    ]
    for name, table, columns in index_specs:
        if _provider(conn) == "mysql":
            exists = conn.execute(
                """
                SELECT index_name FROM information_schema.statistics
                WHERE table_schema = DATABASE() AND table_name = ? AND index_name = ?
                LIMIT 1
                """,
                (table, name),
            ).fetchone()
            if exists is None:
                conn.execute(f"CREATE INDEX {name} ON {table} ({columns})")
        else:
            conn.execute(f"CREATE INDEX IF NOT EXISTS {name} ON {table} ({columns})")


MIGRATIONS = (
    Migration(
        version="2026_08_07_062",
        name="participant_safety_identity_convergence",
        apply=_apply_2026_08_07_062,
        rollback_notes=(
            "Stop application writes before rollback.",
            "Export participant_minor_safeguards and supervision_request_events for audit retention.",
            "Drop additive indexes/tables only after confirming no pilot records depend on them.",
            "Age/risk/supervision columns are additive and should normally remain during rollback; removing columns is a separate reviewed migration.",
        ),
    ),
)


def _pending_migrations(conn) -> list[Migration]:
    _ensure_registry(conn)
    return [
        migration
        for migration in sorted(MIGRATIONS, key=lambda item: item.version)
        if not _applied(conn, migration.version)
    ]


def apply_pending_schema_migrations(conn) -> list[str]:
    """Apply all known migrations in version order and return applied versions.

    MySQL deployments use a named advisory lock only when work is pending. This
    prevents two CloudBase/Gunicorn instances from racing on additive columns or
    the check-then-create index sequence during a rolling start. The migration
    record is still written only after the migration body completes.
    """

    pending = _pending_migrations(conn)
    if not pending:
        return []

    mysql_locked = False
    if _provider(conn) == "mysql":
        _acquire_mysql_migration_lock(conn)
        mysql_locked = True

    applied: list[str] = []
    try:
        # Another instance may have completed the migration while this
        # connection was waiting for the advisory lock, so re-check each item.
        for migration in pending:
            if _applied(conn, migration.version):
                continue
            migration.apply(conn)
            _record(conn, migration)
            applied.append(migration.version)
        return applied
    finally:
        if mysql_locked:
            _release_mysql_migration_lock(conn)


def migration_manifest() -> list[dict]:
    """Expose migration metadata for acceptance tooling without mutating DB."""
    return [
        {
            "version": item.version,
            "name": item.name,
            "rollback_notes": list(item.rollback_notes),
        }
        for item in MIGRATIONS
    ]
