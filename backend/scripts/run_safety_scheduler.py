"""Run one active safety scheduler scan for an external cron/worker."""

from __future__ import annotations

import argparse
import json
import os
import socket
import sys
from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from services.safety_scheduler_service import SchedulerError, run_safety_scheduler  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="SafeHome主动安全时钟")
    parser.add_argument("--worker-id", default=f"{socket.gethostname()}:{os.getpid()}")
    parser.add_argument("--run-key")
    args = parser.parse_args()
    try:
        result = run_safety_scheduler(args.worker_id, run_key=args.run_key)
    except SchedulerError as exc:
        print(json.dumps({"ok": False, "error": {"code": exc.code, "message": str(exc)}}, ensure_ascii=False))
        return 1
    print(json.dumps({"ok": True, "data": result}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
