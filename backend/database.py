"""Database helpers for the MVP skeleton.

The actual schema initialization will be implemented in a later backend task.
"""

import sqlite3
from pathlib import Path

from config import Config


def get_connection(database_path: str | Path | None = None) -> sqlite3.Connection:
    path = Path(database_path or Config.DATABASE_PATH)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Placeholder for future SQLite table creation."""
    with get_connection() as conn:
        conn.execute("SELECT 1")
