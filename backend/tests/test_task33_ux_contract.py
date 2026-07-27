import importlib
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"


def test_registry_generator_content_validator_and_experience_audit_pass():
    assert subprocess.run([sys.executable, "backend/scripts/generate_task33_ux_registry.py", "--check"], cwd=ROOT).returncode == 0
    assert subprocess.run([sys.executable, "backend/scripts/validate_content.py"], cwd=ROOT).returncode == 0
    assert subprocess.run([sys.executable, "backend/scripts/audit_task33_experience.py"], cwd=ROOT).returncode == 0


def test_registry_covers_all_pages_routes_states_roles_and_fixed_information_architecture():
    registry = json.loads((ROOT / "content/ux_experience_registry.json").read_text(encoding="utf-8"))
    app = json.loads((ROOT / "apps/miniprogram/app.json").read_text(encoding="utf-8"))
    mini = [item for item in registry["pages"] if item["platform"] == "miniprogram"]
    web = [item for item in registry["pages"] if item["platform"] == "web"]
    assert {item["path"] for item in mini} == set(app["pages"])
    assert len(mini) == len(app["pages"]) and len(web) >= 35
    assert registry["participant_information_architecture"] == ["记录", "练习", "了解自己", "人工支持"]
    assert registry["researcher_information_architecture"] == ["待处理", "参与者", "内容", "研究/导出", "系统状态"]
    assert all(set(item) >= {"goal", "primary_action", "data_source", "states", "roles", "sensitivity", "owner"} for item in registry["pages"])


def test_home_layout_and_researcher_navigation_preserve_product_decisions():
    home = (ROOT / "apps/miniprogram/pages/home/index.wxml").read_text(encoding="utf-8")
    main = (ROOT / "apps/web/src/main.tsx").read_text(encoding="utf-8")
    assert home.index("core-actions") < home.index("today-step-entry") < home.index('<section-title title="三步开始"')
    assert all(f'label: "{label}"' in main for label in ["待处理", "参与者", "内容", "研究/导出", "系统状态"])
    assert 'href: "/system/experience"' in main
    assert "showcaseEnabled" in main


def test_schema_migration_and_rollback_are_idempotent_and_non_destructive(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "task33-migrate.sqlite3"))
    sys.path.insert(0, str(BACKEND))
    for name in ["config", "database", "models"]:
        sys.modules.pop(name, None)
    migration = importlib.import_module("scripts.migrate_task33_ux_governance")
    first = migration.apply()
    second = migration.apply()
    rollback = migration.rollback_plan()
    assert first["schema_version"] == "2026_07_27_038"
    assert second["ok"] is True
    assert rollback["automatic_schema_rollback_executed"] is False
    assert rollback["retain_audit_and_evidence"] is True
    assert rollback["release_approval_inferred"] is False


def test_machine_contract_roles_and_miniprogram_public_boundary():
    contract = json.loads((ROOT / "shared/contracts/api-contract.json").read_text(encoding="utf-8"))
    by_key = {(item["method"], item["path"]): item for item in contract["endpoints"]}
    assert by_key[("GET", "/api/ux-governance/public-status")]["access"]["roles"] == ["public"]
    assert by_key[("GET", "/api/ux-governance/workbench")]["access"]["roles"] == ["researcher", "supervisor", "admin"]
    assert by_key[("POST", "/api/ux-governance/audits")]["access"]["roles"] == ["admin"]
    assert by_key[("POST", "/api/ux-governance/evidence-packages")]["access"]["roles"] == ["supervisor", "admin"]
    mini = (ROOT / "apps/miniprogram/services/api.js").read_text(encoding="utf-8")
    assert "getUXGovernancePublicStatus" in mini
    assert "createUXEvidencePackage" not in mini and "createUXAuditRun" not in mini


def test_form_resilience_has_timestamp_restore_leave_prompt_slow_state_and_idempotency():
    utility = (ROOT / "apps/miniprogram/utils/resilientForm.js").read_text(encoding="utf-8")
    pages = "\n".join((ROOT / path).read_text(encoding="utf-8") for path in [
        "apps/miniprogram/pages/diary-form/index.js", "apps/miniprogram/pages/goal-setting/index.js",
        "apps/miniprogram/pages/supervision/index.js", "apps/miniprogram/pages/assessment-detail/index.js",
        "apps/miniprogram/pages/checkin/index.js", "apps/miniprogram/pages/relationship-growth/index.js",
    ])
    web_hook = (ROOT / "apps/web/src/hooks/useResilientDraft.ts").read_text(encoding="utf-8")
    web_forms = "\n".join((ROOT / path).read_text(encoding="utf-8") for path in [
        "apps/web/src/pages/ReadFeedbackIntegrationPages.tsx", "apps/web/src/pages/RelationshipAssessmentPage.tsx",
    ])
    assert all(value in utility for value in ["savedAt", "enableAlertBeforeUnload", "restore", "clientSubmissionId"])
    assert pages.count("client_submission_id") >= 5 and "slowSaving" in pages
    assert all(value in web_hook for value in ["savedAt", "beforeunload", "clientSubmissionId", "localStorage"])
    assert web_forms.count("client_submission_id") >= 3 and web_forms.count("slowSubmitting") >= 6
