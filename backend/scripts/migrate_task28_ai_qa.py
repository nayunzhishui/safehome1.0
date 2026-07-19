"""Task 28 idempotent migration, audit and non-destructive rollback plan."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from database import CURRENT_SCHEMA_VERSION, get_connection, init_db, list_database_tables  # noqa: E402


TABLES = (
    "ai_qa_sessions",
    "ai_qa_messages",
    "ai_qa_feedback",
    "ai_qa_safety_events",
    "ai_qa_provider_events",
    "ai_qa_evaluation_runs",
    "ai_qa_evaluation_reviews",
    "ai_qa_runtime_control",
)


def audit() -> dict:
    with get_connection() as conn:
        existing = {row["name"] for row in list_database_tables(conn)}
        counts = {
            table: int(conn.execute(f"SELECT COUNT(*) AS count FROM {table}").fetchone()["count"])
            if table in existing else None
            for table in TABLES
        }
        migration = conn.execute(
            "SELECT version, name, applied_at FROM schema_migrations WHERE version = ?",
            (CURRENT_SCHEMA_VERSION,),
        ).fetchone()
    return {
        "ok": all(table in existing for table in TABLES) and migration is not None,
        "schema_version": CURRENT_SCHEMA_VERSION,
        "tables": counts,
        "migration_recorded": dict(migration) if migration else None,
    }


def rollback_plan() -> dict:
    return {
        "automatic_rollback_executed": False,
        "reason": "问答审计与安全证据不可静默删除，参与者能力本就默认关闭。",
        "safe_rollback_steps": [
            "保持 AI_QA_ENABLED=0，并将 AI_QA_SANDBOX_ENABLED=0",
            "管理员执行只允许关闭的 kill switch",
            "回退 Web 研究沙盒入口与 API 路由注册",
            "保留八张表只读并按隐私请求白名单处理会话原文",
            "待负责人确认后再决定是否归档合成评估证据",
        ],
        "destructive_step_requires_human_approval": True,
        "participant_release_approval_inferred": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="执行幂等建表并记录版本")
    parser.add_argument("--rollback-plan", action="store_true", help="仅输出非破坏回滚方案")
    args = parser.parse_args()
    if args.apply:
        init_db()
    result = rollback_plan() if args.rollback_plan else audit()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if args.rollback_plan or result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
