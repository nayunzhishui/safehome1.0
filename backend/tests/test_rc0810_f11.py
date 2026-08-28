import copy
import hashlib
import importlib
import json
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
CONTRACT = ROOT / "config" / "rc0810" / "database_profiles.json"
FIXTURE = BACKEND / "tests" / "fixtures" / "rc0810_f11_synthetic_migration.json"


def _clear_modules():
    sys.path.insert(0, str(BACKEND))
    for name in list(sys.modules):
        if name in {"config", "database", "app"} or name.startswith("services."):
            sys.modules.pop(name, None)


def _production_env(monkeypatch, *, provider="mysql", approved=True):
    host = "mysql.internal.example"
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("DB_PROVIDER", provider)
    monkeypatch.setenv("MYSQL_HOST", host)
    monkeypatch.setenv("MYSQL_PORT", "3306")
    monkeypatch.setenv("MYSQL_USER", "safehome_runtime")
    monkeypatch.setenv("MYSQL_PASSWORD", "fixture-password")
    monkeypatch.setenv("MYSQL_DATABASE", "safehome")
    monkeypatch.setenv("MYSQL_SSL_CA", str(Path(__file__)))
    monkeypatch.setenv("SECRET_KEY", "production-test-secret-key-at-least-32")
    monkeypatch.setenv("ADMIN_EXPORT_TOKEN", "production-test-admin-token")
    monkeypatch.setenv("OPERATIONS_HEALTH_TOKEN", "production-operations-health-token")
    monkeypatch.setenv("DATABASE_DATA_WATERMARK", "participant_production")
    if approved:
        monkeypatch.setenv("DB_PROFILE_APPROVAL_ID", "approval-fixture-001")
        monkeypatch.setenv("DB_APPROVED_HOST_SHA256", hashlib.sha256(host.encode()).hexdigest())
        monkeypatch.setenv("DB_APPROVED_DATABASE", "safehome")
        monkeypatch.setenv("DB_APPROVED_PORT", "3306")
        monkeypatch.setenv("DB_APPROVED_MIGRATION_HEAD", "2026_08_24_063+2026_08_26_078")


def test_f11_contract_freezes_mysql_only_production_and_explicit_heads():
    payload = json.loads(CONTRACT.read_text(encoding="utf-8"))
    assert payload["profiles"]["validation"]["providers"] == ["sqlite"]
    production = payload["profiles"]["production"]
    assert production["providers"] == ["mysql"]
    assert production["automatic_schema_changes"] is False
    assert production["approved_migration_head"] == "2026_08_24_063+2026_08_26_078"
    assert payload["production_gate_eligible"] is False


def test_f11_production_rejects_sqlite_even_with_legacy_override(monkeypatch):
    _clear_modules()
    _production_env(monkeypatch, provider="sqlite")
    monkeypatch.setenv("ALLOW_PRODUCTION_SQLITE", "1")
    module = importlib.import_module("config")
    with pytest.raises(RuntimeError, match="production.*MySQL|生产.*MySQL"):
        module.Config.validate()


def test_f11_production_requires_approved_database_binding(monkeypatch):
    _clear_modules()
    _production_env(monkeypatch, approved=False)
    module = importlib.import_module("config")
    with pytest.raises(RuntimeError, match="批准摘要"):
        module.Config.validate()


def test_f11_production_accepts_exact_approved_binding(monkeypatch):
    _clear_modules()
    _production_env(monkeypatch)
    module = importlib.import_module("config")
    module.Config.validate()


def test_f11_validation_sqlite_requires_explicit_path_and_watermark(monkeypatch):
    _clear_modules()
    monkeypatch.setenv("APP_ENV", "validation")
    monkeypatch.setenv("DB_PROVIDER", "sqlite")
    monkeypatch.setenv("DATABASE_DATA_WATERMARK", "synthetic_validation_only")
    monkeypatch.delenv("DATABASE_PATH", raising=False)
    module = importlib.import_module("config")
    with pytest.raises(RuntimeError, match="DATABASE_PATH"):
        module.Config.validate()


def test_f11_profile_heads_match_database_constants():
    _clear_modules()
    database = importlib.import_module("database")
    migrations = importlib.import_module("services.schema_migration_service")
    payload = json.loads(CONTRACT.read_text(encoding="utf-8"))["profiles"]["production"]
    assert payload["legacy_schema_version"] == database.CURRENT_SCHEMA_VERSION
    assert payload["explicit_migration_head"] == migrations.MIGRATIONS[-1].version


def test_f11_runtime_rejects_wrong_database_old_schema_and_read_only_account(monkeypatch):
    _clear_modules()
    _production_env(monkeypatch)
    config = importlib.import_module("config").Config
    service = importlib.import_module("services.database_profile_service")
    facts = {
        "database_name": "wrong_database",
        "legacy_schema_version": "old",
        "explicit_migration_head": "old",
        "server_read_only": True,
        "privileges": {"SELECT"},
    }
    errors = service.runtime_profile_errors(config, facts)
    assert {
        "connected_database_not_approved",
        "legacy_schema_version_mismatch",
        "explicit_migration_head_mismatch",
        "database_server_read_only",
        "database_runtime_privileges_insufficient",
    } <= set(errors)


def test_f11_runtime_accepts_current_writable_mysql_profile(monkeypatch):
    _clear_modules()
    _production_env(monkeypatch)
    config = importlib.import_module("config").Config
    service = importlib.import_module("services.database_profile_service")
    facts = {
        "database_name": "safehome",
        "legacy_schema_version": "2026_08_24_063",
        "explicit_migration_head": "2026_08_26_078",
        "server_read_only": False,
        "privileges": {"SELECT", "INSERT", "UPDATE", "DELETE"},
    }
    assert service.runtime_profile_errors(config, facts) == []


def test_f11_fingerprint_is_irreversible_and_contains_no_database_name_or_user(monkeypatch):
    _clear_modules()
    _production_env(monkeypatch)
    config = importlib.import_module("config").Config
    service = importlib.import_module("services.database_profile_service")
    fingerprint = service.public_database_fingerprint(
        config,
        {"legacy_schema_version": "2026_08_24_063", "explicit_migration_head": "2026_08_26_078"},
    )
    text = json.dumps(fingerprint)
    assert len(fingerprint["host_sha256"]) == 64
    assert "mysql.internal.example" not in text
    assert "safehome_runtime" not in text
    assert "fixture-password" not in text


def test_f11_grant_parser_distinguishes_runtime_crud_from_read_only():
    _clear_modules()
    service = importlib.import_module("services.database_profile_service")
    assert service.granted_privileges([("GRANT SELECT ON `safehome`.* TO `reader`",)]) == {"SELECT"}
    assert service.granted_privileges([
        ("GRANT SELECT, INSERT, UPDATE, DELETE ON `safehome`.* TO `runtime`",)
    ]) == {"SELECT", "INSERT", "UPDATE", "DELETE"}
    database = importlib.import_module("database")

    class FakeConnection:
        def execute(self, sql):
            if sql.startswith("SELECT DATABASE"):
                return type("Cursor", (), {"fetchone": lambda _self: {"database_name": "safehome"}})()
            if sql == "SHOW GRANTS":
                return type("Cursor", (), {"fetchall": lambda _self: [
                    {"grant": "GRANT SELECT, INSERT, UPDATE, DELETE ON `safehome`.* TO `runtime`"}
                ]})()
            return type("Cursor", (), {"fetchall": lambda _self: [
                {"Variable_name": "read_only", "Value": "OFF"}
            ]})()

    facts = database.inspect_mysql_runtime(FakeConnection())
    assert facts == {
        "database_name": "safehome",
        "server_read_only": False,
        "privileges": {"SELECT", "INSERT", "UPDATE", "DELETE"},
    }


def test_f11_synthetic_migration_fixture_preserves_ids_counts_status_versions_and_owners():
    _clear_modules()
    service = importlib.import_module("services.database_profile_service")
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    assert service.validate_synthetic_migration_fixture(payload) == []
    changed = copy.deepcopy(payload)
    changed["records"].pop()
    assert "fixture_categories_incomplete" in service.validate_synthetic_migration_fixture(changed)


def test_f11_synthetic_verifier_executes_real_pending_migrations():
    completed = __import__("subprocess").run(
        [sys.executable, str(BACKEND / "scripts" / "migrate_rc0810_f11_database_profile.py")],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    result = json.loads(completed.stdout)
    assert result["records_compared"] == 9
    assert result["before_after_equal"] is True
    assert result["synthetic_database_mutated"] is True
    assert result["production_database_mutated"] is False
    assert result["database_deleted_after_verification"] is True
    assert result["applied_migrations"] == [
        "2026_08_07_062",
        "2026_08_07_063",
        "2026_08_24_064",
        "2026_08_24_065",
        "2026_08_24_066",
        "2026_08_24_067",
        "2026_08_24_068",
        "2026_08_25_069",
        "2026_08_25_070",
        "2026_08_25_071",
        "2026_08_25_072",
        "2026_08_25_073",
        "2026_08_25_074",
        "2026_08_25_075",
        "2026_08_25_076",
        "2026_08_26_077",
        "2026_08_26_078",
    ]


def test_f11_connection_timeout_is_sanitized(monkeypatch, tmp_path):
    _clear_modules()
    monkeypatch.setenv("APP_ENV", "testing")
    monkeypatch.setenv("DB_PROVIDER", "sqlite")
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "timeout.sqlite3"))
    database = importlib.import_module("database")

    def fail_connection(*_args, **_kwargs):
        raise TimeoutError("mysql.internal.example timed out with fixture-password")

    monkeypatch.setattr(database, "get_connection", fail_connection)
    result = database.check_database_health()
    assert result["ok"] is False
    assert result["error_code"] == "database_connection_timeout"
    assert "error" not in result
    assert "mysql.internal.example" not in json.dumps(result)


def test_f11_readyz_returns_503_without_connection_details(monkeypatch, tmp_path):
    _clear_modules()
    monkeypatch.setenv("APP_ENV", "testing")
    monkeypatch.setenv("DB_PROVIDER", "sqlite")
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "ready.sqlite3"))
    monkeypatch.setenv("CONTENT_DIR", str(ROOT / "content"))
    app_module = importlib.import_module("app")
    monkeypatch.setattr(
        app_module,
        "check_database_health",
        lambda: {"ok": False, "error_code": "database_connection_failed", "profile_errors": []},
    )
    response = app_module.app.test_client().get("/readyz")
    assert response.status_code == 503
    assert "fixture-password" not in response.get_data(as_text=True)
    assert "mysql.internal.example" not in response.get_data(as_text=True)


def test_f11_production_app_startup_never_runs_schema_changes(monkeypatch, tmp_path):
    _clear_modules()
    monkeypatch.setenv("APP_ENV", "testing")
    monkeypatch.setenv("DB_PROVIDER", "sqlite")
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "bootstrap.sqlite3"))
    monkeypatch.setenv("CONTENT_DIR", str(ROOT / "content"))
    app_module = importlib.import_module("app")
    config_module = importlib.import_module("config")
    ca_path = tmp_path / "mysql-ca.pem"
    ca_path.write_text("synthetic-ca", encoding="utf-8")

    class ProductionConfig(config_module.Config):
        APP_ENV = "production"
        DB_PROVIDER = "mysql"
        MYSQL_HOST = "mysql.internal.example"
        MYSQL_PORT = 3306
        MYSQL_USER = "safehome_runtime"
        MYSQL_PASSWORD = "fixture-password"
        MYSQL_DATABASE = "safehome"
        MYSQL_SSL_CA = str(ca_path)
        MYSQL_SSL_VERIFY_IDENTITY = True
        MYSQL_TLS_MIN_VERSION = "TLSv1.2"
        SAFETY_SCHEDULER_ENABLED = False
        DATABASE_DATA_WATERMARK = "participant_production"
        DB_PROFILE_APPROVAL_ID = "approval-fixture-001"
        DB_APPROVED_HOST_SHA256 = hashlib.sha256(MYSQL_HOST.encode()).hexdigest()
        DB_APPROVED_DATABASE = "safehome"
        DB_APPROVED_PORT = 3306
        DB_APPROVED_MIGRATION_HEAD = "2026_08_24_063+2026_08_26_078"
        SECRET_KEY = "production-test-secret-key-at-least-32"
        ADMIN_EXPORT_TOKEN = "production-test-admin-token"
        OPERATIONS_HEALTH_TOKEN = "production-operations-health-token"

    monkeypatch.setattr(config_module, "DB_PROVIDER_ENV_VALUE", "mysql")
    monkeypatch.setattr(app_module, "check_database_health", lambda: {"ok": True})
    monkeypatch.setattr(app_module, "init_db", lambda: (_ for _ in ()).throw(AssertionError("init_db called")))
    monkeypatch.setattr(
        app_module,
        "apply_pending_schema_migrations",
        lambda _conn: (_ for _ in ()).throw(AssertionError("migration called")),
    )
    created = app_module.create_app(config_class=ProductionConfig, init_database=True)
    assert created.config["APP_ENV"] == "production"


def test_f11_rollback_document_forbids_schema_rollback():
    text = (ROOT / "deploy" / "rc0810_f11_database_rollback.md").read_text(encoding="utf-8")
    assert "不得回退已执行的数据迁移" in text
    assert "前一应用版本" in text
