import hashlib
import json
import importlib.util
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATH = ROOT / "content" / "rc0810_release_candidate_registry.json"
BASELINE_PATH = (
    ROOT
    / "docs"
    / "02_专项进度与验收"
    / "rc0810_f10a_ci_failure_baseline.json"
)
VERIFY_PATH = ROOT / "scripts" / "verify_rc0810_f10_baseline.py"
EVIDENCE_PATH = (
    ROOT
    / "docs"
    / "02_专项进度与验收"
    / "rc0810_f10a_github_actions_evidence.json"
)


def _baseline() -> dict:
    return json.loads(BASELINE_PATH.read_text(encoding="utf-8"))


def _runner_module():
    spec = importlib.util.spec_from_file_location("rc0810_runner_f10_test", ROOT / "scripts" / "run_rc0810.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_f10a_baseline_binds_current_main_run_and_source_tree():
    baseline = _baseline()

    assert baseline["schema"] == "safehome.rc0810.ci-failure-baseline.v1"
    assert baseline["task"] == "RC0810-F10-A"
    assert baseline["status"] == "frozen_failure_baseline"
    assert baseline["release_gate_eligible"] is False
    assert baseline["source"]["head"] == (
        "98fca029f3f97e13d7e787cd40cb939465a992d4"
    )
    assert baseline["source"]["origin_main"] == baseline["source"]["head"]
    assert baseline["source"]["source_tree"] == (
        "dd2b037d84ede36bb1b054ceb536598692a85d6c"
    )
    assert baseline["github_actions"]["authoritative_run"]["database_id"] == 31325141640
    assert baseline["github_actions"]["authoritative_run"]["head_sha"] == baseline["source"]["head"]
    assert baseline["github_actions"]["authoritative_run"]["conclusion"] == "failure"


def test_f10_phases_cannot_mark_unexecuted_subtasks_verified():
    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    units = {unit["id"]: unit for unit in registry["execution_units"]}

    assert units["RC0810-F10-A"]["subtasks"] == ["F10.1", "F10.8"]
    assert len(units["RC0810-F10-A"]["allowed_files"]) == 12
    assert (
        "docs/02_专项进度与验收/rc0810_f10a_github_actions_evidence.json"
        in units["RC0810-F10-A"]["allowed_files"]
    )
    assert set(units["RC0810-F10-A"]["inherited_shared_files"]) == {
        "docs/00_当前事实基准/Claude计划模式.md",
        "docs/00_当前事实基准/开发日志.md",
        "docs/00_当前事实基准/开发说明.md",
        "docs/00_当前事实基准/当前进度交接.md",
    }
    assert units["RC0810-F10-B"]["subtasks"] == [
        "F10.2",
        "F10.3",
        "F10.4",
        "F10.5",
        "F10.6",
        "F10.7",
        "F10.8",
        "F10.9",
    ]


def test_f10a_baseline_classifies_every_failure_without_changing_tests():
    baseline = _baseline()
    failures = baseline["github_actions"]["authoritative_run"]["failures"]

    assert len(failures) == 9
    assert len({failure["id"] for failure in failures}) == 9
    assert all(failure["test_nodeid"] for failure in failures)
    assert all(failure["root_cause_group"] for failure in failures)
    assert all(failure["disposition"] for failure in failures)
    assert {failure["classification"] for failure in failures} <= {
        "true_defect",
        "contract_drift",
        "snapshot_drift",
        "environment_gap",
    }
    assert baseline["classification_counts"] == {
        "true_defect": 5,
        "contract_drift": 3,
        "snapshot_drift": 1,
        "environment_gap": 0,
    }
    pending_decisions = {
        failure["root_cause_group"]
        for failure in failures
        if failure["disposition"] == "decision_required_in_f10_2"
    }
    assert pending_decisions == {
        "bootstrap_participant_policy",
        "participant_ai_client_policy",
        "production_ai_policy",
    }


def test_f10a_verifier_rejects_treating_fail_fast_run_as_release_gate():
    baseline = _baseline()
    run = baseline["github_actions"]["authoritative_run"]

    assert run["summary"] == {
        "failed_tests": 9,
        "passed_tests": 988,
        "warnings": 1,
        "executed_workflow_steps": 9,
        "skipped_workflow_steps": 11,
    }
    assert baseline["workflow_findings"]["single_job_fail_fast"] is True
    assert baseline["workflow_findings"]["independent_required_jobs"] is False
    assert baseline["workflow_findings"]["f10_b_required"] is True

    completed = subprocess.run(
        [sys.executable, str(VERIFY_PATH), "--baseline", str(BASELINE_PATH)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    result = json.loads(completed.stdout)
    assert result["status"] == "frozen_failure_baseline"
    assert result["release_gate_eligible"] is False
    assert result["failure_count"] == 9


def test_f10a_verifier_recomputes_actions_facts_from_frozen_raw_evidence(tmp_path):
    baseline = _baseline()
    evidence = json.loads(EVIDENCE_PATH.read_text(encoding="utf-8"))

    assert baseline["github_actions"]["evidence_artifact"]["path"] == (
        "docs/02_专项进度与验收/rc0810_f10a_github_actions_evidence.json"
    )
    assert evidence["run"]["id"] == 31325141640
    assert evidence["job"]["id"] == 93274187305

    evidence["job"]["steps"][10]["conclusion"] = "success"
    tampered = tmp_path / "tampered-actions-evidence.json"
    tampered.write_text(json.dumps(evidence), encoding="utf-8")
    completed = subprocess.run(
        [
            sys.executable,
            str(VERIFY_PATH),
            "--baseline",
            str(BASELINE_PATH),
            "--evidence",
            str(tampered),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode != 0
    assert "workflow step counts do not match raw Actions evidence" in completed.stdout


def test_f10a_full_actions_log_is_runtime_only_and_hash_verified(tmp_path):
    evidence = json.loads(EVIDENCE_PATH.read_text(encoding="utf-8"))
    failed_log = evidence["failed_log"]

    assert "payload" not in failed_log
    assert failed_log["encoding"] == "runtime_gzip"
    runtime_path = ROOT / failed_log["runtime_artifact"]["path"]
    assert failed_log["runtime_artifact"]["committed"] is False
    tracked = subprocess.run(
        ["git", "ls-files", "--error-unmatch", failed_log["runtime_artifact"]["path"]],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert tracked.returncode != 0

    completed = subprocess.run(
        [sys.executable, str(VERIFY_PATH)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stdout
    result = json.loads(completed.stdout)
    assert result["runtime_log_verified"] is runtime_path.is_file()
    assert result["release_gate_eligible"] is False

    clean_evidence = json.loads(EVIDENCE_PATH.read_text(encoding="utf-8"))
    clean_evidence["failed_log"]["runtime_artifact"]["path"] = (
        ".codex_tmp/rc0810/clean-checkout/github-actions-failed.log.gz"
    )
    clean_evidence_path = tmp_path / "clean-actions-evidence.json"
    clean_evidence_path.write_text(json.dumps(clean_evidence), encoding="utf-8")
    clean_baseline = _baseline()
    clean_baseline["github_actions"]["evidence_artifact"]["sha256"] = (
        hashlib.sha256(clean_evidence_path.read_bytes()).hexdigest()
    )
    clean_baseline_path = tmp_path / "clean-baseline.json"
    clean_baseline_path.write_text(json.dumps(clean_baseline), encoding="utf-8")

    clean_completed = subprocess.run(
        [
            sys.executable,
            str(VERIFY_PATH),
            "--baseline",
            str(clean_baseline_path),
            "--evidence",
            str(clean_evidence_path),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert clean_completed.returncode == 0, clean_completed.stdout
    clean_result = json.loads(clean_completed.stdout)
    assert clean_result["status"] == "frozen_failure_baseline"
    assert clean_result["runtime_log_verified"] is False
    assert clean_result["release_gate_eligible"] is False


def test_concurrent_overlay_is_explicit_and_does_not_hide_task_delta():
    runner = _runner_module()
    task_state = {
        "start_snapshot": {
            "source_manifest": {
                "design/concurrent.json": "old-concurrent",
                "scripts/task.py": "old-task",
            }
        }
    }
    current = {
        "git": {
            "source_manifest": {
                "design/concurrent.json": "new-concurrent",
                "scripts/task.py": "new-task",
            }
        }
    }

    records = runner._acknowledge_concurrent_overlay(
        task_state,
        current,
        ["design/concurrent.json"],
        "parallel UI task",
        ["scripts/task.py"],
        [],
    )

    assert records[0]["start_blob"] == "old-concurrent"
    assert records[0]["inherited_blob"] == "new-concurrent"
    assert task_state["start_snapshot"]["source_manifest"] == {
        "design/concurrent.json": "new-concurrent",
        "scripts/task.py": "old-task",
    }
    assert task_state["concurrent_inherited_overlay_sha256"]

    try:
        runner._acknowledge_concurrent_overlay(
            task_state,
            current,
            ["scripts/task.py"],
            "must not hide task file",
            ["scripts/task.py"],
            [],
        )
    except runner.HarnessError as exc:
        assert "任务专属文件" in str(exc)
    else:
        raise AssertionError("task-owned files must not be hidden as overlays")
