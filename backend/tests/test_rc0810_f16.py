import hashlib
import json
import sqlite3
import ssl
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = PROJECT_ROOT / "backend"
sys.path.insert(0, str(BACKEND_ROOT))


def _source_database(path: Path, *, orphan: bool = False) -> None:
    conn = sqlite3.connect(path)
    conn.executescript(
        """
        CREATE TABLE users (id TEXT PRIMARY KEY, status TEXT NOT NULL);
        CREATE TABLE assessment_results (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            result_summary TEXT NOT NULL
        );
        CREATE TABLE explicit_schema_migrations (
            version TEXT PRIMARY KEY,
            applied_at TEXT NOT NULL
        );
        """
    )
    conn.execute("INSERT INTO users VALUES ('user-1', 'active')")
    conn.execute(
        "INSERT INTO assessment_results VALUES ('result-1', ?, 'synthetic')",
        ("missing-user" if orphan else "user-1",),
    )
    conn.execute(
        "INSERT INTO explicit_schema_migrations VALUES ('2026_08_25_070', '2026-08-25T00:00:00+00:00')"
    )
    conn.commit()
    conn.close()


def _marker(directory: Path, target: Path, environment: str = "isolated_validation") -> Path:
    marker = directory / ".safehome-recovery-target.json"
    marker.write_text(
        json.dumps({"environment": environment, "allowed_target": target.name}),
        encoding="utf-8",
    )
    return marker


def test_production_tls_contract_requires_ca_identity_and_tls12(tmp_path):
    from services.database_recovery_service import tls_contract_errors

    settings = SimpleNamespace(
        APP_ENV="production",
        DB_PROVIDER="mysql",
        MYSQL_SSL_CA="",
        MYSQL_SSL_VERIFY_IDENTITY=False,
        MYSQL_TLS_MIN_VERSION="TLSv1.1",
    )
    assert tls_contract_errors(settings) == [
        "mysql_tls_ca_required",
        "mysql_tls_identity_verification_required",
        "mysql_tls_minimum_version_too_low",
    ]


def test_tls_context_rejects_bad_ca_and_enforces_minimum(tmp_path):
    from services.database_recovery_service import mysql_ssl_context

    bad_ca = tmp_path / "bad-ca.pem"
    bad_ca.write_text("not a certificate", encoding="utf-8")
    with pytest.raises(ssl.SSLError):
        mysql_ssl_context(bad_ca, "TLSv1.2")
    context = mysql_ssl_context(None, "TLSv1.2")
    assert context.minimum_version == ssl.TLSVersion.TLSv1_2
    assert context.check_hostname is True
    assert context.verify_mode == ssl.CERT_REQUIRED


def test_hostname_check_fails_closed_and_public_contract_redacts_ca():
    from services.database_recovery_service import public_tls_contract, verify_peer_hostname

    certificate = {"subjectAltName": (("DNS", "mysql.internal.example"),)}
    verify_peer_hostname(certificate, "mysql.internal.example")
    with pytest.raises(ssl.CertificateError):
        verify_peer_hostname(certificate, "other.internal.example")
    public = public_tls_contract("C:/private/mysql-ca.pem", "TLSv1.2", True)
    assert public == {
        "ca_configured": True,
        "verify_identity": True,
        "minimum_version": "TLSv1.2",
    }
    assert "private" not in json.dumps(public)


def test_integrity_contract_detects_orphan_rows(tmp_path):
    from services.database_recovery_service import detect_orphans, load_recovery_policy

    database_path = tmp_path / "orphan.sqlite3"
    _source_database(database_path, orphan=True)
    conn = sqlite3.connect(database_path)
    conn.row_factory = sqlite3.Row
    findings = detect_orphans(conn, load_recovery_policy()["relationships"])
    conn.close()
    assert findings["assessment_result_owner"]["orphan_count"] == 1
    assert findings["assessment_result_owner"]["status"] == "failed"


def test_backup_manifest_records_head_counts_digest_time_and_encryption(tmp_path):
    from services.database_recovery_service import create_sqlite_backup

    source = tmp_path / "source.sqlite3"
    backup = tmp_path / "backup.sqlite3"
    _source_database(source)
    manifest = create_sqlite_backup(source, backup, encryption_state="synthetic_unencrypted")
    assert manifest["schema_head"] == "2026_08_25_070"
    assert manifest["table_counts"]["users"] == 1
    assert manifest["sha256"] == hashlib.sha256(backup.read_bytes()).hexdigest()
    assert manifest["started_at"] <= manifest["finished_at"]
    assert manifest["encryption_state"] == "synthetic_unencrypted"


def test_restore_refuses_production_or_unmarked_target(tmp_path):
    from services.database_recovery_service import RecoveryError, create_sqlite_backup, restore_sqlite_backup

    source = tmp_path / "source.sqlite3"
    backup = tmp_path / "backup.sqlite3"
    target = tmp_path / "target.sqlite3"
    _source_database(source)
    manifest = create_sqlite_backup(source, backup, encryption_state="synthetic_unencrypted")
    with pytest.raises(RecoveryError, match="隔离恢复目标标识"):
        restore_sqlite_backup(backup, manifest, target)
    _marker(tmp_path, target, "production")
    with pytest.raises(RecoveryError, match="禁止恢复到 production"):
        restore_sqlite_backup(backup, manifest, target)


def test_corrupted_backup_is_rejected_before_restore(tmp_path):
    from services.database_recovery_service import RecoveryError, create_sqlite_backup, restore_sqlite_backup

    source = tmp_path / "source.sqlite3"
    backup = tmp_path / "backup.sqlite3"
    target = tmp_path / "target.sqlite3"
    _source_database(source)
    manifest = create_sqlite_backup(source, backup, encryption_state="synthetic_unencrypted")
    backup.write_bytes(backup.read_bytes() + b"corrupt")
    _marker(tmp_path, target)
    with pytest.raises(RecoveryError, match="备份校验摘要不匹配"):
        restore_sqlite_backup(backup, manifest, target)
    assert not target.exists()


def test_interrupted_restore_keeps_existing_target_unchanged(tmp_path):
    from services.database_recovery_service import RecoveryError, create_sqlite_backup, restore_sqlite_backup

    source = tmp_path / "source.sqlite3"
    backup = tmp_path / "backup.sqlite3"
    target = tmp_path / "target.sqlite3"
    _source_database(source)
    manifest = create_sqlite_backup(source, backup, encryption_state="synthetic_unencrypted")
    target.write_bytes(b"existing-target")
    _marker(tmp_path, target)
    with pytest.raises(RecoveryError, match="模拟恢复中断"):
        restore_sqlite_backup(backup, manifest, target, inject_failure=True)
    assert target.read_bytes() == b"existing-target"
    assert not target.with_suffix(".sqlite3.restore").exists()


def test_repeated_restore_is_idempotent_and_post_checks_pass(tmp_path):
    from services.database_recovery_service import create_sqlite_backup, restore_sqlite_backup

    source = tmp_path / "source.sqlite3"
    backup = tmp_path / "backup.sqlite3"
    target = tmp_path / "target.sqlite3"
    _source_database(source)
    manifest = create_sqlite_backup(source, backup, encryption_state="synthetic_unencrypted")
    _marker(tmp_path, target)
    first = restore_sqlite_backup(backup, manifest, target)
    second = restore_sqlite_backup(backup, manifest, target)
    assert first["status"] == "restored"
    assert second["status"] == "already_restored"
    assert first["post_restore"]["schema_head"] == "2026_08_25_070"
    assert first["post_restore"]["orphan_count"] == 0
    assert first["production_release_approved"] is False


def test_f11_fixture_backup_restore_upgrade_drill_is_synthetic_and_no_go():
    result = subprocess.run(
        [sys.executable, str(BACKEND_ROOT / "scripts" / "run_database_recovery_drill.py")],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert report["fixture_data_class"] == "synthetic_only"
    assert report["before"] == report["after"]
    assert report["migration_head"] == "2026_08_25_070"
    assert report["rpo_rto"]["production_actual"] is None
    assert report["rpo_rto"]["status"] == "pending_external"
    assert report["production_release_approved"] is False
