"""Synthetic-only online research analysis for T36-F14.

Real participant text remains blocked until the T35 data, ethics and model
rights gates have human approval.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter

from flask import current_app

from database import get_connection, json_loads, write_audit_log
from services.research_access_service import assert_capability
from services.research_analysis_service import (
    BOUNDARY_NOTICE,
    ResearchAnalysisError,
    claim_job,
    complete_job,
)


CATALOG_VERSION = "2026-07-25-t36-f14-v1"
FIXTURE_ID = "safehome_synthetic_affect_240_v1"
ALGORITHM_VERSIONS = {
    "affect_aggregate": "affect-rules-synthetic-v1",
    "semantic_network": "semantic-network-synthetic-v1",
    "family_topology": "family-topology-synthetic-v1",
}
ANALYSIS_LABELS = {
    "affect_aggregate": "聚合情感线索",
    "semantic_network": "语义共现网络",
    "family_topology": "家庭结构数据质量",
}
MINIMUM_SAMPLE = 5
MAX_GRAPH_NODES = 40
MAX_GRAPH_EDGES = 80


def _fixture_path():
    return current_app.config["CONTENT_DIR"] / "synthetic_affect_benchmark_240.json"


def _fixture_bytes() -> bytes:
    try:
        return _fixture_path().read_bytes()
    except OSError as exc:
        raise ResearchAnalysisError(
            "synthetic_fixture_unavailable",
            "合成分析基准暂时不可用。",
            503,
        ) from exc


def _fixture_hash() -> str:
    return hashlib.sha256(_fixture_bytes()).hexdigest()


def _fixture_cases() -> list[dict]:
    try:
        payload = json.loads(_fixture_bytes().decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ResearchAnalysisError(
            "synthetic_fixture_invalid",
            "合成分析基准格式无效。",
            503,
        ) from exc
    if payload.get("contains_real_data") is not False or not isinstance(payload.get("cases"), list):
        raise ResearchAnalysisError(
            "synthetic_fixture_rights_gate_failed",
            "只允许明确标记为不含真实数据的项目自有合成基准。",
            409,
        )
    return payload["cases"]


def get_catalog(actor: dict) -> dict:
    assert_capability(actor, "research.analysis.read")
    resource_hash = _fixture_hash()
    pipelines = [
        {
            "analysis_type": analysis_type,
            "label": ANALYSIS_LABELS[analysis_type],
            "analysis_version": version,
            "resource_hash": resource_hash,
            "data_mode": "project_owned_synthetic_only",
            "real_participant_processing_enabled": False,
            "minimum_sample": MINIMUM_SAMPLE,
            "maximum_graph_nodes": MAX_GRAPH_NODES if analysis_type != "affect_aggregate" else 0,
            "maximum_graph_edges": MAX_GRAPH_EDGES if analysis_type != "affect_aggregate" else 0,
            "status": "engineering_shadow_ready",
        }
        for analysis_type, version in ALGORITHM_VERSIONS.items()
    ]
    return {
        "catalog_version": CATALOG_VERSION,
        "fixture_id": FIXTURE_ID,
        "pipelines": pipelines,
        "external_datasets_downloaded": False,
        "production_training_enabled": False,
        "real_participant_processing_enabled": False,
        "human_rights_review_status": "pending",
        "boundary_notice": BOUNDARY_NOTICE,
    }


def _quality(sample_size: int, unknown_count: int, minimum_count: int) -> tuple[str, float, float, list[str]]:
    unknown_rate = round(unknown_count / sample_size, 4) if sample_size else 1.0
    coverage_rate = round(1 - unknown_rate, 4)
    warnings: list[str] = []
    if sample_size < minimum_count:
        warnings.append("small_sample_suppressed")
        return "insufficient", coverage_rate, unknown_rate, warnings
    if unknown_rate > 0.4:
        warnings.append("high_unknown_rate")
        return "limited", coverage_rate, unknown_rate, warnings
    return "sufficient", coverage_rate, unknown_rate, warnings


def _affect_result(cases: list[dict], suppressed: bool) -> dict:
    if suppressed:
        return {"suppressed": True, "categories": []}
    counts = Counter(str(item.get("generator_label") or "unmapped") for item in cases)
    return {
        "suppressed": False,
        "categories": [
            {"key": key, "count": count}
            for key, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))
        ],
        "category_definition": "项目自有合成句子的生成类别计数，不用于推断个人。",
    }


def _semantic_result(cases: list[dict], minimum_count: int, suppressed: bool) -> dict:
    if suppressed:
        return {"suppressed": True, "nodes": [], "edges": [], "minimum_support": minimum_count}
    labels = [str(item.get("generator_label") or "unmapped") for item in cases]
    counts = Counter(labels)
    nodes = [
        {"id": key, "display_name": key, "support": count}
        for key, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))
        if count >= minimum_count
    ][:MAX_GRAPH_NODES]
    allowed = {item["id"] for item in nodes}
    edge_counts: Counter[tuple[str, str]] = Counter()
    for index in range(len(labels) - 1):
        left, right = sorted((labels[index], labels[index + 1]))
        if left != right and left in allowed and right in allowed:
            edge_counts[(left, right)] += 1
    edges = [
        {"source": left, "target": right, "support": support}
        for (left, right), support in sorted(edge_counts.items(), key=lambda item: (-item[1], item[0]))
        if support >= minimum_count
    ][:MAX_GRAPH_EDGES]
    return {
        "suppressed": False,
        "nodes": nodes,
        "edges": edges,
        "node_definition": "合成情绪类别",
        "edge_definition": "相邻合成案例类别共现，仅用于图算法验收",
        "minimum_support": minimum_count,
        "node_limit": MAX_GRAPH_NODES,
        "edge_limit": MAX_GRAPH_EDGES,
    }


def _topology_result(sample_size: int, minimum_count: int, suppressed: bool) -> dict:
    if suppressed:
        return {"suppressed": True, "nodes": [], "edges": [], "minimum_support": minimum_count}
    nodes = [
        {"id": "caregiver", "display_name": "照顾者（合成）", "recorded_count": sample_size},
        {"id": "child", "display_name": "孩子（合成）", "recorded_count": sample_size},
        {"id": "supporter", "display_name": "支持者（合成）", "recorded_count": sample_size // 2},
    ]
    edges = [
        {
            "source": "caregiver",
            "target": "child",
            "event_count": sample_size,
            "definition": "明确记录的合成交互事件",
        },
        {
            "source": "caregiver",
            "target": "supporter",
            "event_count": sample_size // 2,
            "definition": "明确记录的合成支持事件",
        },
    ]
    return {
        "suppressed": False,
        "nodes": nodes,
        "edges": [edge for edge in edges if edge["event_count"] >= minimum_count],
        "minimum_support": minimum_count,
        "inference_disabled": True,
        "quality_judgement_disabled": True,
    }


def execute_synthetic_job(actor: dict, job_id: str) -> dict:
    """Claim and complete one job against the governed project-owned fixture."""

    assert_capability(actor, "research.analysis.operate")
    if not current_app.config.get("RESEARCH_ANALYSIS_JOB_EXECUTION_ENABLED", False):
        raise ResearchAnalysisError("analysis_execution_disabled", "当前环境未开启在线分析执行器。", 503)
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM research_analysis_jobs WHERE id = ?", (job_id,)).fetchone()
        if not row:
            raise ResearchAnalysisError("not_found", "没有找到在线分析任务。", 404)
        item = dict(row)
        links = [
            dict(link)
            for link in conn.execute(
                "SELECT source_type, source_id, source_hash FROM research_analysis_snapshot_links WHERE snapshot_id = ?",
                (item["snapshot_id"],),
            ).fetchall()
        ]
    expected_version = ALGORITHM_VERSIONS.get(str(item["analysis_type"]))
    expected_hash = _fixture_hash()
    if (
        not links
        or any(link["source_type"] != "synthetic_fixture" or link["source_id"] != FIXTURE_ID for link in links)
        or any(link["source_hash"] != expected_hash for link in links)
    ):
        raise ResearchAnalysisError(
            "real_participant_analysis_blocked",
            "T35门禁未批准，在线执行器当前只接受项目自有合成基准。",
            409,
        )
    if item["analysis_version"] != expected_version or item["resource_hash"] != expected_hash:
        raise ResearchAnalysisError(
            "analysis_version_mismatch",
            "任务版本或资源指纹与受控目录不一致。",
            409,
        )

    params = json_loads(item.get("parameters_json"), {})
    minimum_count = max(MINIMUM_SAMPLE, min(int(params.get("minimum_count") or MINIMUM_SAMPLE), 50))
    requested = max(0, min(int(params.get("synthetic_sample_size") or 240), 240))
    cases = _fixture_cases()[:requested]
    unknown_count = sum(1 for case in cases if str(case.get("generator_label") or "unmapped") == "unmapped")
    quality, coverage, unknown_rate, warnings = _quality(len(cases), unknown_count, minimum_count)
    suppressed = quality == "insufficient"
    if item["analysis_type"] == "affect_aggregate":
        result = _affect_result(cases, suppressed)
    elif item["analysis_type"] == "semantic_network":
        result = _semantic_result(cases, minimum_count, suppressed)
    else:
        result = _topology_result(len(cases), minimum_count, suppressed)

    claim_job(actor, job_id, {"lease_seconds": 300})
    completed = complete_job(
        actor,
        job_id,
        {
            "metrics": {
                "coverage_rate": coverage,
                "unknown_rate": unknown_rate,
                "sample_size": len(cases),
                "quality_status": quality,
                "result": {
                    **result,
                    "catalog_version": CATALOG_VERSION,
                    "fixture_id": FIXTURE_ID,
                    "data_mode": "project_owned_synthetic_only",
                },
                "warnings": warnings,
            }
        },
    )
    with get_connection() as conn:
        write_audit_log(
            conn,
            "research_analysis_synthetic_executed",
            actor["id"],
            "research_analysis_job",
            job_id,
            {
                "analysis_type": item["analysis_type"],
                "analysis_version": item["analysis_version"],
                "sample_size": len(cases),
                "small_sample_suppressed": suppressed,
                "real_participant_data_used": False,
            },
        )
        conn.commit()
    return completed
