from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "backend" / "scripts" / "migrate_rc0810_production_mysql.py"


def load_module():
    spec = importlib.util.spec_from_file_location("migrate_rc0810_production_mysql", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_production_target_and_confirmation_are_exact(monkeypatch):
    module = load_module()
    monkeypatch.setattr(module.Config, "DB_PROVIDER", "mysql")
    monkeypatch.setattr(module.Config, "MYSQL_DATABASE", "safehome")

    with pytest.raises(ValueError, match="production_database_name_mismatch"):
        module.run("plan", "safehome-r3")
    with pytest.raises(ValueError, match="production_apply_confirmation_mismatch"):
        module.run("apply", "safehome", "APPROVE")


def test_apply_reuses_guarded_flow_and_preserves_critical_counts(monkeypatch):
    module = load_module()
    monkeypatch.setattr(module.Config, "DB_PROVIDER", "mysql")
    monkeypatch.setattr(module.Config, "MYSQL_DATABASE", "safehome")

    class Connection:
        def execute(self, _statement):
            return self

        def fetchone(self):
            return {"database_name": "safehome"}

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

    snapshots = iter(
        [
            {"critical_row_counts": {"users": 15}},
            {"critical_row_counts": {"users": 15}},
        ]
    )
    monkeypatch.setattr(module.database, "get_connection", lambda: Connection())
    monkeypatch.setattr(module, "_snapshot", lambda *_args: next(snapshots))
    monkeypatch.setattr(module, "_apply_candidate_schema", lambda _conn: ["2026_08_26_078"])
    monkeypatch.setattr(module, "_verification_ok", lambda _snapshot: True)

    result, exit_code = module.run(
        "apply", "safehome", module.PRODUCTION_CONFIRMATION
    )

    assert exit_code == 0
    assert result["ok"] is True
    assert result["critical_row_counts_unchanged"] is True


def test_apply_fails_verification_when_critical_counts_change(monkeypatch):
    module = load_module()
    monkeypatch.setattr(module.Config, "DB_PROVIDER", "mysql")
    monkeypatch.setattr(module.Config, "MYSQL_DATABASE", "safehome")

    class Connection:
        def execute(self, _statement):
            return self

        def fetchone(self):
            return {"database_name": "safehome"}

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

    snapshots = iter(
        [
            {"critical_row_counts": {"users": 15}},
            {"critical_row_counts": {"users": 14}},
        ]
    )
    monkeypatch.setattr(module.database, "get_connection", lambda: Connection())
    monkeypatch.setattr(module, "_snapshot", lambda *_args: next(snapshots))
    monkeypatch.setattr(module, "_apply_candidate_schema", lambda _conn: [])
    monkeypatch.setattr(module, "_verification_ok", lambda _snapshot: True)

    result, exit_code = module.run(
        "apply", "safehome", module.PRODUCTION_CONFIRMATION
    )

    assert exit_code == 1
    assert result["ok"] is False
    assert result["critical_row_counts_unchanged"] is False
