"""Validate the current F22-B gate while retaining F22-A audit compatibility."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from run_rc0810_f22_scans import (  # noqa: E402
    build_blocking_findings,
    parse_json,
    security_source_snapshot,
    sha256_git_blob,
    summarize,
    validate_report_payload,
)
from run_rc0810_f22b_security import docker_context_unchanged  # noqa: E402


SCHEMA_PATH = ROOT / "config" / "rc0810" / "security_gate.schema.json"
POLICY_PATH = ROOT / "config" / "rc0810" / "security_gate_policy.json"
EXCEPTIONS_PATH = ROOT / "config" / "rc0810" / "security_exception_registry.json"
BASELINE_PATH = ROOT / "docs" / "02_专项进度与验收" / "rc0810_f22b_security_gate.json"
LEGACY_BASELINE_PATH = ROOT / "docs" / "02_专项进度与验收" / "rc0810_f22a_security_baseline.json"
EXPECTED_INPUTS = (
    "backend/requirements.txt",
    "analysis/profiling/requirements.txt",
    "analysis/text_analysis/requirements.txt",
    "apps/web/package-lock.json",
    "Dockerfile",
    "config/rc0810/database_profiles.json",
    "config/rc0810/detect_secrets.baseline.json",
)
EXPECTED_TOOLS = {"bandit", "detect-secrets", "npm-audit", "pip-audit"}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_bytes(*args: str) -> bytes:
    completed = subprocess.run(
        ["git", *args], cwd=ROOT, capture_output=True, check=False
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.decode("utf-8", errors="replace"))
    return completed.stdout


def source_binding_errors(
    gate: dict[str, Any], source: dict[str, str]
) -> list[str]:
    """Validate frozen source while permitting later release-evidence commits."""

    errors: list[str] = []
    for field, label in (
        ("source_tree", "source_tree_mismatch"),
        ("source_manifest_sha256", "source_manifest_mismatch"),
    ):
        if gate.get(field) != source[field]:
            errors.append(label)
    recorded_head = gate.get("head")
    recorded_tree = gate.get("head_tree")
    if not isinstance(recorded_head, str) or not isinstance(recorded_tree, str):
        return [*errors, "head_binding_mismatch"]
    try:
        git_bytes("merge-base", "--is-ancestor", recorded_head, "HEAD")
        actual_tree = git_bytes(
            "rev-parse", f"{recorded_head}^{{tree}}"
        ).decode("ascii").strip()
        expected_diff = git_bytes(
            "diff-tree", "--binary", "--no-ext-diff", recorded_tree,
            str(gate.get("source_tree")),
        )
    except RuntimeError:
        errors.append("head_binding_mismatch")
        return errors
    if recorded_tree != actual_tree:
        errors.append("head_binding_mismatch")
    if gate.get("dirty_diff_sha256") != hashlib.sha256(expected_diff).hexdigest():
        errors.append("dirty_diff_mismatch")
    return errors


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def validate_exceptions(
    exceptions: dict[str, Any],
    schema: dict[str, Any],
    captured_at: str,
    *,
    baseline: dict[str, Any] | None = None,
    policy: dict[str, Any] | None = None,
) -> list[str]:
    errors: list[str] = []
    if exceptions.get("schema") != "safehome.rc0810.security-exceptions.v1":
        errors.append("exception_registry_schema_invalid")
    if exceptions.get("automation_may_approve") is not False:
        errors.append("exception_automation_approval_forbidden")
    exception_schema = schema["$defs"]["exception"]
    validator = Draft202012Validator(
        exception_schema,
        resolver=Draft202012Validator(schema).resolver,
        format_checker=FormatChecker(),
    )
    seen: set[str] = set()
    captured = parse_time(captured_at)
    trusted_reviewers = set(
        (policy or {}).get("exception_policy", {}).get(
            "trusted_exception_reviewers", []
        )
    )
    bound_findings = {
        (str(item.get("finding_id", "")), str(item.get("fingerprint", "")))
        for item in (baseline or {}).get("blocking_findings", [])
        if isinstance(item, dict)
    }
    for item in exceptions.get("exceptions", []):
        for problem in validator.iter_errors(item):
            errors.append(f"exception_schema:{problem.message}")
        finding_id = str(item.get("finding_id", ""))
        if finding_id in seen:
            errors.append("duplicate_exception_finding")
        seen.add(finding_id)
        try:
            created = parse_time(item["created_at"])
            expires = parse_time(item["expires_at"])
            if expires <= captured or expires <= created:
                errors.append("expired_exception")
            if (expires - created).days > 30:
                errors.append("exception_too_long")
        except (KeyError, TypeError, ValueError):
            errors.append("exception_time_invalid")
        if str(item.get("reviewer_id", "")).lower() in {"", "automation", "runner", "self"}:
            errors.append("exception_reviewer_not_independent")
        if str(item.get("owner", "")).strip().casefold() == str(
            item.get("reviewer_id", "")
        ).strip().casefold():
            errors.append("exception_self_approval_forbidden")
        if item.get("reviewer_id") not in trusted_reviewers:
            errors.append("exception_reviewer_untrusted")
        if (finding_id, str(item.get("fingerprint", ""))) not in bound_findings:
            errors.append("exception_finding_not_bound")
    return errors


def normalized(value: Any) -> str:
    return str(value).replace("\\", "/")


def contract_arg(value: Any) -> str:
    result = normalized(value)
    marker = result.rfind("/.codex_tmp/")
    return result[marker:] if marker >= 0 else result


def python_command(argv: list[Any], module: str, tail: list[str]) -> bool:
    if len(argv) != 3 + len(tail):
        return False
    executable = normalized(argv[0]).rsplit("/", 1)[-1].lower()
    return executable.startswith("python") and argv[1:3] == ["-m", module] and [
        contract_arg(item) for item in argv[3:]
    ] == tail


def report_contract_errors(
    report: dict[str, Any], baseline: dict[str, Any], policy: dict[str, Any], *, negative: bool = False
) -> list[str]:
    errors: list[str] = []
    tool = str(report.get("tool", ""))
    source_tree = str(baseline.get("source_tree", ""))
    phase_slug = "f22b" if baseline.get("phase") == "F22-B" else "f22a"
    prefix = f"/.codex_tmp/rc0810/security/{phase_slug}/{source_tree}"
    filename = f"negative-{tool}.json" if negative else f"{tool}.json"
    if not normalized(report.get("path", "")).endswith(f"{prefix}/reports/{filename}"):
        errors.append("path")
    if report.get("version") != policy.get("tools", {}).get(tool):
        errors.append("version")
    if report.get("source_tree") != source_tree:
        errors.append("source_tree")
    expected_captured_at = baseline.get("source_scan_captured_at", baseline.get("captured_at"))
    if report.get("captured_at") != expected_captured_at:
        errors.append("captured_at")
    allowed_exit_codes = {"detect-secrets": {0}, "bandit": {0, 1}, "pip-audit": {0, 1}, "npm-audit": {0, 1}}
    if report.get("exit_code") not in allowed_exit_codes.get(tool, set()):
        errors.append("exit_code")
    argv = report.get("command")
    if not isinstance(argv, list):
        errors.append("command")
        return errors
    staging = f"{prefix}/staging"
    fixture = f"{prefix}/negative-fixtures"
    valid_command = False
    if negative and tool == "detect-secrets":
        valid_command = python_command(
            argv, "detect_secrets", ["scan", "--all-files", f"{fixture}/fake-secret.txt"]
        )
    elif negative and tool == "bandit":
        valid_command = python_command(
            argv, "bandit", ["-r", f"{fixture}/dangerous.py", "-f", "json"]
        )
    elif negative and tool == "pip-audit":
        normalized_argv = [normalized(argv[0]), *[contract_arg(item) for item in argv[1:]]]
        valid_command = (
            len(normalized_argv) == 15
            and normalized_argv[0].rsplit("/", 1)[-1].lower().startswith("python")
            and normalized_argv[1:14] == [
                "-m", "pip_audit", "-r", f"{fixture}/requirements.txt",
                "--format", "json", "--progress-spinner", "off",
                "--no-deps", "--disable-pip", "--vulnerability-service", "osv", "--osv-url",
            ]
            and re.fullmatch(r"http://127\.0\.0\.1:\d+/v1/query", normalized_argv[14]) is not None
        )
    elif not negative and tool == "detect-secrets":
        valid_command = python_command(
            argv,
            "detect_secrets",
            [
                "scan",
                "--exclude-files",
                contract_arg(r"config[\\/]rc0810[\\/]detect_secrets\.baseline\.json$"),
                "--all-files",
                staging,
            ],
        )
    elif not negative and tool == "bandit":
        valid_command = python_command(
            argv,
            "bandit",
            ["-r", f"{staging}/backend", f"{staging}/scripts", f"{staging}/analysis", "-f", "json"],
        )
    elif not negative and tool == "pip-audit":
        valid_command = python_command(
            argv,
            "pip_audit",
            [
                "-r", f"{staging}/backend/requirements.txt",
                "-r", f"{staging}/analysis/profiling/requirements.txt",
                "-r", f"{staging}/analysis/text_analysis/requirements.txt",
                "--format", "json", "--progress-spinner", "off",
            ],
        )
    elif not negative and tool == "npm-audit":
        executable = normalized(argv[0]).rsplit("/", 1)[-1].lower() if argv else ""
        valid_command = executable in {"npm", "npm.cmd"} and argv[1:] == [
            "audit", "--json", "--package-lock-only"
        ]
    if not valid_command:
        errors.append("command")
    return errors


def verify_runtime_report(
    report: dict[str, Any], *, require_runtime: bool
) -> tuple[bool, Path | None, list[str]]:
    errors: list[str] = []
    path = Path(str(report.get("path", "")))
    if not path.is_file():
        if require_runtime:
            errors.append("runtime_report_missing")
        return False, None, errors
    if sha256_file(path) != report.get("sha256"):
        errors.append("runtime_report_hash_mismatch")
        return False, None, errors
    if path.stat().st_size != report.get("bytes"):
        errors.append("runtime_report_size_mismatch")
        return False, None, errors
    try:
        payload = parse_json(path)
        validate_report_payload(str(report.get("tool", "")), payload)
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        errors.append("runtime_report_parse_failed")
        return False, None, errors
    return True, path, errors


def blocking_count(summary: dict[str, int]) -> int:
    return (
        int(summary.get("secret", 0))
        + int(summary.get("sast_high", 0))
        + int(summary.get("python_vulnerability", 0))
        + int(summary.get("node_critical", 0))
        + int(summary.get("node_high", 0))
    )


def finding_is_blocking(category: str, severity: str, policy: dict[str, Any]) -> bool:
    gate_key = "dependency" if category in {"python_dependency", "node_dependency"} else category
    return severity in policy["severity_gate"].get(gate_key, [])


def trivy_summary(payload: dict[str, Any]) -> dict[str, int]:
    summary = {"critical": 0, "high": 0, "secret": 0}
    for result in payload.get("Results", []):
        if not isinstance(result, dict):
            continue
        for finding in result.get("Vulnerabilities") or []:
            severity = str(finding.get("Severity", "")).lower()
            if severity in {"critical", "high"}:
                summary[severity] += 1
        summary["secret"] += len(result.get("Secrets") or [])
    return summary


def trivy_license_names(payload: dict[str, Any]) -> list[str]:
    names: set[str] = set()
    for result in payload.get("Results", []):
        if not isinstance(result, dict):
            continue
        for item in result.get("Licenses") or []:
            if isinstance(item, dict) and item.get("Name"):
                names.add(str(item["Name"]))
    return sorted(names)


def validate_f22b(
    gate: dict[str, Any],
    *,
    require_runtime: bool,
    policy: dict[str, Any],
    schema: dict[str, Any],
    exceptions: dict[str, Any],
) -> dict[str, Any]:
    errors: list[str] = []
    required = {
        "schema", "phase", "captured_at", "source_scan_captured_at", "head",
        "head_tree", "source_tree", "dirty_diff_sha256", "source_manifest_sha256",
        "policy_sha256", "exception_registry_sha256", "dependency_inputs",
        "action_inputs", "source_reports", "negative_gate_evidence",
        "blocking_findings", "finding_summary", "source_open_gate_findings",
        "container_scan", "sbom_status", "license_status",
        "supply_chain_attestation", "open_gate_findings",
        "production_gate_eligible", "status",
    }
    if set(gate) != required:
        errors.append("f22b_contract_fields_invalid")
    if gate.get("schema") != "safehome.rc0810.security-gate.v2" or gate.get("phase") != "F22-B":
        errors.append("f22b_schema_invalid")

    source = security_source_snapshot()
    errors.extend(source_binding_errors(gate, source))
    if gate.get("policy_sha256") != sha256_git_blob(
        source["source_tree"], POLICY_PATH.relative_to(ROOT).as_posix()
    ):
        errors.append("policy_hash_mismatch")
    if gate.get("exception_registry_sha256") != sha256_git_blob(
        source["source_tree"], EXCEPTIONS_PATH.relative_to(ROOT).as_posix()
    ):
        errors.append("exception_registry_hash_mismatch")
    current_inputs = {
        item: sha256_git_blob(source["source_tree"], item)
        for item in EXPECTED_INPUTS
    }
    if gate.get("dependency_inputs") != current_inputs:
        errors.append("dependency_input_mismatch")
    action_paths = (".github/workflows/security-gate.yml", ".github/workflows/check.yml")
    current_actions = {
        item: sha256_git_blob(source["source_tree"], item)
        for item in action_paths
    }
    if gate.get("action_inputs") != current_actions:
        errors.append("action_input_mismatch")
    errors.extend(validate_exceptions(exceptions, schema, gate.get("captured_at", ""), baseline=gate, policy=policy))
    if policy.get("phase") != "F22-B" or policy.get("production_release_approved") is not False:
        errors.append("policy_must_not_approve_production")

    source_reports = gate.get("source_reports", [])
    tools = [str(item.get("tool", "")) for item in source_reports if isinstance(item, dict)]
    contract_valid = len(source_reports) == 4 and set(tools) == EXPECTED_TOOLS and len(tools) == len(set(tools))
    report_paths: dict[str, Path] = {}
    runtime_verified = contract_valid
    if not contract_valid:
        errors.append("runtime_report_contract_invalid")
    for report in source_reports:
        if not isinstance(report, dict) or report_contract_errors(report, gate, policy):
            contract_valid = False
            runtime_verified = False
            if "runtime_report_contract_invalid" not in errors:
                errors.append("runtime_report_contract_invalid")
            continue
        valid, path, report_errors = verify_runtime_report(report, require_runtime=require_runtime)
        errors.extend(report_errors)
        runtime_verified = runtime_verified and valid
        if path is not None:
            report_paths[str(report.get("tool"))] = path
    if runtime_verified and len(report_paths) == 4:
        try:
            if summarize(report_paths) != gate.get("finding_summary"):
                errors.append("runtime_summary_mismatch")
            if build_blocking_findings(report_paths, str(gate.get("source_tree", ""))) != gate.get("blocking_findings"):
                errors.append("runtime_blocking_finding_index_mismatch")
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            errors.append("runtime_report_parse_failed")
            runtime_verified = False
    if blocking_count(gate.get("finding_summary", {})) != gate.get("source_open_gate_findings"):
        errors.append("gate_finding_count_mismatch")
    if len(gate.get("blocking_findings", [])) != gate.get("source_open_gate_findings"):
        errors.append("blocking_finding_index_count_mismatch")

    negative = gate.get("negative_gate_evidence", {})
    negative_reports = negative.get("reports", []) if isinstance(negative, dict) else []
    negative_tools = [str(item.get("tool", "")) for item in negative_reports if isinstance(item, dict)]
    expected_checks = {
        "fake_secret_fixture_rejected": True,
        "high_sast_fixture_rejected": True,
        "high_dependency_fixture_rejected": True,
    }
    if (
        not isinstance(negative, dict)
        or negative.get("source_tree") != gate.get("source_tree")
        or set(negative_tools) != {"detect-secrets", "bandit", "pip-audit"}
        or len(negative_tools) != 3
        or negative.get("checks") != expected_checks
    ):
        errors.append("negative_gate_evidence_invalid")
    for report in negative_reports:
        if not isinstance(report, dict) or report_contract_errors(report, gate, policy, negative=True):
            if "negative_gate_evidence_invalid" not in errors:
                errors.append("negative_gate_evidence_invalid")
            continue
        valid, _, report_errors = verify_runtime_report(report, require_runtime=require_runtime)
        errors.extend(report_errors)
        runtime_verified = runtime_verified and valid

    evidence_payloads: dict[str, dict[str, Any]] = {}
    for key, expected_tool in (
        ("container_scan", "trivy-container"),
        ("sbom_status", "trivy-sbom"),
        ("license_status", "trivy-license"),
    ):
        section = gate.get(key, {})
        report = section.get("report", {}) if isinstance(section, dict) else {}
        if (
            section.get("status") != "completed"
            or report.get("tool") != expected_tool
            or report.get("version") != policy.get("tools", {}).get("trivy")
            or report.get("source_tree") != gate.get("source_tree")
            or report.get("captured_at") != gate.get("captured_at")
            or report.get("exit_code") != 0
            or not str(report.get("path", "")).replace("\\", "/").endswith(
                f"/.codex_tmp/rc0810/security/f22b/{gate.get('source_tree')}/reports/"
                + {"container_scan": "trivy-container.json", "sbom_status": "trivy-sbom.cdx.json", "license_status": "trivy-license.json"}[key]
            )
            or f"aquasec/trivy@{policy.get('tool_images', {}).get('trivy')}" not in report.get("command", [])
        ):
            errors.append(f"{key}_contract_invalid")
            continue
        path = Path(str(report.get("path", "")))
        if path.is_file():
            if sha256_file(path) != report.get("sha256") or path.stat().st_size != report.get("bytes"):
                errors.append("runtime_report_hash_mismatch")
                continue
            try:
                evidence_payloads[key] = load_json(path)
            except (OSError, ValueError, TypeError, json.JSONDecodeError):
                errors.append("runtime_report_parse_failed")
        elif require_runtime:
            errors.append("runtime_report_missing")

    container = gate.get("container_scan", {})
    expected_image = f"aquasec/trivy@{policy.get('tool_images', {}).get('trivy')}"
    if (
        re.fullmatch(r"sha256:[0-9a-f]{64}", str(container.get("image_id", ""))) is None
        or container.get("tool_image") != expected_image
    ):
        errors.append("container_image_binding_invalid")
    container_summary = container.get("finding_summary", {})
    container_open = sum(int(container_summary.get(key, 0)) for key in ("critical", "high", "secret"))
    if container.get("production_blocking") is not (container_open > 0):
        errors.append("container_gate_status_invalid")
    if "container_scan" in evidence_payloads and trivy_summary(evidence_payloads["container_scan"]) != container_summary:
        errors.append("container_summary_mismatch")

    sbom = gate.get("sbom_status", {})
    if sbom.get("format") != "CycloneDX" or sbom.get("production_blocking") is not False:
        errors.append("sbom_contract_invalid")
    if "sbom_status" in evidence_payloads:
        payload = evidence_payloads["sbom_status"]
        if payload.get("bomFormat") != "CycloneDX" or len(payload.get("components") or []) != sbom.get("component_count"):
            errors.append("sbom_summary_mismatch")

    licenses = gate.get("license_status", {})
    forbidden = sorted(set(licenses.get("observed_licenses", [])) & set(policy["severity_gate"]["forbidden_licenses"]))
    if forbidden != licenses.get("forbidden_licenses_found") or licenses.get("production_blocking") is not bool(forbidden):
        errors.append("license_gate_status_invalid")
    if "license_status" in evidence_payloads and trivy_license_names(evidence_payloads["license_status"]) != licenses.get("observed_licenses"):
        errors.append("license_summary_mismatch")

    attestation = gate.get("supply_chain_attestation", {})
    artifact_reuse = attestation.get("local_artifact_reuse")
    if artifact_reuse is not None:
        previous_tree = str(artifact_reuse.get("from_source_tree", ""))
        if (
            re.fullmatch(r"[0-9a-f]{40}", previous_tree) is None
            or artifact_reuse.get("docker_context_unchanged") is not True
            or not docker_context_unchanged(
                previous_tree, str(gate.get("source_tree", ""))
            )
        ):
            errors.append("artifact_reuse_binding_invalid")
    if (
        attestation.get("status") != "pending_external"
        or attestation.get("production_blocking") is not True
        or attestation.get("runner") != "ubuntu-24.04"
        or attestation.get("action_commits") != policy.get("action_commits")
        or attestation.get("trivy_image_digest") != policy.get("tool_images", {}).get("trivy")
    ):
        errors.append("supply_chain_attestation_invalid")
    expected_open = int(gate.get("source_open_gate_findings", 0)) + container_open + len(forbidden)
    if gate.get("open_gate_findings") != expected_open:
        errors.append("open_gate_finding_total_invalid")
    expected_status = "rescan_complete_no_go" if expected_open else "attestation_pending_no_go"
    if gate.get("production_gate_eligible") is not False or gate.get("status") != expected_status:
        errors.append("production_gate_must_remain_closed")

    if require_runtime and not errors and artifact_reuse is None:
        completed = subprocess.run(
            ["docker", "image", "inspect", str(container.get("image_tag", "")), "--format", "{{.Id}}"],
            cwd=ROOT, capture_output=True, text=True, check=False,
        )
        if completed.returncode != 0 or completed.stdout.strip() != container.get("image_id"):
            errors.append("runtime_image_binding_mismatch")
    return {
        "valid": not errors,
        "status": expected_status if not errors else "invalid",
        "phase": "F22-B",
        "source_tree": gate.get("source_tree"),
        "runtime_reports_verified": runtime_verified and len(evidence_payloads) == 3,
        "finding_summary": gate.get("finding_summary", {}),
        "open_gate_findings": gate.get("open_gate_findings"),
        "container_status": container.get("status"),
        "sbom_status": sbom.get("status"),
        "license_status": licenses.get("status"),
        "production_gate_eligible": False,
        "errors": list(dict.fromkeys(errors)),
    }


def validate_baseline(
    baseline_path: Path = BASELINE_PATH, *, require_runtime: bool = False
) -> dict[str, Any]:
    errors: list[str] = []
    try:
        baseline = load_json(baseline_path)
        schema = load_json(SCHEMA_PATH)
        policy = load_json(POLICY_PATH)
        exceptions = load_json(EXCEPTIONS_PATH)
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        return {
            "valid": False,
            "status": "invalid",
            "phase": "F22-A",
            "production_gate_eligible": False,
            "errors": [f"definition_missing_or_invalid:{exc}"],
        }

    if baseline.get("phase") == "F22-B":
        return validate_f22b(
            baseline,
            require_runtime=require_runtime,
            policy=policy,
            schema=schema,
            exceptions=exceptions,
        )

    for problem in Draft202012Validator(
        schema, format_checker=FormatChecker()
    ).iter_errors(baseline):
        errors.append(f"baseline_schema:{problem.message}")

    source = security_source_snapshot()
    if baseline.get("source_tree") != source["source_tree"]:
        errors.append("source_tree_mismatch")
    if baseline.get("dirty_diff_sha256") != source["dirty_diff_sha256"]:
        errors.append("dirty_diff_mismatch")
    if baseline.get("source_manifest_sha256") != source["source_manifest_sha256"]:
        errors.append("source_manifest_mismatch")
    if baseline.get("head") != source["head"] or baseline.get("head_tree") != source["head_tree"]:
        errors.append("head_binding_mismatch")

    if baseline.get("policy_sha256") != sha256_git_blob(
        source["source_tree"], POLICY_PATH.relative_to(ROOT).as_posix()
    ):
        errors.append("policy_hash_mismatch")
    if baseline.get("exception_registry_sha256") != sha256_git_blob(
        source["source_tree"], EXCEPTIONS_PATH.relative_to(ROOT).as_posix()
    ):
        errors.append("exception_registry_hash_mismatch")
    current_inputs = {
        item: sha256_git_blob(source["source_tree"], item)
        for item in EXPECTED_INPUTS
    }
    if baseline.get("dependency_inputs") != current_inputs:
        errors.append("dependency_input_mismatch")

    errors.extend(
        validate_exceptions(
            exceptions,
            schema,
            baseline.get("captured_at", ""),
            baseline=baseline,
            policy=policy,
        )
    )
    if policy.get("production_release_approved") is not False:
        errors.append("policy_must_not_approve_production")
    if baseline.get("production_gate_eligible") is not False:
        errors.append("baseline_must_not_approve_production")
    if blocking_count(baseline.get("finding_summary", {})) != baseline.get(
        "open_gate_findings"
    ):
        errors.append("gate_finding_count_mismatch")
    if len(baseline.get("blocking_findings", [])) != baseline.get(
        "open_gate_findings"
    ):
        errors.append("blocking_finding_index_count_mismatch")

    raw_reports = baseline.get("raw_reports", [])
    raw_tools = [str(item.get("tool", "")) for item in raw_reports if isinstance(item, dict)]
    contract_valid = len(raw_reports) == 4 and set(raw_tools) == EXPECTED_TOOLS and len(raw_tools) == len(set(raw_tools))
    if not contract_valid:
        errors.append("runtime_report_contract_invalid")
    for report in raw_reports:
        if not isinstance(report, dict) or report_contract_errors(report, baseline, policy):
            contract_valid = False
            if "runtime_report_contract_invalid" not in errors:
                errors.append("runtime_report_contract_invalid")

    runtime_verified = contract_valid
    report_paths: dict[str, Path] = {}
    for report in raw_reports:
        if not isinstance(report, dict):
            runtime_verified = False
            continue
        valid_report, path, report_errors = verify_runtime_report(
            report, require_runtime=require_runtime
        )
        errors.extend(report_errors)
        runtime_verified = runtime_verified and valid_report
        if path is not None:
            report_paths[str(report.get("tool"))] = path
    if runtime_verified and len(report_paths) == 4:
        try:
            if summarize(report_paths) != baseline.get("finding_summary"):
                errors.append("runtime_summary_mismatch")
                runtime_verified = False
            if build_blocking_findings(
                report_paths, str(baseline.get("source_tree", ""))
            ) != baseline.get("blocking_findings"):
                errors.append("runtime_blocking_finding_index_mismatch")
                runtime_verified = False
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            errors.append("runtime_report_parse_failed")
            runtime_verified = False
    elif require_runtime:
        runtime_verified = False

    negative = baseline.get("negative_gate_evidence", {})
    negative_reports = negative.get("reports", []) if isinstance(negative, dict) else []
    negative_tools = [str(item.get("tool", "")) for item in negative_reports if isinstance(item, dict)]
    if (
        not isinstance(negative, dict)
        or negative.get("source_tree") != baseline.get("source_tree")
        or set(negative_tools) != {"detect-secrets", "bandit", "pip-audit"}
        or len(negative_tools) != 3
        or len(set(negative_tools)) != 3
        or negative.get("checks") != {
            "fake_secret_fixture_rejected": True,
            "high_sast_fixture_rejected": True,
            "high_dependency_fixture_rejected": True,
        }
    ):
        errors.append("negative_gate_evidence_invalid")
        runtime_verified = False
    negative_payloads: dict[str, Any] = {}
    for report in negative_reports:
        if not isinstance(report, dict) or report_contract_errors(report, baseline, policy, negative=True):
            if "negative_gate_evidence_invalid" not in errors:
                errors.append("negative_gate_evidence_invalid")
            runtime_verified = False
            continue
        valid_report, path, report_errors = verify_runtime_report(report, require_runtime=require_runtime)
        errors.extend(report_errors)
        runtime_verified = runtime_verified and valid_report
        if path is not None:
            negative_payloads[str(report.get("tool"))] = parse_json(path)
    if len(negative_payloads) == 3:
        observed_checks = {
            "fake_secret_fixture_rejected": sum(
                len(items) for items in negative_payloads["detect-secrets"]["results"].values()
            ) > 0,
            "high_sast_fixture_rejected": any(
                str(item.get("issue_severity", "")).upper() == "HIGH"
                for item in negative_payloads["bandit"]["results"]
            ),
            "high_dependency_fixture_rejected": any(
                item.get("vulns") for item in negative_payloads["pip-audit"]["dependencies"]
            ),
        }
        if observed_checks != negative.get("checks"):
            errors.append("negative_gate_evidence_invalid")
            runtime_verified = False
    if exceptions.get("exceptions") and not runtime_verified:
        errors.append("exception_requires_runtime_reports")

    return {
        "valid": not errors,
        "status": "frozen_security_baseline" if not errors else "invalid",
        "phase": "F22-A",
        "source_tree": baseline.get("source_tree"),
        "runtime_reports_verified": runtime_verified,
        "finding_summary": baseline.get("finding_summary", {}),
        "open_gate_findings": baseline.get("open_gate_findings"),
        "container_status": baseline.get("container_scan", {}).get("status"),
        "sbom_status": baseline.get("sbom_status", {}).get("status"),
        "license_status": baseline.get("license_status", {}).get("status"),
        "production_gate_eligible": False,
        "errors": errors,
    }


def run_self_checks() -> dict[str, bool]:
    baseline = load_json(BASELINE_PATH)
    policy = load_json(POLICY_PATH)
    schema = load_json(SCHEMA_PATH)
    expired = {
        "schema": "safehome.rc0810.security-exceptions.v1",
        "automation_may_approve": False,
        "exceptions": [
            {
                "finding_id": "SELF-CHECK",
                "fingerprint": "0" * 64,
                "owner": "security-owner",
                "reason": "self check expired exception",
                "compensating_control": "self check compensating control",
                "created_at": "2026-08-01T00:00:00+00:00",
                "expires_at": "2026-08-02T00:00:00+00:00",
                "review_status": "approved",
                "reviewer_id": "independent-security-reviewer",
            }
        ],
    }
    expired_errors = validate_exceptions(
        expired,
        schema,
        baseline["captured_at"],
        baseline=baseline,
        policy=policy,
    )
    self_approved = copy.deepcopy(expired)
    self_approved["exceptions"][0]["expires_at"] = "2026-08-20T00:00:00+00:00"
    self_approved["exceptions"][0]["owner"] = "same-person"
    self_approved["exceptions"][0]["reviewer_id"] = "same-person"
    self_approved_errors = validate_exceptions(
        self_approved,
        schema,
        baseline["captured_at"],
        baseline=baseline,
        policy=policy,
    )
    stale = copy.deepcopy(baseline)
    report_key = "source_reports" if baseline.get("phase") == "F22-B" else "raw_reports"
    stale[report_key][0]["sha256"] = "0" * 64
    with tempfile.TemporaryDirectory(prefix="rc0810-f22-self-check-") as directory:
        phase_slug = "f22b" if baseline.get("phase") == "F22-B" else "f22a"
        runtime_report = (
            Path(directory)
            / ".codex_tmp"
            / "rc0810"
            / "security"
            / phase_slug
            / baseline["source_tree"]
            / "reports"
            / Path(stale[report_key][0]["path"]).name
        )
        runtime_report.parent.mkdir(parents=True)
        runtime_report.write_text("{}", encoding="utf-8")
        stale[report_key][0]["path"] = str(runtime_report)
        stale_path = Path(directory) / "stale.json"
        stale_path.write_text(json.dumps(stale), encoding="utf-8")
        stale_result = validate_baseline(stale_path)
    checks = {
        "expired_exception_rejected": "expired_exception" in expired_errors,
        "fake_secret_fixture_rejected": baseline.get("negative_gate_evidence", {}).get("checks", {}).get("fake_secret_fixture_rejected") is True,
        "high_dependency_fixture_rejected": baseline.get("negative_gate_evidence", {}).get("checks", {}).get("high_dependency_fixture_rejected") is True,
        "high_sast_fixture_rejected": baseline.get("negative_gate_evidence", {}).get("checks", {}).get("high_sast_fixture_rejected") is True,
        "self_approved_exception_rejected": "exception_self_approval_forbidden" in self_approved_errors,
        "untrusted_reviewer_rejected": "exception_reviewer_untrusted" in self_approved_errors,
        "unknown_finding_rejected": "exception_finding_not_bound" in self_approved_errors,
        "stale_report_rejected": (
            not stale_result["valid"]
            and "runtime_report_hash_mismatch" in stale_result["errors"]
        ),
    }
    if baseline.get("phase") == "F22-B":
        container = copy.deepcopy(baseline)
        container["container_scan"]["finding_summary"]["critical"] += 1
        container["container_scan"]["production_blocking"] = False
        license_gate = copy.deepcopy(baseline)
        forbidden_license = policy["severity_gate"]["forbidden_licenses"][0]
        license_gate["license_status"]["observed_licenses"].append(forbidden_license)
        attestation = copy.deepcopy(baseline)
        attestation["supply_chain_attestation"]["status"] = "completed"
        with tempfile.TemporaryDirectory(prefix="rc0810-f22b-gates-") as directory:
            paths = []
            for name, payload in (
                ("container", container),
                ("license", license_gate),
                ("attestation", attestation),
            ):
                path = Path(directory) / f"{name}.json"
                path.write_text(json.dumps(payload), encoding="utf-8")
                paths.append(path)
            results = [validate_baseline(path) for path in paths]
        checks.update(
            {
                "critical_container_fixture_rejected": "container_gate_status_invalid" in results[0]["errors"],
                "forbidden_license_fixture_rejected": "license_gate_status_invalid" in results[1]["errors"],
                "missing_attestation_rejected": "supply_chain_attestation_invalid" in results[2]["errors"],
            }
        )
    return checks


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", type=Path, default=BASELINE_PATH)
    parser.add_argument("--require-runtime", action="store_true")
    parser.add_argument("--self-check", action="store_true")
    args = parser.parse_args()
    result = validate_baseline(args.baseline, require_runtime=args.require_runtime)
    if args.self_check and result["valid"]:
        checks = run_self_checks()
        result["self_checks"] = checks
        result["valid"] = all(checks.values())
        result["status"] = "self_check_passed" if result["valid"] else "invalid"
        if not result["valid"]:
            result["errors"].append("self_check_failed")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
