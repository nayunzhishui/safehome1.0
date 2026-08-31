"""Immutable model registration and synthetic-only shadow execution."""

from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from pathlib import Path

from flask import current_app

from config import PROJECT_ROOT
from database import (
    CURRENT_SCHEMA_VERSION,
    get_connection,
    json_dumps,
    json_loads,
    new_id,
    now_iso,
    row_to_dict,
    rows_to_dicts,
    write_audit_log,
)
from services.affect_model_benchmark_service import (
    compare_affect_candidates,
    synthetic_case_partition,
    triage_text,
)


COMMIT_PATTERN = re.compile(r"^[0-9a-f]{40}$")
SYNTHETIC_CASE_PATTERN = re.compile(r"^syn-affect-\d{3}$")


class AffectShadowError(ValueError):
    def __init__(
        self,
        code: str,
        message: str,
        status: int = 400,
        details: dict | None = None,
    ):
        super().__init__(message)
        self.code = code
        self.status = status
        self.details = details or {}


def _read_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise AffectShadowError(
            "shadow_asset_invalid", f"影子执行制品不可用：{path.name}", 503
        ) from exc


def _content_json(filename: str) -> dict:
    return _read_json(Path(current_app.config["CONTENT_DIR"]) / filename)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _asset_snapshot(code_commit: str) -> dict:
    if not COMMIT_PATTERN.fullmatch(str(code_commit or "").lower()):
        raise AffectShadowError(
            "code_commit_required", "模型注册必须提供40位Git commit哈希"
        )
    content_dir = Path(current_app.config["CONTENT_DIR"])
    registry_path = content_dir / "affect_model_candidate_registry.json"
    dataset_path = content_dir / "synthetic_affect_benchmark_240.json"
    lexicon_path = (
        PROJECT_ROOT / "analysis" / "text_analysis" / "dictionaries" / "emotion_terms.json"
    )
    registry = _read_json(registry_path)
    dataset = _read_json(dataset_path)
    lexicon_hash = _sha256(lexicon_path)
    threshold_hash = hashlib.sha256(
        json_dumps(registry["abstention_policy"]).encode("utf-8")
    ).hexdigest()
    snapshot = {
        "registry_version": registry["version"],
        "registry_hash": _sha256(registry_path),
        "lexicon_hash": lexicon_hash,
        "threshold_hash": threshold_hash,
        "feature_version": registry["feature_contract"]["version"],
        "code_commit": code_commit.lower(),
        "dataset_id": registry["dataset_id"],
        "dataset_hash": str(dataset["case_hash"]),
        "schema_version": CURRENT_SCHEMA_VERSION,
    }
    snapshot["asset_manifest_hash"] = hashlib.sha256(
        json_dumps(snapshot).encode("utf-8")
    ).hexdigest()
    return snapshot


def _decode_version(row) -> dict:
    item = row_to_dict(row)
    item["limitations"] = json_loads(item.pop("limitations_json"), [])
    return item


def _decode_run(row) -> dict:
    item = row_to_dict(row)
    result = json_loads(item.pop("result_json"), {})
    item.update(result)
    return item


def register_model_version(actor: dict, code_commit: str) -> dict:
    policy = _content_json("affect_shadow_execution_policy.json")
    registry = _content_json("affect_model_candidate_registry.json")
    snapshot = _asset_snapshot(code_commit)
    candidate = next(
        (
            item
            for item in registry["candidates"]
            if item["id"] == policy["active_candidate_id"]
        ),
        None,
    )
    if not candidate or candidate.get("execution_status") != "runnable_synthetic_engineering_only":
        raise AffectShadowError(
            "active_candidate_unavailable", "当前影子候选模型未通过工程准入", 409
        )
    timestamp = now_iso()
    model_id = new_id("omv")
    with get_connection() as conn:
        existing = conn.execute(
            "SELECT * FROM offline_model_versions "
            "WHERE candidate_id = ? AND model_version = ? AND asset_manifest_hash = ?",
            (candidate["id"], candidate["version"], snapshot["asset_manifest_hash"]),
        ).fetchone()
        if existing:
            return _decode_version(existing)
        conn.execute(
            "INSERT INTO offline_model_versions "
            "(id, candidate_id, model_version, registry_version, lexicon_hash, "
            "threshold_hash, feature_version, code_commit, dataset_id, dataset_hash, "
            "schema_version, asset_manifest_hash, limitations_json, status, created_by, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'registered_shadow_only', ?, ?)",
            (
                model_id,
                candidate["id"],
                candidate["version"],
                snapshot["registry_version"],
                snapshot["lexicon_hash"],
                snapshot["threshold_hash"],
                snapshot["feature_version"],
                snapshot["code_commit"],
                snapshot["dataset_id"],
                snapshot["dataset_hash"],
                snapshot["schema_version"],
                snapshot["asset_manifest_hash"],
                json_dumps(registry["model_card"]["known_limitations"]),
                actor["id"],
                timestamp,
            ),
        )
        write_audit_log(
            conn,
            "offline_model_version_registered",
            actor["id"],
            "offline_model_version",
            model_id,
            {
                "candidate_id": candidate["id"],
                "asset_manifest_hash": snapshot["asset_manifest_hash"],
                "raw_text_included": False,
                "participant_effect_allowed": False,
            },
        )
        conn.commit()
        row = conn.execute(
            "SELECT * FROM offline_model_versions WHERE id = ?", (model_id,)
        ).fetchone()
    return _decode_version(row)


def list_model_versions() -> dict:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM offline_model_versions ORDER BY created_at DESC LIMIT 50"
        ).fetchall()
    return {
        "items": [_decode_version(row) for row in rows],
        "boundary_notice": _content_json("affect_shadow_execution_policy.json")[
            "boundary_notice"
        ],
    }


def _assert_assets_unchanged(model: dict) -> dict:
    snapshot = _asset_snapshot(model["code_commit"])
    comparisons = {
        "registry_version": model["registry_version"],
        "lexicon_hash": model["lexicon_hash"],
        "threshold_hash": model["threshold_hash"],
        "feature_version": model["feature_version"],
        "code_commit": model["code_commit"],
        "dataset_id": model["dataset_id"],
        "dataset_hash": model["dataset_hash"],
        "schema_version": model["schema_version"],
        "asset_manifest_hash": model["asset_manifest_hash"],
    }
    drift = [
        key for key, expected in comparisons.items() if snapshot.get(key) != expected
    ]
    if drift:
        raise AffectShadowError(
            "shadow_asset_drift",
            "模型、内容、数据或数据库契约发生漂移，影子执行已停止",
            409,
            {"drift_fields": drift},
        )
    return snapshot


def _dictionary_terms() -> dict[str, list[str]]:
    payload = _read_json(
        PROJECT_ROOT / "analysis" / "text_analysis" / "dictionaries" / "emotion_terms.json"
    )
    terms: dict[str, list[str]] = {}
    for item in payload["terms"]:
        terms.setdefault(str(item["category"]), []).append(str(item["word"]))
    return terms


def run_shadow(actor: dict, model_version_id: str, parent_run_id: str | None = None) -> dict:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM offline_model_versions WHERE id = ?", (model_version_id,)
        ).fetchone()
        if parent_run_id:
            parent = conn.execute(
                "SELECT id, model_version_id FROM offline_model_shadow_runs "
                "WHERE id = ? AND (? IN ('admin', 'supervisor') OR created_by = ?)",
                (parent_run_id, actor["role"], actor["id"]),
            ).fetchone()
            if not parent:
                raise AffectShadowError(
                    "shadow_run_not_found", "待回放运行不存在", 404
                )
            if parent["model_version_id"] != model_version_id:
                raise AffectShadowError(
                    "shadow_replay_model_mismatch",
                    "回放必须使用父运行登记的模型版本",
                    409,
                )
    if not row:
        raise AffectShadowError("model_version_not_found", "模型版本不存在", 404)
    model = _decode_version(row)
    _assert_assets_unchanged(model)
    policy = _content_json("affect_shadow_execution_policy.json")
    dataset = _content_json("synthetic_affect_benchmark_240.json")
    if dataset.get("contains_real_data") is not False:
        raise AffectShadowError("real_data_forbidden", "影子执行只允许项目自有合成数据", 403)
    registry = _content_json("affect_model_candidate_registry.json")
    terms = _dictionary_terms()
    metrics = compare_affect_candidates(dataset["cases"], terms, registry)
    test_cases = [
        case
        for case in dataset["cases"]
        if synthetic_case_partition(case)[1] == "test"
    ]
    queue = []
    queued_ids: set[str] = set()
    for case in test_cases:
        triage = triage_text(case["text"], terms, registry)
        if triage["needs_human_review"]:
            queue.append({"case_id": case["id"], "reason": triage["reason"]})
            queued_ids.add(case["id"])
    selected = next(
        item
        for item in metrics["candidates"]
        if item["candidate_id"] == model["candidate_id"]
    )
    expected_unknown = int(selected["metrics"]["unknown_count"])
    for case in test_cases:
        if len(queue) >= expected_unknown:
            break
        if case["id"] not in queued_ids:
            queue.append({"case_id": case["id"], "reason": "low_model_confidence"})
            queued_ids.add(case["id"])
    sample_count = int(selected["metrics"]["sample_count"])
    known_count = max(0, sample_count - expected_unknown)
    unknown_rate = round(expected_unknown / sample_count, 4) if sample_count else 0.0
    reported_coverage_rate = float(selected["metrics"]["coverage_rate"])
    computed_coverage_rate = round(known_count / sample_count, 4) if sample_count else 0.0
    coverage_rate_gap = round(reported_coverage_rate - computed_coverage_rate, 4)
    coverage_rate_consistent = abs(coverage_rate_gap) <= 0.0001
    review_reason_counts = dict(sorted(Counter(item["reason"] for item in queue).items()))
    result = {
        "sample_count": sample_count,
        "known_count": known_count,
        "coverage_rate": reported_coverage_rate,
        "computed_coverage_rate": computed_coverage_rate,
        "coverage_rate_gap": coverage_rate_gap,
        "coverage_rate_consistent": coverage_rate_consistent,
        "unknown_count": expected_unknown,
        "unknown_rate": unknown_rate,
        "review_queue_count": len(queue),
        "review_queue_rate": round(len(queue) / sample_count, 4) if sample_count else 0.0,
        "review_reason_counts": review_reason_counts,
        "limitations": model["limitations"],
        "model_version": model["model_version"],
        "summary_text": (
            f"合成测试 {sample_count} 条：可覆盖 {known_count} 条，"
            f"未知 {expected_unknown} 条，人工复核队列 {len(queue)} 条。"
        ),
        "next_check_text": (
            "覆盖率与未知数分母不一致，先停止版本比较并核对评测产物。"
            if not coverage_rate_consistent
            else "先按原因分布复核未知案例，再比较模型版本；不得据此影响参与者反馈。"
            if queue
            else "继续用固定合成集回放并核对版本漂移。"
        ),
        "boundary_notice": policy["boundary_notice"],
    }
    timestamp = now_iso()
    run_id = new_id("osr")
    artifact_hash = hashlib.sha256(
        json_dumps(
            {
                "model_version_id": model_version_id,
                "input_snapshot_hash": dataset["case_hash"],
                "result": result,
                "parent_run_id": parent_run_id,
            }
        ).encode("utf-8")
    ).hexdigest()
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO offline_model_shadow_runs "
            "(id, model_version_id, parent_run_id, input_snapshot_hash, result_json, "
            "artifact_hash, status, raw_text_included, participant_effect_allowed, created_by, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, 'completed_shadow_only', 0, 0, ?, ?)",
            (
                run_id,
                model_version_id,
                parent_run_id,
                dataset["case_hash"],
                json_dumps(result),
                artifact_hash,
                actor["id"],
                timestamp,
            ),
        )
        for item in queue:
            if not SYNTHETIC_CASE_PATTERN.fullmatch(item["case_id"]):
                raise AffectShadowError(
                    "review_case_identifier_invalid",
                    "人工复核队列只允许合成案例代号",
                )
            conn.execute(
                "INSERT INTO offline_model_review_queue "
                "(id, shadow_run_id, case_id, reason, status, raw_text_included, created_at) "
                "VALUES (?, ?, ?, ?, 'pending', 0, ?)",
                (new_id("omq"), run_id, item["case_id"], item["reason"], timestamp),
            )
        write_audit_log(
            conn,
            "offline_model_shadow_run_created",
            actor["id"],
            "offline_model_shadow_run",
            run_id,
            {
                "model_version_id": model_version_id,
                "parent_run_id": parent_run_id,
                "input_snapshot_hash": dataset["case_hash"],
                "raw_text_included": False,
                "participant_effect_allowed": False,
            },
        )
        conn.commit()
        saved = conn.execute(
            "SELECT * FROM offline_model_shadow_runs WHERE id = ?", (run_id,)
        ).fetchone()
    return _decode_run(saved)


def list_shadow_runs(actor: dict) -> dict:
    scope = "" if actor["role"] in {"admin", "supervisor"} else " WHERE created_by = ?"
    params = () if not scope else (actor["id"],)
    with get_connection() as conn:
        rows = conn.execute(
            f"SELECT * FROM offline_model_shadow_runs{scope} "
            "ORDER BY created_at DESC LIMIT 100",
            params,
        ).fetchall()
    return {"items": [_decode_run(row) for row in rows]}


def list_review_queue(actor: dict) -> dict:
    with get_connection() as conn:
        rows = rows_to_dicts(
            conn.execute(
                "SELECT q.id, q.shadow_run_id, q.case_id, q.reason, q.status, "
                "q.raw_text_included, q.created_at "
                "FROM offline_model_review_queue q "
                "JOIN offline_model_shadow_runs r ON r.id = q.shadow_run_id "
                "WHERE (? IN ('admin', 'supervisor') OR r.created_by = ?) "
                "ORDER BY q.created_at DESC LIMIT 200",
                (actor["role"], actor["id"]),
            ).fetchall()
        )
    return {
        "items": rows,
        "raw_text_included": False,
        "participant_identifiers_included": False,
    }
