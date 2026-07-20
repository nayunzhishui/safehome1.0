import importlib
import json
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = PROJECT_ROOT / "backend"
CONTENT_ROOT = PROJECT_ROOT / "content"


def test_task30_registry_is_deterministic_and_has_no_fake_approval():
    result = subprocess.run([sys.executable, str(BACKEND_ROOT / "scripts" / "generate_task30_methodology_registry.py"), "--check"], cwd=PROJECT_ROOT, capture_output=True, text=True)
    assert result.returncode == 0 and "33 measures" in result.stdout
    registry = json.loads((CONTENT_ROOT / "research_methodology_registry.json").read_text(encoding="utf-8"))
    assert registry["status"] == "draft_before_freeze"
    assert registry["formal_freeze_allowed"] is False and registry["confirmatory_analysis_allowed"] is False
    assert registry["generated_from"]["outcome_rows_read"] == 0
    assert all(item["status"] == "pending_human_signature" for item in registry["signature_requirements"])


def test_task30_content_validator_and_reporting_sources():
    sys.path.insert(0, str(BACKEND_ROOT))
    validator = importlib.import_module("scripts.validate_content")
    assert validator.validate_content(CONTENT_ROOT, CONTENT_ROOT / "schemas") == []
    registry = json.loads((CONTENT_ROOT / "research_methodology_registry.json").read_text(encoding="utf-8"))
    standards = {item["id"]: item for item in registry["reporting_standards"]}
    assert standards["APA_JARS_QUANT"]["status"] == "applicable"
    assert standards["STROBE"]["status"] == "conditional"
    assert standards["SPIRIT_2025"]["status"] == "not_currently_applicable"
    assert standards["CONSORT_2025"]["status"] == "not_currently_applicable"
    assert standards["DECIDE_AI"]["status"].startswith("future_conditional")


def test_task30_schema_migration_and_non_destructive_rollback(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "task30-contract.sqlite3"))
    monkeypatch.setenv("CONTENT_DIR", str(CONTENT_ROOT))
    sys.path.insert(0, str(BACKEND_ROOT))
    for name in ["config", "database", "models", "scripts.migrate_task30_research_methodology"]:
        sys.modules.pop(name, None)
    database = importlib.import_module("database")
    models = importlib.import_module("models")
    database.init_db()
    migration = importlib.import_module("scripts.migrate_task30_research_methodology")
    assert migration.audit()["ok"] is True
    assert len(migration.audit()["tables"]) == 5
    plan = migration.rollback_plan()
    assert plan["destructive_step_requires_human_approval"] is True
    assert plan["formal_freeze_inferred"] is False and plan["production_release_inferred"] is False
    statements = [sql for sql in models.SCHEMA_SQL if "CREATE TABLE IF NOT EXISTS research_methodology_" in sql]
    assert len(statements) == 5
    converted = [database.mysqlize_schema_statement(sql) for sql in statements]
    assert all("TEXT PRIMARY KEY" not in sql for sql in converted)


def test_task30_migration_backfills_legacy_score_provenance_idempotently(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "task30-backfill.sqlite3"))
    monkeypatch.setenv("CONTENT_DIR", str(CONTENT_ROOT))
    sys.path.insert(0, str(BACKEND_ROOT))
    for name in ["config", "database", "models", "services.assessment_execution_service", "scripts.migrate_task30_research_methodology"]:
        sys.modules.pop(name, None)
    database = importlib.import_module("database")
    database.init_db()
    worksheets = json.loads((CONTENT_ROOT / "assessment_worksheets.json").read_text(encoding="utf-8"))["worksheets"]
    worksheet = next(item for item in worksheets if item["id"] == "regulatory_focus_relationship_18")
    answers = [{"question_id": item["id"], "value": "9", "score": 9} for item in worksheet["questions"]]
    scores = {"total_score": 162, "dimensions": []}
    with database.get_connection() as conn:
        now = database.now_iso()
        conn.execute("INSERT INTO users (id, nickname, role, source, status, created_at, updated_at) VALUES ('legacy-user', 'legacy', 'parent', 'test', 'active', ?, ?)", (now, now))
        conn.execute(
            """INSERT INTO assessment_results
               (id, user_id, worksheet_id, worksheet_title, category, answers_json, scores_json, total_score, result_summary, created_at)
               VALUES ('legacy-result', 'legacy-user', ?, ?, ?, ?, ?, 162, 'legacy', ?)""",
            (worksheet["id"], worksheet["display_title"], worksheet.get("category"), database.json_dumps(answers), database.json_dumps(scores), now),
        )
        conn.commit()
    migration = importlib.import_module("scripts.migrate_task30_research_methodology")
    first = migration.backfill_score_provenance()
    second = migration.backfill_score_provenance()
    assert first == {"updated": 1, "already_present": 0, "unknown_worksheet": 0}
    assert second == {"updated": 0, "already_present": 1, "unknown_worksheet": 0}
    with database.get_connection() as conn:
        row = conn.execute("SELECT raw_scores_json, transformed_scores_json, transformation_version FROM assessment_results WHERE id = 'legacy-result'").fetchone()
    assert set(database.json_loads(row["raw_scores_json"], {})["item_scores"].values()) == {9}
    assert set(database.json_loads(row["transformed_scores_json"], {})["item_scores"].values()) == {5.0}
    assert row["transformation_version"] == "linear_9_to_5_v1"


def test_task30_shared_web_and_miniprogram_surface_is_role_appropriate():
    constants = (PROJECT_ROOT / "shared" / "constants" / "api.ts").read_text(encoding="utf-8")
    types = (PROJECT_ROOT / "shared" / "types" / "api.ts").read_text(encoding="utf-8")
    web = (PROJECT_ROOT / "apps" / "web" / "src" / "services" / "safehomeApi.ts").read_text(encoding="utf-8")
    mini = (PROJECT_ROOT / "apps" / "miniprogram" / "services" / "api.js").read_text(encoding="utf-8")
    assert "researchMethodology" in constants
    assert all(name in types for name in ("ResearchMethodologyConfig", "ResearchMethodologyRegistry", "ResearchMethodologySimulation"))
    assert "runResearchMethodologyChecks" in web and "createResearchMethodologyEvidencePackage" in web
    assert "getResearchMethodologyPublicStatus" in mini
    assert "runResearchMethodologyChecks" not in mini and "syncResearchMethodologyRegistry" not in mini


def test_task30_existing_profile_model_artifact_is_not_changed_by_methodology_generator():
    profile_path = CONTENT_ROOT / "readfeedback" / "student_profile_model.json"
    before = profile_path.read_bytes()
    result = subprocess.run([sys.executable, str(BACKEND_ROOT / "scripts" / "generate_task30_methodology_registry.py"), "--check"], cwd=PROJECT_ROOT)
    assert result.returncode == 0 and profile_path.read_bytes() == before
