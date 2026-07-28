import importlib
import json
import shutil
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
CONTENT = ROOT / "content"


def _app(tmp_path, monkeypatch):
    sys.path.insert(0, str(BACKEND))
    for name in list(sys.modules):
        if name in {"app", "config", "database", "models"} or name.startswith(
            ("routes.", "services.")
        ):
            sys.modules.pop(name, None)
    content_dir = tmp_path / "content"
    shutil.copytree(CONTENT, content_dir)
    monkeypatch.setenv("APP_ENV", "testing")
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "a04.sqlite3"))
    monkeypatch.setenv("CONTENT_DIR", str(content_dir))
    monkeypatch.setenv("OFFLINE_BENCHMARK_ENABLED", "1")
    monkeypatch.setenv("OFFLINE_EXTERNAL_INGEST_ENABLED", "0")
    monkeypatch.setenv("OFFLINE_PRODUCTION_REPLACEMENT_ALLOWED", "0")
    return importlib.import_module("app").app


def _headers(app):
    specs = [("researcher-a", "researcher"), ("participant-a", "participant")]
    with app.app_context():
        database = importlib.import_module("database")
        auth_utils = importlib.import_module("routes.auth_utils")
        with database.get_connection() as conn:
            now = database.now_iso()
            for actor_id, role in specs:
                conn.execute(
                    "INSERT INTO users (id, nickname, role, source, status, created_at, updated_at) "
                    "VALUES (?, ?, ?, 'test', 'active', ?, ?)",
                    (actor_id, actor_id, role, now, now),
                )
            conn.commit()
        return {
            actor_id: {
                "Authorization": f"Bearer {auth_utils.generate_auth_token({'id': actor_id, 'role': role})}"
            }
            for actor_id, role in specs
        }


def _synthetic_payload():
    return json.loads(
        (CONTENT / "synthetic_group_network_suite.json").read_text(encoding="utf-8")
    )


def test_network_policy_defines_group_scope_privacy_and_noncausal_boundary(
    tmp_path, monkeypatch
):
    app = _app(tmp_path, monkeypatch)
    headers = _headers(app)
    client = app.test_client()
    forbidden = client.get(
        "/api/research/benchmarks/network-policy", headers=headers["participant-a"]
    )
    response = client.get(
        "/api/research/benchmarks/network-policy", headers=headers["researcher-a"]
    )
    data = response.get_json()["data"]
    assert forbidden.status_code == 403 and response.status_code == 200
    assert data["participant_visible"] is False
    assert data["training_model"] is False
    assert data["causal_inference_allowed"] is False
    assert data["individual_metrics_allowed"] is False
    assert data["minimum_privacy_thresholds"]["nodes"] >= 12
    assert set(data["boundary_variants"]) == {
        "approved_cohort",
        "observed_nodes",
        "active_nodes",
    }


def test_group_analysis_reports_boundary_missingness_and_temporal_sensitivity(
    tmp_path, monkeypatch
):
    app = _app(tmp_path, monkeypatch)
    headers = _headers(app)
    client = app.test_client()
    first = client.post(
        "/api/research/benchmarks/network/analyze",
        json=_synthetic_payload(),
        headers=headers["researcher-a"],
    )
    second = client.post(
        "/api/research/benchmarks/network/analyze",
        json=_synthetic_payload(),
        headers=headers["researcher-a"],
    )
    report = first.get_json()["data"]
    assert first.status_code == 200
    assert report["analysis_digest"] == second.get_json()["data"]["analysis_digest"]
    assert report["suppressed"] is False
    assert report["individual_metrics_included"] is False
    assert report["node_identifiers_included"] is False
    assert report["training_model"] is False
    assert report["causal_inference"] is False
    assert len(report["boundary_sensitivity"]) == 3
    assert len(report["missingness_sensitivity"]) == 3
    assert report["temporal_change"]["window_count"] == 2
    assert {
        "density",
        "weighted_strength_distribution",
        "community_size_distribution",
        "component_count",
    }.issubset(report["aggregate_metrics"])
    serialized = json.dumps(report, ensure_ascii=False)
    assert all(node["id"] not in serialized for node in _synthetic_payload()["nodes"])
    assert "核心人物" not in serialized and "边缘人物" not in serialized


def test_small_group_is_suppressed_instead_of_returning_unstable_metrics(
    tmp_path, monkeypatch
):
    app = _app(tmp_path, monkeypatch)
    headers = _headers(app)
    payload = _synthetic_payload()
    payload["nodes"] = payload["nodes"][:6]
    allowed = {item["id"] for item in payload["nodes"]}
    for window in payload["windows"]:
        window["edges"] = [
            edge
            for edge in window["edges"]
            if edge["source"] in allowed and edge["target"] in allowed
        ]
    response = app.test_client().post(
        "/api/research/benchmarks/network/analyze",
        json=payload,
        headers=headers["researcher-a"],
    )
    data = response.get_json()["data"]
    assert response.status_code == 200
    assert data["suppressed"] is True
    assert data["suppression_reason"] == "minimum_privacy_threshold_not_met"
    assert data["aggregate_metrics"] is None


def test_individual_output_and_identity_or_text_fields_are_rejected(
    tmp_path, monkeypatch
):
    app = _app(tmp_path, monkeypatch)
    headers = _headers(app)
    client = app.test_client()
    individual = _synthetic_payload()
    individual["output_mode"] = "individual_ranking"
    blocked_output = client.post(
        "/api/research/benchmarks/network/analyze",
        json=individual,
        headers=headers["researcher-a"],
    )
    unsafe = _synthetic_payload()
    unsafe["nodes"][0]["nickname"] = "不应进入分析"
    unsafe["windows"][0]["edges"][0]["raw_text"] = "不应进入分析"
    blocked_shape = client.post(
        "/api/research/benchmarks/network/analyze",
        json=unsafe,
        headers=headers["researcher-a"],
    )
    assert blocked_output.status_code == 400
    assert (
        blocked_output.get_json()["error"]["code"]
        == "network_individual_output_forbidden"
    )
    assert blocked_shape.status_code == 400
    assert (
        blocked_shape.get_json()["error"]["code"]
        == "network_sensitive_field_forbidden"
    )


def test_saved_network_run_contains_only_aggregate_report(tmp_path, monkeypatch):
    app = _app(tmp_path, monkeypatch)
    headers = _headers(app)
    response = app.test_client().post(
        "/api/research/benchmarks/runs/network", headers=headers["researcher-a"]
    )
    run = response.get_json()["data"]
    assert response.status_code == 200
    assert run["benchmark_type"] == "network_group_descriptive"
    assert run["raw_text_included"] == 0
    assert run["production_replacement_allowed"] == 0
    assert run["metrics"]["individual_metrics_included"] is False
    assert run["metrics"]["node_identifiers_included"] is False
    assert "nodes" not in run["metrics"] and "edges" not in run["metrics"]
