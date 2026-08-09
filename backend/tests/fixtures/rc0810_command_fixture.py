"""Subprocess fixture for RC0810 harness timeout/resume contracts."""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path


def _increment_counter() -> None:
    target = os.environ.get("RC0810_FIXTURE_COUNTER")
    if not target:
        return
    path = Path(target)
    current = int(path.read_text(encoding="utf-8")) if path.exists() else 0
    path.write_text(str(current + 1), encoding="utf-8")


def main() -> int:
    mode = sys.argv[1] if len(sys.argv) > 1 else "success"
    _increment_counter()
    if mode == "timeout":
        time.sleep(2)
        return 0
    if mode == "fail":
        print("synthetic failure", file=sys.stderr)
        return 7
    print("synthetic success")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
