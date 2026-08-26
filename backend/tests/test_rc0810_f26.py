from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
import tarfile
import zipfile
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
BUILDER = ROOT / "scripts" / "build_rc0810_f26_rc.py"
REGISTRY = ROOT / "content" / "rc0810_release_candidate_registry.json"


def _load_builder():
    spec = importlib.util.spec_from_file_location("build_rc0810_f26_rc", BUILDER)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.path.insert(0, str(BUILDER.parent))
    try:
        spec.loader.exec_module(module)
    finally:
        sys.path.pop(0)
    return module


@pytest.fixture(scope="module")
def f26(tmp_path_factory):
    module = _load_builder()
    directory = tmp_path_factory.mktemp("f26-report")
    report_path = directory / "report.json"
    markdown_path = directory / "report.md"
    report = module.build_report(report_path, markdown_path=markdown_path)
    return module, report, report_path, markdown_path


def test_f26_clean_archives_bind_candidate_commit_and_hashes(f26):
    _, report, _, _ = f26
    candidate = report["candidate"]
    assert len(candidate["source_commit"]) == 40
    assert len(candidate["source_tree"]) == 40
    assert candidate["packaging_mode"] == "isolated_git_archive"
    assert candidate["direct_dirty_worktree_build_allowed"] is False
    for artifact in report["artifacts"].values():
        if artifact["status"] != "generated":
            continue
        path = ROOT / artifact["path"]
        assert path.is_file()
        assert hashlib.sha256(path.read_bytes()).hexdigest() == artifact["sha256"]


def test_f26_production_packages_exclude_internal_and_local_files(f26):
    _, report, _, _ = f26
    mini = ROOT / report["artifacts"]["miniprogram_zip"]["path"]
    with zipfile.ZipFile(mini) as archive:
        names = set(archive.namelist())
        assert not names & {
            "project.private.config.json",
            "pages/debug/index.js",
            "pages/integration-test/index.js",
            "pages/researcher-dashboard/index.js",
            "pages/therapeutic-assessment-quality/index.js",
        }
        project = json.loads(archive.read("project.config.json"))
        assert project["setting"]["urlCheck"] is True
        assert project["condition"]["miniprogram"]["list"] == []
    backend = ROOT / report["artifacts"]["backend_source_tar"]["path"]
    with tarfile.open(backend) as archive:
        lowered = [name.lower() for name in archive.getnames()]
    assert not any("/__pycache__/" in f"/{name}/" for name in lowered)
    assert not any(name.endswith((".sqlite", ".sqlite3", ".db", ".log", ".pyc")) for name in lowered)
    assert not any(Path(name).name in {".env", ".env.local", "project.private.config.json"} for name in lowered)


def test_f26_required_ci_and_security_gaps_force_no_go(f26):
    _, report, _, _ = f26
    assert report["required_ci"]
    assert all(item["required"] is True for item in report["required_ci"])
    assert all(item["status"] == "not_run_user_waiver" for item in report["required_ci"])
    assert report["security_evidence"]["current_status"] == "stale"
    assert report["artifacts"]["backend_image"]["digest"] is None
    assert report["release_decision"]["recommendation"] == "NO_GO"
    assert report["release_decision"]["production_gate_eligible"] is False


def test_f26_stale_evidence_is_not_promoted(f26):
    _, report, _, _ = f26
    assert report["security_evidence"]["source_tree"] != report["candidate"]["source_tree"]
    assert report["security_evidence"]["current_status"] == "stale"
    assert report["platform_evidence"]["production_approved"] is False
    assert report["platform_evidence"]["external_blockers"]


def test_f26_pr8_close_matrix_covers_every_registered_id_without_false_resolution(f26):
    _, report, _, _ = f26
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    expected = {pr_id for task in registry["tasks"] for pr_id in task["pr_ids"]}
    matrix = report["pr8_close_matrix"]
    assert {item["pr_id"] for item in matrix} == expected
    assert all(item["status"] in {"partial", "blocked_external", "blocked"} for item in matrix)
    assert all(item["owner"] and item["next_action"] for item in matrix)


def test_f26_release_drill_has_72h_observation_rollback_and_side_effect_ledger(f26):
    _, report, _, _ = f26
    drill = report["release_drill"]
    assert drill["execution_status"] == "planned_not_executed"
    assert drill["observation_window"]["hours"] >= 72
    assert drill["observation_window"]["owner_approved_alternative"] is None
    assert drill["rollback_order"] == ["stop_traffic", "code", "database", "content", "data_reconciliation"]
    assert {item["domain"] for item in report["irreversible_side_effect_ledger"]} == {
        "messages", "external_ai", "exports", "risk_tasks"
    }
    assert all(item["status"] == "planned_not_executed" for item in report["irreversible_side_effect_ledger"])


def test_f26_four_go_phase_separation_and_review_remain_truthful(f26):
    _, report, _, _ = f26
    assert set(report["four_go"]) == {"product", "platform", "engineering", "professional"}
    assert not any(item["approved"] for item in report["four_go"].values())
    assert report["wave_c_review"]["status"] == "review_pending_wave"
    assert report["wave_c_review"]["reviewer_id"] == "sartre_replacement"
    phases = report["phase_separation"]
    assert phases["engineering_materials_complete"] is True
    assert phases["rc_formed"] is False
    assert phases["platform_approved"] is False
    assert phases["released"] is False
    assert phases["stable_operation_verified"] is False


def test_f26_self_checks_reject_forged_go_ci_review_and_hash(f26):
    module, _, report_path, _ = f26
    checks = module.run_self_checks(report_path)
    assert checks == {
        "forged_release_go_rejected": True,
        "forged_required_ci_rejected": True,
        "forged_review_pass_rejected": True,
        "artifact_hash_drift_rejected": True,
        "missing_pr8_item_rejected": True,
        "short_observation_window_rejected": True,
    }

