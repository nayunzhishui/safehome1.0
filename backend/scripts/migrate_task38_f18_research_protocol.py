"""Task38-F18 readiness check for the frozen research protocol."""

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


CONFIRMATION = "APPLY_TASK38_F18_RESEARCH_PROTOCOL"


def inspect() -> dict:
    path = Path(Config.CONTENT_DIR) / "therapeutic_assessment_research_protocol.json"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        payload = {}
    metrics = payload.get("metrics") or {}
    metric_count = sum(len(items) for items in metrics.values() if isinstance(items, list))
    with get_connection() as conn:
        audit_ready = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='audit_logs'"
        ).fetchone() is not None
    content_ok = (
        payload.get("schema")
        == "safehome.therapeutic-assessment.research-protocol.v1"
        and metric_count >= 19
        and payload.get("analysis_rules", {}).get(
            "satisfaction_may_offset_serious_harm"
        )
        is False
    )
    return {
        "ok": content_ok and audit_ready,
        "schema_version": CURRENT_SCHEMA_VERSION,
        "schema_name": CURRENT_SCHEMA_NAME,
        "schema_change_required": False,
        "audit_table_reused": audit_ready,
        "content_ok": content_ok,
        "metric_count": metric_count,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["plan", "apply", "verify", "rollback"])
    parser.add_argument("--database-path", default="")
    parser.add_argument("--allow-production", action="store_true")
    parser.add_argument("--confirmation", default="")
    args = parser.parse_args()
    if args.database_path:
        Config.DATABASE_PATH = Path(args.database_path).resolve()
    production = str(Config.APP_ENV).lower() == "production"
    if production and args.action == "apply" and (
        not args.allow_production or args.confirmation != CONFIRMATION
    ):
        raise RuntimeError("生产检查已阻断：需要独立批准和精确确认短语")
    if args.action == "apply":
        init_db()
        result = {"action": "apply", **inspect(), "production_mutation": production}
    elif args.action == "verify":
        result = {"action": "verify", **inspect(), "production_mutation": False}
    elif args.action == "rollback":
        result = {
            "action": "rollback",
            "ok": True,
            "schema_preserved": True,
            "tables_dropped": False,
            "audit_deleted": False,
            "protocol_file_changed": False,
            "production_mutation": False,
        }
    else:
        current = inspect()
        result = {
            "action": "plan",
            "ok": True,
            "already_ready": current["ok"],
            "current_state": current,
            "additive_only": True,
            "production_mutation": False,
        }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
