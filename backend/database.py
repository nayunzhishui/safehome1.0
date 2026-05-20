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
        sync_training_cards(conn)
        conn.commit()


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
