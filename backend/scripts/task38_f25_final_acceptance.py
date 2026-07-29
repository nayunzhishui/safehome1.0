"""Execute and verify the T38-F25 local engineering acceptance package.

The verifier runs the commands registered for every automatic acceptance
category. It records only command metadata and output hashes; it never trusts a
caller-supplied ``passed`` receipt and never signs an external gate.
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
SECRET_PATTERN = re.compile(
    r"(secret|password|passwd|token|cookie|authorization|appsecret|"
    r"participant_text|raw_text)",
    re.IGNORECASE,
)


class AcceptanceError(ValueError):
    """Raised when final acceptance execution or evidence is incomplete."""


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _source_commit() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return "unavailable"


def _f25_task(registry: dict[str, Any]) -> dict[str, Any]:
    task = next(
        (item for item in registry.get("tasks", []) if item.get("id") == "T38-F25"),
        None,
    )
    if not task or task.get("dependencies") != ["T38-F24"]:
        raise AcceptanceError("T38-F25注册或依赖不正确")
    return task


def _validate_registry(
    policy: dict[str, Any], registry: dict[str, Any]
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    pending = [
        item["id"]
        for item in registry.get("tasks", [])
        if item.get("id") != "T38-F25" and item.get("engineering_complete") is not True
    ]
    if pending:
        raise AcceptanceError(f"前置工程任务未完成：{pending}")
    task = _f25_task(registry)
    categories = task.get("acceptance_categories")
    if not isinstance(categories, list):
        raise AcceptanceError("T38-F25缺少可执行验收类别")
    expected = [
        item["id"]
        for item in policy["automatic_acceptance_categories"]
        if item.get("required") is True
    ]
    if [item.get("id") for item in categories] != expected:
        raise AcceptanceError("可执行验收类别缺失、重复或顺序漂移")
    return task, categories


def _normalize_spec(registry: dict[str, Any], raw: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raise AcceptanceError("验收命令必须是对象")
    command = raw.get("command")
    cwd_value = raw.get("cwd", ".")
    timeout_seconds = raw.get("timeout_seconds", 1800)
    if (
        not isinstance(command, list)
        or not command
        or not all(isinstance(part, str) and part for part in command)
    ):
        raise AcceptanceError("验收命令格式无效")
    if not isinstance(cwd_value, str) or not cwd_value:
        raise AcceptanceError("验收命令cwd无效")
    if not isinstance(timeout_seconds, int) or not 1 <= timeout_seconds <= 3600:
        raise AcceptanceError("验收命令timeout_seconds无效")
    allowed = set(
        registry.get("policy", {}).get(
            "allowed_command_executables",
            ["python", "python.exe", "node", "node.exe", "npm", "npm.cmd"],
        )
    )
    if command[0].lower() not in {item.lower() for item in allowed}:
        raise AcceptanceError(f"验收命令不在允许列表：{command[0]}")
    serialized = " ".join(command)
    forbidden = registry.get("policy", {}).get("forbidden_command_terms", [])
    if SECRET_PATTERN.search(serialized) or any(
        str(term).lower() in serialized.lower() for term in forbidden
    ):
        raise AcceptanceError("验收命令包含敏感或禁止内容")
    cwd = (ROOT / cwd_value).resolve()
    try:
        cwd.relative_to(ROOT.resolve())
    except ValueError as exc:
        raise AcceptanceError("验收命令cwd必须位于项目内") from exc
    return {
        "cwd": cwd_value,
        "command": command,
        "timeout_seconds": timeout_seconds,
    }


def _spec_digest(spec: dict[str, Any]) -> str:
    payload = json.dumps(
        {"cwd": spec["cwd"], "command": spec["command"]},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return _sha256_bytes(payload)


def _execute(spec: dict[str, Any]) -> dict[str, Any]:
    cwd = (ROOT / spec["cwd"]).resolve()
    try:
        completed = subprocess.run(
            spec["command"],
            cwd=cwd,
            capture_output=True,
            check=False,
            timeout=spec["timeout_seconds"],
        )
    except subprocess.TimeoutExpired as exc:
        raise AcceptanceError(
            f"验收命令超时：{' '.join(spec['command'][:3])}"
        ) from exc
    outcome = {
        "command": spec["command"],
        "cwd": spec["cwd"],
        "command_sha256": _spec_digest(spec),
        "returncode": completed.returncode,
        "stdout_bytes": len(completed.stdout),
        "stdout_sha256": _sha256_bytes(completed.stdout),
        "stderr_bytes": len(completed.stderr),
        "stderr_sha256": _sha256_bytes(completed.stderr),
    }
    if completed.returncode != 0:
        raise AcceptanceError(
            f"验收命令失败({completed.returncode})：{' '.join(spec['command'][:3])}"
        )
    return outcome


def _collect_artifacts(categories: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[str]]:
    relative_paths = sorted(
        {
            "config/task37_38_registry.json",
            "content/task37_38_final_acceptance_policy.json",
            *(
                relative
                for item in categories
                for relative in item.get("artifact_paths", [])
            ),
        }
    )
    artifacts: list[dict[str, Any]] = []
    missing: list[str] = []
    for relative in relative_paths:
        if not isinstance(relative, str) or ".." in Path(relative).parts:
            raise AcceptanceError(f"证据路径必须是安全相对路径：{relative}")
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
    return artifacts, missing


def plan(
    *,
    policy_path: Path = POLICY,
    registry_path: Path = REGISTRY,
) -> dict[str, Any]:
    policy = _load(policy_path)
    registry = _load(registry_path)
    _, categories = _validate_registry(policy, registry)
    return {
        "schema": "safehome.tasks37-38.final-acceptance-evidence.v2",
        "action": "plan",
        "ok": True,
        "automatic_categories": [item["id"] for item in categories],
        "commands_to_execute": sum(len(item.get("commands", [])) for item in categories),
        "external_gates": [
            {"id": item["id"], "status": "external_gate_pending"}
            for item in policy["external_gates"]
        ],
        "production_mutation_executed": False,
        "production_release_approved": False,
    }


def verify(
    *,
    policy_path: Path = POLICY,
    registry_path: Path = REGISTRY,
) -> dict[str, Any]:
    policy_sha256 = _sha256(policy_path)
    registry_sha256 = _sha256(registry_path)
    policy = _load(policy_path)
    registry = _load(registry_path)
    _, categories = _validate_registry(policy, registry)
    outcomes_by_digest: dict[str, dict[str, Any]] = {}
    category_results: list[dict[str, Any]] = []
    for category in categories:
        raw_commands = category.get("commands")
        if not isinstance(raw_commands, list) or not raw_commands:
            raise AcceptanceError(f"验收类别缺少命令：{category.get('id')}")
        command_digests: list[str] = []
        for raw in raw_commands:
            spec = _normalize_spec(registry, raw)
            digest = _spec_digest(spec)
            if digest not in outcomes_by_digest:
                outcomes_by_digest[digest] = _execute(spec)
            command_digests.append(digest)
        category_results.append(
            {
                "id": category["id"],
                "status": "passed",
                "command_sha256": command_digests,
                "artifact_paths": sorted(category.get("artifact_paths", [])),
            }
        )
    if _sha256(policy_path) != policy_sha256 or _sha256(registry_path) != registry_sha256:
        raise AcceptanceError("验收期间政策或注册表发生变化，请重新执行")
    artifacts, missing = _collect_artifacts(categories)
    canonical = json.dumps(artifacts, sort_keys=True, separators=(",", ":"))
    result = {
        "schema": "safehome.tasks37-38.final-acceptance-evidence.v2",
        "action": "verify",
        "task_id": "T38-F25",
        "source_commit": _source_commit(),
        "automatic_acceptance": category_results,
        "automatic_acceptance_complete": not missing,
        "executed_commands": list(outcomes_by_digest.values()),
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
    result["ok"] = result["automatic_acceptance_complete"]
    return result


def rollback_plan() -> dict[str, Any]:
    return {
        "schema": "safehome.tasks37-38.final-acceptance-evidence.v2",
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
    parser.add_argument("action", choices=["plan", "verify", "rollback-plan"])
    parser.add_argument("--policy", type=Path, default=POLICY)
    parser.add_argument("--registry", type=Path, default=REGISTRY)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    if args.action == "plan":
        result = plan(policy_path=args.policy, registry_path=args.registry)
    elif args.action == "verify":
        result = verify(policy_path=args.policy, registry_path=args.registry)
    else:
        result = rollback_plan()
    payload = json.dumps(result, ensure_ascii=False, indent=2)
    if args.action == "verify":
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload + "\n", encoding="utf-8")
    print(payload)
    return 0 if result.get("ok", True) else 1


if __name__ == "__main__":
    raise SystemExit(main())
