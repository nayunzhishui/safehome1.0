import importlib
import os
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = PROJECT_ROOT / "backend"


def _fresh_app(tmp_path, allowed_origins: str | None = None):
    sys.path.insert(0, str(BACKEND_ROOT))
    for name in list(sys.modules):
        if name in {"app", "config", "database", "models"} or name.startswith("routes.") or name.startswith("services."):
            sys.modules.pop(name, None)
    os.environ["APP_ENV"] = "development"
    os.environ["DATABASE_PATH"] = str(tmp_path / "safehome-test.sqlite3")
    os.environ["CONTENT_DIR"] = str(PROJECT_ROOT / "content")
    if allowed_origins is None:
        os.environ.pop("ALLOWED_ORIGINS", None)
    else:
        os.environ["ALLOWED_ORIGINS"] = allowed_origins
    module = importlib.import_module("app")
    return module.app


def test_cors_allows_configured_local_origin(tmp_path):
    app = _fresh_app(tmp_path)
    client = app.test_client()

    response = client.get("/healthz", headers={"Origin": "http://127.0.0.1:5173"})

    assert response.status_code == 200
    assert response.headers["Access-Control-Allow-Origin"] == "http://127.0.0.1:5173"
    assert "Authorization" in response.headers["Access-Control-Allow-Headers"]


def test_cors_rejects_unconfigured_origin_header(tmp_path):
    app = _fresh_app(tmp_path, "https://admin.safehome.example.com")
    client = app.test_client()

    response = client.get("/healthz", headers={"Origin": "https://evil.example.com"})

    assert response.status_code == 200
    assert "Access-Control-Allow-Origin" not in response.headers


def test_healthz_without_origin_still_works(tmp_path):
    app = _fresh_app(tmp_path)
    client = app.test_client()

    response = client.get("/healthz")

    assert response.status_code == 200
    assert response.get_json()["ok"] is True
