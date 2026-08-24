"""Write compact, source-bound CI evidence to stdout and GitHub step summary."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import subprocess
import sys
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


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--job", required=True)
    parser.add_argument("--status", default="success")
    parser.add_argument("--artifact", action="append", default=[])
    args = parser.parse_args()

    head = _git("rev-parse", "HEAD")
    expected_head = os.environ.get("GITHUB_SHA", "").strip()
    if expected_head and expected_head != head:
        print(f"GITHUB_SHA {expected_head} does not match checked-out HEAD {head}", file=sys.stderr)
        return 1
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
