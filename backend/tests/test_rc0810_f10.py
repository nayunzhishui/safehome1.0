import hashlib
import json
import importlib.util
import os
import re
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
DECISIONS_PATH = ROOT / "config" / "rc0810" / "ci_contract_decisions.json"
CHECK_WORKFLOW_PATH = ROOT / ".github" / "workflows" / "check.yml"
CONTROLLED_FAILURE_PATH = ROOT / "scripts" / "ci_fail_job.py"
RELEASE_GATE_PATH = ROOT / "scripts" / "verify_ci_release_gate.py"
CI_EVIDENCE_PATH = ROOT / "scripts" / "write_ci_job_evidence.py"


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


def test_f10b_decisions_replace_three_stale_ci_assumptions():
    decisions = json.loads(DECISIONS_PATH.read_text(encoding="utf-8"))
    assert decisions["schema"] == "safehome.rc0810.ci-contract-decisions.v1"
    assert decisions["task"] == "RC0810-F10-B"
    assert decisions["production_gate_eligible"] is False
    assert decisions["decisions"] == {
        "bootstrap_participant_policy": {
            "decision": "admin_controlled_one_time_provisioning_allowed",
            "public_self_registration_allowed": False,
        },
        "participant_ai_client_policy": {
            "decision": "client_methods_may_exist_behind_server_and_runtime_gates",
            "method_presence_means_released": False,
        },
        "production_ai_policy": {
            "decision": "real_provider_code_may_exist_behind_explicit_gates",
            "current_production_release_allowed": False,
        },
    }


def _workflow_job_sections(source: str) -> dict[str, str]:
    jobs_source = source.split("\njobs:\n", 1)[1]
    matches = list(re.finditer(r"(?m)^  ([a-z][a-z0-9-]+):\s*$", jobs_source))
    return {
        match.group(1): jobs_source[match.start() : matches[index + 1].start()]
        if index + 1 < len(matches)
        else jobs_source[match.start() :]
        for index, match in enumerate(matches)
    }


def test_f10b_workflow_has_independent_required_jobs_and_aggregate_gate():
    source = CHECK_WORKFLOW_PATH.read_text(encoding="utf-8")
    sections = _workflow_job_sections(source)
    required = {
        "backend", "ai", "mysql-redis", "web", "npm-audit", "miniprogram",
        "content-api", "artifact", "security-contract",
    }
    assert set(sections) == required | {"release-gate"}
    assert all("\n    needs:" not in sections[job] for job in required)
    assert all(f"ci_fail_job.py {job}" in sections[job] for job in required)
    assert "working-directory: apps/web" in sections["miniprogram"]
    assert "npm ci" in sections["miniprogram"]
    assert "npx playwright install --with-deps chromium" in sections["miniprogram"]
    assert "if: always()" in sections["release-gate"]
    assert all(job in sections["release-gate"] for job in required)
    assert "verify_ci_release_gate.py" in sections["release-gate"]


def test_f10b_workflow_pins_actions_and_declares_lock_aware_caches():
    source = CHECK_WORKFLOW_PATH.read_text(encoding="utf-8")
    assert "actions/checkout@d23441a48e516b6c34aea4fa41551a30e30af803" in source
    assert "actions/setup-python@5fda3b95a4ea91299a34e894583c3862153e4b97" in source
    assert "actions/setup-node@249970729cb0ef3589644e2896645e5dc5ba9c38" in source
    assert "cache-dependency-path: apps/web/package-lock.json" in source
    assert "cache-dependency-path: |" in source
    assert "backend/requirements.txt" in source
    assert not re.search(r"uses:\s+[^\s]+@v\d+", source)


def test_f10b_controlled_failure_only_fails_selected_job():
    clean_env = os.environ.copy()
    clean_env.pop("SAFEHOME_CI_FAIL_JOB", None)
    success = subprocess.run(
        [sys.executable, str(CONTROLLED_FAILURE_PATH), "web"], cwd=ROOT,
        env=clean_env, capture_output=True, text=True, check=False,
    )
    selected = subprocess.run(
        [sys.executable, str(CONTROLLED_FAILURE_PATH), "web"], cwd=ROOT,
        env=clean_env | {"SAFEHOME_CI_FAIL_JOB": "web"},
        capture_output=True, text=True, check=False,
    )
    other = subprocess.run(
        [sys.executable, str(CONTROLLED_FAILURE_PATH), "backend"], cwd=ROOT,
        env=clean_env | {"SAFEHOME_CI_FAIL_JOB": "web"},
        capture_output=True, text=True, check=False,
    )
    assert success.returncode == 0
    assert selected.returncode != 0
    assert other.returncode == 0


def test_f10b_release_gate_rejects_any_non_success_job_result():
    required = [
        "backend", "ai", "mysql-redis", "web", "npm-audit", "miniprogram",
        "content-api", "artifact", "security-contract",
    ]
    success_payload = json.dumps({job: "success" for job in required})
    success = subprocess.run(
        [sys.executable, str(RELEASE_GATE_PATH), "--results-json", success_payload],
        cwd=ROOT, capture_output=True, text=True, check=False,
    )
    assert success.returncode == 0
    assert json.loads(success.stdout)["ci_gate_eligible"] is True
    failed_payload = json.dumps(
        {job: "failure" if job == "web" else "success" for job in required}
    )
    failed = subprocess.run(
        [sys.executable, str(RELEASE_GATE_PATH), "--results-json", failed_payload],
        cwd=ROOT, capture_output=True, text=True, check=False,
    )
    assert failed.returncode != 0
    assert json.loads(failed.stdout)["failed_jobs"] == ["web"]


def test_f10b_job_evidence_binds_source_locks_artifacts_and_provenance(tmp_path):
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True
    ).stdout.strip()
    summary_path = tmp_path / "step-summary.md"
    env = os.environ.copy() | {
        "GITHUB_SHA": head, "GITHUB_RUN_ID": "123", "GITHUB_RUN_ATTEMPT": "2",
        "GITHUB_WORKFLOW": "SafeHome Required Checks", "GITHUB_JOB": "artifact",
        "GITHUB_STEP_SUMMARY": str(summary_path),
    }
    completed = subprocess.run(
        [sys.executable, str(CI_EVIDENCE_PATH), "--job", "artifact", "--artifact", "Dockerfile"],
        cwd=ROOT, env=env, capture_output=True, text=True, check=False,
    )
    assert completed.returncode == 0, completed.stderr
    payload = json.loads(completed.stdout)
    assert payload["schema"] == "safehome.ci-job-evidence.v1"
    assert payload["source"]["commit"] == head
    assert len(payload["source"]["tree"]) == 40
    assert set(payload["dependency_inputs"]) == {
        "backend/requirements.txt", "analysis/profiling/requirements.txt",
        "analysis/text_analysis/requirements.txt", "apps/web/package-lock.json", "Dockerfile",
    }
    assert len(payload["artifacts"]["Dockerfile"]) == 64
    assert payload["provenance"]["run_id"] == "123"
    assert payload["sbom_summary"]["status"] == "dependency_inputs_bound"
    assert payload["attestation_summary"]["status"] == "pending_f22b"
    assert payload["production_gate_eligible"] is False
    assert "safehome.ci-job-evidence.v1" in summary_path.read_text(encoding="utf-8")


def test_f10b_job_evidence_rejects_untrusted_source_identity(tmp_path):
    env = os.environ.copy() | {
        "GITHUB_SHA": "0" * 40,
        "GITHUB_STEP_SUMMARY": str(tmp_path / "summary.md"),
    }
    completed = subprocess.run(
        [sys.executable, str(CI_EVIDENCE_PATH), "--job", "backend"], cwd=ROOT,
        env=env, capture_output=True, text=True, check=False,
    )
    assert completed.returncode != 0
    assert "GITHUB_SHA" in completed.stderr
