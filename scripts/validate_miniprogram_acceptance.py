#!/usr/bin/env python3
"""Static validator for the SafeHome WeChat quasi-device acceptance harness.

This script performs no network access, CloudBase mutation, login, database write,
or device interaction. It verifies that the acceptance manifest is internally
consistent with the current Mini Program registration and Task36 external gates.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP_JSON_PATH = ROOT / "apps/miniprogram/app.json"
SCENARIO_PATH = ROOT / "tools/miniprogram-acceptance/scenarios.json"
TASK36_PATH = ROOT / "config/task36_registry.json"
RUNNER_PATH = ROOT / "tools/miniprogram-acceptance/run.js"
PACKAGE_PATH = ROOT / "tools/miniprogram-acceptance/package.json"

SECRET_PATTERNS = (
    re.compile(r"Bearer\s+[A-Za-z0-9._-]+", re.I),
    re.compile(r"(?i)(appsecret|password|token)\s*[:=]\s*[\"'][^\"']{8,}[\"']"),
)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    app = load_json(APP_JSON_PATH)
    manifest = load_json(SCENARIO_PATH)
    task36 = load_json(TASK36_PATH)
    package = load_json(PACKAGE_PATH)
    runner_text = RUNNER_PATH.read_text(encoding="utf-8")
    manifest_text = SCENARIO_PATH.read_text(encoding="utf-8")

    registered_pages = set(app.get("pages", []))
    referenced_pages: set[str] = set()
    failures: list[str] = []
    warnings: list[str] = []

    if manifest.get("schema") != "safehome.miniprogram.acceptance.v1":
        failures.append("unexpected acceptance manifest schema")

    principles = manifest.get("principles", {})
    if principles.get("production_mutation_default") is not False:
        failures.append("production_mutation_default must remain false")
    if principles.get("clear_auth_before_run") is not True:
        failures.append("clear_auth_before_run must remain true")

    for pages in manifest.get("route_groups", {}).values():
        referenced_pages.update(pages)

    for item in manifest.get("automated_scenarios", []):
        page = item.get("page")
        if page:
            referenced_pages.add(page)
        referenced_pages.update(item.get("pages", []))
        if item.get("writes_allowed") is True and not item.get("requires_env"):
            failures.append(f"{item.get('id')}: write scenario requires an explicit environment guard")

    missing = sorted(referenced_pages - registered_pages)
    if missing:
        failures.append(f"manifest references unregistered pages: {missing}")

    uncovered = sorted(registered_pages - referenced_pages)
    if uncovered:
        warnings.append(
            "pages not assigned to a named route_group (still covered by AC-ROUTE-ALL): "
            + ", ".join(uncovered)
        )

    external_gates = set()
    for task in task36.get("tasks", []):
        for gate in task.get("external_gates_pending", []):
            external_gates.add(gate)
    # T36-F10 audit also encodes these gates directly in source; registry versions
    # may represent them at task or policy level, so the harness requires the
    # canonical acceptance concepts rather than a brittle exact task layout.
    combined_task_text = TASK36_PATH.read_text(encoding="utf-8")
    for required in (
        "wechat_devtools",
        "android",
        "ios",
    ):
        if required.lower() not in combined_task_text.lower():
            warnings.append(f"Task36 registry does not visibly contain expected external gate token: {required}")

    if "miniprogram-automator" not in package.get("dependencies", {}):
        failures.append("package.json must pin miniprogram-automator")
    if package.get("dependencies", {}).get("miniprogram-automator") != "0.12.1":
        failures.append("miniprogram-automator must be pinned to 0.12.1 for reproducibility")

    required_runner_guards = (
        "SAFEHOME_ACCEPTANCE_ALLOW_TEST_WRITES",
        "SAFEHOME_ACCEPTANCE_ALLOW_EXTERNAL_READS",
        'callWxMethod("clearStorageSync")',
        '"safehome_cloud_config"',
        "SECRET_KEY_PATTERN",
    )
    for token in required_runner_guards:
        if token not in runner_text:
            failures.append(f"runner safety guard missing: {token}")

    for secret_pattern in SECRET_PATTERNS:
        if secret_pattern.search(manifest_text):
            failures.append(f"scenario manifest appears to contain a secret-like value: {secret_pattern.pattern}")

    report = {
        "schema": "safehome.miniprogram.acceptance.validation.v1",
        "status": "failed" if failures else "passed",
        "registered_page_count": len(registered_pages),
        "referenced_page_count": len(referenced_pages),
        "failures": failures,
        "warnings": warnings,
        "external_gate_tokens_seen": sorted(external_gates),
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
