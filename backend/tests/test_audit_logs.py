import importlib
import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = PROJECT_ROOT / "backend"


def _fresh_database(tmp_path, monkeypatch):
    sys.path.insert(0, str(BACKEND_ROOT))
    for name in list(sys.modules):
        if name in {"app", "config", "database", "models"} or name.startswith("routes.") or name.startswith("services."):
            sys.modules.pop(name, None)
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "safehome-test.sqlite3"))
    monkeypatch.setenv("CONTENT_DIR", str(PROJECT_ROOT / "content"))
    database = importlib.import_module("database")
    database.init_db()
    return database


def test_audit_logs_table_is_created_and_write_helper_inserts_metadata(tmp_path, monkeypatch):
    database = _fresh_database(tmp_path, monkeypatch)

    with database.get_connection() as conn:
        columns = {row["name"] for row in conn.execute("PRAGMA table_info(audit_logs)").fetchall()}
        audit_id = database.write_audit_log(
            conn,
            action="test_action",
            actor_id="test-admin",
            target_type="test_target",
            target_id="target-001",
            metadata={"row_count": 1, "contains_high_risk": False},
        )
        conn.commit()
        row = conn.execute("SELECT * FROM audit_logs WHERE id = ?", (audit_id,)).fetchone()

    assert {"id", "actor_id", "action", "target_type", "target_id", "metadata_json", "created_at"}.issubset(columns)
    assert row["actor_id"] == "test-admin"
    assert row["action"] == "test_action"
    assert json.loads(row["metadata_json"])["row_count"] == 1
