import importlib.util
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "run_tasks_23_34.py"
REGISTRY = ROOT / "config" / "task23_34_registry.json"


def _module():
    spec = importlib.util.spec_from_file_location("tasks_23_34_orchestrator", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_registry_covers_t23_to_t34_and_t25_to_t34_are_engineering_complete():
    payload = json.loads(REGISTRY.read_text(encoding="utf-8"))
    expected = [f"T{number}" for number in range(23, 35)]
    assert payload["scope"] == expected
    assert [task["id"] for task in payload["tasks"]] == expected
    assert all(task["engineering_complete"] for task in payload["tasks"] if task["id"] >= "T25")
    assert payload["policy"]["release_approval_mutation_allowed"] is False
    assert payload["policy"]["external_gate_execution_allowed"] is False
    assert payload["policy"]["temporary_showcase_bypass_counts_as_permission_evidence"] is False


def test_report_proves_commits_and_evidence_without_claiming_external_approval():
    module = _module()
    report = module.report(module.load_registry())
    assert report["all_t25_t34_engineering_complete"] is True
    assert report["tasks_t25_t34_engineering_complete"] == 10
    assert report["all_commits_reachable"] is True
    assert report["all_evidence_present"] is True
    assert report["release_approved"] is False
    assert report["external_gates_executed"] is False


def test_verify_dry_run_writes_only_ignored_state_and_never_runs_external_gates():
    state_path = ROOT / ".codex_tmp" / "task23_34_state.json"
    previous = state_path.read_bytes() if state_path.exists() else None
    try:
        completed = subprocess.run(
            [sys.executable, str(SCRIPT), "verify", "--task", "T34", "--dry-run"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
    finally:
        if previous is None:
            state_path.unlink(missing_ok=True)
        else:
            state_path.write_bytes(previous)
    assert completed.returncode == 0
    payload = json.loads(completed.stdout)
    assert payload["status"] == "dry_run"
    assert payload["release_approved"] is False
    assert payload["external_gates_executed"] is False
    assert all(item["status"] == "dry_run" for item in payload["outcomes"])
    ignored = subprocess.run(
        ["git", "check-ignore", ".codex_tmp/task23_34_state.json"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert ignored.returncode == 0


def test_resume_point_skips_only_successful_matching_commands_and_rejects_registry_drift():
    module = _module()
    specs = [
        {"cwd": ".", "command": ["python", "first.py"]},
        {"cwd": ".", "command": ["python", "second.py"]},
    ]
    record = {
        "outcomes": [
            {"command": ["python", "first.py"], "returncode": 0},
            {"command": ["python", "second.py"], "returncode": 1},
        ]
    }
    index, prefix = module.resume_point(record, specs)
    assert index == 1 and len(prefix) == 1
    changed = [{"cwd": ".", "command": ["python", "changed.py"]}, *specs[1:]]
    try:
        module.resume_point(record, changed)
    except module.RegistryError:
        pass
    else:
        raise AssertionError("registry drift must block resume")
