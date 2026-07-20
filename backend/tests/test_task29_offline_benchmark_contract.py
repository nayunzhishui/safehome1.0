import importlib
import json
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = PROJECT_ROOT / "backend"
CONTENT_ROOT = PROJECT_ROOT / "content"


def test_task29_content_and_generated_fixture_are_deterministic():
    sys.path.insert(0, str(BACKEND_ROOT))
    validator = importlib.import_module("scripts.validate_content")
    assert validator.validate_content(CONTENT_ROOT, CONTENT_ROOT / "schemas") == []
    result = subprocess.run([sys.executable, str(BACKEND_ROOT / "scripts" / "generate_task29_synthetic_benchmark.py"), "--check"], cwd=PROJECT_ROOT, capture_output=True, text=True)
    assert result.returncode == 0 and "240 cases" in result.stdout


def test_task29_registry_blocks_unapproved_external_downloads():
    registry = json.loads((CONTENT_ROOT / "offline_benchmark_registry.json").read_text(encoding="utf-8"))
    assert registry["external_ingest_enabled"] is False
    assert registry["production_replacement_allowed"] is False
    external = [card for card in registry["cards"] if card["platform"] != "synthetic"]
    assert external
    assert all(card["ingest_status"].startswith("blocked_") for card in external)
    assert all(card["local_path"] is None and card["artifact_sha256"] is None for card in external)


def test_task29_schema_is_mysql_portable_and_rollback_non_destructive(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "task29-contract.sqlite3"))
    monkeypatch.setenv("CONTENT_DIR", str(CONTENT_ROOT))
    sys.path.insert(0, str(BACKEND_ROOT))
    for name in ["config", "database", "models", "scripts.migrate_task29_offline_benchmarks"]:
        sys.modules.pop(name, None)
    database = importlib.import_module("database")
    models = importlib.import_module("models")
    database.init_db()
    migration = importlib.import_module("scripts.migrate_task29_offline_benchmarks")
    assert migration.audit()["ok"] is True
    assert len(migration.audit()["tables"]) == 5
    assert migration.rollback_plan()["destructive_step_requires_human_approval"] is True
    statements = [sql for sql in models.SCHEMA_SQL if "CREATE TABLE IF NOT EXISTS offline_" in sql]
    assert len(statements) == 5
    converted = [database.mysqlize_schema_statement(sql) for sql in statements]
    assert all("TEXT PRIMARY KEY" not in sql for sql in converted)


def test_task29_shared_web_and_miniprogram_contracts_have_no_participant_run_method():
    constants = (PROJECT_ROOT / "shared" / "constants" / "api.ts").read_text(encoding="utf-8")
    types = (PROJECT_ROOT / "shared" / "types" / "api.ts").read_text(encoding="utf-8")
    web = (PROJECT_ROOT / "apps" / "web" / "src" / "services" / "safehomeApi.ts").read_text(encoding="utf-8")
    mini = (PROJECT_ROOT / "apps" / "miniprogram" / "services" / "api.js").read_text(encoding="utf-8")
    assert "offlineBenchmarks" in constants
    assert all(name in types for name in ("OfflineBenchmarkConfig", "OfflineDatasetCard", "OfflineBenchmarkRun", "OfflineAgreementSummary"))
    assert "runOfflineBenchmark" in web and "reviewOfflineBenchmark" in web
    assert "getOfflineBenchmarkConfig" in mini
    assert "runOfflineBenchmark" not in mini and "syncOfflineDatasetCards" not in mini
