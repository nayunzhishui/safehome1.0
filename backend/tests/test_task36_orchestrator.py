import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "run_task36.py"
REGISTRY = ROOT / "config" / "task36_registry.json"


def _module():
    spec = importlib.util.spec_from_file_location("task36_orchestrator", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_registry_covers_f00_to_f19_and_freezes_mutation_boundaries():
    payload = json.loads(REGISTRY.read_text(encoding="utf-8"))
    expected = [f"T36-F{number:02d}" for number in range(20)]
    assert payload["scope"] == expected
    assert [task["id"] for task in payload["tasks"]] == expected
    policy = payload["policy"]
    assert policy["dirty_worktree_policy"] == "observe_only_never_revert"
    assert policy["production_account_mutation_allowed"] is False
    assert policy["public_tunnel_start_allowed"] is False
    assert policy["wechat_secret_mutation_allowed"] is False
    assert policy["showcase_write_scope_expansion_allowed"] is False
    assert policy["release_approval_mutation_allowed"] is False
    assert policy["external_gate_execution_allowed"] is False
    assert policy["temporary_showcase_bypass_counts_as_formal_permission_evidence"] is False


def test_registry_freezes_routes_roles_scopes_faults_schema_and_flags():
    payload = json.loads(REGISTRY.read_text(encoding="utf-8"))
    endpoint_ids = {item["id"] for item in payload["baseline"]["cloudbase"]["endpoints"]}
    assert {"health", "ready", "auth_capabilities", "messages_fault", "checkins_fault", "researcher_dashboard_fault"} <= endpoint_ids
    assert {role["id"] for role in payload["roles"]} == {"participant", "researcher", "supervisor", "admin", "showcase"}
    assert payload["baseline"]["database"]["expected_schema_version"] == "2026_07_21_023"
    flags = {item["id"]: item for item in payload["baseline"]["feature_flags"]}
    assert flags["researcher_platform_full_access"]["formal_permission_evidence"] is False
    assert flags["researcher_platform_full_access"]["must_not_expand_in_f00"] is True
    assert flags["trust_cloudbase_identity_headers"]["frozen_value"] is False
    assert {item["issue"] for item in payload["image_issue_map"]} == {
        "researcher_dashboard_permission_denied",
        "training_history_server_load_failure",
        "messages_server_load_failure",
        "wechat_login_no_response",
    }


def test_load_registry_rejects_forbidden_registered_command(monkeypatch):
    module = _module()
    payload = json.loads(REGISTRY.read_text(encoding="utf-8"))
    payload["tasks"][0]["verify_commands"].append(["python", "bootstrap_researcher.py", "rotate"])
    monkeypatch.setattr(module, "REGISTRY_PATH", ROOT / ".codex_tmp" / "task36-invalid-registry.json")
    module.REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)
    module.REGISTRY_PATH.write_text(json.dumps(payload), encoding="utf-8")
    try:
        with pytest.raises(module.RegistryError, match="禁止操作"):
            module.load_registry()
    finally:
        module.REGISTRY_PATH.unlink(missing_ok=True)


def test_baseline_summarizer_does_not_retain_sensitive_values():
    module = _module()
    summary = module._safe_json_summary(
        "fault",
        {
            "ok": False,
            "token": "must-not-survive",
            "openid": "must-not-survive",
            "error": {"code": "unauthorized", "message": "Bearer must-not-survive"},
            "request_id": "req-safe",
        },
    )
    serialized = json.dumps(summary)
    assert "must-not-survive" not in serialized
    assert summary["error"] == {"code": "unauthorized", "message_present": True}
    assert summary["request_id_present"] is True


def test_capability_summary_keeps_modes_but_not_credentials():
    module = _module()
    summary = module._safe_json_summary(
        "capabilities",
        {
            "ok": True,
            "data": {
                "wechat_login": {"available": True, "mode": "jscode2session", "secret": "hidden"},
                "phone_login": {"available": True, "mode": "wechat_access_token", "token": "hidden"},
            },
        },
    )
    assert summary["wechat_login"] == {"available": True, "mode": "jscode2session"}
    assert summary["phone_login"] == {"available": True, "mode": "wechat_access_token"}
    assert "hidden" not in json.dumps(summary)


def test_verify_dry_run_writes_only_ignored_state_and_never_mutates_external_systems():
    state_path = ROOT / ".codex_tmp" / "task36_state.json"
    previous = state_path.read_bytes() if state_path.exists() else None
    try:
        completed = subprocess.run(
            [sys.executable, str(SCRIPT), "verify", "--task", "T36-F00", "--dry-run"],
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
    assert completed.returncode == 0, completed.stderr
    payload = json.loads(completed.stdout)
    assert payload["status"] == "dry_run"
    assert payload["release_approved"] is False
    assert payload["external_gates_executed"] is False
    assert payload["production_mutations_executed"] is False
    ignored = subprocess.run(
        ["git", "check-ignore", ".codex_tmp/task36_state.json"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert ignored.returncode == 0


def test_resume_rejects_command_drift():
    module = _module()
    specs = [
        {"cwd": ".", "command": ["python", "first.py"]},
        {"cwd": ".", "command": ["python", "second.py"]},
    ]
    record = {
        "command_digest": module.command_digest(specs),
        "outcomes": [
            {"command": ["python", "first.py"], "returncode": 0},
            {"command": ["python", "second.py"], "returncode": 1},
        ],
    }
    index, prefix = module.resume_point(record, specs)
    assert index == 1
    assert len(prefix) == 1
    changed = [{"cwd": ".", "command": ["python", "changed.py"]}, *specs[1:]]
    with pytest.raises(module.RegistryError, match="不能resume"):
        module.resume_point(record, changed)


def test_runner_source_contains_no_git_revert_or_external_mutation_commands():
    source = SCRIPT.read_text(encoding="utf-8").lower()
    assert "git reset" not in source
    assert "git checkout --" not in source
    assert "git clean" not in source
    assert "cloudflared tunnel run" not in source
    assert "bootstrap_researcher.py\", \"rotate" not in source
    assert "wechat_app_secret=" not in source


def test_report_keeps_external_and_formal_permission_gates_false():
    module = _module()
    report = module.report(module.load_registry())
    assert report["tasks_total"] == 20
    assert report["release_approved"] is False
    assert report["external_gates_executed"] is False
    assert report["production_mutations_executed"] is False
    assert report["temporary_showcase_bypass_counts_as_formal_permission_evidence"] is False
    assert report["all_current_evidence_present"] is True
    assert report["next_automatable_task"] == "T36-F01"
