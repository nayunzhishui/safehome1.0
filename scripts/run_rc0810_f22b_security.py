"""Generate the F22-B security gate from fresh source, image and supply-chain scans."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / "config" / "rc0810" / "security_gate_policy.json"
EXCEPTIONS_PATH = ROOT / "config" / "rc0810" / "security_exception_registry.json"
GATE_PATH = ROOT / "docs" / "02_专项进度与验收" / "rc0810_f22b_security_gate.json"
DEFAULT_RUNTIME = ROOT / ".codex_tmp" / "rc0810" / "security" / "f22b"
DEFAULT_TOOLS = ROOT / ".codex_tmp" / "rc0810" / "security-tools"
DEPENDENCY_INPUTS = (
    "backend/requirements.txt",
    "analysis/profiling/requirements.txt",
    "analysis/text_analysis/requirements.txt",
    "apps/web/package-lock.json",
    "Dockerfile",
    "config/rc0810/database_profiles.json",
    "config/rc0810/detect_secrets.baseline.json",
)
ACTION_INPUTS = (
    ".github/workflows/security-gate.yml",
    ".github/workflows/check.yml",
)
IMAGE_CONTEXT_PATHS = (
    ".dockerignore",
    "Dockerfile",
    "backend",
    ":(exclude)backend/tests",
    "content",
    "shared",
    "config/rc0810/database_profiles.json",
    "deploy/verify_rc0810_f03_images.py",
)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def docker_context_unchanged(previous_tree: str, source_tree: str) -> bool:
    completed = subprocess.run(
        ["git", "diff", "--quiet", previous_tree, source_tree, "--", *IMAGE_CONTEXT_PATHS],
        cwd=ROOT,
        capture_output=True,
        check=False,
    )
    return completed.returncode == 0


def run(argv: list[str], *, cwd: Path = ROOT, timeout: int) -> subprocess.CompletedProcess[bytes]:
    completed = subprocess.run(
        argv, cwd=cwd, capture_output=True, timeout=timeout, check=False
    )
    if completed.returncode != 0:
        stderr = completed.stderr.decode("utf-8", errors="replace")[-4000:]
        raise RuntimeError(f"command failed ({completed.returncode}): {' '.join(argv)}\n{stderr}")
    return completed


def write_report(path: Path, completed: subprocess.CompletedProcess[bytes]) -> dict[str, Any]:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(completed.stdout)
    payload = load_json(path)
    if not isinstance(payload, dict):
        raise RuntimeError(f"report is not a JSON object: {path}")
    return payload


def evidence(
    *,
    tool: str,
    version: str,
    path: Path,
    command: list[str],
    source_tree: str,
    captured_at: str,
) -> dict[str, Any]:
    return {
        "tool": tool,
        "version": version,
        "path": str(path.resolve()),
        "sha256": sha256_file(path),
        "bytes": path.stat().st_size,
        "exit_code": 0,
        "command": command,
        "source_tree": source_tree,
        "captured_at": captured_at,
    }


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


def license_names(payload: dict[str, Any]) -> list[str]:
    names: set[str] = set()
    for result in payload.get("Results", []):
        if not isinstance(result, dict):
            continue
        for license_item in result.get("Licenses") or []:
            if isinstance(license_item, dict) and license_item.get("Name"):
                names.add(str(license_item["Name"]))
    return sorted(names)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runtime-root", type=Path, default=DEFAULT_RUNTIME)
    parser.add_argument("--tools-dir", type=Path, default=DEFAULT_TOOLS)
    parser.add_argument("--gate-out", type=Path, default=GATE_PATH)
    parser.add_argument("--reuse-existing-image-gate", action="store_true")
    args = parser.parse_args()

    policy = load_json(POLICY_PATH)
    previous_gate = (
        load_json(GATE_PATH)
        if args.reuse_existing_image_gate and GATE_PATH.is_file()
        else None
    )
    trivy_version = policy["tools"]["trivy"]
    trivy_digest = policy["tool_images"]["trivy"]
    trivy_image = f"aquasec/trivy@{trivy_digest}"
    source_runtime = args.runtime_root.resolve()
    source_baseline = source_runtime / "source-rescan.json"
    source_command = [
        sys.executable,
        str(ROOT / "scripts" / "run_rc0810_f22_scans.py"),
        "--tools-dir",
        str(args.tools_dir.resolve()),
        "--runtime-root",
        str(source_runtime),
        "--baseline-out",
        str(source_baseline),
    ]
    run(source_command, timeout=2400)
    source = load_json(source_baseline)
    source_tree = source["source_tree"]
    runtime = source_runtime / source_tree
    staging = runtime / "staging"
    reports = runtime / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    captured_at = datetime.now(timezone.utc).isoformat()

    container_path = reports / "trivy-container.json"
    sbom_path = reports / "trivy-sbom.cdx.json"
    license_path = reports / "trivy-license.json"
    artifact_reuse: dict[str, Any] | None = None
    if previous_gate is not None:
        previous_tree = str(previous_gate.get("source_tree", ""))
        if not docker_context_unchanged(previous_tree, source_tree):
            raise RuntimeError("existing image gate cannot be reused after Docker context changes")
        for section, destination in (
            ("container_scan", container_path),
            ("sbom_status", sbom_path),
            ("license_status", license_path),
        ):
            source_report = Path(previous_gate[section]["report"]["path"])
            if not source_report.is_file() or sha256_file(source_report) != previous_gate[section]["report"]["sha256"]:
                raise RuntimeError(f"existing {section} report is missing or stale")
            shutil.copyfile(source_report, destination)
        tag = previous_gate["container_scan"]["image_tag"]
        image_id = previous_gate["container_scan"]["image_id"]
        build_command = previous_gate["supply_chain_attestation"]["build_command"]
        container_command = previous_gate["container_scan"]["report"]["command"]
        sbom_command = previous_gate["sbom_status"]["report"]["command"]
        license_command = previous_gate["license_status"]["report"]["command"]
        artifact_reuse = {
            "from_source_tree": previous_tree,
            "docker_context_unchanged": True,
            "reason": "Docker Desktop unavailable after source-only Harness and documentation changes",
        }
    else:
        tag = f"safehome-rc0810-f22b:{source_tree[:12]}"
        iid_file = runtime / "image.iid"
        build_command = [
            "docker", "build", "--iidfile", str(iid_file), "--tag", tag, str(staging)
        ]
        run(build_command, timeout=1800)
        image_id = iid_file.read_text(encoding="utf-8").strip()
        if re.fullmatch(r"sha256:[0-9a-f]{64}", image_id) is None:
            raise RuntimeError("docker build did not produce an immutable image id")
        cache = runtime / "trivy-cache"
        cache.mkdir(exist_ok=True)
        socket_mount = "//var/run/docker.sock:/var/run/docker.sock"
        cache_mount = f"{cache.resolve()}:/root/.cache/trivy"
        container_command = [
            "docker", "run", "--rm", "-v", socket_mount, "-v", cache_mount,
            trivy_image, "image", "--image-src", "docker", "--scanners", "vuln,secret",
            "--severity", "HIGH,CRITICAL", "--format", "json", tag,
        ]
        write_report(container_path, run(container_command, timeout=1800))
        sbom_command = [
            "docker", "run", "--rm", "-v", socket_mount, "-v", cache_mount,
            trivy_image, "image", "--image-src", "docker", "--format", "cyclonedx", tag,
        ]
        write_report(sbom_path, run(sbom_command, timeout=1800))
        source_mount = f"{staging.resolve()}:/source:ro"
        license_command = [
            "docker", "run", "--rm", "-v", source_mount, "-v", cache_mount,
            trivy_image, "filesystem", "--scanners", "license", "--license-full",
            "--format", "json", "/source",
        ]
        write_report(license_path, run(license_command, timeout=1800))

    container_payload = load_json(container_path)
    container_summary = trivy_summary(container_payload)
    sbom_payload = load_json(sbom_path)
    if sbom_payload.get("bomFormat") != "CycloneDX":
        raise RuntimeError("Trivy did not produce a CycloneDX SBOM")
    license_payload = load_json(license_path)
    observed_licenses = license_names(license_payload)
    forbidden = sorted(set(observed_licenses) & set(policy["severity_gate"]["forbidden_licenses"]))

    container_open = sum(container_summary.values())
    source_open = int(source["open_gate_findings"])
    production_blocking = source_open + container_open + len(forbidden) > 0
    gate = {
        "schema": "safehome.rc0810.security-gate.v2",
        "phase": "F22-B",
        "captured_at": captured_at,
        "source_scan_captured_at": source["captured_at"],
        "head": source["head"],
        "head_tree": source["head_tree"],
        "source_tree": source_tree,
        "dirty_diff_sha256": source["dirty_diff_sha256"],
        "source_manifest_sha256": source["source_manifest_sha256"],
        "policy_sha256": sha256_file(POLICY_PATH),
        "exception_registry_sha256": sha256_file(EXCEPTIONS_PATH),
        "dependency_inputs": {item: sha256_file(ROOT / item) for item in DEPENDENCY_INPUTS},
        "action_inputs": {item: sha256_file(ROOT / item) for item in ACTION_INPUTS},
        "source_reports": source["raw_reports"],
        "negative_gate_evidence": source["negative_gate_evidence"],
        "blocking_findings": source["blocking_findings"],
        "finding_summary": source["finding_summary"],
        "source_open_gate_findings": source_open,
        "container_scan": {
            "status": "completed",
            "production_blocking": container_open > 0,
            "image_tag": tag,
            "image_id": image_id,
            "tool_image": trivy_image,
            "finding_summary": container_summary,
            "report": evidence(tool="trivy-container", version=trivy_version, path=container_path, command=container_command, source_tree=source_tree, captured_at=captured_at),
        },
        "sbom_status": {
            "status": "completed",
            "production_blocking": False,
            "format": "CycloneDX",
            "component_count": len(sbom_payload.get("components") or []),
            "report": evidence(tool="trivy-sbom", version=trivy_version, path=sbom_path, command=sbom_command, source_tree=source_tree, captured_at=captured_at),
        },
        "license_status": {
            "status": "completed",
            "production_blocking": bool(forbidden),
            "observed_licenses": observed_licenses,
            "forbidden_licenses_found": forbidden,
            "report": evidence(tool="trivy-license", version=trivy_version, path=license_path, command=license_command, source_tree=source_tree, captured_at=captured_at),
        },
        "supply_chain_attestation": {
            "status": "pending_external",
            "production_blocking": True,
            "runner": "ubuntu-24.04",
            "action_commits": policy["action_commits"],
            "trivy_image_digest": trivy_digest,
            "base_image_provenance": "pending_external_registry_attestation",
            "build_command": build_command,
            "local_artifact_reuse": artifact_reuse,
        },
        "open_gate_findings": source_open + container_open + len(forbidden),
        "production_gate_eligible": False,
        "status": "rescan_complete_no_go" if production_blocking else "attestation_pending_no_go",
    }
    args.gate_out.parent.mkdir(parents=True, exist_ok=True)
    args.gate_out.write_text(json.dumps(gate, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "gate": str(args.gate_out),
        "source_tree": source_tree,
        "image_id": image_id,
        "source_open_gate_findings": source_open,
        "container_open_gate_findings": container_open,
        "forbidden_licenses": forbidden,
        "production_gate_eligible": False,
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
