"""Privacy-preserving, group-only social network description."""

from __future__ import annotations

import hashlib
import json
import re
from collections import Counter, deque
from datetime import date
from statistics import median


class NetworkAnalysisError(ValueError):
    def __init__(self, code: str, message: str, status: int = 400):
        super().__init__(message)
        self.code = code
        self.status = status
        self.details: dict = {}


SENSITIVE_FIELDS = {
    "raw_text",
    "message",
    "content",
    "nickname",
    "name",
    "phone",
    "email",
    "openid",
    "unionid",
    "user_id",
    "participant_id",
    "relationship_label",
}


def public_policy(policy: dict) -> dict:
    return {
        "version": policy["version"],
        "status": policy["status"],
        "research_questions": policy["research_questions"],
        "node_definition": policy["node_definition"],
        "edge_definition": policy["edge_definition"],
        "window_definition": policy["window_definition"],
        "missingness_definition": policy["missingness_definition"],
        "boundary_variants": policy["boundary_variants"],
        "minimum_privacy_thresholds": policy["minimum_privacy_thresholds"],
        "participant_visible": policy["participant_visible"],
        "individual_metrics_allowed": policy["individual_metrics_allowed"],
        "training_model": policy["training_model"],
        "causal_inference_allowed": policy["causal_inference_allowed"],
        "family_quality_inference_allowed": policy[
            "family_quality_inference_allowed"
        ],
        "production_group_data_allowed": policy["production_group_data_allowed"],
        "real_data_gate": policy["real_data_gate"],
        "boundary_notice": policy["boundary_notice"],
    }


def _find_sensitive_field(value) -> str | None:
    if isinstance(value, dict):
        for key, nested in value.items():
            if str(key).lower() in SENSITIVE_FIELDS:
                return str(key)
            found = _find_sensitive_field(nested)
            if found:
                return found
    elif isinstance(value, list):
        for nested in value:
            found = _find_sensitive_field(nested)
            if found:
                return found
    return None


def validate_group_network(payload: dict, policy: dict) -> dict:
    if not isinstance(payload, dict):
        raise NetworkAnalysisError("network_payload_invalid", "网络分析输入必须为对象")
    sensitive = _find_sensitive_field(payload)
    if sensitive:
        raise NetworkAnalysisError(
            "network_sensitive_field_forbidden",
            f"群体网络分析不得接收身份或正文内容字段：{sensitive}",
        )
    if payload.get("output_mode") != "group_aggregate":
        raise NetworkAnalysisError(
            "network_individual_output_forbidden",
            "网络分析只允许群体聚合输出",
        )
    if payload.get("data_class") != "synthetic" or payload.get(
        "contains_real_data"
    ) is not False:
        raise NetworkAnalysisError(
            "network_real_data_gate_closed",
            "真实群体网络数据门禁尚未批准，当前只允许合成数据",
            409,
        )
    question_ids = {
        item["id"] for item in policy.get("research_questions", [])
    }
    if payload.get("research_question_id") not in question_ids:
        raise NetworkAnalysisError(
            "network_research_question_invalid", "研究问题未在政策中登记"
        )
    nodes = payload.get("nodes")
    windows = payload.get("windows")
    if not isinstance(nodes, list) or not isinstance(windows, list):
        raise NetworkAnalysisError(
            "network_shape_invalid", "网络分析需要节点数组和窗口数组"
        )
    limits = policy["input_limits"]
    if not nodes or len(nodes) > int(limits["maximum_nodes"]):
        raise NetworkAnalysisError(
            "network_node_count_invalid", "节点数为空或超过工程上限"
        )
    pattern = re.compile(limits["node_id_pattern"])
    node_ids: set[str] = set()
    for node in nodes:
        if not isinstance(node, dict) or set(node) != {
            "id",
            "approved_cohort",
            "observed",
            "active",
        }:
            raise NetworkAnalysisError(
                "network_node_shape_invalid", "节点只允许去标识ID和三类边界状态"
            )
        node_id = str(node.get("id") or "")
        if not pattern.fullmatch(node_id) or node_id in node_ids:
            raise NetworkAnalysisError(
                "network_node_id_invalid", "节点ID必须是唯一的分析专用代号"
            )
        node_ids.add(node_id)
    maximum_windows = int(policy["window_definition"]["maximum_windows_per_run"])
    if not 1 <= len(windows) <= maximum_windows:
        raise NetworkAnalysisError(
            "network_window_count_invalid", "观察窗口数量无效"
        )
    for window in windows:
        if not isinstance(window, dict) or set(window) != {
            "id",
            "start_date",
            "end_date",
            "edges",
        }:
            raise NetworkAnalysisError(
                "network_window_shape_invalid", "观察窗口字段不符合契约"
            )
        try:
            start = date.fromisoformat(str(window["start_date"]))
            end = date.fromisoformat(str(window["end_date"]))
        except (TypeError, ValueError) as exc:
            raise NetworkAnalysisError(
                "network_window_date_invalid", "观察窗口日期无效"
            ) from exc
        days = (end - start).days + 1
        if not (
            int(policy["window_definition"]["minimum_days"])
            <= days
            <= int(policy["window_definition"]["maximum_days"])
        ):
            raise NetworkAnalysisError(
                "network_window_duration_invalid", "观察窗口长度超出政策范围"
            )
        edges = window["edges"]
        if not isinstance(edges, list) or len(edges) > int(
            limits["maximum_edges_per_window"]
        ):
            raise NetworkAnalysisError(
                "network_edge_count_invalid", "边数量格式无效或超过工程上限"
            )
        seen_edges: set[tuple[str, str]] = set()
        for edge in edges:
            if not isinstance(edge, dict) or set(edge) != {
                "source",
                "target",
                "weight",
            }:
                raise NetworkAnalysisError(
                    "network_edge_shape_invalid", "边只允许来源、目标和权重"
                )
            source, target = str(edge["source"]), str(edge["target"])
            pair = tuple(sorted((source, target)))
            if (
                source not in node_ids
                or target not in node_ids
                or source == target
                or pair in seen_edges
            ):
                raise NetworkAnalysisError(
                    "network_edge_invalid", "边端点不存在、重复或形成自环"
                )
            seen_edges.add(pair)
            try:
                weight = float(edge["weight"])
            except (TypeError, ValueError) as exc:
                raise NetworkAnalysisError(
                    "network_edge_weight_invalid", "边权重必须为正数"
                ) from exc
            if not 0 < weight <= 1000:
                raise NetworkAnalysisError(
                    "network_edge_weight_invalid", "边权重必须为正数"
                )
    try:
        missing_rate = float(payload.get("expected_missing_edge_rate", 0))
    except (TypeError, ValueError) as exc:
        raise NetworkAnalysisError(
            "network_missingness_invalid", "预期缺失率必须为0至1数值"
        ) from exc
    if not 0 <= missing_rate <= 1:
        raise NetworkAnalysisError(
            "network_missingness_invalid", "预期缺失率必须为0至1数值"
        )
    return payload


def _distribution(values: list[float]) -> dict:
    ordered = sorted(values)
    return {
        "count": len(ordered),
        "minimum": round(ordered[0], 4) if ordered else None,
        "median": round(float(median(ordered)), 4) if ordered else None,
        "mean": round(sum(ordered) / len(ordered), 4) if ordered else None,
        "maximum": round(ordered[-1], 4) if ordered else None,
    }


def _component_sizes(
    node_ids: set[str], edges: list[dict], threshold: float
) -> list[int]:
    graph = {node_id: set() for node_id in node_ids}
    for edge in edges:
        if float(edge["weight"]) >= threshold:
            graph[edge["source"]].add(edge["target"])
            graph[edge["target"]].add(edge["source"])
    seen: set[str] = set()
    sizes: list[int] = []
    for start in sorted(node_ids):
        if start in seen:
            continue
        queue = deque([start])
        seen.add(start)
        size = 0
        while queue:
            current = queue.popleft()
            size += 1
            for neighbor in graph[current] - seen:
                seen.add(neighbor)
                queue.append(neighbor)
        sizes.append(size)
    return sorted(sizes)


def _aggregate(
    node_ids: set[str], edges: list[dict], policy: dict
) -> dict:
    filtered = [
        edge
        for edge in edges
        if edge["source"] in node_ids and edge["target"] in node_ids
    ]
    node_count = len(node_ids)
    edge_count = len(filtered)
    possible_edges = node_count * (node_count - 1) / 2
    strength = Counter({node_id: 0.0 for node_id in node_ids})
    for edge in filtered:
        weight = float(edge["weight"])
        strength[edge["source"]] += weight
        strength[edge["target"]] += weight
    sizes = _component_sizes(
        node_ids,
        filtered,
        float(policy["community_edge_weight_threshold"]),
    )
    minimum_community = int(
        policy["minimum_privacy_thresholds"]["community_size"]
    )
    visible_sizes = [size for size in sizes if size >= minimum_community]
    return {
        "node_count": node_count,
        "edge_count": edge_count,
        "density": round(edge_count / possible_edges, 4)
        if possible_edges
        else 0.0,
        "weighted_strength_distribution": _distribution(list(strength.values())),
        "component_count": len(sizes),
        "community_size_distribution": _distribution(
            [float(size) for size in visible_sizes]
        ),
        "suppressed_small_community_count": len(sizes) - len(visible_sizes),
    }


def _boundary_nodes(nodes: list[dict], variant: str) -> set[str]:
    return {
        node["id"]
        for node in nodes
        if bool(node.get(variant))
    }


def _missing_edges(edges: list[dict], rate: float, window_id: str) -> list[dict]:
    if rate <= 0:
        return list(edges)
    kept = []
    for edge in edges:
        value = (
            f"{window_id}:{min(edge['source'], edge['target'])}:"
            f"{max(edge['source'], edge['target'])}"
        )
        bucket = int(hashlib.sha256(value.encode()).hexdigest()[:8], 16) / 0xFFFFFFFF
        if bucket >= rate:
            kept.append(edge)
    return kept


def analyze_group_network(payload: dict, policy: dict) -> dict:
    data = validate_group_network(payload, policy)
    nodes = data["nodes"]
    windows = data["windows"]
    thresholds = policy["minimum_privacy_thresholds"]
    approved_nodes = _boundary_nodes(nodes, "approved_cohort")
    latest_edges = windows[-1]["edges"]
    missing_rate = float(data.get("expected_missing_edge_rate", 0))
    suppressed = (
        len(approved_nodes) < int(thresholds["nodes"])
        or len(latest_edges) < int(thresholds["edges_per_window"])
        or missing_rate > float(thresholds["maximum_missing_edge_rate"])
    )
    if suppressed:
        return {
            "suppressed": True,
            "suppression_reason": "minimum_privacy_threshold_not_met",
            "aggregate_metrics": None,
            "boundary_sensitivity": [],
            "missingness_sensitivity": [],
            "temporal_change": {"window_count": len(windows), "density_series": []},
            "individual_metrics_included": False,
            "node_identifiers_included": False,
            "training_model": False,
            "causal_inference": False,
            "family_quality_inference": False,
            "participant_visible": False,
            "boundary_notice": policy["boundary_notice"],
        }

    boundary_sensitivity = []
    for variant in policy["boundary_variants"]:
        metrics = _aggregate(_boundary_nodes(nodes, variant), latest_edges, policy)
        boundary_sensitivity.append({"boundary": variant, "metrics": metrics})
    missingness_sensitivity = []
    for rate in policy["missingness_sensitivity_rates"]:
        edges = _missing_edges(latest_edges, float(rate), windows[-1]["id"])
        metrics = _aggregate(approved_nodes, edges, policy)
        missingness_sensitivity.append(
            {"removed_edge_rate": float(rate), "metrics": metrics}
        )
    density_series = [
        {
            "window_index": index + 1,
            "density": _aggregate(approved_nodes, window["edges"], policy)["density"],
        }
        for index, window in enumerate(windows)
    ]
    temporal_change = {
        "window_count": len(windows),
        "density_series": density_series,
        "density_change_first_to_last": round(
            density_series[-1]["density"] - density_series[0]["density"], 4
        ),
        "causal_interpretation_allowed": False,
    }
    report = {
        "suppressed": False,
        "suppression_reason": None,
        "aggregate_metrics": _aggregate(approved_nodes, latest_edges, policy),
        "boundary_sensitivity": boundary_sensitivity,
        "missingness_sensitivity": missingness_sensitivity,
        "temporal_change": temporal_change,
        "individual_metrics_included": False,
        "node_identifiers_included": False,
        "training_model": False,
        "causal_inference": False,
        "family_quality_inference": False,
        "participant_visible": False,
        "input_summary": {
            "node_count": len(nodes),
            "window_count": len(windows),
            "expected_missing_edge_rate": missing_rate,
            "data_class": "synthetic",
        },
        "boundary_notice": policy["boundary_notice"],
    }
    report["analysis_digest"] = hashlib.sha256(
        json.dumps(
            report, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
    ).hexdigest()
    return report
