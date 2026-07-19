import importlib
import sqlite3
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = PROJECT_ROOT / "backend"


def _reload_database(monkeypatch, database_path: Path):
    sys.path.insert(0, str(BACKEND_ROOT))
    for name in ["config", "models", "database"]:
        sys.modules.pop(name, None)
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("DATABASE_PATH", str(database_path))
    monkeypatch.setenv("CONTENT_DIR", str(PROJECT_ROOT / "content"))
    return importlib.import_module("database")


def test_task25_schema_upgrades_legacy_sqlite_and_is_repeatable(tmp_path, monkeypatch):
    path = tmp_path / "legacy-task25.sqlite3"
    with sqlite3.connect(path) as conn:
        conn.execute(
            """
            CREATE TABLE notification_deliveries (
                id TEXT PRIMARY KEY, user_id TEXT NOT NULL, notification_type TEXT NOT NULL,
                template_id TEXT NOT NULL, schedule_key TEXT NOT NULL, idempotency_key TEXT NOT NULL,
                status TEXT NOT NULL, attempt_count INTEGER NOT NULL DEFAULT 0,
                scheduled_for TEXT NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL
            )
            """
        )
    database = _reload_database(monkeypatch, path)

    database.init_db()
    database.init_db()

    with database.get_connection() as conn:
        delivery_columns = {row["name"] for row in conn.execute("PRAGMA table_info(notification_deliveries)").fetchall()}
        tables = {row["name"] for row in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'").fetchall()}
        migration = conn.execute(
            "SELECT name FROM schema_migrations WHERE version = ?",
            (database.CURRENT_SCHEMA_VERSION,),
        ).fetchone()
    assert {"retry_category", "next_attempt_at", "max_attempts", "dead_lettered_at", "last_attempt_at"}.issubset(delivery_columns)
    assert {"research_work_items", "research_work_item_notes", "research_work_item_actions"}.issubset(tables)
    assert migration["name"] == "research_operations_work_items"


def test_task25_mysql_schema_contract_contains_portable_work_item_columns(monkeypatch, tmp_path):
    database = _reload_database(monkeypatch, tmp_path / "mysql-contract.sqlite3")
    models = importlib.import_module("models")
    statement = next(sql for sql in models.SCHEMA_SQL if "CREATE TABLE IF NOT EXISTS research_work_items" in sql)
    converted = database.mysqlize_schema_statement(statement)
    assert "queue_type VARCHAR(255)" in converted
    assert "source_id VARCHAR(255)" in converted
    assert "version INTEGER NOT NULL DEFAULT 0" in converted
    assert "UNIQUE(queue_type, source_type, source_id)" in converted


def test_task25_interrupted_transaction_rolls_back_action_and_backup_restores(tmp_path, monkeypatch):
    database = _reload_database(monkeypatch, tmp_path / "rollback-task25.sqlite3")
    database.init_db()
    timestamp = database.now_iso()
    with database.get_connection() as conn:
        database.ensure_user(conn, "task25-rollback-user", "rollback")
        conn.execute(
            """
            INSERT INTO research_work_items (
                id, queue_type, source_type, source_id, user_id, priority, status,
                version, created_at, updated_at
            ) VALUES ('rollback-item', 'supervision', 'supervision_requests', 'rollback-source',
                      'task25-rollback-user', 'routine', 'open', 0, ?, ?)
            """,
            (timestamp, timestamp),
        )
        conn.commit()

    service = importlib.import_module("services.research_work_item_service")
    try:
        with database.get_connection() as conn:
            service.perform_work_item_action(
                conn,
                "rollback-item",
                {"id": "admin-token", "role": "admin"},
                action="claim",
                expected_version=0,
                idempotency_key="rollback-action",
            )
            raise RuntimeError("simulated interruption")
    except RuntimeError:
        pass

    with database.get_connection() as conn:
        item = conn.execute("SELECT status, version FROM research_work_items WHERE id = 'rollback-item'").fetchone()
        action_count = conn.execute("SELECT COUNT(*) AS count FROM research_work_item_actions").fetchone()["count"]
    assert item["status"] == "open" and item["version"] == 0
    assert action_count == 0

    backup_path = tmp_path / "task25-backup.sqlite3"
    with sqlite3.connect(database.Config.DATABASE_PATH) as source, sqlite3.connect(backup_path) as target:
        source.backup(target)
    with sqlite3.connect(backup_path) as restored:
        restored.row_factory = sqlite3.Row
        restored_item = restored.execute("SELECT status, version FROM research_work_items WHERE id = 'rollback-item'").fetchone()
    assert restored_item["status"] == "open" and restored_item["version"] == 0
