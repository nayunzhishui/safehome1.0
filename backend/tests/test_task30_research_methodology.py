import importlib
import json
import shutil
import sys
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = PROJECT_ROOT / "backend"
CONTENT_ROOT = PROJECT_ROOT / "content"


def _fresh_app(tmp_path, monkeypatch, *, enabled=True):
    sys.path.insert(0, str(BACKEND_ROOT))
    for name in list(sys.modules):
        if name in {"app", "config", "database", "models"} or name.startswith("routes.") or name.startswith("services."):
            sys.modules.pop(name, None)
    content_dir = tmp_path / "content"
    shutil.copytree(CONTENT_ROOT, content_dir)
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "task30.sqlite3"))
    monkeypatch.setenv("CONTENT_DIR", str(content_dir))
    monkeypatch.setenv("RESEARCH_METHODOLOGY_WORKBENCH_ENABLED", "1" if enabled else "0")
    monkeypatch.setenv("RESEARCH_METHODOLOGY_FORMAL_FREEZE_ALLOWED", "0")
    monkeypatch.setenv("RESEARCH_OUTCOME_ANALYSIS_ALLOWED", "0")
    monkeypatch.setenv("AI_QA_ENABLED", "0")
    monkeypatch.setenv("AI_QA_PROVIDER", "fake")
    return importlib.import_module("app").app


def _actors(app):
    specs = [("participant-a", "parent"), ("researcher-a", "researcher"), ("supervisor-a", "supervisor"), ("admin-a", "admin")]
    with app.app_context():
        database = importlib.import_module("database")
        auth_utils = importlib.import_module("routes.auth_utils")
        with database.get_connection() as conn:
            now = database.now_iso()
            for actor_id, role in specs:
                conn.execute("INSERT INTO users (id, nickname, role, source, status, created_at, updated_at) VALUES (?, ?, ?, 'test', 'active', ?, ?)", (actor_id, actor_id, role, now, now))
            conn.commit()
        return {actor_id: {"Authorization": f"Bearer {auth_utils.generate_auth_token({'id': actor_id, 'role': role})}"} for actor_id, role in specs}


def _sync(client, headers):
    response = client.post("/api/research/methodology/versions/sync", headers=headers["admin-a"])
    assert response.status_code == 200
    return response.get_json()["data"]


def test_public_status_is_safe_and_internal_routes_are_role_restricted(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    headers = _actors(app)
    client = app.test_client()
    public = client.get("/api/research/methodology/public-status")
    denied = client.get("/api/research/methodology/registry", headers=headers["participant-a"])
    forbidden_sync = client.post("/api/research/methodology/versions/sync", headers=headers["researcher-a"])
    assert public.status_code == 200
    assert public.get_json()["data"] == {
        "status": "draft_before_freeze",
        "formal_freeze_recorded": False,
        "confirmatory_analysis_allowed": False,
        "real_outcome_data_accessed": False,
        "workbench_enabled": True,
        "boundary_notice": public.get_json()["data"]["boundary_notice"],
    }
    assert denied.status_code == 403 and forbidden_sync.status_code == 403


def test_registry_is_immutable_and_machine_checks_cover_all_measures(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    headers = _actors(app)
    client = app.test_client()
    version = _sync(client, headers)
    same = _sync(client, headers)
    check = client.post("/api/research/methodology/checks/run", json={"version_id": version["id"]}, headers=headers["researcher-a"]).get_json()["data"]
    assert same["id"] == version["id"]
    assert check["worksheet_count"] == check["measure_count"] == 33
    assert check["hard_check_passed"] is True
    assert check["formal_freeze_ready"] is False and check["formal_freeze_recorded"] is False
    assert check["real_outcome_rows_read"] == 0
    assert all(check["hard_checks"].values())


def test_synthetic_simulation_is_deterministic_and_never_claims_power(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    headers = _actors(app)
    client = app.test_client()
    version = _sync(client, headers)
    first = client.post("/api/research/methodology/simulations/run", json={"version_id": version["id"]}, headers=headers["researcher-a"]).get_json()["data"]
    second = client.post("/api/research/methodology/simulations/run", json={"version_id": version["id"]}, headers=headers["researcher-a"]).get_json()["data"]
    assert first["artifact_hash"] == second["artifact_hash"]
    assert first["metrics"]["contains_real_data"] is False
    assert first["metrics"]["real_outcome_rows_read"] == 0
    assert first["metrics"]["confirmatory_power_claim"] is False
    assert [item["n"] for item in first["metrics"]["completion_precision"]] == [20, 40, 80]
    assert [item["attrition"] for item in first["metrics"]["attrition_sensitivity"]] == [0.0, 0.2, 0.4]


def test_evidence_package_requires_both_runs_and_stays_unsigned(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    headers = _actors(app)
    client = app.test_client()
    version = _sync(client, headers)
    missing = client.post("/api/research/methodology/evidence-packages", json={"version_id": version["id"]}, headers=headers["supervisor-a"])
    client.post("/api/research/methodology/checks/run", json={"version_id": version["id"]}, headers=headers["researcher-a"])
    client.post("/api/research/methodology/simulations/run", json={"version_id": version["id"]}, headers=headers["researcher-a"])
    forbidden = client.post("/api/research/methodology/evidence-packages", json={"version_id": version["id"]}, headers=headers["researcher-a"])
    created = client.post("/api/research/methodology/evidence-packages", json={"version_id": version["id"]}, headers=headers["supervisor-a"])
    data = created.get_json()["data"]
    assert missing.status_code == 409 and forbidden.status_code == 403 and created.status_code == 200
    assert data["status"] == "draft_for_human_signature"
    assert data["formal_freeze_recorded"] is False and data["confirmatory_analysis_allowed"] is False
    assert all(item["status"] == "pending_human_signature" for item in data["signature_placeholders"])


def test_disable_is_admin_only_audited_and_blocks_future_runs(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    headers = _actors(app)
    client = app.test_client()
    _sync(client, headers)
    denied = client.post("/api/research/methodology/disable", json={"reason": "专项停用演练"}, headers=headers["supervisor-a"])
    disabled = client.post("/api/research/methodology/disable", json={"reason": "专项停用演练"}, headers=headers["admin-a"])
    blocked = client.post("/api/research/methodology/checks/run", headers=headers["researcher-a"])
    assert denied.status_code == 403 and disabled.status_code == 200 and blocked.status_code == 503
    with app.app_context():
        database = importlib.import_module("database")
        with database.get_connection() as conn:
            actions = {row["action"] for row in conn.execute("SELECT action FROM audit_logs WHERE action LIKE 'research_methodology_%'").fetchall()}
    assert {"research_methodology_registry_synced", "research_methodology_workbench_disabled"} <= actions


def test_config_forbids_programmatic_freeze_and_outcome_analysis(monkeypatch):
    sys.path.insert(0, str(BACKEND_ROOT))
    monkeypatch.setenv("RESEARCH_METHODOLOGY_FORMAL_FREEZE_ALLOWED", "1")
    for name in ["config"]:
        sys.modules.pop(name, None)
    with pytest.raises(RuntimeError, match="RESEARCH_METHODOLOGY_FORMAL_FREEZE_ALLOWED"):
        importlib.import_module("config").Config.validate()
    monkeypatch.setenv("RESEARCH_METHODOLOGY_FORMAL_FREEZE_ALLOWED", "0")
    monkeypatch.setenv("RESEARCH_OUTCOME_ANALYSIS_ALLOWED", "1")
    sys.modules.pop("config", None)
    with pytest.raises(RuntimeError, match="RESEARCH_OUTCOME_ANALYSIS_ALLOWED"):
        importlib.import_module("config").Config.validate()


def test_disabled_workbench_keeps_read_only_structure_but_blocks_runs(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch, enabled=False)
    headers = _actors(app)
    client = app.test_client()
    config = client.get("/api/research/methodology/config", headers=headers["researcher-a"])
    registry = client.get("/api/research/methodology/registry", headers=headers["researcher-a"])
    sync = client.post("/api/research/methodology/versions/sync", headers=headers["admin-a"])
    assert config.status_code == 200 and config.get_json()["data"]["workbench_enabled"] is False
    assert registry.status_code == 200 and len(registry.get_json()["data"]["measures"]) == 33
    assert sync.status_code == 409


def test_nine_point_scores_preserve_raw_and_separate_model_input(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    headers = _actors(app)
    client = app.test_client()
    worksheet = json.loads((CONTENT_ROOT / "assessment_worksheets.json").read_text(encoding="utf-8"))["worksheets"]
    worksheet = next(item for item in worksheet if item["id"] == "regulatory_focus_relationship_18")
    answers = [{"question_id": item["id"], "value": "9"} for item in worksheet["questions"]]
    response = client.post("/api/assessment-results", json={"worksheet_id": worksheet["id"], "answers": answers}, headers=headers["participant-a"])
    data = response.get_json()["data"]
    assert response.status_code == 201
    assert set(data["raw_scores"]["item_scores"].values()) == {9}
    assert set(data["transformed_scores"]["item_scores"].values()) == {5.0}
    assert data["transformation_version"] == "linear_9_to_5_v1"
    detail = client.get(f"/api/assessment-results/{data['id']}", headers=headers["participant-a"]).get_json()["data"]
    profile = client.get(f"/api/assessment-results/{data['id']}/profile-position", headers=headers["participant-a"]).get_json()["data"]
    assert detail["raw_scale"]["ranges"] == [{"min": 1.0, "max": 9.0}]
    assert profile["score_spaces_separated"] is True
    assert set(profile["raw_scores"].values()) == {9.0}
    assert set(profile["model_input_scores"].values()) == {5.0}


def test_other_five_point_scale_has_no_transform(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    headers = _actors(app)
    client = app.test_client()
    worksheets = json.loads((CONTENT_ROOT / "assessment_worksheets.json").read_text(encoding="utf-8"))["worksheets"]
    worksheet = next(item for item in worksheets if item["id"] == "relationship_initiation_intention_action")
    answers = [{"question_id": item["id"], "value": "5"} for item in worksheet["questions"]]
    data = client.post("/api/assessment-results", json={"worksheet_id": worksheet["id"], "answers": answers}, headers=headers["participant-a"]).get_json()["data"]
    assert data["transformed_scores"] == {}
    assert data["transformation_version"] is None


def test_methodology_service_source_never_queries_outcome_tables():
    source = (BACKEND_ROOT / "services" / "research_methodology_service.py").read_text(encoding="utf-8")
    for table in ("assessment_results", "emotion_diaries", "feedback_results", "checkins", "student_profiles"):
        assert table not in source
