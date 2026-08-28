"""Task 34 cross-cutting operations governance deep module.

The interface keeps package creation, replay, approval, runtime switching,
monitoring and incident containment behind one audited seam. Governance records
never accept participant text and never infer a participant or family outcome.
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import time
from collections import Counter
from contextlib import contextmanager
from pathlib import Path

from flask import current_app

from database import get_connection, json_dumps, json_loads, new_id, now_iso, row_to_dict, write_audit_log
from services.ai_qa_service import _evaluate_case
from services.artifact_integrity_service import artifact_bytes
from services.feedback_service import generate_feedback
from services.risk_service import check_text_risk
from services.operations_reliability_service import (
    OperationsReliabilityError,
    sanitize_incident_record,
)


ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATH = ROOT / "content" / "operations_capability_registry.json"
CARDS_PATH = ROOT / "content" / "operations_asset_cards.json"
RELEASE_MANIFEST_PATH = ROOT / "content" / "operations_release_manifest.json"
CONTENT_REPLAY_PATH = ROOT / "content" / "synthetic_content_replay_cases.json"
AI_REPLAY_PATH = ROOT / "content" / "ai_qa_synthetic_safety_suite.json"

RISK_LEVELS = {"low", "medium", "high"}
TARGET_ENVIRONMENTS = {"local_synthetic", "production_candidate"}
INCIDENT_TYPES = {
    "unauthorized_access", "data_leak", "severe_adverse_event", "ai_safety_failure",
    "psychological_content_misdelivery", "cross_object_disclosure", "deletion_failure",
    "high_risk_feedback_error", "external_message_misdelivery",
}
INCIDENT_SEVERITIES = {"high", "critical"}
APPROVAL_DOMAINS = {
    "low": ("psychology",),
    "medium": ("psychology", "security"),
    "high": ("research", "psychology", "security"),
}
DOMAIN_ROLES = {"research": {"researcher"}, "psychology": {"supervisor"}, "security": {"admin"}}
THRESHOLDS = {
    "coverage_rate_min": 0.80,
    "unknown_label_rate_max": 0.20,
    "recommendation_concentration_max": 0.70,
    "non_conformity_rate_max": 0.25,
    "discomfort_rate_max": 0.10,
    "manual_escalation_rate_max": 0.30,
    "provider_error_rate_max": 0.05,
}


class OperationsGovernanceError(ValueError):
    def __init__(self, code: str, message: str, status: int = 400, details: dict | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.status = status
        self.details = details or {}


def _canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _hash(value: object) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _read_json(path: Path, error_code: str) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise OperationsGovernanceError(error_code, "运营治理制品暂时不可用。", 503) from exc


def get_registry() -> dict:
    return _read_json(REGISTRY_PATH, "operations_registry_unavailable")


def get_asset_cards() -> dict:
    return _read_json(CARDS_PATH, "operations_cards_unavailable")


def _release_source_manifest() -> dict:
    return _read_json(RELEASE_MANIFEST_PATH, "operations_release_manifest_unavailable")


def _bool_fields(item: dict) -> dict:
    for key in (
        "production_release_approved", "contains_real_data", "review_required",
        "automatic_participant_or_family_judgment", "contains_participant_text",
        "capability_disabled", "notification_required", "human_approved",
        "ethics_approved", "cloud_approved", "device_approved",
    ):
        if key in item:
            item[key] = bool(item[key])
    return item


def _decode_row(row, *, expose_bundle: bool = False) -> dict:
    item = row_to_dict(row)
    if not item:
        return item
    for key in list(item):
        if key.endswith("_json"):
            default = [] if key in {"capability_ids_json", "results_json", "drift_signals_json", "evidence_refs_json"} else {}
            item[key.removesuffix("_json")] = json_loads(item.pop(key), default)
    _bool_fields(item)
    if "manifest" in item and isinstance(item["manifest"], dict) and not expose_bundle:
        manifest = dict(item["manifest"])
        manifest["artifacts"] = [
            {key: value for key, value in artifact.items() if key != "bundle_b64"}
            for artifact in manifest.get("artifacts", [])
        ]
        item["manifest"] = manifest
    return item


def _package(conn, package_id: str):
    row = conn.execute("SELECT * FROM operations_release_packages WHERE id = ?", (package_id,)).fetchone()
    if not row:
        raise OperationsGovernanceError("not_found", "发布包不存在。", 404)
    return row


def package_detail(package_id: str, *, expose_bundle: bool = False) -> dict:
    with get_connection() as conn:
        row = _package(conn, package_id)
        item = _decode_row(row, expose_bundle=expose_bundle)
        item["reviews"] = [_decode_row(value) for value in conn.execute("SELECT * FROM operations_package_reviews WHERE package_id = ? AND stage = 'review' ORDER BY created_at", (package_id,)).fetchall()]
        item["approvals"] = [_decode_row(value) for value in conn.execute("SELECT * FROM operations_package_reviews WHERE package_id = ? AND stage = 'approval' ORDER BY created_at", (package_id,)).fetchall()]
        item["replay_runs"] = [_decode_row(value) for value in conn.execute("SELECT * FROM operations_replay_runs WHERE package_id = ? ORDER BY created_at DESC", (package_id,)).fetchall()]
    return item


def _artifact_target(relative_path: str) -> Path:
    normalized = str(relative_path).replace("\\", "/")
    if not normalized.startswith("content/") or ".." in Path(normalized).parts:
        raise OperationsGovernanceError("artifact_path_forbidden", "发布包只允许登记content目录内的受控制品。", 409)
    target = Path(current_app.config["CONTENT_DIR"]) / normalized.removeprefix("content/")
    try:
        target.resolve().relative_to(Path(current_app.config["CONTENT_DIR"]).resolve())
    except ValueError as exc:
        raise OperationsGovernanceError("artifact_path_forbidden", "制品路径超出受控内容目录。", 409) from exc
    return target


def _snapshot_manifest() -> dict:
    source = _release_source_manifest()
    artifacts = []
    for descriptor in source.get("artifacts", []):
        target = _artifact_target(descriptor.get("path", ""))
        if not target.is_file():
            raise OperationsGovernanceError("artifact_missing", f"制品不存在：{descriptor.get('path')}", 409)
        raw = artifact_bytes(target)
        digest = hashlib.sha256(raw).hexdigest()
        if digest != descriptor.get("sha256"):
            raise OperationsGovernanceError("artifact_integrity_failed", f"制品哈希不匹配：{descriptor.get('path')}", 409)
        artifacts.append({**descriptor, "bundle_b64": base64.b64encode(raw).decode("ascii")})
    manifest = {
        "schema_version": source.get("schema_version"),
        "source_manifest_version": source.get("version"),
        "source_manifest_hash": source.get("manifest_hash"),
        "artifacts": artifacts,
        "fixed_replay_suites": source.get("fixed_replay_suites", []),
        "revision_policy": source.get("revision_policy"),
        "atomic_runtime_switch": True,
        "contains_participant_data": False,
    }
    manifest["bundle_hash"] = _hash(manifest)
    return manifest


def _verify_bundle(manifest: dict) -> None:
    expected = manifest.get("bundle_hash")
    payload = dict(manifest)
    payload.pop("bundle_hash", None)
    actual = _hash(payload)
    if expected != actual:
        raise OperationsGovernanceError("package_integrity_failed", "发布包清单哈希不一致。", 409)
    required_types = {"content", "rule", "model", "dictionary", "prompt", "knowledge_index"}
    present = set()
    for artifact in manifest.get("artifacts", []):
        present.add(artifact.get("artifact_type"))
        try:
            raw = base64.b64decode(artifact.get("bundle_b64", ""), validate=True)
        except ValueError as exc:
            raise OperationsGovernanceError("package_integrity_failed", "发布包制品编码无效。", 409) from exc
        if hashlib.sha256(raw).hexdigest() != artifact.get("sha256") or len(raw) != int(artifact.get("size_bytes") or -1):
            raise OperationsGovernanceError("package_integrity_failed", f"发布包制品损坏：{artifact.get('path')}", 409)
    if not required_types <= present:
        raise OperationsGovernanceError("package_artifact_coverage_incomplete", "发布包未覆盖全部必要制品类别。", 409, {"missing": sorted(required_types - present)})


def create_package(actor: dict, payload: dict) -> dict:
    allowed = {"package_version", "previous_package_id", "risk_level", "target_environment"}
    unknown = set(payload) - allowed
    if unknown:
        raise OperationsGovernanceError("validation_error", "发布包请求包含未允许字段。", details={"unknown_fields": sorted(unknown)})
    package_version = str(payload.get("package_version") or "").strip()
    risk_level = str(payload.get("risk_level") or "").strip()
    target_environment = str(payload.get("target_environment") or "").strip()
    previous_package_id = str(payload.get("previous_package_id") or "").strip() or None
    if not package_version or len(package_version) > 120 or risk_level not in RISK_LEVELS or target_environment not in TARGET_ENVIRONMENTS:
        raise OperationsGovernanceError("validation_error", "package_version、risk_level或target_environment无效。")
    registry = get_registry()
    capability_ids = [item["id"] for item in registry["capabilities"]]
    manifest = _snapshot_manifest()
    _verify_bundle(manifest)
    package_id = new_id("opspkg")
    timestamp = now_iso()
    with get_connection() as conn:
        if previous_package_id:
            _package(conn, previous_package_id)
        try:
            conn.execute(
                """INSERT INTO operations_release_packages
                   (id,package_version,previous_package_id,risk_level,target_environment,capability_ids_json,
                    manifest_json,manifest_hash,artifact_count,status,proposed_by,production_release_approved,created_at,updated_at)
                   VALUES (?,?,?,?,?,?,?,?,?,'proposed',?,0,?,?)""",
                (package_id, package_version, previous_package_id, risk_level, target_environment, json_dumps(capability_ids), json_dumps(manifest), manifest["bundle_hash"], len(manifest["artifacts"]), actor["id"], timestamp, timestamp),
            )
        except Exception as exc:
            if "unique" in str(exc).lower() or "duplicate" in str(exc).lower():
                raise OperationsGovernanceError("package_version_exists", "修订必须使用新的发布包版本。", 409) from exc
            raise
        write_audit_log(conn, "operations_package_proposed", actor["id"], "operations_release_package", package_id, {"package_version": package_version, "manifest_hash": manifest["bundle_hash"], "risk_level": risk_level, "target_environment": target_environment, "contains_participant_data": False})
        conn.commit()
    return package_detail(package_id)


def _wording_snapshot() -> dict:
    snapshot = {}
    for filename, list_key, text_keys in (
        ("ai_qa_safety_responses.json", "responses", ("title", "body", "boundary_notice")),
        ("feedback_rules.json", "rules", ("label", "supportive_feedback", "alternative_response")),
        ("training_cards.json", "cards", ("title", "purpose", "boundary_notice")),
    ):
        payload = json.loads((Path(current_app.config["CONTENT_DIR"]) / filename).read_text(encoding="utf-8"))
        for index, item in enumerate(payload.get(list_key, [])):
            item_id = str(item.get("id") or item.get("rule_id") or index)
            for key in text_keys:
                if item.get(key):
                    snapshot[f"{filename}:{item_id}:{key}"] = str(item[key])
    return snapshot


def execute_fixed_replay(_package_item: dict, previous_run: dict | None = None) -> dict:
    content_suite = _read_json(CONTENT_REPLAY_PATH, "content_replay_unavailable")
    ai_suite = _read_json(AI_REPLAY_PATH, "ai_replay_unavailable")
    if content_suite.get("contains_real_data") is not False or ai_suite.get("contains_real_data") is not False:
        raise OperationsGovernanceError("replay_fixture_privacy_invalid", "固定回放集必须明确不含真实数据。", 409)
    results = []
    for case in content_suite.get("cases", []):
        text = str(case.get("text") or "")
        risk = check_text_risk(text, source="operations_governance_replay")
        feedback = None if not risk["allow_auto_feedback"] else generate_feedback({"scene": "合成回放", "raw_text": text, "parent_emotion": case.get("emotion", "")})
        actual = {
            "risk_level": risk["risk_level"],
            "auto_feedback_allowed": risk["allow_auto_feedback"],
            "recommendation_allowed": risk["allow_recommended_training_cards"],
            "recommended_card_ids": (feedback or {}).get("recommended_card_ids", []),
            "boundary_notice_present": bool(risk.get("boundary_notice")),
        }
        expected = case.get("expected") or {}
        passed = all(actual.get(key) == value for key, value in expected.items())
        results.append({"case_id": f"content:{case.get('case_id')}", "family": "recommendation_risk", "severity": "critical" if case.get("case_id") == "high-risk-block" else "medium", "passed": passed, "actual": actual, "expected": expected})
    for case in ai_suite.get("cases", []):
        evaluated = _evaluate_case(case)
        critical = case.get("category") in {"diagnosis", "treatment", "crisis", "violence", "abuse", "privacy", "injection", "tool_abuse"}
        results.append({"case_id": f"ai:{case.get('id')}", "family": "refusal_and_safety", "severity": "critical" if critical else "medium", "passed": evaluated["passed"], "actual": {"route": evaluated["actual_route"]}, "expected": {"route": evaluated["expected_route"]}})
    wording = _wording_snapshot()
    previous_payload = (previous_run or {}).get("results") if previous_run else {}
    previous_cases = {item["case_id"]: item for item in (previous_payload or {}).get("cases", [])}
    previous_wording = (previous_payload or {}).get("wording_snapshot", {})
    behavior_regressions = []
    for item in results:
        previous = previous_cases.get(item["case_id"])
        if previous and previous.get("actual") != item.get("actual"):
            behavior_regressions.append({"case_id": item["case_id"], "severity": item["severity"], "before": previous.get("actual"), "after": item.get("actual")})
    wording_diff_keys = sorted(key for key in set(wording) | set(previous_wording) if previous_wording and wording.get(key) != previous_wording.get(key))
    high_failures = sum(1 for item in results if item["severity"] == "critical" and not item["passed"])
    high_regressions = high_failures + sum(1 for item in behavior_regressions if item["severity"] == "critical")
    metrics = {
        "total": len(results),
        "passed": sum(1 for item in results if item["passed"]),
        "failed": sum(1 for item in results if not item["passed"]),
        "high_severity_regressions": high_regressions,
        "behavior_diff_count": len(behavior_regressions),
        "wording_diff_count": len(wording_diff_keys),
    }
    stored_results = {"cases": results, "behavior_regressions": behavior_regressions, "wording_snapshot": wording, "wording_diff_keys": wording_diff_keys}
    return {"suite_version": f"{content_suite.get('version')}+{ai_suite.get('version')}", "results": stored_results, "metrics": metrics, "snapshot_hash": _hash(stored_results)}


def run_replay(actor: dict, package_id: str) -> dict:
    package_item = package_detail(package_id, expose_bundle=True)
    _verify_bundle(package_item["manifest"])
    previous_run = None
    previous_id = package_item.get("previous_package_id")
    if previous_id:
        previous = package_detail(previous_id)
        previous_run = previous.get("replay_runs", [None])[0] if previous.get("replay_runs") else None
    outcome = execute_fixed_replay(package_item, previous_run)
    metrics = outcome.get("metrics") or {}
    high = int(metrics.get("high_severity_regressions") or 0)
    wording = int(metrics.get("wording_diff_count") or 0)
    status = "blocked_high_severity_regression" if high else "engineering_replay_passed_human_review_pending"
    run_id = new_id("opsreplay")
    timestamp = now_iso()
    with get_connection() as conn:
        conn.execute(
            """INSERT INTO operations_replay_runs
               (id,package_id,suite_version,results_json,metrics_json,snapshot_hash,status,high_severity_regressions,wording_diff_count,contains_real_data,created_by,created_at)
               VALUES (?,?,?,?,?,?,?,?,?,0,?,?)""",
            (run_id, package_id, outcome.get("suite_version", "unknown"), json_dumps(outcome.get("results", [])), json_dumps(metrics), outcome.get("snapshot_hash") or _hash(outcome), status, high, wording, actor["id"], timestamp),
        )
        write_audit_log(conn, "operations_replay_run", actor["id"], "operations_release_package", package_id, {"run_id": run_id, "status": status, "high_severity_regressions": high, "wording_diff_count": wording, "contains_real_data": False})
        conn.commit()
        row = conn.execute("SELECT * FROM operations_replay_runs WHERE id = ?", (run_id,)).fetchone()
    return _decode_row(row)


def submit_package(actor: dict, package_id: str) -> dict:
    package_item = package_detail(package_id, expose_bundle=True)
    if package_item["proposed_by"] != actor["id"] and actor.get("role") != "admin":
        raise OperationsGovernanceError("package_submit_forbidden", "仅提出者或管理员可送审。", 403)
    if package_item["status"] not in {"proposed", "changes_requested"}:
        raise OperationsGovernanceError("invalid_package_transition", "当前发布包不能送审。", 409)
    _verify_bundle(package_item["manifest"])
    latest = package_item.get("replay_runs", [None])[0] if package_item.get("replay_runs") else None
    if not latest or latest["status"] != "engineering_replay_passed_human_review_pending" or latest["high_severity_regressions"]:
        raise OperationsGovernanceError("release_replay_gate_failed", "固定回放未通过或存在高严重度回归。", 409)
    timestamp = now_iso()
    with get_connection() as conn:
        conn.execute("UPDATE operations_release_packages SET status = 'under_review', submitted_at = ?, updated_at = ? WHERE id = ?", (timestamp, timestamp, package_id))
        write_audit_log(conn, "operations_package_submitted", actor["id"], "operations_release_package", package_id, {"replay_run_id": latest["id"]})
        conn.commit()
    return package_detail(package_id)


def review_package(actor: dict, package_id: str, payload: dict) -> dict:
    unknown = set(payload) - {"decision", "evidence_ref", "note"}
    decision = str(payload.get("decision") or "")
    evidence_ref = str(payload.get("evidence_ref") or "").strip()
    if unknown or decision not in {"recommended", "changes_requested"} or not evidence_ref:
        raise OperationsGovernanceError("validation_error", "审核决定或证据引用无效。", details={"unknown_fields": sorted(unknown)})
    item = package_detail(package_id)
    if item["status"] != "under_review" or actor["id"] == item["proposed_by"]:
        raise OperationsGovernanceError("review_independence_required", "审核人与提出者必须分离，且发布包须处于审核中。", 409)
    review_id = new_id("opsreview")
    timestamp = now_iso()
    with get_connection() as conn:
        conn.execute("DELETE FROM operations_package_reviews WHERE package_id = ? AND stage = 'review' AND reviewer_id = ?", (package_id, actor["id"]))
        conn.execute(
            "INSERT INTO operations_package_reviews (id,package_id,stage,domain,decision,reviewer_id,reviewer_role,evidence_ref,note,created_at) VALUES (?,?,'review','cross_functional',?,?,?,?,?,?)",
            (review_id, package_id, decision, actor["id"], actor["role"], evidence_ref, str(payload.get("note") or "")[:1000] or None, timestamp),
        )
        new_status = "changes_requested" if decision == "changes_requested" else "under_review"
        conn.execute("UPDATE operations_release_packages SET status = ?, updated_at = ? WHERE id = ?", (new_status, timestamp, package_id))
        write_audit_log(conn, "operations_package_reviewed", actor["id"], "operations_release_package", package_id, {"decision": decision, "evidence_ref": evidence_ref})
        conn.commit()
    return package_detail(package_id)


def approve_package(actor: dict, package_id: str, payload: dict) -> dict:
    unknown = set(payload) - {"domain", "decision", "evidence_ref", "note"}
    domain = str(payload.get("domain") or "")
    decision = str(payload.get("decision") or "")
    evidence_ref = str(payload.get("evidence_ref") or "").strip()
    if unknown or domain not in DOMAIN_ROLES or decision not in {"approved", "rejected"} or not evidence_ref:
        raise OperationsGovernanceError("validation_error", "批准领域、决定或证据引用无效。", details={"unknown_fields": sorted(unknown)})
    if actor.get("role") not in DOMAIN_ROLES[domain]:
        raise OperationsGovernanceError("approval_domain_forbidden", "当前角色不能代表该专业领域批准。", 403)
    item = package_detail(package_id)
    if item["status"] not in {"under_review", "approved"} or actor["id"] == item["proposed_by"]:
        raise OperationsGovernanceError("approval_independence_required", "批准人与提出者必须分离，且发布包须处于审核中。", 409)
    if not any(review["decision"] == "recommended" for review in item["reviews"]):
        raise OperationsGovernanceError("independent_review_required", "批准前必须有独立审核建议。", 409)
    if any(review["reviewer_id"] == actor["id"] for review in item["reviews"]):
        raise OperationsGovernanceError("review_approval_separation_required", "同一人不能同时完成审核和批准。", 409)
    if any(approval["reviewer_id"] == actor["id"] and approval["domain"] != domain for approval in item["approvals"]):
        raise OperationsGovernanceError("multi_domain_approval_independence_required", "同一人不能代表多个批准领域。", 409)
    approval_id = new_id("opsapproval")
    timestamp = now_iso()
    with get_connection() as conn:
        conn.execute("DELETE FROM operations_package_reviews WHERE package_id = ? AND stage = 'approval' AND domain = ? AND reviewer_id = ?", (package_id, domain, actor["id"]))
        conn.execute(
            "INSERT INTO operations_package_reviews (id,package_id,stage,domain,decision,reviewer_id,reviewer_role,evidence_ref,note,created_at) VALUES (?,?,'approval',?,?,?,?,?,?,?)",
            (approval_id, package_id, domain, decision, actor["id"], actor["role"], evidence_ref, str(payload.get("note") or "")[:1000] or None, timestamp),
        )
        rows = conn.execute("SELECT domain,decision,created_at FROM operations_package_reviews WHERE package_id = ? AND stage = 'approval' ORDER BY created_at", (package_id,)).fetchall()
        latest = {}
        for row in rows:
            latest[row["domain"]] = row["decision"]
        required = APPROVAL_DOMAINS[item["risk_level"]]
        status = "changes_requested" if "rejected" in latest.values() else ("approved" if all(latest.get(name) == "approved" for name in required) else "under_review")
        conn.execute("UPDATE operations_release_packages SET status = ?, updated_at = ? WHERE id = ?", (status, timestamp, package_id))
        write_audit_log(conn, "operations_package_approval_recorded", actor["id"], "operations_release_package", package_id, {"domain": domain, "decision": decision, "required_domains": list(required), "resulting_status": status})
        conn.commit()
    return package_detail(package_id)


@contextmanager
def _release_lock():
    lock = Path(current_app.config["CONTENT_DIR"]) / ".operations-governance.lock"
    descriptor = None
    for _ in range(2):
        try:
            descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(descriptor, now_iso().encode("utf-8"))
            break
        except FileExistsError as exc:
            if lock.exists() and time.time() - lock.stat().st_mtime > 300:
                lock.unlink(missing_ok=True)
                continue
            raise OperationsGovernanceError("operations_release_in_progress", "已有发布、恢复或回滚操作正在执行。", 409) from exc
    if descriptor is None:
        raise OperationsGovernanceError("operations_release_lock_failed", "无法取得运营发布锁。", 409)
    try:
        yield
    finally:
        os.close(descriptor)
        lock.unlink(missing_ok=True)


def _apply_bundle(manifest: dict) -> dict[Path, bytes | None]:
    _verify_bundle(manifest)
    backups: dict[Path, bytes | None] = {}
    staged: list[tuple[Path, Path]] = []
    try:
        for artifact in manifest["artifacts"]:
            target = _artifact_target(artifact["path"])
            raw = base64.b64decode(artifact["bundle_b64"])
            backups[target] = target.read_bytes() if target.exists() else None
            target.parent.mkdir(parents=True, exist_ok=True)
            temp = target.with_suffix(target.suffix + ".t34-stage")
            temp.write_bytes(raw)
            if hashlib.sha256(temp.read_bytes()).hexdigest() != artifact["sha256"]:
                raise OperationsGovernanceError("staged_artifact_integrity_failed", f"暂存制品哈希失败：{artifact['path']}", 409)
            staged.append((temp, target))
        for temp, target in staged:
            os.replace(temp, target)
        return backups
    except Exception:
        for temp, _target in staged:
            temp.unlink(missing_ok=True)
        _restore_files(backups)
        raise


def _restore_files(backups: dict[Path, bytes | None]) -> None:
    for target, raw in backups.items():
        if raw is None:
            target.unlink(missing_ok=True)
        else:
            restore = target.with_suffix(target.suffix + ".t34-restore")
            restore.write_bytes(raw)
            os.replace(restore, target)


def _set_runtime_control(conn, capability_id: str, package_id: str | None, state: str, reason_code: str, actor_id: str) -> None:
    row = conn.execute("SELECT * FROM operations_runtime_controls WHERE capability_id = ?", (capability_id,)).fetchone()
    timestamp = now_iso()
    if row:
        conn.execute(
            "UPDATE operations_runtime_controls SET previous_package_id = active_package_id, active_package_id = ?, state = ?, version = version + 1, reason_code = ?, changed_by = ?, changed_at = ?, production_release_approved = 0 WHERE capability_id = ?",
            (package_id, state, reason_code, actor_id, timestamp, capability_id),
        )
    else:
        conn.execute(
            "INSERT INTO operations_runtime_controls (capability_id,active_package_id,previous_package_id,state,version,reason_code,changed_by,changed_at,production_release_approved) VALUES (?,?,NULL,?,1,?,?,?,0)",
            (capability_id, package_id, state, reason_code, actor_id, timestamp),
        )


def _release_gate(item: dict, actor: dict, payload: dict) -> None:
    if item["status"] != "approved":
        raise OperationsGovernanceError("package_not_approved", "发布包尚未完成分权批准。", 409)
    participant_ids = {item["proposed_by"]} | {review["reviewer_id"] for review in item["reviews"] + item["approvals"]}
    if actor["id"] in participant_ids:
        raise OperationsGovernanceError("release_actor_independence_required", "发布执行人与提出、审核和批准人员必须分离。", 409)
    latest = item.get("replay_runs", [None])[0] if item.get("replay_runs") else None
    if not latest or latest["status"] != "engineering_replay_passed_human_review_pending" or latest["high_severity_regressions"]:
        raise OperationsGovernanceError("release_replay_gate_failed", "发布前固定回放门禁未通过。", 409)
    if item["target_environment"] == "local_synthetic":
        if not current_app.config.get("OPERATIONS_LOCAL_RELEASE_ENABLED", False) or payload.get("confirmation") != "LOCAL_SYNTHETIC_RELEASE_ONLY":
            raise OperationsGovernanceError("local_release_gate_disabled", "本地合成发布开关或确认短语不满足。", 503)
    else:
        if not current_app.config.get("OPERATIONS_PRODUCTION_RELEASE_ENABLED", False):
            raise OperationsGovernanceError("production_release_gate_disabled", "生产运营发布门禁未批准。", 503)
        with get_connection() as conn:
            evidence = conn.execute("SELECT * FROM operations_evidence_packages WHERE human_approved = 1 AND ethics_approved = 1 AND cloud_approved = 1 AND device_approved = 1 AND production_release_approved = 1 ORDER BY created_at DESC LIMIT 1").fetchone()
        if not evidence:
            raise OperationsGovernanceError("external_release_evidence_missing", "缺少人工、伦理、云、真机和生产批准证据。", 409)


def release_package(actor: dict, package_id: str, payload: dict) -> dict:
    item = package_detail(package_id, expose_bundle=True)
    _release_gate(item, actor, payload)
    _verify_bundle(item["manifest"])
    with _release_lock():
        backups = _apply_bundle(item["manifest"])
        try:
            with get_connection() as conn:
                conn.execute("UPDATE operations_release_packages SET status = 'superseded', updated_at = ? WHERE status = 'active_local_synthetic' AND id <> ?", (now_iso(), package_id))
                state = "active_local_synthetic" if item["target_environment"] == "local_synthetic" else "active_production"
                timestamp = now_iso()
                conn.execute("UPDATE operations_release_packages SET status = ?, released_by = ?, released_at = ?, updated_at = ?, production_release_approved = ? WHERE id = ?", (state, actor["id"], timestamp, timestamp, int(item["target_environment"] == "production_candidate"), package_id))
                for capability_id in item["capability_ids"]:
                    _set_runtime_control(conn, capability_id, package_id, state, "package_release", actor["id"])
                write_audit_log(conn, "operations_package_released", actor["id"], "operations_release_package", package_id, {"target_environment": item["target_environment"], "manifest_hash": item["manifest_hash"], "production_release_approved": item["target_environment"] == "production_candidate"})
                conn.commit()
        except Exception:
            _restore_files(backups)
            raise
    return package_detail(package_id)


def change_package_state(actor: dict, package_id: str, action: str, payload: dict) -> dict:
    if action not in {"pause", "resume", "retire"}:
        raise OperationsGovernanceError("validation_error", "不支持的发布包动作。")
    reason = str(payload.get("reason_code") or "").strip()
    if set(payload) - {"reason_code"} or not reason:
        raise OperationsGovernanceError("validation_error", "必须提供固定原因代码，且不得附带参与者文本。")
    item = package_detail(package_id, expose_bundle=True)
    timestamp = now_iso()
    if action == "pause":
        if item["status"] not in {"active_local_synthetic", "active_production"}:
            raise OperationsGovernanceError("invalid_package_transition", "只有活动发布包可以暂停。", 409)
        with get_connection() as conn:
            conn.execute("UPDATE operations_release_packages SET status = 'paused', paused_by = ?, paused_at = ?, pause_reason_code = ?, updated_at = ? WHERE id = ?", (actor["id"], timestamp, reason, timestamp, package_id))
            for capability_id in item["capability_ids"]:
                _set_runtime_control(conn, capability_id, package_id, "paused", reason, actor["id"])
            write_audit_log(conn, "operations_package_paused", actor["id"], "operations_release_package", package_id, {"reason_code": reason})
            conn.commit()
    elif action == "resume":
        if item["status"] != "paused" or item.get("paused_by") == actor["id"]:
            raise OperationsGovernanceError("resume_independence_required", "恢复人与暂停人必须分离，且发布包须处于暂停状态。", 409)
        latest = item.get("replay_runs", [None])[0] if item.get("replay_runs") else None
        if not latest or latest["created_at"] <= (item.get("paused_at") or "") or latest["high_severity_regressions"]:
            raise OperationsGovernanceError("fresh_replay_required", "恢复前必须在暂停后重新通过固定回放。", 409)
        with _release_lock():
            backups = _apply_bundle(item["manifest"])
            try:
                with get_connection() as conn:
                    state = "active_local_synthetic" if item["target_environment"] == "local_synthetic" else "active_production"
                    conn.execute("UPDATE operations_release_packages SET status = ?, updated_at = ? WHERE id = ?", (state, timestamp, package_id))
                    for capability_id in item["capability_ids"]:
                        _set_runtime_control(conn, capability_id, package_id, state, reason, actor["id"])
                    write_audit_log(conn, "operations_package_resumed", actor["id"], "operations_release_package", package_id, {"reason_code": reason, "replay_run_id": latest["id"]})
                    conn.commit()
            except Exception:
                _restore_files(backups)
                raise
    else:
        if item["status"] not in {"paused", "superseded"}:
            raise OperationsGovernanceError("invalid_package_transition", "只有暂停或已替代发布包可以退役。", 409)
        with get_connection() as conn:
            conn.execute("UPDATE operations_release_packages SET status = 'retired', retired_by = ?, retired_at = ?, updated_at = ? WHERE id = ?", (actor["id"], timestamp, timestamp, package_id))
            write_audit_log(conn, "operations_package_retired", actor["id"], "operations_release_package", package_id, {"reason_code": reason})
            conn.commit()
    return package_detail(package_id)


def rollback_runtime(actor: dict, payload: dict) -> dict:
    if set(payload) - {"target_package_id", "reason_code"}:
        raise OperationsGovernanceError("validation_error", "回滚请求包含未允许字段。")
    target_id = str(payload.get("target_package_id") or "")
    reason = str(payload.get("reason_code") or "").strip()
    if not target_id or not reason:
        raise OperationsGovernanceError("validation_error", "target_package_id与reason_code为必填。")
    target = package_detail(target_id, expose_bundle=True)
    if target["status"] not in {"superseded", "active_local_synthetic", "paused"} or target["target_environment"] != "local_synthetic":
        raise OperationsGovernanceError("rollback_target_invalid", "目标包不是可恢复的本地合成不可变发布包。", 409)
    _verify_bundle(target["manifest"])
    with _release_lock():
        backups = _apply_bundle(target["manifest"])
        try:
            with get_connection() as conn:
                current = conn.execute("SELECT id FROM operations_release_packages WHERE status = 'active_local_synthetic' AND id <> ?", (target_id,)).fetchone()
                if current:
                    conn.execute("UPDATE operations_release_packages SET status = 'superseded', updated_at = ? WHERE id = ?", (now_iso(), current["id"]))
                conn.execute("UPDATE operations_release_packages SET status = 'active_local_synthetic', updated_at = ? WHERE id = ?", (now_iso(), target_id))
                for capability_id in target["capability_ids"]:
                    _set_runtime_control(conn, capability_id, target_id, "active_local_synthetic", reason, actor["id"])
                write_audit_log(conn, "operations_runtime_rolled_back", actor["id"], "operations_release_package", target_id, {"reason_code": reason, "manifest_hash": target["manifest_hash"], "previous_active_package_id": current["id"] if current else None})
                conn.commit()
        except Exception:
            _restore_files(backups)
            raise
    return {"active_package_id": target_id, "state": "active_local_synthetic", "manifest_hash": target["manifest_hash"], "atomic_pointer_switch": True, "artifact_restore_verified": True, "production_release_approved": False}


def _rate(numerator: int, denominator: int) -> float | None:
    return round(numerator / denominator, 4) if denominator else None


def create_monitor_snapshot(actor: dict, payload: dict) -> dict:
    if set(payload) - {"window_days", "environment"}:
        raise OperationsGovernanceError("validation_error", "监控快照只接受窗口与环境，不接受文本或自报结论。")
    window_days = int(payload.get("window_days") or 30)
    environment = str(payload.get("environment") or "local_synthetic")
    if window_days < 1 or window_days > 365 or environment not in {"local_synthetic", "test_cloud", "production_observation"}:
        raise OperationsGovernanceError("validation_error", "监控窗口或环境无效。")
    registry = get_registry()
    with get_connection() as conn:
        observed_modules = {row["module"] for row in conn.execute("SELECT DISTINCT module FROM observability_events").fetchall()}
        module_ids = {item["id"].removeprefix("capability.") for item in registry["capabilities"]}
        normalized_observed = {value.removeprefix("routes.") for value in observed_modules}
        coverage_rate = _rate(len(module_ids & normalized_observed), len(module_ids)) or 0.0
        annotations = conn.execute("SELECT emotion_label, uncertain FROM offline_benchmark_annotations").fetchall()
        unknown = sum(1 for row in annotations if row["emotion_label"] in {"unmapped", "unknown"} or bool(row["uncertain"]))
        feedback_rows = conn.execute("SELECT evaluation FROM feedback_ledger WHERE status = 'active'").fetchall()
        non_conformity = sum(1 for row in feedback_rows if row["evaluation"] == "does_not_match")
        discomfort = sum(1 for row in feedback_rows if row["evaluation"] == "uncomfortable")
        provider_rows = conn.execute("SELECT status FROM ai_qa_provider_events").fetchall()
        provider_errors = sum(1 for row in provider_rows if row["status"] not in {"success", "answered", "ok"})
        recommendations = []
        for row in conn.execute("SELECT recommended_card_ids_json FROM feedback_results").fetchall():
            recommendations.extend(json_loads(row["recommended_card_ids_json"], []))
        top_recommendation = max(Counter(recommendations).values(), default=0)
        supervision_count = int(conn.execute("SELECT COUNT(*) AS count FROM supervision_requests").fetchone()["count"])
        source_count = int(conn.execute("SELECT COUNT(*) AS count FROM emotion_diaries").fetchone()["count"]) + int(conn.execute("SELECT COUNT(*) AS count FROM assessment_results").fetchone()["count"])
    metrics = {
        "coverage_rate": coverage_rate,
        "unknown_label_rate": _rate(unknown, len(annotations)),
        "recommendation_concentration": _rate(top_recommendation, len(recommendations)),
        "non_conformity_rate": _rate(non_conformity, len(feedback_rows)),
        "discomfort_rate": _rate(discomfort, len(feedback_rows)),
        "manual_escalation_rate": _rate(supervision_count, source_count),
        "provider_error_rate": _rate(provider_errors, len(provider_rows)),
        "sample_sizes": {"observed_modules": len(observed_modules), "annotations": len(annotations), "recommendations": len(recommendations), "feedback": len(feedback_rows), "provider_events": len(provider_rows), "journey_sources": source_count},
    }
    signals = []
    comparisons = [
        ("coverage_rate", "below", THRESHOLDS["coverage_rate_min"]),
        ("unknown_label_rate", "above", THRESHOLDS["unknown_label_rate_max"]),
        ("recommendation_concentration", "above", THRESHOLDS["recommendation_concentration_max"]),
        ("non_conformity_rate", "above", THRESHOLDS["non_conformity_rate_max"]),
        ("discomfort_rate", "above", THRESHOLDS["discomfort_rate_max"]),
        ("manual_escalation_rate", "above", THRESHOLDS["manual_escalation_rate_max"]),
        ("provider_error_rate", "above", THRESHOLDS["provider_error_rate_max"]),
    ]
    for name, direction, threshold in comparisons:
        value = metrics[name]
        if value is not None and ((direction == "above" and value > threshold) or (direction == "below" and value < threshold)):
            signals.append({"metric": name, "direction": direction, "value": value, "threshold": threshold, "action": "human_review_required"})
    review_required = bool(signals)
    snapshot_id = new_id("opsmonitor")
    timestamp = now_iso()
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO operations_monitor_snapshots (id,environment,window_days,metrics_json,thresholds_json,drift_signals_json,review_required,automatic_participant_or_family_judgment,contains_participant_text,created_by,created_at) VALUES (?,?,?,?,?,?,?,0,0,?,?)",
            (snapshot_id, environment, window_days, json_dumps(metrics), json_dumps(THRESHOLDS), json_dumps(signals), int(review_required), actor["id"], timestamp),
        )
        write_audit_log(conn, "operations_monitor_snapshot_created", actor["id"], "operations_monitor_snapshot", snapshot_id, {"environment": environment, "review_required": review_required, "signal_count": len(signals), "contains_participant_text": False, "automatic_participant_or_family_judgment": False})
        conn.commit()
        row = conn.execute("SELECT * FROM operations_monitor_snapshots WHERE id = ?", (snapshot_id,)).fetchone()
    item = _decode_row(row)
    item["interpretation"] = "这些是运营复核信号，只触发人工检查，不代表任何参与者或家庭状态变差。"
    return item


def _notification_roles(incident_type: str) -> tuple[str, ...]:
    mapping = {
        "unauthorized_access": ("security_owner", "privacy_owner", "operations_owner"),
        "data_leak": ("security_owner", "privacy_owner", "operations_owner"),
        "severe_adverse_event": ("psychology_supervisor", "ethics_owner", "operations_owner"),
        "ai_safety_failure": ("ai_safety_owner", "security_owner", "operations_owner"),
        "psychological_content_misdelivery": ("psychology_supervisor", "content_owner", "operations_owner"),
        "cross_object_disclosure": ("security_owner", "privacy_owner", "operations_owner"),
        "deletion_failure": ("privacy_owner", "database_owner", "operations_owner"),
        "high_risk_feedback_error": ("psychology_supervisor", "ethics_owner", "operations_owner"),
        "external_message_misdelivery": ("privacy_owner", "operations_owner", "communications_owner"),
    }
    return mapping[incident_type]


def _incident_detail(conn, incident_id: str) -> dict:
    row = conn.execute("SELECT * FROM operations_incidents WHERE id = ?", (incident_id,)).fetchone()
    if not row:
        raise OperationsGovernanceError("not_found", "运营事件不存在。", 404)
    item = _decode_row(row)
    item["notifications"] = [_decode_row(value) for value in conn.execute("SELECT * FROM operations_incident_notifications WHERE incident_id = ? ORDER BY created_at", (incident_id,)).fetchall()]
    return item


def report_incident(actor: dict, payload: dict) -> dict:
    allowed = {
        "capability_id", "package_id", "incident_type", "severity", "evidence_refs", "summary_code",
        "impact_code", "started_at", "detected_at", "decisions", "followup_actions",
    }
    unknown = set(payload) - allowed
    capability_id = str(payload.get("capability_id") or "")
    package_id = str(payload.get("package_id") or "").strip() or None
    incident_type = str(payload.get("incident_type") or "")
    severity = str(payload.get("severity") or "")
    evidence_refs = payload.get("evidence_refs")
    summary_code = str(payload.get("summary_code") or "").strip()
    capability_ids = {item["id"] for item in get_registry()["capabilities"]}
    if unknown or capability_id not in capability_ids or incident_type not in INCIDENT_TYPES or severity not in INCIDENT_SEVERITIES or not summary_code or not isinstance(evidence_refs, list) or not evidence_refs or len(evidence_refs) > 20:
        raise OperationsGovernanceError("validation_error", "事件字段无效或包含未允许内容。", details={"unknown_fields": sorted(unknown)})
    normalized_refs = [str(value)[:300] for value in evidence_refs if str(value).strip()]
    if len(normalized_refs) != len(evidence_refs):
        raise OperationsGovernanceError("validation_error", "证据引用不能为空。")
    incident_id = new_id("opsincident")
    timestamp = now_iso()
    try:
        incident_record = sanitize_incident_record(
            {
                "impact_code": str(payload.get("impact_code") or summary_code),
                "started_at": str(payload.get("started_at") or timestamp),
                "detected_at": str(payload.get("detected_at") or timestamp),
                "recovered_at": None,
                "evidence_refs": normalized_refs,
                "decisions": payload.get("decisions") or ["contain_and_disable"],
                "followup_actions": payload.get("followup_actions") or ["human_postmortem_required"],
            }
        )
    except OperationsReliabilityError as exc:
        raise OperationsGovernanceError(exc.code, str(exc)) from exc
    evidence_hold_hash = _hash({"incident_id": incident_id, "capability_id": capability_id, "package_id": package_id, "incident_type": incident_type, "severity": severity, "summary_code": summary_code, "evidence_refs": normalized_refs, "reported_at": timestamp})
    with get_connection() as conn:
        if package_id:
            _package(conn, package_id)
        conn.execute(
            """INSERT INTO operations_incidents
               (id,capability_id,package_id,incident_type,severity,status,summary_code,evidence_refs_json,evidence_hold_hash,
                capability_disabled,notification_required,postmortem_json,reported_by,reported_at,updated_at)
               VALUES (?,?,?,?,?,'contained_disabled_notifications_queued',?,?,?,1,1,?,?,?,?)""",
            (incident_id, capability_id, package_id, incident_type, severity, summary_code, json_dumps(normalized_refs), evidence_hold_hash, json_dumps({"incident_record": incident_record}), actor["id"], timestamp, timestamp),
        )
        _set_runtime_control(conn, capability_id, package_id, "disabled_by_incident", f"incident:{incident_type}", actor["id"])
        for recipient_role in _notification_roles(incident_type):
            notification_id = new_id("opsnotice")
            key = f"{incident_id}:{recipient_role}"
            conn.execute(
                "INSERT INTO operations_incident_notifications (id,incident_id,recipient_role,status,attempt_count,idempotency_key,next_attempt_at,created_at,updated_at) VALUES (?,?,?,'queued',0,?,?,?,?)",
                (notification_id, incident_id, recipient_role, key, timestamp, timestamp, timestamp),
            )
        write_audit_log(conn, "operations_incident_contained", actor["id"], "operations_incident", incident_id, {"capability_id": capability_id, "incident_type": incident_type, "severity": severity, "evidence_hold_hash": evidence_hold_hash, "capability_disabled": True, "notification_roles": list(_notification_roles(incident_type)), "contains_participant_text": False})
        conn.commit()
        return _incident_detail(conn, incident_id)


def record_postmortem(actor: dict, incident_id: str, payload: dict) -> dict:
    allowed = {"root_cause_code", "corrective_actions", "evidence_refs", "recovered_at", "decisions", "followup_actions"}
    unknown = set(payload) - allowed
    root = str(payload.get("root_cause_code") or "").strip()
    actions = payload.get("corrective_actions")
    refs = payload.get("evidence_refs") or []
    if unknown or not root or not isinstance(actions, list) or not actions or len(actions) > 20 or not isinstance(refs, list):
        raise OperationsGovernanceError("validation_error", "复盘只接受原因代码、纠正动作和证据引用。", details={"unknown_fields": sorted(unknown)})
    timestamp = now_iso()
    with get_connection() as conn:
        item = _incident_detail(conn, incident_id)
        if item["status"] == "closed":
            raise OperationsGovernanceError("incident_already_closed", "事件已关闭。", 409)
        initial_record = (item.get("postmortem") or {}).get("incident_record") or {}
        try:
            incident_record = sanitize_incident_record(
                {
                    **initial_record,
                    "recovered_at": str(payload.get("recovered_at") or timestamp),
                    "decisions": payload.get("decisions") or initial_record.get("decisions") or ["keep_capability_disabled"],
                    "followup_actions": payload.get("followup_actions") or initial_record.get("followup_actions") or ["human_close_required"],
                }
            )
        except OperationsReliabilityError as exc:
            raise OperationsGovernanceError(exc.code, str(exc)) from exc
        postmortem = {
            "root_cause_code": root,
            "corrective_actions": [str(value)[:300] for value in actions],
            "evidence_refs": [str(value)[:300] for value in refs],
            "incident_record": incident_record,
            "automatic_resume": False,
            "human_close_required": True,
        }
        conn.execute("UPDATE operations_incidents SET status = 'postmortem_recorded_human_close_pending', postmortem_json = ?, postmortem_by = ?, postmortem_at = ?, updated_at = ? WHERE id = ?", (json_dumps(postmortem), actor["id"], timestamp, timestamp, incident_id))
        write_audit_log(conn, "operations_incident_postmortem_recorded", actor["id"], "operations_incident", incident_id, {"root_cause_code": root, "automatic_resume": False, "capability_disabled": True})
        conn.commit()
        return _incident_detail(conn, incident_id)


def update_notification(actor: dict, incident_id: str, notification_id: str, action: str, payload: dict) -> dict:
    if action not in {"dispatch", "fail"} or set(payload) - {"error_code"}:
        raise OperationsGovernanceError("validation_error", "通知动作或字段无效。")
    timestamp = now_iso()
    with get_connection() as conn:
        _incident_detail(conn, incident_id)
        row = conn.execute("SELECT * FROM operations_incident_notifications WHERE id = ? AND incident_id = ?", (notification_id, incident_id)).fetchone()
        if not row:
            raise OperationsGovernanceError("not_found", "事件通知不存在。", 404)
        if action == "dispatch":
            conn.execute("UPDATE operations_incident_notifications SET status = 'dispatched', attempt_count = attempt_count + 1, dispatched_by = ?, dispatched_at = ?, updated_at = ? WHERE id = ?", (actor["id"], timestamp, timestamp, notification_id))
        else:
            error_code = str(payload.get("error_code") or "notification_delivery_failed")[:120]
            conn.execute("UPDATE operations_incident_notifications SET status = 'retry_queued', attempt_count = attempt_count + 1, last_error_code = ?, next_attempt_at = ?, updated_at = ? WHERE id = ?", (error_code, timestamp, timestamp, notification_id))
        write_audit_log(conn, f"operations_incident_notification_{action}", actor["id"], "operations_incident_notification", notification_id, {"incident_id": incident_id, "contains_participant_text": False})
        conn.commit()
        return _decode_row(conn.execute("SELECT * FROM operations_incident_notifications WHERE id = ?", (notification_id,)).fetchone())


def public_status() -> dict:
    registry = get_registry()
    with get_connection() as conn:
        active = int(conn.execute("SELECT COUNT(*) AS count FROM operations_release_packages WHERE status IN ('active_local_synthetic','active_production')").fetchone()["count"])
        open_incidents = int(conn.execute("SELECT COUNT(*) AS count FROM operations_incidents WHERE status <> 'closed'").fetchone()["count"])
    return {
        "status": registry["status"],
        "registry_version": registry["version"],
        "capability_count": registry["capability_count"],
        "active_package_count": active,
        "open_incident_count": open_incidents,
        "temporary_showcase_exception_retained": True,
        "formal_permission_acceptance": False,
        "production_release_approved": False,
        "boundary_notice": registry["boundary_notice"],
    }


def workbench() -> dict:
    if not current_app.config.get("OPERATIONS_GOVERNANCE_WORKBENCH_ENABLED", False):
        raise OperationsGovernanceError("operations_workbench_disabled", "当前环境未开启运营治理工作台。", 503)
    with get_connection() as conn:
        packages = [_decode_row(row) for row in conn.execute("SELECT * FROM operations_release_packages ORDER BY created_at DESC LIMIT 30").fetchall()]
        controls = [_decode_row(row) for row in conn.execute("SELECT * FROM operations_runtime_controls ORDER BY capability_id").fetchall()]
        snapshots = [_decode_row(row) for row in conn.execute("SELECT * FROM operations_monitor_snapshots ORDER BY created_at DESC LIMIT 20").fetchall()]
        incidents = [_incident_detail(conn, row["id"]) for row in conn.execute("SELECT id FROM operations_incidents ORDER BY reported_at DESC LIMIT 20").fetchall()]
        evidence = [_decode_row(row) for row in conn.execute("SELECT * FROM operations_evidence_packages ORDER BY created_at DESC LIMIT 20").fetchall()]
    return {"registry": get_registry(), "asset_cards": get_asset_cards(), "packages": packages, "runtime_controls": controls, "monitor_snapshots": snapshots, "incidents": incidents, "evidence_packages": evidence, "production_release_approved": False}


def create_evidence_package(actor: dict) -> dict:
    registry = get_registry()
    with get_connection() as conn:
        package = {
            "registry_version": registry["version"],
            "release_package_count": int(conn.execute("SELECT COUNT(*) AS count FROM operations_release_packages").fetchone()["count"]),
            "replay_run_count": int(conn.execute("SELECT COUNT(*) AS count FROM operations_replay_runs").fetchone()["count"]),
            "open_incident_count": int(conn.execute("SELECT COUNT(*) AS count FROM operations_incidents WHERE status <> 'closed'").fetchone()["count"]),
            "external_gates": registry["external_gates"],
            "human_approved": False,
            "ethics_approved": False,
            "cloud_approved": False,
            "device_approved": False,
            "production_release_approved": False,
            "signatures": [],
        }
        package_id = new_id("opsevidence")
        timestamp = now_iso()
        digest = _hash(package)
        conn.execute(
            "INSERT INTO operations_evidence_packages (id,status,package_json,artifact_hash,human_approved,ethics_approved,cloud_approved,device_approved,production_release_approved,created_by,created_at) VALUES (?,'draft_for_external_governance_review',?,?,0,0,0,0,0,?,?)",
            (package_id, json_dumps(package), digest, actor["id"], timestamp),
        )
        write_audit_log(conn, "operations_evidence_package_created", actor["id"], "operations_evidence_package", package_id, {"production_release_approved": False, "signatures": []})
        conn.commit()
    return {"id": package_id, "status": "draft_for_external_governance_review", **package, "artifact_hash": digest, "created_at": timestamp}
