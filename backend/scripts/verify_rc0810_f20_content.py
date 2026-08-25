"""Verify the RC0810-F20 psychological content governance contract."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from services.psychological_content_governance_service import (  # noqa: E402
    build_content_audit,
    production_eligibility,
)


def verify(root: Path = ROOT) -> dict:
    audit = build_content_audit(root)
    errors = []
    descriptors = audit.get("governed_payloads") or []
    governed_types = {item.get("content_type") for item in descriptors}
    if governed_types != {"worksheet", "training_card", "feedback_rule"}:
        errors.append("governed_payload_types_incomplete")
    if any(
        item.get("hash_algorithm") != "sha256"
        or len(str(item.get("payload_hash") or "")) != 64
        or not item.get("version")
        for item in descriptors
    ):
        errors.append("governed_payload_descriptor_invalid")
    if audit.get("production_manifest") != {
        "worksheet_ids": [],
        "status": "blocked_external",
    }:
        errors.append("production_manifest_not_fail_closed")
    if audit.get("external_gates") != {
        "psychology_reviewer": "pending_external",
        "content_rights_owner": "pending_external",
    }:
        errors.append("external_gate_drift")
    legacy_profile = next(
        (
            item
            for item in audit.get("legacy_content_tracks") or []
            if item.get("endpoint") == "/api/profile"
        ),
        None,
    )
    if not legacy_profile or legacy_profile.get("production_enabled") is not False:
        errors.append("legacy_profile_track_not_fail_closed")
    rights = audit.get("scale_rights_and_use") or []
    if not rights or any(item.get("production_eligible") is not False for item in rights):
        errors.append("unapproved_scale_entered_production")
    if audit.get("dual_track_audit", {}).get("hardcoded_payload_matches"):
        errors.append("frontend_content_payload_hardcoded")
    if audit.get("copy_audit", {}).get("participant_findings"):
        errors.append("participant_copy_boundary_failed")
    return {
        "ok": not errors,
        "schema_version": audit.get("schema_version"),
        "policy_version": audit.get("policy_version"),
        "governed_payload_count": len(descriptors),
        "scale_rights_count": len(rights),
        "production_worksheet_count": len(
            audit.get("production_manifest", {}).get("worksheet_ids") or []
        ),
        "external_gates": audit.get("external_gates"),
        "dual_track_findings": len(
            audit.get("dual_track_audit", {}).get("hardcoded_payload_matches") or []
        ),
        "participant_copy_findings": len(
            audit.get("copy_audit", {}).get("participant_findings") or []
        ),
        "errors": errors,
    }


def self_check() -> dict:
    incomplete = {
        "id": "unsafe",
        "source_file": "unknown",
        "source_version": "v1",
        "questions": [],
        "scoring": "",
        "boundary_notice": "",
        "result_disclaimer": "",
    }
    decision = production_eligibility(
        incomplete,
        {"copyright_status": "owned", "production_approval": "approved"},
    )
    expected = {
        "questions_missing",
        "scoring_missing",
        "boundary_notice_missing",
        "result_disclaimer_missing",
    }
    ok = decision["eligible"] is False and expected.issubset(decision["blockers"])
    return {
        "ok": ok,
        "detected_failure": "incomplete_scale_blocked" if ok else None,
        "blockers": decision["blockers"],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-check", action="store_true")
    args = parser.parse_args()
    result = self_check() if args.self_check else verify()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
