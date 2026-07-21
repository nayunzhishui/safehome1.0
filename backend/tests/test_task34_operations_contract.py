import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_task34_machine_contract_roles_and_miniprogram_read_only_boundary():
    contract = json.loads((ROOT / "shared/contracts/api-contract.json").read_text(encoding="utf-8"))
    by_key = {(item["method"], item["path"]): item for item in contract["endpoints"]}
    assert by_key[("GET", "/api/operations-governance/public-status")]["access"]["roles"] == ["public"]
    assert by_key[("GET", "/api/operations-governance/workbench")]["access"]["roles"] == ["researcher", "supervisor", "admin"]
    assert by_key[("POST", "/api/operations-governance/packages")]["access"]["roles"] == ["researcher", "supervisor", "admin"]
    assert by_key[("POST", "/api/operations-governance/packages/<package_id>/release")]["access"]["roles"] == ["admin"]
    assert by_key[("POST", "/api/operations-governance/evidence-packages")]["access"]["roles"] == ["supervisor", "admin"]
    mini = (ROOT / "apps/miniprogram/services/api.js").read_text(encoding="utf-8")
    assert "getOperationsGovernancePublicStatus" in mini
    assert "createOperationsReleasePackage" not in mini
    assert "reportOperationsIncident" not in mini


def test_task34_schema_shared_web_migration_and_rollback_contracts_exist():
    models = (ROOT / "backend/models.py").read_text(encoding="utf-8")
    types = (ROOT / "shared/types/api.ts").read_text(encoding="utf-8")
    web = (ROOT / "apps/web/src/pages/OperationsGovernanceWorkbench.tsx").read_text(encoding="utf-8")
    migration = (ROOT / "backend/scripts/migrate_task34_operations_governance.py").read_text(encoding="utf-8")
    tables = {
        "operations_release_packages",
        "operations_package_reviews",
        "operations_replay_runs",
        "operations_runtime_controls",
        "operations_monitor_snapshots",
        "operations_incidents",
        "operations_incident_notifications",
        "operations_evidence_packages",
    }
    assert all(f"CREATE TABLE IF NOT EXISTS {table}" in models for table in tables)
    assert all(name in types for name in ["OperationsCapability", "OperationsReleasePackage", "OperationsIncident", "OperationsMonitoringSnapshot"])
    assert all(label in web for label in ["能力与开放边界", "不可变发布包", "固定合成回放", "漂移复核", "事件与停用"])
    assert "automatic_schema_rollback_executed" in migration and "retain_tables" in migration


def test_task34_registry_cards_and_release_manifest_are_deterministically_checkable():
    script = (ROOT / "backend/scripts/generate_task34_operations_registry.py").read_text(encoding="utf-8")
    audit = (ROOT / "backend/scripts/audit_task34_operations.py").read_text(encoding="utf-8")
    assert "--check" in script
    assert all(name in audit for name in ["operations_capability_registry.json", "operations_asset_cards.json", "operations_release_manifest.json"])
    registry = json.loads((ROOT / "content/operations_capability_registry.json").read_text(encoding="utf-8"))
    assert registry["temporary_showcase_exception"]["formal_permission_acceptance"] is False
    assert registry["treatment_assessment"]["real_participant_release_allowed"] is False
    assert registry["production_release_approved"] is False
