import importlib
import shutil
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = PROJECT_ROOT / "backend"
CONTENT_ROOT = PROJECT_ROOT / "content"


def _fresh_app(tmp_path, monkeypatch):
    sys.path.insert(0, str(BACKEND_ROOT))
    for name in list(sys.modules):
        if name in {"app", "config", "database", "models"} or name.startswith("routes.") or name.startswith("services."):
            sys.modules.pop(name, None)
    content_dir = tmp_path / "content"
    shutil.copytree(CONTENT_ROOT, content_dir)
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "task28.sqlite3"))
    monkeypatch.setenv("CONTENT_DIR", str(content_dir))
    monkeypatch.setenv("AI_QA_ENABLED", "0")
    monkeypatch.setenv("AI_QA_SANDBOX_ENABLED", "1")
    monkeypatch.setenv("AI_QA_PROVIDER", "fake")
    return importlib.import_module("app").app


def test_task28_content_contract_is_valid_and_keeps_participant_gate_closed():
    sys.path.insert(0, str(BACKEND_ROOT))
    validator = importlib.import_module("scripts.validate_content")
    errors = validator.validate_content(CONTENT_ROOT, CONTENT_ROOT / "schemas")
    assert errors == []


def test_task28_schema_migration_audit_and_rollback_are_non_destructive(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    with app.app_context():
        migration = importlib.import_module("scripts.migrate_task28_ai_qa")
        result = migration.audit()
        rollback = migration.rollback_plan()
    assert result["ok"] is True
    assert len(result["tables"]) == 8
    assert rollback["automatic_rollback_executed"] is False
    assert rollback["destructive_step_requires_human_approval"] is True
    assert rollback["participant_release_approval_inferred"] is False


def test_task28_mysql_schema_contract_keeps_ai_keys_indexable(tmp_path, monkeypatch):
    _fresh_app(tmp_path, monkeypatch)
    database = importlib.import_module("database")
    models = importlib.import_module("models")
    statements = [sql for sql in models.SCHEMA_SQL if "CREATE TABLE IF NOT EXISTS ai_qa" in sql]
    assert len(statements) >= 8
    converted = [database.mysqlize_schema_statement(sql) for sql in statements]
    assert all("TEXT PRIMARY KEY" not in sql for sql in converted)
    assert any("UNIQUE(message_id, user_id)" in sql for sql in converted)


def test_task28_ai_qa_raw_and_derived_session_data_is_in_privacy_whitelist(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    with app.app_context():
        database = importlib.import_module("database")
        privacy = importlib.import_module("services.privacy_request_service")
        user_id = "researcher-privacy-task28"
        now = database.now_iso()
        tables = ("ai_qa_feedback", "ai_qa_messages", "ai_qa_safety_events", "ai_qa_provider_events", "ai_qa_sessions")
        assert set(tables) <= set(privacy.SCOPE_TABLES["messages_and_notifications"])
        with database.get_connection() as conn:
            conn.execute("INSERT INTO users (id, nickname, role, source, status, created_at, updated_at) VALUES (?, '研究者', 'researcher', 'test', 'active', ?, ?)", (user_id, now, now))
            conn.execute("INSERT INTO ai_qa_sessions (id, user_id, mode, status, synthetic_data, context_policy, research_use_allowed, created_at, updated_at) VALUES ('aiqs-privacy', ?, 'research_sandbox', 'active', 1, 'current_session_only', 0, ?, ?)", (user_id, now, now))
            conn.execute("INSERT INTO ai_qa_messages (id, session_id, user_id, role, content, citations_json, model_json, safety_json, prompt_version, knowledge_version, token_estimate, cost_micros, created_at) VALUES ('aiqm-privacy', 'aiqs-privacy', ?, 'user', '合成文本', '[]', '{}', '{}', 'v1', 'k1', 1, 0, ?)", (user_id, now))
            conn.execute("INSERT INTO ai_qa_feedback (id, message_id, session_id, user_id, evaluation, research_use_allowed, created_at) VALUES ('aiqf-privacy', 'aiqm-privacy', 'aiqs-privacy', ?, 'helpful', 0, ?)", (user_id, now))
            conn.execute("INSERT INTO ai_qa_safety_events (id, session_id, user_id, request_hash, category, severity, outcome, metadata_json, created_at) VALUES ('aiqse-privacy', 'aiqs-privacy', ?, 'hash', 'allowed', 'low', 'answered', '{}', ?)", (user_id, now))
            conn.execute("INSERT INTO ai_qa_provider_events (id, session_id, user_id, provider, model_version, status, latency_ms, token_estimate, cost_micros, created_at) VALUES ('aiqpe-privacy', 'aiqs-privacy', ?, 'fake', 'fake-v1', 'success', 1, 1, 0, ?)", (user_id, now))
            for table in tables:
                assert privacy._table_count(conn, table, user_id) == 1
                assert privacy._delete_table_rows(conn, table, user_id) == 1
            conn.commit()
            assert all(privacy._table_count(conn, table, user_id) == 0 for table in tables)


def test_task28_shared_web_and_miniprogram_contracts_keep_participant_api_hidden():
    constants = (PROJECT_ROOT / "shared" / "constants" / "api.ts").read_text(encoding="utf-8")
    types = (PROJECT_ROOT / "shared" / "types" / "api.ts").read_text(encoding="utf-8")
    web_api = (PROJECT_ROOT / "apps" / "web" / "src" / "services" / "safehomeApi.ts").read_text(encoding="utf-8")
    mini_api = (PROJECT_ROOT / "apps" / "miniprogram" / "services" / "api.js").read_text(encoding="utf-8")
    main = (PROJECT_ROOT / "apps" / "web" / "src" / "main.tsx").read_text(encoding="utf-8")
    assert all(name in constants for name in ("aiQaConfig", "aiQaSessions", "aiQaEvaluation", "aiQaReviewEvidence", "aiQaKillSwitch"))
    assert all(name in types for name in ("AiQaConfig", "AiQaSession", "AiQaCitation", "AiQaEvaluationRun"))
    assert "createAiQaSession" in web_api and "runAiQaEvaluation" in web_api
    assert 'href: "/ai-sandbox"' in main
    assert "getAiQaConfig" in mini_api
    assert "sendAiQaMessage" not in mini_api
    assert "createAiQaSession" not in mini_api
