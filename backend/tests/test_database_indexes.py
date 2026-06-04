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


def test_init_db_creates_common_indexes(tmp_path, monkeypatch):
    database = _fresh_database(tmp_path, monkeypatch)

    database.init_db()

    with database.get_connection() as conn:
        rows = conn.execute("SELECT name FROM sqlite_master WHERE type = 'index'").fetchall()

    index_names = {row["name"] for row in rows}
    assert {
        "idx_emotion_diaries_user_created",
        "idx_feedback_results_user_created",
        "idx_student_profiles_user_created",
        "idx_student_profiles_risk_created",
        "idx_risk_review_status_created",
        "idx_audit_logs_action_created",
        "idx_records_module_created",
    }.issubset(index_names)
