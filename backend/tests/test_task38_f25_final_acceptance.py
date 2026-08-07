import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
REGISTRY = ROOT / "content" / "task37_38_final_acceptance_policy.json"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))


def _runner_module():
    path = ROOT / "backend" / "scripts" / "task38_f25_final_acceptance.py"
    spec = importlib.util.spec_from_file_location("task38_f25_final_acceptance", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _run_package_builder(*, package: Path, label: str, manifest: str, latest: str):
    result = subprocess.run(
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
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode != 0:
        raise AssertionError(
            "CloudBase package builder failed.\n"
            f"returncode={result.returncode}\n"
            f"stdout:\n{result.stdout}\n"
            f"stderr:\n{result.stderr}"
        )
    return result


def test_f25_registry_exists_and_is_conservative():
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    assert registry["schema"] == "safehome.task37_38_final_acceptance.v1"
    assert registry["production_release_approved"] is False
    assert registry["cloud_acceptance_completed"] is False
    assert registry["real_device_acceptance_completed"] is False
    assert registry["human_acceptance_completed"] is False
    assert registry["research_release_completed"] is False
    assert registry["source_binding_required"] is True
    assert registry["source_repository_clean_required"] is True
    assert registry["source_commit_reachable_required"] is True
    assert registry["source_tree_required"] is True
    assert registry["post_verify_source_clean_required"] is True
    assert registry["production_dual_control_required"] is True
    assert registry["required_external_approvals"] == [
        "human_acceptance",
        "ethics_legal_privacy_security",
        "cloudbase_mysql_migration",
        "real_device_acceptance",
        "production_owner_approval",
        "production_dual_control",
    ]


def test_f25_runner_preserves_source_binding_and_cleanliness_guards():
    runner_path = ROOT / "backend" / "scripts" / "task38_f25_final_acceptance.py"
    source = runner_path.read_text(encoding="utf-8")
    assert "source_repository_clean" in source
    assert "source_commit_reachable" in source
    assert "source_tree" in source
    assert "source_commit" in source
    assert "source_clean_after_verify" in source
    assert "git diff --quiet" in source
    assert "git diff --cached --quiet" in source
    assert "git ls-files --others --exclude-standard" in source
    assert "git cat-file -e" in source
    assert "git rev-parse" in source


def test_f25_runner_preserves_approval_boundaries():
    runner = _runner_module()
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    summary = runner.external_gates_summary(registry)
    assert summary["production_release_approved"] is False
    assert summary["human_acceptance_completed"] is False
    assert summary["cloud_acceptance_completed"] is False
    assert summary["real_device_acceptance_completed"] is False
    assert summary["research_release_completed"] is False
    assert "engineering_complete_is_not_production_release" in summary["boundary_notice"]


def test_f25_builder_and_verifier_preserve_source_proof_contract():
    builder = (ROOT / "scripts" / "build_task9_cloudbase_package.ps1").read_text(encoding="utf-8")
    verifier = (
        ROOT / "scripts" / "verify_task9_cloudbase_package.ps1"
    ).read_text(encoding="utf-8")
    visual = (ROOT / "scripts" / "task38_visual_acceptance.mjs").read_text(encoding="utf-8")
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
    _run_package_builder(package=package, label=label, manifest=manifest, latest=latest)
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


def test_f25_acceptance_config_supports_optional_cloud_and_visual_evidence(tmp_path, monkeypatch):
    runner = _runner_module()
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    monkeypatch.setenv("TASK38_CLOUD_PACKAGE", str(tmp_path / "cloud.zip"))
    monkeypatch.setenv("TASK38_CLOUD_PUBLIC_URL", "https://example.test/safehome")
    monkeypatch.setenv("TASK38_CLOUD_SERVICE_NAME", "safehome-test")
    monkeypatch.setenv("TASK38_MYSQL_DSN", "mysql+pymysql://user:pass@example.test/safehome")
    monkeypatch.setenv("TASK38_DB_SOURCE", "sqlite")
    monkeypatch.setenv("TASK38_DB_TARGET", "mysql")
    monkeypatch.setenv("TASK38_DB_MIGRATION_MODE", "dry-run")
    monkeypatch.setenv("TASK38_DB_MIGRATION_SALT", "task38-test-salt")
    monkeypatch.setenv("TASK38_DB_BACKUP_PATH", str(tmp_path / "backup.sqlite3"))
    monkeypatch.setenv("TASK38_VISUAL_BASE_URL", "https://example.test/safehome")
    monkeypatch.setenv("TASK38_VISUAL_TARGETS", "student,admin")
    monkeypatch.setenv("TASK38_VISUAL_VIEWPORTS", "390x844,1440x900")

    specs = runner.command_specs(registry["tasks"][-1], registry, full=True)
    commands = [spec["command"] for spec in specs]
    assert any("verify_task9_cloudbase_package.ps1" in " ".join(command) for command in commands)
    assert any("migrate_database.py" in " ".join(command) for command in commands)
    assert any("task38_visual_acceptance.mjs" in " ".join(command) for command in commands)


def test_f25_artifact_hash_utility_matches_sha256(tmp_path):
    runner = _runner_module()
    target = tmp_path / "artifact.bin"
    target.write_bytes(b"safehome-f25")
    assert runner.sha256_file(target) == hashlib.sha256(b"safehome-f25").hexdigest()


def test_f25_source_clean_guard_fails_on_dirty_repo(tmp_path, monkeypatch):
    runner = _runner_module()
    target = tmp_path / "dirty.txt"
    target.write_text("dirty", encoding="utf-8")
    monkeypatch.setattr(runner, "ROOT", tmp_path)

    def fake_run_git(*args):
        if args[:2] == ("rev-parse", "HEAD"):
            return "a" * 40
        if args[:2] == ("rev-parse", "HEAD^{tree}"):
            return "b" * 40
        if args[:2] == ("branch", "--show-current"):
            return "test"
        if args[:2] == ("ls-files", "--others"):
            return "dirty.txt"
        if args[:2] == ("diff", "--quiet") or args[:2] == ("diff", "--cached"):
            return ""
        if args[:2] == ("cat-file", "-e"):
            return ""
        return ""

    monkeypatch.setattr(runner, "run_git", fake_run_git)
    evidence = runner.source_repository_evidence()
    assert evidence["clean"] is False
    assert evidence["untracked_files"] == ["dirty.txt"]


def test_f25_source_tree_binding_matches_head(monkeypatch):
    runner = _runner_module()
    monkeypatch.setattr(runner, "run_git", lambda *args: "f" * 40 if args[:2] == ("rev-parse", "HEAD") else "e" * 40)
    evidence = runner.source_repository_evidence()
    assert evidence["head"] == "f" * 40
    assert evidence["source_tree"] == "e" * 40


def test_f25_production_dual_control_stays_external_gate():
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    assert "production_dual_control" in registry["required_external_approvals"]
    assert registry["production_dual_control_required"] is True
    assert registry["production_release_approved"] is False
