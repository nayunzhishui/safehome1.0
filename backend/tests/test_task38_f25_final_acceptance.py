import importlib.util
import json
from pathlib import Path
import subprocess
import zipfile

import pytest


ROOT = Path(__file__).resolve().parents[2]
POLICY = ROOT / "content" / "task37_38_final_acceptance_policy.json"
REGISTRY = ROOT / "config" / "task37_38_registry.json"
SCRIPT = ROOT / "backend" / "scripts" / "task38_f25_final_acceptance.py"
RUNNER = ROOT / "scripts" / "run_tasks_37_38.py"


def _module():
    spec = importlib.util.spec_from_file_location("task38_f25_final_acceptance", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def _runner_module():
    spec = importlib.util.spec_from_file_location("run_tasks_37_38", RUNNER)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def _execution_registry(tmp_path: Path, *, failing: bool = False) -> Path:
    policy = json.loads(POLICY.read_text(encoding="utf-8"))
    command = [
        "python",
        "-c",
        "raise SystemExit(3)" if failing else "print('verified')",
    ]
    path = tmp_path / "registry.json"
    path.write_text(
        json.dumps(
            {
                "schema": "safehome.tasks37_38.registry.v1",
                "policy": {
                    "allowed_command_executables": ["python"],
                    "forbidden_command_terms": ["git reset"],
                },
                "tasks": [
                    {
                        "id": "T37-P00",
                        "engineering_complete": True,
                        "dependencies": [],
                    },
                    {
                        "id": "T38-F25",
                        "engineering_complete": True,
                        "dependencies": ["T38-F24"],
                        "acceptance_categories": [
                            {
                                "id": item["id"],
                                "commands": [{"cwd": ".", "command": command}],
                                "artifact_paths": [],
                            }
                            for item in policy["automatic_acceptance_categories"]
                        ],
                    },
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    return path


def _clean_source_repo(tmp_path: Path) -> Path:
    path = tmp_path / "source"
    path.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=path, check=True)
    subprocess.run(
        ["git", "config", "user.email", "acceptance@example.invalid"],
        cwd=path,
        check=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Acceptance Test"],
        cwd=path,
        check=True,
    )
    (path / "source.txt").write_text("accepted\n", encoding="utf-8")
    subprocess.run(["git", "add", "source.txt"], cwd=path, check=True)
    subprocess.run(["git", "commit", "-qm", "fixture"], cwd=path, check=True)
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


def test_f25_executes_registered_commands_before_building_evidence(tmp_path):
    source_repo = _clean_source_repo(tmp_path)
    result = _module().verify(
        policy_path=POLICY,
        registry_path=_execution_registry(tmp_path),
        source_root=source_repo,
    )
    assert result["ok"] is True
    assert result["missing_artifacts"] == []
    assert len(result["artifact_set_sha256"]) == 64
    assert result["automatic_acceptance_complete"] is True
    assert len(result["executed_commands"]) == 1
    assert result["executed_commands"][0]["returncode"] == 0
    assert len(result["executed_commands"][0]["stdout_sha256"]) == 64
    assert {item["status"] for item in result["external_gates"]} == {
        "external_gate_pending"
    }
    assert result["production_migration_executed"] is False
    assert result["production_restore_executed"] is False
    assert result["real_device_acceptance_complete"] is False
    assert result["production_release_approved"] is False
    assert result["source_worktree_clean"] is True
    assert len(result["source_tree"]) == 40


def test_f25_rejects_dirty_source_worktree(tmp_path):
    source_repo = _clean_source_repo(tmp_path)
    (source_repo / "source.txt").write_text("uncommitted\n", encoding="utf-8")
    module = _module()
    with pytest.raises(module.AcceptanceError, match="源码工作区必须干净"):
        module.verify(
            policy_path=POLICY,
            registry_path=_execution_registry(tmp_path),
            source_root=source_repo,
        )


def test_f25_rejects_failed_registered_command_instead_of_trusting_a_receipt(tmp_path):
    module = _module()
    with pytest.raises(module.AcceptanceError, match="验收命令失败"):
        module.verify(
            policy_path=POLICY,
            registry_path=_execution_registry(tmp_path, failing=True),
            source_root=_clean_source_repo(tmp_path),
        )


def test_f25_rejects_policy_or_registry_drift_during_execution(tmp_path, monkeypatch):
    module = _module()
    registry_path = _execution_registry(tmp_path)
    original_execute = module._execute

    def execute_and_mutate(spec):
        outcome = original_execute(spec)
        registry_path.write_text(
            registry_path.read_text(encoding="utf-8") + "\n",
            encoding="utf-8",
        )
        return outcome

    monkeypatch.setattr(module, "_execute", execute_and_mutate)
    with pytest.raises(module.AcceptanceError, match="验收期间政策或注册表发生变化"):
        module.verify(
            policy_path=POLICY,
            registry_path=registry_path,
            source_root=_clean_source_repo(tmp_path),
        )


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
    assert "git archive" in builder
    assert "SourceMode=git_archive_head" in builder
    assert "SourceTree=" in builder
    assert '$ManifestFile = "TASK9_PACKAGE_MANIFEST.txt"' in builder
    assert "WorkingTreeDirty=" in builder
    assert "Join-Path $StagingRoot \"backend\\app.py\"" in builder
    assert "for p in ['backend/app.py','backend/database.py','backend/config.py']" not in builder
    assert "SourceMode=git_archive_head" in verifier
    assert "SourceTree=" in verifier
    assert "Source package content does not match the recorded Git commit." in verifier
    assert "$PackageLabel" in verifier and "$ManifestFile" in verifier


def test_cloudbase_verifier_rejects_tampered_archived_source(tmp_path):
    package = tmp_path / "package.zip"
    label = "SafeHome acceptance tamper test"
    manifest = "ACCEPTANCE_MANIFEST.txt"
    latest = "acceptance-latest.zip"
    subprocess.run(
        [
            "pwsh",
            "-NoProfile",
            "-File",
            str(ROOT / "scripts" / "build_task9_cloudbase_package.ps1"),
            "-OutputPath",
            str(package),
            "-PackageLabel",
            label,
            "-ManifestFile",
            manifest,
            "-LatestFile",
            latest,
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    with zipfile.ZipFile(package, "r") as archive:
        entries = {
            item.filename: archive.read(item.filename)
            for item in archive.infolist()
        }
    entries["backend/app.py"] += b"\n# tampered-source\n"
    with zipfile.ZipFile(package, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, payload in entries.items():
            archive.writestr(name, payload)
    package.with_suffix(".zip.sha256").unlink(missing_ok=True)
    result = subprocess.run(
        [
            "pwsh",
            "-NoProfile",
            "-File",
            str(ROOT / "scripts" / "verify_task9_cloudbase_package.ps1"),
            "-PackagePath",
            str(package),
            "-PackageLabel",
            label,
            "-ManifestFile",
            manifest,
            "-LatestFile",
            latest,
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    assert result.returncode != 0
    assert "Source package content does not match the recorded Git commit." in (
        result.stdout + result.stderr
    )


def test_f25_registry_invokes_trusted_verify_instead_of_plan_only():
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    f25 = next(item for item in registry["tasks"] if item["id"] == "T38-F25")
    commands = f25["verify_commands"]
    assert any(
        command[:3]
        == [
            "python",
            "backend/scripts/task38_f25_final_acceptance.py",
            "verify",
        ]
        for command in commands
    )
    assert len(f25["acceptance_categories"]) == 10
    assert f25["verify_includes_full_acceptance"] is True
    runner = _runner_module()
    assert runner.command_specs(f25, registry, full=True) == runner.command_specs(
        f25, registry, full=False
    )
