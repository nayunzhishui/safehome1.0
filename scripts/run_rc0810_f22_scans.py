"""Run the F22 source scanners against one immutable Git tree."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile
import re
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from run_rc0810 import collect_git_snapshot, load_registry  # noqa: E402


POLICY_PATH = ROOT / "config" / "rc0810" / "security_gate_policy.json"
EXCEPTIONS_PATH = ROOT / "config" / "rc0810" / "security_exception_registry.json"
SECRET_BASELINE_PATH = ROOT / "config" / "rc0810" / "detect_secrets.baseline.json"
BASELINE_PATH = ROOT / "docs" / "02_专项进度与验收" / "rc0810_f22a_security_baseline.json"
BASELINE_RELATIVE = BASELINE_PATH.relative_to(ROOT).as_posix()
F22B_GATE_PATH = ROOT / "docs" / "02_专项进度与验收" / "rc0810_f22b_security_gate.json"
SECURITY_REPORT_RELATIVES = (
    BASELINE_RELATIVE,
    F22B_GATE_PATH.relative_to(ROOT).as_posix(),
    "docs/02_专项进度与验收/rc0810_f25a_platform_baseline.json",
    "docs/02_专项进度与验收/rc0810_f25a_platform_baseline_current.json",
    "docs/02_专项进度与验收/rc0810_f25b_evidence.json",
    "docs/02_专项进度与验收/rc0810_f26_final_rc.json",
    "docs/02_专项进度与验收/rc0810_f26_final_rc.md",
    "docs/02_专项进度与验收/rc0810_required_ci_evidence.json",
    "docs/02_专项进度与验收/rc0810_wave_c_review_packet.json",
    "docs/02_专项进度与验收/rc0810_wave_c_review_decision.json",
)
DEFAULT_TOOLS = ROOT / ".codex_tmp" / "rc0810" / "security-tools"
DEFAULT_RUNTIME = ROOT / ".codex_tmp" / "rc0810" / "security" / "f22a"
PYTHON_REQUIREMENTS = (
    "backend/requirements.txt",
    "analysis/profiling/requirements.txt",
    "analysis/text_analysis/requirements.txt",
)


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def sha256_git_blob(tree: str, relative: str) -> str:
    """Hash tracked bytes so Windows and Linux validate the same input."""
    return sha256_bytes(git("cat-file", "blob", f"{tree}:{relative}"))


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def git(*args: str, env: dict[str, str] | None = None) -> bytes:
    completed = subprocess.run(
        ["git", *args], cwd=ROOT, env=env, capture_output=True, check=False
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.decode("utf-8", errors="replace"))
    return completed.stdout


def security_source_snapshot() -> dict[str, str]:
    """Return a real Git tree excluding self-referential tracked reports."""
    # Diagnostic security evidence must remain reproducible even when a human
    # review checkpoint has expired. The normal Harness loader still enforces
    # current review evidence before any task transition or release decision.
    registry = load_registry(require_current_review_evidence=False)
    current = collect_git_snapshot(registry)["git"]
    with tempfile.TemporaryDirectory(prefix="rc0810-f22-index-") as directory:
        index = Path(directory) / "index"
        env = os.environ.copy()
        env["GIT_INDEX_FILE"] = str(index)
        git("read-tree", current["source_tree"], env=env)
        for relative in SECURITY_REPORT_RELATIVES:
            subprocess.run(
                ["git", "update-index", "--force-remove", "--", relative],
                cwd=ROOT,
                env=env,
                capture_output=True,
                check=False,
            )
        source_tree = git("write-tree", env=env).decode("ascii").strip()
    manifest = git("ls-tree", "-r", "-z", source_tree)
    diff = git("diff-tree", "--binary", "--no-ext-diff", current["head_tree"], source_tree)
    return {
        "head": current["head"],
        "head_tree": current["head_tree"],
        "source_tree": source_tree,
        "dirty_diff_sha256": sha256_bytes(diff),
        "source_manifest_sha256": sha256_bytes(manifest),
    }


def run_command(
    argv: list[str], cwd: Path, env: dict[str, str], timeout: int
) -> tuple[int, bytes, bytes]:
    completed = subprocess.run(
        argv,
        cwd=cwd,
        env=env,
        capture_output=True,
        timeout=timeout,
        check=False,
    )
    return completed.returncode, completed.stdout, completed.stderr


def write_raw_report(path: Path, stdout: bytes, stderr: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if stdout.strip():
        path.write_bytes(stdout)
    else:
        path.write_bytes(
            canonical(
                {
                    "empty_stdout": True,
                    "stderr_sha256": sha256_bytes(stderr),
                    "stderr_bytes": len(stderr),
                }
            )
        )


def parse_json(path: Path) -> Any:
    text = path.read_text(encoding="utf-8-sig")
    starts = [index for token in ("{", "[") if (index := text.find(token)) >= 0]
    if not starts:
        raise ValueError(f"scanner report contains no JSON: {path}")
    payload_text = text[min(starts) :]
    value, end = json.JSONDecoder().raw_decode(payload_text)
    if payload_text[end:].strip():
        raise ValueError(f"scanner report contains trailing content: {path}")
    return value


def validate_report_payload(tool: str, payload: Any) -> None:
    if not isinstance(payload, dict):
        raise ValueError(f"{tool} report must be an object")
    if tool == "detect-secrets":
        results = payload.get("results")
        if not isinstance(results, dict) or not all(
            isinstance(path, str) and isinstance(items, list)
            for path, items in results.items()
        ):
            raise ValueError("detect-secrets report schema invalid")
    elif tool == "bandit":
        results = payload.get("results")
        if not isinstance(results, list) or not all(
            isinstance(item, dict)
            and str(item.get("issue_severity", "")).upper() in {"LOW", "MEDIUM", "HIGH"}
            for item in results
        ):
            raise ValueError("bandit report schema invalid")
    elif tool == "pip-audit":
        dependencies = payload.get("dependencies")
        if not isinstance(dependencies, list) or not all(
            isinstance(item, dict) and isinstance(item.get("vulns"), list)
            for item in dependencies
        ):
            raise ValueError("pip-audit report schema invalid")
    elif tool == "npm-audit":
        counts = payload.get("metadata", {}).get("vulnerabilities")
        if not isinstance(counts, dict) or not all(
            isinstance(counts.get(level), int)
            for level in ("critical", "high", "moderate", "low")
        ):
            raise ValueError("npm-audit report schema invalid")
    else:
        raise ValueError(f"unexpected scanner: {tool}")


def scanner_version(tool: str, env: dict[str, str]) -> str:
    commands = {
        "bandit": [sys.executable, "-m", "bandit", "--version"],
        "detect-secrets": [sys.executable, "-m", "detect_secrets", "--version"],
        "pip-audit": [sys.executable, "-m", "pip_audit", "--version"],
        "npm-audit": ["npm.cmd" if os.name == "nt" else "npm", "--version"],
    }
    code, stdout, stderr = run_command(commands[tool], ROOT, env, 30)
    if code != 0:
        raise RuntimeError(f"cannot query {tool} version: {stderr.decode(errors='replace')}")
    match = re.search(r"\d+\.\d+\.\d+", (stdout + stderr).decode("utf-8", errors="replace"))
    if not match:
        raise RuntimeError(f"cannot parse {tool} version")
    return match.group(0)


def reviewed_secret_keys() -> set[tuple[str, str, str]]:
    baseline = parse_json(SECRET_BASELINE_PATH)
    return {
        (
            normalized_source_path(item.get("filename") or filename),
            str(item.get("type", "")),
            str(item.get("hashed_secret", "")),
        )
        for filename, items in baseline.get("results", {}).items()
        for item in items
        if item.get("is_secret") is False
    }


def secret_is_reviewed(
    filename: str, item: dict[str, Any], reviewed: set[tuple[str, str, str]]
) -> bool:
    return item.get("is_secret") is False or (
        normalized_source_path(item.get("filename") or filename),
        str(item.get("type", "")),
        str(item.get("hashed_secret", "")),
    ) in reviewed


def summarize(report_paths: dict[str, Path]) -> dict[str, int]:
    secrets = parse_json(report_paths["detect-secrets"])
    bandit = parse_json(report_paths["bandit"])
    pip_audit = parse_json(report_paths["pip-audit"])
    npm_audit = parse_json(report_paths["npm-audit"])
    for tool, payload in (
        ("detect-secrets", secrets),
        ("bandit", bandit),
        ("pip-audit", pip_audit),
        ("npm-audit", npm_audit),
    ):
        validate_report_payload(tool, payload)
    reviewed = reviewed_secret_keys()
    secret_count = sum(
        1
        for filename, items in secrets.get("results", {}).items()
        for item in items
        if not secret_is_reviewed(filename, item, reviewed)
    )
    bandit_counts = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
    for finding in bandit.get("results", []):
        severity = str(finding.get("issue_severity", "")).upper()
        if severity in bandit_counts:
            bandit_counts[severity] += 1
    python_vulnerabilities = sum(
        len(item.get("vulns", [])) for item in pip_audit.get("dependencies", [])
    )
    npm_counts = npm_audit.get("metadata", {}).get("vulnerabilities", {})
    return {
        "secret": secret_count,
        "sast_high": bandit_counts["HIGH"],
        "sast_medium": bandit_counts["MEDIUM"],
        "sast_low": bandit_counts["LOW"],
        "python_vulnerability": python_vulnerabilities,
        "node_critical": int(npm_counts.get("critical", 0)),
        "node_high": int(npm_counts.get("high", 0)),
        "node_moderate": int(npm_counts.get("moderate", 0)),
        "node_low": int(npm_counts.get("low", 0)),
    }


def build_blocking_findings(
    report_paths: dict[str, Path], source_tree: str
) -> list[dict[str, str]]:
    secrets = parse_json(report_paths["detect-secrets"])
    bandit = parse_json(report_paths["bandit"])
    pip_audit = parse_json(report_paths["pip-audit"])
    npm_audit = parse_json(report_paths["npm-audit"])
    findings: list[dict[str, str]] = []

    def append(category: str, severity: str, identity: dict[str, Any]) -> None:
        fingerprint = sha256_bytes(canonical(identity))
        findings.append(
            {
                "finding_id": f"{category}:{fingerprint[:24]}",
                "category": category,
                "severity": severity,
                "fingerprint": fingerprint,
                "source_tree": source_tree,
            }
        )

    reviewed = reviewed_secret_keys()
    for filename, items in sorted(secrets["results"].items()):
        for item in items:
            if secret_is_reviewed(filename, item, reviewed):
                continue
            append(
                "secret",
                "unknown",
                {
                    "category": "secret",
                    "filename": normalized_source_path(item.get("filename") or filename),
                    "line_number": item.get("line_number"),
                    "type": item.get("type"),
                    "hashed_secret": item.get("hashed_secret"),
                },
            )
    for item in bandit["results"]:
        if str(item.get("issue_severity", "")).upper() != "HIGH":
            continue
        append(
            "sast",
            "high",
            {
                "category": "sast",
                "filename": normalized_source_path(item.get("filename")),
                "line_number": item.get("line_number"),
                "test_id": item.get("test_id"),
                "issue_text": item.get("issue_text"),
            },
        )
    for dependency in pip_audit["dependencies"]:
        for vulnerability in dependency.get("vulns", []):
            append(
                "python_dependency",
                "high",
                {
                    "category": "python_dependency",
                    "name": dependency.get("name"),
                    "version": dependency.get("version"),
                    "vulnerability": vulnerability.get("id"),
                },
            )
    for name, vulnerability in sorted(npm_audit.get("vulnerabilities", {}).items()):
        severity = str(vulnerability.get("severity", "")).lower()
        if severity not in {"high", "critical"}:
            continue
        append(
            "node_dependency",
            severity,
            {
                "category": "node_dependency",
                "name": name,
                "severity": severity,
                "via": vulnerability.get("via"),
            },
        )
    return sorted(findings, key=lambda item: (item["category"], item["finding_id"]))


def normalized_source_path(value: Any) -> str:
    result = str(value or "").replace("\\", "/")
    marker = result.find("/staging/")
    return result[marker + len("/staging/") :] if marker >= 0 else result


def run_negative_gate_fixtures(
    runtime: Path,
    env: dict[str, str],
    versions: dict[str, str],
    timeouts: dict[str, int],
    source_tree: str,
    captured_at: str,
) -> dict[str, Any]:
    fixture_root = runtime / "negative-fixtures"
    fixture_root.mkdir(parents=True, exist_ok=True)
    secret_fixture = fixture_root / "fake-secret.txt"
    secret_fixture.write_text("AKIA" + "A" * 16 + "\n", encoding="utf-8")
    sast_fixture = fixture_root / "dangerous.py"
    sast_fixture.write_text(
        "import subprocess\nvalue = input()\nsubprocess.Popen(value, shell=True)\n",
        encoding="utf-8",
    )
    dependency_fixture = fixture_root / "requirements.txt"
    dependency_fixture.write_text("urllib3==1.24.1\n", encoding="utf-8")
    reports_dir = runtime / "reports"
    commands = {
        "detect-secrets": [
            sys.executable,
            "-m",
            "detect_secrets",
            "scan",
            "--all-files",
            str(secret_fixture),
        ],
        "bandit": [
            sys.executable,
            "-m",
            "bandit",
            "-r",
            str(sast_fixture),
            "-f",
            "json",
        ],
    }
    reports: list[dict[str, Any]] = []
    payloads: dict[str, Any] = {}
    for tool, argv in commands.items():
        exit_code, stdout, stderr = run_command(
            argv, fixture_root, env, int(timeouts.get(tool, 600))
        )
        path = reports_dir / f"negative-{tool}.json"
        write_raw_report(path, stdout, stderr)
        payload = parse_json(path)
        validate_report_payload(tool, payload)
        payloads[tool] = payload
        reports.append(
            {
                "tool": tool,
                "version": versions[tool],
                "path": str(path),
                "sha256": sha256_file(path),
                "bytes": path.stat().st_size,
                "exit_code": exit_code,
                "command": argv,
                "source_tree": source_tree,
                "captured_at": captured_at,
            }
        )

    class LocalOsvHandler(BaseHTTPRequestHandler):
        def do_POST(self) -> None:  # noqa: N802
            length = int(self.headers.get("Content-Length", "0"))
            self.rfile.read(length)
            body = canonical(
                {
                    "vulns": [
                        {
                            "id": "GHSA-F22-HIGH-FIXTURE",
                            "summary": "deterministic F22 high dependency fixture",
                            "affected": [
                                {
                                    "package": {"ecosystem": "PyPI", "name": "urllib3"},
                                    "ranges": [
                                        {
                                            "type": "ECOSYSTEM",
                                            "events": [
                                                {"introduced": "0"},
                                                {"fixed": "99.0.0"},
                                            ],
                                        }
                                    ],
                                }
                            ],
                        }
                    ]
                }
            )
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format: str, *args: Any) -> None:
            return

    server = ThreadingHTTPServer(("127.0.0.1", 0), LocalOsvHandler)
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    osv_url = f"http://127.0.0.1:{server.server_port}/v1/query"
    pip_argv = [
        sys.executable,
        "-m",
        "pip_audit",
        "-r",
        str(dependency_fixture),
        "--format",
        "json",
        "--progress-spinner",
        "off",
        "--no-deps",
        "--disable-pip",
        "--vulnerability-service",
        "osv",
        "--osv-url",
        osv_url,
    ]
    try:
        exit_code, stdout, stderr = run_command(
            pip_argv, fixture_root, env, int(timeouts.get("pip-audit", 600))
        )
    finally:
        server.shutdown()
        server.server_close()
        server_thread.join(timeout=5)
    pip_path = reports_dir / "negative-pip-audit.json"
    write_raw_report(pip_path, stdout, stderr)
    pip_payload = parse_json(pip_path)
    validate_report_payload("pip-audit", pip_payload)
    payloads["pip-audit"] = pip_payload
    reports.append(
        {
            "tool": "pip-audit",
            "version": versions["pip-audit"],
            "path": str(pip_path),
            "sha256": sha256_file(pip_path),
            "bytes": pip_path.stat().st_size,
            "exit_code": exit_code,
            "command": pip_argv,
            "source_tree": source_tree,
            "captured_at": captured_at,
        }
    )
    checks = {
        "fake_secret_fixture_rejected": sum(
            len(items) for items in payloads["detect-secrets"]["results"].values()
        )
        > 0,
        "high_sast_fixture_rejected": any(
            str(item.get("issue_severity", "")).upper() == "HIGH"
            for item in payloads["bandit"]["results"]
        ),
        "high_dependency_fixture_rejected": any(
            item.get("vulns") for item in payloads["pip-audit"]["dependencies"]
        ),
    }
    if not all(checks.values()):
        raise RuntimeError(f"negative security gate fixture escaped: {checks}")
    return {"source_tree": source_tree, "reports": reports, "checks": checks}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tools-dir", type=Path, default=DEFAULT_TOOLS)
    parser.add_argument("--runtime-root", type=Path, default=DEFAULT_RUNTIME)
    parser.add_argument("--baseline-out", type=Path, default=BASELINE_PATH)
    args = parser.parse_args()

    policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    source = security_source_snapshot()
    runtime = args.runtime_root.resolve() / source["source_tree"]
    if runtime.exists():
        shutil.rmtree(runtime)
    staging = runtime / "staging"
    reports_dir = runtime / "reports"
    runtime.mkdir(parents=True, exist_ok=True)
    archive = runtime / "source.zip"
    git("archive", "--format=zip", "--output", str(archive), source["source_tree"])
    with zipfile.ZipFile(archive) as source_zip:
        source_zip.extractall(staging)

    env = os.environ.copy()
    tools_dir = args.tools_dir.resolve()
    env["PYTHONPATH"] = str(tools_dir) + os.pathsep + env.get("PYTHONPATH", "")
    env["PYTHONNOUSERSITE"] = "1"
    actual_versions = {
        tool: scanner_version(tool, env)
        for tool in ("bandit", "detect-secrets", "pip-audit", "npm-audit")
    }
    for tool, actual in actual_versions.items():
        if actual != policy["tools"][tool]:
            raise RuntimeError(
                f"scanner version mismatch for {tool}: expected {policy['tools'][tool]}, got {actual}"
            )
    commands = {
        "detect-secrets": [
            sys.executable,
            "-m",
            "detect_secrets",
            "scan",
            "--exclude-files",
            r"config[\\/]rc0810[\\/]detect_secrets\.baseline\.json$",
            "--all-files",
            str(staging),
        ],
        "bandit": [
            sys.executable,
            "-m",
            "bandit",
            "-r",
            str(staging / "backend"),
            str(staging / "scripts"),
            str(staging / "analysis"),
            "-f",
            "json",
        ],
        "pip-audit": [
            sys.executable,
            "-m",
            "pip_audit",
            "-r",
            str(staging / "backend" / "requirements.txt"),
            "-r",
            str(staging / "analysis" / "profiling" / "requirements.txt"),
            "-r",
            str(staging / "analysis" / "text_analysis" / "requirements.txt"),
            "--format",
            "json",
            "--progress-spinner",
            "off",
        ],
        "npm-audit": [
            "npm.cmd" if os.name == "nt" else "npm",
            "audit",
            "--json",
            "--package-lock-only",
        ],
    }
    timeouts = {
        item["tool"]: item["timeout_seconds"] for item in policy["scans"]
    }
    report_paths: dict[str, Path] = {}
    raw_reports: list[dict[str, Any]] = []
    captured_at = datetime.now(timezone.utc).isoformat()
    for tool, argv in commands.items():
        cwd = staging / "apps" / "web" if tool == "npm-audit" else staging
        exit_code, stdout, stderr = run_command(
            argv, cwd, env, int(timeouts.get(tool, 600))
        )
        path = reports_dir / f"{tool}.json"
        write_raw_report(path, stdout, stderr)
        report_paths[tool] = path
        raw_reports.append(
            {
                "tool": tool,
                "version": actual_versions[tool],
                "path": str(path),
                "sha256": sha256_file(path),
                "bytes": path.stat().st_size,
                "exit_code": exit_code,
                "command": argv,
                "source_tree": source["source_tree"],
                "captured_at": captured_at,
            }
        )

    summary = summarize(report_paths)
    blocking_findings = build_blocking_findings(report_paths, source["source_tree"])
    negative_gate_evidence = run_negative_gate_fixtures(
        runtime,
        env,
        actual_versions,
        timeouts,
        source["source_tree"],
        captured_at,
    )
    open_gate_findings = (
        summary["secret"]
        + summary["sast_high"]
        + summary["python_vulnerability"]
        + summary["node_critical"]
        + summary["node_high"]
    )
    if len(blocking_findings) != open_gate_findings:
        raise RuntimeError(
            f"blocking finding index mismatch: index={len(blocking_findings)}, count={open_gate_findings}"
        )
    baseline = {
        "schema": "safehome.rc0810.security-baseline.v1",
        "phase": "F22-A",
        "captured_at": captured_at,
        **source,
        "policy_sha256": sha256_git_blob(
            source["source_tree"], POLICY_PATH.relative_to(ROOT).as_posix()
        ),
        "exception_registry_sha256": sha256_git_blob(
            source["source_tree"], EXCEPTIONS_PATH.relative_to(ROOT).as_posix()
        ),
        "dependency_inputs": {
            relative: sha256_git_blob(source["source_tree"], relative)
            for relative in (
                "backend/requirements.txt",
                "analysis/profiling/requirements.txt",
                "analysis/text_analysis/requirements.txt",
                "apps/web/package-lock.json",
                "Dockerfile",
                "config/rc0810/detect_secrets.baseline.json",
            )
        },
        "raw_reports": raw_reports,
        "negative_gate_evidence": negative_gate_evidence,
        "blocking_findings": blocking_findings,
        "finding_summary": summary,
        "open_gate_findings": open_gate_findings,
        "container_scan": {
            "status": "pending_f22b_image",
            "production_blocking": True,
        },
        "sbom_status": {
            "status": "pending_f22b_final_dependencies",
            "production_blocking": True,
        },
        "license_status": {
            "status": "pending_f22b_isolated_install",
            "production_blocking": True,
        },
        "supply_chain_attestation": {
            "status": "pending_external",
            "production_blocking": True,
        },
        "production_gate_eligible": False,
        "status": "frozen_findings",
    }
    args.baseline_out.parent.mkdir(parents=True, exist_ok=True)
    args.baseline_out.write_text(
        json.dumps(baseline, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({"baseline": str(args.baseline_out), **summary, "open_gate_findings": open_gate_findings}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
