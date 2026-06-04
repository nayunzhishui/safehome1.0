import importlib
import json
import os
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = PROJECT_ROOT / "backend"


def _fresh_app(tmp_path):
    sys.path.insert(0, str(BACKEND_ROOT))
    for name in list(sys.modules):
        if name in {"app", "config", "database", "models"} or name.startswith("routes.") or name.startswith("services."):
            sys.modules.pop(name, None)
    os.environ["DATABASE_PATH"] = str(tmp_path / "safehome-test.sqlite3")
    os.environ["CONTENT_DIR"] = str(PROJECT_ROOT / "content")
    os.environ.pop("APP_ENV", None)
    module = importlib.import_module("app")
    return module.app


def test_admin_export_writes_audit_log_after_success(tmp_path):
    app = _fresh_app(tmp_path)
    client = app.test_client()

    response = client.get("/api/admin/export?type=diaries", headers={"X-Admin-Token": "safehome-local-admin-token"})

    assert response.status_code == 200

    import database

    with database.get_connection() as conn:
        audit = conn.execute(
            """
            SELECT action, actor_id, target_type, target_id, metadata_json
            FROM audit_logs
            WHERE action = 'export_diaries'
            """
        ).fetchone()

    assert audit is not None
    assert audit["actor_id"] == "admin-token"
    assert audit["target_type"] == "export"
    assert audit["target_id"] == "diaries"
    metadata = json.loads(audit["metadata_json"])
    assert metadata["type"] == "diaries"
    assert metadata["row_count"] == 0


def test_unauthorized_admin_export_does_not_write_audit_log(tmp_path):
    app = _fresh_app(tmp_path)
    client = app.test_client()

    response = client.get("/api/admin/export?type=diaries", headers={"X-Admin-Token": "wrong-token"})

    assert response.status_code == 401

    import database

    with database.get_connection() as conn:
        count = conn.execute("SELECT COUNT(*) AS count FROM audit_logs").fetchone()["count"]

    assert count == 0
