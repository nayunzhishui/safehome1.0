import importlib.util
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "backend" / "scripts" / "migrate_rc0810_isolated_mysql.py"


def _load_script():
    spec = importlib.util.spec_from_file_location("migrate_rc0810_isolated_mysql", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_isolated_migration_rejects_original_production_database():
    module = _load_script()
    with pytest.raises(ValueError, match="original_production_database_forbidden"):
        module.validate_expected_database("safehome")


def test_isolated_migration_accepts_numbered_restore_database():
    module = _load_script()
    assert module.validate_expected_database("safehome-r2") == "safehome-r2"


def test_isolated_migration_rejects_runtime_database_mismatch_before_table_access():
    module = _load_script()

    class FakeConnection:
        def __init__(self):
            self.queries = []

        def execute(self, sql, _params=None):
            self.queries.append(sql.strip())
            if sql.strip().startswith("SELECT DATABASE"):
                return type("Cursor", (), {"fetchone": lambda _self: {"database_name": "safehome"}})()
            raise AssertionError("target mismatch must stop before table access")

    conn = FakeConnection()
    with pytest.raises(ValueError, match="connected_database_mismatch"):
        module.assert_connected_database(conn, "safehome-202609012247")
    assert len(conn.queries) == 1


def test_isolated_migration_apply_requires_target_specific_confirmation():
    module = _load_script()
    expected = "safehome-202609012247"
    phrase = module.required_confirmation(expected)
    assert phrase == "APPLY_RC0810_ISOLATED_SAFEHOME_202609012247"
    with pytest.raises(ValueError, match="apply_confirmation_mismatch"):
        module.validate_confirmation(expected, "APPLY_RC0810_ISOLATED")
    module.validate_confirmation(expected, phrase)


def test_existing_migration_ledger_read_failure_is_not_reported_as_all_pending():
    module = _load_script()

    class FakeConnection:
        def execute(self, _sql):
            raise RuntimeError("ledger read failed")

    with pytest.raises(RuntimeError, match="ledger read failed"):
        module._applied_explicit_versions(
            FakeConnection(), {"explicit_schema_migrations"}
        )


def test_apply_reports_sanitized_failed_stage_and_mysql_errno(monkeypatch):
    module = _load_script()

    class FakeMySqlError(RuntimeError):
        pass

    class FakeConnection:
        def execute(self, _sql, _params=None):
            raise FakeMySqlError(1142, "sensitive database message")

    monkeypatch.setattr(module.database, "SCHEMA_SQL", ("CREATE TABLE hidden",))

    with pytest.raises(module.MigrationStageError) as captured:
        module._apply_candidate_schema(FakeConnection())

    assert captured.value.stage == "base_schema:1"
    assert captured.value.database_errno == 1142
    assert "sensitive database message" not in str(captured.value)


def test_explicit_migration_failure_reports_version_without_database_message(monkeypatch):
    module = _load_script()

    class FakeExplicitError(RuntimeError):
        version = "2026_08_24_064"
        original = RuntimeError(1054, "sensitive column message")

    monkeypatch.setattr(module.database, "SCHEMA_SQL", ())
    monkeypatch.setattr(module.database, "ensure_mysql_index_columns", lambda _conn: None)
    monkeypatch.setattr(module.database, "ensure_mysql_content_text_capacity", lambda _conn: None)
    monkeypatch.setattr(module.database, "ensure_schema_columns", lambda _conn: None)
    monkeypatch.setattr(module.database, "INDEX_SQL", ())
    monkeypatch.setattr(module.database, "check_identity_uniqueness", lambda _conn: {"ok": False})
    monkeypatch.setattr(module.database, "sync_training_cards", lambda _conn: None)
    monkeypatch.setattr(module.database, "sync_assessment_worksheets", lambda _conn: None)
    monkeypatch.setattr(module.database, "record_schema_migration", lambda _conn: None)
    monkeypatch.setattr(module, "ExplicitMigrationApplyError", FakeExplicitError)

    def fail_explicit(_conn):
        raise FakeExplicitError()

    monkeypatch.setattr(module, "apply_pending_schema_migrations", fail_explicit)

    with pytest.raises(module.MigrationStageError) as captured:
        module._apply_candidate_schema(type("Conn", (), {"commit": lambda _self: None})())

    assert captured.value.stage == "explicit_migration:2026_08_24_064"
    assert captured.value.database_errno == 1054
    assert "sensitive column message" not in str(captured.value)


def test_run_returns_sanitized_stage_failure_to_service_wrapper(monkeypatch):
    module = _load_script()
    expected = "safehome-202609030054"

    class FakeConnection:
        def execute(self, sql, _params=None):
            if sql.strip().startswith("SELECT DATABASE"):
                return type(
                    "Cursor",
                    (),
                    {"fetchone": lambda _self: {"database_name": expected}},
                )()
            raise AssertionError(sql)

    class FakeContext:
        def __enter__(self):
            return FakeConnection()

        def __exit__(self, *_args):
            return False

    monkeypatch.setattr(module.Config, "DB_PROVIDER", "mysql")
    monkeypatch.setattr(module.Config, "MYSQL_DATABASE", expected)
    monkeypatch.setattr(module.database, "get_connection", lambda: FakeContext())
    monkeypatch.setattr(module.database, "list_database_tables", lambda _conn: [])
    monkeypatch.setattr(
        module,
        "_apply_candidate_schema",
        lambda _conn: (_ for _ in ()).throw(
            module.MigrationStageError("schema_columns", RuntimeError(1060, "secret"))
        ),
    )

    result, exit_code = module.run(
        "apply", expected, module.required_confirmation(expected)
    )

    assert exit_code == 1
    assert result == {
        "ok": False,
        "action": "apply",
        "error_code": "migration_operation_failed",
        "failure_stage": "schema_columns",
        "database_errno": 1060,
    }
