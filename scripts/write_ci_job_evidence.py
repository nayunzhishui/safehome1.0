"""Write compact, source-bound CI evidence to stdout and GitHub step summary."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import os
import platform
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEPENDENCY_INPUTS = (
    "backend/requirements.txt",
    "analysis/profiling/requirements.txt",
    "analysis/text_analysis/requirements.txt",
    "apps/web/package-lock.json",
    "Dockerfile",
)


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=ROOT, capture_output=True, text=True, check=True
    ).stdout.strip()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    if path.is_file():
        digest.update(path.read_bytes())
        return digest.hexdigest()
    if path.is_dir():
        for child in sorted(item for item in path.rglob("*") if item.is_file()):
            digest.update(child.relative_to(path).as_posix().encode("utf-8"))
            digest.update(b"\0")
            digest.update(child.read_bytes())
        return digest.hexdigest()
    raise FileNotFoundError(path)


def _node_version() -> str | None:
    try:
        return subprocess.run(
            ["node", "--version"], capture_output=True, text=True, check=True
        ).stdout.strip()
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None


def _dependency_versions() -> dict[str, dict]:
    python_dependencies: dict[str, dict[str, object]] = {}
    for relative_path in DEPENDENCY_INPUTS[:3]:
        for raw_line in (ROOT / relative_path).read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            match = re.match(r"^([A-Za-z0-9_.-]+)\s*(.*)$", line)
            if not line or line.startswith("#") or not match:
                continue
            name, constraint = match.group(1), match.group(2).strip()
            record = python_dependencies.setdefault(
                name,
                {"declared": [], "installed": None},
            )
            if constraint and constraint not in record["declared"]:
                record["declared"].append(constraint)
            try:
                record["installed"] = importlib.metadata.version(name)
            except importlib.metadata.PackageNotFoundError:
                pass

    lock = json.loads((ROOT / "apps" / "web" / "package-lock.json").read_text(encoding="utf-8"))
    node_dependencies: dict[str, str] = {}
    for package_path, metadata in lock.get("packages", {}).items():
        if not package_path.startswith("node_modules/") or not isinstance(metadata, dict):
            continue
        version = metadata.get("version")
        if version:
            node_dependencies[package_path.removeprefix("node_modules/")] = str(version)
    return {
        "python": dict(sorted(python_dependencies.items())),
        "node": dict(sorted(node_dependencies.items())),
    }


def _unique_test_count(paths: list[str]) -> tuple[int | None, str]:
    if not paths:
        return None, "not_declared"
    identities: set[tuple[str, str, str]] = set()
    for relative_path in paths:
        path = ROOT / relative_path
        if not path.is_file():
            return None, "report_missing_due_prior_failure"
        root = ET.parse(path).getroot()
        for case in root.iter("testcase"):
            identities.add(
                (
                    str(case.get("file") or ""),
                    str(case.get("classname") or ""),
                    str(case.get("name") or ""),
                )
            )
    return len(identities), "junit_unique_cases"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--job", required=True)
    parser.add_argument("--status", default="success")
    parser.add_argument("--artifact", action="append", default=[])
    parser.add_argument("--test-count", type=int)
    parser.add_argument("--test-report", action="append", default=[])
    args = parser.parse_args()

    head = _git("rev-parse", "HEAD")
    expected_head = os.environ.get("GITHUB_SHA", "").strip()
    if expected_head and expected_head != head:
        print(f"GITHUB_SHA {expected_head} does not match checked-out HEAD {head}", file=sys.stderr)
        return 1
    if args.test_count is not None and args.test_report:
        print("--test-count and --test-report cannot be used together", file=sys.stderr)
        return 1
    if args.test_count is not None and args.test_count < 0:
        print("--test-count must be non-negative", file=sys.stderr)
        return 1
    if args.test_count is None:
        test_count, test_count_source = _unique_test_count(args.test_report)
    else:
        test_count, test_count_source = args.test_count, "explicit_non_test_count"
    dependencies = {path: _sha256(ROOT / path) for path in DEPENDENCY_INPUTS}
    artifacts = {path: _sha256(ROOT / path) for path in args.artifact}
    payload = {
        "schema": "safehome.ci-job-evidence.v1",
        "job": args.job,
        "status": args.status,
        "source": {
            "commit": head,
            "tree": _git("rev-parse", "HEAD^{tree}"),
        },
        "runtime": {
            "python": platform.python_version(),
            "node": _node_version(),
        },
        "test_count": test_count,
        "test_count_source": test_count_source,
        "dependency_versions": _dependency_versions(),
        "dependency_inputs": dependencies,
        "artifacts": artifacts,
        "provenance": {
            "workflow": os.environ.get("GITHUB_WORKFLOW"),
            "job": os.environ.get("GITHUB_JOB", args.job),
            "run_id": os.environ.get("GITHUB_RUN_ID"),
            "run_attempt": os.environ.get("GITHUB_RUN_ATTEMPT"),
        },
        "sbom_summary": {
            "status": "dependency_inputs_bound",
            "inputs": sorted(dependencies),
        },
        "attestation_summary": {
            "status": "pending_f22b",
            "reason": "F10 records provenance; final attestation remains in F22-B.",
        },
        "production_gate_eligible": False,
    }
    rendered = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    print(rendered)
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY", "").strip()
    if summary_path:
        with Path(summary_path).open("a", encoding="utf-8") as handle:
            handle.write(f"### {args.job} evidence\n\n```json\n{rendered}\n```\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
