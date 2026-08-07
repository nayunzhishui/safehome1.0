import importlib
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"


def _fresh_database(tmp_path, monkeypatch):
    sys.path.insert(0, str(BACKEND))
    for name in ["config", "models", "database"]:
        sys.modules.pop(name, None)
    monkeypatch.setenv("APP_ENV", "testing")
    monkeypatch.setenv("DB_PROVIDER", "sqlite")
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "integrity.sqlite3"))
    monkeypatch.setenv("CONTENT_DIR", str(ROOT / "content"))
    database = importlib.import_module("database")
    database.init_db()
    return database


def test_runtime_architecture_guard_passes_current_repository():
    module_path = BACKEND / "scripts" / "audit_runtime_architecture.py"
    spec = importlib.util.spec_from_file_location("audit_runtime_architecture", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)

    result = module.audit()
    assert result["ok"] is True
    assert result["architecture_style"] == "modular_monolith"


def test_generic_computation_contract_keeps_legacy_import_compatible():
    sys.path.insert(0, str(BACKEND))
    generic = importlib.import_module("services.computation_contract_service")
    legacy = importlib.import_module("services.task37_contract_service")

    assert generic.public_status() == legacy.public_status()
    assert generic.registry()["contract_version"] == "safehome.computation.v1"
    assert generic.registry()["migration"]["task_number_is_runtime_domain"] is False


def test_referential_integrity_audit_detects_orphan_without_exposing_text(tmp_path, monkeypatch):
    database = _fresh_database(tmp_path, monkeypatch)
    service = importlib.import_module("services.referential_integrity_service")

    with database.get_connection() as conn:
        baseline = service.audit_referential_integrity(conn)
        assert baseline["ok"] is True

        conn.execute(
            """
            INSERT INTO consent_records (
                id, user_id, consent_type, consent_version, agreed,
                agreed_at, revoked_at, created_at
            ) VALUES (?, ?, ?, ?, 1, ?, NULL, ?)
            """,
            (
                "consent-orphan-test",
                "missing-user",
                "privacy_policy",
                "test-v1",
                database.now_iso(),
                database.now_iso(),
            ),
        )
        conn.commit()
        result = service.audit_referential_integrity(conn)

    assert result["ok"] is False
    consent_check = next(item for item in result["checks"] if item["relationship"] == "consent_records.user_id")
    assert consent_check["orphan_count"] == 1
    assert "missing-user" not in str(result)


def test_assert_reference_exists_rejects_unknown_user(tmp_path, monkeypatch):
    database = _fresh_database(tmp_path, monkeypatch)
    service = importlib.import_module("services.referential_integrity_service")

    with database.get_connection() as conn:
        try:
            service.assert_reference_exists(
                conn,
                source_table="consent_records",
                source_column="user_id",
                target_table="users",
                target_column="id",
                value="missing-user",
            )
        except ValueError as exc:
            assert "不存在" in str(exc)
        else:
            raise AssertionError("orphan reference should be rejected")
