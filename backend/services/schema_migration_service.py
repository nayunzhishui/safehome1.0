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

from database import (
    audit_event_hash,
    ensure_column,
    json_loads,
    mysqlize_column_definition,
    mysqlize_schema_statement,
    new_id,
    now_iso,
)
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


def _apply_2026_08_24_067(conn) -> None:
    for column, definition in {
        "bind_code_hash": "TEXT",
        "bind_code_tail": "TEXT",
        "version": "INTEGER NOT NULL DEFAULT 1",
        "locked_until": "TEXT",
        "lock_reason": "TEXT",
    }.items():
        ensure_column(conn, "family_links", column, definition)
    _create_index_if_missing(
        conn,
        "idx_family_links_code_hash_status",
        "family_links",
        "bind_code_hash, status",
    )


def _apply_2026_08_24_068(conn) -> None:
    from services.family_binding_service import hash_bind_code, redact_bind_code

    _execute_schema(
        conn,
        """
        CREATE TABLE IF NOT EXISTS family_bind_rate_limits (
            id TEXT PRIMARY KEY,
            dimension TEXT NOT NULL,
            dimension_hash TEXT NOT NULL,
            window_key TEXT NOT NULL,
            attempt_count INTEGER NOT NULL DEFAULT 1,
            locked_until TEXT,
            last_attempt_at TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            UNIQUE(dimension, dimension_hash, window_key)
        )
        """,
    )
    rows = conn.execute(
        "SELECT id, bind_code, bind_code_hash, status FROM family_links"
    ).fetchall()
    for row in rows:
        plaintext = str(row["bind_code"] or "")
        if plaintext.isdigit():
            conn.execute(
                """
                UPDATE family_links
                SET bind_code = ?, bind_code_hash = ?, bind_code_tail = ?, version = version + 1
                WHERE id = ?
                """,
                (
                    redact_bind_code(plaintext),
                    row["bind_code_hash"] or hash_bind_code(plaintext),
                    plaintext[-4:],
                    row["id"],
                ),
            )
        elif not plaintext.startswith("redacted:"):
            conn.execute(
                "UPDATE family_links SET bind_code = 'redacted:unknown', version = version + 1 WHERE id = ?",
                (row["id"],),
            )
        if not row["bind_code_hash"] and not plaintext.isdigit() and row["status"] == "pending":
            timestamp = now_iso()
            conn.execute(
                """
                UPDATE family_links
                SET status = 'revoked', revoked_at = ?, updated_at = ?, version = version + 1
                WHERE id = ?
                """,
                (timestamp, timestamp, row["id"]),
            )
    timestamp = now_iso()
    conn.execute(
        """
        UPDATE family_links
        SET status = 'consumed', updated_at = ?, version = version + 1
        WHERE status = 'active'
        """,
        (timestamp,),
    )
    _create_index_if_missing(
        conn,
        "idx_family_bind_rate_limits_lookup",
        "family_bind_rate_limits",
        "dimension, dimension_hash, window_key",
    )


def _apply_2026_08_25_069(conn) -> None:
    for statement in (
        """
        CREATE TABLE IF NOT EXISTS safety_scheduler_runtime (
            id TEXT PRIMARY KEY, paused INTEGER NOT NULL DEFAULT 0,
            kill_switch INTEGER NOT NULL DEFAULT 0, reason TEXT,
            disabled_scopes_json TEXT NOT NULL DEFAULT '[]', lease_owner TEXT,
            lease_expires_at TEXT, last_started_at TEXT, last_success_at TEXT,
            last_failure_at TEXT, backlog_count INTEGER NOT NULL DEFAULT 0,
            oldest_due_age_seconds INTEGER NOT NULL DEFAULT 0,
            claim_failure_count INTEGER NOT NULL DEFAULT 0,
            dead_letter_count INTEGER NOT NULL DEFAULT 0,
            backfill_required INTEGER NOT NULL DEFAULT 0,
            version INTEGER NOT NULL DEFAULT 1, updated_at TEXT NOT NULL
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS safety_scheduler_runs (
            id TEXT PRIMARY KEY, run_key TEXT NOT NULL UNIQUE,
            worker_id TEXT NOT NULL, status TEXT NOT NULL,
            attempt_count INTEGER NOT NULL DEFAULT 0,
            max_attempts INTEGER NOT NULL DEFAULT 3, started_at TEXT NOT NULL,
            lease_expires_at TEXT, finished_at TEXT, error_code TEXT,
            stats_json TEXT NOT NULL DEFAULT '{}', created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS safety_scheduler_events (
            id TEXT PRIMARY KEY, event_key TEXT NOT NULL UNIQUE,
            source_type TEXT NOT NULL, source_id TEXT NOT NULL,
            action TEXT NOT NULL, due_at TEXT, metadata_json TEXT NOT NULL DEFAULT '{}',
            created_at TEXT NOT NULL
        )
        """,
    ):
        _execute_schema(conn, statement)


def _apply_2026_08_25_070(conn) -> None:
    timestamp = now_iso()
    if conn.execute(
        "SELECT id FROM safety_scheduler_runtime WHERE id = 'global'"
    ).fetchone() is None:
        conn.execute(
            """INSERT INTO safety_scheduler_runtime
            (id, paused, kill_switch, disabled_scopes_json, version, updated_at)
            VALUES ('global', 0, 0, '[]', 1, ?)""",
            (timestamp,),
        )
    _create_index_if_missing(
        conn,
        "idx_safety_scheduler_runs_status_started",
        "safety_scheduler_runs",
        "status, started_at",
    )
    _create_index_if_missing(
        conn,
        "idx_safety_scheduler_events_source",
        "safety_scheduler_events",
        "source_type, source_id, created_at",
    )


def _apply_2026_08_25_071(conn) -> None:
    for statement in (
        """
        CREATE TABLE IF NOT EXISTS content_release_artifacts (
            id TEXT PRIMARY KEY, filename TEXT NOT NULL,
            payload_text TEXT NOT NULL, artifact_hash TEXT NOT NULL,
            schema_version TEXT NOT NULL, metadata_json TEXT NOT NULL DEFAULT '{}',
            status TEXT NOT NULL DEFAULT 'verified', created_by TEXT NOT NULL,
            created_at TEXT NOT NULL, UNIQUE(filename, artifact_hash)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS content_active_artifacts (
            filename TEXT PRIMARY KEY, artifact_id TEXT NOT NULL,
            generation INTEGER NOT NULL DEFAULT 1, switch_reason TEXT NOT NULL,
            impact_scope_json TEXT NOT NULL DEFAULT '[]', updated_by TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """,
    ):
        _execute_schema(conn, statement)


def _apply_2026_08_25_072(conn) -> None:
    ensure_column(conn, "content_governance_releases", "artifact_id", "TEXT")
    _create_index_if_missing(
        conn,
        "idx_content_artifacts_file_created",
        "content_release_artifacts",
        "filename, created_at",
    )
    _create_index_if_missing(
        conn,
        "idx_content_active_artifact",
        "content_active_artifacts",
        "artifact_id",
    )


def _apply_2026_08_25_073(conn) -> None:
    for statement in (
        """CREATE TABLE IF NOT EXISTS research_source_objects (
            id TEXT PRIMARY KEY, source_id TEXT NOT NULL, source_type TEXT NOT NULL,
            storage_path TEXT NOT NULL, payload_blob LONGBLOB NOT NULL,
            server_hash TEXT NOT NULL, size_bytes INTEGER NOT NULL,
            data_mode TEXT NOT NULL, rights_status TEXT NOT NULL,
            owner_scope TEXT NOT NULL, retention_policy TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'verified', created_by TEXT NOT NULL,
            created_at TEXT NOT NULL, UNIQUE(source_id, server_hash))""",
        """CREATE TABLE IF NOT EXISTS research_execution_manifests (
            id TEXT PRIMARY KEY, job_id TEXT NOT NULL, attempt_number INTEGER NOT NULL,
            source_object_id TEXT NOT NULL, source_hash TEXT NOT NULL, code_commit TEXT NOT NULL,
            execution_environment TEXT NOT NULL, execution_image_ref TEXT NOT NULL,
            runtime_version TEXT NOT NULL, dependency_hash TEXT NOT NULL,
            algorithm_version TEXT NOT NULL, model_version TEXT NOT NULL,
            dictionary_hash TEXT NOT NULL, thresholds_hash TEXT NOT NULL,
            input_snapshot_hash TEXT NOT NULL, random_seed INTEGER NOT NULL,
            parameters_json TEXT NOT NULL DEFAULT '{}', metrics_hash TEXT, result_hash TEXT,
            result_reference TEXT, log_summary_json TEXT NOT NULL DEFAULT '{}',
            log_digest TEXT, manifest_hash TEXT,
            reproducibility_key TEXT NOT NULL, reproducibility_status TEXT, failure_code TEXT,
            status TEXT NOT NULL DEFAULT 'prepared',
            created_by TEXT NOT NULL, created_at TEXT NOT NULL, completed_at TEXT,
            consumed_at TEXT,
            UNIQUE(job_id, attempt_number))""",
    ):
        _execute_schema(conn, statement)


def _apply_2026_08_25_074(conn) -> None:
    ensure_column(conn, "research_analysis_artifacts", "execution_manifest_id", "TEXT")
    _create_index_if_missing(conn, "idx_research_source_hash", "research_source_objects", "server_hash, status")
    _create_index_if_missing(conn, "idx_research_manifest_job_status", "research_execution_manifests", "job_id, status, created_at")
    _create_index_if_missing(conn, "idx_research_manifest_reproducibility", "research_execution_manifests", "reproducibility_key, status, created_at")
    _create_index_if_missing(conn, "idx_research_artifact_manifest", "research_analysis_artifacts", "execution_manifest_id")


def _apply_2026_08_25_075(conn) -> None:
    _execute_schema(
        conn,
        """CREATE TABLE IF NOT EXISTS ai_capability_decisions (
            id TEXT PRIMARY KEY, actor_id TEXT, actor_role TEXT NOT NULL,
            operation TEXT NOT NULL, environment TEXT NOT NULL,
            audience TEXT NOT NULL, enabled INTEGER NOT NULL,
            provider TEXT NOT NULL, real_provider_allowed INTEGER NOT NULL,
            reason_code TEXT NOT NULL, policy_version TEXT NOT NULL,
            data_mode TEXT NOT NULL, created_at TEXT NOT NULL
        )""",
    )
    _create_index_if_missing(
        conn,
        "idx_ai_capability_decisions_actor_created",
        "ai_capability_decisions",
        "actor_id, created_at",
    )
    _create_index_if_missing(
        conn,
        "idx_ai_capability_decisions_reason_created",
        "ai_capability_decisions",
        "reason_code, created_at",
    )


def _apply_2026_08_25_076(conn) -> None:
    for column, definition in {
        "content_snapshot_json": "TEXT NOT NULL DEFAULT '{}'",
        "content_snapshot_hash": "TEXT",
        "worksheet_payload_hash": "TEXT",
        "worksheet_version": "TEXT",
        "interpretation_version": "TEXT",
    }.items():
        ensure_column(conn, "assessment_results", column, definition)


def _apply_2026_08_26_077(conn) -> None:
    for column, definition in {
        "claim_token_digest": "TEXT",
        "claim_token_expires_at": "TEXT",
        "claim_token_used_at": "TEXT",
        "attempt_count": "INTEGER NOT NULL DEFAULT 0",
        "locked_until": "TEXT",
    }.items():
        ensure_column(conn, "data_claims", column, definition)
    if _provider(conn) == "mysql":
        digest_definition = mysqlize_column_definition("claim_token_digest", "TEXT")
        conn.execute(
            "ALTER TABLE data_claims MODIFY COLUMN claim_token_digest "
            f"{digest_definition} NULL"
        )
    _create_index_if_missing(
        conn,
        "idx_data_claim_target_digest",
        "data_claims",
        "target_user_id, claim_token_digest",
    )


def _apply_2026_08_26_078(conn) -> None:
    for column, definition in {
        "sequence_no": "INTEGER",
        "previous_hash": "TEXT",
        "event_hash": "TEXT",
        "hash_version": "TEXT",
    }.items():
        ensure_column(conn, "audit_logs", column, definition)
    _execute_schema(
        conn,
        """CREATE TABLE IF NOT EXISTS audit_chain_state (
            singleton_id INTEGER PRIMARY KEY,
            last_sequence INTEGER NOT NULL DEFAULT 0,
            last_hash TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )""",
    )
    rows = conn.execute(
        "SELECT id, actor_id, action, target_type, target_id, metadata_json, created_at FROM audit_logs ORDER BY created_at ASC, id ASC"
    ).fetchall()
    previous_hash = ""
    for sequence_no, raw in enumerate(rows, start=1):
        row = dict(raw)
        event_hash = audit_event_hash(
            audit_id=row["id"],
            sequence_no=sequence_no,
            previous_hash=previous_hash,
            actor_id=row.get("actor_id"),
            action=row["action"],
            target_type=row.get("target_type"),
            target_id=row.get("target_id"),
            metadata_json=row["metadata_json"],
            created_at=row["created_at"],
        )
        conn.execute(
            "UPDATE audit_logs SET sequence_no = ?, previous_hash = ?, event_hash = ?, hash_version = 'sha256-v1' WHERE id = ?",
            (sequence_no, previous_hash, event_hash, row["id"]),
        )
        previous_hash = event_hash
    conn.execute("DELETE FROM audit_chain_state WHERE singleton_id = 1")
    conn.execute(
        "INSERT INTO audit_chain_state (singleton_id, last_sequence, last_hash, updated_at) VALUES (1, ?, ?, ?)",
        (len(rows), previous_hash, now_iso()),
    )
    _create_index_if_missing(conn, "idx_audit_logs_sequence", "audit_logs", "sequence_no")


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
    Migration(
        version="2026_08_24_067",
        name="family_binding_code_digest",
        apply=_apply_2026_08_24_067,
        rollback_notes=(
            "Stop family binding writes before rollback.",
            "Keep digest, tail, version and lock columns because they contain no plaintext binding code.",
            "Do not restore plaintext codes; revoke pending codes if the previous application cannot read digests.",
        ),
    ),
    Migration(
        version="2026_08_24_068",
        name="family_binding_rate_limits_and_plaintext_backfill",
        apply=_apply_2026_08_24_068,
        rollback_notes=(
            "Stop family binding writes before rollback.",
            "Preserve the rate-limit ledger for abuse investigation and retention review.",
            "Never restore plaintext binding codes; revoke pending codes before running an application version that lacks digest lookup.",
            "Consumed and revoked family relationships remain business records and must not be deleted by rollback.",
        ),
    ),
    Migration(
        version="2026_08_25_069",
        name="safety_scheduler_lease_and_event_ledger",
        apply=_apply_2026_08_25_069,
        rollback_notes=(
            "Stop scheduler workers before application rollback.",
            "Preserve scheduler runs and events as operational safety evidence.",
            "Do not restore read-triggered timeout processing as the only safety clock.",
        ),
    ),
    Migration(
        version="2026_08_25_070",
        name="safety_scheduler_runtime_backfill",
        apply=_apply_2026_08_25_070,
        rollback_notes=(
            "Keep the global runtime row, dead letters and pause state.",
            "Rollback may stop new workers but must not clear an active kill switch.",
            "Human evidence remains required before resuming paused automation.",
        ),
    ),
    Migration(
        version="2026_08_25_071",
        name="immutable_content_artifacts",
        apply=_apply_2026_08_25_071,
        rollback_notes=(
            "Disable content publishing before application rollback.",
            "Preserve immutable artifact rows and active-pointer audit facts.",
            "Do not copy governed payloads back into a container filesystem.",
        ),
    ),
    Migration(
        version="2026_08_25_072",
        name="content_artifact_pointer_binding",
        apply=_apply_2026_08_25_072,
        rollback_notes=(
            "Keep release-to-artifact bindings for audit and rollback.",
            "Rollback only by switching to a previously verified artifact.",
            "Never delete the active artifact before all instances stop reading it.",
        ),
    ),
    Migration(
        version="2026_08_25_073",
        name="research_server_source_and_execution_manifest",
        apply=_apply_2026_08_25_073,
        rollback_notes=(
            "Stop research workers before rollback.",
            "Preserve server-computed source objects and execution manifests as audit evidence.",
            "Do not replace server hashes with client-declared values.",
        ),
    ),
    Migration(
        version="2026_08_25_074",
        name="research_artifact_manifest_binding",
        apply=_apply_2026_08_25_074,
        rollback_notes=(
            "Keep artifact-to-manifest bindings and completed manifests.",
            "Disable generic completion rather than accepting unproved metrics.",
            "Derived artifacts remain subject to consent withdrawal and deletion rules.",
        ),
    ),
    Migration(
        version="2026_08_25_075",
        name="ai_capability_decision_ledger",
        apply=_apply_2026_08_25_075,
        rollback_notes=(
            "Keep AI capability decisions as audit evidence.",
            "Disable AI routes before application rollback.",
            "Never treat rollback as approval to enable participant AI.",
        ),
    ),
    Migration(
        version="2026_08_25_076",
        name="assessment_content_snapshot",
        apply=_apply_2026_08_25_076,
        rollback_notes=(
            "Stop assessment writes before application rollback.",
            "Preserve immutable assessment content snapshots with historical results.",
            "Do not replace stored worksheet payloads with the current content version.",
            "The additive columns may remain unused by an older application version.",
        ),
    ),
    Migration(
        version="2026_08_26_077",
        name="anonymous_claim_token_digest",
        apply=_apply_2026_08_26_077,
        rollback_notes=(
            "Stop anonymous claim writes before application rollback.",
            "Preserve token digests and consumption timestamps for abuse review; never restore plaintext tokens.",
            "Revoke unconsumed claims before running an application that cannot validate digest-backed tokens.",
        ),
    ),
    Migration(
        version="2026_08_26_078",
        name="audit_tamper_evident_chain",
        apply=_apply_2026_08_26_078,
        rollback_notes=(
            "Stop audit writers before application rollback.",
            "Preserve sequence and chain hash columns as audit evidence.",
            "The chain detects modification but is not an external immutable archive.",
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
