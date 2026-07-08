"""Build aggregate social-network-style co-occurrence summary."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import networkx as nx

from analyze_text_sources import PROJECT_ROOT, analyze_records, get_connection, init_db, _iter_text_records


def _top_pairs(edges: list[dict], left_prefix: str, right_prefix: str) -> list[dict]:
    pairs = []
    for edge in edges:
        source = edge["source"]
        target = edge["target"]
        if source.startswith(left_prefix) and target.startswith(right_prefix):
            pairs.append(edge)
        elif source.startswith(right_prefix) and target.startswith(left_prefix):
            pairs.append({"source": target, "target": source, "weight": edge["weight"]})
    return pairs[:20]


def _network_metrics(nodes: list[dict], edges: list[dict]) -> tuple[list[dict], list[dict]]:
    graph = nx.Graph()
    for node in nodes:
        graph.add_node(node["id"], **node)
    for edge in edges:
        graph.add_edge(edge["source"], edge["target"], weight=edge.get("weight", 1))
    if not graph:
        return nodes, []
    degree = nx.degree_centrality(graph)
    betweenness = nx.betweenness_centrality(graph, weight="weight", normalized=True)
    try:
        eigenvector = nx.eigenvector_centrality_numpy(graph, weight="weight")
    except Exception:
        eigenvector = {node_id: 0 for node_id in graph.nodes}
    communities = list(nx.algorithms.community.greedy_modularity_communities(graph, weight="weight"))
    community_index = {}
    for index, community in enumerate(communities):
        for node_id in community:
            community_index[node_id] = index
    enriched = []
    for node in nodes:
        node_id = node["id"]
        enriched.append(
            {
                **node,
                "degree_centrality": round(degree.get(node_id, 0), 4),
                "betweenness_centrality": round(betweenness.get(node_id, 0), 4),
                "eigenvector_centrality": round(float(eigenvector.get(node_id, 0)), 4),
                "community_id": community_index.get(node_id, -1),
            }
        )
    enriched.sort(key=lambda item: (item["degree_centrality"], item["betweenness_centrality"], item["count"]), reverse=True)
    community_summary = [
        {"community_id": index, "size": len(community), "top_nodes": sorted(list(community))[:8]}
        for index, community in enumerate(communities)
    ]
    return enriched, community_summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Build SafeHome aggregate co-occurrence network.")
    parser.add_argument("--user-id", default="")
    parser.add_argument("--days", type=int, default=0)
    parser.add_argument("--output", default=str(PROJECT_ROOT / "outputs" / "text_analysis" / "social_network_summary.json"))
    args = parser.parse_args()

    init_db()
    with get_connection() as conn:
        records = list(_iter_text_records(conn, args.user_id or None, args.days or None))
    aggregate = analyze_records(records)
    nodes = aggregate["cooccurrence_network"]["nodes"]
    edges = aggregate["cooccurrence_network"]["edges"]
    enriched_nodes, communities = _network_metrics(nodes, edges)
    max_weight = max((edge.get("weight", 0) for edge in edges), default=0) or 1
    normalized_edges = [
        {**edge, "normalized_weight": round(edge.get("weight", 0) / max_weight, 4)}
        for edge in edges
    ]
    result = {
        "analysis_version": "social_network_v2_networkx_reflex_arc",
        "record_count": aggregate["record_count"],
        "nodes": enriched_nodes,
        "edges": normalized_edges,
        "top_nodes": enriched_nodes[:20],
        "top_edges": normalized_edges[:20],
        "communities": communities,
        "scene_emotion_pairs": _top_pairs(normalized_edges, "scene:", "emotion:"),
        "person_emotion_pairs": _top_pairs(normalized_edges, "person:", "emotion:"),
        "behavior_emotion_pairs": _top_pairs(normalized_edges, "behavior:", "emotion:"),
        "reflex_arc_edges": aggregate["cooccurrence_network"].get("reflex_arc_edges", []),
        "reflex_arc_chains": aggregate["cooccurrence_network"].get("reflex_arc_chains", []),
        "raw_text_included": False,
        "boundary_notice": aggregate["boundary_notice"],
        "filters": {"user_id": args.user_id or None, "days": args.days or None},
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"output": str(output), "record_count": result["record_count"], "raw_text_included": False}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
