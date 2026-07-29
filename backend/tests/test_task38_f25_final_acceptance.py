import importlib.util
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
POLICY = ROOT / "content" / "task37_38_final_acceptance_policy.json"
REGISTRY = ROOT / "config" / "task37_38_registry.json"
SCRIPT = ROOT / "backend" / "scripts" / "task38_f25_final_acceptance.py"


def _module():
    spec = importlib.util.spec_from_file_location("task38_f25_final_acceptance", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def _receipt(tmp_path: Path) -> Path:
    policy = json.loads(POLICY.read_text(encoding="utf-8"))
    path = tmp_path / "receipt.json"
    path.write_text(
        json.dumps(
            {
                "schema": "safehome.tasks37-38.acceptance-receipt.v1",
                "results": [
                    {
                        "id": item["id"],
                        "status": "passed",
                        "command": ["python", "-m", "pytest", "-q"],
                        "summary": "sanitized local engineering check passed",
                        "artifact_paths": [],
                    }
                    for item in policy["automatic_acceptance_categories"]
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    return path


def test_f25_policy_covers_all_automatic_and_external_gate_categories():
    policy = json.loads(POLICY.read_text(encoding="utf-8"))
    assert [item["id"] for item in policy["automatic_acceptance_categories"]] == [
        "backend",
        "schema_migration_recovery_rollback",
        "shared_api",
        "web_miniprogram",
        "permission_scope_audit",
        "idempotency_concurrency_withdrawal_recovery",
        "content_boundary",
        "accessibility_four_viewports",
        "full_regression",
        "machine_registry",
    ]
    assert len(policy["external_gates"]) == 6
    assert {item["status"] for item in policy["external_gates"]} == {
        "external_gate_pending"
    }
    assert len(policy["completion_definitions"]) == 5


def test_f25_registry_marks_all_engineering_tasks_complete_after_acceptance():
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    pending = [
        item["id"]
        for item in registry["tasks"]
        if item.get("engineering_complete") is not True
    ]
    assert pending == []
    f25 = next(item for item in registry["tasks"] if item["id"] == "T38-F25")
    assert f25["status"] == (
        "engineering_complete_full_automatic_acceptance_passed_external_gates_pending"
    )


def test_f25_builds_sanitized_local_evidence_without_signing_external_gates(tmp_path):
    result = _module().build(_receipt(tmp_path))
    assert result["ok"] is True
    assert result["missing_artifacts"] == []
    assert len(result["artifact_set_sha256"]) == 64
    assert result["automatic_acceptance_complete"] is True
    assert {item["status"] for item in result["external_gates"]} == {
        "external_gate_pending"
    }
    assert result["production_migration_executed"] is False
    assert result["production_restore_executed"] is False
    assert result["real_device_acceptance_complete"] is False
    assert result["production_release_approved"] is False


def test_f25_rejects_missing_failed_or_sensitive_acceptance_receipts(tmp_path):
    module = _module()
    receipt = json.loads(_receipt(tmp_path).read_text(encoding="utf-8"))
    receipt["results"][0]["status"] = "failed"
    failed = tmp_path / "failed.json"
    failed.write_text(json.dumps(receipt), encoding="utf-8")
    with pytest.raises(module.AcceptanceError, match="自动验收未通过"):
        module.build(failed)

    receipt["results"][0]["status"] = "passed"
    receipt["results"][0]["raw_text"] = "participant material"
    sensitive = tmp_path / "sensitive.json"
    sensitive.write_text(json.dumps(receipt), encoding="utf-8")
    with pytest.raises(module.AcceptanceError, match="未允许字段"):
        module.build(sensitive)


def test_f25_plan_and_rollback_never_mutate_production():
    module = _module()
    plan = module.plan()
    rollback = module.rollback_plan()
    assert plan["ok"] is True
    assert plan["production_mutation_executed"] is False
    assert plan["production_release_approved"] is False
    assert rollback["ok"] is True
    assert rollback["rollback_executed"] is False
    assert rollback["production_mutation_executed"] is False


def test_f25_visual_and_cloudbase_delivery_support_final_acceptance():
    visual = (ROOT / "scripts" / "audit_task23_visual_system.mjs").read_text(
        encoding="utf-8"
    )
    builder = (ROOT / "scripts" / "build_task9_cloudbase_package.ps1").read_text(
        encoding="utf-8"
    )
    verifier = (
        ROOT / "scripts" / "verify_task9_cloudbase_package.ps1"
    ).read_text(encoding="utf-8")
    assert "const FONT_SCALES = [1, 2]" in visual
    assert "viewport-${width}-font-${fontScale * 100}.png" in visual
    assert 'element.style.fontSize = `${fontSize * scale}px`' in visual
    assert '$PackageLabel = "SafeHome task 9 CloudBase package"' in builder
    assert '$ManifestFile = "TASK9_PACKAGE_MANIFEST.txt"' in builder
    assert "WorkingTreeDirty=" in builder
    assert "WorkingTreeStatus:" not in builder
    assert "$PackageLabel" in verifier and "$ManifestFile" in verifier
