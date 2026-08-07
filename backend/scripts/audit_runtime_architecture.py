"""Audit SafeHome modular-monolith runtime boundaries.

This is intentionally small: it prevents new task-numbered runtime modules and
obvious test/migration imports without forcing a risky repository-wide rewrite
of historical Task37 code.
"""

from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
POLICY_PATH = ROOT / "config" / "runtime_architecture.json"
RUNTIME_DIRS = (ROOT / "backend" / "routes", ROOT / "backend" / "services")
TASK_FILE = re.compile(r"^task(\d+)[_a-zA-Z0-9]*\.py$")
FORBIDDEN_IMPORTS = (
    re.compile(r"^\s*from\s+(?:backend\.)?tests(?:\.|\s)", re.MULTILINE),
    re.compile(r"^\s*import\s+(?:backend\.)?tests(?:\.|\s|$)", re.MULTILINE),
    re.compile(r"^\s*from\s+(?:backend\.)?scripts(?:\.|\s)", re.MULTILINE),
    re.compile(r"^\s*import\s+(?:backend\.)?scripts(?:\.|\s|$)", re.MULTILINE),
)


def audit() -> dict:
    policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    max_legacy_task = int(policy["runtime_rules"]["new_task_numbered_runtime_modules_forbidden_after_task"])
    violations: list[dict] = []
    warnings: list[dict] = []

    for directory in RUNTIME_DIRS:
        for path in sorted(directory.glob("*.py")):
            relative = path.relative_to(ROOT).as_posix()
            text = path.read_text(encoding="utf-8")
            match = TASK_FILE.match(path.name)
            if match and int(match.group(1)) > max_legacy_task:
                violations.append(
                    {
                        "path": relative,
                        "rule": "no_new_task_numbered_runtime_modules",
                        "message": "Task 编号只能留在测试/脚本/文档/迁移元数据，不能成为新的运行时领域名。",
                    }
                )
            if any(pattern.search(text) for pattern in FORBIDDEN_IMPORTS):
                violations.append(
                    {
                        "path": relative,
                        "rule": "runtime_must_not_import_tests_or_scripts",
                        "message": "运行时代码不能依赖测试或迁移脚本。",
                    }
                )
            line_count = text.count("\n") + 1
            if line_count > 1200:
                warnings.append(
                    {
                        "path": relative,
                        "rule": "large_runtime_module",
                        "line_count": line_count,
                        "message": "模块超过1200行，应在后续改动时优先按领域拆分；本检查暂不阻断历史模块。",
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
