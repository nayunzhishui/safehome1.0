import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATH = ROOT / "content" / "rc0810_release_candidate_registry.json"
RUNNER_PATH = ROOT / "scripts" / "run_rc0810.py"


def run_cli(*args: str, env: dict[str, str] | None = None):
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)
    return subprocess.run(
        [sys.executable, str(RUNNER_PATH), *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
        env=merged_env,
    )


def fixture_registry(tmp_path: Path, mode: str = "success", timeout: int = 10):
    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    registry["tasks"][0]["acceptance_commands"] = [
        {
            "argv": [
                "python",
                "backend/tests/fixtures/rc0810_command_fixture.py",
                mode,
            ],
            "cwd": ".",
            "timeout_seconds": timeout,
            "shell": False,
            "status": "active",
        }
    ]
    path = tmp_path / f"registry-{mode}.json"
    path.write_text(json.dumps(registry, ensure_ascii=False), encoding="utf-8")
    return path


def write_review_decision(
    packet_result: dict,
    *,
    reviewer_id: str,
    decision: str = "pass",
    reviewer_kind: str = "separate_agent",
) -> Path:
    packet_path = Path(packet_result["review_packet_path"])
    packet = json.loads(packet_path.read_text(encoding="utf-8"))
    decision_path = packet_path.with_name(f"decision-{reviewer_id}.json")
    decision_path.write_text(
        json.dumps(
            {
                "schema": "safehome.rc0810.review-decision.v1",
                "review_packet_sha256": packet_result["review_packet_sha256"],
                "challenge_nonce": packet["challenge_nonce"],
                "decision": decision,
                "reviewer_id": reviewer_id,
                "reviewer_kind": reviewer_kind,
                "findings": [],
                "created_at": "2026-08-09T16:00:00+00:00",
                "valid_until": "2099-01-01T00:00:00+00:00",
            }
        ),
        encoding="utf-8",
    )
    return decision_path


def test_registry_covers_f00_to_f26_and_binds_inherited_dirty_baseline():
    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))

    assert registry["schema"] == "safehome.rc0810.registry.v1"
    assert [task["id"] for task in registry["tasks"]] == [
        f"RC0810-F{index:02d}" for index in range(27)
    ]
    assert registry["frozen_baseline"]["head"] == (
        "77bb5c2643e029693afd8088d74dd563d9480c12"
    )
    assert registry["frozen_baseline"]["source_tree"] == (
        "563b3cd00209aa8350fa5d883f632663ce5802e6"
    )
    assert registry["frozen_baseline"]["dirty_diff"]["sha256"] == (
        "711e9e9fce45674df81747ff9496eda3210c95fe484f91e5e17349b9d84437ba"
    )
    assert len(registry["preflight_documents"]) == 10
    for document in registry["preflight_documents"]:
        assert len(document["sha256"]) == hashlib.sha256().digest_size * 2


def test_registry_is_complete_machine_contract_with_bidirectional_mapping():
    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    tasks = registry["tasks"]
    tasks_by_id = {task["id"]: task for task in tasks}

    assert sum(len(task["subtasks"]) for task in tasks) == 225
    assert len(
        {
            subtask["id"]
            for task in tasks
            for subtask in task["subtasks"]
        }
    ) == 225
    required = {
        "dependencies",
        "priority",
        "pr_ids",
        "allowed_files",
        "forbidden_files",
        "acceptance_commands",
        "external_gates",
        "change_budget",
        "rollback",
    }
    for task in tasks:
        assert required.issubset(task)
        assert set(task["dependencies"]).issubset(tasks_by_id)
        assert task["change_budget"]["pause_when_actual_exceeds_percent"] == 50
        assert task["change_budget"]["actual_delta_baseline"] == "task_start_snapshot"
        assert task["change_budget"]["on_exceeded"] == [
            "pause",
            "plan_backfill",
            "split_subtask",
        ]
        assert set(task["allowed_files"]) == set(
            task["change_budget"]["allowed_modules"]
        )
        assert set(task["forbidden_files"]) == set(
            task["change_budget"]["forbidden_modules"]
        )
        if task["change_budget"]["expected_migrations"] > 0:
            assert "backend/migrations/**" in task["allowed_files"]

    assert tasks_by_id["RC0810-F00"]["dependencies"] == []
    reverse = registry["pr_mapping"]["pr_to_tasks"]
    for task in tasks:
        assert registry["pr_mapping"]["task_to_pr"][task["id"]] == task["pr_ids"]
        for pr_id in task["pr_ids"]:
            assert task["id"] in reverse[pr_id]

    assert set(registry["claim_classes"]) == {
        "current_code_fact",
        "external_rule",
        "project_decision",
        "recommendation",
        "todo",
    }
    risk = registry["risk_priority_model"]
    assert risk["dimensions"]["detectability"]["high_score_means"] == (
        "harder_to_detect"
    )
    assert set(risk["forced_p0_categories"]) == {
        "cross_object_disclosure",
        "data_loss",
        "incorrect_high_risk_feedback",
        "incorrect_release",
        "credential_exposure",
    }
    assert registry["evidence_policy"]["invalidation"][
        "propagation"
    ] == "recursive_dependents"


def test_plan_validates_schema_topology_and_start_order(tmp_path):
    runtime = tmp_path / "runtime"
    env = {"RC0810_RUNTIME_ROOT": str(runtime)}

    planned = run_cli("plan", env=env)
    assert planned.returncode == 0, planned.stderr
    payload = json.loads(planned.stdout)
    assert payload["task_count"] == 27
    assert payload["subtask_count"] == 225
    assert payload["execution_order"][0] == "RC0810-F00"
    assert payload["execution_order"][1:6] == [
        "RC0810-F10-A",
        "RC0810-F12-A",
        "RC0810-F14-A",
        "RC0810-F22-A",
        "RC0810-F25-A",
    ]

    unknown = run_cli("start", "RC0810-F99", env=env)
    assert unknown.returncode != 0

    out_of_order = run_cli("start", "RC0810-F01", env=env)
    assert out_of_order.returncode != 0

    invalid = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    invalid["schema"] = "broken"
    invalid_path = tmp_path / "invalid.json"
    invalid_path.write_text(json.dumps(invalid), encoding="utf-8")
    invalid_env = env | {"RC0810_REGISTRY_PATH": str(invalid_path)}
    assert run_cli("plan", env=invalid_env).returncode != 0

    cyclic = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    cyclic["tasks"][0]["dependencies"] = ["RC0810-F26"]
    cyclic_path = tmp_path / "cyclic.json"
    cyclic_path.write_text(json.dumps(cyclic), encoding="utf-8")
    cyclic_env = env | {"RC0810_REGISTRY_PATH": str(cyclic_path)}
    assert run_cli("plan", env=cyclic_env).returncode != 0


def test_recoverable_lifecycle_binds_dirty_source_and_requires_independent_review(
    tmp_path,
):
    runtime = tmp_path / "runtime"
    counter = tmp_path / "counter.txt"
    registry_path = fixture_registry(tmp_path)
    env = {
        "RC0810_RUNTIME_ROOT": str(runtime),
        "RC0810_REGISTRY_PATH": str(registry_path),
        "RC0810_RUN_ID": "run-contract",
        "RC0810_FIXTURE_COUNTER": str(counter),
    }

    started = run_cli("start", "RC0810-F00", env=env)
    assert started.returncode == 0, started.stderr

    snap = run_cli("snapshot", env=env)
    assert snap.returncode == 0, snap.stderr
    snapshot = json.loads(snap.stdout)
    assert snapshot["git"]["dirty"] is True
    assert snapshot["git"]["source_tree"] != snapshot["git"]["head_tree"]
    assert snapshot["git"]["head_verified"] is False
    assert len(snapshot["git"]["dirty_diff_sha256"]) == 64

    verified = run_cli("verify", "RC0810-F00", env=env)
    assert verified.returncode == 0, verified.stderr
    assert json.loads(verified.stdout)["status"] == "implemented"
    assert counter.read_text(encoding="utf-8") == "1"

    pointer = json.loads((runtime / "state.json").read_text(encoding="utf-8"))
    state = json.loads((runtime / pointer["state_path"]).read_text(encoding="utf-8"))
    for subtask in state["tasks"]["RC0810-F00"]["subtasks"].values():
        assert subtask["status"] == "running"
        assert subtask["input_baseline"]
        assert subtask["commands"]
        assert subtask["exit_codes"] == [0]
        assert subtask["test_count"] == 1
        assert subtask["source_tree"]

    original_registry = registry_path.read_text(encoding="utf-8")
    changed_registry = json.loads(original_registry)
    changed_registry["claim_register"][0]["statement"] += " drift"
    registry_path.write_text(json.dumps(changed_registry), encoding="utf-8")
    stale_review = run_cli("review", "RC0810-F00", env=env)
    assert stale_review.returncode != 0
    registry_path.write_text(original_registry, encoding="utf-8")
    assert run_cli("start", "RC0810-F00", env=env).returncode == 0
    reverified = run_cli("verify", "RC0810-F00", env=env)
    assert reverified.returncode == 0, reverified.stderr
    assert counter.read_text(encoding="utf-8") == "2"

    packet_result = run_cli("review", "RC0810-F00", env=env)
    assert packet_result.returncode == 0, packet_result.stderr
    packet = json.loads(packet_result.stdout)
    assert packet["status"] == "reviewing"
    assert packet["review_decision"] is None

    reviewing_registry = json.loads(registry_path.read_text(encoding="utf-8"))
    reviewing_registry["claim_register"][0]["statement"] += " review drift"
    registry_path.write_text(json.dumps(reviewing_registry), encoding="utf-8")
    stale_while_reviewing = run_cli("review", "RC0810-F00", env=env)
    assert stale_while_reviewing.returncode != 0
    registry_path.write_text(original_registry, encoding="utf-8")
    assert run_cli("start", "RC0810-F00", env=env).returncode == 0
    assert run_cli("verify", "RC0810-F00", env=env).returncode == 0
    packet_result = run_cli("review", "RC0810-F00", env=env)
    assert packet_result.returncode == 0, packet_result.stderr
    packet = json.loads(packet_result.stdout)
    self_decision = write_review_decision(packet, reviewer_id="automation")

    self_signed = run_cli(
        "review",
        "RC0810-F00",
        "--decision",
        "pass",
        "--reviewer-id",
        "automation",
        "--decision-evidence",
        str(self_decision),
        env=env,
    )
    assert self_signed.returncode != 0
    accepted_decision = write_review_decision(
        packet, reviewer_id="f00-independent-reviewer"
    )

    decision_registry = json.loads(registry_path.read_text(encoding="utf-8"))
    decision_registry["claim_register"][0]["statement"] += " decision drift"
    registry_path.write_text(json.dumps(decision_registry), encoding="utf-8")
    stale_decision = run_cli(
        "review",
        "RC0810-F00",
        "--decision",
        "pass",
        "--reviewer-id",
        "f00-independent-reviewer",
        "--decision-evidence",
        str(accepted_decision),
        env=env,
    )
    assert stale_decision.returncode != 0

    registry_path.write_text(original_registry, encoding="utf-8")
    assert run_cli("start", "RC0810-F00", env=env).returncode == 0
    assert run_cli("verify", "RC0810-F00", env=env).returncode == 0
    packet = json.loads(run_cli("review", "RC0810-F00", env=env).stdout)
    accepted_decision = write_review_decision(
        packet, reviewer_id="f00-independent-reviewer"
    )

    accepted = run_cli(
        "review",
        "RC0810-F00",
        "--decision",
        "pass",
        "--reviewer-id",
        "f00-independent-reviewer",
        "--decision-evidence",
        str(accepted_decision),
        env=env,
    )
    assert accepted.returncode == 0, accepted.stderr
    assert json.loads(accepted.stdout)["status"] == "verified"

    next_task = run_cli("next", env=env)
    assert next_task.returncode == 0, next_task.stderr
    assert json.loads(next_task.stdout)["task"] == "RC0810-F10-A"

    phase_started = run_cli("start", "RC0810-F10-A", env=env)
    assert phase_started.returncode == 0, phase_started.stderr
    pointer = json.loads((runtime / "state.json").read_text(encoding="utf-8"))
    state = json.loads((runtime / pointer["state_path"]).read_text(encoding="utf-8"))
    phase_snapshot = state["tasks"]["RC0810-F10-A"]["start_snapshot"]
    assert phase_snapshot["binding"] == "task_start_worktree"
    assert phase_snapshot["source_tree"]
    assert phase_snapshot["source_manifest"]
    assert phase_snapshot["dirty_diff_sha256"]

    resumed = run_cli("resume", env=env)
    assert resumed.returncode == 0, resumed.stderr
    assert json.loads(resumed.stdout)["resume_from"] == "RC0810-F00:verified"
    assert counter.read_text(encoding="utf-8") == "4"

    reported = run_cli("report", env=env)
    assert reported.returncode == 0, reported.stderr
    report = json.loads(reported.stdout)
    assert report["tasks"]["RC0810-F00"]["status"] == "verified"
    assert Path(report["report_path"]).is_file()

    phase_verified = run_cli("verify", "RC0810-F10-A", env=env)
    assert phase_verified.returncode == 0, phase_verified.stderr
    phase_packet = json.loads(run_cli("review", "RC0810-F10-A", env=env).stdout)
    phase_decision = write_review_decision(
        phase_packet, reviewer_id="f10a-independent-reviewer"
    )
    phase_accepted = run_cli(
        "review",
        "RC0810-F10-A",
        "--decision",
        "pass",
        "--reviewer-id",
        "f10a-independent-reviewer",
        "--decision-evidence",
        str(phase_decision),
        env=env,
    )
    assert phase_accepted.returncode == 0, phase_accepted.stderr

    state = json.loads((runtime / pointer["state_path"]).read_text(encoding="utf-8"))
    subtasks = state["tasks"]["RC0810-F10-A"]["subtasks"]
    assert subtasks["F10.1"]["status"] == "verified"
    assert subtasks["F10.8"]["status"] == "phase_a_verified"
    assert all(
        subtasks[f"F10.{index}"]["status"] == "pending"
        for index in range(2, 10)
        if index != 8
    )


def test_timeout_and_tampered_evidence_fail_closed(tmp_path):
    failure_runtime = tmp_path / "failure-runtime"
    failure_registry = fixture_registry(tmp_path, mode="fail")
    failure_env = {
        "RC0810_RUNTIME_ROOT": str(failure_runtime),
        "RC0810_REGISTRY_PATH": str(failure_registry),
        "RC0810_RUN_ID": "run-failure",
    }
    assert run_cli("start", "RC0810-F00", env=failure_env).returncode == 0
    failed = run_cli("verify", "RC0810-F00", env=failure_env)
    assert failed.returncode != 0
    assert json.loads(failed.stdout)["outcomes"][0]["exit_code"] == 7

    runtime = tmp_path / "runtime"
    registry_path = fixture_registry(tmp_path, mode="timeout", timeout=1)
    env = {
        "RC0810_RUNTIME_ROOT": str(runtime),
        "RC0810_REGISTRY_PATH": str(registry_path),
        "RC0810_RUN_ID": "run-timeout",
    }

    assert run_cli("start", "RC0810-F00", env=env).returncode == 0
    assert run_cli("snapshot", env=env).returncode == 0
    timed_out = run_cli("verify", "RC0810-F00", env=env)
    assert timed_out.returncode != 0
    outcome = json.loads(timed_out.stdout)["outcomes"][0]
    assert outcome["timed_out"] is True
    assert outcome["exit_code"] == 124

    pointer = json.loads((runtime / "state.json").read_text(encoding="utf-8"))
    state_path = runtime / pointer["state_path"]
    state = json.loads(state_path.read_text(encoding="utf-8"))
    evidence_path = Path(state["evidence_chain"][0]["path"])
    evidence_path.write_text("{}\n", encoding="utf-8")

    assert run_cli("resume", env=env).returncode != 0
    assert run_cli("report", env=env).returncode != 0


def test_package_check_and_recursive_evidence_invalidation(tmp_path):
    runtime = tmp_path / "runtime"
    registry_path = fixture_registry(tmp_path)
    env = {
        "RC0810_RUNTIME_ROOT": str(runtime),
        "RC0810_REGISTRY_PATH": str(registry_path),
        "RC0810_RUN_ID": "run-package",
    }
    assert run_cli("start", "RC0810-F00", env=env).returncode == 0
    snapshot = json.loads(run_cli("snapshot", env=env).stdout)

    staging = runtime / "staging"
    staging.mkdir(parents=True)
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    profile_id = "f00_harness_sources"
    expected_paths = registry["artifact_profiles"][profile_id]["expected_files"]
    artifact_files = []
    for relative in expected_paths:
        content = subprocess.run(
            ["git", "show", f"{snapshot['git']['source_tree']}:{relative}"],
            cwd=ROOT,
            capture_output=True,
            check=True,
        ).stdout
        target = staging / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
        artifact_files.append(
            {"path": relative, "sha256": hashlib.sha256(content).hexdigest()}
        )
    manifest = {
        "schema": "safehome.rc0810.package.v1",
        "profile_id": profile_id,
        "artifact_kind": "engineering_evidence",
        "artifact_root": str(staging),
        "commit": snapshot["git"]["head"],
        "head_tree": snapshot["git"]["head_tree"],
        "source_tree": snapshot["git"]["source_tree"],
        "dirty_diff_sha256": snapshot["git"]["dirty_diff_sha256"],
        "built_from": "staging",
        "worktree_source_used": False,
        "complete_file_set": True,
        "source_attestation": {
            "source_kind": "git_tree",
            "source_tree": snapshot["git"]["source_tree"],
        },
        "files": artifact_files,
    }
    manifest_path = runtime / "package.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    checked = run_cli("package-check", str(manifest_path), env=env)
    assert checked.returncode == 0, checked.stderr
    assert json.loads(checked.stdout)["status"] == "passed"

    original_path = manifest["files"][0]["path"]
    manifest["files"][0]["path"] = "../artifact.txt"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    assert run_cli("package-check", str(manifest_path), env=env).returncode != 0

    manifest["files"][0]["path"] = original_path
    manifest["commit"] = "0" * 40
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    assert run_cli("package-check", str(manifest_path), env=env).returncode != 0

    verified = run_cli("verify", "RC0810-F00", env=env)
    assert verified.returncode == 0, verified.stderr
    packet = json.loads(run_cli("review", "RC0810-F00", env=env).stdout)
    accepted_decision = write_review_decision(
        packet, reviewer_id="f00-independent-reviewer"
    )
    accepted = run_cli(
        "review",
        "RC0810-F00",
        "--decision",
        "pass",
        "--reviewer-id",
        "f00-independent-reviewer",
        "--decision-evidence",
        str(accepted_decision),
        env=env,
    )
    assert accepted.returncode == 0, accepted.stderr

    changed_registry = json.loads(registry_path.read_text(encoding="utf-8"))
    changed_registry["claim_register"][0]["statement"] += " changed"
    registry_path.write_text(
        json.dumps(changed_registry, ensure_ascii=False), encoding="utf-8"
    )
    stale_report = run_cli("report", env=env)
    assert stale_report.returncode == 0, stale_report.stderr
    assert json.loads(stale_report.stdout)["stale_tasks"] == [
        f"RC0810-F{index:02d}" for index in range(27)
    ]
