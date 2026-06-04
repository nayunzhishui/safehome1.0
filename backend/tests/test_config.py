import importlib
import os
import sys
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = PROJECT_ROOT / "backend"


def _clear_backend_modules():
    sys.path.insert(0, str(BACKEND_ROOT))
    for name in list(sys.modules):
        if name in {"app", "config", "database", "models"} or name.startswith("routes.") or name.startswith("services."):
            sys.modules.pop(name, None)


def test_production_rejects_default_admin_export_token(tmp_path, monkeypatch):
    _clear_backend_modules()
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.delenv("ADMIN_EXPORT_TOKEN", raising=False)
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "safehome-test.sqlite3"))
    monkeypatch.setenv("CONTENT_DIR", str(PROJECT_ROOT / "content"))

    with pytest.raises(RuntimeError, match="生产环境禁止使用默认 ADMIN_EXPORT_TOKEN"):
        importlib.import_module("app")


def test_production_accepts_explicit_admin_export_token(tmp_path, monkeypatch):
    _clear_backend_modules()
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("ADMIN_EXPORT_TOKEN", "production-test-token")
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "safehome-test.sqlite3"))
    monkeypatch.setenv("CONTENT_DIR", str(PROJECT_ROOT / "content"))

    module = importlib.import_module("app")
    client = module.app.test_client()

    unauthorized = client.get("/api/admin/export?type=diaries", headers={"X-Admin-Token": "safehome-local-admin-token"})
    authorized = client.get("/api/admin/export?type=diaries", headers={"X-Admin-Token": "production-test-token"})

    assert unauthorized.status_code == 401
    assert authorized.status_code == 200
