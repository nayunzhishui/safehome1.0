import importlib
import shutil
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"


def _app(tmp_path, monkeypatch):
    sys.path.insert(0, str(BACKEND))
    from test_consent_route import _fresh_app

    return _fresh_app(tmp_path, monkeypatch)


def _service():
    sys.modules.pop("services.task37_lineage_service", None)
    return importlib.import_module("services.task37_lineage_service")


def test_schema_030_adds_lineage_and_lifecycle_tables(tmp_path, monkeypatch):
    _app(tmp_path, monkeypatch)
    database = importlib.import_module("database")
    assert database.CURRENT_SCHEMA_VERSION == "2026_07_27_036"
    with database.get_connection() as conn:
        tables = {row["name"] for row in database.list_database_tables(conn)}
        assert {
            "computation_datasets",
            "computation_authorization_snapshots",
            "computation_lineage_edges",
            "computation_deletion_tombstones",
            "computation_legal_holds",
        } <= tables


def test_dataset_registry_rejects_raw_text_and_records_authorization_snapshot(tmp_path, monkeypatch):
    _app(tmp_path, monkeypatch)
    service = _service()
    with pytest.raises(service.LineageError) as exc:
        service.register_dataset({"id": "ds-raw", "raw_text": "不应写入"})
    assert exc.value.code == "raw_sensitive_data_forbidden"

    dataset = service.register_dataset(
        {
            "id": "ds-1",
            "dataset_key": "participant-observation",
            "version": "v1",
            "data_class": "source_metadata",
            "storage_layer": "restricted_source",
            "source_kind": "participant_text",
            "rights_status": "explicit_opt_in",
            "purpose": "quality_evaluation",
            "retention_until": "2026-08-27T00:00:00Z",
        }
    )
    snapshot = service.record_authorization(
        dataset["id"],
        {
            "subject_ref": "participant-1",
            "consent_type": "quality_evaluation",
            "consent_version": "2026.07-quality-v1",
            "status": "agreed",
        },
    )
    assert dataset["raw_text_stored"] is False
    assert snapshot["subject_hash"] != "participant-1"


def test_withdrawal_traces_all_descendants_and_keeps_minimal_tombstone(tmp_path, monkeypatch):
    _app(tmp_path, monkeypatch)
    service = _service()
    service.add_lineage("dataset", "ds-1", "feature", "feature-1", "rules-v1", "quality_evaluation")
    service.add_lineage("feature", "feature-1", "model_run", "run-1", "model-v1", "quality_evaluation")
    service.add_lineage("model_run", "run-1", "research_export", "export-1", "export-v1", "secondary_research")

    traced = service.trace_descendants("dataset", "ds-1")
    assert [(item["resource_type"], item["resource_id"]) for item in traced] == [
        ("feature", "feature-1"),
        ("model_run", "run-1"),
        ("research_export", "export-1"),
    ]

    result = service.record_withdrawal("participant-1", "dataset", "ds-1", "consent_withdrawn")
    assert result["affected_count"] == 4
    assert result["raw_subject_stored"] is False
    database = importlib.import_module("database")
    with database.get_connection() as conn:
        row = conn.execute("SELECT * FROM computation_deletion_tombstones").fetchone()
        assert "participant-1" not in str(dict(row))
        assert "export-1" in row["affected_resources_json"]


def test_legal_hold_is_recorded_without_silently_deleting_lineage(tmp_path, monkeypatch):
    _app(tmp_path, monkeypatch)
    service = _service()
    hold = service.create_legal_hold("dataset", "ds-1", "ethics_investigation", "2026-08-30T00:00:00Z")
    result = service.record_withdrawal("participant-2", "dataset", "ds-1", "consent_withdrawn")
    assert hold["reason_code"] == "ethics_investigation"
    assert result["blocked_by_legal_hold"] is True
    assert result["tombstone_recorded"] is True


def test_migration_plan_and_rollback_are_non_destructive(tmp_path, monkeypatch):
    _app(tmp_path, monkeypatch)
    sys.modules.pop("scripts.migrate_task37_p03_lineage", None)
    module = importlib.import_module("scripts.migrate_task37_p03_lineage")
    plan = module.inspect()
    assert plan["ok"] is True
    assert plan["schema_version"] == "2026_07_27_036"
    rollback = module.rollback()
    assert rollback["schema_preserved"] is True
    assert rollback["tables_dropped"] is False
    assert rollback["production_mutation"] is False


def test_backup_restore_verifier_matches_schema_counts_and_tombstones(tmp_path, monkeypatch):
    _app(tmp_path, monkeypatch)
    service = _service()
    service.record_withdrawal("participant-restore", "dataset", "ds-restore", "consent_withdrawn")
    source = tmp_path / "safehome-test.sqlite3"
    restored = tmp_path / "restored.sqlite3"
    shutil.copy2(source, restored)

    sys.modules.pop("scripts.verify_task37_p03_lineage_restore", None)
    verifier = importlib.import_module("scripts.verify_task37_p03_lineage_restore")
    result = verifier.compare(source, restored)
    assert result["ok"] is True
    assert result["source"]["schema_version"] == "2026_07_27_036"
    assert result["source"]["tombstone_sha256"] == result["restored"]["tombstone_sha256"]
    assert result["raw_rows_emitted"] is False


def test_production_apply_requires_exact_confirmation(tmp_path, monkeypatch):
    _app(tmp_path, monkeypatch)
    module = importlib.import_module("scripts.migrate_task37_p03_lineage")
    previous = module.Config.APP_ENV
    module.Config.APP_ENV = "production"
    try:
        with pytest.raises(RuntimeError, match="生产迁移已阻断"):
            module._guard("apply", False, "")
        module._guard("apply", True, module.PRODUCTION_CONFIRMATION)
    finally:
        module.Config.APP_ENV = previous
