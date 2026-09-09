"""Task36 F18 isolated migration, backup/restore and non-destructive rollback lab."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
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
import models
from services.schema_migration_service import apply_pending_schema_migrations


MATRIX_PATH = ROOT / "config" / "task36_migration_matrix.json"
PRODUCTION_CONFIRMATION = "APPLY_TASK36_F18_PRODUCTION_MIGRATION"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _table_names(path: Path) -> list[str]:
    with sqlite3.connect(path) as conn:
        return sorted(row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'"))


def _manifest(path: Path) -> dict:
    with sqlite3.connect(path) as conn:
        tables = sorted(row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'"))
        row_counts = {
            table: int(conn.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0])
            for table in tables
            if table != "sqlite_sequence"
        }
        schema_lines = [
            row[0] or ""
            for row in conn.execute(
                "SELECT sql FROM sqlite_master WHERE sql IS NOT NULL ORDER BY type, name"
            )
        ]
        latest = None
        if "schema_migrations" in tables:
            row = conn.execute("SELECT version FROM schema_migrations ORDER BY version DESC LIMIT 1").fetchone()
            latest = row[0] if row else None
    return {
        "sha256": sha256_file(path),
        "schema_hash": hashlib.sha256("\n".join(schema_lines).encode("utf-8")).hexdigest(),
        "table_row_counts": row_counts,
        "schema_version": latest,
        "created_at": database.now_iso(),
    }


def _with_database(path: Path, callback):
    previous = Config.DATABASE_PATH
    Config.DATABASE_PATH = path
    try:
        return callback()
    finally:
        Config.DATABASE_PATH = previous


def _apply(path: Path) -> dict:
    def run():
        database.init_db()
        with database.get_connection() as conn:
            apply_pending_schema_migrations(conn)
            conn.commit()
        return database.check_database_health()

    return _with_database(path, run)


def _seed_legacy(path: Path) -> None:
    with sqlite3.connect(path) as conn:
        conn.execute("CREATE TABLE schema_migrations (version TEXT PRIMARY KEY, name TEXT NOT NULL, applied_at TEXT NOT NULL)")
        conn.execute("INSERT INTO schema_migrations VALUES ('2026_07_20_023', 'legacy_task23', '2026-07-20T00:00:00Z')")
        conn.execute("CREATE TABLE legacy_marker (id TEXT PRIMARY KEY, value TEXT NOT NULL)")
        conn.execute("INSERT INTO legacy_marker VALUES ('keep-me', 'preserved')")
        conn.commit()


def _seed_partial(path: Path) -> None:
    statements = [
        statement
        for statement in models.SCHEMA_SQL
        if any(
            f"CREATE TABLE IF NOT EXISTS {table}" in statement
            for table in ("therapeutic_assessment_cases", "therapeutic_assessment_feedback_versions")
        )
    ]
    with sqlite3.connect(path) as conn:
        for statement in statements:
            conn.execute(statement)
        conn.commit()


def mysql57_contract() -> dict:
    converted = [database.mysqlize_schema_statement(statement) for statement in models.SCHEMA_SQL]
    invalid_text_defaults = [
        line.strip()
        for statement in converted
        for line in statement.splitlines()
        if re.search(r"\b(?:TEXT|LONGTEXT)\b.*\bDEFAULT\b", line, re.IGNORECASE)
    ]
    destructive = [
        statement
        for statement in [*converted, *models.INDEX_SQL]
        if re.search(r"\b(?:DROP|TRUNCATE|DELETE)\b", statement, re.IGNORECASE)
    ]
    indexed_text_columns: list[str] = []
    oversized_indexes: list[str] = []
    table_columns: dict[str, dict[str, str]] = {}
    for statement in converted:
        match = re.search(r"CREATE TABLE IF NOT EXISTS\s+(\w+)", statement, re.IGNORECASE)
        if not match:
            continue
        columns: dict[str, str] = {}
        for line in statement.splitlines():
            column = re.match(r"\s*([A-Za-z_]\w*)\s+([A-Z]+(?:\(\d+\))?)", line, re.IGNORECASE)
            if column and column.group(1).upper() not in {"CREATE", "UNIQUE", "PRIMARY", "FOREIGN", "CHECK", "CONSTRAINT"}:
                columns[column.group(1)] = column.group(2).upper()
        table_columns[match.group(1)] = columns
    for statement in models.INDEX_SQL:
        parsed = database._parse_index_statement(statement)
        target = database._parse_index_target(parsed[1]) if parsed else None
        if not target:
            continue
        table, columns = target
        width = 0
        for column in columns:
            value = table_columns.get(table, {}).get(column, "")
            if value in {"TEXT", "LONGTEXT"}:
                indexed_text_columns.append(f"{table}.{column}")
            match = re.fullmatch(r"VARCHAR\((\d+)\)", value)
            if match:
                width += int(match.group(1)) * 4
        if width > 3072:
            oversized_indexes.append(statement)
    return {
        "ok": not invalid_text_defaults and not destructive and not indexed_text_columns and not oversized_indexes,
        "mysql_version": "5.7-contract",
        "schema_statement_count": len(converted),
        "index_statement_count": len(models.INDEX_SQL),
        "invalid_text_defaults": invalid_text_defaults,
        "destructive_statements": destructive,
        "indexed_text_columns": indexed_text_columns,
        "oversized_indexes": oversized_indexes,
        "placeholder_conversion_ok": database._mysqlize_query("SELECT * FROM users WHERE id = ?") == "SELECT * FROM users WHERE id = %s",
    }


def exercise(work_dir: Path | None = None) -> dict:
    matrix = json.loads(MATRIX_PATH.read_text(encoding="utf-8"))
    base_dir = work_dir.resolve() if work_dir is not None else None
    if base_dir is not None:
        base_dir.mkdir(parents=True, exist_ok=True)
    temporary = tempfile.TemporaryDirectory(
        prefix="safehome-f18-",
        dir=base_dir,
        ignore_cleanup_errors=True,
    )
    root = Path(temporary.name)
    try:
        empty = root / "empty.sqlite3"
        legacy = root / "legacy.sqlite3"
        partial = root / "partial.sqlite3"
        interrupted = root / "interrupted.sqlite3"
        backup = root / "backup.sqlite3"
        restored = root / "restored.sqlite3"
        empty_health = _apply(empty)
        first_manifest = _manifest(empty)
        repeated_health = _apply(empty)
        repeated_manifest = _manifest(empty)

        _seed_legacy(legacy)
        legacy_health = _apply(legacy)
        with sqlite3.connect(legacy) as conn:
            legacy_preserved = conn.execute("SELECT value FROM legacy_marker WHERE id = 'keep-me'").fetchone()[0] == "preserved"

        _seed_partial(partial)
        partial_health = _apply(partial)

        _apply(interrupted)
        with sqlite3.connect(interrupted) as conn:
            conn.execute("CREATE TABLE IF NOT EXISTS f18_transaction_probe (id TEXT PRIMARY KEY)")
            try:
                conn.execute("BEGIN")
                conn.execute("INSERT INTO f18_transaction_probe VALUES ('must-rollback')")
                raise RuntimeError("simulated interruption")
            except RuntimeError:
                conn.rollback()
            interrupted_count = int(conn.execute("SELECT COUNT(*) FROM f18_transaction_probe").fetchone()[0])

        with sqlite3.connect(empty) as source, sqlite3.connect(backup) as target:
            source.backup(target)
        backup_manifest = _manifest(backup)
        with sqlite3.connect(backup) as source, sqlite3.connect(restored) as target:
            source.backup(target)
        restored_manifest = _manifest(restored)
        restore_equal = (
            backup_manifest["schema_hash"] == restored_manifest["schema_hash"]
            and backup_manifest["table_row_counts"] == restored_manifest["table_row_counts"]
            and backup_manifest["schema_version"] == restored_manifest["schema_version"]
        )

        mysql = mysql57_contract()
        result = {
            "schema": "safehome.task36.migration_evidence.v1",
            "matrix_version": matrix["version"],
            "target_schema": matrix["target_schema"],
            "scenarios": {
                "empty_database": empty_health["ok"],
                "legacy_database": legacy_health["ok"] and legacy_preserved,
                "repeated_apply": repeated_health["ok"] and first_manifest["schema_hash"] == repeated_manifest["schema_hash"],
                "partially_created_target_tables": partial_health["ok"],
                "interrupted_transaction": interrupted_count == 0,
                "backup_restore_isolated": restore_equal,
                "mysql57_contract": mysql["ok"] and mysql["placeholder_conversion_ok"],
            },
            "backup_manifest": backup_manifest,
            "restore_manifest": restored_manifest,
            "mysql57": mysql,
            "production_commands": {
                "apply": "python backend/scripts/task36_migration_recovery.py production-command --action apply",
                "restore": "python backend/scripts/task36_migration_recovery.py production-command --action restore",
                "rollback": "python backend/scripts/task36_migration_recovery.py production-command --action rollback",
            },
            "production_mutation_executed": False,
            "external_gate_approved": False,
            "release_approved": False,
        }
        result["ok"] = all(result["scenarios"].values())
        return result
    finally:
        temporary.cleanup()


def rollback_plan() -> dict:
    matrix = json.loads(MATRIX_PATH.read_text(encoding="utf-8"))
    return {
        "action": "rollback_plan",
        "steps": matrix["rollback_order"],
        "drop_tables": False,
        "delete_history": False,
        "delete_audit": False,
        "production_mutation_executed": False,
        "requires_human_approval": True,
    }


def production_command(action: str) -> dict:
    return {
        "action": action,
        "command_generated_only": True,
        "production_mutation_executed": False,
        "requires_human_approval": True,
        "required_confirmation": PRODUCTION_CONFIRMATION,
        "operator_note": "先在批准的维护窗口完成备份、hash和行数核对；本工具不会自动连接或修改生产数据库。",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["plan", "exercise", "verify", "rollback", "production-command"])
    parser.add_argument("--work-dir", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--action", dest="production_action", choices=["apply", "restore", "rollback"])
    args = parser.parse_args()
    if args.action == "plan":
        result = {
            "action": "plan",
            "matrix": json.loads(MATRIX_PATH.read_text(encoding="utf-8")),
            "production_mutation_executed": False,
        }
    elif args.action in {"exercise", "verify"}:
        result = exercise(args.work_dir)
    elif args.action == "rollback":
        result = rollback_plan()
    else:
        result = production_command(args.production_action or "apply")
    payload = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload + "\n", encoding="utf-8")
    print(payload)
    return 0 if result.get("ok", True) else 1


if __name__ == "__main__":
    raise SystemExit(main())
