"""Task37-R02 isolated migration, backup, restore and tombstone evidence."""

from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import sqlite3
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from config import Config
import database
from scripts.verify_privacy_restore import verify as verify_privacy_restore


REGISTRY = ROOT / "content" / "task37_release_execution_registry.json"
PRODUCTION_CONFIRMATION = "APPROVE_TASK37_R02_PRODUCTION_MIGRATION"
SYNTHETIC_SECRET = b"task37-r02-synthetic-tombstone"


def _stage() -> dict:
    payload = json.loads(REGISTRY.read_text(encoding="utf-8"))
    return next(item for item in payload["stages"] if item["id"] == "R02")


def _manifest(path: Path) -> dict:
    with sqlite3.connect(path) as conn:
        tables = sorted(row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'"))
        schema_lines = [
            row[0] or ""
            for row in conn.execute("SELECT sql FROM sqlite_master WHERE sql IS NOT NULL ORDER BY type, name")
        ]
        counts = {
            table: int(conn.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0])
            for table in tables
            if table != "sqlite_sequence"
        }
        integrity = str(conn.execute("PRAGMA integrity_check").fetchone()[0])
        row = conn.execute("SELECT version FROM schema_migrations ORDER BY version DESC LIMIT 1").fetchone()
    return {
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "schema_hash": hashlib.sha256("\n".join(schema_lines).encode("utf-8")).hexdigest(),
        "table_row_counts": counts,
        "integrity_check": integrity,
        "schema_version": row[0] if row else None,
    }


def exercise(work_dir: Path | None = None) -> dict:
    base = work_dir.resolve() if work_dir else None
    if base:
        base.mkdir(parents=True, exist_ok=True)
    temporary = tempfile.TemporaryDirectory(prefix="safehome-r02-", dir=base, ignore_cleanup_errors=True)
    root = Path(temporary.name)
    previous = Config.DATABASE_PATH
    try:
        source = root / "source.sqlite3"
        backup = root / "backup.sqlite3"
        restored = root / "restored.sqlite3"
        Config.DATABASE_PATH = source
        database.init_db()
        subject_hash = hmac.new(SYNTHETIC_SECRET, b"synthetic-deleted-subject", hashlib.sha256).hexdigest()
        with database.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO privacy_deletion_tombstones (
                    id, request_id, subject_hash, replacement_user_id,
                    policy_version, scope_json, proof_hash, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    "r02-tombstone",
                    "r02-request",
                    subject_hash,
                    "deleted-r02",
                    "task37-r02",
                    json.dumps(["account_identity", "participant_records", "therapeutic_assessment"]),
                    hashlib.sha256(b"synthetic-proof").hexdigest(),
                    database.now_iso(),
                ),
            )
            conn.commit()
        before = _manifest(source)
        with sqlite3.connect(source) as source_conn, sqlite3.connect(backup) as target_conn:
            source_conn.backup(target_conn)
        backup_manifest = _manifest(backup)
        with sqlite3.connect(backup) as source_conn, sqlite3.connect(restored) as target_conn:
            source_conn.backup(target_conn)
        restore_manifest = _manifest(restored)
        tombstone = verify_privacy_restore(restored, SYNTHETIC_SECRET)
        equivalent = (
            backup_manifest["schema_hash"] == restore_manifest["schema_hash"]
            and backup_manifest["table_row_counts"] == restore_manifest["table_row_counts"]
            and backup_manifest["schema_version"] == restore_manifest["schema_version"]
        )
        result = {
            "schema": "safehome.task37.r02-migration-evidence.v1",
            "target_schema_version": database.CURRENT_SCHEMA_VERSION,
            "target_schema_name": database.CURRENT_SCHEMA_NAME,
            "source_manifest": before,
            "backup_manifest": backup_manifest,
            "restore_manifest": restore_manifest,
            "backup_restore_equivalent": equivalent,
            "privacy_tombstone": tombstone,
            "raw_identifiers_included": False,
            "production_migration_executed": False,
            "production_restore_executed": False,
            "production_release_approved": False,
        }
        result["ok"] = (
            before["schema_version"] == database.CURRENT_SCHEMA_VERSION
            and before["integrity_check"] == "ok"
            and backup_manifest["integrity_check"] == "ok"
            and restore_manifest["integrity_check"] == "ok"
            and equivalent
            and tombstone["ok"]
        )
        return result
    finally:
        Config.DATABASE_PATH = previous
        temporary.cleanup()


def plan() -> dict:
    stage = _stage()
    return {
        "action": "plan",
        "ok": True,
        "ordered_steps": stage["ordered_steps"],
        "required_evidence_fields": stage["required_evidence_fields"],
        "command_generation_only": True,
        "production_migration_executed": False,
    }


def rollback_plan() -> dict:
    return {
        "action": "rollback-plan",
        "ok": True,
        "policy": _stage()["rollback_policy"],
        "steps": [
            "disable new writes",
            "capture current checksum, schema and row counts",
            "restore the verified backup in isolation",
            "verify tombstones, health, ready and core journeys",
            "switch runtime only after independent verification",
        ],
        "rollback_executed": False,
        "production_mutation_executed": False,
    }


def production_command(action: str) -> dict:
    return {
        "action": action,
        "ok": True,
        "command_generated_only": True,
        "required_confirmation": PRODUCTION_CONFIRMATION,
        "production_mutation_executed": False,
        "operator_note": "需使用批准的维护窗口、已验证备份和独立核验者；本脚本不连接生产。",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["plan", "exercise", "verify", "rollback-plan", "production-command"])
    parser.add_argument("--work-dir", type=Path)
    parser.add_argument("--operation", choices=["apply", "restore", "rollback"], default="apply")
    args = parser.parse_args()
    if args.action == "plan":
        result = plan()
    elif args.action in {"exercise", "verify"}:
        result = exercise(args.work_dir)
        result["action"] = args.action
    elif args.action == "rollback-plan":
        result = rollback_plan()
    else:
        result = production_command(args.operation)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("ok", True) else 1


if __name__ == "__main__":
    raise SystemExit(main())
