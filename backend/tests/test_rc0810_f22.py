import json
import hashlib
import importlib.util
import re
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
VERIFIER = ROOT / "scripts" / "verify_rc0810_f22_security.py"
POLICY = ROOT / "config" / "rc0810" / "security_gate_policy.json"
EXCEPTIONS = ROOT / "config" / "rc0810" / "security_exception_registry.json"
BASELINE = ROOT / "docs" / "02_专项进度与验收" / "rc0810_f22a_security_baseline.json"
WORKFLOW = ROOT / ".github" / "workflows" / "security-gate.yml"
REGISTRY = ROOT / "content" / "rc0810_release_candidate_registry.json"


def run_verifier(*args: str):
    return subprocess.run(
        [sys.executable, str(VERIFIER), *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def load_verifier_module():
    spec = importlib.util.spec_from_file_location("verify_rc0810_f22_security", VERIFIER)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_f22a_default_baseline_is_valid_but_release_stays_no_go():
    completed = run_verifier()
    assert completed.returncode == 0, completed.stderr
    payload = json.loads(completed.stdout)
    assert payload["valid"] is True
    assert payload["status"] == "frozen_security_baseline"
    assert payload["production_gate_eligible"] is False
    assert payload["phase"] == "F22-A"


def test_f22a_policy_pins_tool_versions_and_action_commits():
    policy = json.loads(POLICY.read_text(encoding="utf-8"))
    assert policy["tools"] == {
        "bandit": "1.9.4",
        "detect-secrets": "1.5.0",
        "npm-audit": "11.13.0",
        "pip-audit": "2.10.1",
        "pip-licenses": "5.5.5",
        "trivy": "0.72.0",
    }
    assert all(re.fullmatch(r"[0-9a-f]{40}", value) for value in policy["action_commits"].values())


def test_f22a_policy_covers_every_required_scan_and_excludes_no_business_source():
    policy = json.loads(POLICY.read_text(encoding="utf-8"))
    scans = {item["id"]: item for item in policy["scans"]}
    assert set(scans) == {
        "secret",
        "sast",
        "python_dependency",
        "node_dependency",
        "container",
        "sbom",
        "license",
    }
    assert all(item["scope"] for item in scans.values())
    assert all(item["timeout_seconds"] > 0 for item in scans.values())
    assert not any("backend" in path or "apps" in path for path in policy["excluded_paths"])
    assert scans["sast"]["scope"] == ["backend", "scripts", "analysis"]
    assert scans["python_dependency"]["scope"] == [
        "backend/requirements.txt",
        "analysis/profiling/requirements.txt",
        "analysis/text_analysis/requirements.txt",
    ]
    assert set(policy["exclusion_reasons"]) == set(policy["excluded_paths"])


def test_f22a_exception_registry_is_empty_and_schema_requires_owner_reason_expiry():
    exceptions = json.loads(EXCEPTIONS.read_text(encoding="utf-8"))
    assert exceptions["exceptions"] == []
    schema = json.loads(
        (ROOT / "config" / "rc0810" / "security_gate.schema.json").read_text(
            encoding="utf-8"
        )
    )
    required = set(schema["$defs"]["exception"]["required"])
    assert {"finding_id", "owner", "reason", "compensating_control", "expires_at", "review_status"} <= required
    verifier = load_verifier_module()
    self_approved = {
        "schema": "safehome.rc0810.security-exceptions.v1",
        "automation_may_approve": False,
        "exceptions": [{
            "finding_id": "F22-SELF-APPROVAL",
            "fingerprint": "0" * 64,
            "owner": "same-person",
            "reason": "temporary accepted risk for test",
            "compensating_control": "independent monitoring remains active",
            "created_at": "2026-08-10T00:00:00+00:00",
            "expires_at": "2026-08-20T00:00:00+00:00",
            "review_status": "approved",
            "reviewer_id": "same-person",
        }],
    }
    assert "exception_self_approval_forbidden" in verifier.validate_exceptions(
        self_approved,
        schema,
        "2026-08-10T01:00:00+00:00",
        baseline=json.loads(BASELINE.read_text(encoding="utf-8")),
        policy=json.loads(POLICY.read_text(encoding="utf-8")),
    )
    self_approved["exceptions"][0]["owner"] = "different-owner"
    errors = verifier.validate_exceptions(
        self_approved,
        schema,
        "2026-08-10T01:00:00+00:00",
        baseline=json.loads(BASELINE.read_text(encoding="utf-8")),
        policy=json.loads(POLICY.read_text(encoding="utf-8")),
    )
    assert "exception_reviewer_untrusted" in errors
    assert "exception_finding_not_bound" in errors


def test_f22a_baseline_binds_source_locks_policy_exceptions_and_raw_reports():
    baseline = json.loads(BASELINE.read_text(encoding="utf-8"))
    assert len(baseline["source_tree"]) == 40
    assert len(baseline["dirty_diff_sha256"]) == 64
    assert set(baseline["dependency_inputs"]) == {
        "backend/requirements.txt",
        "analysis/profiling/requirements.txt",
        "analysis/text_analysis/requirements.txt",
        "apps/web/package-lock.json",
        "Dockerfile",
    }
    assert all(len(value) == 64 for value in baseline["dependency_inputs"].values())
    assert len(baseline["policy_sha256"]) == 64
    assert len(baseline["exception_registry_sha256"]) == 64
    assert {item["tool"] for item in baseline["raw_reports"]} >= {
        "bandit",
        "detect-secrets",
        "npm-audit",
        "pip-audit",
    }
    assert len(baseline["blocking_findings"]) == baseline["open_gate_findings"]
    assert all(len(item["fingerprint"]) == 64 for item in baseline["blocking_findings"])


def test_f22a_rejects_source_or_lock_binding_tamper(tmp_path):
    baseline = json.loads(BASELINE.read_text(encoding="utf-8"))
    baseline["source_tree"] = "0" * 40
    baseline["dependency_inputs"]["backend/requirements.txt"] = "0" * 64
    candidate = tmp_path / "tampered-baseline.json"
    candidate.write_text(json.dumps(baseline), encoding="utf-8")
    completed = run_verifier("--baseline", str(candidate))
    assert completed.returncode != 0
    assert "source_tree_mismatch" in completed.stdout
    assert "dependency_input_mismatch" in completed.stdout


def test_f22a_require_runtime_rejects_missing_or_hash_mismatched_reports(tmp_path):
    baseline = json.loads(BASELINE.read_text(encoding="utf-8"))
    for report in baseline["raw_reports"]:
        report["path"] = str(tmp_path / f"missing-{report['tool']}.json")
    candidate = tmp_path / "missing-runtime.json"
    candidate.write_text(json.dumps(baseline), encoding="utf-8")
    completed = run_verifier("--baseline", str(candidate), "--require-runtime")
    assert completed.returncode != 0
    assert "runtime_report_missing" in completed.stdout

    forged = json.loads(BASELINE.read_text(encoding="utf-8"))
    for report in forged["raw_reports"]:
        fake = tmp_path / f"forged-{report['tool']}.json"
        fake.write_text("{}", encoding="utf-8")
        report["path"] = str(fake)
        report["sha256"] = hashlib.sha256(fake.read_bytes()).hexdigest()
        report["bytes"] = fake.stat().st_size
        report["exit_code"] = 127
        report["command"] = ["forged"]
    forged["finding_summary"] = {key: 0 for key in forged["finding_summary"]}
    forged["open_gate_findings"] = 0
    forged_path = tmp_path / "forged-runtime.json"
    forged_path.write_text(json.dumps(forged), encoding="utf-8")
    completed = run_verifier("--baseline", str(forged_path), "--require-runtime")
    assert completed.returncode != 0
    assert "runtime_report_contract_invalid" in completed.stdout

    trailing = json.loads(BASELINE.read_text(encoding="utf-8"))
    source_tree = trailing["source_tree"]
    report_dir = tmp_path / ".codex_tmp" / "rc0810" / "security" / "f22a" / source_tree / "reports"
    report_dir.mkdir(parents=True)
    for group in (trailing["raw_reports"], trailing["negative_gate_evidence"]["reports"]):
        for report in group:
            destination = report_dir / Path(report["path"]).name
            shutil.copyfile(report["path"], destination)
            report["path"] = str(destination)
            report["sha256"] = hashlib.sha256(destination.read_bytes()).hexdigest()
            report["bytes"] = destination.stat().st_size
    detect = next(item for item in trailing["raw_reports"] if item["tool"] == "detect-secrets")
    detect_path = Path(detect["path"])
    detect_path.write_text(
        '{"results":{}}\n{"results":{"hidden":[{"type":"Secret"}]}}',
        encoding="utf-8",
    )
    detect["sha256"] = hashlib.sha256(detect_path.read_bytes()).hexdigest()
    detect["bytes"] = detect_path.stat().st_size
    trailing["finding_summary"]["secret"] = 0
    trailing["open_gate_findings"] -= 254
    trailing_path = tmp_path / "trailing-runtime.json"
    trailing_path.write_text(json.dumps(trailing), encoding="utf-8")
    completed = run_verifier("--baseline", str(trailing_path), "--require-runtime")
    assert completed.returncode != 0
    assert "runtime_report_parse_failed" in completed.stdout


def test_f22a_self_check_rejects_fake_secret_high_sast_and_high_dependency():
    completed = run_verifier("--self-check")
    assert completed.returncode == 0, completed.stderr
    payload = json.loads(completed.stdout)
    assert payload["self_checks"] == {
        "expired_exception_rejected": True,
        "fake_secret_fixture_rejected": True,
        "high_dependency_fixture_rejected": True,
        "high_sast_fixture_rejected": True,
        "self_approved_exception_rejected": True,
        "untrusted_reviewer_rejected": True,
        "unknown_finding_rejected": True,
        "stale_report_rejected": True,
    }


def test_f22a_open_secret_critical_high_or_unknown_severity_keeps_gate_closed():
    policy = json.loads(POLICY.read_text(encoding="utf-8"))
    assert policy["severity_gate"] == {
        "secret": ["unknown", "low", "medium", "high", "critical"],
        "sast": ["high", "critical", "unknown"],
        "dependency": ["high", "critical", "unknown"],
        "forbidden_licenses": ["AGPL-3.0", "GPL-3.0-only", "SSPL-1.0"],
    }


def test_f22a_workflow_uses_only_sha_pinned_actions_and_runs_negative_gate():
    workflow = WORKFLOW.read_text(encoding="utf-8")
    uses = re.findall(r"uses:\s*([^\s]+)", workflow)
    assert uses
    assert all(re.search(r"@[0-9a-f]{40}$", value) for value in uses)
    assert "--self-check" in workflow
    assert "--require-runtime" in workflow
    assert "pip-audit==2.10.1" in workflow
    assert "bandit==1.9.4" in workflow
    assert "detect-secrets==1.5.0" in workflow


def test_f22a_container_and_supply_chain_gaps_remain_explicitly_blocking():
    baseline = json.loads(BASELINE.read_text(encoding="utf-8"))
    assert baseline["container_scan"]["status"] == "pending_f22b_image"
    assert baseline["container_scan"]["production_blocking"] is True
    assert baseline["supply_chain_attestation"]["status"] == "pending_external"
    assert baseline["supply_chain_attestation"]["production_blocking"] is True


def test_f22a_registry_freezes_exact_scope_and_phase_without_business_changes():
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    unit = next(item for item in registry["execution_units"] if item["id"] == "RC0810-F22-A")
    task = next(item for item in registry["tasks"] if item["id"] == "RC0810-F22")
    assert unit["subtasks"] == [f"F22.{index}" for index in range(1, 9)]
    assert unit["change_budget"]["expected_files"] == 14
    assert len(unit["allowed_files"]) == 14
    assert all(not path.startswith("backend/") or path.endswith("test_rc0810_f22.py") for path in unit["allowed_files"])
    assert [item["expected_test_count"] for item in task["acceptance_commands"]] == [12, 19, 1, 1, 1]
