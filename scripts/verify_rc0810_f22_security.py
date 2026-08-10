"""Validate the F22-A security baseline and prove its gates fail closed."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
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
    summarize,
    validate_report_payload,
)


SCHEMA_PATH = ROOT / "config" / "rc0810" / "security_gate.schema.json"
POLICY_PATH = ROOT / "config" / "rc0810" / "security_gate_policy.json"
EXCEPTIONS_PATH = ROOT / "config" / "rc0810" / "security_exception_registry.json"
BASELINE_PATH = ROOT / "docs" / "02_专项进度与验收" / "rc0810_f22a_security_baseline.json"
EXPECTED_INPUTS = (
    "backend/requirements.txt",
    "analysis/profiling/requirements.txt",
    "analysis/text_analysis/requirements.txt",
    "apps/web/package-lock.json",
    "Dockerfile",
)
EXPECTED_TOOLS = {"bandit", "detect-secrets", "npm-audit", "pip-audit"}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


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
    marker = result.find("/.codex_tmp/")
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
    prefix = f"/.codex_tmp/rc0810/security/f22a/{source_tree}"
    filename = f"negative-{tool}.json" if negative else f"{tool}.json"
    if not normalized(report.get("path", "")).endswith(f"{prefix}/reports/{filename}"):
        errors.append("path")
    if report.get("version") != policy.get("tools", {}).get(tool):
        errors.append("version")
    if report.get("source_tree") != source_tree:
        errors.append("source_tree")
    if report.get("captured_at") != baseline.get("captured_at"):
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
            argv, "detect_secrets", ["scan", "--all-files", staging]
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

    if baseline.get("policy_sha256") != sha256_file(POLICY_PATH):
        errors.append("policy_hash_mismatch")
    if baseline.get("exception_registry_sha256") != sha256_file(EXCEPTIONS_PATH):
        errors.append("exception_registry_hash_mismatch")
    current_inputs = {item: sha256_file(ROOT / item) for item in EXPECTED_INPUTS}
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
    stale["raw_reports"][0]["sha256"] = "0" * 64
    with tempfile.TemporaryDirectory(prefix="rc0810-f22-self-check-") as directory:
        stale_path = Path(directory) / "stale.json"
        stale_path.write_text(json.dumps(stale), encoding="utf-8")
        stale_result = validate_baseline(stale_path)
    return {
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
