"""Explicit additive schema migrations introduced after the legacy ensure_column era.

The historical `schema_migrations` table is also used by SafeHome readiness
checks as a single legacy schema-version marker. New migrations therefore use
`explicit_schema_migrations` so adding a migration cannot accidentally make an
otherwise healthy deployment fail `/readyz` merely because the legacy marker
has not been bumped in `database.py`.

Migrations are additive, idempotent and carry a reviewed rollback plan.
Rollbacks are never executed automatically on startup.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from database import ensure_column, json_loads, mysqlize_schema_statement, new_id, now_iso
from services.idempotency_service import canonical_request_hash

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


def _create_index_if_missing(conn, name: str, table: str, columns: str) -> None:
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

    for name, table, columns in [
        ("idx_minor_safeguards_user", "participant_minor_safeguards", "user_id"),
        ("idx_minor_safeguards_guardian", "participant_minor_safeguards", "guardian_user_id"),
        ("idx_risk_review_due", "risk_review_records", "review_status, due_at"),
        ("idx_supervision_due", "supervision_requests", "status, due_at"),
        ("idx_supervision_events_request", "supervision_request_events", "request_id, created_at"),
    ]:
        _create_index_if_missing(conn, name, table, columns)


def _apply_2026_08_07_063(conn) -> None:
    # Real embeddings remain optional. Existing deterministic vector_json is
    # preserved as the zero-dependency fallback and for reproducible tests.
    for column, definition in {
        "embedding_json": "TEXT",
        "embedding_model": "TEXT",
        "embedding_dimensions": "INTEGER",
        "embedding_updated_at": "TEXT",
        "retrieval_metadata_json": "TEXT NOT NULL DEFAULT '{}'",
    }.items():
        ensure_column(conn, "ai_knowledge_chunks", column, definition)

    _execute_schema(
        conn,
        """
        CREATE TABLE IF NOT EXISTS agent_runs (
            id TEXT PRIMARY KEY,
            actor_id TEXT NOT NULL,
            actor_role TEXT NOT NULL,
            objective_hash TEXT NOT NULL,
            status TEXT NOT NULL,
            planner TEXT NOT NULL,
            policy_version TEXT NOT NULL,
            tool_budget INTEGER NOT NULL DEFAULT 0,
            tool_count INTEGER NOT NULL DEFAULT 0,
            synthetic_data INTEGER NOT NULL DEFAULT 1,
            metadata_json TEXT NOT NULL DEFAULT '{}',
            created_at TEXT NOT NULL,
            completed_at TEXT
        )
        """,
    )
    _execute_schema(
        conn,
        """
        CREATE TABLE IF NOT EXISTS agent_tool_calls (
            id TEXT PRIMARY KEY,
            run_id TEXT NOT NULL,
            tool_name TEXT NOT NULL,
            status TEXT NOT NULL,
            input_hash TEXT NOT NULL,
            output_hash TEXT,
            latency_ms DOUBLE,
            error_code TEXT,
            created_at TEXT NOT NULL
        )
        """,
    )

    for name, table, columns in [
        ("idx_agent_runs_actor_created", "agent_runs", "actor_id, created_at"),
        ("idx_agent_runs_status_created", "agent_runs", "status, created_at"),
        ("idx_agent_tool_calls_run_created", "agent_tool_calls", "run_id, created_at"),
    ]:
        _create_index_if_missing(conn, name, table, columns)


def _apply_2026_08_24_064(conn) -> None:
    _execute_schema(
        conn,
        """
        CREATE TABLE IF NOT EXISTS core_idempotency_records (
            id TEXT PRIMARY KEY,
            actor_id TEXT NOT NULL,
            endpoint TEXT NOT NULL,
            idempotency_key TEXT NOT NULL,
            request_hash TEXT NOT NULL,
            resource_type TEXT NOT NULL,
            resource_id TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'committed',
            response_status INTEGER,
            response_json TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            UNIQUE(actor_id, endpoint, idempotency_key)
        )
        """,
    )
    for table in (
        "goals",
        "emotion_diaries",
        "checkins",
        "supervision_requests",
        "assessment_results",
        "parent_assessment_submissions",
    ):
        ensure_column(conn, table, "request_hash", "TEXT")
    for name, table, columns in (
        (
            "idx_core_idempotency_resource",
            "core_idempotency_records",
            "resource_type, resource_id",
        ),
        (
            "idx_core_idempotency_created",
            "core_idempotency_records",
            "created_at",
        ),
    ):
        _create_index_if_missing(conn, name, table, columns)


def _apply_2026_08_24_065(conn) -> None:
    configs = (
        (
            "goals",
            "POST /api/goals",
            "goal",
            lambda row: {
                "scene": row["scene"],
                "smart_goal": row["smart_goal"],
                "motivation": row["motivation"],
                "start_date": row["start_date"],
                "status": row["status"],
            },
        ),
        (
            "emotion_diaries",
            "POST /api/diaries",
            "diary",
            lambda row: {
                key: row[key]
                for key in (
                    "goal_id",
                    "event_time",
                    "scene",
                    "event_description",
                    "parent_emotion",
                    "parent_emotion_intensity",
                    "child_emotion",
                    "child_emotion_intensity",
                    "automatic_thought",
                    "body_sensation",
                    "behavior",
                    "raw_text",
                )
            },
        ),
        (
            "checkins",
            "POST /api/checkins",
            "checkin",
            lambda row: {
                "card_id": row["card_id"],
                "diary_id": row["diary_id"],
                "completed": bool(row["completed"]),
                "emotion_before": row["emotion_before"],
                "emotion_after": row["emotion_after"],
                "reflection": str(row["reflection"] or ""),
                "helpfulness_rating": row["helpfulness_rating"],
                "skip_reason": row["skip_reason"],
                "source_recommendation_id": row["source_recommendation_id"],
                "before_thermometer_id": row["before_thermometer_id"],
                "after_thermometer_id": row["after_thermometer_id"],
            },
        ),
        (
            "supervision_requests",
            "POST /api/supervision",
            "supervision_request",
            lambda row: {
                "message": row["message"],
                "source_type": str(row["source_type"] or ""),
                "source_id": str(row["source_id"] or ""),
                "source_title": str(row["source_title"] or ""),
                "contact": row["contact"],
                "risk_hint": row["risk_hint"],
            },
        ),
        (
            "assessment_results",
            "POST /api/assessment-results",
            "assessment_result",
            lambda row: {
                "worksheet_id": row["worksheet_id"],
                "answers": json_loads(row["answers_json"], []),
                "result_summary": row["result_summary"],
            },
        ),
        (
            "parent_assessment_submissions",
            "POST /api/parent-assessments",
            "parent_assessment",
            lambda row: {
                "answers": json_loads(row["answers_json"], {}),
                "research_consent": bool(row["research_consent"]),
            },
        ),
    )
    for table, endpoint, resource_type, payload_builder in configs:
        rows = conn.execute(
            f"SELECT * FROM {table} WHERE client_submission_id IS NOT NULL AND client_submission_id <> ''"
        ).fetchall()
        for row in rows:
            payload = payload_builder(row)
            if resource_type == "parent_assessment":
                consent = conn.execute(
                    """
                    SELECT consent_version FROM consent_records
                    WHERE user_id = ? AND consent_type = 'research_authorization'
                      AND agreed = ? AND created_at <= ?
                    ORDER BY created_at DESC LIMIT 1
                    """,
                    (row["user_id"], row["research_consent"], row["created_at"]),
                ).fetchone()
                payload.update(
                    {
                        "consent_version": consent["consent_version"] if consent else "2026.07-consent-v2",
                        "participant_code": str(row["participant_code"] or ""),
                        "study_batch": str(row["study_batch"] or ""),
                        "source_channel": str(row["source_channel"] or "safehome-web"),
                        "started_at": row["started_at"],
                        "completed_at": row["completed_at"],
                        "free_text": "",
                        "raw_text": "",
                        "reflection_text": "",
                    }
                )
            request_hash = canonical_request_hash(
                actor_id=str(row["user_id"]),
                endpoint=endpoint,
                version="v1",
                payload=payload,
            )
            conn.execute(
                f"UPDATE {table} SET request_hash = ? WHERE id = ? AND request_hash IS NULL",
                (request_hash, row["id"]),
            )
            _insert_legacy_idempotency_record(
                conn,
                actor_id=str(row["user_id"]),
                endpoint=endpoint,
                idempotency_key=str(row["client_submission_id"]),
                request_hash=request_hash,
                resource_type=resource_type,
                resource_id=str(row["id"]),
                created_at=str(row["created_at"]),
            )


def _insert_legacy_idempotency_record(
    conn,
    *,
    actor_id: str,
    endpoint: str,
    idempotency_key: str,
    request_hash: str,
    resource_type: str,
    resource_id: str,
    created_at: str,
) -> None:
    params = (
        new_id("idem"),
        actor_id,
        endpoint,
        idempotency_key,
        request_hash,
        resource_type,
        resource_id,
        created_at,
        now_iso(),
    )
    if _provider(conn) == "mysql":
        conn.execute(
            """
            INSERT IGNORE INTO core_idempotency_records (
                id, actor_id, endpoint, idempotency_key, request_hash,
                resource_type, resource_id, status, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, 'committed', ?, ?)
            """,
            params,
        )
    else:
        conn.execute(
            """
            INSERT INTO core_idempotency_records (
                id, actor_id, endpoint, idempotency_key, request_hash,
                resource_type, resource_id, status, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, 'committed', ?, ?)
            ON CONFLICT(actor_id, endpoint, idempotency_key) DO NOTHING
            """,
            params,
        )


def _apply_2026_08_24_066(conn) -> None:
    _execute_schema(
        conn,
        """
        CREATE TABLE IF NOT EXISTS core_side_effect_ledger (
            id TEXT PRIMARY KEY,
            idempotency_record_id TEXT NOT NULL,
            effect_type TEXT NOT NULL,
            effect_key TEXT NOT NULL,
            status TEXT NOT NULL,
            external_reference TEXT,
            metadata_json TEXT NOT NULL DEFAULT '{}',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            UNIQUE(idempotency_record_id, effect_type, effect_key)
        )
        """,
    )
    for name, table, columns in (
        (
            "idx_core_side_effect_status",
            "core_side_effect_ledger",
            "effect_type, status, updated_at",
        ),
        (
            "idx_core_side_effect_record",
            "core_side_effect_ledger",
            "idempotency_record_id",
        ),
    ):
        _create_index_if_missing(conn, name, table, columns)


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
    Migration(
        version="2026_08_07_063",
        name="engineering_ai_runtime_foundation",
        apply=_apply_2026_08_07_063,
        rollback_notes=(
            "Disable RAG_V2_ENABLED and all Agent execution before rollback.",
            "Keep embedding columns in place unless a separate destructive migration is approved; legacy vector_json remains valid.",
            "Export agent_runs and agent_tool_calls if they contain audit evidence before dropping them.",
            "Agent tables contain hashes/metadata only and must never be repurposed as a participant-text store.",
        ),
    ),
    Migration(
        version="2026_08_24_064",
        name="core_write_idempotency_schema",
        apply=_apply_2026_08_24_064,
        rollback_notes=(
            "Stop core writes before rollback.",
            "Keep request_hash columns unless a separate destructive migration is approved.",
            "Drop core_idempotency_records only after exporting its actor/key/resource bindings.",
        ),
    ),
    Migration(
        version="2026_08_24_065",
        name="core_write_idempotency_backfill",
        apply=_apply_2026_08_24_065,
        rollback_notes=(
            "Stop core writes before rollback.",
            "Backfilled request hashes and idempotency records are additive and should normally remain.",
            "Never delete primary business records when rolling back this backfill.",
        ),
    ),
    Migration(
        version="2026_08_24_066",
        name="core_side_effect_ledger",
        apply=_apply_2026_08_24_066,
        rollback_notes=(
            "Stop side-effect producers before rollback.",
            "Export unresolved and externally committed ledger rows before any table removal.",
            "Do not mark external actions as reverted merely because the application transaction rolled back.",
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
    prevents multiple CloudBase/Gunicorn instances from racing on additive
    columns or check-then-create indexes during a rolling start. After waiting
    for the lock, every migration is rechecked before it is applied.
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
    return [
        {
            "version": item.version,
            "name": item.name,
            "rollback_notes": list(item.rollback_notes),
        }
        for item in MIGRATIONS
    ]
