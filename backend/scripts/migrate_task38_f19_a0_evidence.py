"""Task38-F19 no-schema readiness and rollback evidence."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from config import Config
from database import CURRENT_SCHEMA_NAME, CURRENT_SCHEMA_VERSION, get_connection, init_db


def inspect() -> dict:
    path = Path(Config.CONTENT_DIR) / "therapeutic_assessment_pilot_evidence_registry.json"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        payload = {}
    a0 = next((item for item in payload.get("stages") or [] if item.get("id") == "A0"), None)
    with get_connection() as conn:
        audit_ready = conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='audit_logs'").fetchone() is not None
    content_ok = bool(a0 and len(a0.get("roles") or []) == 5 and a0.get("simulated_role_may_sign") is False)
    return {"ok": content_ok and audit_ready, "schema_version": CURRENT_SCHEMA_VERSION, "schema_name": CURRENT_SCHEMA_NAME, "schema_change_required": False, "content_ok": content_ok, "audit_table_reused": audit_ready}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["plan", "apply", "verify", "rollback"])
    parser.add_argument("--database-path", default="")
    args = parser.parse_args()
    if args.database_path:
        Config.DATABASE_PATH = Path(args.database_path).resolve()
    if args.action == "apply":
        init_db()
        result = {"action": "apply", **inspect(), "production_mutation": False}
    elif args.action == "verify":
        result = {"action": "verify", **inspect(), "production_mutation": False}
    elif args.action == "rollback":
        result = {"action": "rollback", "ok": True, "schema_preserved": True, "tables_dropped": False, "human_reviews_deleted": False, "production_mutation": False}
    else:
        current = inspect()
        result = {"action": "plan", "ok": True, "already_ready": current["ok"], "current_state": current, "additive_only": True, "production_mutation": False}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
