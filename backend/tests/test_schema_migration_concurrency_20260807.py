from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

import services.schema_migration_service as migrations


class FakeMySQLConnection:
    provider = "mysql"


def test_pending_mysql_migration_is_serialized(monkeypatch):
    events = []
    conn = FakeMySQLConnection()
    migration = migrations.Migration(
        version="test_001",
        name="test",
        apply=lambda current: events.append("apply"),
        rollback_notes=(),
    )

    monkeypatch.setattr(migrations, "_pending_migrations", lambda current: [migration])
    monkeypatch.setattr(migrations, "_acquire_mysql_migration_lock", lambda current: events.append("lock"))
    monkeypatch.setattr(migrations, "_release_mysql_migration_lock", lambda current: events.append("release"))
    monkeypatch.setattr(migrations, "_applied", lambda current, version: False)
    monkeypatch.setattr(migrations, "_record", lambda current, item: events.append("record"))

    applied = migrations.apply_pending_schema_migrations(conn)

    assert applied == ["test_001"]
    assert events == ["lock", "apply", "record", "release"]


def test_mysql_migration_rechecks_after_waiting_for_lock(monkeypatch):
    events = []
    conn = FakeMySQLConnection()
    migration = migrations.Migration(
        version="test_002",
        name="test",
        apply=lambda current: events.append("apply"),
        rollback_notes=(),
    )

    monkeypatch.setattr(migrations, "_pending_migrations", lambda current: [migration])
    monkeypatch.setattr(migrations, "_acquire_mysql_migration_lock", lambda current: events.append("lock"))
    monkeypatch.setattr(migrations, "_release_mysql_migration_lock", lambda current: events.append("release"))
    monkeypatch.setattr(migrations, "_applied", lambda current, version: True)
    monkeypatch.setattr(migrations, "_record", lambda current, item: events.append("record"))

    applied = migrations.apply_pending_schema_migrations(conn)

    assert applied == []
    assert events == ["lock", "release"]


def test_no_mysql_lock_when_nothing_is_pending(monkeypatch):
    events = []
    conn = FakeMySQLConnection()

    monkeypatch.setattr(migrations, "_pending_migrations", lambda current: [])
    monkeypatch.setattr(migrations, "_acquire_mysql_migration_lock", lambda current: events.append("lock"))

    assert migrations.apply_pending_schema_migrations(conn) == []
    assert events == []
