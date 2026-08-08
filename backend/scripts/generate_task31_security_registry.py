"""Generate and live-validate the Task 31 security/privacy registry.

The machine API contract is the source of truth for the authorization matrix.
The persisted JSON remains a human-governed snapshot and must not silently
become the runtime authority when the contract evolves.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = ROOT / "shared" / "contracts" / "api-contract.json"
OUTPUT_PATH = ROOT / "content" / "security_privacy_abuse_registry.json"
ROLES = ("parent", "student", "researcher", "supervisor", "admin")


ASSETS = [
    ("identity_and_tokens", "users/auth tokens", "high", "auth backend", "service access", "revoke token epoch; anonymize approved identity scope"),
    ("assessment_raw_answers", "assessment_results.answers_json", "high", "participant and authorized reviewer", "service or separate research consent", "transactional privacy scope deletion"),
    ("emotion_diary_text", "emotion_diaries", "high", "participant and assigned reviewer", "service purpose", "transactional privacy scope deletion"),
    ("feedback_and_reports", "feedback_results/relationship reports", "high", "participant and assigned reviewer", "service delivery", "versioned withdrawal and privacy execution"),
    ("feedback_ledger", "feedback_ledger", "medium_high", "participant and assigned researcher aggregate", "collaborative correction", "privacy scope deletion; aggregate minimum retention pending"),
    ("messages_and_notifications", "messages/notification_*", "high", "participant and authorized sender", "in-app and WeChat consent separated", "delete approved scope; provider receipt boundary documented"),
    ("training_and_checkins", "training_cards/checkins/assignments", "medium_high", "participant and authorized reviewer", "service purpose", "privacy scope deletion"),
    ("research_exports", "admin export/records", "high", "authorized researcher/admin", "active research consent", "withdrawal blocks new exports; derived artifact policy pending"),
    ("offline_analysis", "offline benchmark artifacts", "high_or_aggregate", "authorized research workflow", "licensed public or synthetic data only", "participant text prohibited; dataset-card withdrawal"),
    ("ai_provider_boundary", "fake provider only", "critical", "internal sandbox", "no participant approval", "real egress absent and forced off"),
    ("backup_logs_audit", "backup/platform logs/audit_logs", "medium_high", "engineering/security", "security and accountability", "minimum audit proof retained; backup deletion SLA human-gated"),
]


WEB_THREATS = [
    ("token_leakage", "short-lived signed token, auth epoch revocation, no-store responses", "auth failure/security event", "engineering_security", "device compromise remains"),
    ("idor", "server-side owner/role/assignment checks; client role never authoritative", "allow/deny matrix and 403 audit tests", "backend_owner", "showcase read bypass remains a release blocker"),
    ("replay", "Idempotency-Key for stateful delivery/privacy/work-item actions", "idempotency conflict events", "backend_owner", "legacy writes without keys require inventory follow-up"),
    ("bulk_export", "role gate, consent filter, high-risk confirmation, 1000 default/5000 maximum", "export audit with row counts", "data_governance", "production export approval pending"),
    ("csv_injection", "prefix spreadsheet formula cells and fixed allowlisted filename", "CSV regression test", "backend_owner", "downstream spreadsheet policy still required"),
    ("malicious_filename", "server-generated filename from allowlisted export type", "invalid export type audit", "backend_owner", "none known"),
    ("log_leakage", "structured metadata only; never log body, token, query text, or participant original text", "repository scan and log-key checks", "engineering_security", "platform logs need test-cloud review"),
    ("weak_network_duplicate", "idempotent state transitions and optimistic versions", "duplicate-key/conflict metrics", "backend_owner", "legacy non-critical writes may duplicate"),
    ("unauthorized_deep_link", "server authorization on every sensitive API; Web route guard is only UX", "cross-role browser and API tests", "frontend_backend", "showcase UI may display links but cannot count as formal access evidence"),
]


AI_THREATS = [
    ("prompt_injection", "fixed pre-provider block and fake provider only", "synthetic red-team suite", "ai_safety_owner", "human review required before any real pilot"),
    ("knowledge_poisoning", "published content versions and hashes only", "content governance diff/check", "content_owner", "approval signatures pending"),
    ("cross_user_retrieval", "no participant retrieval tool and no cross-user context", "source inspection plus privacy tests", "backend_owner", "real RAG is prohibited"),
    ("provider_retention", "real provider adapter absent; fake provider only", "configuration hard-fail", "privacy_owner", "contract/region/retention unresolved"),
    ("system_prompt_leakage", "fixed refusal; system prompts and secrets excluded from response context", "synthetic leakage cases", "ai_safety_owner", "model behavior needs external red team"),
    ("tool_abuse", "no write tools, messages, record mutation, tasks, or researcher feedback", "tool-call count must remain zero", "engineering_security", "future tools require new threat review"),
    ("cost_exhaustion", "hourly limit, daily zero budget, timeout and kill switch", "budget/rate events", "operations_owner", "real-provider cost not measured"),
    ("unauthorized_action", "participant AI endpoint absent and AI_QA_ENABLED forced false", "route/config contract checks", "product_security", "release remains blocked"),
]


def _action(item: dict) -> str:
    path = item["path"].lower()
    method = item["method"]
    if "/send" in path or "notification" in path and method == "POST":
        return "send"
    if "export" in path:
        return "export"
    if method == "DELETE" or "delete-my-data" in path:
        return "delete"
    if method == "GET":
        return "read"
    if any(marker in path for marker in ("/transition", "/confirm", "/review", "/approve", "/disable", "/resolve", "/claim")):
        return "update"
    return "create" if method == "POST" else "update"


def _object_type(item: dict) -> str:
    module = str(item.get("module") or "routes.unknown").removeprefix("routes.")
    return module.replace("_routes", "")


def _operation_matrix(contract: dict) -> list[dict]:
    matrix = []
    for item in contract.get("endpoints", []):
        access = item.get("access") or {}
        allowed = list(access.get("roles") or [])
        if access.get("mode") == "public":
            allowed = ["public"]
        denied = list(ROLES) if allowed == ["public"] else [role for role in ROLES if role not in allowed]
        matrix.append(
            {
                "operation_id": item["operation_id"],
                "method": item["method"],
                "path": item["path"],
                "object_type": _object_type(item),
                "action": _action(item),
                "object_scope": item.get("object_scope") or "unspecified",
                "allowed_roles": allowed,
                "denied_roles": denied,
                "legacy_admin_token": bool(access.get("legacy_admin_token")),
                "showcase_read_bypass": bool(access.get("showcase_read_bypass")),
                "idempotency": (item.get("request") or {}).get("idempotency") or {},
            }
        )
    return matrix


def _threat_rows(rows: list[tuple[str, str, str, str, str]]) -> list[dict]:
    return [
        {"id": key, "mitigation": mitigation, "detection": detection, "owner": owner, "residual_risk": residual}
        for key, mitigation, detection, owner, residual in rows
    ]


def build_registry() -> dict:
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    matrix = _operation_matrix(contract)
    operation_ids = [item["operation_id"] for item in matrix]
    if len(operation_ids) != len(set(operation_ids)):
        raise RuntimeError("machine API contract contains duplicate operation_id values")
    bypass = [item for item in matrix if item["showcase_read_bypass"]]
    return {
        "schema": "safehome.security_privacy_abuse_registry.v1",
        "version": "2026-07-20-t31-security-v1",
        "status": "engineering_controls_ready_formal_acceptance_blocked",
        "generated_from_contract_version": contract.get("version"),
        "matrix_source": "shared/contracts/api-contract.json",
        "persisted_matrix_is_authoritative": False,
        "asset_inventory": [
            {
                "asset_id": asset_id,
                "location": location,
                "sensitivity": sensitivity,
                "processor": processor,
                "authorization_basis": basis,
                "deletion_or_withdrawal": deletion,
            }
            for asset_id, location, sensitivity, processor, basis, deletion in ASSETS
        ],
        "authorization_matrix": matrix,
        "authorization_summary": {
            "operation_count": len(matrix),
            "showcase_bypass_operation_count": len(bypass),
            "formal_permission_acceptance_passed": False,
            "reason": "临时展示越权按负责人要求保留，不能作为正式权限验收证据。",
        },
        "web_miniprogram_threats": _threat_rows(WEB_THREATS),
        "ai_threats": _threat_rows(AI_THREATS),
        "identity_controls": {
            "token_lifetime_seconds": 604800,
            "server_side_account_status_check": True,
            "auth_epoch_rotation": True,
            "account_disable_revokes_existing_tokens": True,
            "sensitive_access_audit_required": True,
        },
        "privacy_deletion_proof": {
            "allowlisted_transactional_deletion": True,
            "post_delete_zero_count_verification": True,
            "withdrawal_blocks_new_export_offline_ai": True,
            "audit_and_tombstone_minimized": True,
            "backup_erasure_sla": "human_policy_pending",
        },
        "temporary_showcase_exception": {
            "enabled": True,
            "risk_id": "T31-F07-showcase-overpermission",
            "scope": [item["operation_id"] for item in bypass],
            "stop_condition": "正式权限验收、真实治疗性评估、试点发布或生产发布前必须停用并重跑允许/拒绝矩阵。",
            "accepted_for_formal_permission_testing": False,
        },
        "automated_scans": [
            "tracked_secret_pattern_scan",
            "dependency_pin_inventory",
            "container_non_root_check",
            "cors_production_config_check",
            "default_secret_production_guard_check",
            "sensitive_logging_source_check",
            "api_security_header_check",
        ],
        "external_gates": [
            "dependency advisory database/network scan",
            "test-cloud platform log review",
            "CloudBase gateway identity-header verification",
            "real-device deep-link and token-loss tests",
            "privacy/ethics/security owner signatures",
            "backup retention and erasure policy approval",
            "production release approval",
        ],
    }


def _validate_persisted_governance_snapshot(live: dict) -> None:
    if not OUTPUT_PATH.exists():
        raise SystemExit("security governance snapshot is missing")
    persisted = json.loads(OUTPUT_PATH.read_text(encoding="utf-8"))
    if persisted.get("schema") != live["schema"]:
        raise SystemExit("security governance snapshot schema mismatch")
    if persisted.get("status") != live["status"]:
        raise SystemExit("security governance snapshot status mismatch")
    persisted_assets = {item.get("asset_id") for item in persisted.get("asset_inventory", [])}
    required_assets = {item.get("asset_id") for item in live.get("asset_inventory", [])}
    if not required_assets.issubset(persisted_assets):
        raise SystemExit("security governance snapshot is missing required assets")
    persisted_threats = {item.get("id") for item in persisted.get("web_miniprogram_threats", [])}
    persisted_threats |= {item.get("id") for item in persisted.get("ai_threats", [])}
    required_threats = {item.get("id") for item in live.get("web_miniprogram_threats", [])}
    required_threats |= {item.get("id") for item in live.get("ai_threats", [])}
    if not required_threats.issubset(persisted_threats):
        raise SystemExit("security governance snapshot is missing required threat IDs")
    if (persisted.get("temporary_showcase_exception") or {}).get("enabled") is not True:
        raise SystemExit("showcase exception truth must remain explicit in the governance snapshot")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    payload = build_registry()
    rendered = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    if args.check:
        _validate_persisted_governance_snapshot(payload)
        digest = hashlib.sha256(rendered.encode("utf-8")).hexdigest()
        print(
            f"security live-contract check passed: {len(payload['authorization_matrix'])} operations; "
            f"sha256={digest[:16]}; persisted matrix treated as governance snapshot"
        )
        return 0
    OUTPUT_PATH.write_text(rendered, encoding="utf-8")
    print(f"wrote {OUTPUT_PATH}: {len(payload['authorization_matrix'])} operations")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
