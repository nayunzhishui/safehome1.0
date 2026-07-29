import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
REGISTRY = ROOT / "content" / "task37_release_execution_registry.json"
SCRIPT = ROOT / "backend" / "scripts" / "task37_r02_migration_evidence.py"


def _module():
    spec = importlib.util.spec_from_file_location("task37_r02_migration_evidence", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_r02_isolated_backup_restore_checksum_counts_and_tombstone(tmp_path):
    result = _module().exercise(tmp_path)
    assert result["ok"] is True
    assert result["source_manifest"]["schema_version"] == result["target_schema_version"]
    assert result["backup_restore_equivalent"] is True
    assert result["backup_manifest"]["table_row_counts"] == result["restore_manifest"]["table_row_counts"]
    assert len(result["backup_manifest"]["sha256"]) == 64
    assert len(result["backup_manifest"]["schema_hash"]) == 64
    assert result["privacy_tombstone"]["ok"] is True
    assert result["privacy_tombstone"]["tombstone_count"] == 1
    assert result["raw_identifiers_included"] is False


def test_r02_plan_and_rollback_are_non_destructive():
    module = _module()
    plan = module.plan()
    rollback = module.rollback_plan()
    assert plan["command_generation_only"] is True
    assert plan["production_migration_executed"] is False
    assert rollback["policy"]["drop_tables_automatically"] is False
    assert rollback["policy"]["delete_audit_automatically"] is False
    assert rollback["rollback_executed"] is False
    for operation in ("apply", "restore", "rollback"):
        command = module.production_command(operation)
        assert command["command_generated_only"] is True
        assert command["production_mutation_executed"] is False


def test_r02_registry_requires_backup_restore_tombstone_and_independent_verifier():
    payload = json.loads(REGISTRY.read_text(encoding="utf-8"))
    stage = next(item for item in payload["stages"] if item["id"] == "R02")
    fields = set(stage["required_evidence_fields"])
    assert {
        "backup_sha256",
        "backup_integrity_check",
        "pre_migration_row_counts",
        "post_migration_row_counts",
        "schema_hash_before",
        "schema_hash_after",
        "restore_sha256",
        "restore_row_counts",
        "privacy_tombstone_result",
        "rollback_rehearsal_result",
        "independent_verifier_reference",
    } <= fields
    assert stage["privacy_tombstone_required"] is True
    assert stage["checksum_and_row_count_required"] is True
    assert stage["production_migration_executed"] is False
    assert stage["production_restore_executed"] is False
