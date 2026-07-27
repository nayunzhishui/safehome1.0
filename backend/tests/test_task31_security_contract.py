import importlib
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"


def test_security_registry_generator_and_content_validator_pass():
    assert subprocess.run([sys.executable, "backend/scripts/generate_task31_security_registry.py", "--check"], cwd=ROOT).returncode == 0
    assert subprocess.run([sys.executable, "backend/scripts/validate_content.py"], cwd=ROOT).returncode == 0


def test_local_security_scanner_is_redacted_and_hard_checks_pass():
    sys.path.insert(0, str(BACKEND))
    scanner = importlib.import_module("scripts.scan_task31_security")
    result = scanner.run_scan(ROOT)
    assert result["hard_checks_passed"] is True
    assert result["blockers"] == [] and result["secret_values_returned"] is False
    assert next(item for item in result["checks"] if item["id"] == "network_dependency_advisories")["status"] == "evidence_pending"


def test_machine_contract_registers_security_roles_and_privacy_verification():
    contract = json.loads((ROOT / "shared/contracts/api-contract.json").read_text(encoding="utf-8"))
    by_key = {(item["method"], item["path"]): item for item in contract["endpoints"]}
    assert by_key[("GET", "/api/security/public-status")]["access"]["roles"] == ["public"]
    assert by_key[("GET", "/api/security/workbench")]["access"]["roles"] == ["researcher", "supervisor", "admin"]
    assert by_key[("POST", "/api/security/scans")]["access"]["roles"] == ["admin"]
    assert by_key[("PATCH", "/api/security/accounts/<user_id>/status")]["access"]["roles"] == ["admin"]
    assert by_key[("GET", "/api/privacy/admin/requests/<request_id>/verification")]["access"]["roles"] == ["supervisor", "admin"]


def test_schema_migration_and_rollback_plan_are_idempotent(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "task31-migrate.sqlite3"))
    sys.path.insert(0, str(BACKEND))
    for name in ["config", "database", "models"]:
        sys.modules.pop(name, None)
    migration = importlib.import_module("scripts.migrate_task31_security_controls")
    first = migration.apply()
    second = migration.apply()
    rollback = migration.rollback_plan()
    assert first["ok"] is True and second["ok"] is True
    assert first["schema_version"] == "2026_07_27_032"
    assert first["temporary_showcase_exception_changed"] is False
    assert rollback["automatic_rollback_executed"] is False
    assert rollback["formal_security_acceptance_inferred"] is False


def test_miniprogram_only_exposes_public_security_status():
    source = (ROOT / "apps/miniprogram/services/api.js").read_text(encoding="utf-8")
    assert "getSecurityPublicStatus" in source
    assert "runSecurityScan" not in source
    assert "updateAccountStatus" not in source
    assert "resolveSecurityEvent" not in source


def test_ai_security_boundary_has_no_real_provider_or_write_tools():
    governance = json.loads((ROOT / "content/ai_qa_governance.json").read_text(encoding="utf-8"))
    registry = json.loads((ROOT / "content/security_privacy_abuse_registry.json").read_text(encoding="utf-8"))
    config_source = (ROOT / "backend/config.py").read_text(encoding="utf-8")
    assert governance["decisions"]["provider"]["status"] == "owner_security_review_required"
    assert "AI_QA_ENABLED 必须保持关闭" in config_source
    assert {item["id"] for item in registry["ai_threats"]} >= {"prompt_injection", "knowledge_poisoning", "cross_user_retrieval", "provider_retention", "tool_abuse", "cost_exhaustion", "unauthorized_action"}


def test_web_route_is_internal_and_server_remains_authority():
    main = (ROOT / "apps/web/src/main.tsx").read_text(encoding="utf-8")
    page = (ROOT / "apps/web/src/pages/SecurityPrivacyWorkbench.tsx").read_text(encoding="utf-8")
    route = (ROOT / "backend/routes/security_controls.py").read_text(encoding="utf-8")
    assert 'href: "/security/privacy"' in main
    assert 'roles: ["admin", "researcher", "supervisor"]' in main
    assert "临时展示越权继续保留" in page
    assert '_actor("admin")' in route and '_actor("researcher", "supervisor", "admin")' in route
