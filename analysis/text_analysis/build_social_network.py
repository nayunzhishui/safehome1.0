"""Build the offline semantic co-occurrence network (legacy filename)."""

from __future__ import annotations

import argparse
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

import networkx as nx

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from analyze_text_sources import (  # noqa: E402
    BOUNDARY_NOTICE,
    DEFAULT_DB,
    PROJECT_ROOT,
    _iter_text_records,
    analyze_records,
    open_readonly_sqlite,
)


def _top_pairs(edges: list[dict], left_prefix: str, right_prefix: str) -> list[dict]:
    pairs = []
    for edge in edges:
        source, target = edge["source"], edge["target"]
        if source.startswith(left_prefix) and target.startswith(right_prefix):
            pairs.append(edge)
        elif source.startswith(right_prefix) and target.startswith(left_prefix):
            pairs.append({**edge, "source": target, "target": source})
    return pairs[:20]


def _network_metrics(nodes: list[dict], edges: list[dict]) -> tuple[list[dict], list[dict], dict]:
    graph = nx.Graph()
    for node in nodes:
        graph.add_node(node["id"], **node)
    for edge in edges:
        weight = max(float(edge.get("weight", 1)), 0.0)
        graph.add_edge(edge["source"], edge["target"], weight=weight, distance=1.0 / (weight + 1e-9))

    metadata = {
        "betweenness_distance": "1/(weight+epsilon)",
        "weighted_degree_metric": "strength",
        "metrics_status": "insufficient_data" if graph.number_of_nodes() < 3 or graph.number_of_edges() < 2 else "valid",
    }
    if not graph:
        return nodes, [], metadata

    strength = dict(graph.degree(weight="weight"))
    if metadata["metrics_status"] == "valid":
        betweenness = nx.betweenness_centrality(graph, weight="distance", normalized=True)
        degree = nx.degree_centrality(graph)
    else:
        betweenness = {node_id: 0.0 for node_id in graph}
        degree = {node_id: 0.0 for node_id in graph}

    eigenvector = {node_id: 0.0 for node_id in graph}
    if metadata["metrics_status"] == "valid" and nx.is_connected(graph):
        try:
            eigenvector = nx.eigenvector_centrality(graph, weight="weight", max_iter=1000)
        except (nx.PowerIterationFailedConvergence, nx.NetworkXException):
            metadata["eigenvector_status"] = "not_converged"
        else:
            metadata["eigenvector_status"] = "valid"
    else:
        metadata["eigenvector_status"] = "not_reported"

    communities: list[frozenset] = []
    if metadata["metrics_status"] == "valid":
        communities = list(nx.algorithms.community.greedy_modularity_communities(graph, weight="weight"))
    community_index = {node_id: index for index, community in enumerate(communities) for node_id in community}
    enriched = [
        {
            **node,
            "strength": round(float(strength.get(node["id"], 0)), 4),
            "degree_centrality": round(float(degree.get(node["id"], 0)), 4),
            "betweenness_centrality": round(float(betweenness.get(node["id"], 0)), 4),
            "eigenvector_centrality": round(float(eigenvector.get(node["id"], 0)), 4),
            "community_id": community_index.get(node["id"], -1),
        }
        for node in nodes
    ]
    enriched.sort(key=lambda item: (item["strength"], item["betweenness_centrality"], item.get("count", 0)), reverse=True)
    community_summary = [
        {"community_id": index, "size": len(community), "top_nodes": sorted(community)[:8]}
        for index, community in enumerate(communities)
    ]
    return enriched, community_summary, metadata


def build_semantic_network_summary(records: list[dict], minimum_support: int = 5) -> dict:
    aggregate = analyze_records(records, minimum_support=minimum_support)
    nodes = aggregate["cooccurrence_network"]["nodes"]
    edges = aggregate["cooccurrence_network"]["edges"]
    enriched_nodes, communities, metrics = _network_metrics(nodes, edges)
    max_weight = max((float(edge.get("weight", 0)) for edge in edges), default=0) or 1
    normalized_edges = [{**edge, "normalized_weight": round(float(edge.get("weight", 0)) / max_weight, 4)} for edge in edges]
    return {
        "schema_version": "2026-07-11-semantic-network-v1",
        "analysis_kind": "semantic_cooccurrence_network",
        "analysis_version": "semantic_network_v3_sentence_inverse_distance",
        "record_count": aggregate["record_count"],
        "nodes": enriched_nodes,
        "edges": normalized_edges,
        "top_nodes": enriched_nodes[:20] if metrics["metrics_status"] == "valid" else [],
        "top_edges": normalized_edges[:20],
        "communities": communities if metrics["metrics_status"] == "valid" else [],
        "metrics": metrics,
        "scene_emotion_pairs": _top_pairs(normalized_edges, "scene:", "emotion:"),
        "person_emotion_pairs": _top_pairs(normalized_edges, "person:", "emotion:"),
        "behavior_emotion_pairs": _top_pairs(normalized_edges, "behavior:", "emotion:"),
        "reflex_arc_edges": aggregate["cooccurrence_network"].get("reflex_arc_edges", []),
        "reflex_arc_chains": aggregate["cooccurrence_network"].get("reflex_arc_chains", []),
        "suppression": aggregate["cooccurrence_network"]["suppression"],
        "quality_status": aggregate["quality_status"],
        "available": aggregate["available"] and metrics["metrics_status"] == "valid",
        "privacy_gate_passed": True,
        "raw_text_included": False,
        "boundary_notice": BOUNDARY_NOTICE + " 该网络是文本概念共现，不是真实社会关系网络。",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build SafeHome aggregate semantic co-occurrence network.")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--user-id", default="")
    parser.add_argument("--days", type=int, default=0)
    parser.add_argument("--minimum-support", type=int, default=5)
    parser.add_argument("--output", type=Path, default=PROJECT_ROOT / "outputs" / "text_analysis" / "semantic_network_summary.json")
    args = parser.parse_args()

    with open_readonly_sqlite(args.db) as conn:
        records = list(_iter_text_records(conn, args.user_id or None, args.days or None))
    result = build_semantic_network_summary(records, max(1, args.minimum_support))
    result["filters"] = {"user_scope_applied": bool(args.user_id), "days": args.days or None, "minimum_support": max(1, args.minimum_support)}
    result["generated_at"] = datetime.now(timezone.utc).isoformat()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(args.output), "record_count": result["record_count"], "quality_status": result["quality_status"], "raw_text_included": False}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
