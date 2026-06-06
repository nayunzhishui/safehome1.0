"""Database helpers for the SafeHome MVP backend."""

import json
import re
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path

from config import Config
from models import INDEX_SQL, SCHEMA_SQL


REQUIRED_HEALTH_TABLES = [
    "users",
    "schema_migrations",
    "emotion_diaries",
    "feedback_results",
    "student_profiles",
    "risk_review_records",
    "audit_logs",
    "consent_records",
    "records",
]
CURRENT_SCHEMA_VERSION = "2026_06_04_001"
CURRENT_SCHEMA_NAME = "baseline_safehome_schema"
MYSQL_VARCHAR_COLUMNS = {
    "id",
    "version",
    "name",
    "user_id",
    "nickname",
    "role",
    "username",
    "phone_or_email",
    "password_hash",
    "status",
    "last_login_at",
    "source",
    "created_at",
    "updated_at",
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
    "relation_label",
    "expires_at",
    "last_attempt_at",
    "confirmed_at",
    "closed_reason",
    "reviewed_at",
    "week_start",
    "week_end",
    "replied_at",
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

        self._connection = pymysql.connect(
            host=Config.MYSQL_HOST,
            port=Config.MYSQL_PORT,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD,
            database=Config.MYSQL_DATABASE,
            charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=False,
        )

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        if exc_type is None:
            self.commit()
        else:
            self._connection.rollback()
        self.close()
        return False

    def execute(self, sql: str, params=None):
        cursor = self._connection.cursor()
        cursor.execute(_mysqlize_query(sql), tuple(params or ()))
        return cursor

    def commit(self) -> None:
        self._connection.commit()

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
        column_type = "VARCHAR(255)"
    elif column.endswith("_json"):
        column_type = "LONGTEXT"
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
    return line.split(" ", 1)[1]


def _parse_index_statement(statement: str) -> tuple[str, str] | None:
    match = re.match(r"\s*CREATE\s+INDEX\s+IF\s+NOT\s+EXISTS\s+(\w+)\s+ON\s+(.+)", statement, re.IGNORECASE)
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
        ensure_schema_columns(conn)
        for statement in INDEX_SQL:
            create_index(conn, statement)
        sync_training_cards(conn)
        record_schema_migration(conn)
        conn.commit()


def check_database_health() -> dict:
    """Run a read-only database health check for cloud and deploy diagnostics."""
    path = Path(Config.DATABASE_PATH)
    result = {
        "ok": False,
        "provider": Config.DB_PROVIDER,
        "path": str(path),
        "mysql": {
            "host": Config.MYSQL_HOST if is_mysql_enabled() else "",
            "port": Config.MYSQL_PORT if is_mysql_enabled() else None,
            "database": Config.MYSQL_DATABASE if is_mysql_enabled() else "",
        },
        "database_path_parent_exists": path.parent.exists(),
        "database_file_exists": path.exists(),
        "expected_schema_version": CURRENT_SCHEMA_VERSION,
        "current_schema_version": None,
        "schema_version_ok": False,
        "required_tables_ok": False,
        "missing_tables": [],
        "training_cards_count": 0,
        "content_training_cards_count": 0,
        "training_cards_sync_ok": False,
    }
    try:
        with get_connection() as conn:
            rows = list_database_tables(conn)
            result["current_schema_version"] = get_latest_schema_version(conn)
            result["schema_version_ok"] = result["current_schema_version"] == CURRENT_SCHEMA_VERSION
            result["training_cards_count"] = get_table_count(conn, "training_cards")
        existing_tables = {row["name"] for row in rows}
        missing_tables = [table for table in REQUIRED_HEALTH_TABLES if table not in existing_tables]
        content_training_cards = load_content_json("training_cards.json").get("cards", [])
        result["content_training_cards_count"] = len(content_training_cards)
        result["training_cards_sync_ok"] = result["training_cards_count"] == result["content_training_cards_count"]
        result["missing_tables"] = missing_tables
        result["required_tables_ok"] = not missing_tables
        if is_mysql_enabled():
            result["database_path_parent_exists"] = None
            result["database_file_exists"] = None
        result["ok"] = bool(not missing_tables and result["schema_version_ok"] and result["training_cards_sync_ok"])
    except (sqlite3.Error, OSError, json.JSONDecodeError, RuntimeError, Exception) as exc:
        result["error"] = str(exc)
    return result


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
        conn.execute(f"CREATE INDEX {index_name} ON {target}")
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
                FROM information_schema.columns
                WHERE table_schema = DATABASE() AND table_name = ? AND column_name = ?
                LIMIT 1
                """,
                (table, column),
            ).fetchone()
            if not row:
                continue
            if str(row["data_type"]).lower() not in {"tinytext", "text", "mediumtext", "longtext"}:
                continue
            null_clause = "NOT NULL" if row["is_nullable"] == "NO" else "NULL"
            conn.execute(f"ALTER TABLE {table} MODIFY COLUMN {column} VARCHAR(255) {null_clause}")


def get_latest_schema_version(conn) -> str | None:
    try:
        row = conn.execute(
            """
            SELECT version FROM schema_migrations
            ORDER BY applied_at DESC
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
            conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {mysqlize_column_definition(column, definition)}")
        return

    columns = {row["name"] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}
    if column not in columns:
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
        "status": "TEXT DEFAULT 'active'",
        "last_login_at": "TEXT",
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
    conn.execute(
        """
        INSERT INTO audit_logs (id, actor_id, action, target_type, target_id, metadata_json, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            audit_id,
            actor_id,
            action,
            target_type,
            target_id,
            json_dumps(metadata or {}),
            now_iso(),
        ),
    )
    return audit_id


def load_content_json(filename: str) -> dict:
    path = Config.CONTENT_DIR / filename
    return json.loads(path.read_text(encoding="utf-8"))


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
