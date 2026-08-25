"""Fail-closed MySQL TLS and isolated synthetic backup/restore helpers."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import sqlite3
import ssl
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_POLICY_PATH = ROOT / "config" / "rc0810" / "database_recovery_policy.json"
ALLOWED_TLS_VERSIONS = {"TLSv1.2": ssl.TLSVersion.TLSv1_2, "TLSv1.3": ssl.TLSVersion.TLSv1_3}


@dataclass(frozen=True)
class RecoveryError(ValueError):
    message: str

    def __str__(self) -> str:
        return self.message


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def tls_contract_errors(settings: Any) -> list[str]:
    if str(getattr(settings, "APP_ENV", "")).lower() != "production" or str(
        getattr(settings, "DB_PROVIDER", "")
    ).lower() != "mysql":
        return []
    errors: list[str] = []
    ca_path = str(getattr(settings, "MYSQL_SSL_CA", "") or "").strip()
    if not ca_path or not Path(ca_path).is_file():
        errors.append("mysql_tls_ca_required")
    if not bool(getattr(settings, "MYSQL_SSL_VERIFY_IDENTITY", False)):
        errors.append("mysql_tls_identity_verification_required")
    if str(getattr(settings, "MYSQL_TLS_MIN_VERSION", "")) not in ALLOWED_TLS_VERSIONS:
        errors.append("mysql_tls_minimum_version_too_low")
    return errors


def mysql_ssl_context(ca_path: str | Path | None, minimum_version: str) -> ssl.SSLContext:
    version = ALLOWED_TLS_VERSIONS.get(str(minimum_version))
    if version is None:
        raise RecoveryError("MySQL TLS 最低版本必须为 TLSv1.2 或 TLSv1.3")
    context = ssl.create_default_context(cafile=str(ca_path) if ca_path else None)
    context.minimum_version = version
    context.check_hostname = True
    context.verify_mode = ssl.CERT_REQUIRED
    return context


def verify_peer_hostname(certificate: dict[str, Any], hostname: str) -> None:
    ssl.match_hostname(certificate, hostname)


def public_tls_contract(ca_path: str, minimum_version: str, verify_identity: bool) -> dict[str, Any]:
    return {
        "ca_configured": bool(str(ca_path or "").strip()),
        "verify_identity": bool(verify_identity),
        "minimum_version": str(minimum_version),
    }


def load_recovery_policy(path: str | Path | None = None) -> dict[str, Any]:
    payload = json.loads(Path(path or DEFAULT_POLICY_PATH).read_text(encoding="utf-8"))
    if payload.get("schema") != "safehome.rc0810.database-recovery-policy.v1":
        raise RecoveryError("数据库恢复策略版本无效")
    return payload


def _safe_identifier(value: str) -> str:
    if not value.replace("_", "a").isalnum() or not value:
        raise RecoveryError("关系合同包含非法标识符")
    return value


def _table_names(conn: sqlite3.Connection) -> set[str]:
    return {
        str(row[0])
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'"
        ).fetchall()
    }


def detect_orphans(conn: sqlite3.Connection, relationships: list[dict[str, Any]]) -> dict[str, Any]:
    tables = _table_names(conn)
    results: dict[str, Any] = {}
    for relation in relationships:
        child = _safe_identifier(str(relation["child_table"]))
        parent = _safe_identifier(str(relation["parent_table"]))
        child_column = _safe_identifier(str(relation["child_column"]))
        parent_column = _safe_identifier(str(relation["parent_column"]))
        query = (
            f"SELECT COUNT(*) FROM {child} c LEFT JOIN {parent} p "
            f"ON c.{child_column} = p.{parent_column} "
            f"WHERE c.{child_column} IS NOT NULL AND p.{parent_column} IS NULL"
        )
        if child not in tables or parent not in tables:
            results[str(relation["id"])] = {
                "status": "not_applicable",
                "orphan_count": 0,
                "orphan_detection_sql": query,
            }
            continue
        count = int(conn.execute(query).fetchone()[0])
        results[str(relation["id"])] = {
            "status": "passed" if count == 0 else "failed",
            "orphan_count": count,
            "orphan_detection_sql": query,
        }
    return results


def _database_snapshot(path: Path) -> dict[str, Any]:
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    try:
        integrity = str(conn.execute("PRAGMA integrity_check").fetchone()[0])
        tables = sorted(_table_names(conn))
        counts: dict[str, int] = {}
        samples: dict[str, str] = {}
        for table in tables:
            safe = _safe_identifier(table)
            counts[table] = int(conn.execute(f"SELECT COUNT(*) FROM {safe}").fetchone()[0])
            rows = conn.execute(f"SELECT * FROM {safe} ORDER BY rowid LIMIT 10").fetchall()
            encoded = json.dumps(
                [dict(row) for row in rows], ensure_ascii=False, sort_keys=True, default=str
            ).encode("utf-8")
            samples[table] = hashlib.sha256(encoded).hexdigest()
        schema_head = None
        if "explicit_schema_migrations" in tables:
            row = conn.execute(
                "SELECT version FROM explicit_schema_migrations ORDER BY version DESC LIMIT 1"
            ).fetchone()
            schema_head = str(row["version"]) if row else None
        relationships = detect_orphans(conn, load_recovery_policy()["relationships"])
        return {
            "integrity_check": integrity,
            "schema_head": schema_head,
            "table_counts": counts,
            "sample_hashes": samples,
            "relationships": relationships,
            "orphan_count": sum(item["orphan_count"] for item in relationships.values()),
        }
    finally:
        conn.close()


def create_sqlite_backup(
    source_path: str | Path,
    backup_path: str | Path,
    *,
    encryption_state: str,
) -> dict[str, Any]:
    source = Path(source_path).resolve()
    backup = Path(backup_path).resolve()
    started_at = _utc_now()
    backup.parent.mkdir(parents=True, exist_ok=True)
    source_conn = sqlite3.connect(source)
    backup_conn = sqlite3.connect(backup)
    try:
        source_conn.backup(backup_conn)
    finally:
        backup_conn.close()
        source_conn.close()
    snapshot = _database_snapshot(backup)
    return {
        "schema": "safehome.rc0810.database-backup-manifest.v1",
        "source_kind": "synthetic_sqlite",
        "schema_head": snapshot["schema_head"],
        "table_counts": snapshot["table_counts"],
        "sample_hashes": snapshot["sample_hashes"],
        "sha256": _sha256(backup),
        "started_at": started_at,
        "finished_at": _utc_now(),
        "encryption_state": str(encryption_state),
        "production_release_approved": False,
    }


def _validate_target_marker(target: Path) -> None:
    marker_path = target.parent / ".safehome-recovery-target.json"
    if not marker_path.is_file():
        raise RecoveryError("缺少隔离恢复目标标识")
    try:
        marker = json.loads(marker_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise RecoveryError("隔离恢复目标标识无效") from exc
    if marker.get("environment") == "production":
        raise RecoveryError("禁止恢复到 production 目标")
    if marker.get("environment") != "isolated_validation" or marker.get("allowed_target") != target.name:
        raise RecoveryError("隔离恢复目标标识不匹配")


def restore_sqlite_backup(
    backup_path: str | Path,
    manifest: dict[str, Any],
    target_path: str | Path,
    *,
    inject_failure: bool = False,
) -> dict[str, Any]:
    backup = Path(backup_path).resolve()
    target = Path(target_path).resolve()
    _validate_target_marker(target)
    if manifest.get("schema") != "safehome.rc0810.database-backup-manifest.v1":
        raise RecoveryError("备份清单版本无效")
    if not backup.is_file() or _sha256(backup) != manifest.get("sha256"):
        raise RecoveryError("备份校验摘要不匹配")
    if target.is_file() and _sha256(target) == manifest["sha256"]:
        snapshot = _database_snapshot(target)
        return {
            "status": "already_restored",
            "post_restore": snapshot,
            "production_release_approved": False,
        }
    temporary = target.with_suffix(target.suffix + ".restore")
    try:
        shutil.copy2(backup, temporary)
        if inject_failure:
            raise RecoveryError("模拟恢复中断")
        snapshot = _database_snapshot(temporary)
        if snapshot["integrity_check"] != "ok":
            raise RecoveryError("恢复副本完整性检查失败")
        if snapshot["table_counts"] != manifest.get("table_counts"):
            raise RecoveryError("恢复后表计数不匹配")
        if snapshot["sample_hashes"] != manifest.get("sample_hashes"):
            raise RecoveryError("恢复后抽样摘要不匹配")
        os.replace(temporary, target)
    finally:
        if temporary.exists():
            temporary.unlink()
    return {
        "status": "restored",
        "post_restore": snapshot,
        "permission_check": "isolated_validation_only",
        "production_release_approved": False,
    }
