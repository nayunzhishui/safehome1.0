"""Database helpers for the SafeHome MVP backend."""

import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path

from config import Config
from models import SCHEMA_SQL


def get_connection(database_path: str | Path | None = None) -> sqlite3.Connection:
    path = Path(database_path or Config.DATABASE_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Create MVP tables and sync content training cards into SQLite."""
    with get_connection() as conn:
        for statement in SCHEMA_SQL:
            conn.execute(statement)
        ensure_schema_columns(conn)
        sync_training_cards(conn)
        conn.commit()


def ensure_column(conn: sqlite3.Connection, table: str, column: str, definition: str) -> None:
    columns = {row["name"] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}
    if column not in columns:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


def ensure_schema_columns(conn: sqlite3.Connection) -> None:
    """Add columns needed by the ReadFeedback merge without replacing local data."""

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


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def row_to_dict(row: sqlite3.Row | None) -> dict | None:
    if row is None:
        return None
    return dict(row)


def rows_to_dicts(rows: list[sqlite3.Row]) -> list[dict]:
    return [dict(row) for row in rows]


def json_dumps(value) -> str:
    return json.dumps(value, ensure_ascii=False)


def json_loads(value: str | None, fallback=None):
    if not value:
        return fallback
    return json.loads(value)


def ensure_user(conn: sqlite3.Connection, user_id: str, nickname: str | None = None) -> None:
    timestamp = now_iso()
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
    conn: sqlite3.Connection,
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


def sync_training_cards(conn: sqlite3.Connection) -> None:
    payload = load_content_json("training_cards.json")
    version = payload.get("version", "unknown")
    timestamp = now_iso()
    for card in payload.get("cards", []):
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
            (
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
            ),
        )
