#!/usr/bin/env python3
"""Static, redacted engineering audit for Task36 F10.

The audit intentionally performs no CloudBase mutation, login attempt, secret
read, production probe, or device acceptance. External gates remain explicit.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_APP_ID = "wxd548597e78862269"
EXPECTED_ENVIRONMENT = "prod-d3gl35otiaa7c8d24"
EXPECTED_SERVICE = "flask-gh3l"


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _check(passed: bool, evidence: list[str]) -> dict:
    return {"passed": bool(passed), "evidence": evidence}


def build_report() -> dict:
    project = json.loads(_read("apps/miniprogram/project.config.json"))
    cloud_config = _read("apps/miniprogram/services/cloudConfig.js")
    auth_route = _read("backend/routes/auth.py")
    login_js = _read("apps/miniprogram/pages/login/index.js")
    login_wxml = _read("apps/miniprogram/pages/login/index.wxml")
    registry = json.loads(_read("config/task36_registry.json"))

    flags = {item["id"]: item for item in registry["baseline"]["feature_flags"]}
    trust_flag = flags["trust_cloudbase_identity_headers"]
    forbidden = registry["policy"]["forbidden_command_terms"]

    checks = {
        "project_identity": _check(
            project.get("appid") == EXPECTED_APP_ID
            and EXPECTED_ENVIRONMENT in cloud_config
            and EXPECTED_SERVICE in cloud_config,
            [
                "apps/miniprogram/project.config.json",
                "apps/miniprogram/services/cloudConfig.js",
            ],
        ),
        "explicit_header_trust": _check(
            trust_flag.get("frozen_value") is False
            and trust_flag.get("formal_permission_evidence") is False
            and "TRUST_CLOUDBASE_IDENTITY_HEADERS=1" in forbidden
            and 'current_app.config.get("TRUST_CLOUDBASE_IDENTITY_HEADERS", False)' in auth_route
            and '_CLOUDBASE_MINIPROGRAM_SOURCES = {"wx_devtools", "wx_client"}' in auth_route,
            ["config/task36_registry.json", "backend/routes/auth.py"],
        ),
        "capability_contract": _check(
            '@bp.get("/capabilities")' in auth_route
            and '"cloudbase_identity"' in auth_route
            and '"jscode2session"' in auth_route
            and '"not_configured"' in auth_route
            and "WECHAT_APPID" in auth_route
            and "WECHAT_SECRET" in auth_route,
            ["backend/routes/auth.py"],
        ),
        "password_fallback": _check(
            "api.login({ username, password })" in login_js
            and "账号密码" in login_wxml
            and "api.getAuthCapabilities()" in login_js,
            [
                "apps/miniprogram/pages/login/index.js",
                "apps/miniprogram/pages/login/index.wxml",
            ],
        ),
        "safe_error_mapping": _check(
            "wechat_network_unavailable" in auth_route
            and "wechat_upstream_http_error" in auth_route
            and "wechat_upstream_invalid_response" in auth_route
            and "never log URLs, codes, AppSecret or response bodies" in auth_route,
            ["backend/routes/auth.py"],
        ),
    }
    passed = all(item["passed"] for item in checks.values())
    return {
        "schema": "safehome.task36.wechat_login_audit.v1",
        "task": "T36-F10",
        "status": "passed" if passed else "failed",
        "engineering_complete": passed,
        "release_approved": False,
        "production_mutations_executed": False,
        "checks": checks,
        "external_gates_pending": [
            "cloudbase_security_package_release",
            "public_header_spoof_negative_probe",
            "cloudbase_egress_or_vpc_nat",
            "wechat_devtools_first_and_repeat_login",
            "android_ios_real_device",
            "disabled_account_and_token_expiry",
        ],
    }


def main() -> int:
    report = build_report()
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    sys.exit(main())
