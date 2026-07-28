"""Generate the deterministic synthetic group-network fixture for T37-A04."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT = ROOT / "content" / "synthetic_group_network_suite.json"


def _node_id(index: int) -> str:
    digest = hashlib.sha256(f"safehome-synthetic-network-node:{index}".encode()).hexdigest()
    return f"n_{digest[:12]}"


def _edge(left: int, right: int, weight: float) -> dict:
    return {"source": _node_id(left), "target": _node_id(right), "weight": weight}


def _window_edges(extra: bool) -> list[dict]:
    edges: list[dict] = []
    for start in (0, 6, 12):
        for offset in range(6):
            edges.append(_edge(start + offset, start + ((offset + 1) % 6), 1.0))
        edges.append(_edge(start, start + 3, 0.8))
    edges.extend([_edge(2, 8, 0.2), _edge(9, 15, 0.2)])
    if extra:
        edges.extend(
            [
                _edge(1, 4, 0.7),
                _edge(7, 10, 0.7),
                _edge(13, 16, 0.7),
                _edge(4, 10, 0.25),
                _edge(11, 17, 0.25),
            ]
        )
    return edges


def payload() -> dict:
    nodes = [
        {
            "id": _node_id(index),
            "approved_cohort": True,
            "observed": index < 16,
            "active": index < 14,
        }
        for index in range(18)
    ]
    windows = [
        {
            "id": "window_1",
            "start_date": "2026-06-01",
            "end_date": "2026-06-14",
            "edges": _window_edges(False),
        },
        {
            "id": "window_2",
            "start_date": "2026-06-15",
            "end_date": "2026-06-28",
            "edges": _window_edges(True),
        },
    ]
    canonical = {"nodes": nodes, "windows": windows}
    fixture_hash = hashlib.sha256(
        json.dumps(
            canonical, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
    ).hexdigest()
    return {
        "schema": "safehome.synthetic-group-network.v1",
        "version": "2026-07-28-t37-a04-v1",
        "contains_real_data": False,
        "data_class": "synthetic",
        "output_mode": "group_aggregate",
        "research_question_id": "group_interaction_structure_over_time",
        "expected_missing_edge_rate": 0.05,
        "nodes": nodes,
        "windows": windows,
        "fixture_hash": fixture_hash,
        "boundary_notice": "固定生成的无真人图，只用于群体级描述算法与隐私阈值工程验收。",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    rendered = json.dumps(payload(), ensure_ascii=False, indent=2) + "\n"
    if args.check:
        if not args.output.exists() or args.output.read_text(encoding="utf-8") != rendered:
            raise SystemExit("synthetic group-network fixture drift detected")
        print("synthetic group-network fixture check passed")
        return 0
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(rendered, encoding="utf-8")
    print(f"generated {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
