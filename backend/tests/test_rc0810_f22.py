import json
import importlib.util
import hashlib
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
VERIFIER = ROOT / "scripts" / "verify_rc0810_f22_security.py"
SCANNER = ROOT / "scripts" / "run_rc0810_f22_scans.py"
POLICY = ROOT / "config" / "rc0810" / "security_gate_policy.json"
EXCEPTIONS = ROOT / "config" / "rc0810" / "security_exception_registry.json"
BASELINE = ROOT / "docs" / "02_专项进度与验收" / "rc0810_f22b_security_gate.json"
LEGACY_BASELINE = ROOT / "docs" / "02_专项进度与验收" / "rc0810_f22a_security_baseline.json"
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


def load_scanner_module():
    spec = importlib.util.spec_from_file_location("run_rc0810_f22_scans", SCANNER)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_f22b_reviewed_false_positive_does_not_hide_new_secret(tmp_path):
    module = load_scanner_module()
    reports = {
        "detect-secrets": {
            "results": {
                "fixture.py": [
                    {
                        "type": "Hex High Entropy String",
                        "line_number": 1,
                        "hashed_secret": "a" * 64,
                        "is_secret": False,
                    },
                    {
                        "type": "AWS Access Key",
                        "line_number": 2,
                        "hashed_secret": "b" * 64,
                    },
                ]
            }
        },
        "bandit": {"results": []},
        "pip-audit": {"dependencies": []},
        "npm-audit": {
            "metadata": {
                "vulnerabilities": {
                    "critical": 0,
                    "high": 0,
                    "moderate": 0,
                    "low": 0,
                }
            }
        },
    }
    paths = {}
    for tool, payload in reports.items():
        path = tmp_path / f"{tool}.json"
        path.write_text(json.dumps(payload), encoding="utf-8")
        paths[tool] = path

    assert module.summarize(paths)["secret"] == 1
    findings = module.build_blocking_findings(paths, "c" * 40)
    assert len(findings) == 1
    assert findings[0]["category"] == "secret"


def test_f22b_source_binding_allows_later_evidence_only_commit(monkeypatch):
    module = load_verifier_module()
    recorded_head = "a" * 40
    recorded_tree = "b" * 40
    source_tree = "c" * 40
    diff_bytes = b"frozen security diff"
    gate = {
        "head": recorded_head,
        "head_tree": recorded_tree,
        "source_tree": source_tree,
        "dirty_diff_sha256": hashlib.sha256(diff_bytes).hexdigest(),
        "source_manifest_sha256": "d" * 64,
    }
    current = {
        "head": "e" * 40,
        "head_tree": "f" * 40,
        "source_tree": source_tree,
        "dirty_diff_sha256": "0" * 64,
        "source_manifest_sha256": "d" * 64,
    }

    def fake_git_bytes(*args):
        if args[:2] == ("merge-base", "--is-ancestor"):
            return b""
        if args[0] == "rev-parse":
            return f"{recorded_tree}\n".encode("ascii")
        if args[0] == "diff-tree":
            return diff_bytes
        raise AssertionError(args)

    monkeypatch.setattr(module, "git_bytes", fake_git_bytes)
    assert module.source_binding_errors(gate, current) == []


def test_f22b_default_gate_is_valid_but_release_stays_no_go():
    completed = run_verifier()
    assert completed.returncode == 0, completed.stderr
    payload = json.loads(completed.stdout)
    assert payload["valid"] is True
    assert payload["status"] in {"rescan_complete_no_go", "attestation_pending_no_go"}
    assert payload["production_gate_eligible"] is False
    assert payload["phase"] == "F22-B"


def test_f22b_policy_pins_tool_versions_images_and_action_commits():
    policy = json.loads(POLICY.read_text(encoding="utf-8"))
    assert policy["tools"] == {
        "bandit": "1.9.4",
        "detect-secrets": "1.5.0",
        "npm-audit": "11.13.0",
        "pip-audit": "2.10.1",
        "pip-licenses": "5.5.5",
        "trivy": "0.72.0",
    }
    assert policy["phase"] == "F22-B"
    assert policy["tool_images"]["trivy"] == "sha256:cffe3f5161a47a6823fbd23d985795b3ed72a4c806da4c4df16266c02accdd6f"
    assert all(re.fullmatch(r"[0-9a-f]{40}", value) for value in policy["action_commits"].values())


def test_f22_scan_is_not_blocked_by_expired_human_review_checkpoint():
    runner_path = ROOT / "scripts" / "run_rc0810_f22_scans.py"
    spec = importlib.util.spec_from_file_location("run_rc0810_f22_scans", runner_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    registry = module.load_registry(require_current_review_evidence=False)
    assert registry["schema"] == "safehome.rc0810.registry.v1"


def test_f22b_policy_covers_every_required_scan_and_excludes_no_business_source():
    runner_path = ROOT / "scripts" / "run_rc0810_f22_scans.py"
    spec = importlib.util.spec_from_file_location("run_rc0810_f22_scans", runner_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    assert set(module.SECURITY_REPORT_RELATIVES) == {
        "docs/02_专项进度与验收/rc0810_f22a_security_baseline.json",
        "docs/02_专项进度与验收/rc0810_f22b_security_gate.json",
        "docs/02_专项进度与验收/rc0810_f25a_platform_baseline.json",
        "docs/02_专项进度与验收/rc0810_f25a_platform_baseline_current.json",
        "docs/02_专项进度与验收/rc0810_f25b_evidence.json",
        "docs/02_专项进度与验收/rc0810_f26_final_rc.json",
        "docs/02_专项进度与验收/rc0810_f26_final_rc.md",
        "docs/02_专项进度与验收/rc0810_required_ci_evidence.json",
        "docs/02_专项进度与验收/rc0810_wave_c_review_packet.json",
        "docs/02_专项进度与验收/rc0810_wave_c_review_decision.json",
    }
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
    assert all(item["phase_b_status"] == "active" for item in scans.values())


def test_f22b_exception_registry_is_empty_and_schema_requires_owner_reason_expiry():
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


def test_f22b_gate_binds_source_locks_actions_image_and_reports():
    gate = json.loads(BASELINE.read_text(encoding="utf-8"))
    assert len(gate["source_tree"]) == 40
    assert len(gate["dirty_diff_sha256"]) == 64
    assert set(gate["dependency_inputs"]) == {
        "backend/requirements.txt",
        "analysis/profiling/requirements.txt",
        "analysis/text_analysis/requirements.txt",
        "apps/web/package-lock.json",
        "Dockerfile",
        "config/rc0810/database_profiles.json",
        "config/rc0810/detect_secrets.baseline.json",
    }
    assert all(len(value) == 64 for value in gate["dependency_inputs"].values())
    assert set(gate["action_inputs"]) == {".github/workflows/check.yml", ".github/workflows/security-gate.yml"}
    assert len(gate["policy_sha256"]) == 64
    assert len(gate["exception_registry_sha256"]) == 64
    assert {item["tool"] for item in gate["source_reports"]} == {
        "bandit",
        "detect-secrets",
        "npm-audit",
        "pip-audit",
    }
    assert len(gate["blocking_findings"]) == gate["source_open_gate_findings"]
    assert re.fullmatch(r"sha256:[0-9a-f]{64}", gate["container_scan"]["image_id"])
    assert all(len(item["fingerprint"]) == 64 for item in gate["blocking_findings"])


def test_f22b_rejects_source_or_lock_binding_tamper(tmp_path):
    baseline = json.loads(BASELINE.read_text(encoding="utf-8"))
    baseline["source_tree"] = "0" * 40
    baseline["dependency_inputs"]["backend/requirements.txt"] = "0" * 64
    candidate = tmp_path / "tampered-baseline.json"
    candidate.write_text(json.dumps(baseline), encoding="utf-8")
    completed = run_verifier("--baseline", str(candidate))
    assert completed.returncode != 0
    assert "source_tree_mismatch" in completed.stdout
    assert "dependency_input_mismatch" in completed.stdout


def test_f22b_require_runtime_rejects_missing_or_hash_mismatched_reports(tmp_path):
    baseline = json.loads(BASELINE.read_text(encoding="utf-8"))
    report_dir = (
        tmp_path / ".codex_tmp" / "rc0810" / "security" / "f22b"
        / baseline["source_tree"] / "reports"
    )
    for report in baseline["source_reports"]:
        report["path"] = str(report_dir / Path(report["path"]).name)
    candidate = tmp_path / "missing-runtime.json"
    candidate.write_text(json.dumps(baseline), encoding="utf-8")
    completed = run_verifier("--baseline", str(candidate), "--require-runtime")
    assert completed.returncode != 0
    assert "runtime_report_missing" in completed.stdout

    forged = json.loads(BASELINE.read_text(encoding="utf-8"))
    forged["container_scan"]["report"]["sha256"] = "0" * 64
    forged_path = tmp_path / "forged-runtime.json"
    forged_path.write_text(json.dumps(forged), encoding="utf-8")
    completed = run_verifier("--baseline", str(forged_path), "--require-runtime")
    assert completed.returncode != 0
    assert "runtime_report_hash_mismatch" in completed.stdout


def test_f22b_self_check_rejects_each_blocking_gate_fixture():
    completed = run_verifier("--self-check")
    assert completed.returncode == 0, completed.stderr
    payload = json.loads(completed.stdout)
    assert payload["self_checks"] == {
        "expired_exception_rejected": True,
        "critical_container_fixture_rejected": True,
        "fake_secret_fixture_rejected": True,
        "forbidden_license_fixture_rejected": True,
        "high_dependency_fixture_rejected": True,
        "high_sast_fixture_rejected": True,
        "missing_attestation_rejected": True,
        "self_approved_exception_rejected": True,
        "untrusted_reviewer_rejected": True,
        "unknown_finding_rejected": True,
        "stale_report_rejected": True,
    }


def test_f22b_open_secret_critical_high_or_unknown_severity_keeps_gate_closed():
    policy = json.loads(POLICY.read_text(encoding="utf-8"))
    assert policy["severity_gate"] == {
        "secret": ["unknown", "low", "medium", "high", "critical"],
        "sast": ["high", "critical", "unknown"],
        "dependency": ["high", "critical", "unknown"],
        "forbidden_licenses": ["AGPL-3.0", "GPL-3.0-only", "SSPL-1.0"],
    }


def test_f22b_workflow_uses_pinned_actions_and_immutable_trivy_image():
    workflow = WORKFLOW.read_text(encoding="utf-8")
    uses = re.findall(r"uses:\s*([^\s]+)", workflow)
    assert uses
    assert all(re.search(r"@[0-9a-f]{40}$", value) for value in uses)
    assert "--self-check" in workflow
    assert "--require-runtime" in workflow
    assert "pip-audit==2.10.1" in workflow
    assert "bandit==1.9.4" in workflow
    assert "detect-secrets==1.5.0" in workflow
    assert "run_rc0810_f22b_security.py" in workflow
    assert "cffe3f5161a47a6823fbd23d985795b3ed72a4c806da4c4df16266c02accdd6f" in json.loads(POLICY.read_text(encoding="utf-8"))["tool_images"]["trivy"]


def test_f22b_workflow_publishes_raw_runtime_evidence_with_immutable_name():
    workflow = WORKFLOW.read_text(encoding="utf-8")
    policy = json.loads(POLICY.read_text(encoding="utf-8"))
    upload_sha = policy["action_commits"]["actions/upload-artifact"]
    assert f"actions/upload-artifact@{upload_sha}" in workflow
    assert "if: always()" in workflow
    assert "name: rc0810-f22b-${{ github.sha }}-${{ github.run_id }}" in workflow
    assert "include-hidden-files: true" in workflow
    assert ".codex_tmp/rc0810/security/f22b/" in workflow
    assert "docs/02_专项进度与验收/rc0810_f22b_security_gate.json" in workflow
    assert "--platform linux/amd64" in workflow
    assert "--provenance=mode=max" in workflow
    assert "org.opencontainers.image.revision=${GITHUB_SHA}" in workflow
    assert "name: rc0810-registry-evidence-${{ github.sha }}-${{ github.run_id }}" in workflow


def test_f22b_container_sbom_license_complete_but_attestation_blocks_production():
    gate = json.loads(BASELINE.read_text(encoding="utf-8"))
    assert gate["container_scan"]["status"] == "completed"
    assert gate["sbom_status"]["status"] == "completed"
    assert gate["license_status"]["status"] == "completed"
    assert gate["supply_chain_attestation"]["status"] == "pending_external"
    assert gate["supply_chain_attestation"]["production_blocking"] is True
    assert gate["production_gate_eligible"] is False


def test_f22b_registry_freezes_exact_scope_and_phase_without_business_changes():
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    unit = next(item for item in registry["execution_units"] if item["id"] == "RC0810-F22-B")
    task = next(item for item in registry["tasks"] if item["id"] == "RC0810-F22")
    assert unit["dependencies"] == ["RC0810-F21", "RC0810-F22-A"]
    assert task["subtasks"] == [{"id": f"F22.{index}", "default_status": "pending"} for index in range(1, 9)]
    assert task["change_budget"]["expected_files"] == 14
    assert all(not path.startswith("backend/") or path.endswith("test_rc0810_f22.py") for path in task["allowed_files"])
    assert [item["expected_test_count"] for item in task["acceptance_commands"]] == [12, 29, 1, 1, 1]
