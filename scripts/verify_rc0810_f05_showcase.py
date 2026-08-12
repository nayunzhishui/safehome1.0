"""Verify the F05 production/validation Showcase profile contract."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def verify() -> dict:
    policy = json.loads((ROOT / "content" / "showcase_access.json").read_text(encoding="utf-8"))
    service = (ROOT / "backend" / "services" / "showcase_access_service.py").read_text(encoding="utf-8")
    auth = (ROOT / "backend" / "routes" / "auth_utils.py").read_text(encoding="utf-8")
    research_access = (ROOT / "backend" / "services" / "research_access_service.py").read_text(encoding="utf-8")
    profiles = json.loads((ROOT / "config" / "rc0810" / "build_profiles.json").read_text(encoding="utf-8"))

    allowed = set(policy.get("allowed_profiles") or [])
    errors: list[str] = []
    if "production" in allowed or not {"development", "testing", "validation"}.issubset(allowed):
        errors.append("showcase_allowed_profiles_invalid")
    if policy.get("break_glass", {}).get("implemented") is not False:
        errors.append("production_break_glass_must_not_be_invented_in_f05")
    if policy.get("break_glass", {}).get("production_available") is not False:
        errors.append("production_break_glass_must_remain_unavailable")
    if "profile not in allowed_profiles" not in service or "showcase_elevation_blocked" not in service:
        errors.append("service_profile_gate_or_audit_missing")
    if "record_showcase_elevation_decision(actor, allowed=True)" not in auth:
        errors.append("validation_grant_audit_missing")
    if "record_showcase_elevation_decision(actor, allowed=False)" not in auth:
        errors.append("production_block_audit_missing")
    if 'actor.get("showcase_full_access")' not in research_access:
        errors.append("capability_summary_not_bound_to_request_elevation")
    for item in profiles.get("artifact_profiles") or []:
        if item.get("target_environment") == "production" and item.get("capabilities", {}).get("showcase") is not False:
            errors.append(f"production_profile_showcase_enabled:{item.get('profile_id')}")

    return {
        "schema": "safehome.rc0810.f05-showcase-verification.v1",
        "valid": not errors,
        "allowed_profiles": sorted(allowed),
        "production_showcase_enabled": False,
        "break_glass_implemented": False,
        "errors": errors,
    }


if __name__ == "__main__":
    result = verify()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(0 if result["valid"] else 1)
