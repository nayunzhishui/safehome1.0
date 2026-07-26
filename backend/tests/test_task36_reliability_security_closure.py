import json
import importlib
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"


def _fresh_app(tmp_path, monkeypatch):
    sys.path.insert(0, str(BACKEND))
    for name in list(sys.modules):
        if name in {"app", "config", "database", "models"} or name.startswith("routes.") or name.startswith("services."):
            sys.modules.pop(name, None)
    monkeypatch.setenv("APP_ENV", "testing")
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "task36-f17.sqlite3"))
    monkeypatch.setenv("CONTENT_DIR", str(ROOT / "content"))
    monkeypatch.setenv("RELIABILITY_WORKBENCH_ENABLED", "1")
    monkeypatch.setenv("AI_QA_ENABLED", "0")
    monkeypatch.setenv("AI_QA_PROVIDER", "fake")
    return importlib.import_module("app").app


def _actors(app):
    with app.app_context():
        from database import get_connection, now_iso
        from routes.auth_utils import generate_auth_token

        actors = {"researcher-f17": "researcher", "admin-f17": "admin"}
        now = now_iso()
        with get_connection() as conn:
            for actor_id, role in actors.items():
                conn.execute(
                    "INSERT INTO users (id, nickname, role, status, created_at, updated_at) VALUES (?, ?, ?, 'active', ?, ?)",
                    (actor_id, actor_id, role, now, now),
                )
            conn.commit()
        return {
            actor_id: {"Authorization": f"Bearer {generate_auth_token({'id': actor_id, 'role': role})}"}
            for actor_id, role in actors.items()
        }


def test_task36_registry_closes_six_journeys_and_keeps_production_off():
    registry = json.loads(
        (ROOT / "content" / "task36_reliability_security_registry.json").read_text(encoding="utf-8")
    )
    assert registry["schema"] == "safehome.task36.reliability_security.v1"
    assert {item["id"] for item in registry["journeys"]} == {
        "messages", "checkins", "login", "research_analysis", "ai_qa", "therapeutic_assessment"
    }
    assert all(not value for value in registry["production_defaults"].values())
    assert registry["temporary_showcase_exception_is_evidence"] is False
    assert registry["formal_permission_acceptance_passed"] is False
    assert registry["production_release_approved"] is False
    assert "password" in registry["forbidden_evidence_fields"]
    assert "participant_text" in registry["forbidden_evidence_fields"]


def test_reliability_workbench_exposes_redacted_task36_matrix(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    headers = _actors(app)
    app.config["RELIABILITY_WORKBENCH_ENABLED"] = True
    response = app.test_client().get("/api/reliability/workbench", headers=headers["admin-f17"])
    assert response.status_code == 200
    payload = response.get_json()["data"]["task36_integration"]
    assert payload["production_release_approved"] is False
    assert len(payload["journeys"]) == 6
    assert all("payload" not in item and "body" not in item for item in payload["journeys"])


def test_security_workbench_exposes_same_release_blockers(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    headers = _actors(app)
    response = app.test_client().get("/api/security/workbench", headers=headers["admin-f17"])
    assert response.status_code == 200
    payload = response.get_json()["data"]["task36_integration"]
    assert payload["temporary_showcase_exception_is_evidence"] is False
    assert "cloudbase_observation" in payload["external_gates"]


def test_analysis_catalog_includes_recovery_and_deletion_contract(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    headers = _actors(app)
    response = app.test_client().get("/api/research/analysis/catalog", headers=headers["researcher-f17"])
    assert response.status_code == 200
    summary = response.get_json()["data"]["resilience_summary"]
    assert summary["idempotency"] is True
    assert summary["dead_letter"] is True
    assert summary["manual_recovery"] is True
    assert summary["derived_deletion"] == "derived_artifact_tombstone"
    assert summary["production_release_approved"] is False


def test_ai_qa_tables_remain_in_participant_deletion_scope():
    source = (ROOT / "backend" / "services" / "privacy_request_service.py").read_text(encoding="utf-8")
    for table in ("ai_qa_sessions", "ai_qa_messages", "ai_qa_feedback", "ai_qa_provider_events"):
        assert f'"{table}"' in source
