import importlib
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = PROJECT_ROOT / "backend"


def _fresh_app(tmp_path, monkeypatch):
    sys.path.insert(0, str(BACKEND_ROOT))
    for name in list(sys.modules):
        if name in {"app", "config", "database", "models"} or name.startswith("routes.") or name.startswith("services."):
            sys.modules.pop(name, None)
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "safehome-test.sqlite3"))
    monkeypatch.setenv("CONTENT_DIR", str(PROJECT_ROOT / "content"))
    monkeypatch.setenv("ADMIN_EXPORT_TOKEN", "test-secret-token")
    module = importlib.import_module("app")
    return module.app


def test_healthz_returns_lightweight_status_without_secret(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()

    response = client.get("/healthz")

    assert response.status_code == 200
    data = response.get_json()
    assert data["ok"] is True
    assert data["service"] == "safehome-backend"
    assert data["env"] == "development"
    assert data["version"] == "safehome-2026-06-04"
    assert "test-secret-token" not in response.get_data(as_text=True)


def test_deep_healthz_checks_database_and_content(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()

    response = client.get("/healthz/deep")

    assert response.status_code == 200
    data = response.get_json()
    assert data["ok"] is True
    assert data["database"]["ok"] is True
    assert data["database"]["expected_schema_version"] == "2026_06_04_001"
    assert data["database"]["current_schema_version"] == "2026_06_04_001"
    assert data["database"]["schema_version_ok"] is True
    assert data["database"]["required_tables_ok"] is True
    assert data["database"]["missing_tables"] == []
    assert data["database"]["database_path_parent_exists"] is True
    assert data["database"]["database_file_exists"] is True
    assert data["database"]["training_cards_count"] > 0
    assert data["database"]["content_training_cards_count"] == data["database"]["training_cards_count"]
    assert data["database"]["training_cards_sync_ok"] is True
    assert data["content"]["ok"] is True
    assert data["content"]["required_files_ok"] is True
    assert data["content"]["missing_files"] == []
    assert "test-secret-token" not in response.get_data(as_text=True)
