#!/usr/bin/env python3
"""Static, redacted engineering audit for Task36 F11."""

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
    models = _read("backend/models.py")
    login_js = _read("apps/miniprogram/pages/login/index.js")
    login_wxml = _read("apps/miniprogram/pages/login/index.wxml")
    api_js = _read("apps/miniprogram/services/api.js")
    web_login = _read("apps/web/src/pages/LoginPage.tsx")
    users_table = models.split("CREATE TABLE IF NOT EXISTS users (", 1)[1].split(");", 1)[0]

    checks = {
        "privacy_minimization": _check(
            "phone_hash TEXT" in users_table
            and "phone_verified_at TEXT" in users_table
            and "phone_source TEXT" in users_table
            and "phone_number" not in users_table
            and "raw_phone" not in users_table
            and "phone_masked" in auth_route
            and "_phone_hash(phone_number)" in auth_route,
            ["backend/models.py", "backend/routes/auth.py"],
        ),
        "account_conflict": _check(
            "phone_row is not None and openid_row is not None" in auth_route
            and '"phone_account_conflict"' in auth_route
            and '"account_inactive"' in auth_route,
            ["backend/routes/auth.py", "backend/tests/test_auth_route.py"],
        ),
        "capability_gating": _check(
            "phoneAvailable: true" in login_js
            and "this.setData({ capabilityMessage, wechatAvailable, phoneAvailable })" in login_js
            and 'wx:if="{{phoneAvailable}}"' in login_wxml
            and "手机号快捷登录（暂不可用）" in login_wxml,
            [
                "apps/miniprogram/pages/login/index.js",
                "apps/miniprogram/pages/login/index.wxml",
            ],
        ),
        "authorization_recovery": _check(
            'open-type="getPhoneNumber"' in login_wxml
            and "detailMessage.includes(\"deny\")" in login_js
            and "detailMessage.includes(\"cancel\")" in login_js
            and "api.login({ username, password })" in login_js
            and "wechat_phone_exchange_failed" in api_js
            and "phone_account_conflict" in api_js,
            [
                "apps/miniprogram/pages/login/index.js",
                "apps/miniprogram/pages/login/index.wxml",
                "apps/miniprogram/services/api.js",
            ],
        ),
        "web_boundary": _check(
            "手机号快捷登录仅在微信小程序内发起" in web_login
            and "网页端不会申请或读取手机号" in web_login,
            ["apps/web/src/pages/LoginPage.tsx"],
        ),
    }
    passed = all(item["passed"] for item in checks.values())
    return {
        "schema": "safehome.task36.phone_login_audit.v1",
        "task": "T36-F11",
        "status": "passed" if passed else "failed",
        "engineering_complete": passed,
        "release_approved": False,
        "production_mutations_executed": False,
        "checks": checks,
        "external_gates_pending": [
            "wechat_phone_qualification",
            "wechat_privacy_guideline_approval",
            "cloudbase_token_or_secret_configuration",
            "cloudbase_release",
            "wechat_devtools_authorize_deny_expired",
            "android_ios_real_device",
        ],
    }


def main() -> int:
    report = build_report()
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    sys.exit(main())
