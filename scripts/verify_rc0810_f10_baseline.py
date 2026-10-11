"""Fail-closed verifier for the RC0810-F10-A CI failure baseline."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import re
import subprocess
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BASELINE = (
    ROOT
    / "docs"
    / "02_专项进度与验收"
    / "rc0810_f10a_ci_failure_baseline.json"
)
DEFAULT_EVIDENCE = (
    ROOT
    / "docs"
    / "02_专项进度与验收"
    / "rc0810_f10a_github_actions_evidence.json"
)
ALLOWED_CLASSIFICATIONS = {
    "true_defect",
    "contract_drift",
    "snapshot_drift",
    "environment_gap",
}


def _git(*args: str, binary: bool = False) -> bytes | str:
    completed = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        raise ValueError(
            f"git {' '.join(args)} failed: "
            f"{completed.stderr.decode('utf-8', errors='replace').strip()}"
        )
    if binary:
        return completed.stdout
    return completed.stdout.decode("utf-8").strip()


def verify(path: Path, evidence_path: Path = DEFAULT_EVIDENCE) -> dict:
    baseline = json.loads(path.read_text(encoding="utf-8"))
    errors: list[str] = []

    if baseline.get("schema") != "safehome.rc0810.ci-failure-baseline.v1":
        errors.append("schema mismatch")
    if baseline.get("task") != "RC0810-F10-A":
        errors.append("task mismatch")
    if baseline.get("status") != "frozen_failure_baseline":
        errors.append("baseline status must remain frozen_failure_baseline")
    if baseline.get("release_gate_eligible") is not False:
        errors.append("a failing F10-A baseline cannot be release-gate eligible")

    source = baseline.get("source", {})
    head = source.get("head")
    if not head or source.get("origin_main") != head:
        errors.append("head and origin_main must be bound and equal")
    else:
        try:
            tree = _git("show", "-s", "--format=%T", head)
            if tree != source.get("source_tree"):
                errors.append("source_tree does not match the frozen head")
        except ValueError as exc:
            errors.append(str(exc))

    for item in baseline.get("workflow_snapshot", []):
        try:
            oid = _git("rev-parse", f"{head}:{item['path']}")
            payload = _git("cat-file", "blob", oid, binary=True)
            if oid != item.get("git_blob"):
                errors.append(f"workflow blob mismatch: {item['path']}")
            if hashlib.sha256(payload).hexdigest() != item.get("sha256"):
                errors.append(f"workflow sha256 mismatch: {item['path']}")
        except (KeyError, ValueError) as exc:
            errors.append(str(exc))

    actions = baseline.get("github_actions", {})
    artifact = actions.get("evidence_artifact", {})
    try:
        evidence_bytes = evidence_path.read_bytes()
        evidence = json.loads(evidence_bytes.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        evidence = {}
        errors.append(f"Actions evidence cannot be read: {exc}")
    if artifact.get("schema") != "safehome.rc0810.github-actions-evidence.v1":
        errors.append("Actions evidence schema binding mismatch")
    if evidence.get("schema") != artifact.get("schema"):
        errors.append("Actions evidence schema mismatch")
    if evidence and hashlib.sha256(evidence_bytes).hexdigest() != artifact.get("sha256"):
        errors.append("Actions evidence sha256 mismatch")

    run = actions.get("authoritative_run", {})
    failures = run.get("failures", [])
    if run.get("head_sha") != head:
        errors.append("Actions run is not bound to the frozen head")
    if run.get("conclusion") != "failure":
        errors.append("F10-A must preserve the observed failing conclusion")
    if run.get("summary", {}).get("failed_tests") != len(failures):
        errors.append("failed test count does not match failure records")
    if len({item.get("id") for item in failures}) != len(failures):
        errors.append("failure ids must be unique")
    if any(item.get("classification") not in ALLOWED_CLASSIFICATIONS for item in failures):
        errors.append("unknown failure classification")
    required_fields = {"id", "test_nodeid", "classification", "root_cause_group", "evidence", "disposition", "priority"}
    if any(not required_fields.issubset(item) for item in failures):
        errors.append("failure record is incomplete")

    raw_run = evidence.get("run", {})
    raw_job = evidence.get("job", {})
    raw_log = evidence.get("failed_log", {})
    run_bindings = {
        "id": "database_id",
        "name": "workflow",
        "event": "event",
        "head_branch": "head_branch",
        "head_sha": "head_sha",
        "conclusion": "conclusion",
        "created_at": "created_at",
        "updated_at": "updated_at",
        "html_url": "url",
    }
    for raw_key, baseline_key in run_bindings.items():
        if raw_run.get(raw_key) != run.get(baseline_key):
            errors.append(f"Actions run field mismatch: {raw_key}")
    job = run.get("job", {})
    if (
        raw_job.get("id") != job.get("database_id")
        or raw_job.get("name") != job.get("name")
        or raw_job.get("html_url") != job.get("url")
        or raw_job.get("head_sha") != head
        or raw_job.get("conclusion") != "failure"
    ):
        errors.append("Actions job binding mismatch")

    steps = [step for step in raw_job.get("steps", []) if 2 <= step.get("number", 0) <= 21]
    executed_steps = sum(step.get("conclusion") != "skipped" for step in steps)
    skipped_steps = sum(step.get("conclusion") == "skipped" for step in steps)
    summary = run.get("summary", {})
    if (
        executed_steps != summary.get("executed_workflow_steps")
        or skipped_steps != summary.get("skipped_workflow_steps")
    ):
        errors.append("workflow step counts do not match raw Actions evidence")
    failed_steps = [step.get("name") for step in steps if step.get("conclusion") == "failure"]
    if failed_steps != [job.get("failed_step")]:
        errors.append("failed workflow step does not match raw Actions evidence")

    runtime_log_verified = False
    baseline_log = run.get("failed_log", {})
    if raw_log.get("encoding") != "runtime_gzip":
        errors.append("failed log must be retained as runtime_gzip")
    if raw_log.get("command") != "gh run view 31325141640 --log-failed":
        errors.append("failed log capture command mismatch")
    if raw_log.get("exit_code") != 0:
        errors.append("failed log capture did not succeed")
    if raw_log.get("sha256") != baseline_log.get("sha256"):
        errors.append("baseline failed log sha256 mismatch")
    if raw_log.get("line_count") != baseline_log.get("line_count"):
        errors.append("baseline failed log line count mismatch")

    raw_nodeids = set(raw_log.get("failure_nodeids", []))
    baseline_nodeids = {item.get("test_nodeid") for item in failures}
    if raw_nodeids != baseline_nodeids:
        errors.append("failure nodeids do not match raw Actions evidence")
    raw_summary = raw_log.get("pytest_summary", {})
    if (
        raw_summary.get("failed") != summary.get("failed_tests")
        or raw_summary.get("passed") != summary.get("passed_tests")
        or raw_summary.get("warnings") != summary.get("warnings")
    ):
        errors.append("pytest summary does not match raw Actions evidence")

    runtime_ref = raw_log.get("runtime_artifact", {})
    runtime_relative = Path(str(runtime_ref.get("path", "")))
    runtime_path = (ROOT / runtime_relative).resolve()
    runtime_root = (ROOT / ".codex_tmp" / "rc0810").resolve()
    try:
        runtime_path.relative_to(runtime_root)
    except ValueError:
        errors.append("full failed log must stay under .codex_tmp/rc0810")
    if runtime_ref.get("committed") is not False:
        errors.append("full failed log must be marked uncommitted")
    if _git("ls-files", "--", runtime_relative.as_posix()):
        errors.append("full failed log must not be tracked")

    try:
        if runtime_path.is_file():
            compressed = runtime_path.read_bytes()
            if hashlib.sha256(compressed).hexdigest() != runtime_ref.get("sha256"):
                errors.append("runtime failed log gzip sha256 mismatch")
            if len(compressed) != runtime_ref.get("size_bytes"):
                errors.append("runtime failed log gzip size mismatch")
            log_text = gzip.decompress(compressed).decode("utf-8")
            normalized_log = "\n".join(log_text.splitlines()) + "\n"
            normalized_bytes = normalized_log.encode("utf-8")
            if hashlib.sha256(normalized_bytes).hexdigest() != raw_log.get("sha256"):
                errors.append("raw failed log sha256 mismatch")
            if len(normalized_log.splitlines()) != raw_log.get("line_count"):
                errors.append("raw failed log line count mismatch")
            runtime_nodeids = {
                f"backend/tests/{nodeid}"
                for nodeid in re.findall(r"FAILED tests/([^ \r\n]+)", log_text)
            }
            if runtime_nodeids != raw_nodeids:
                errors.append("runtime failure nodeids do not match structured evidence")
            match = re.search(
                r"(\d+) failed, (\d+) passed, (\d+) warning(?:s)? in", log_text
            )
            if not match or tuple(map(int, match.groups())) != (
                raw_summary.get("failed"),
                raw_summary.get("passed"),
                raw_summary.get("warnings"),
            ):
                errors.append("runtime pytest summary does not match structured evidence")
            runtime_log_verified = True
    except (KeyError, ValueError, OSError, UnicodeDecodeError) as exc:
        errors.append(f"raw failed log cannot be verified: {exc}")

    counts = Counter(item.get("classification") for item in failures)
    normalized_counts = {
        category: counts.get(category, 0) for category in sorted(ALLOWED_CLASSIFICATIONS)
    }
    expected_counts = {
        category: baseline.get("classification_counts", {}).get(category, 0)
        for category in sorted(ALLOWED_CLASSIFICATIONS)
    }
    if normalized_counts != expected_counts:
        errors.append("classification counts do not match failure records")

    findings = baseline.get("workflow_findings", {})
    if findings.get("single_job_fail_fast") is not True:
        errors.append("single-job fail-fast finding was lost")
    if findings.get("independent_required_jobs") is not False:
        errors.append("independent required jobs must not be claimed before F10-B")
    if findings.get("f10_b_required") is not True:
        errors.append("F10-B requirement was lost")

    if errors:
        return {
            "schema": "safehome.rc0810.ci-failure-baseline-verification.v1",
            "status": "invalid",
            "release_gate_eligible": False,
            "failure_count": len(failures),
            "runtime_log_verified": runtime_log_verified,
            "errors": errors,
        }
    return {
        "schema": "safehome.rc0810.ci-failure-baseline-verification.v1",
        "status": "frozen_failure_baseline",
        "release_gate_eligible": False,
        "failure_count": len(failures),
        "runtime_log_verified": runtime_log_verified,
        "errors": [],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", type=Path, default=DEFAULT_BASELINE)
    parser.add_argument("--evidence", type=Path, default=DEFAULT_EVIDENCE)
    args = parser.parse_args()
    result = verify(args.baseline.resolve(), args.evidence.resolve())
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "frozen_failure_baseline" else 1


if __name__ == "__main__":
    raise SystemExit(main())
