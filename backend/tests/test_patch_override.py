"""The mini program cannot send PATCH; POST + X-HTTP-Method-Override: PATCH must reach PATCH routes."""

import importlib
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = PROJECT_ROOT / "backend"


def test_post_with_patch_override_reaches_patch_routes_only(tmp_path, monkeypatch):
    sys.path.insert(0, str(BACKEND_ROOT))
    for name in list(sys.modules):
        if name in {"app", "config", "database", "models"} or name.startswith("routes.") or name.startswith("services."):
            sys.modules.pop(name, None)
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "patch-override.sqlite3"))
    monkeypatch.setenv("CONTENT_DIR", str(PROJECT_ROOT / "content"))
    client = importlib.import_module("app").app.test_client()
    path = "/api/research/deliveries/synthetic-workflow"
    override = {"X-HTTP-Method-Override": "PATCH"}

    assert client.post(path, json={}).status_code == 405
    # Reaches the PATCH handler, which then asks for a login like any direct PATCH.
    assert client.post(path, json={}, headers=override).status_code == 401
    assert client.patch(path, json={}).status_code == 401
    # Only POST is rewritten.
    assert client.delete(path, headers=override).status_code == 405
