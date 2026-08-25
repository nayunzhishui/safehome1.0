"""Run RC0810-F21 in-memory alert and recovery drills only."""

from __future__ import annotations

import json
import sys
from pathlib import Path


BACKEND = Path(__file__).resolve().parents[1]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from services.operations_reliability_service import run_isolated_drills  # noqa: E402


def main() -> int:
    result = run_isolated_drills()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
