from __future__ import annotations

from pathlib import Path

import pytest

from config import Config
from database import get_connection, init_db, list_database_columns, list_database_tables
from services.agent_runtime_service import AgentRuntimeError, public_policy, run_agent
from services.embedding_service import embed_text
from services.mysql_pool_runtime import install_mysql_pool
from services.rag_v2_service import settings as rag_settings
from services.redis_service import rate_limit
from services.schema_migration_service import apply_pending_schema_migrations, migration_manifest


ROOT = Path(__file__).resolve().parents[2]


def _sqlite_runtime(tmp_path, monkeypatch):
    monkeypatch.setattr(Config, "DB_PROVIDER", "sqlite")
    monkeypatch.setattr(Config, "DATABASE_PATH", tmp_path / "engineering-ai.sqlite3")
    monkeypatch.setattr(Config, "CONTENT_DIR", ROOT / "content")
    monkeypatch.setenv("RAG_EMBEDDING_PROVIDER", "hash")
    monkeypatch.setenv("REDIS_ENABLED", "0")
    monkeypatch.delenv("REDIS_URL", raising=False)
    init_db()
    with get_connection() as conn:
        applied = apply_pending_schema_migrations(conn)
        conn.commit()
    return applied


def test_hash_embedding_is_deterministic_96_dimensions(monkeypatch):
    monkeypatch.setenv("RAG_EMBEDDING_PROVIDER", "hash")
    first = embed_text("SafeHome RAG 工程检索")
    second = embed_text("SafeHome RAG 工程检索")
    assert first == second
    assert len(first) == 96
    assert sum(value * value for value in first) == pytest.approx(1.0, rel=1e-6)


def test_redis_disabled_is_fail_soft(monkeypatch):
    monkeypatch.setenv("REDIS_ENABLED", "0")
    monkeypatch.delenv("REDIS_URL", raising=False)
    decision = rate_limit("unit-test", limit=1, window_seconds=60)
    assert decision["available"] is False
    assert decision["allowed"] is True


def test_mysql_pool_adapter_does_not_install_for_sqlite(tmp_path, monkeypatch):
    monkeypatch.setattr(Config, "DB_PROVIDER", "sqlite")
    result = install_mysql_pool()
    assert result["installed"] is False
    assert result["reason"] == "sqlite_provider"


def test_migration_063_creates_embedding_and_agent_audit_schema(tmp_path, monkeypatch):
    _sqlite_runtime(tmp_path, monkeypatch)
    assert any(item["version"] == "2026_08_07_063" for item in migration_manifest())
    with get_connection() as conn:
        tables = {row["name"] for row in list_database_tables(conn)}
        chunk_columns = {row["name"] for row in list_database_columns(conn, "ai_knowledge_chunks")}
    assert {"agent_runs", "agent_tool_calls", "explicit_schema_migrations"}.issubset(tables)
    assert {"embedding_json", "embedding_model", "embedding_dimensions", "embedding_updated_at"}.issubset(chunk_columns)


def test_agent_rejects_non_synthetic_and_persists_hash_only_audit(tmp_path, monkeypatch):
    _sqlite_runtime(tmp_path, monkeypatch)
    actor = {"id": "researcher_engineering_test", "role": "researcher"}
    objective = "查看 MySQL Redis embedding 运行配置"

    with pytest.raises(AgentRuntimeError) as exc:
        run_agent(actor, objective, synthetic_data=False)
    assert exc.value.code == "agent_synthetic_data_required"

    result = run_agent(actor, objective, synthetic_data=True)
    assert result["status"] == "completed"
    assert result["write_tools_allowed"] is False
    assert result["plan"] == [{"tool": "runtime.config"}]
    runtime = result["outputs"][0]["result"]
    assert runtime["secrets_exposed"] is False
    assert "MYSQL_PASSWORD" not in str(runtime)
    assert "REDIS_URL" not in str(runtime)

    with get_connection() as conn:
        run_row = conn.execute("SELECT * FROM agent_runs WHERE id = ?", (result["run_id"],)).fetchone()
        tool_rows = conn.execute("SELECT * FROM agent_tool_calls WHERE run_id = ?", (result["run_id"],)).fetchall()
    assert run_row is not None
    assert len(str(run_row["objective_hash"])) == 64
    assert objective not in str(dict(run_row))
    assert len(tool_rows) == 1
    assert tool_rows[0]["tool_name"] == "runtime.config"
    assert len(str(tool_rows[0]["input_hash"])) == 64
    assert len(str(tool_rows[0]["output_hash"])) == 64


def test_agent_policy_is_read_only_and_blocks_high_impact_actions():
    policy = public_policy()
    assert policy["synthetic_data_required"] is True
    assert policy["participant_data_allowed"] is False
    assert policy["write_tools_allowed"] is False
    prohibited = set(policy["prohibited_actions"])
    assert {
        "diagnosis",
        "close_or_downgrade_risk_review",
        "change_guardian_consent",
        "delete_participant_data",
        "change_user_role",
        "approve_research_export",
        "publish_content",
        "execute_arbitrary_sql",
        "execute_shell_command",
    }.issubset(prohibited)


def test_rag_v2_tuning_defaults_are_bounded(monkeypatch):
    monkeypatch.delenv("RAG_LEXICAL_TOP_K", raising=False)
    monkeypatch.delenv("RAG_VECTOR_TOP_K", raising=False)
    monkeypatch.delenv("RAG_FINAL_CONTEXT_K", raising=False)
    monkeypatch.delenv("RAG_RRF_K", raising=False)
    cfg = rag_settings()
    assert cfg["lexical_top_k"] == 20
    assert cfg["vector_top_k"] == 30
    assert cfg["final_context_k"] == 6
    assert cfg["rrf_k"] == 60
