"""Synchronize API-derived governance coverage without weakening validation.

This utility treats `shared/contracts/api-contract.json` as the machine source of
truth for endpoint identity/access metadata. It only:

1. adds/refreshes one security authorization-matrix row per contract endpoint;
2. preserves existing hand-authored security rows when their endpoint still exists,
   while refreshing machine-derived fields that must match the contract;
3. adds currently-uncovered endpoints to one explicitly named operations
   capability for this security-convergence change;
4. never marks production release approved.

Run after `backend/scripts/build_api_contract.py`, then run
`backend/scripts/validate_content.py`.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = ROOT / "shared" / "contracts" / "api-contract.json"
SECURITY_PATH = ROOT / "content" / "security_privacy_abuse_registry.json"
OPERATIONS_PATH = ROOT / "content" / "operations_capability_registry.json"

FORMAL_ROLES = ("parent", "student", "researcher", "supervisor", "admin")


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def dump(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def operation_action(endpoint: dict) -> str:
    method = str(endpoint.get("method") or "GET").upper()
    path = str(endpoint.get("path") or "").lower()
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


def object_type(endpoint: dict) -> str:
    module = str(endpoint.get("module") or "routes.unknown").removeprefix("routes.")
    return module.replace("_routes", "")


def machine_security_fields(endpoint: dict) -> dict:
    access = endpoint.get("access") or {}
    request = endpoint.get("request") or {}
    allowed_roles = list(access.get("roles") or [])
    if access.get("mode") == "public":
        allowed_roles = ["public"]
    denied_roles = list(FORMAL_ROLES) if allowed_roles == ["public"] else [
        role for role in FORMAL_ROLES if role not in allowed_roles
    ]
    return {
        "operation_id": endpoint.get("operation_id"),
        "method": endpoint.get("method"),
        "path": endpoint.get("path"),
        "object_type": object_type(endpoint),
        "action": operation_action(endpoint),
        "object_scope": endpoint.get("object_scope") or "unspecified",
        "allowed_roles": allowed_roles,
        "denied_roles": denied_roles,
        "legacy_admin_token": bool(access.get("legacy_admin_token", False)),
        "showcase_read_bypass": bool(access.get("showcase_read_bypass", False)),
        "idempotency": request.get("idempotency") or {},
    }


def sync_security(contract: dict, registry: dict) -> tuple[dict, list[str]]:
    existing = {
        str(item.get("operation_id")): item
        for item in registry.get("authorization_matrix", [])
        if item.get("operation_id")
    }
    rows: list[dict] = []
    added: list[str] = []
    for endpoint in contract.get("endpoints", []):
        operation_id = str(endpoint.get("operation_id") or "")
        if not operation_id:
            continue
        machine = machine_security_fields(endpoint)
        old = existing.get(operation_id)
        if old is None:
            rows.append(machine)
            added.append(operation_id)
        else:
            # Keep future human annotations, but refresh all contract-derived
            # fields so the authorization matrix cannot contradict runtime.
            rows.append({**old, **machine})
    registry["generated_from_contract_version"] = contract.get("version")
    registry["authorization_matrix"] = rows
    # Preserve formal release block regardless of historical file contents.
    if "production_release_approved" in registry:
        registry["production_release_approved"] = False
    return registry, added


def convergence_capability(operation_ids: list[str], contract_version: str) -> dict:
    return {
        "id": "participant_safety_identity_convergence_20260807",
        "name": "参与者安全、年龄保护、认证收敛与督导增强",
        "intended_use": "覆盖本分支新增的年龄/监护人保护、风险复核身份、人工督导状态和相关机器API；仅用于受控试点与工程验收。",
        "owner": "SafeHome project owner + security/supervision reviewer",
        "dependencies": [
            "shared/contracts/api-contract.json",
            "participant_minor_policy.json",
            "risk_keywords.json",
            "explicit_schema_migrations",
            "named Bearer actor authentication"
        ],
        "data": [
            "age_band (under_14 / 14_or_over only; no DOB)",
            "guardian/child safeguard decisions",
            "risk-review operational metadata",
            "supervision operational metadata and restricted contact"
        ],
        "open_roles": ["parent", "student", "supervisor", "admin"],
        "feature_flags": [
            "MINOR_SAFEGUARDS_ENFORCED",
            "LEGACY_ADMIN_TOKEN_ENABLED (compatibility only)"
        ],
        "version": "2026-08-07-security-convergence-v1",
        "tests": [
            "backend/tests/test_security_convergence_20260807.py",
            "backend/tests/test_risk_service.py",
            ".github/workflows/check.yml"
        ],
        "rollback": "revert branch commits before merge; if already piloted, stop writes, retain audit evidence, then follow explicit_schema_migrations rollback notes and restore prior route adapters",
        "governance_status": "engineering_ready_human_and_pilot_acceptance_required",
        "contract_version": contract_version,
        "operation_ids": sorted(operation_ids),
    }


def sync_operations(contract: dict, registry: dict) -> tuple[dict, list[str]]:
    endpoint_ids = {
        str(item.get("operation_id"))
        for item in contract.get("endpoints", [])
        if item.get("operation_id")
    }
    target_id = "participant_safety_identity_convergence_20260807"
    capabilities = list(registry.get("capabilities", []))
    existing_target = next((item for item in capabilities if item.get("id") == target_id), None)

    covered_elsewhere = {
        str(operation_id)
        for item in capabilities
        if item.get("id") != target_id
        for operation_id in item.get("operation_ids", [])
        if operation_id in endpoint_ids
    }
    target_operations = sorted(endpoint_ids - covered_elsewhere)

    new_target = convergence_capability(target_operations, str(contract.get("version") or "unknown"))
    if existing_target and not target_operations:
        capabilities = [item for item in capabilities if item.get("id") != target_id]
    elif existing_target:
        # Preserve any future human fields while refreshing the required
        # machine coverage and branch-specific evidence fields.
        new_target = {**existing_target, **new_target}
        capabilities = [new_target if item.get("id") == target_id else item for item in capabilities]
    elif target_operations:
        capabilities.append(new_target)

    # Remove stale operation IDs from all other capabilities when the API no
    # longer exists. Duplicate ownership is also removed from the target set by
    # construction. This keeps the union exactly equal to the contract.
    for item in capabilities:
        if item.get("id") == target_id:
            continue
        item["operation_ids"] = [
            op for op in item.get("operation_ids", []) if op in endpoint_ids
        ]

    registry["capabilities"] = capabilities
    registry["production_release_approved"] = False
    registry.pop("api_contract_version", None)
    registry["generated_from_contract_version"] = contract.get("version")
    return registry, target_operations


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="exit non-zero if files would change")
    args = parser.parse_args()

    contract = load(CONTRACT_PATH)
    security_before = load(SECURITY_PATH)
    operations_before = load(OPERATIONS_PATH)
    security_after, security_added = sync_security(contract, json.loads(json.dumps(security_before)))
    operations_after, convergence_ops = sync_operations(contract, json.loads(json.dumps(operations_before)))

    changed = security_after != security_before or operations_after != operations_before
    report = {
        "changed": changed,
        "security_added_operation_ids": security_added,
        "convergence_operation_ids": convergence_ops,
        "contract_endpoint_count": len(contract.get("endpoints", [])),
        "security_matrix_count": len(security_after.get("authorization_matrix", [])),
        "operations_covered_count": len({
            op for item in operations_after.get("capabilities", []) for op in item.get("operation_ids", [])
        }),
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if args.check:
        return 1 if changed else 0
    if changed:
        dump(SECURITY_PATH, security_after)
        dump(OPERATIONS_PATH, operations_after)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
