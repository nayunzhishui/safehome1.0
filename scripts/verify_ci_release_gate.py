"""Aggregate independent required-job results into the RC technical CI gate."""

from __future__ import annotations

import argparse
import json


REQUIRED_JOBS = (
    "backend",
    "ai",
    "mysql-redis",
    "web",
    "npm-audit",
    "miniprogram",
    "content-api",
    "artifact",
    "security-contract",
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results-json", required=True)
    args = parser.parse_args()
    try:
        results = json.loads(args.results_json)
    except json.JSONDecodeError as exc:
        parser.error(f"invalid results JSON: {exc}")
    if not isinstance(results, dict):
        parser.error("results JSON must be an object")

    missing = [job for job in REQUIRED_JOBS if job not in results]
    unknown = sorted(set(results) - set(REQUIRED_JOBS))
    failed = [job for job in REQUIRED_JOBS if results.get(job) != "success"]
    eligible = not missing and not unknown and not failed
    payload = {
        "schema": "safehome.ci-release-gate.v1",
        "ci_gate_eligible": eligible,
        "production_gate_eligible": False,
        "results": results,
        "failed_jobs": failed,
        "missing_jobs": missing,
        "unknown_jobs": unknown,
        "boundary": "Technical CI only; F22-B and external release approvals remain required.",
    }
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return 0 if eligible else 1


if __name__ == "__main__":
    raise SystemExit(main())
