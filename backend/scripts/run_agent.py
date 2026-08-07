"""Run SafeHome Agent v1 from an internal CLI.

This is intentionally not an HTTP participant endpoint.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from database import get_connection, init_db
from services.agent_runtime_service import AgentRuntimeError, run_agent
from services.schema_migration_service import apply_pending_schema_migrations


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--objective", required=True)
    parser.add_argument("--actor-id", default="internal-agent-cli")
    parser.add_argument("--actor-role", choices=["researcher", "supervisor", "admin"], default="researcher")
    parser.add_argument("--synthetic-data", action="store_true", help="required acknowledgement for Agent v1")
    args = parser.parse_args()

    init_db()
    with get_connection() as conn:
        apply_pending_schema_migrations(conn)
        conn.commit()

    actor = {"id": args.actor_id, "role": args.actor_role}
    try:
        result = run_agent(actor, args.objective, synthetic_data=bool(args.synthetic_data))
    except AgentRuntimeError as exc:
        print(json.dumps({"ok": False, "error": {"code": exc.code, "message": str(exc), "details": exc.details}}, ensure_ascii=False, indent=2))
        return 2
    print(json.dumps({"ok": True, "data": result}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
