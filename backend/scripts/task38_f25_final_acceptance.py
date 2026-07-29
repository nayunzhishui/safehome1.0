"""Build and verify the T38-F25 local engineering acceptance evidence package.

This command only consumes a sanitized local test receipt. It never executes a
production migration, signs an external gate, or stores participant text.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
POLICY = ROOT / "content" / "task37_38_final_acceptance_policy.json"
REGISTRY = ROOT / "config" / "task37_38_registry.json"
DEFAULT_OUTPUT = ROOT / ".codex_tmp" / "task38_f25_final_acceptance_evidence.json"
SAFE_RESULT_KEYS = {"id", "status", "command", "summary", "artifact_paths"}
SECRET_KEY_PATTERN = re.compile(
    r"(secret|password|passwd|token|cookie|authorization|appsecret|participant_text|raw_text)",
    re.IGNORECASE,
)
ABSOLUTE_PATH_PATTERN = re.compile(r"(?:[A-Za-z]:[\\/]|/Users/|/home/)")
SAFE_SUMMARY_PATTERN = re.compile(r"^[A-Za-z0-9 .,_/%()+-]{1,200}$")


class AcceptanceError(ValueError):
    """Raised when final acceptance evidence is incomplete or unsafe."""


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _source_commit() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return "unavailable"


def _validate_registry(registry: dict[str, Any]) -> None:
    pending = [
        item["id"]
        for item in registry.get("tasks", [])
        if item.get("id") != "T38-F25" and item.get("engineering_complete") is not True
    ]
    if pending:
        raise AcceptanceError(f"前置工程任务未完成：{pending}")
    f25 = next(
        (item for item in registry.get("tasks", []) if item.get("id") == "T38-F25"),
        None,
    )
    if not f25 or f25.get("dependencies") != ["T38-F24"]:
        raise AcceptanceError("T38-F25注册或依赖不正确")


def _validate_receipt(policy: dict[str, Any], receipt: dict[str, Any]) -> list[dict[str, Any]]:
    if receipt.get("schema") != "safehome.tasks37-38.acceptance-receipt.v1":
        raise AcceptanceError("验收回执schema不兼容")
    results = receipt.get("results")
    if not isinstance(results, list):
        raise AcceptanceError("验收回执缺少results")
    expected = [
        item["id"]
        for item in policy["automatic_acceptance_categories"]
        if item.get("required") is True
    ]
    ids = [item.get("id") for item in results]
    if ids != expected:
        raise AcceptanceError("验收回执类别缺失、重复或顺序漂移")
    for item in results:
        unknown = set(item) - SAFE_RESULT_KEYS
        if unknown:
            raise AcceptanceError(f"验收回执包含未允许字段：{sorted(unknown)}")
        if item.get("status") != "passed":
            raise AcceptanceError(f"自动验收未通过：{item.get('id')}")
        command = item.get("command")
        if not isinstance(command, list) or not command or not all(
            isinstance(part, str) and part for part in command
        ):
            raise AcceptanceError(f"验收命令无效：{item.get('id')}")
        artifact_paths = item.get("artifact_paths", [])
        if not isinstance(artifact_paths, list):
            raise AcceptanceError(f"证据路径无效：{item.get('id')}")
        summary = item.get("summary")
        if not isinstance(summary, str) or not SAFE_SUMMARY_PATTERN.fullmatch(summary):
            raise AcceptanceError(f"验收摘要必须是短且脱敏的机器说明：{item.get('id')}")
        for relative in artifact_paths:
            if (
                not isinstance(relative, str)
                or ABSOLUTE_PATH_PATTERN.search(relative)
                or Path(relative).is_absolute()
                or ".." in Path(relative).parts
            ):
                raise AcceptanceError(f"证据路径必须是安全相对路径：{relative}")
            candidate = (ROOT / relative).resolve()
            try:
                candidate.relative_to(ROOT.resolve())
            except ValueError as exc:
                raise AcceptanceError(f"证据路径越出项目目录：{relative}") from exc
    serialized = json.dumps(receipt, ensure_ascii=False)
    if SECRET_KEY_PATTERN.search(serialized) or ABSOLUTE_PATH_PATTERN.search(serialized):
        raise AcceptanceError("验收回执包含敏感字段或本机绝对路径")
    return results


def plan() -> dict[str, Any]:
    policy = _load(POLICY)
    registry = _load(REGISTRY)
    _validate_registry(registry)
    return {
        "schema": "safehome.tasks37-38.final-acceptance-evidence.v1",
        "action": "plan",
        "ok": True,
        "automatic_categories": [
            item["id"] for item in policy["automatic_acceptance_categories"]
        ],
        "external_gates": [
            {"id": item["id"], "status": "external_gate_pending"}
            for item in policy["external_gates"]
        ],
        "production_mutation_executed": False,
        "production_release_approved": False,
    }


def build(results_file: Path) -> dict[str, Any]:
    policy = _load(POLICY)
    registry = _load(REGISTRY)
    receipt = _load(results_file)
    _validate_registry(registry)
    results = _validate_receipt(policy, receipt)
    artifact_paths = sorted(
        {
            "config/task37_38_registry.json",
            "content/task37_38_final_acceptance_policy.json",
            *(
                relative
                for item in results
                for relative in item.get("artifact_paths", [])
            ),
        }
    )
    artifacts = []
    missing = []
    for relative in artifact_paths:
        path = (ROOT / relative).resolve()
        try:
            path.relative_to(ROOT.resolve())
        except ValueError as exc:
            raise AcceptanceError(f"证据路径越出项目目录：{relative}") from exc
        if not path.is_file():
            missing.append(relative)
            continue
        artifacts.append(
            {
                "path": relative.replace("\\", "/"),
                "sha256": _sha256(path),
                "size_bytes": path.stat().st_size,
            }
        )
    canonical = json.dumps(artifacts, sort_keys=True, separators=(",", ":"))
    result = {
        "schema": "safehome.tasks37-38.final-acceptance-evidence.v1",
        "action": "build",
        "task_id": "T38-F25",
        "source_commit": _source_commit(),
        "automatic_acceptance": results,
        "automatic_acceptance_complete": not missing,
        "artifacts": artifacts,
        "artifact_set_sha256": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
        "missing_artifacts": missing,
        "completion_definitions": policy["completion_definitions"],
        "external_gates": [
            {"id": item["id"], "status": "external_gate_pending"}
            for item in policy["external_gates"]
        ],
        "engineering_complete_is_production_release": False,
        "temporary_showcase_bypass_used_as_evidence": False,
        "production_migration_executed": False,
        "production_restore_executed": False,
        "real_device_acceptance_complete": False,
        "production_release_approved": False,
    }
    result["ok"] = result["automatic_acceptance_complete"] and len(artifacts) == len(
        artifact_paths
    )
    return result


def verify(results_file: Path) -> dict[str, Any]:
    result = build(results_file)
    result["action"] = "verify"
    if any(item["status"] != "external_gate_pending" for item in result["external_gates"]):
        raise AcceptanceError("外部门禁不得由自动验收签署")
    if any(
        result[key] is not False
        for key in (
            "engineering_complete_is_production_release",
            "temporary_showcase_bypass_used_as_evidence",
            "production_migration_executed",
            "production_restore_executed",
            "real_device_acceptance_complete",
            "production_release_approved",
        )
    ):
        raise AcceptanceError("工程证据不得声明生产迁移、真机或发布批准")
    return result


def rollback_plan() -> dict[str, Any]:
    return {
        "schema": "safehome.tasks37-38.final-acceptance-evidence.v1",
        "action": "rollback-plan",
        "ok": True,
        "actions": [
            "discard_unpublished_local_evidence_package",
            "keep_committed_source_and_audit_history",
            "keep_external_gates_pending",
            "do_not_mutate_production",
        ],
        "rollback_executed": False,
        "production_mutation_executed": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["plan", "build", "verify", "rollback-plan"])
    parser.add_argument("--results-file", type=Path)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    if args.action == "plan":
        result = plan()
    elif args.action in {"build", "verify"}:
        if not args.results_file:
            parser.error("--results-file is required for build/verify")
        result = (
            build(args.results_file)
            if args.action == "build"
            else verify(args.results_file)
        )
    else:
        result = rollback_plan()
    payload = json.dumps(result, ensure_ascii=False, indent=2)
    if args.action in {"build", "verify"}:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload + "\n", encoding="utf-8")
    print(payload)
    return 0 if result.get("ok", True) else 1


if __name__ == "__main__":
    raise SystemExit(main())
