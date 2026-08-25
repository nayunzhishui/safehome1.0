"""Run the F16 backup/restore drill only against disposable F11 synthetic data."""

from __future__ import annotations

import json
import os
import sqlite3
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))
sys.path.insert(0, str(BACKEND / "scripts"))

from migrate_rc0810_f11_database_profile import DEFAULT_FIXTURE, _seed, _snapshot  # noqa: E402
from services.database_profile_service import validate_synthetic_migration_fixture  # noqa: E402
from services.database_recovery_service import (  # noqa: E402
    create_sqlite_backup,
    load_recovery_policy,
    restore_sqlite_backup,
)


def main() -> int:
    fixture = json.loads(DEFAULT_FIXTURE.read_text(encoding="utf-8"))
    errors = validate_synthetic_migration_fixture(fixture)
    if fixture.get("data_class") != "synthetic_only":
        errors.append("fixture_data_class_invalid")
    if errors:
        print(json.dumps({"errors": errors}, ensure_ascii=False))
        return 1

    with tempfile.TemporaryDirectory(prefix="safehome-rc0810-f16-") as temp_dir:
        root = Path(temp_dir)
        source = root / "source.sqlite3"
        backup = root / "backup.sqlite3"
        target = root / "restored.sqlite3"
        os.environ.update(
            {
                "APP_ENV": "validation",
                "DB_PROVIDER": "sqlite",
                "DATABASE_PATH": str(source),
                "DATABASE_DATA_WATERMARK": "synthetic_validation_only",
                "CONTENT_DIR": str(ROOT / "content"),
            }
        )
        import database
        from services.schema_migration_service import apply_pending_schema_migrations

        conn = database.get_connection()
        try:
            for statement in database.SCHEMA_SQL:
                conn.execute(statement)
            database.ensure_schema_columns(conn)
            for statement in database.INDEX_SQL:
                database.create_index(conn, statement)
            database.record_schema_migration(conn)
            apply_pending_schema_migrations(conn)
            _seed(conn, fixture["records"])
            before = _snapshot(conn, fixture["records"])
        finally:
            conn.close()

        manifest = create_sqlite_backup(
            source, backup, encryption_state="synthetic_unencrypted"
        )
        (root / ".safehome-recovery-target.json").write_text(
            json.dumps(
                {
                    "environment": "isolated_validation",
                    "allowed_target": target.name,
                }
            ),
            encoding="utf-8",
        )
        restored = restore_sqlite_backup(backup, manifest, target)
        restored_conn = sqlite3.connect(target)
        restored_conn.row_factory = sqlite3.Row
        try:
            apply_pending_schema_migrations(restored_conn)
            restored_conn.commit()
            after = _snapshot(restored_conn, fixture["records"])
            head_row = restored_conn.execute(
                "SELECT version FROM explicit_schema_migrations ORDER BY version DESC LIMIT 1"
            ).fetchone()
            migration_head = str(head_row["version"]) if head_row else None
        finally:
            restored_conn.close()

        policy = load_recovery_policy()
        report = {
            "schema": "safehome.rc0810.database-recovery-drill.v1",
            "fixture_data_class": fixture["data_class"],
            "before": before,
            "after": after,
            "migration_head": migration_head,
            "backup_manifest": manifest,
            "restore": restored,
            "rpo_rto": {
                "rpo_target_minutes": policy["recovery"]["rpo_target_minutes"],
                "rto_target_minutes": policy["recovery"]["rto_target_minutes"],
                "synthetic_drill_completed": True,
                "production_actual": policy["recovery"]["production_actual"],
                "status": policy["recovery"]["status"],
            },
            "production_release_approved": False,
        }
        print(json.dumps(report, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
