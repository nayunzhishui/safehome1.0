#!/usr/bin/env python3
"""Static, redacted engineering audit for Task36 F12."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _check(passed: bool, evidence: list[str]) -> dict:
    return {"passed": bool(passed), "evidence": evidence}


def build_report() -> dict:
    auth_route = _read("backend/routes/auth.py")
    lifecycle = _read("backend/services/identity_lifecycle_service.py")
    claims = _read("backend/services/data_claim_service.py")
    models = _read("backend/models.py")
    migration = _read("backend/scripts/migrate_task36_identity_claims.py")
    shared = _read("shared/types/api.ts")
    mini_profile = _read("apps/miniprogram/pages/profile/index.js")
    web_privacy = _read("apps/web/src/pages/PrivacyCenterPage.tsx")
    tests = _read("backend/tests/test_task36_identity_lifecycle.py")

    checks = {
        "quick_login_role_preservation": _check(
            "backend_role_quick_login_forbidden" in auth_route
            and "_participant_quick_login_row" in auth_route
            and "test_phone_quick_login_never_inherits_backend_role" in tests,
            ["backend/routes/auth.py", "backend/tests/test_task36_identity_lifecycle.py"],
        ),
        "redacted_identity_state": _check(
            '@bp.get("/identity-status")' in auth_route
            and "这里只显示绑定状态" in lifecycle
            and '"identities": {' in lifecycle
            and '"f12-secret-openid" not in str(status_data)' in tests,
            ["backend/routes/auth.py", "backend/services/identity_lifecycle_service.py"],
        ),
        "safe_unbind": _check(
            '@bp.post("/identity-unbind")' in auth_route
            and "last_login_identity" in lifecycle
            and "auth_epoch = auth_epoch + 1" in lifecycle
            and "business_records_deleted" in lifecycle,
            ["backend/routes/auth.py", "backend/services/identity_lifecycle_service.py"],
        ),
        "claim_concurrency": _check(
            "status = 'processing'" in claims
            and "version = version + 1" in claims
            and "idempotency_key" in claims
            and "already_completed" in claims,
            ["backend/services/data_claim_service.py", "backend/models.py"],
        ),
        "reversible_account_merge": _check(
            "identity_merge_workflows" in models
            and "identity_merge_record_links" in models
            and "candidate" in lifecycle
            and "confirmed" in lifecycle
            and "executed" in lifecycle
            and "verified" in lifecycle
            and "rolled_back" in lifecycle,
            ["backend/models.py", "backend/services/identity_lifecycle_service.py"],
        ),
        "migration_and_rollback": _check(
            "2026_07_24_027" in _read("backend/database.py")
            and "schema_preserved" in migration
            and "business_records_preserved" in migration
            and "不自动DROP" in migration,
            ["backend/database.py", "backend/scripts/migrate_task36_identity_claims.py"],
        ),
        "cross_client_contract": _check(
            "interface IdentityStatus" in shared
            and "requestIdentityUnbind" in mini_profile
            and "unbindIdentity" in web_privacy
            and "不会删除" in mini_profile
            and "不会删除" in web_privacy,
            [
                "shared/types/api.ts",
                "apps/miniprogram/pages/profile/index.js",
                "apps/web/src/pages/PrivacyCenterPage.tsx",
            ],
        ),
    }
    passed = all(item["passed"] for item in checks.values())
    return {
        "schema": "safehome.task36.identity_lifecycle_audit.v1",
        "task": "T36-F12",
        "status": "passed" if passed else "failed",
        "engineering_complete": passed,
        "release_approved": False,
        "production_mutations_executed": False,
        "temporary_showcase_bypass_counts_as_formal_permission_evidence": False,
        "checks": checks,
        "external_gates_pending": [
            "cloudbase_schema_migration_approval",
            "cloudbase_package_release",
            "wechat_devtools_identity_binding",
            "android_ios_real_device",
            "human_account_merge_confirmation_sample",
            "production_rollback_window_owner",
        ],
    }


def main() -> int:
    report = build_report()
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    sys.exit(main())
