import importlib
import hashlib
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


def _configure_production_mysql(monkeypatch):
    host = "mysql.internal.example"
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("DB_PROVIDER", "mysql")
    monkeypatch.setenv("MYSQL_HOST", host)
    monkeypatch.setenv("MYSQL_PORT", "3306")
    monkeypatch.setenv("MYSQL_USER", "safehome_runtime")
    monkeypatch.setenv("MYSQL_PASSWORD", "fixture-password")
    monkeypatch.setenv("MYSQL_DATABASE", "safehome")
    monkeypatch.setenv("DATABASE_DATA_WATERMARK", "participant_production")
    monkeypatch.setenv("DB_PROFILE_APPROVAL_ID", "approval-fixture-001")
    monkeypatch.setenv("DB_APPROVED_HOST_SHA256", hashlib.sha256(host.encode()).hexdigest())
    monkeypatch.setenv("DB_APPROVED_DATABASE", "safehome")
    monkeypatch.setenv("DB_APPROVED_PORT", "3306")
    monkeypatch.setenv("DB_APPROVED_MIGRATION_HEAD", "2026_08_24_063+2026_08_25_074")
    monkeypatch.setenv("MYSQL_SSL_CA", str(Path(__file__)))
    monkeypatch.setenv("MYSQL_SSL_VERIFY_IDENTITY", "1")
    monkeypatch.setenv("MYSQL_TLS_MIN_VERSION", "TLSv1.2")
    monkeypatch.delenv("ALLOW_PRODUCTION_SQLITE", raising=False)


def test_production_rejects_default_admin_export_token(tmp_path, monkeypatch):
    _clear_backend_modules()
    _configure_production_mysql(monkeypatch)
    monkeypatch.delenv("ADMIN_EXPORT_TOKEN", raising=False)
    monkeypatch.setenv("SECRET_KEY", "production-test-secret-key-32-chars")
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "safehome-test.sqlite3"))
    monkeypatch.setenv("CONTENT_DIR", str(PROJECT_ROOT / "content"))

    with pytest.raises(RuntimeError, match="生产环境禁止使用默认 ADMIN_EXPORT_TOKEN"):
        importlib.import_module("app")


def test_production_requires_explicit_db_provider(tmp_path, monkeypatch):
    _clear_backend_modules()
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.delenv("DB_PROVIDER", raising=False)
    monkeypatch.setenv("ADMIN_EXPORT_TOKEN", "production-test-token")
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "safehome-test.sqlite3"))
    monkeypatch.setenv("CONTENT_DIR", str(PROJECT_ROOT / "content"))

    with pytest.raises(RuntimeError, match="生产环境必须显式配置 DB_PROVIDER"):
        importlib.import_module("app")


def test_production_sqlite_is_rejected_even_with_legacy_override(tmp_path, monkeypatch):
    _clear_backend_modules()
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("DB_PROVIDER", "sqlite")
    monkeypatch.setenv("ALLOW_PRODUCTION_SQLITE", "1")
    monkeypatch.setenv("ADMIN_EXPORT_TOKEN", "production-test-token")
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "safehome-test.sqlite3"))
    monkeypatch.setenv("CONTENT_DIR", str(PROJECT_ROOT / "content"))

    with pytest.raises(RuntimeError, match="只允许 MySQL"):
        importlib.import_module("app")


def test_explicit_admin_export_token_requires_legacy_opt_in(tmp_path, monkeypatch):
    _clear_backend_modules()
    monkeypatch.setenv("APP_ENV", "testing")
    monkeypatch.setenv("DB_PROVIDER", "sqlite")
    monkeypatch.setenv("ADMIN_EXPORT_TOKEN", "production-test-token")
    monkeypatch.setenv("LEGACY_ADMIN_TOKEN_ENABLED", "1")
    monkeypatch.setenv("SECRET_KEY", "production-test-secret-key-32-chars")
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "safehome-test.sqlite3"))
    monkeypatch.setenv("CONTENT_DIR", str(PROJECT_ROOT / "content"))

    module = importlib.import_module("app")
    client = module.app.test_client()

    unauthorized = client.get("/api/admin/export?type=diaries", headers={"X-Admin-Token": "safehome-local-admin-token"})
    authorized = client.get("/api/admin/export?type=diaries", headers={"X-Admin-Token": "production-test-token"})

    assert unauthorized.status_code == 401
    assert authorized.status_code == 200


def test_production_rejects_default_secret_key(tmp_path, monkeypatch):
    _clear_backend_modules()
    _configure_production_mysql(monkeypatch)
    monkeypatch.setenv("ADMIN_EXPORT_TOKEN", "production-test-token")
    monkeypatch.delenv("SECRET_KEY", raising=False)
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "safehome-test.sqlite3"))
    monkeypatch.setenv("CONTENT_DIR", str(PROJECT_ROOT / "content"))

    with pytest.raises(RuntimeError, match="生产环境禁止使用默认 SECRET_KEY"):
        importlib.import_module("app")


def test_production_rejects_short_secret_key(tmp_path, monkeypatch):
    _clear_backend_modules()
    _configure_production_mysql(monkeypatch)
    monkeypatch.setenv("ADMIN_EXPORT_TOKEN", "production-test-token")
    monkeypatch.setenv("SECRET_KEY", "short-secret")
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "safehome-test.sqlite3"))
    monkeypatch.setenv("CONTENT_DIR", str(PROJECT_ROOT / "content"))

    with pytest.raises(RuntimeError, match="SECRET_KEY 长度不能少于 32 个字符"):
        importlib.import_module("app")


def test_guarded_production_features_require_explicit_unlock(tmp_path, monkeypatch):
    _clear_backend_modules()
    monkeypatch.setenv("APP_ENV", "testing")
    monkeypatch.setenv("AI_QA_ENABLED", "1")
    monkeypatch.delenv("PRODUCTION_FEATURES_UNLOCKED", raising=False)
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "safehome-test.sqlite3"))
    monkeypatch.setenv("CONTENT_DIR", str(PROJECT_ROOT / "content"))

    with pytest.raises(RuntimeError, match="PRODUCTION_FEATURES_UNLOCKED"):
        importlib.import_module("app")


def test_guarded_production_features_can_be_opened_with_explicit_unlock(
    tmp_path, monkeypatch
):
    _clear_backend_modules()
    monkeypatch.setenv("APP_ENV", "testing")
    monkeypatch.setenv("PRODUCTION_FEATURES_UNLOCKED", "1")
    monkeypatch.setenv("AI_QA_ENABLED", "1")
    monkeypatch.setenv("AI_QA_SANDBOX_ENABLED", "1")
    monkeypatch.setenv("OFFLINE_EXTERNAL_INGEST_ENABLED", "1")
    monkeypatch.setenv("RESEARCH_METHODOLOGY_FORMAL_FREEZE_ALLOWED", "1")
    monkeypatch.setenv("RESEARCH_OUTCOME_ANALYSIS_ALLOWED", "1")
    monkeypatch.setenv("RELIABILITY_GRADUAL_RELEASE_ENABLED", "1")
    monkeypatch.setenv("RELIABILITY_PRODUCTION_SLO_FROZEN", "1")
    monkeypatch.setenv("OPERATIONS_PRODUCTION_RELEASE_ENABLED", "1")
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "safehome-test.sqlite3"))
    monkeypatch.setenv("CONTENT_DIR", str(PROJECT_ROOT / "content"))

    module = importlib.import_module("app")

    assert module.app.config["PRODUCTION_FEATURES_UNLOCKED"] is True
    assert module.app.config["AI_QA_ENABLED"] is True
    assert module.app.config["OPERATIONS_PRODUCTION_RELEASE_ENABLED"] is True


def test_production_ai_cannot_use_fake_provider(tmp_path, monkeypatch):
    _clear_backend_modules()
    _configure_production_mysql(monkeypatch)
    monkeypatch.setenv("ADMIN_EXPORT_TOKEN", "production-test-token")
    monkeypatch.setenv("SECRET_KEY", "production-test-secret-key-32-chars")
    monkeypatch.setenv("PRODUCTION_FEATURES_UNLOCKED", "1")
    monkeypatch.setenv("AI_QA_ENABLED", "1")
    monkeypatch.setenv("AI_QA_PROVIDER", "fake")
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "safehome-test.sqlite3"))
    monkeypatch.setenv("CONTENT_DIR", str(PROJECT_ROOT / "content"))

    with pytest.raises(RuntimeError, match="生产环境参与者AI问答禁止使用 fake"):
        importlib.import_module("app")
