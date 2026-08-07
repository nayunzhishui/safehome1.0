"""Audit SafeHome modular-monolith runtime boundaries.

The audit freezes known historical compatibility debt but fails new
Task-numbered runtime modules and new runtime dependencies on tests/scripts.
It is intentionally small and does not create another runtime governance layer.
"""

from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
POLICY_PATH = ROOT / "config" / "runtime_architecture.json"
RUNTIME_DIRS = (ROOT / "backend" / "routes", ROOT / "backend" / "services")
TASK_FILE = re.compile(r"^task\d+[_a-zA-Z0-9]*\.py$")
FORBIDDEN_IMPORTS = (
    re.compile(r"^\s*from\s+(?:backend\.)?tests(?:\.|\s)", re.MULTILINE),
    re.compile(r"^\s*import\s+(?:backend\.)?tests(?:\.|\s|$)", re.MULTILINE),
    re.compile(r"^\s*from\s+(?:backend\.)?scripts(?:\.|\s)", re.MULTILINE),
    re.compile(r"^\s*import\s+(?:backend\.)?scripts(?:\.|\s|$)", re.MULTILINE),
)


def audit() -> dict:
    policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    rules = policy["runtime_rules"]
    legacy_task_allowlist = set(rules.get("legacy_task_runtime_allowlist") or [])
    legacy_script_import_allowlist = set(rules.get("legacy_runtime_script_import_allowlist") or [])
    violations: list[dict] = []
    warnings: list[dict] = []

    for directory in RUNTIME_DIRS:
        for path in sorted(directory.glob("*.py")):
            relative = path.relative_to(ROOT).as_posix()
            text = path.read_text(encoding="utf-8")
            if TASK_FILE.match(path.name) and relative not in legacy_task_allowlist:
                violations.append(
                    {
                        "path": relative,
                        "rule": "no_new_task_numbered_runtime_modules",
                        "message": "Task 编号只能留在测试/脚本/文档/迁移元数据或冻结兼容层，不能成为新的运行时领域名。",
                    }
                )

            imports_forbidden_runtime_layer = any(pattern.search(text) for pattern in FORBIDDEN_IMPORTS)
            if imports_forbidden_runtime_layer:
                if relative in legacy_script_import_allowlist:
                    warnings.append(
                        {
                            "path": relative,
                            "rule": "legacy_runtime_script_import",
                            "message": "这是冻结的历史依赖，只允许迁出，不允许新增同类依赖。",
                        }
                    )
                else:
                    violations.append(
                        {
                            "path": relative,
                            "rule": "runtime_must_not_import_tests_or_scripts",
                            "message": "新的运行时代码不能依赖测试或迁移/审计脚本。",
                        }
                    )

            line_count = text.count("\n") + 1
            if line_count > 1200:
                warnings.append(
                    {
                        "path": relative,
                        "rule": "large_runtime_module",
                        "line_count": line_count,
                        "message": "模块超过1200行，应在后续相关改动时按领域拆分；历史大模块暂不作为阻断项。",
                    }
                )

    for relative in sorted(legacy_task_allowlist):
        if not (ROOT / relative).exists():
            warnings.append(
                {
                    "path": relative,
                    "rule": "legacy_allowlist_cleanup_due",
                    "message": "历史兼容文件已不存在，可以从 allowlist 删除。",
                }
            )

    required = [
        ROOT / "backend" / "services" / "computation_contract_service.py",
        ROOT / "content" / "computation_contract.json",
    ]
    for path in required:
        if not path.exists():
            violations.append(
                {
                    "path": path.relative_to(ROOT).as_posix(),
                    "rule": "generic_domain_runtime_required",
                    "message": "计算契约必须使用通用领域命名实现。",
                }
            )

    return {
        "ok": not violations,
        "policy_version": policy["version"],
        "architecture_style": policy["architecture_style"],
        "violations": violations,
        "warnings": warnings,
    }


def main() -> int:
    result = audit()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
