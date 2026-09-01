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
