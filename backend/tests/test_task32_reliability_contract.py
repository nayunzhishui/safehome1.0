import importlib
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"


def test_reliability_registry_generator_and_content_validator_pass():
    assert subprocess.run([sys.executable, "backend/scripts/generate_task32_reliability_registry.py", "--check"], cwd=ROOT).returncode == 0
    assert subprocess.run([sys.executable, "backend/scripts/validate_content.py"], cwd=ROOT).returncode == 0


def test_registry_has_complete_journeys_jobs_faults_and_human_gates():
    registry = json.loads((ROOT / "content/reliability_release_registry.json").read_text(encoding="utf-8"))
    assert len(registry["journeys"]) == 9
    assert set(registry["trace_fields"]) == {"request_id", "actor_scope", "module", "journey", "outcome", "error_code", "status_code", "latency_ms", "retry_count", "recovered"}
    assert {"notification_delivery", "privacy_execution", "ai_evaluation", "offline_benchmark"}.issubset(
        {item["job_type"] for item in registry["job_adapters"]}
    )
    assert {item["scenario"] for item in registry["fault_scenarios"]} == {"content_missing", "database_timeout", "provider_failure", "token_invalidated", "duplicate_message", "artifact_corrupted"}
    assert registry["production_slo"]["status"] == "pending_test_cloud_observation"
    assert registry["production_release"]["approved"] is False


def test_machine_contract_registers_reliability_roles():
    contract = json.loads((ROOT / "shared/contracts/api-contract.json").read_text(encoding="utf-8"))
    by_key = {(item["method"], item["path"]): item for item in contract["endpoints"]}
    assert by_key[("GET", "/api/reliability/public-status")]["access"]["roles"] == ["public"]
    assert by_key[("GET", "/api/reliability/workbench")]["access"]["roles"] == ["researcher", "supervisor", "admin"]
    assert by_key[("POST", "/api/reliability/jobs")]["access"]["roles"] == ["admin"]
    assert by_key[("PATCH", "/api/reliability/feature-flags/<flag_name>")]["access"]["roles"] == ["admin"]
    assert by_key[("POST", "/api/reliability/evidence-packages")]["access"]["roles"] == ["supervisor", "admin"]


def test_schema_migration_and_rollback_plan_are_idempotent(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "task32-migrate.sqlite3"))
    sys.path.insert(0, str(BACKEND))
    for name in ["config", "database", "models"]:
        sys.modules.pop(name, None)
    migration = importlib.import_module("scripts.migrate_task32_reliability_release")
    first = migration.apply()
    second = migration.apply()
    rollback = migration.rollback_plan()
    assert first["ok"] is True and second["ok"] is True
    assert first["schema_version"] >= "2026_07_27_038"
    assert rollback["automatic_schema_rollback_executed"] is False
    assert rollback["production_release_inferred"] is False


def test_miniprogram_only_exposes_public_reliability_status():
    source = (ROOT / "apps/miniprogram/services/api.js").read_text(encoding="utf-8")
    assert "getReliabilityPublicStatus" in source
    assert "runReliabilityDrill" not in source
    assert "updateReliabilityFeatureFlag" not in source
    assert "recoverReliableJob" not in source


def test_web_route_is_internal_and_has_no_release_approval_button():
    main = (ROOT / "apps/web/src/main.tsx").read_text(encoding="utf-8")
    page = (ROOT / "apps/web/src/pages/ReliabilityReleaseWorkbench.tsx").read_text(encoding="utf-8")
    assert 'href: "/reliability/release"' in main
    assert 'roles: ["admin", "researcher", "supervisor"]' in main
    assert "测试云阈值尚未冻结" in page
    assert "生产发布批准" not in page


def test_runbook_and_evidence_templates_exist_without_auto_signature():
    runbook = (ROOT / "docs/04_部署运维/任务三十二可靠性运行手册_20260720.md").read_text(encoding="utf-8")
    assert all(label in runbook for label in ["P0", "P1", "P2", "恢复时间", "事后复盘", "证据包"])
    assert "自动签字" not in runbook
