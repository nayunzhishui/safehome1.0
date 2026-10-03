from __future__ import annotations

import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from config import Config
from database import get_connection, init_db, list_database_columns, list_database_tables
from services.agent_runtime_service import AgentRuntimeError, public_policy, run_agent
from services.embedding_service import embed_text
from services.mysql_pool_runtime import install_mysql_pool
from services.rag_v2_service import settings as rag_settings
from services.redis_service import rate_limit
from services.schema_migration_service import apply_pending_schema_migrations, migration_manifest


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


@pytest.mark.parametrize("pooled", [False, True])
@pytest.mark.parametrize("failure", ["enter", "commit", "rollback"])
def test_mysql_adapter_releases_connection_on_transaction_failure(pooled, failure):
    from database import MySQLConnection
    from services.mysql_pool_runtime import PooledMySQLConnection

    class BrokenConnection:
        closed = False

        def ping(self, **_kwargs):
            if failure == "enter":
                raise OSError("synthetic ping failure")

        def commit(self):
            if failure == "commit":
                raise OSError("synthetic commit failure")

        def rollback(self):
            raise OSError("synthetic rollback failure")

        def close(self):
            self.closed = True

    adapter_class = PooledMySQLConnection if pooled else MySQLConnection
    adapter = adapter_class.__new__(adapter_class)
    connection = BrokenConnection()
    adapter._connection = connection
    if failure == "rollback":
        with pytest.raises(ValueError, match="original transaction failure"):
            with adapter:
                raise ValueError("original transaction failure")
    else:
        with pytest.raises(OSError, match=f"synthetic {'ping' if failure == 'enter' else 'commit'} failure"):
            with adapter:
                pass
    assert connection.closed


@pytest.mark.parametrize("pooled", [False, True])
def test_mysql_disconnect_between_writes_does_not_commit_partial_transaction(pooled):
    from database import MySQLConnection
    from services.mysql_pool_runtime import PooledMySQLConnection
    class Connection:
        def __init__(self):
            self.pending, self.saved, self.pings, self.begins = [], [], [], 0
            self.lost = self.closed = False
        def begin(self): self.begins += 1
        def ping(self, reconnect):
            self.pings.append(reconnect)
            if self.lost:
                self.pending = []
                if not reconnect: raise OSError("synthetic connection lost")
                self.lost = False
        def cursor(self): return self
        def execute(self, sql, params): self.pending.append(params[0])
        def commit(self): self.saved.extend(self.pending); self.pending = []
        def rollback(self): self.pending = []
        def close(self): self.closed = True
    adapter_class = PooledMySQLConnection if pooled else MySQLConnection
    adapter = adapter_class.__new__(adapter_class); adapter._connection = connection = Connection()
    with pytest.raises(OSError, match="connection lost"):
        with adapter:
            adapter.execute("INSERT INTO synthetic VALUES (?)", ["first"])
            connection.lost = True
            adapter.execute("INSERT INTO synthetic VALUES (?)", ["second"])
    assert connection.saved == [] and connection.closed
    assert connection.pings == [True, False, False]
    if pooled: assert connection.begins == 1


def test_mysql_pool_restarts_transaction_guard_after_explicit_commit():
    from services.mysql_pool_runtime import PooledMySQLConnection
    class Connection:
        def __init__(self): self.begins = 0
        def begin(self): self.begins += 1
        def ping(self, reconnect): pass
        def cursor(self): return self
        def execute(self, sql, params): pass
        def commit(self): pass
        def rollback(self): pass
    adapter = PooledMySQLConnection.__new__(PooledMySQLConnection); adapter._connection = connection = Connection()
    adapter.execute("SELECT 1"); adapter.execute("SELECT 2")
    adapter.commit(); adapter.execute("SELECT 3")
    adapter.rollback(); adapter.execute("SELECT 4")
    assert connection.begins == 3
