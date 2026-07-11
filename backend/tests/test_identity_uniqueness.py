import importlib
import sys
from pathlib import Path

import pytest


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


def test_new_database_enforces_non_empty_identity_uniqueness(tmp_path, monkeypatch):
    database = _fresh_database(tmp_path, monkeypatch)
    database.init_db()

    with database.get_connection() as conn:
        assert database.identity_unique_indexes_present(conn) is True
        conn.execute("INSERT INTO users (id, username, created_at, updated_at) VALUES ('u1', 'same-user', '2026-07-11', '2026-07-11')")
        with pytest.raises(Exception):
            conn.execute("INSERT INTO users (id, username, created_at, updated_at) VALUES ('u2', 'same-user', '2026-07-11', '2026-07-11')")


def test_duplicate_identity_preflight_blocks_index_without_exposing_values(tmp_path, monkeypatch):
    database = _fresh_database(tmp_path, monkeypatch)
    database.init_db()

    with database.get_connection() as conn:
        conn.execute("DROP INDEX idx_users_username_unique")
        conn.execute("INSERT INTO users (id, username, created_at, updated_at) VALUES ('u1', 'secret-name', '2026-07-11', '2026-07-11')")
        conn.execute("INSERT INTO users (id, username, created_at, updated_at) VALUES ('u2', 'secret-name', '2026-07-11', '2026-07-11')")
        conn.commit()

    database.init_db()
    health = database.check_database_health()

    assert health["ok"] is False
    assert health["identity_uniqueness_ok"] is False
    assert health["identity_unique_indexes_ok"] is False
    assert health["identity_duplicate_groups"]["username"] == 1
    assert "secret-name" not in str(health)


def test_records_composite_index_is_created(tmp_path, monkeypatch):
    database = _fresh_database(tmp_path, monkeypatch)
    database.init_db()

    with database.get_connection() as conn:
        rows = conn.execute("PRAGMA index_list('records')").fetchall()

    assert "idx_records_user_module_source_created" in {row["name"] for row in rows}
