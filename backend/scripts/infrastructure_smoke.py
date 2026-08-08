"""CI smoke test for MySQL pool, explicit migrations, Redis and RAG primitives."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))


def main() -> int:
    # Environment must be configured before importing Config/database modules.
    os.environ.setdefault("APP_ENV", "testing")
    os.environ.setdefault("CONTENT_DIR", str(ROOT / "content"))
    os.environ.setdefault("MYSQL_POOL_ENABLED", "1")
    os.environ.setdefault("RAG_EMBEDDING_PROVIDER", "hash")

    from config import Config
    from services.mysql_pool_runtime import install_mysql_pool, status as mysql_pool_status

    Config.validate()
    pool_install = install_mysql_pool()

    from database import get_connection, init_db, list_database_columns, list_database_tables
    from services.embedding_service import embed_text, public_status as embedding_status
    from services.redis_service import health as redis_health, rate_limit
    from services.schema_migration_service import apply_pending_schema_migrations

    init_db()
    with get_connection() as conn:
        applied = apply_pending_schema_migrations(conn)
        conn.commit()
        one = conn.execute("SELECT 1 AS value").fetchone()
        tables = {row["name"] for row in list_database_tables(conn)}
        chunk_columns = {row["name"] for row in list_database_columns(conn, "ai_knowledge_chunks")}

    required_tables = {"explicit_schema_migrations", "agent_runs", "agent_tool_calls"}
    required_chunk_columns = {"embedding_json", "embedding_model", "embedding_dimensions", "embedding_updated_at"}
    if int(one["value"]) != 1:
        raise RuntimeError("MySQL SELECT 1 failed")
    if not required_tables.issubset(tables):
        raise RuntimeError(f"missing engineering tables: {sorted(required_tables - tables)}")
    if not required_chunk_columns.issubset(chunk_columns):
        raise RuntimeError(f"missing RAG columns: {sorted(required_chunk_columns - chunk_columns)}")

    redis = redis_health()
    if os.environ.get("REDIS_URL") and not redis.get("ok"):
        raise RuntimeError(f"Redis health failed: {redis}")
    first = rate_limit("ci-smoke", limit=1, window_seconds=60)
    second = rate_limit("ci-smoke", limit=1, window_seconds=60)
    if redis.get("enabled") and (not first.get("allowed") or second.get("allowed")):
        raise RuntimeError("Redis distributed rate-limit smoke failed")

    vector = embed_text("SafeHome工程检索测试")
    if len(vector) != 96:
        raise RuntimeError(f"deterministic embedding expected 96 dimensions, got {len(vector)}")

    result = {
        "ok": True,
        "db_provider": Config.DB_PROVIDER,
        "mysql_pool": mysql_pool_status(),
        "applied_migrations": applied,
        "redis": redis,
        "embedding": {**embedding_status(), "dimensions": len(vector)},
        "secrets_exposed": False,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
