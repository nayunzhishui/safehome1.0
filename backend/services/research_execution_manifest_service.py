"""Server-owned source verification and execution proof for research jobs."""

from __future__ import annotations

import hashlib
import json
import os
import platform
from pathlib import Path

from flask import current_app

from database import json_dumps, new_id, now_iso, row_to_dict


ROOT = Path(__file__).resolve().parents[2]
POLICY_PATH = ROOT / "config" / "rc0810" / "research_execution_manifest_policy.json"
DEPENDENCY_PATH = ROOT / "backend" / "requirements.txt"


class ResearchManifestError(Exception):
    def __init__(self, code: str, message: str, status: int = 409, details: dict | None = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status = status
        self.details = details or {}


def canonical_hash(value: object) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _file_hash(path: Path) -> str:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError as exc:
        raise ResearchManifestError("source_unavailable", "服务端无法读取研究来源对象。", 503) from exc


def load_policy() -> dict:
    try:
        return json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ResearchManifestError("manifest_policy_unavailable", "研究执行证明策略不可用。", 503) from exc


def _relative_content_path(source_path: Path) -> tuple[Path, str]:
    root = Path(current_app.config["CONTENT_DIR"]).resolve()
    resolved = source_path.resolve()
    try:
        relative = resolved.relative_to(root)
    except ValueError as exc:
        raise ResearchManifestError("source_storage_scope_rejected", "研究来源对象不在受控内容目录内。", 409) from exc
    return resolved, relative.as_posix()


def register_server_source(
    conn,
    *,
    actor_id: str,
    source_id: str,
    source_type: str,
    source_path: Path,
    declared_hash: str,
    source_bytes: bytes | None = None,
) -> dict:
    policy = load_policy()
    if source_type not in set(policy["active_source_types"]):
        raise ResearchManifestError(
            "real_participant_analysis_blocked",
            "外部数据与伦理门禁未批准，当前只允许项目自有合成来源。",
            409,
        )
    resolved, storage_path = _relative_content_path(source_path)
    if source_bytes is None:
        try:
            source_bytes = resolved.read_bytes()
        except OSError as exc:
            raise ResearchManifestError("source_unavailable", "服务端无法读取研究来源对象。", 503) from exc
    server_hash = hashlib.sha256(source_bytes).hexdigest()
    if declared_hash.lower() != server_hash:
        raise ResearchManifestError(
            "source_hash_mismatch",
            "客户端或快照声明的来源指纹与服务端读取结果不一致。",
            409,
        )
    existing = conn.execute(
        "SELECT * FROM research_source_objects WHERE source_id = ? AND server_hash = ?",
        (source_id, server_hash),
    ).fetchone()
    if existing:
        item = row_to_dict(existing)
        if (
            item["status"] != "verified"
            or item["source_type"] != source_type
            or bytes(item["payload_blob"]) != source_bytes
        ):
            raise ResearchManifestError("source_registry_conflict", "研究来源登记状态冲突。", 409)
        return item
    source_object_id = new_id("research_source")
    source_policy = policy["source"]
    conn.execute(
        """INSERT INTO research_source_objects
           (id, source_id, source_type, storage_path, payload_blob, server_hash, size_bytes, data_mode,
            rights_status, owner_scope, retention_policy, status, created_by, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, 'project_owned_synthetic_only', ?, ?, ?, 'verified', ?, ?)""",
        (
            source_object_id,
            source_id,
            source_type,
            storage_path,
            source_bytes,
            server_hash,
            len(source_bytes),
            source_policy["rights_status"],
            source_policy["owner_scope"],
            source_policy["retention_policy"],
            actor_id,
            now_iso(),
        ),
    )
    return row_to_dict(
        conn.execute("SELECT * FROM research_source_objects WHERE id = ?", (source_object_id,)).fetchone()
    )


def _execution_facts() -> dict:
    environment = str(current_app.config.get("APP_ENV") or "development").lower()
    code_commit = os.environ.get("SAFEHOME_BUILD_COMMIT", "").strip()
    image_ref = os.environ.get("SAFEHOME_EXECUTION_IMAGE_REF", "").strip()
    if environment == "production" and (not code_commit or not image_ref):
        raise ResearchManifestError(
            "production_execution_identity_missing",
            "生产研究执行必须绑定构建提交与镜像引用。",
            503,
        )
    return {
        "code_commit": code_commit or "local-unversioned",
        "execution_environment": environment,
        "execution_image_ref": image_ref or "local-process",
        "runtime_version": platform.python_version(),
        "dependency_hash": _file_hash(DEPENDENCY_PATH),
    }


def prepare_execution_manifest(
    conn,
    *,
    actor_id: str,
    job: dict,
    snapshot_hash: str,
    source_id: str,
    source_type: str,
    source_path: Path,
    declared_hash: str,
    model_version: str,
    dictionary_hash: str,
    thresholds_hash: str,
    random_seed: int,
    source_bytes: bytes | None = None,
) -> dict:
    source = register_server_source(
        conn,
        actor_id=actor_id,
        source_id=source_id,
        source_type=source_type,
        source_path=source_path,
        declared_hash=declared_hash,
        source_bytes=source_bytes,
    )
    facts = _execution_facts()
    parameters = json.loads(job.get("parameters_json") or "{}")
    reproducibility_inputs = {
        **facts,
        "source_hash": source["server_hash"],
        "algorithm_version": job["analysis_version"],
        "model_version": model_version,
        "dictionary_hash": dictionary_hash,
        "thresholds_hash": thresholds_hash,
        "input_snapshot_hash": snapshot_hash,
        "random_seed": random_seed,
        "parameters": parameters,
    }
    previous_attempt = conn.execute(
        "SELECT MAX(attempt_number) AS value FROM research_execution_manifests WHERE job_id = ?",
        (job["id"],),
    ).fetchone()
    attempt_number = int(previous_attempt["value"] or 0) + 1
    manifest_id = new_id("research_manifest")
    conn.execute(
        """INSERT INTO research_execution_manifests
           (id, job_id, attempt_number, source_object_id, source_hash, code_commit,
            execution_environment, execution_image_ref, runtime_version, dependency_hash,
            algorithm_version, model_version, dictionary_hash, thresholds_hash,
            input_snapshot_hash, random_seed, parameters_json, reproducibility_key,
            status, created_by, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'prepared', ?, ?)""",
        (
            manifest_id,
            job["id"],
            attempt_number,
            source["id"],
            source["server_hash"],
            facts["code_commit"],
            facts["execution_environment"],
            facts["execution_image_ref"],
            facts["runtime_version"],
            facts["dependency_hash"],
            job["analysis_version"],
            model_version,
            dictionary_hash,
            thresholds_hash,
            snapshot_hash,
            random_seed,
            json_dumps(parameters),
            canonical_hash(reproducibility_inputs),
            actor_id,
            now_iso(),
        ),
    )
    return row_to_dict(
        conn.execute("SELECT * FROM research_execution_manifests WHERE id = ?", (manifest_id,)).fetchone()
    )


def _assert_complete_output(analysis_type: str, metrics: dict) -> None:
    if set(metrics) != {"coverage_rate", "unknown_rate", "sample_size", "quality_status", "result", "warnings"}:
        raise ResearchManifestError("partial_output_rejected", "执行结果缺少完整受控指标。", 409)
    result = metrics.get("result")
    if not isinstance(result, dict) or not isinstance(metrics.get("warnings"), list):
        raise ResearchManifestError("partial_output_rejected", "执行结果结构不完整。", 409)
    policy = load_policy()
    allowed = set(policy["allowed_outputs"].get(analysis_type, [])) | {
        "catalog_version",
        "fixture_id",
        "data_mode",
    }
    if not set(result).issubset(allowed):
        raise ResearchManifestError("result_contract_rejected", "执行结果包含未批准字段。", 409)
    mandatory = {
        "affect_aggregate": {"suppressed", "categories"},
        "semantic_network": {"suppressed", "nodes", "edges", "minimum_support"},
        "family_topology": {"suppressed", "nodes", "edges", "minimum_support"},
    }.get(analysis_type, set())
    if not mandatory.issubset(result) or not {"catalog_version", "fixture_id", "data_mode"}.issubset(result):
        raise ResearchManifestError("partial_output_rejected", "执行结果缺少算法合同字段。", 409)
    forbidden = set(policy["forbidden_output_fields"])
    if forbidden & set(result):
        raise ResearchManifestError("result_contract_rejected", "执行结果包含隐私或诊断字段。", 409)


def _manifest_hash_payload(item: dict) -> dict:
    keys = (
        "id",
        "job_id",
        "attempt_number",
        "source_object_id",
        "source_hash",
        "code_commit",
        "execution_environment",
        "execution_image_ref",
        "runtime_version",
        "dependency_hash",
        "algorithm_version",
        "model_version",
        "dictionary_hash",
        "thresholds_hash",
        "input_snapshot_hash",
        "random_seed",
        "parameters_json",
        "metrics_hash",
        "result_hash",
        "result_reference",
        "log_summary_json",
        "log_digest",
        "reproducibility_key",
        "reproducibility_status",
        "created_by",
        "created_at",
    )
    return {key: item[key] for key in keys}


def finalize_execution_manifest(conn, manifest_id: str, analysis_type: str, metrics: dict) -> dict:
    _assert_complete_output(analysis_type, metrics)
    row = conn.execute("SELECT * FROM research_execution_manifests WHERE id = ?", (manifest_id,)).fetchone()
    if not row:
        raise ResearchManifestError("manifest_not_found", "没有找到服务端执行证明。", 404)
    item = row_to_dict(row)
    if item["status"] != "prepared":
        raise ResearchManifestError("manifest_replay_rejected", "执行证明已结束，不能重复签发。", 409)
    metrics_hash = canonical_hash(metrics)
    result_hash = canonical_hash(metrics["result"])
    prior = conn.execute(
        """SELECT result_hash FROM research_execution_manifests
           WHERE reproducibility_key = ? AND status IN ('completed', 'consumed')
           ORDER BY created_at DESC LIMIT 1""",
        (item["reproducibility_key"],),
    ).fetchone()
    reproducibility_status = "baseline" if not prior else ("match" if prior["result_hash"] == result_hash else "mismatch")
    result_reference = f"research-manifest:{manifest_id}:result"
    log_summary = {
        "job_id": item["job_id"],
        "manifest_id": manifest_id,
        "status": "succeeded",
        "metrics_hash": metrics_hash,
        "partial_output": False,
    }
    log_summary_json = json_dumps(log_summary)
    log_digest = canonical_hash(log_summary)
    finalized = {
        **item,
        "metrics_hash": metrics_hash,
        "result_hash": result_hash,
        "result_reference": result_reference,
        "log_summary_json": log_summary_json,
        "log_digest": log_digest,
        "reproducibility_status": reproducibility_status,
    }
    manifest_hash = canonical_hash(_manifest_hash_payload(finalized))
    if reproducibility_status == "mismatch":
        conn.execute(
            """UPDATE research_execution_manifests
               SET metrics_hash = ?, result_hash = ?, result_reference = ?, log_summary_json = ?, log_digest = ?,
                   manifest_hash = ?, reproducibility_status = 'mismatch',
                   status = 'failed', failure_code = 'reproducibility_mismatch', completed_at = ?
               WHERE id = ? AND status = 'prepared'""",
            (metrics_hash, result_hash, result_reference, log_summary_json, log_digest, manifest_hash, now_iso(), manifest_id),
        )
        raise ResearchManifestError("reproducibility_mismatch", "相同执行输入产生了不同结果，任务已失败关闭。", 409)
    updated = conn.execute(
        """UPDATE research_execution_manifests
           SET metrics_hash = ?, result_hash = ?, result_reference = ?, log_summary_json = ?, log_digest = ?,
               manifest_hash = ?, reproducibility_status = ?, status = 'completed', completed_at = ?
           WHERE id = ? AND status = 'prepared'""",
        (metrics_hash, result_hash, result_reference, log_summary_json, log_digest, manifest_hash, reproducibility_status, now_iso(), manifest_id),
    )
    if updated.rowcount != 1:
        raise ResearchManifestError("manifest_replay_rejected", "执行证明已被并发处理。", 409)
    return row_to_dict(
        conn.execute("SELECT * FROM research_execution_manifests WHERE id = ?", (manifest_id,)).fetchone()
    )


def validate_completion_manifest(conn, *, job: dict, manifest_id: str, metrics: dict) -> dict:
    row = conn.execute("SELECT * FROM research_execution_manifests WHERE id = ?", (manifest_id,)).fetchone()
    if not row:
        raise ResearchManifestError("completion_proof_missing", "任务完成缺少服务端执行证明。", 409)
    item = row_to_dict(row)
    if item["status"] != "completed":
        code = "manifest_replay_rejected" if item["status"] == "consumed" else "completion_proof_invalid"
        raise ResearchManifestError(code, "服务端执行证明状态无效或已被使用。", 409)
    if item["job_id"] != job["id"] or item["algorithm_version"] != job["analysis_version"]:
        raise ResearchManifestError("completion_proof_invalid", "执行证明与任务或算法版本不匹配。", 409)
    if item["source_hash"] != job["resource_hash"] or item["metrics_hash"] != canonical_hash(metrics):
        raise ResearchManifestError("completion_proof_invalid", "执行证明与来源或结果不匹配。", 409)
    if item["manifest_hash"] != canonical_hash(_manifest_hash_payload(item)):
        raise ResearchManifestError("completion_proof_invalid", "执行证明完整性校验失败。", 409)
    return item


def consume_completion_manifest(conn, manifest_id: str, artifact_id: str) -> None:
    updated = conn.execute(
        """UPDATE research_execution_manifests
           SET status = 'consumed', consumed_at = ?
           WHERE id = ? AND status = 'completed'""",
        (now_iso(), manifest_id),
    )
    if updated.rowcount != 1:
        raise ResearchManifestError("manifest_replay_rejected", "执行证明已被其他完成请求使用。", 409)


def fail_execution_manifest(conn, manifest_id: str, error_code: str) -> None:
    conn.execute(
        """UPDATE research_execution_manifests
           SET status = 'failed', failure_code = ?, completed_at = ?
           WHERE id = ? AND status IN ('prepared', 'completed')""",
        (error_code[:64], now_iso(), manifest_id),
    )
