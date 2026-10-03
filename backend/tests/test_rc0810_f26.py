from __future__ import annotations

import copy
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
F26_REPORT = ROOT / "docs" / "02_专项进度与验收" / "rc0810_f26_final_rc.json"
WAVE_C_DECISION = Path("docs/02_专项进度与验收/rc0810_wave_c_review_decision.json")



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


def test_f26_backend_source_archive_covers_docker_copy_inputs():
    module = _load_builder()
    for line in (ROOT / "Dockerfile").read_text(encoding="utf-8").splitlines():
        if not line.startswith("COPY "):
            continue
        for source in line.split()[1:-1]:
            assert any(
                source == context or source.startswith(context + "/")
                for context in module.BACKEND_SOURCE_PATHS
            ), source


def test_f26_missing_ci_is_not_automatically_a_user_waiver():
    module = _load_builder()
    checks = module._required_ci({"automatic_acceptance_categories": [
        {"id": "backend", "title": "后端全量回归", "required": True},
    ]})
    assert checks[0]["status"] == "not_run"
    assert checks[0]["evidence"] is None
    assert checks[0]["release_effect"] == "blocking"


@pytest.fixture(scope="module")
def f26(tmp_path_factory):
    module = _load_builder()
    directory = tmp_path_factory.mktemp("f26-report")
    report_path = directory / "report.json"
    markdown_path = directory / "report.md"
    frozen_commit = json.loads(F26_REPORT.read_text(encoding="utf-8"))["candidate"]["source_commit"]
    report = module.build_report(report_path, markdown_path=markdown_path, commit=frozen_commit)
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
    assert all(item["status"] == "not_run" for item in report["required_ci"])
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


def test_f26_unbound_image_does_not_claim_daemon_unavailable(f26):
    _, report, _, _ = f26
    assert report["artifacts"]["backend_image"] == {
        "status": "missing_blocking", "digest": None,
        "reason": "current_registered_image_digest_not_bound",
    }
    assert "No current backend image" not in " ".join(report["known_issues"])


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


def test_f26_review_packet_is_prebound_and_rejects_self_reported_or_changed_identity(f26, monkeypatch):
    module, report, _, _ = f26
    # Contract fixture only: no persisted packet and no review approval.
    bound = copy.deepcopy(report)
    review = bound["wave_c_review"]
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    tree = subprocess.check_output(["git", "rev-parse", "HEAD^{tree}"], cwd=ROOT, text=True).strip()
    packet_path = ROOT / ".codex_tmp/contract-fixture/wave-C-f26.json"
    state_path = ROOT / ".codex_tmp/contract-fixture/state.json"
    pointer = {"run_id": "contract-fixture", "state_sha256": "a" * 64}
    monkeypatch.setattr(module, "_expected_wave_c_packet_path", lambda: (packet_path, pointer, {}, state_path))
    packet = {
        "schema": "safehome.rc0810.wave-review-packet.v2", "wave": "C",
        "packet_nonce": "synthetic-contract-fixture", "reviewer_id": "sartre_replacement",
        "base_checkpoint": {"commit": review["base_commit"]},
        "review_head": {"commit": head, "source_tree": tree},
        "release_candidate": {"commit": bound["candidate"]["source_commit"], "source_tree": bound["candidate"]["source_tree"]},
    }
    digest = hashlib.sha256(json.dumps(packet, sort_keys=True).encode()).hexdigest()
    review.update({
        "packet_path": packet_path.relative_to(ROOT).as_posix(), "packet_sha256": digest,
        "packet_nonce": packet["packet_nonce"], "packet_head": head, "packet_source_tree": tree,
        "harness_binding": {**pointer, "state_path": state_path.relative_to(ROOT).as_posix(),
                            "fixed_reviewer_id": "sartre_replacement", "last_review_pass_checkpoint": "RC0810-F21:verified"},
    })
    def errors(candidate, path=packet_path):
        return module._packet_payload_errors(candidate, packet, actual_sha256=digest, packet_path=path)
    assert errors(bound) == []
    assert errors(bound, ROOT / ".codex_tmp/self-reported/wave-C-f26.json")
    assert module._bound_review_packet_errors(bound) == ["review_packet_missing_or_self_reported_path"]
    for key, value in [("packet_sha256", "0" * 64), ("packet_nonce", "forged-nonce-value"), ("packet_head", "0" * 40)]:
        changed = copy.deepcopy(bound)
        changed["wave_c_review"][key] = value
        assert errors(changed)
    for key, value in [("source_commit", "0" * 40), ("source_tree", "0" * 40)]:
        changed = copy.deepcopy(bound)
        changed["candidate"][key] = value
        assert errors(changed)
    assert module._review_decision_errors(
        bound, {"path": ".codex_tmp/self-reported-decision.json", "sha256": "0" * 64},
    ) == ["review_decision_path_invalid"]


def test_f26_resolves_repository_relative_review_decision_path(f26):
    module, _, _, _ = f26
    assert module._resolve_repository_path(WAVE_C_DECISION) == ROOT / WAVE_C_DECISION


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


def test_f26_self_checks_cover_recorded_review_pass(f26):
    module, _, _, _ = f26
    assert all(module.run_self_checks(F26_REPORT).values())


def test_f26_review_pass_closes_only_review_pending_state(f26):
    module, pending_report, _, _ = f26
    report = copy.deepcopy(pending_report)
    remaining_blockers = set(report["release_decision"]["blocking_reasons"]) - {
        module.WAVE_C_PENDING_BLOCKER
    }
    report["wave_c_review"]["status"] = "review_pass"
    module._complete_wave_c_review_state(report)

    assert module._review_state_errors(report) == []
    assert set(report["release_decision"]["blocking_reasons"]) == remaining_blockers
    assert next(item for item in report["subtasks"] if item["id"] == "F26.8")["status"] == "review_pass"
    rendered = module.render_markdown(report)
    assert "波次 C 固定 reviewer 已审查通过" in rendered
    assert "波次 C 先由固定 reviewer" not in rendered
    assert module.WAVE_C_PENDING_BLOCKER not in rendered
