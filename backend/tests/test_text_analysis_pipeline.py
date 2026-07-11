import importlib.util
import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
TEXT_ANALYSIS_DIR = PROJECT_ROOT / "analysis" / "text_analysis"


def _module(filename: str, name: str):
    spec = importlib.util.spec_from_file_location(name, TEXT_ANALYSIS_DIR / filename)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


def _record(text: str, source_type: str = "user_text", network_ok: bool = True) -> dict:
    return {
        "source": "synthetic.text",
        "source_type": source_type,
        "text": text,
        "sentiment_ok": True,
        "network_ok": network_ok,
    }


def test_affect_rules_handle_negation_degree_repetition_and_contrast():
    analysis = _module("analyze_text_sources.py", "text_analysis_affect")

    negated = analysis.analyze_records([_record("我不生气")])
    slight = analysis.analyze_records([_record("我有点生气")])
    intense = analysis.analyze_records([_record("我非常生气")])
    repeated = analysis.analyze_records([_record("我生气生气")])
    contrast = analysis.analyze_records([_record("虽然着急，但后来平静了")])

    assert negated["sentiment_summary"]["negated_match_count"] == 1
    assert negated["sentiment_summary"]["intensity_signal_score"] == 0
    assert intense["sentiment_summary"]["intensity_signal_score"] > slight["sentiment_summary"]["intensity_signal_score"]
    assert repeated["sentiment_summary"]["matched_emotion_count"] == 2
    assert contrast["sentiment_summary"]["valence"] > 0


def test_affect_aggregates_keep_writer_sources_separate():
    analysis = _module("analyze_text_sources.py", "text_analysis_sources")

    result = analysis.analyze_records(
        [
            _record("我很生气", "user_text", False),
            _record("你已经做得很好", "system_text", False),
        ]
    )

    assert set(result["sentiment_by_source_type"]) == {"user_text", "system_text"}
    assert result["sentiment_by_source_type"]["user_text"]["record_count"] == 1
    assert result["sentiment_by_source_type"]["system_text"]["record_count"] == 1


def test_semantic_network_uses_inverse_weight_as_shortest_path_distance():
    network = _module("build_social_network.py", "semantic_network_metrics")
    nodes = [{"id": item, "type": "term", "label": item, "count": 2, "document_frequency": 2} for item in "ABCD"]
    edges = [
        {"source": "A", "target": "B", "weight": 10},
        {"source": "B", "target": "C", "weight": 10},
        {"source": "A", "target": "D", "weight": 1},
        {"source": "D", "target": "C", "weight": 1},
    ]

    enriched, _communities, metadata = network._network_metrics(nodes, edges)
    by_id = {node["id"]: node for node in enriched}

    assert metadata["betweenness_distance"] == "1/(weight+epsilon)"
    assert by_id["B"]["betweenness_centrality"] > by_id["D"]["betweenness_centrality"]


def test_family_topology_only_keeps_active_unrevoked_edges_and_never_exports_node_ids():
    topology = _module("build_family_topology_audit.py", "family_topology_audit")
    edges = [
        {"parent_user_id": "parent-real", "student_user_id": "student-real", "status": "active", "revoked_at": None, "relation_label": "parent"},
        {"parent_user_id": "parent-revoked", "student_user_id": "student-revoked", "status": "confirmed", "revoked_at": "2026-07-11", "relation_label": "parent"},
        {"parent_user_id": "parent-pending", "student_user_id": "student-pending", "status": "pending", "revoked_at": None, "relation_label": "parent"},
    ]

    result = topology.build_topology_summary(edges, secret=b"test-secret", minimum_group_size=2)
    serialized = json.dumps(result, ensure_ascii=False)

    assert result["edge_count"] == 1
    assert result["filter_counts"]["revoked"] == 1
    assert result["filter_counts"]["not_confirmed"] == 1
    assert "parent-real" not in serialized
    assert "student-real" not in serialized
    assert "nodes" not in result
    assert "edges" not in result


def test_empty_offline_output_is_not_reported_as_available(tmp_path, monkeypatch):
    service = importlib.import_module("services.text_analysis_service")
    path = tmp_path / "empty.json"
    path.write_text(json.dumps({"record_count": 0, "raw_text_included": False}), encoding="utf-8")
    monkeypatch.setattr(service, "OUTPUT_DIR", tmp_path)

    result = service._read_output(path.name)

    assert result["available"] is False
    assert result["quality_status"] == "empty"


def test_invalid_offline_output_is_blocked_instead_of_raising(tmp_path, monkeypatch):
    service = importlib.import_module("services.text_analysis_service")
    path = tmp_path / "invalid.json"
    path.write_text("{not-json", encoding="utf-8")
    monkeypatch.setattr(service, "OUTPUT_DIR", tmp_path)

    result = service._read_output(path.name)

    assert result["available"] is False
    assert result["quality_status"] == "validation_failed"
    assert result["reason"] == "offline_output_invalid"
