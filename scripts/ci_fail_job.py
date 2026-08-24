"""Fail exactly one selected CI job for isolation checks."""

from __future__ import annotations

import os
import sys


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: ci_fail_job.py <job>", file=sys.stderr)
        return 2
    job = sys.argv[1]
    selected = os.environ.get("SAFEHOME_CI_FAIL_JOB", "").strip()
    if selected and selected == job:
        print(f"controlled CI failure selected for {job}", file=sys.stderr)
        return 1
    print(f"controlled CI failure not selected for {job}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
