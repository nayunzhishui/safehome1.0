"""Versioned bridge for Task 38 therapeutic-assessment contracts."""

from __future__ import annotations

import hashlib
import json

from flask import current_app

from database import get_connection, json_dumps, new_id, now_iso, row_to_dict, write_audit_log
from services.therapeutic_assessment_service import TherapeuticAssessmentError


EXPECTED = {
    "service_levels": {"L0", "L1", "L2", "L3"},
    "competency_levels": {"T1", "T2", "T3"},
    "evidence_kinds": {"O", "P", "H", "U"},
    "five_gates": {"minimum_input", "permission", "source", "language", "responsibility"},
}


def _read(name: str) -> tuple[dict, str]:
    raw = (current_app.config["CONTENT_DIR"] / name).read_bytes()
    return json.loads(raw.decode("utf-8")), hashlib.sha256(raw).hexdigest()


def contract_status() -> dict:
    contract, contract_hash = _read("therapeutic_assessment_production_contract.json")
    drift = []
    actual_hashes = {}
    for filename, expected_hash in contract["source_contracts"].items():
        _, actual_hash = _read(filename)
        actual_hashes[filename] = actual_hash
        if actual_hash != expected_hash:
            drift.append(filename)
    for field, expected in EXPECTED.items():
        if set(contract.get(field, [])) != expected:
            drift.append(field)
    if contract.get("default_unknown_decision") != "deny":
        drift.append("default_unknown_decision")
    if drift:
        raise TherapeuticAssessmentError(
            "contract_drift",
            "协作式评估机器契约发生漂移，已默认拒绝。",
            409,
            {"drift_fields": drift},
        )
    return {
        **contract,
        "contract_hash": contract_hash,
        "source_hashes": actual_hashes,
        "drift_detected": False,
        "production_release_approved": False,
    }


def validate_dimensions(payload: dict) -> dict:
    contract = contract_status()
    checks = {
        "service_level": str(payload.get("service_level") or "") in EXPECTED["service_levels"],
        "competency_level": str(payload.get("competency_level") or "") in EXPECTED["competency_levels"],
        "evidence_kind": str(payload.get("evidence_kind") or "") in EXPECTED["evidence_kinds"],
        "object_permission": payload.get("object_permission") is True,
        "safety_state": str(payload.get("safety_state") or "") in {
            "low_risk",
            "needs_human_review",
            "safety_path",
            "stabilized",
            "closed",
        },
        "responsible_role": bool(str(payload.get("responsible_role") or "").strip()),
    }
    return {
        "allowed": all(checks.values()),
        "checks": checks,
        "default_unknown_decision": contract["default_unknown_decision"],
        "dimensions_are_separate": True,
        "temporary_showcase_bypass_accepted": False,
    }


def create_snapshot(actor: dict) -> dict:
    contract = contract_status()
    timestamp = now_iso()
    snapshot_id = new_id("tac")
    with get_connection() as conn:
        existing = conn.execute(
            "SELECT * FROM therapeutic_assessment_contract_snapshots "
            "WHERE contract_version = ? AND contract_hash = ?",
            (contract["version"], contract["contract_hash"]),
        ).fetchone()
        if existing:
            item = row_to_dict(existing)
            item["production_release_approved"] = False
            return item
        conn.execute(
            "INSERT INTO therapeutic_assessment_contract_snapshots "
            "(id, contract_version, contract_hash, source_hashes_json, status, "
            "drift_detected, production_release_approved, created_by, created_at) "
            "VALUES (?, ?, ?, ?, 'engineering_frozen', 0, 0, ?, ?)",
            (
                snapshot_id,
                contract["version"],
                contract["contract_hash"],
                json_dumps(contract["source_hashes"]),
                actor["id"],
                timestamp,
            ),
        )
        write_audit_log(
            conn,
            "therapeutic_assessment_contract_snapshot_created",
            actor["id"],
            "therapeutic_assessment_contract",
            snapshot_id,
            {
                "contract_version": contract["version"],
                "contract_hash": contract["contract_hash"],
                "production_release_approved": False,
            },
        )
        conn.commit()
        row = conn.execute(
            "SELECT * FROM therapeutic_assessment_contract_snapshots WHERE id = ?",
            (snapshot_id,),
        ).fetchone()
    item = row_to_dict(row)
    item["production_release_approved"] = False
    return item
