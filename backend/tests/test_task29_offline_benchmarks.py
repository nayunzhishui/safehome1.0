import importlib
import shutil
import sys
from pathlib import Path


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
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "task29.sqlite3"))
    monkeypatch.setenv("CONTENT_DIR", str(content_dir))
    monkeypatch.setenv("OFFLINE_BENCHMARK_ENABLED", "1" if enabled else "0")
    monkeypatch.setenv("OFFLINE_EXTERNAL_INGEST_ENABLED", "0")
    monkeypatch.setenv("OFFLINE_PRODUCTION_REPLACEMENT_ALLOWED", "0")
    monkeypatch.setenv("AI_QA_ENABLED", "0")
    monkeypatch.setenv("AI_QA_PROVIDER", "fake")
    return importlib.import_module("app").app


def _actors(app):
    specs = [("researcher-a", "researcher"), ("researcher-b", "researcher"), ("supervisor-a", "supervisor"), ("admin-a", "admin")]
    with app.app_context():
        database = importlib.import_module("database")
        auth_utils = importlib.import_module("routes.auth_utils")
        with database.get_connection() as conn:
            now = database.now_iso()
            for actor_id, role in specs:
                conn.execute("INSERT INTO users (id, nickname, role, source, status, created_at, updated_at) VALUES (?, ?, ?, 'test', 'active', ?, ?)", (actor_id, actor_id, role, now, now))
            conn.commit()
        return {actor_id: {"Authorization": f"Bearer {auth_utils.generate_auth_token({'id': actor_id, 'role': role})}"} for actor_id, role in specs}


def test_registry_sync_records_blocked_external_sources_without_downloading(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    headers = _actors(app)
    client = app.test_client()
    forbidden = client.post("/api/research/benchmarks/dataset-cards/sync", headers=headers["researcher-a"])
    response = client.post("/api/research/benchmarks/dataset-cards/sync", headers=headers["admin-a"])
    cards = client.get("/api/research/benchmarks/dataset-cards", headers=headers["researcher-a"]).get_json()["data"]["items"]
    assert forbidden.status_code == 403
    assert response.get_json()["data"]["external_downloaded"] is False
    assert len(cards) == 5
    external = [item for item in cards if item["platform"] not in {"synthetic"}]
    assert external and all(item["local_path"] is None and item["artifact_sha256"] is None for item in external)
    assert all(item["allowed_uses"] == ["metadata_review_only"] for item in external)


def test_blind_case_api_hides_generator_labels_and_limits_page(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    headers = _actors(app)
    response = app.test_client().get("/api/research/benchmarks/cases?limit=500", headers=headers["researcher-a"])
    data = response.get_json()["data"]
    assert response.status_code == 200
    assert data["blind"] is True and data["generator_labels_included"] is False
    assert len(data["items"]) == 50 and data["total"] == 240
    assert all("generator_label" not in item for item in data["items"])


def test_annotations_are_actor_scoped_blind_and_agreement_needs_two_people(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    headers = _actors(app)
    client = app.test_client()
    payload = {"emotion_label": "anxiety", "valence": -0.7, "arousal": 0.7, "context": "synthetic", "reflex_node": "emotion"}
    first = client.post("/api/research/benchmarks/cases/syn-affect-001/annotations", json=payload, headers=headers["researcher-a"])
    one = client.get("/api/research/benchmarks/agreement", headers=headers["supervisor-a"]).get_json()["data"]
    second = client.post("/api/research/benchmarks/cases/syn-affect-001/annotations", json=payload, headers=headers["researcher-b"])
    two = client.get("/api/research/benchmarks/agreement", headers=headers["supervisor-a"]).get_json()["data"]
    assert first.get_json()["data"]["generator_label_visible"] is False
    assert one["complete_double_annotated_cases"] == 0
    assert second.status_code == 200 and two["complete_double_annotated_cases"] == 1
    assert two["emotion_cohen_kappa"] == 1.0
    assert two["agreement_thresholds"] == {
        "emotion_cohen_kappa": 0.7,
        "maximum_mean_valence_gap": 0.25,
        "maximum_mean_arousal_gap": 0.2,
        "minimum_complete_cases": 200,
    }
    assert two["human_gold_release_eligible"] is False and two["human_gold_released"] is False


def test_annotation_validation_rejects_unknown_labels_and_ranges(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    headers = _actors(app)
    client = app.test_client()
    invalid_label = client.post("/api/research/benchmarks/cases/syn-affect-001/annotations", json={"emotion_label": "diagnosis", "valence": 0, "arousal": 0.5, "reflex_node": "emotion"}, headers=headers["researcher-a"])
    invalid_range = client.post("/api/research/benchmarks/cases/syn-affect-001/annotations", json={"emotion_label": "calm", "valence": 2, "arousal": 0.5, "reflex_node": "emotion"}, headers=headers["researcher-a"])
    assert invalid_label.status_code == 400 and invalid_range.status_code == 400


def test_affect_benchmark_reports_full_metrics_without_calling_it_human_gold(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    headers = _actors(app)
    client = app.test_client()
    response = client.post("/api/research/benchmarks/runs/affect", headers=headers["researcher-a"])
    run = response.get_json()["data"]
    metrics = run["metrics"]
    assert response.status_code == 200
    assert metrics["sample_count"] == 240
    assert all(key in metrics for key in ("coverage_rate", "macro_f1_against_generator_seed", "confusion_matrix", "calibration_error", "subgroups", "failed_cases"))
    assert metrics["human_gold_used"] is False
    assert run["raw_text_included"] == 0 and run["production_replacement_allowed"] == 0


def test_network_benchmark_validates_weight_threshold_stability_and_boundary(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    headers = _actors(app)
    run = app.test_client().post("/api/research/benchmarks/runs/network", headers=headers["researcher-a"]).get_json()["data"]
    metrics = run["metrics"]
    assert metrics["suppressed"] is False
    assert metrics["individual_metrics_included"] is False
    assert metrics["node_identifiers_included"] is False
    assert len(metrics["boundary_sensitivity"]) == 3
    assert len(metrics["missingness_sensitivity"]) == 3
    assert metrics["family_quality_inference"] is False


def test_researcher_only_lists_own_runs_while_supervisor_sees_all(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    headers = _actors(app)
    client = app.test_client()
    client.post("/api/research/benchmarks/runs/network", headers=headers["researcher-a"])
    client.post("/api/research/benchmarks/runs/network", headers=headers["researcher-b"])
    own = client.get("/api/research/benchmarks/runs", headers=headers["researcher-a"]).get_json()["data"]["items"]
    all_runs = client.get("/api/research/benchmarks/runs", headers=headers["supervisor-a"]).get_json()["data"]["items"]
    assert len(own) == 1 and own[0]["created_by"] == "researcher-a"
    assert len(all_runs) == 2


def test_review_and_disable_are_role_restricted_and_audited(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    headers = _actors(app)
    client = app.test_client()
    run = client.post("/api/research/benchmarks/runs/network", headers=headers["researcher-a"]).get_json()["data"]
    forbidden_review = client.post(f"/api/research/benchmarks/runs/{run['id']}/reviews", json={"decision": "engineering_reviewed", "evidence_path": "evidence/t29.md"}, headers=headers["researcher-a"])
    review = client.post(f"/api/research/benchmarks/runs/{run['id']}/reviews", json={"decision": "engineering_reviewed", "evidence_path": "evidence/t29.md"}, headers=headers["supervisor-a"])
    forbidden_disable = client.post("/api/research/benchmarks/disable", json={"reason": "工程停用演练"}, headers=headers["supervisor-a"])
    disabled = client.post("/api/research/benchmarks/disable", json={"reason": "工程停用演练"}, headers=headers["admin-a"])
    blocked = client.post("/api/research/benchmarks/runs/network", headers=headers["researcher-a"])
    assert forbidden_review.status_code == 403 and review.status_code == 200
    assert forbidden_disable.status_code == 403 and disabled.status_code == 200
    assert blocked.status_code == 503
    with app.app_context():
        database = importlib.import_module("database")
        with database.get_connection() as conn:
            actions = {row["action"] for row in conn.execute("SELECT action FROM audit_logs WHERE action LIKE 'offline_%'").fetchall()}
    assert {"offline_benchmark_run_created", "offline_benchmark_review_saved", "offline_benchmark_disabled"} <= actions


def test_disabled_config_and_production_replacement_flags_cannot_be_enabled(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch, enabled=False)
    headers = _actors(app)
    blocked = app.test_client().post("/api/research/benchmarks/runs/network", headers=headers["researcher-a"])
    assert blocked.status_code == 409
    monkeypatch.setenv("OFFLINE_EXTERNAL_INGEST_ENABLED", "1")
    for name in ["config"]:
        sys.modules.pop(name, None)
    with __import__("pytest").raises(RuntimeError, match="OFFLINE_EXTERNAL_INGEST_ENABLED"):
        importlib.import_module("config").Config.validate()
