import importlib
from itertools import combinations
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
    assert [
        item["metrics"]["node_count"] for item in report["boundary_sensitivity"]
    ] == [18, 16, 14]
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


def test_each_window_must_meet_edge_privacy_threshold(tmp_path, monkeypatch):
    app = _app(tmp_path, monkeypatch)
    headers = _headers(app)
    payload = _synthetic_payload()
    payload["windows"][0]["edges"] = payload["windows"][0]["edges"][:9]

    response = app.test_client().post(
        "/api/research/benchmarks/network/analyze",
        json=payload,
        headers=headers["researcher-a"],
    )

    data = response.get_json()["data"]
    assert response.status_code == 200
    assert data["suppressed"] is True
    assert data["analysis_summary"]["minimum_window_edge_count"] == 9
    assert data["analysis_summary"]["insufficient_window_count"] == 1


def test_edge_privacy_threshold_only_counts_approved_cohort_edges(
    tmp_path, monkeypatch
):
    app = _app(tmp_path, monkeypatch)
    headers = _headers(app)
    payload = _synthetic_payload()
    approved_ids = {item["id"] for item in payload["nodes"][:12]}
    outside_ids = [item["id"] for item in payload["nodes"][12:]]
    for node in payload["nodes"]:
        node["approved_cohort"] = node["id"] in approved_ids
    outside_edges = [
        {"source": source, "target": target, "weight": 1}
        for source, target in list(combinations(outside_ids, 2))[:10]
    ]
    for window in payload["windows"]:
        window["edges"] = outside_edges

    response = app.test_client().post(
        "/api/research/benchmarks/network/analyze",
        json=payload,
        headers=headers["researcher-a"],
    )

    data = response.get_json()["data"]
    assert response.status_code == 200
    assert data["suppressed"] is True
    assert data["analysis_summary"]["minimum_window_edge_count"] == 0
    assert data["analysis_summary"]["insufficient_window_count"] == 2


def test_network_boundary_flags_require_json_booleans(tmp_path, monkeypatch):
    app = _app(tmp_path, monkeypatch)
    headers = _headers(app)
    client = app.test_client()
    for field in ("approved_cohort", "observed", "active"):
        for invalid_value in ("false", 0, None):
            payload = _synthetic_payload()
            payload["nodes"][0][field] = invalid_value
            response = client.post(
                "/api/research/benchmarks/network/analyze",
                json=payload,
                headers=headers["researcher-a"],
            )
            assert response.status_code == 400
            assert (
                response.get_json()["error"]["code"]
                == "network_node_boundary_invalid"
            )


def test_network_windows_are_analyzed_in_chronological_order(tmp_path, monkeypatch):
    app = _app(tmp_path, monkeypatch)
    headers = _headers(app)
    client = app.test_client()
    chronological = _synthetic_payload()
    reversed_windows = _synthetic_payload()
    reversed_windows["windows"] = list(reversed(reversed_windows["windows"]))

    expected = client.post(
        "/api/research/benchmarks/network/analyze",
        json=chronological,
        headers=headers["researcher-a"],
    ).get_json()["data"]
    actual = client.post(
        "/api/research/benchmarks/network/analyze",
        json=reversed_windows,
        headers=headers["researcher-a"],
    ).get_json()["data"]

    assert actual["temporal_change"] == expected["temporal_change"]
    assert actual["analysis_digest"] == expected["analysis_digest"]


def test_network_rejects_duplicate_or_overlapping_windows(tmp_path, monkeypatch):
    app = _app(tmp_path, monkeypatch)
    headers = _headers(app)
    client = app.test_client()
    duplicate = _synthetic_payload()
    duplicate["windows"][1]["id"] = duplicate["windows"][0]["id"]
    overlap = _synthetic_payload()
    overlap["windows"][1]["start_date"] = overlap["windows"][0]["end_date"]

    duplicate_response = client.post(
        "/api/research/benchmarks/network/analyze",
        json=duplicate,
        headers=headers["researcher-a"],
    )
    overlap_response = client.post(
        "/api/research/benchmarks/network/analyze",
        json=overlap,
        headers=headers["researcher-a"],
    )

    assert duplicate_response.status_code == 400
    assert duplicate_response.get_json()["error"]["code"] == "network_window_id_invalid"
    assert overlap_response.status_code == 400
    assert overlap_response.get_json()["error"]["code"] == "network_window_overlap"


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
