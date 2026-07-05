"""Offline social-network prototype for SafeHome family-link data.

Outputs hashed nodes and aggregate graph metrics only.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
from collections import Counter, defaultdict, deque
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB = PROJECT_ROOT / "backend" / "safehome.sqlite3"
DEFAULT_OUTPUT_DIR = Path(r"D:\codex\workspace\safehome1.0其他内容\画像系统设计_Claude_20260628\07_情感计算与SNA雏形_20260701")


def hash_id(value: str) -> str:
    return hashlib.sha256(str(value).encode("utf-8")).hexdigest()[:12]


def table_exists(conn: sqlite3.Connection, table: str) -> bool:
    row = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,)).fetchone()
    return bool(row)


def collect_edges(db_path: Path) -> list[dict]:
    if not db_path.exists():
        return []
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    if not table_exists(conn, "family_links"):
        conn.close()
        return []
    rows = conn.execute(
        """
        SELECT parent_user_id, student_user_id, relation_label, status, created_at, confirmed_at, revoked_at
        FROM family_links
        WHERE parent_user_id IS NOT NULL AND student_user_id IS NOT NULL
        """
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def connected_components(graph: dict[str, set[str]]) -> list[list[str]]:
    seen = set()
    components = []
    for node in graph:
        if node in seen:
            continue
        queue = deque([node])
        seen.add(node)
        component = []
        while queue:
            current = queue.popleft()
            component.append(current)
            for neighbor in graph[current]:
                if neighbor not in seen:
                    seen.add(neighbor)
                    queue.append(neighbor)
        components.append(sorted(component))
    return components


def build_summary(edges: list[dict]) -> dict:
    graph: dict[str, set[str]] = defaultdict(set)
    status_counts = Counter()
    relation_counts = Counter()
    edge_rows = []
    for edge in edges:
        parent = hash_id(edge.get("parent_user_id"))
        student = hash_id(edge.get("student_user_id"))
        graph[parent].add(student)
        graph[student].add(parent)
        status_counts[edge.get("status") or "unknown"] += 1
        relation_counts[edge.get("relation_label") or "unknown"] += 1
        edge_rows.append(
            {
                "source": parent,
                "target": student,
                "status": edge.get("status"),
                "relation_label": edge.get("relation_label"),
            }
        )

    degree = [{"node": node, "degree": len(neighbors)} for node, neighbors in sorted(graph.items())]
    components = connected_components(graph)
    return {
        "schema_version": "2026-07-01-sna-prototype-v1",
        "privacy_note": "节点已哈希化，仅输出关系结构摘要，不包含真实身份、联系方式或原始文本。",
        "node_count": len(graph),
        "edge_count": len(edge_rows),
        "status_counts": dict(status_counts),
        "relation_counts": dict(relation_counts),
        "degree": degree,
        "components": [{"size": len(component), "nodes": component} for component in components],
        "edges": edge_rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    payload = build_summary(collect_edges(args.db))
    output_path = args.output_dir / "社会网络脱敏摘要.json"
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
