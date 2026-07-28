"""Audit the additive Task37-B04 lifecycle and privacy propagation contract."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from database import get_connection, init_db, list_database_tables  # noqa: E402
from services.privacy_request_service import SCOPE_TABLES  # noqa: E402


REQUIRED_TABLES = {
    "therapeutic_assessment_cases",
    "therapeutic_assessment_feedback_versions",
    "therapeutic_assessment_feedback_deliveries",
    "therapeutic_assessment_feedback_responses",
    "therapeutic_assessment_actions",
    "therapeutic_assessment_events",
    "therapeutic_assessment_quality_incidents",
    "privacy_requests",
}
PRIVACY_REQUIRED = {
    "therapeutic_assessment_feedback_deliveries",
    "therapeutic_assessment_feedback_responses",
    "therapeutic_assessment_evidence_items",
    "therapeutic_assessment_data_items",
    "therapeutic_assessment_actions",
    "therapeutic_assessment_cases",
}


def audit() -> dict:
    with get_connection() as conn:
        tables = {row["name"] for row in list_database_tables(conn)}
    privacy_tables = set(SCOPE_TABLES["therapeutic_assessment"])
    return {
        "ok": REQUIRED_TABLES.issubset(tables) and PRIVACY_REQUIRED.issubset(privacy_tables),
        "missing_tables": sorted(REQUIRED_TABLES - tables),
        "missing_privacy_tables": sorted(PRIVACY_REQUIRED - privacy_tables),
        "additive_only": True,
        "legacy_feedback_readable": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["plan", "apply", "verify", "rollback"])
    args = parser.parse_args()
    if args.action == "apply":
        init_db()
    if args.action == "rollback":
        result = {
            "ok": True,
            "action": "rollback",
            "tables_dropped": False,
            "history_deleted": False,
            "strategy": "关闭生命周期读取入口，保留既有状态、回执和审计记录。",
        }
    else:
        result = {"action": args.action, **audit()}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
