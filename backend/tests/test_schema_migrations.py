import importlib
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = PROJECT_ROOT / "backend"


def _fresh_database(tmp_path, monkeypatch):
    sys.path.insert(0, str(BACKEND_ROOT))
    for name in list(sys.modules):
        if name in {"config", "database", "models"}:
            sys.modules.pop(name, None)
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "safehome-test.sqlite3"))
    monkeypatch.setenv("CONTENT_DIR", str(PROJECT_ROOT / "content"))
    return importlib.import_module("database")


def test_init_db_records_current_schema_migration_once(tmp_path, monkeypatch):
    database = _fresh_database(tmp_path, monkeypatch)

    database.init_db()
    database.init_db()

    with database.get_connection() as conn:
        table = conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'schema_migrations'"
        ).fetchone()
        rows = conn.execute("SELECT * FROM schema_migrations").fetchall()
        enrollment_columns = {
            row["name"] for row in conn.execute("PRAGMA table_info(relationship_pilot_enrollments)").fetchall()
        }

    assert table is not None
    assert len(rows) == 1
    assert rows[0]["version"] == database.CURRENT_SCHEMA_VERSION
    assert rows[0]["name"] == database.CURRENT_SCHEMA_NAME
    assert "assigned_researcher_id" in enrollment_columns


def test_latest_schema_version_uses_version_order_not_mixed_timestamp_formats(tmp_path, monkeypatch):
    database = _fresh_database(tmp_path, monkeypatch)
    database.init_db()

    with database.get_connection() as conn:
        conn.execute(
            "INSERT INTO schema_migrations (version, name, applied_at) VALUES (?, ?, ?)",
            ("2026_07_11_004", "older_schema", "9999-12-31T23:59:59+08:00"),
        )
        latest = database.get_latest_schema_version(conn)

    assert latest == database.CURRENT_SCHEMA_VERSION
