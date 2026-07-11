"""Build a privacy-preserving family-link topology data-quality audit."""

from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import os
import sqlite3
import sys
from collections import Counter, defaultdict, deque
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from analyze_text_sources import BOUNDARY_NOTICE, DEFAULT_DB, PROJECT_ROOT, open_readonly_sqlite  # noqa: E402


def collect_edges(database_path: Path) -> list[dict]:
    with open_readonly_sqlite(database_path) as conn:
        columns = {row["name"] for row in conn.execute("PRAGMA table_info(family_links)").fetchall()}
        if not {"parent_user_id", "student_user_id"} <= columns:
            return []
        rows = conn.execute(
            """
            SELECT parent_user_id, student_user_id, relation_label, status,
                   created_at, confirmed_at, revoked_at
            FROM family_links
            WHERE parent_user_id IS NOT NULL AND student_user_id IS NOT NULL
            """
        ).fetchall()
        return [dict(row) for row in rows]


def _pseudonym(value: str, secret: bytes) -> str:
    return hmac.new(secret, str(value).encode("utf-8"), hashlib.sha256).hexdigest()


def _components(graph: dict[str, set[str]]) -> list[int]:
    seen: set[str] = set()
    sizes: list[int] = []
    for node in sorted(graph):
        if node in seen:
            continue
        queue = deque([node])
        seen.add(node)
        size = 0
        while queue:
            current = queue.popleft()
            size += 1
            for neighbor in graph[current]:
                if neighbor not in seen:
                    seen.add(neighbor)
                    queue.append(neighbor)
        sizes.append(size)
    return sorted(sizes, reverse=True)


def build_topology_summary(edges: list[dict], *, secret: bytes, minimum_group_size: int = 5) -> dict:
    if not secret:
        raise ValueError("家庭拓扑审计必须提供运行级 HMAC 密钥")
    filters = Counter()
    relation_counts = Counter()
    graph: dict[str, set[str]] = defaultdict(set)
    admitted: set[tuple[str, str]] = set()

    for edge in edges:
        # 当前 family route 使用 active；confirmed 仅兼容早期快照语义。
        if edge.get("status") not in {"active", "confirmed"}:
            filters["not_confirmed"] += 1
            continue
        if edge.get("revoked_at"):
            filters["revoked"] += 1
            continue
        parent_raw = str(edge.get("parent_user_id") or "")
        student_raw = str(edge.get("student_user_id") or "")
        if not parent_raw or not student_raw:
            filters["missing_identity"] += 1
            continue
        parent = _pseudonym(parent_raw, secret)
        student = _pseudonym(student_raw, secret)
        if parent == student:
            filters["self_loop"] += 1
            continue
        pair = tuple(sorted((parent, student)))
        if pair in admitted:
            filters["duplicate"] += 1
            continue
        admitted.add(pair)
        graph[parent].add(student)
        graph[student].add(parent)
        relation_counts[edge.get("relation_label") or "unspecified"] += 1

    component_sizes = _components(graph)
    edge_count = len(admitted)
    node_count = len(graph)
    mostly_dyads = bool(component_sizes) and sum(size == 2 for size in component_sizes) / len(component_sizes) >= 0.8
    if not edges:
        quality_status = "empty"
        reasons = ["no_relationship_records"]
    elif edge_count == 0:
        quality_status = "insufficient_data"
        reasons = ["no_admitted_edges"]
    elif node_count < minimum_group_size or mostly_dyads:
        quality_status = "insufficient_data"
        reasons = ["small_topology"] + (["mostly_two_node_components"] if mostly_dyads else [])
    else:
        quality_status = "valid"
        reasons = []

    component_distribution = Counter(component_sizes)
    degree_distribution = Counter(len(neighbors) for neighbors in graph.values())
    allow_detail = node_count >= minimum_group_size
    return {
        "schema_version": "2026-07-11-family-topology-audit-v1",
        "analysis_kind": "family_topology_audit",
        "analysis_version": "family_topology_hmac_aggregate_v1",
        "input_edge_count": len(edges),
        "node_count": node_count,
        "edge_count": edge_count,
        "filter_counts": dict(filters),
        "relation_counts": dict(relation_counts) if allow_detail else {},
        "component_size_distribution": {str(size): count for size, count in sorted(component_distribution.items())} if allow_detail else {},
        "degree_distribution": {str(degree): count for degree, count in sorted(degree_distribution.items())} if allow_detail else {},
        "quality_status": quality_status,
        "available": quality_status == "valid",
        "insufficient_data_reasons": reasons,
        "privacy_gate_passed": True,
        "minimum_group_size": minimum_group_size,
        "raw_text_included": False,
        "stable_pseudonyms_exported": False,
        "boundary_notice": BOUNDARY_NOTICE + " 家庭拓扑仅审计绑定覆盖和结构数据质量，不评价任何家庭成员。",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build aggregate family topology audit.")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--minimum-group-size", type=int, default=5)
    parser.add_argument("--output", type=Path, default=PROJECT_ROOT / "outputs" / "text_analysis" / "family_topology_audit_summary.json")
    args = parser.parse_args()
    secret_text = os.environ.get("SAFEHOME_ANALYSIS_HMAC_KEY", "")
    if not secret_text:
        raise SystemExit("请通过 SAFEHOME_ANALYSIS_HMAC_KEY 提供运行级 HMAC 密钥；密钥不会写入产物。")
    result = build_topology_summary(collect_edges(args.db), secret=secret_text.encode("utf-8"), minimum_group_size=max(2, args.minimum_group_size))
    result["generated_at"] = datetime.now(timezone.utc).isoformat()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(args.output), "edge_count": result["edge_count"], "quality_status": result["quality_status"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
