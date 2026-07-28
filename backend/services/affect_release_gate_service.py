"""Evidence-only release gate for affect computation.

This service can assemble and audit a gate package. It never activates a model
runtime or turns an engineering result into a production approval.
"""

from __future__ import annotations

import hashlib
import json
import re

from flask import current_app

from database import (
    get_connection,
    json_dumps,
    json_loads,
    new_id,
    now_iso,
    row_to_dict,
    rows_to_dicts,
    write_audit_log,
)
from services.affect_shadow_service import AffectShadowError


SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")


def _content(name: str) -> dict:
    path = current_app.config["CONTENT_DIR"] / name
    return json.loads(path.read_text(encoding="utf-8"))


def _decode_run(row) -> dict:
    item = row_to_dict(row)
    item["checks"] = json_loads(item.pop("checks_json"), [])
    item["blockers"] = json_loads(item.pop("blockers_json"), [])
    item["runtime_activation_allowed"] = bool(item["runtime_activation_allowed"])
    item["production_release_approved"] = bool(item["production_release_approved"])
    return item


def _external_evidence() -> dict[str, list[dict]]:
    with get_connection() as conn:
        rows = rows_to_dicts(
            conn.execute(
                "SELECT * FROM offline_model_release_evidence "
                "ORDER BY recorded_at DESC"
            ).fetchall()
        )
    grouped: dict[str, list[dict]] = {}
    for item in rows:
        item["simulated_agent"] = bool(item["simulated_agent"])
        grouped.setdefault(item["gate_id"], []).append(item)
    return grouped


def _machine_checks(policy: dict) -> dict[str, bool]:
    candidate = _content("affect_model_candidate_registry.json")
    monitor = _content("affect_monitoring_policy.json")
    governance = _content("task37_data_use_governance.json")
    prohibited = set(
        governance["domains"]["affective_computing"].get("prohibited_uses", [])
    )
    required = set(policy["prohibited_outputs"])
    abstention = candidate.get("abstention_policy", {})
    return {
        "abstention_review_and_rollback": bool(abstention.get("reasons"))
        and "unknown_human_review" == abstention.get("outcome")
        and {"model_rollback", "threshold_rollback", "full_disable"}.issubset(
            set(monitor.get("rollback_actions", []))
        ),
        "non_diagnostic_output_boundary": required.issubset(prohibited),
    }


def build_release_gate(actor: dict) -> dict:
    policy = _content("affect_release_gate_policy.json")
    evidence = _external_evidence()
    machine = _machine_checks(policy)
    checks = []
    blockers = []
    for gate_id in policy["gate_order"]:
        if gate_id in machine:
            passed = machine[gate_id]
            source = "machine_contract"
        else:
            passed = bool(evidence.get(gate_id))
            source = "external_evidence"
        check = {
            "gate_id": gate_id,
            "passed": passed,
            "source": source,
            "evidence_count": len(evidence.get(gate_id, [])),
        }
        checks.append(check)
        if not passed:
            blockers.append(gate_id)
    status = (
        "ready_for_separate_release_decision"
        if not blockers
        else "blocked_external_gates"
    )
    payload = {
        "policy_version": policy["version"],
        "status": status,
        "checks": checks,
        "blockers": blockers,
        "runtime_activation_allowed": False,
        "production_release_approved": False,
    }
    artifact_hash = hashlib.sha256(
        json_dumps(payload).encode("utf-8")
    ).hexdigest()
    run_id = new_id("org")
    timestamp = now_iso()
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO offline_model_release_gate_runs "
            "(id, status, checks_json, blockers_json, artifact_hash, "
            "runtime_activation_allowed, production_release_approved, "
            "generated_by, generated_at) VALUES (?, ?, ?, ?, ?, 0, 0, ?, ?)",
            (
                run_id,
                status,
                json_dumps(checks),
                json_dumps(blockers),
                artifact_hash,
                actor["id"],
                timestamp,
            ),
        )
        write_audit_log(
            conn,
            "offline_model_release_gate_generated",
            actor["id"],
            "offline_model_release_gate",
            run_id,
            {
                "status": status,
                "blockers": blockers,
                "runtime_activation_allowed": False,
                "production_release_approved": False,
            },
        )
        conn.commit()
        row = conn.execute(
            "SELECT * FROM offline_model_release_gate_runs WHERE id = ?",
            (run_id,),
        ).fetchone()
    result = _decode_run(row)
    result["policy_version"] = policy["version"]
    result["boundary_notice"] = policy["boundary_notice"]
    result["temporary_showcase_privilege_counts_as_approval"] = False
    result["simulated_agent_counts_as_human_signoff"] = False
    return result


def release_gate_status() -> dict:
    policy = _content("affect_release_gate_policy.json")
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM offline_model_release_gate_runs "
            "ORDER BY generated_at DESC LIMIT 1"
        ).fetchone()
    latest = _decode_run(row) if row else None
    return {
        "policy_version": policy["version"],
        "latest": latest,
        "evidence": _external_evidence(),
        "runtime_activation_allowed": False,
        "production_release_approved": False,
        "boundary_notice": policy["boundary_notice"],
    }


def record_external_evidence(actor: dict, payload: dict) -> dict:
    policy = _content("affect_release_gate_policy.json")
    gate_id = str(payload.get("gate_id") or "").strip()
    if gate_id not in policy["human_or_external_gates"]:
        raise AffectShadowError("release_gate_invalid", "该门禁不接受外部证据")
    if payload.get("simulated_agent") is not False:
        raise AffectShadowError(
            "simulated_signoff_forbidden", "模拟Agent不能作为真人签字"
        )
    evidence_hash = str(payload.get("evidence_hash") or "").strip().lower()
    if not SHA256_PATTERN.fullmatch(evidence_hash):
        raise AffectShadowError("evidence_hash_invalid", "证据必须提供SHA-256哈希")
    evidence_type = str(payload.get("evidence_type") or "").strip()
    signer_name = str(payload.get("signer_name") or "").strip()
    source_environment = str(payload.get("source_environment") or "").strip()
    notes = str(payload.get("notes") or "").strip()
    if not evidence_type or len(signer_name) < 2 or not source_environment:
        raise AffectShadowError(
            "release_evidence_incomplete", "证据类型、签字人和来源环境不能为空"
        )
    evidence_id = new_id("ore")
    timestamp = now_iso()
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO offline_model_release_evidence "
            "(id, gate_id, evidence_hash, evidence_type, signer_name, "
            "source_environment, notes, simulated_agent, recorded_by, recorded_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, 0, ?, ?)",
            (
                evidence_id,
                gate_id,
                evidence_hash,
                evidence_type,
                signer_name,
                source_environment,
                notes[:500],
                actor["id"],
                timestamp,
            ),
        )
        write_audit_log(
            conn,
            "offline_model_release_evidence_recorded",
            actor["id"],
            "offline_model_release_evidence",
            evidence_id,
            {
                "gate_id": gate_id,
                "evidence_hash": evidence_hash,
                "simulated_agent": False,
                "runtime_activation_allowed": False,
            },
        )
        conn.commit()
        row = conn.execute(
            "SELECT * FROM offline_model_release_evidence WHERE id = ?",
            (evidence_id,),
        ).fetchone()
    result = row_to_dict(row)
    result["simulated_agent"] = False
    result["production_release_approved"] = False
    return result
