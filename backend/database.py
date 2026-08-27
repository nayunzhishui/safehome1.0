"""Database helpers for the SafeHome MVP backend."""

import hashlib
import json
import re
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path

from config import Config
from models import IDENTITY_UNIQUE_INDEX_SQL, INDEX_SQL, SCHEMA_SQL
from services.database_profile_service import (
    granted_privileges,
    public_database_fingerprint,
    runtime_profile_errors,
)


REQUIRED_HEALTH_TABLES = [
    "users",
    "schema_migrations",
    "assessment_worksheets",
    "assessment_results",
    "emotion_diaries",
    "emotion_thermometer",
    "feedback_results",
    "student_profiles",
    "risk_review_records",
    "audit_logs",
    "family_bind_rate_limits",
    "safety_scheduler_runtime",
    "safety_scheduler_runs",
    "safety_scheduler_events",
    "core_idempotency_records",
    "core_side_effect_ledger",
    "consent_records",
    "consent_record_annotations",
    "records",
    "messages",
    "notification_preferences",
    "notification_deliveries",
    "research_work_items",
    "research_work_item_notes",
    "research_work_item_actions",
    "data_claims",
    "identity_merge_workflows",
    "identity_merge_record_links",
    "relationship_pilot_enrollments",
    "relationship_screening_reports",
    "relationship_pilot_tasks",
    "relationship_research_notes",
    "relationship_narratives",
    "relationship_longitudinal_entries",
    "relationship_hypothesis_feedback",
    "research_scope_assignments",
    "research_scope_assignment_actions",
    "research_delivery_workflows",
    "research_delivery_versions",
    "research_delivery_events",
    "feedback_ledger",
    "feedback_ledger_actions",
    "recommendation_snapshots",
    "privacy_request_actions",
    "privacy_request_approvals",
    "privacy_request_executions",
    "privacy_deletion_tombstones",
    "content_governance_versions",
    "content_governance_reviews",
    "content_governance_releases",
    "ai_qa_sessions",
    "ai_qa_messages",
    "ai_qa_feedback",
    "ai_qa_safety_events",
    "ai_qa_provider_events",
    "ai_knowledge_documents",
    "ai_knowledge_chunks",
    "ai_knowledge_candidates",
    "ai_knowledge_evaluation_runs",
    "ai_provider_contract_evidence",
    "ai_qa_evaluation_runs",
    "ai_qa_evaluation_reviews",
    "ai_qa_runtime_control",
    "offline_dataset_cards",
    "offline_benchmark_runs",
    "offline_benchmark_annotations",
    "offline_annotation_adjudications",
    "offline_annotation_group_splits",
    "offline_benchmark_reviews",
    "offline_benchmark_runtime_control",
    "offline_model_versions",
    "offline_model_shadow_runs",
    "offline_model_review_queue",
    "offline_model_monitor_runs",
    "offline_model_runtime_controls",
    "offline_model_release_gate_runs",
    "offline_model_release_evidence",
    "research_methodology_versions",
    "research_methodology_checks",
    "research_methodology_simulation_runs",
    "research_methodology_evidence_packages",
    "research_methodology_runtime_control",
    "security_control_runs",
    "security_events",
    "privacy_deletion_verifications",
    "observability_events",
    "reliable_jobs",
    "reliable_job_actions",
    "research_analysis_snapshots",
    "research_analysis_snapshot_links",
    "research_analysis_jobs",
    "research_analysis_artifacts",
    "research_analysis_events",
    "feature_flag_versions",
    "reliability_slo_snapshots",
    "reliability_drill_runs",
    "reliability_evidence_packages",
    "ux_audit_runs",
    "ux_evidence_packages",
    "operations_release_packages",
    "operations_package_reviews",
    "operations_replay_runs",
    "operations_runtime_controls",
    "operations_monitor_snapshots",
    "operations_incidents",
    "operations_incident_notifications",
    "operations_evidence_packages",
    "therapeutic_assessment_cases",
    "therapeutic_assessment_feedback_versions",
    "therapeutic_assessment_feedback_deliveries",
    "therapeutic_assessment_feedback_responses",
    "therapeutic_assessment_evidence_items",
    "therapeutic_assessment_data_items",
    "therapeutic_assessment_data_consents",
    "therapeutic_assessment_participant_drafts",
    "therapeutic_assessment_participant_draft_events",
    "therapeutic_assessment_responsibility_chains",
    "therapeutic_assessment_safety_events",
    "therapeutic_assessment_runtime_control",
    "therapeutic_assessment_researcher_workbench_drafts",
    "therapeutic_assessment_researcher_workbench_draft_events",
    "therapeutic_assessment_actions",
    "therapeutic_assessment_authorizations",
    "therapeutic_assessment_authorization_events",
    "therapeutic_assessment_quality_reviews",
    "therapeutic_assessment_quality_incidents",
    "therapeutic_assessment_quality_events",
    "therapeutic_assessment_contract_snapshots",
    "therapeutic_assessment_work_queue",
    "therapeutic_assessment_queue_events",
    "therapeutic_assessment_duty_shifts",
    "therapeutic_assessment_duty_events",
    "therapeutic_assessment_queue_runtime",
    "publication_candidates",
    "publication_gate_checks",
    "publication_candidate_events",
    "ai_qa_review_cases",
    "ai_qa_review_actions",
    "ai_qa_circuit_states",
    "ai_qa_release_state",
    "ai_qa_release_events",
    "ai_qa_release_evidence_packages",
    "therapeutic_assessment_release_evidence",
    "therapeutic_assessment_release_gate_runs",
    "therapeutic_assessment_release_gate_checks",
    "therapeutic_assessment_quality_runtime",
    "therapeutic_assessment_events",
    "therapeutic_assessment_launch_screenings",
    "therapeutic_assessment_child_safeguards",
    "therapeutic_assessment_multi_party_safeguards",
    "therapeutic_assessment_ai_assist_candidates",
    "therapeutic_assessment_stop_incidents",
    "therapeutic_assessment_recovery_evidence",
    "computation_datasets",
    "computation_authorization_snapshots",
    "computation_lineage_edges",
    "computation_deletion_tombstones",
    "computation_legal_holds",
]
CURRENT_SCHEMA_VERSION = "2026_08_24_063"
CURRENT_SCHEMA_NAME = "rc0810_f07_consent_provenance"
IDENTITY_FIELDS = ("username", "wechat_openid", "phone_hash")
MYSQL_INDEXABLE_VARCHAR_LENGTH = 191
MYSQL_VARCHAR_COLUMNS = {
    "id",
    "version",
    "name",
    "user_id",
    "target_user_id",
    "source_user_id",
    "participant_user_id",
    "guardian_user_id",
    "child_user_id",
    "merged_into_user_id",
    "requested_by",
    "confirmed_by",
    "table_name",
    "record_id",
    "column_name",
    "nickname",
    "role",
    "username",
    "phone_or_email",
    "phone_hash",
    "enrollment_id",
    "assigned_researcher_id",
    "assignment_role",
    "assigned_by",
    "assignment_id",
    "snapshot_id",
    "execution_manifest_id",
    "analysis_type",
    "analysis_version",
    "resource_hash",
    "purpose_code",
    "consent_type",
    "consent_version",
    "purpose",
    "processor",
    "text_hash",
    "event_type",
    "authorization_status",
    "source_type",
    "source_version",
    "source_hash",
    "idempotency_key",
    "lease_owner",
    "result_artifact_id",
    "artifact_hash",
    "artifact_id",
    "filename",
    "package_hash",
    "quality_status",
    "visibility",
    "deletion_reason_code",
    "request_hash",
    "endpoint",
    "resource_type",
    "resource_id",
    "effect_type",
    "effect_key",
    "external_reference",
    "idempotency_record_id",
    "report_id",
    "response",
    "assessment_result_id",
    "idempotency_key",
    "entry_id",
    "action",
    "from_status",
    "to_status",
    "replacement_entry_id",
    "strategy_version",
    "previous_strategy_version",
    "client_submission_id",
    "job_type",
    "flag_name",
    "journey",
    "scenario",
    "environment",
    "platform",
    "viewport",
    "credential_receipt_id",
    "registry_version",
    "package_version",
    "package_id",
    "previous_package_id",
    "target_environment",
    "capability_id",
    "stage",
    "domain",
    "decision",
    "evidence_ref",
    "snapshot_hash",
    "state",
    "reason_code",
    "dataset_key",
    "dataset_id",
    "subject_hash",
    "parent_resource_type",
    "parent_resource_id",
    "child_resource_type",
    "child_resource_id",
    "root_resource_type",
    "root_resource_id",
    "scope_type",
    "scope_id",
    "released_at",
    "incident_type",
    "severity",
    "summary_code",
    "recipient_role",
    "reported_at",
    "postmortem_at",
    "dispatched_at",
    "password_hash",
    "wechat_openid",
    "avatar_url",
    "status",
    "last_login_at",
    "source",
    "created_at",
    "updated_at",
    "next_probe_at",
    "applied_at",
    "goal_id",
    "diary_id",
    "card_id",
    "scene",
    "parent_emotion",
    "child_emotion",
    "type",
    "title",
    "status",
    "worksheet_id",
    "worksheet_title",
    "category",
    "audience_class",
    "reflex_node",
    "review_status",
    "profile_model_id",
    "dimension_score_method",
    "display_title",
    "source_title",
    "sensitive_category",
    "source_version",
    "source_type",
    "audience",
    "audience_class_detail",
    "anonymous_id",
    "assessment_result_id",
    "profile_code",
    "profile_name",
    "risk_level",
    "rules_version",
    "model_version",
    "model_type",
    "module_type",
    "legacy_source_id",
    "legacy_source_table",
    "data_quality",
    "profile_id",
    "fit",
    "task_done",
    "task_title",
    "participant_code",
    "study_batch",
    "source_channel",
    "questionnaire_version",
    "scoring_version",
    "profile_key",
    "started_at",
    "completed_at",
    "submission_id",
    "action_key",
    "reviewer_id",
    "review_status",
    "review_decision",
    "target_type",
    "target_id",
    "actor_id",
    "workflow_id",
    "delivery_id",
    "active_version_id",
    "source_report_id",
    "message_id",
    "session_id",
    "review_case_id",
    "draft_author_id",
    "publication_candidate_id",
    "required_task_code",
    "required_competency",
    "published_by",
    "candidate_sha256",
    "final_sha256",
    "request_sha256",
    "create_idempotency_key",
    "delivery_type",
    "content_hash",
    "created_by",
    "risk_level",
    "action",
    "consent_type",
    "consent_version",
    "agreed_at",
    "revoked_at",
    "source_type",
    "source_id",
    "request_type",
    "handled_by",
    "parent_user_id",
    "student_user_id",
    "bind_code",
    "bind_code_hash",
    "dimension",
    "dimension_hash",
    "window_key",
    "run_key",
    "event_key",
    "source_type",
    "relation_label",
    "expires_at",
    "last_attempt_at",
    "confirmed_at",
    "closed_reason",
    "reviewed_at",
    "week_start",
    "week_end",
    "replied_at",
    "message_type",
    "sender_id",
    "sender_role",
    "read_at",
    "channel",
    "notification_type",
    "template_id",
    "subscription_mode",
    "consent_status",
    "consent_source",
    "consented_at",
    "last_prompted_at",
    "schedule_key",
    "scheduled_for",
    "sent_at",
    "provider_message_id",
    "error_code",
    "retry_category",
    "next_attempt_at",
    "dead_lettered_at",
    "last_attempt_at",
    "queue_type",
    "assignee_id",
    "lease_expires_at",
    "due_at",
    "resolution_code",
    "closed_at",
    "last_action_at",
    "work_item_id",
    "actor_role",
    "note_type",
    "content_version",
    "evaluation",
    "reason_code",
    "scope_hash",
    "policy_version",
    "decision",
    "environment",
    "mode",
    "proof_hash",
    "replacement_user_id",
    "subject_hash",
    "content_type",
    "item_id",
    "parent_version_id",
    "payload_hash",
    "created_by",
    "submitted_at",
    "published_at",
    "retired_at",
    "version_id",
    "release_id",
    "document_id",
    "document_version",
    "rights_status",
    "retrieval_method",
    "discipline",
    "reviewer_role",
    "evidence_path",
    "previous_release_id",
    "release_reason",
    "released_by",
    "context_policy",
    "deleted_at",
    "session_id",
    "prompt_version",
    "knowledge_version",
    "message_id",
    "request_hash",
    "request_id",
    "case_id",
    "verified_at",
    "job_id",
    "available_at",
    "severity",
    "outcome",
    "provider",
    "model_version",
    "error_code",
    "suite_version",
    "provider_version",
    "knowledge_snapshot_hash",
    "run_id",
    "changed_by",
    "changed_at",
    "dataset_card_id",
    "benchmark_type",
    "evidence_level",
    "algorithm_version",
    "artifact_hash",
    "ingest_status",
    "registry_version",
    "registry_hash",
    "check_type",
    "simulation_version",
    "transformation_version",
    "annotator_id",
    "blind_round",
    "emotion_label",
    "context_label",
    "reflex_node",
    "reviewer_id",
    "recorded_by",
    "evidence_type",
    "trigger_code",
    "incident_id",
    "provider_id",
    "verification_idempotency_key",
    "verified_by",
    "group_hash",
    "split_name",
    "gate_status",
    "evidence_hash",
    "gate_id",
    "recorded_at",
    "generated_at",
    "reason",
    "shadow_run_id",
    "model_version_id",
    "asset_manifest_hash",
    "candidate_id",
    "subject_id",
    "subject_type",
    "gate_name",
    "task_code",
    "contract_hash",
    "contract_version",
    "provider_user_id",
    "starts_at",
    "author_id",
    "kind",
    "feedback_id",
    "sent_by",
    "draft_id",
    "step_id",
    "reporter_user_id",
    "evaluated_by",
    "researcher_user_id",
    "detected_by",
}


_VALID_TABLE_NAME = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")
_VALID_COLUMN_NAME = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")


def is_mysql_enabled() -> bool:
    return Config.DB_PROVIDER == "mysql"


class MySQLConnection:
    """Small DB-API adapter so existing sqlite-style route code can run on MySQL."""

    provider = "mysql"

    def __init__(self):
        try:
            import pymysql
        except ImportError as exc:
            raise RuntimeError("DB_PROVIDER=mysql 时需要安装 PyMySQL") from exc

        from services.database_recovery_service import mysql_ssl_context

        self._connection = pymysql.connect(
            host=Config.MYSQL_HOST,
            port=Config.MYSQL_PORT,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD,
            database=Config.MYSQL_DATABASE,
            charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=False,
            connect_timeout=Config.MYSQL_CONNECT_TIMEOUT_SECONDS,
            read_timeout=Config.MYSQL_READ_TIMEOUT_SECONDS,
            write_timeout=Config.MYSQL_WRITE_TIMEOUT_SECONDS,
            ssl=mysql_ssl_context(Config.MYSQL_SSL_CA, Config.MYSQL_TLS_MIN_VERSION)
            if Config.MYSQL_SSL_CA
            else None,
        )

    def __enter__(self):
        self._connection.ping(reconnect=True)
        return self

    def __exit__(self, exc_type, exc, traceback):
        if exc_type is None:
            self.commit()
        else:
            try:
                self._connection.rollback()
            except Exception:
                pass
        self.close()
        return False

    def execute(self, sql: str, params=None):
        self._connection.ping(reconnect=True)
        cursor = self._connection.cursor()
        cursor.execute(_mysqlize_query(sql), tuple(params or ()))
        return cursor

    def commit(self) -> None:
        self._connection.commit()

    def rollback(self) -> None:
        self._connection.rollback()

    def close(self) -> None:
        self._connection.close()


def _connection_provider(conn) -> str:
    return getattr(conn, "provider", "sqlite")


def _mysqlize_query(sql: str) -> str:
    converted: list[str] = []
    in_single_quote = False
    in_double_quote = False
    index = 0
    while index < len(sql):
        char = sql[index]
        next_char = sql[index + 1] if index + 1 < len(sql) else ""

        if char == "'" and not in_double_quote:
            converted.append(char)
            if in_single_quote and next_char == "'":
                converted.append(next_char)
                index += 2
                continue
            in_single_quote = not in_single_quote
        elif char == '"' and not in_single_quote:
            converted.append(char)
            if in_double_quote and next_char == '"':
                converted.append(next_char)
                index += 2
                continue
            in_double_quote = not in_double_quote
        elif char == "?" and not in_single_quote and not in_double_quote:
            converted.append("%s")
        else:
            converted.append(char)
        index += 1

    return "".join(converted)


def _mysql_column_line(line: str) -> str:
    match = re.match(r"^(\s*)([A-Za-z_][A-Za-z0-9_]*)\s+TEXT(\b.*)$", line)
    if not match:
        return line

    indent, column, rest = match.groups()
    if "PRIMARY KEY" in rest:
        column_type = "VARCHAR(128)"
    elif column in MYSQL_VARCHAR_COLUMNS:
        column_type = f"VARCHAR({MYSQL_INDEXABLE_VARCHAR_LENGTH})"
    elif column.endswith("_json"):
        column_type = "LONGTEXT"
    elif re.search(r"\bDEFAULT\b", rest, re.IGNORECASE):
        # MySQL 5.7 rejects defaults on TEXT/BLOB columns. Scalar TEXT fields
        # with defaults are bounded status/config values, so keep the default
        # while using an index-friendly VARCHAR representation.
        column_type = f"VARCHAR({MYSQL_INDEXABLE_VARCHAR_LENGTH})"
    else:
        column_type = "TEXT"

    if column_type in {"TEXT", "LONGTEXT"}:
        rest = re.sub(r"\s+DEFAULT\s+'(?:\{\}|\[\])'", "", rest)
    return f"{indent}{column} {column_type}{rest}"


def mysqlize_schema_statement(statement: str) -> str:
    lines = [_mysql_column_line(line) for line in statement.splitlines()]
    return "\n".join(lines).replace("REAL", "DOUBLE")


def mysqlize_column_definition(column: str, definition: str) -> str:
    line = _mysql_column_line(f"{column} {definition}")
    return line.split(" ", 1)[1].replace("REAL", "DOUBLE")


def _parse_index_statement(statement: str) -> tuple[str, str] | None:
    match = re.match(r"\s*CREATE\s+(?:UNIQUE\s+)?INDEX\s+IF\s+NOT\s+EXISTS\s+(\w+)\s+ON\s+(.+)", statement, re.IGNORECASE)
    if not match:
        return None
    return match.group(1), match.group(2)


def _parse_index_target(target: str) -> tuple[str, list[str]] | None:
    match = re.match(r"\s*([A-Za-z_][A-Za-z0-9_]*)\s*\(([^)]+)\)\s*$", target)
    if not match:
        return None
    table = match.group(1)
    columns = [column.strip().strip("`").split()[0] for column in match.group(2).split(",")]
    return table, columns


def get_connection(database_path: str | Path | None = None):
    if database_path is None and is_mysql_enabled():
        return MySQLConnection()
    path = Path(database_path or Config.DATABASE_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Create MVP tables and sync content training cards."""
    with get_connection() as conn:
        for statement in SCHEMA_SQL:
            conn.execute(mysqlize_schema_statement(statement) if _connection_provider(conn) == "mysql" else statement)
        if _connection_provider(conn) == "mysql":
            ensure_mysql_index_columns(conn)
            ensure_mysql_content_text_capacity(conn)
        ensure_schema_columns(conn)
        for statement in INDEX_SQL:
            create_index(conn, statement)
        identity_status = check_identity_uniqueness(conn)
        if identity_status["ok"]:
            for statement in IDENTITY_UNIQUE_INDEX_SQL:
                create_index(conn, statement)
        sync_training_cards(conn)
        sync_assessment_worksheets(conn)
        record_schema_migration(conn)
        conn.commit()


def check_database_health() -> dict:
    """Run a read-only database health check for cloud and deploy diagnostics."""
    path = Path(Config.DATABASE_PATH)
    result = {
        "ok": False,
        "provider": Config.DB_PROVIDER,
        "database_path_parent_exists": path.parent.exists(),
        "database_file_exists": path.exists(),
        "expected_schema_version": CURRENT_SCHEMA_VERSION,
        "current_schema_version": None,
        "explicit_migration_head": None,
        "schema_version_ok": False,
        "profile_ok": False,
        "profile_errors": [],
        "fingerprint": None,
        "required_tables_ok": False,
        "missing_tables": [],
        "training_cards_count": 0,
        "content_training_cards_count": 0,
        "training_cards_sync_ok": False,
        "assessment_worksheets_count": 0,
        "content_assessment_worksheets_count": 0,
        "worksheets_sync_ok": False,
        "identity_uniqueness_ok": False,
        "identity_duplicate_groups": {},
        "identity_unique_indexes_ok": False,
    }
    try:
        with get_connection() as conn:
            rows = list_database_tables(conn)
            result["current_schema_version"] = get_latest_schema_version(conn)
            result["explicit_migration_head"] = get_latest_explicit_migration_version(conn)
            result["schema_version_ok"] = result["current_schema_version"] == CURRENT_SCHEMA_VERSION
            result["training_cards_count"] = get_table_count(conn, "training_cards")
            result["assessment_worksheets_count"] = get_table_count(conn, "assessment_worksheets")
            identity_status = check_identity_uniqueness(conn)
            result["identity_uniqueness_ok"] = identity_status["ok"]
            result["identity_duplicate_groups"] = identity_status["duplicate_groups"]
            result["identity_unique_indexes_ok"] = identity_unique_indexes_present(conn)
            runtime_facts = {
                "database_name": None,
                "legacy_schema_version": result["current_schema_version"],
                "explicit_migration_head": result["explicit_migration_head"],
                "server_read_only": False,
                "privileges": {"ALL PRIVILEGES"},
            }
            if _connection_provider(conn) == "mysql":
                runtime_facts.update(inspect_mysql_runtime(conn))
            result["profile_errors"] = runtime_profile_errors(Config, runtime_facts)
            result["profile_ok"] = not result["profile_errors"]
            result["fingerprint"] = public_database_fingerprint(Config, runtime_facts)
        existing_tables = {row["name"] for row in rows}
        missing_tables = [table for table in REQUIRED_HEALTH_TABLES if table not in existing_tables]
        content_training_cards = load_content_json("training_cards.json").get("cards", [])
        content_assessment_worksheets = load_content_json("assessment_worksheets.json").get("worksheets", [])
        result["content_training_cards_count"] = len(content_training_cards)
        result["content_assessment_worksheets_count"] = len(content_assessment_worksheets)
        result["training_cards_sync_ok"] = result["training_cards_count"] == result["content_training_cards_count"]
        result["worksheets_sync_ok"] = result["assessment_worksheets_count"] >= result["content_assessment_worksheets_count"]
        result["missing_tables"] = missing_tables
        result["required_tables_ok"] = not missing_tables
        if is_mysql_enabled():
            result["database_path_parent_exists"] = None
            result["database_file_exists"] = None
        result["ok"] = bool(
            not missing_tables
            and result["schema_version_ok"]
            and result["training_cards_sync_ok"]
            and result["worksheets_sync_ok"]
            and result["identity_uniqueness_ok"]
            and result["identity_unique_indexes_ok"]
            and result["profile_ok"]
        )
    except Exception as exc:
        message = str(exc).lower()
        result["error_code"] = (
            "database_connection_timeout"
            if "timed out" in message or "timeout" in message
            else "database_connection_failed"
        )
    return result


def inspect_mysql_runtime(conn) -> dict:
    database_row = conn.execute("SELECT DATABASE() AS database_name").fetchone()
    grant_rows = conn.execute("SHOW GRANTS").fetchall()
    variable_rows = conn.execute(
        "SHOW VARIABLES WHERE Variable_name IN ('read_only', 'super_read_only')"
    ).fetchall()
    read_only = False
    for row in variable_rows:
        if isinstance(row, dict):
            value = row.get("Value", row.get("value"))
        else:
            value = row[1] if isinstance(row, (tuple, list)) and len(row) > 1 else None
        if str(value or "").strip().lower() in {"1", "on", "true", "yes"}:
            read_only = True
    return {
        "database_name": database_row["database_name"] if database_row else None,
        "server_read_only": read_only,
        "privileges": granted_privileges(grant_rows),
    }


def list_database_tables(conn) -> list[dict]:
    if _connection_provider(conn) == "mysql":
        return conn.execute(
            """
            SELECT table_name AS name
            FROM information_schema.tables
            WHERE table_schema = DATABASE()
            """
        ).fetchall()
    return conn.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'"
    ).fetchall()


def list_database_columns(conn, table: str) -> list[dict]:
    """Return normalized column names for SQLite and MySQL."""
    if not _VALID_TABLE_NAME.match(table):
        raise ValueError(f"非法表名: {table}")
    if _connection_provider(conn) == "mysql":
        return conn.execute(
            """
            SELECT column_name AS name
            FROM information_schema.columns
            WHERE table_schema = DATABASE() AND table_name = ?
            ORDER BY ordinal_position
            """,
            (table,),
        ).fetchall()
    return conn.execute(f"PRAGMA table_info({table})").fetchall()


def check_identity_uniqueness(conn) -> dict:
    """Return duplicate group counts without exposing identity values."""

    duplicate_groups: dict[str, int] = {}
    for field in IDENTITY_FIELDS:
        row = conn.execute(
            f"""
            SELECT COUNT(*) AS count
            FROM (
                SELECT {field}
                FROM users
                WHERE {field} IS NOT NULL AND {field} <> ''
                GROUP BY {field}
                HAVING COUNT(*) > 1
            ) duplicate_values
            """
        ).fetchone()
        duplicate_groups[field] = int(row["count"] if row else 0)
    return {"ok": not any(duplicate_groups.values()), "duplicate_groups": duplicate_groups}


def identity_unique_indexes_present(conn) -> bool:
    expected = {
        "idx_users_username_unique",
        "idx_users_wechat_openid_unique",
        "idx_users_phone_hash_unique",
    }
    if _connection_provider(conn) == "mysql":
        rows = conn.execute(
            """
            SELECT DISTINCT index_name AS name
            FROM information_schema.statistics
            WHERE table_schema = DATABASE() AND table_name = 'users' AND non_unique = 0
            """
        ).fetchall()
    else:
        rows = conn.execute("PRAGMA index_list('users')").fetchall()
    return expected.issubset({str(row["name"]) for row in rows})


def create_index(conn, statement: str) -> None:
    if _connection_provider(conn) != "mysql":
        conn.execute(statement)
        return

    parsed = _parse_index_statement(statement)
    if parsed is None:
        conn.execute(statement)
        return
    index_name, target = parsed
    row = conn.execute(
        """
        SELECT index_name
        FROM information_schema.statistics
        WHERE table_schema = DATABASE() AND index_name = ?
        LIMIT 1
        """,
        (index_name,),
    ).fetchone()
    if row:
        return
    try:
        # index_name and target are parsed from trusted INDEX_SQL schema statements, not request input.
        unique = "UNIQUE " if re.match(r"\s*CREATE\s+UNIQUE\s+INDEX", statement, re.IGNORECASE) else ""
        conn.execute(f"CREATE {unique}INDEX {index_name} ON {target}")
    except Exception as exc:
        if "Duplicate key name" in str(exc) or "1061" in str(exc):
            return
        raise


def ensure_mysql_index_columns(conn) -> None:
    """Convert existing failed-deploy TEXT index columns to VARCHAR before indexing."""
    for statement in INDEX_SQL:
        parsed = _parse_index_statement(statement)
        if parsed is None:
            continue
        target = _parse_index_target(parsed[1])
        if target is None:
            continue
        table, columns = target
        for column in columns:
            if column not in MYSQL_VARCHAR_COLUMNS:
                continue
            row = conn.execute(
                """
            SELECT data_type AS data_type, is_nullable AS is_nullable
                 , character_maximum_length AS character_maximum_length
            FROM information_schema.columns
                WHERE table_schema = DATABASE() AND table_name = ? AND column_name = ?
                LIMIT 1
                """,
                (table, column),
            ).fetchone()
            if not row:
                continue
            data_type = str(row["data_type"]).lower()
            current_length = int(row.get("character_maximum_length") or 0)
            if data_type not in {"tinytext", "text", "mediumtext", "longtext", "varchar"}:
                continue
            if data_type == "varchar" and current_length <= MYSQL_INDEXABLE_VARCHAR_LENGTH:
                continue
            null_clause = "NOT NULL" if row["is_nullable"] == "NO" else "NULL"
            # table/column come from parsed internal INDEX_SQL targets and MYSQL_VARCHAR_COLUMNS allowlist.
            conn.execute(
                f"ALTER TABLE {table} MODIFY COLUMN {column} "
                f"VARCHAR({MYSQL_INDEXABLE_VARCHAR_LENGTH}) {null_clause}"
            )


def ensure_mysql_content_text_capacity(conn) -> None:
    """Widen legacy provenance fields before content synchronization."""
    row = conn.execute(
        """
        SELECT data_type AS data_type, is_nullable AS is_nullable
        FROM information_schema.columns
        WHERE table_schema = DATABASE()
          AND table_name = ?
          AND column_name = ?
        LIMIT 1
        """,
        ("assessment_worksheets", "source_file"),
    ).fetchone()
    if not row or str(row["data_type"]).lower() in {"text", "mediumtext", "longtext"}:
        return
    null_clause = "NOT NULL" if row["is_nullable"] == "NO" else "NULL"
    conn.execute(f"ALTER TABLE assessment_worksheets MODIFY COLUMN source_file TEXT {null_clause}")


def get_latest_schema_version(conn) -> str | None:
    try:
        row = conn.execute(
            """
            SELECT version FROM schema_migrations
            ORDER BY version DESC
            LIMIT 1
            """
        ).fetchone()
    except Exception:
        return None
    return row["version"] if row else None


def get_latest_explicit_migration_version(conn) -> str | None:
    try:
        row = conn.execute(
            """
            SELECT version FROM explicit_schema_migrations
            ORDER BY version DESC
            LIMIT 1
            """
        ).fetchone()
    except Exception:
        return None
    return row["version"] if row else None


def get_table_count(conn, table: str) -> int:
    if not _VALID_TABLE_NAME.match(table):
        raise ValueError(f"非法表名: {table}")
    try:
        # table is accepted only after the local identifier regex above.
        row = conn.execute(f"SELECT COUNT(*) AS count FROM {table}").fetchone()
    except Exception:
        return 0
    return int(row["count"]) if row else 0


def ensure_column(conn, table: str, column: str, definition: str) -> None:
    if not _VALID_TABLE_NAME.match(table):
        raise ValueError(f"非法表名: {table}")
    if not _VALID_COLUMN_NAME.match(column):
        raise ValueError(f"非法列名: {column}")
    if _connection_provider(conn) == "mysql":
        rows = conn.execute(
            """
            SELECT column_name AS name
            FROM information_schema.columns
            WHERE table_schema = DATABASE() AND table_name = ?
            """,
            (table,),
        ).fetchall()
        columns = {row["name"] for row in rows}
        if column not in columns:
            # table/column are accepted only after the local identifier regex above.
            conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {mysqlize_column_definition(column, definition)}")
        return

    # table is accepted only after the local identifier regex above.
    columns = {row["name"] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}
    if column not in columns:
        # table/column are accepted only after the local identifier regex above.
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


def record_schema_migration(conn) -> None:
    conn.execute(
        mysqlize_schema_statement(
            """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            applied_at TEXT NOT NULL
        )
        """
        )
        if _connection_provider(conn) == "mysql"
        else """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            applied_at TEXT NOT NULL
        )
        """
    )
    if _connection_provider(conn) == "mysql":
        conn.execute(
            """
            INSERT INTO schema_migrations (version, name, applied_at)
            VALUES (?, ?, ?)
            ON DUPLICATE KEY UPDATE version = version
            """,
            (CURRENT_SCHEMA_VERSION, CURRENT_SCHEMA_NAME, now_iso()),
        )
    else:
        conn.execute(
            """
            INSERT INTO schema_migrations (version, name, applied_at)
            VALUES (?, ?, ?)
            ON CONFLICT(version) DO NOTHING
            """,
            (CURRENT_SCHEMA_VERSION, CURRENT_SCHEMA_NAME, now_iso()),
        )


def ensure_schema_columns(conn) -> None:
    """Add columns needed by the ReadFeedback merge without replacing local data."""

    user_columns = {
        "username": "TEXT",
        "phone_or_email": "TEXT",
        "password_hash": "TEXT",
        "anonymous_id": "TEXT",
        "wechat_openid": "TEXT",
        "phone_hash": "TEXT",
        "avatar_url": "TEXT",
        "status": "TEXT DEFAULT 'active'",
        "last_login_at": "TEXT",
        "phone_verified_at": "TEXT",
        "phone_source": "TEXT",
        "merged_into_user_id": "TEXT",
        "merged_at": "TEXT",
    }
    for column, definition in user_columns.items():
        ensure_column(conn, "users", column, definition)

    student_profile_columns = {
        "model_version": "TEXT",
        "model_type": "TEXT",
        "cluster_id": "INTEGER",
        "pc1": "REAL",
        "pc2": "REAL",
        "nearest_distance": "REAL",
        "second_distance": "REAL",
        "report_json": "TEXT NOT NULL DEFAULT '{}'",
        "visuals_json": "TEXT NOT NULL DEFAULT '{}'",
        "legacy_source_id": "TEXT",
        "legacy_source_table": "TEXT",
    }
    for column, definition in student_profile_columns.items():
        ensure_column(conn, "student_profiles", column, definition)

    assessment_result_columns = {
        "profile_model_id": "TEXT",
        "profile_cluster_id": "INTEGER",
        "profile_pc1": "REAL",
        "profile_pc2": "REAL",
        "profile_confidence": "REAL",
        "scoring_version": "TEXT",
        "raw_scale_json": "TEXT NOT NULL DEFAULT '{}'",
        "raw_scores_json": "TEXT NOT NULL DEFAULT '{}'",
        "transformed_scores_json": "TEXT NOT NULL DEFAULT '{}'",
        "transformation_version": "TEXT",
    }
    for column, definition in assessment_result_columns.items():
        ensure_column(conn, "assessment_results", column, definition)
    _normalize_assessment_profile_cluster(conn)

    thermometer_columns = {
        "valence_level": "INTEGER",
        "arousal_level": "INTEGER",
        "control_level": "INTEGER",
        "emotion_label": "TEXT",
    }
    for column, definition in thermometer_columns.items():
        ensure_column(conn, "emotion_thermometer", column, definition)

    checkin_columns = {
        "helpfulness_rating": "TEXT",
        "skip_reason": "TEXT",
        "source_recommendation_id": "TEXT",
        "before_thermometer_id": "TEXT",
        "after_thermometer_id": "TEXT",
    }
    for column, definition in checkin_columns.items():
        ensure_column(conn, "checkins", column, definition)

    notification_delivery_columns = {
        "attempt_count": "INTEGER NOT NULL DEFAULT 0",
        "retry_category": "TEXT",
        "next_attempt_at": "TEXT",
        "max_attempts": "INTEGER NOT NULL DEFAULT 3",
        "dead_lettered_at": "TEXT",
        "last_attempt_at": "TEXT",
    }
    for column, definition in notification_delivery_columns.items():
        ensure_column(conn, "notification_deliveries", column, definition)

    weekly_report_columns = {
        "assessment_summary_json": "TEXT NOT NULL DEFAULT '{}'",
        "thermometer_summary_json": "TEXT NOT NULL DEFAULT '{}'",
        "training_effectiveness_summary_json": "TEXT NOT NULL DEFAULT '{}'",
    }
    for column, definition in weekly_report_columns.items():
        ensure_column(conn, "weekly_reports", column, definition)

    risk_review_columns = {
        "action_taken": "TEXT",
        "closed_reason": "TEXT",
    }
    for column, definition in risk_review_columns.items():
        ensure_column(conn, "risk_review_records", column, definition)

    family_link_columns = {
        "expires_at": "TEXT",
        "attempt_count": "INTEGER NOT NULL DEFAULT 0",
        "last_attempt_at": "TEXT",
    }
    for column, definition in family_link_columns.items():
        ensure_column(conn, "family_links", column, definition)

    consent_record_columns = {
        "actor_id": "TEXT",
        "subject_id": "TEXT",
        "purpose": "TEXT",
        "processor": "TEXT",
        "text_hash": "TEXT",
        "source": "TEXT NOT NULL DEFAULT 'provenance_unknown'",
        "reason": "TEXT",
        "evidence_ref": "TEXT",
        "supersedes_id": "TEXT",
        "event_type": "TEXT NOT NULL DEFAULT 'provenance_unknown'",
        "event_version": "INTEGER NOT NULL DEFAULT 1",
    }
    for column, definition in consent_record_columns.items():
        ensure_column(conn, "consent_records", column, definition)

    relationship_task_columns = {"idempotency_key": "TEXT"}
    for column, definition in relationship_task_columns.items():
        ensure_column(conn, "relationship_pilot_tasks", column, definition)
        ensure_column(conn, "relationship_longitudinal_entries", column, definition)

    ensure_column(conn, "relationship_pilot_enrollments", "assigned_researcher_id", "TEXT")
    ensure_column(conn, "research_scope_assignments", "expires_at", "TEXT")

    message_columns = {
        "sender_id": "TEXT",
        "sender_role": "TEXT",
        "idempotency_key": "TEXT",
        "delivery_id": "TEXT",
        "delivery_version": "INTEGER",
        "withdrawn_at": "TEXT",
    }
    for column, definition in message_columns.items():
        ensure_column(conn, "messages", column, definition)

    feedback_ledger_columns = {
        "supersedes_id": "TEXT",
        "participant_status": "TEXT NOT NULL DEFAULT 'visible'",
        "withdrawn_at": "TEXT",
    }
    for column, definition in feedback_ledger_columns.items():
        ensure_column(conn, "feedback_ledger", column, definition)

    supervision_columns = {
        "source_type": "TEXT",
        "source_id": "TEXT",
        "source_title": "TEXT",
        "client_submission_id": "TEXT",
    }
    for column, definition in supervision_columns.items():
        ensure_column(conn, "supervision_requests", column, definition)

    ensure_column(conn, "goals", "client_submission_id", "TEXT")
    ensure_column(conn, "emotion_diaries", "client_submission_id", "TEXT")
    ensure_column(conn, "checkins", "client_submission_id", "TEXT")
    ensure_column(conn, "assessment_results", "client_submission_id", "TEXT")
    ensure_column(conn, "parent_assessment_submissions", "client_submission_id", "TEXT")

    privacy_request_columns = {
        "handling_scope_json": "TEXT NOT NULL DEFAULT '[]'",
        "decision": "TEXT",
        "processing_started_at": "TEXT",
        "handled_at": "TEXT",
        "participant_notice": "TEXT",
        "policy_version": "TEXT",
        "execution_proof_hash": "TEXT",
        "version": "INTEGER NOT NULL DEFAULT 0",
    }
    for column, definition in privacy_request_columns.items():
        ensure_column(conn, "privacy_requests", column, definition)

    provider_event_columns = {
        "provider_request_id": "TEXT",
        "input_tokens": "INTEGER NOT NULL DEFAULT 0",
        "output_tokens": "INTEGER NOT NULL DEFAULT 0",
        "cost_currency": "TEXT NOT NULL DEFAULT 'unknown'",
    }
    for column, definition in provider_event_columns.items():
        ensure_column(conn, "ai_qa_provider_events", column, definition)
    ensure_column(conn, "privacy_deletion_tombstones", "scope_json", "TEXT NOT NULL DEFAULT '[]'")
    ensure_column(conn, "users", "auth_epoch", "INTEGER NOT NULL DEFAULT 0")
    ensure_column(conn, "users", "must_change_password", "INTEGER NOT NULL DEFAULT 0")
    ensure_column(conn, "users", "credential_receipt_id", "TEXT")
    ensure_column(conn, "users", "credential_expires_at", "TEXT")
    ensure_column(conn, "users", "password_changed_at", "TEXT")
    ensure_column(conn, "users", "failed_login_count", "INTEGER NOT NULL DEFAULT 0")
    ensure_column(conn, "users", "last_failed_login_at", "TEXT")
    ensure_column(conn, "users", "locked_until", "TEXT")
    ensure_column(conn, "users", "status_reason", "TEXT")
    ensure_column(conn, "users", "merged_into_user_id", "TEXT")
    ensure_column(conn, "users", "merged_at", "TEXT")
    ensure_column(conn, "data_claims", "idempotency_key", "TEXT")
    ensure_column(conn, "data_claims", "version", "INTEGER NOT NULL DEFAULT 0")
    ensure_column(conn, "identity_merge_record_links", "source_value", "TEXT")
    ensure_column(conn, "identity_merge_record_links", "target_value", "TEXT")
    offline_annotation_columns = {
        "emotion_labels_json": "TEXT NOT NULL DEFAULT '[]'",
        "intensity": "INTEGER NOT NULL DEFAULT 0",
        "polarity_status": "TEXT NOT NULL DEFAULT 'uncertain'",
        "evidence_excerpt": "TEXT",
        "rationale": "TEXT",
        "needs_human_understanding": "INTEGER NOT NULL DEFAULT 0",
        "human_review_reason": "TEXT",
        "manual_version": "TEXT NOT NULL DEFAULT 'legacy-t29-v1'",
        "group_hash": "TEXT",
        "data_split": "TEXT",
    }
    for column, definition in offline_annotation_columns.items():
        ensure_column(conn, "offline_benchmark_annotations", column, definition)
    therapeutic_state_columns = {
        "workflow_state": "TEXT NOT NULL DEFAULT 'draft_local'",
        "hypothesis_state": "TEXT NOT NULL DEFAULT 'observations_only'",
        "safety_state": "TEXT NOT NULL DEFAULT 'not_assessed'",
    }
    for column, definition in therapeutic_state_columns.items():
        ensure_column(conn, "therapeutic_assessment_cases", column, definition)
    therapeutic_question_columns = {
        "working_question": "TEXT",
        "question_candidates_json": "TEXT NOT NULL DEFAULT '[]'",
        "question_quality_json": "TEXT NOT NULL DEFAULT '{}'",
        "best_guess": "TEXT",
        "question_status": "TEXT NOT NULL DEFAULT 'submitted'",
        "candidate_decision": "TEXT NOT NULL DEFAULT 'unreviewed'",
        "question_version": "INTEGER NOT NULL DEFAULT 1",
    }
    for column, definition in therapeutic_question_columns.items():
        ensure_column(conn, "therapeutic_assessment_cases", column, definition)
    ensure_column(
        conn,
        "therapeutic_assessment_evidence_items",
        "method_limitations",
        "TEXT NOT NULL DEFAULT '仅适用于当前已授权资料与时间范围，不代表完整解释或诊断结论。'",
    )
    therapeutic_feedback_columns = {
        "feedback_layer": "TEXT NOT NULL DEFAULT 'layer_1'",
        "recipient_user_id": "TEXT",
        "letter_title": "TEXT NOT NULL DEFAULT '给你的阶段性反馈'",
        "supersedes_feedback_id": "TEXT",
        "withdrawn_at": "TEXT",
        "withdrawal_reason": "TEXT",
        "lifecycle_version": "INTEGER NOT NULL DEFAULT 1",
    }
    for column, definition in therapeutic_feedback_columns.items():
        ensure_column(conn, "therapeutic_assessment_feedback_versions", column, definition)
    therapeutic_action_columns = {
        "purpose_text": "TEXT",
        "planned_date": "TEXT",
        "reminder_mode": "TEXT NOT NULL DEFAULT 'none'",
        "reminder_privacy": "TEXT NOT NULL DEFAULT 'generic_preview'",
        "stop_conditions_json": "TEXT NOT NULL DEFAULT '[]'",
        "setback_plan": "TEXT",
        "training_card_id": "TEXT",
        "linked_checkin_id": "TEXT",
        "version": "INTEGER NOT NULL DEFAULT 1",
        "completed_at": "TEXT",
    }
    for column, definition in therapeutic_action_columns.items():
        ensure_column(conn, "therapeutic_assessment_actions", column, definition)
    ai_qa_session_columns = {
        "use_case_id": "TEXT NOT NULL DEFAULT 'legacy_unscoped'",
        "use_case_policy_version": "TEXT NOT NULL DEFAULT 'legacy'",
    }
    for column, definition in ai_qa_session_columns.items():
        ensure_column(conn, "ai_qa_sessions", column, definition)
    ensure_column(conn, "therapeutic_assessment_authorizations", "status_reason", "TEXT")
    conn.execute(
        """
        UPDATE therapeutic_assessment_cases
        SET working_question = assessment_question
        WHERE working_question IS NULL AND question_status != 'deleted'
        """
    )
    _normalize_therapeutic_assessment_states(conn)


def _normalize_therapeutic_assessment_states(conn) -> None:
    """Map legacy single-status cases into the additive three-track model."""

    conn.execute(
        """
        UPDATE therapeutic_assessment_cases
        SET workflow_state = CASE
            WHEN status = 'withdrawn' THEN 'withdrawn'
            WHEN status = 'support_required' THEN 'safety_path'
            WHEN status = 'feedback_sent' THEN 'participant_check'
            ELSE 'submitted'
        END
        WHERE workflow_state IS NULL OR workflow_state = '' OR workflow_state = 'draft_local'
        """
    )
    conn.execute(
        """
        UPDATE therapeutic_assessment_cases
        SET hypothesis_state = 'observations_only'
        WHERE hypothesis_state IS NULL OR hypothesis_state = ''
        """
    )
    conn.execute(
        """
        UPDATE therapeutic_assessment_cases
        SET safety_state = CASE
            WHEN risk_level IN ('medium', 'high') OR status = 'support_required'
                THEN 'needs_human_review'
            ELSE 'low_risk'
        END
        WHERE safety_state IS NULL OR safety_state = '' OR safety_state = 'not_assessed'
        """
    )


def _normalize_assessment_profile_cluster(conn) -> None:
    """Normalize legacy empty-string profile cluster values after the INTEGER switch."""
    try:
        conn.execute("UPDATE assessment_results SET profile_cluster_id = NULL WHERE profile_cluster_id = ''")
    except Exception:
        return
    if _connection_provider(conn) == "mysql":
        try:
            conn.execute("ALTER TABLE assessment_results MODIFY COLUMN profile_cluster_id INTEGER NULL")
        except Exception:
            pass


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def row_to_dict(row) -> dict | None:
    if row is None:
        return None
    return dict(row)


def rows_to_dicts(rows: list) -> list[dict]:
    return [dict(row) for row in rows]


def json_dumps(value) -> str:
    return json.dumps(value, ensure_ascii=False)


def json_loads(value: str | None, fallback=None):
    if not value:
        return fallback
    return json.loads(value)


def ensure_user(conn, user_id: str, nickname: str | None = None) -> None:
    timestamp = now_iso()
    if _connection_provider(conn) == "mysql":
        conn.execute(
            """
            INSERT INTO users (id, nickname, role, source, created_at, updated_at)
            VALUES (?, ?, 'parent', 'mvp', ?, ?)
            ON DUPLICATE KEY UPDATE
                nickname = COALESCE(VALUES(nickname), nickname),
                updated_at = VALUES(updated_at)
            """,
            (user_id, nickname, timestamp, timestamp),
        )
    else:
        conn.execute(
            """
            INSERT INTO users (id, nickname, role, source, created_at, updated_at)
            VALUES (?, ?, 'parent', 'mvp', ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                nickname = COALESCE(excluded.nickname, users.nickname),
                updated_at = excluded.updated_at
            """,
            (user_id, nickname, timestamp, timestamp),
        )


def write_audit_log(
    conn,
    action: str,
    actor_id: str | None = None,
    target_type: str | None = None,
    target_id: str | None = None,
    metadata: dict | None = None,
) -> str:
    audit_id = new_id("audit")
    created_at = now_iso()
    metadata_json = json.dumps(metadata or {}, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    # Updating the singleton row first obtains the database row/write lock, so
    # concurrent writers cannot allocate the same chain position.
    state = conn.execute(
        "SELECT last_sequence, last_hash FROM audit_chain_state WHERE singleton_id = 1"
    ).fetchone()
    if state is None:
        conn.execute(
            "INSERT INTO audit_chain_state (singleton_id, last_sequence, last_hash, updated_at) VALUES (1, 0, '', ?)",
            (created_at,),
        )
    else:
        conn.execute(
            "UPDATE audit_chain_state SET last_sequence = last_sequence WHERE singleton_id = 1"
        )
    state = conn.execute(
        "SELECT last_sequence, last_hash FROM audit_chain_state WHERE singleton_id = 1"
    ).fetchone()
    sequence_no = int(state["last_sequence"]) + 1
    previous_hash = str(state["last_hash"] or "")
    event_hash = audit_event_hash(
        audit_id=audit_id,
        sequence_no=sequence_no,
        previous_hash=previous_hash,
        actor_id=actor_id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        metadata_json=metadata_json,
        created_at=created_at,
    )
    conn.execute(
        """
        INSERT INTO audit_logs (
            id, actor_id, action, target_type, target_id, metadata_json,
            sequence_no, previous_hash, event_hash, hash_version, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'sha256-v1', ?)
        """,
        (
            audit_id,
            actor_id,
            action,
            target_type,
            target_id,
            metadata_json,
            sequence_no,
            previous_hash,
            event_hash,
            created_at,
        ),
    )
    conn.execute(
        "UPDATE audit_chain_state SET last_sequence = ?, last_hash = ?, updated_at = ? WHERE singleton_id = 1",
        (sequence_no, event_hash, created_at),
    )
    return audit_id


def audit_event_hash(
    *,
    audit_id: str,
    sequence_no: int,
    previous_hash: str,
    actor_id: str | None,
    action: str,
    target_type: str | None,
    target_id: str | None,
    metadata_json: str,
    created_at: str,
) -> str:
    try:
        metadata = json.loads(metadata_json or "{}")
    except (TypeError, ValueError):
        metadata = metadata_json
    payload = {
        "action": action,
        "actor_id": actor_id,
        "audit_id": audit_id,
        "created_at": created_at,
        "metadata": metadata,
        "previous_hash": previous_hash,
        "sequence_no": int(sequence_no),
        "target_id": target_id,
        "target_type": target_type,
    }
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def verify_audit_chain(conn) -> dict:
    """Verify the tamper-evident chain; this does not claim immutable storage."""
    rows = conn.execute(
        """SELECT id, actor_id, action, target_type, target_id, metadata_json,
                  sequence_no, previous_hash, event_hash, hash_version, created_at
           FROM audit_logs ORDER BY sequence_no ASC, created_at ASC, id ASC"""
    ).fetchall()
    previous_hash = ""
    expected_sequence = 1
    for row in rows:
        sequence_no = int(row["sequence_no"] or 0)
        expected_hash = audit_event_hash(
            audit_id=row["id"],
            sequence_no=sequence_no,
            previous_hash=str(row["previous_hash"] or ""),
            actor_id=row["actor_id"],
            action=row["action"],
            target_type=row["target_type"],
            target_id=row["target_id"],
            metadata_json=row["metadata_json"],
            created_at=row["created_at"],
        )
        valid = (
            sequence_no == expected_sequence
            and str(row["previous_hash"] or "") == previous_hash
            and row["hash_version"] == "sha256-v1"
            and row["event_hash"] == expected_hash
        )
        if not valid:
            return {
                "ok": False,
                "checked_count": expected_sequence,
                "first_invalid_audit_id": row["id"],
                "reason": "audit_chain_mismatch",
            }
        previous_hash = expected_hash
        expected_sequence += 1
    state = conn.execute(
        "SELECT last_sequence, last_hash FROM audit_chain_state WHERE singleton_id = 1"
    ).fetchone()
    state_ok = state is not None and int(state["last_sequence"]) == len(rows) and str(state["last_hash"] or "") == previous_hash
    return {
        "ok": state_ok,
        "checked_count": len(rows),
        "first_invalid_audit_id": None,
        "reason": "ok" if state_ok else "audit_chain_state_mismatch",
    }


_CONTENT_ARTIFACT_CACHE: dict[tuple[str, str], str] = {}


class ContentArtifactIntegrityError(RuntimeError):
    """Raised when an active immutable content artifact fails hash validation."""


def clear_content_artifact_cache() -> None:
    _CONTENT_ARTIFACT_CACHE.clear()


def load_content_text(filename: str) -> str:
    try:
        with get_connection() as conn:
            row = conn.execute(
                """
                SELECT a.payload_text, a.artifact_hash, a.status
                FROM content_active_artifacts p
                JOIN content_release_artifacts a ON a.id = p.artifact_id
                WHERE p.filename = ?
                """,
                (filename,),
            ).fetchone()
    except Exception as exc:
        message = str(exc).lower()
        if "no such table" not in message and "doesn't exist" not in message:
            raise
        row = None
    if row is not None:
        payload_text = str(row["payload_text"])
        artifact_hash = str(row["artifact_hash"])
        if row["status"] != "verified" or hashlib.sha256(
            payload_text.encode("utf-8")
        ).hexdigest() != artifact_hash:
            raise ContentArtifactIntegrityError(
                f"active content artifact integrity failed: {filename}"
            )
        cache_key = (filename, artifact_hash)
        cached = _CONTENT_ARTIFACT_CACHE.get(cache_key)
        if cached is None:
            _CONTENT_ARTIFACT_CACHE[cache_key] = payload_text
            cached = payload_text
        return cached
    return (Config.CONTENT_DIR / filename).read_text(encoding="utf-8")


def load_content_json(filename: str) -> dict:
    return json.loads(load_content_text(filename))


def sync_training_cards(conn) -> None:
    payload = load_content_json("training_cards.json")
    version = payload.get("version", "unknown")
    timestamp = now_iso()
    for card in payload.get("cards", []):
        params = (
            card["id"],
            card.get("type", "general"),
            card["title"],
            card.get("purpose"),
            json_dumps(card.get("steps", [])),
            json_dumps(card.get("tags", [])),
            card.get("example"),
            card.get("duration_minutes"),
            1 if card.get("enabled", True) else 0,
            version,
            timestamp,
            timestamp,
        )
        if _connection_provider(conn) == "mysql":
            conn.execute(
                """
                INSERT INTO training_cards (
                    id, type, title, purpose, steps_json, tags_json, example,
                    duration_minutes, enabled, version, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON DUPLICATE KEY UPDATE
                    type = VALUES(type),
                    title = VALUES(title),
                    purpose = VALUES(purpose),
                    steps_json = VALUES(steps_json),
                    tags_json = VALUES(tags_json),
                    example = VALUES(example),
                    duration_minutes = VALUES(duration_minutes),
                    enabled = VALUES(enabled),
                    version = VALUES(version),
                    updated_at = VALUES(updated_at)
                """,
                params,
            )
        else:
            conn.execute(
                """
                INSERT INTO training_cards (
                    id, type, title, purpose, steps_json, tags_json, example,
                    duration_minutes, enabled, version, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    type = excluded.type,
                    title = excluded.title,
                    purpose = excluded.purpose,
                    steps_json = excluded.steps_json,
                    tags_json = excluded.tags_json,
                    example = excluded.example,
                    duration_minutes = excluded.duration_minutes,
                    enabled = excluded.enabled,
                    version = excluded.version,
                    updated_at = excluded.updated_at
                """,
                params,
            )


def _sensitive_category(value) -> str:
    if isinstance(value, bool):
        return "screening_or_health" if value else "none"
    return str(value or "none")


def sync_assessment_worksheets(conn) -> None:
    if not (Config.CONTENT_DIR / "assessment_worksheets.json").exists():
        return
    payload = load_content_json("assessment_worksheets.json")
    timestamp = now_iso()
    columns = [
        "id",
        "display_title",
        "source_title",
        "source_file",
        "category",
        "audience_class",
        "reflex_node",
        "questions_json",
        "dimensions_json",
        "dimension_score_method",
        "scoring_notes_json",
        "search_keywords_json",
        "boundary_notice",
        "result_disclaimer",
        "instructions",
        "sensitive_category",
        "profile_model_id",
        "enabled_for_user",
        "review_status",
        "review_note",
        "source_version",
        "source_type",
        "audience",
        "audience_class_detail",
        "recommended_card_ids_json",
        "sections_json",
        "scoring",
        "pages",
        "_meta_json",
        "created_at",
        "updated_at",
    ]
    for worksheet in payload.get("worksheets", []):
        if not isinstance(worksheet, dict) or not worksheet.get("id"):
            continue
        existing = conn.execute("SELECT created_at FROM assessment_worksheets WHERE id = ?", (worksheet["id"],)).fetchone()
        row = {
            "id": worksheet["id"],
            "display_title": worksheet.get("display_title") or worksheet.get("source_title") or worksheet["id"],
            "source_title": worksheet.get("source_title"),
            "source_file": worksheet.get("source_file"),
            "category": worksheet.get("category"),
            "audience_class": worksheet.get("audience_class"),
            "reflex_node": worksheet.get("reflex_node"),
            "questions_json": json_dumps(worksheet.get("questions", [])),
            "dimensions_json": json_dumps(worksheet.get("dimensions", [])),
            "dimension_score_method": worksheet.get("dimension_score_method") or "sum",
            "scoring_notes_json": json_dumps(worksheet.get("scoring_notes", {})),
            "search_keywords_json": json_dumps(worksheet.get("search_keywords", [])),
            "boundary_notice": worksheet.get("boundary_notice"),
            "result_disclaimer": worksheet.get("result_disclaimer"),
            "instructions": worksheet.get("instructions"),
            "sensitive_category": _sensitive_category(worksheet.get("sensitive_category")),
            "profile_model_id": worksheet.get("profile_model_id"),
            "enabled_for_user": 1 if worksheet.get("enabled_for_user", True) else 0,
            "review_status": worksheet.get("review_status") or "approved",
            "review_note": worksheet.get("review_note"),
            "source_version": worksheet.get("source_version"),
            "source_type": worksheet.get("source_type"),
            "audience": worksheet.get("audience"),
            "audience_class_detail": worksheet.get("audience_class_detail"),
            "recommended_card_ids_json": json_dumps(worksheet.get("recommended_card_ids", [])),
            "sections_json": json_dumps(worksheet.get("sections", [])),
            "scoring": worksheet.get("scoring"),
            "pages": worksheet.get("pages"),
            "_meta_json": json_dumps(worksheet.get("_meta", {})),
            "created_at": existing["created_at"] if existing else timestamp,
            "updated_at": timestamp,
        }
        params = [row[column] for column in columns]
        placeholders = ", ".join("?" for _ in columns)
        column_sql = ", ".join(columns)
        update_columns = [column for column in columns if column not in {"id", "created_at"}]
        if _connection_provider(conn) == "mysql":
            updates = ", ".join(f"{column}=VALUES({column})" for column in update_columns)
            conn.execute(
                f"""
                INSERT INTO assessment_worksheets ({column_sql})
                VALUES ({placeholders})
                ON DUPLICATE KEY UPDATE {updates}
                """,
                params,
            )
        else:
            updates = ", ".join(f"{column}=excluded.{column}" for column in update_columns)
            conn.execute(
                f"""
                INSERT INTO assessment_worksheets ({column_sql})
                VALUES ({placeholders})
                ON CONFLICT(id) DO UPDATE SET {updates}
                """,
                params,
            )
