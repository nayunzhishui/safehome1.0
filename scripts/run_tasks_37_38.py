"""Deterministic and recoverable orchestrator for SafeHome tasks 37 and 38.

The runner verifies registered local engineering slices and records sanitized
checkpoints under ``.codex_tmp``. It never treats simulated agents as human
sign-off and never records secrets or raw participant text.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "config" / "task37_38_registry.json"
STATE_SCHEMA = "safehome.tasks37_38.state.v1"
SNAPSHOT_SCHEMA = "safehome.tasks37_38.snapshot.v1"


class RegistryError(ValueError):
    """Raised when the machine registry or checkpoint is unsafe or invalid."""


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _safe_runtime_path(registry: dict[str, Any], key: str) -> Path:
    target = (ROOT / registry["policy"][key]).resolve()
    runtime_root = (ROOT / ".codex_tmp").resolve()
    try:
        target.relative_to(runtime_root)
    except ValueError as exc:
        raise RegistryError("任务37/38运行产物只能写入.codex_tmp。") from exc
    return target


def state_path(registry: dict[str, Any]) -> Path:
    return _safe_runtime_path(registry, "state_path")


def snapshot_path(registry: dict[str, Any]) -> Path:
    return _safe_runtime_path(registry, "snapshot_path")


def _task_map(registry: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {task["id"]: task for task in registry["tasks"]}


def topological_order(registry: dict[str, Any]) -> list[str]:
    """Return the stable dependency order or reject cycles/missing references."""

    tasks = _task_map(registry)
    expected_order = registry.get("execution_order", [])
    if set(tasks) != set(expected_order) or len(expected_order) != len(tasks):
        raise RegistryError("执行顺序必须与任务集合一一对应。")
    for task in registry["tasks"]:
        missing = set(task.get("dependencies", [])) - set(tasks)
        if missing:
            raise RegistryError(f"{task['id']}依赖不存在：{sorted(missing)}")
        if task["id"] in task.get("dependencies", []):
            raise RegistryError(f"{task['id']}不能依赖自身。")

    remaining = set(tasks)
    completed: set[str] = set()
    result: list[str] = []
    while remaining:
        selected = next(
            (
                task_id
                for task_id in expected_order
                if task_id in remaining
                and set(tasks[task_id].get("dependencies", [])).issubset(completed)
            ),
            None,
        )
        if selected is None:
            raise RegistryError("任务依赖存在环或无法满足的依赖。")
        result.append(selected)
        completed.add(selected)
        remaining.remove(selected)
    return result


def _command_text(command: list[str]) -> str:
    return " ".join(str(item) for item in command)


def _validate_command(registry: dict[str, Any], command: list[str]) -> None:
    if not command or not all(isinstance(item, str) and item for item in command):
        raise RegistryError("验收命令必须是非空字符串数组。")
    executable = Path(command[0]).name.lower()
    allowed = {
        item.lower()
        for item in registry["policy"].get("allowed_command_executables", [])
    }
    if executable not in allowed:
        raise RegistryError(f"验收命令执行器未获允许：{command[0]}")
    normalized = _command_text(command).lower()
    for term in registry["policy"].get("forbidden_command_terms", []):
        if term.lower() in normalized:
            raise RegistryError(f"验收命令包含禁止操作：{term}")


def _validate_registry_policy(registry: dict[str, Any]) -> None:
    policy = registry.get("policy", {})
    required_false = (
        "simulated_agent_may_sign_external_gate",
        "secret_values_may_be_recorded",
        "default_training_consent_allowed",
        "temporary_showcase_bypass_counts_as_formal_permission_evidence",
    )
    if any(policy.get(key) is not False for key in required_false):
        raise RegistryError("模拟签字、敏感值、默认训练同意或展示旁路不得计为正式门禁。")
    if policy.get("dirty_worktree_policy") != "observe_only_never_revert":
        raise RegistryError("dirty工作区必须只观察且不得回退。")
    if policy.get("production_automation_authorized") is not True:
        raise RegistryError("生产自动化授权状态未明确登记。")
    if (
        policy.get(
            "production_automation_requires_backup_restore_canary_kill_switch"
        )
        is not True
    ):
        raise RegistryError("生产自动化必须依赖备份恢复、canary和kill switch。")


def load_registry() -> dict[str, Any]:
    try:
        registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RegistryError("任务37/38注册表缺失或不是有效JSON。") from exc
    if registry.get("schema") != "safehome.tasks37_38.registry.v1":
        raise RegistryError("任务37/38注册表schema不兼容。")
    tasks = registry.get("tasks", [])
    task_ids = [task.get("id") for task in tasks]
    if len(tasks) != 57 or len(set(task_ids)) != 57:
        raise RegistryError("任务37/38注册表必须包含57个唯一子任务。")
    if set(registry.get("scope", [])) != set(task_ids):
        raise RegistryError("注册表scope与任务集合不一致。")
    if [task["id"] for task in tasks] != registry.get("execution_order"):
        raise RegistryError("任务顺序必须与execution_order一致。")
    if topological_order(registry) != registry["execution_order"]:
        raise RegistryError("任务依赖顺序不稳定。")
    _validate_registry_policy(registry)
    for task in tasks:
        for command in task.get("verify_commands", []):
            _validate_command(registry, command)
    return registry


def read_state(registry: dict[str, Any]) -> dict[str, Any]:
    path = state_path(registry)
    if not path.exists():
        return {"schema": STATE_SCHEMA, "runs": {}}
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RegistryError("任务37/38状态文件损坏；请保留后人工复核。") from exc
    if state.get("schema") != STATE_SCHEMA:
        raise RegistryError("任务37/38状态文件schema不兼容。")
    return state


def command_specs(
    task: dict[str, Any], registry: dict[str, Any], full: bool
) -> list[dict[str, Any]]:
    specs = [
        {"cwd": ".", "command": command}
        for command in task.get("verify_commands", [])
    ]
    if full and not task.get("verify_includes_full_acceptance"):
        specs.extend(registry.get("full_acceptance_commands", []))
    for spec in specs:
        _validate_command(registry, spec["command"])
    return specs


def command_digest(specs: list[dict[str, Any]]) -> str:
    normalized = json.dumps(
        specs,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return _sha256_bytes(normalized.encode("utf-8"))


def _sanitized_process_outcome(
    spec: dict[str, Any], completed: subprocess.CompletedProcess[bytes]
) -> dict[str, Any]:
    return {
        "command": spec["command"],
        "cwd": spec.get("cwd", "."),
        "returncode": completed.returncode,
        "stdout_bytes": len(completed.stdout),
        "stdout_sha256": _sha256_bytes(completed.stdout),
        "stderr_bytes": len(completed.stderr),
        "stderr_sha256": _sha256_bytes(completed.stderr),
    }


def run_specs(
    registry: dict[str, Any],
    specs: list[dict[str, Any]],
    *,
    dry_run: bool,
) -> tuple[bool, list[dict[str, Any]]]:
    outcomes: list[dict[str, Any]] = []
    for spec in specs:
        _validate_command(registry, spec["command"])
        cwd = (ROOT / spec.get("cwd", ".")).resolve()
        try:
            cwd.relative_to(ROOT.resolve())
        except ValueError as exc:
            raise RegistryError("验收命令工作目录必须位于项目内。") from exc
        if dry_run:
            outcomes.append(
                {
                    "command": spec["command"],
                    "cwd": spec.get("cwd", "."),
                    "status": "dry_run",
                }
            )
            continue
        completed = subprocess.run(
            spec["command"],
            cwd=cwd,
            capture_output=True,
            check=False,
        )
        outcomes.append(_sanitized_process_outcome(spec, completed))
        if completed.returncode != 0:
            return False, outcomes
    return True, outcomes


def resume_point(
    record: dict[str, Any], specs: list[dict[str, Any]]
) -> tuple[int, list[dict[str, Any]]]:
    if record.get("command_digest") != command_digest(specs):
        raise RegistryError("注册表命令已变化，不能resume；请重新verify。")
    prefix: list[dict[str, Any]] = []
    for index, outcome in enumerate(record.get("outcomes", [])):
        if index >= len(specs) or outcome.get("command") != specs[index]["command"]:
            raise RegistryError("运行记录与当前命令不一致，不能resume。")
        if outcome.get("returncode") != 0:
            return index, prefix
        prefix.append(outcome)
    return len(prefix), prefix


def next_task(registry: dict[str, Any]) -> dict[str, Any] | None:
    tasks = _task_map(registry)
    for task_id in registry["execution_order"]:
        task = tasks[task_id]
        if task.get("engineering_complete"):
            continue
        if all(
            tasks[dependency].get("engineering_complete")
            for dependency in task.get("dependencies", [])
        ):
            return task
    return None


def verify_task(
    registry: dict[str, Any],
    task_id: str,
    *,
    full: bool,
    dry_run: bool,
    start_index: int = 0,
    previous_outcomes: list[dict[str, Any]] | None = None,
) -> int:
    task = _task_map(registry).get(task_id)
    if not task:
        raise RegistryError(f"未知任务：{task_id}")
    specs = command_specs(task, registry, full)
    if not specs:
        raise RegistryError(f"{task_id}尚未登记验收命令。")
    if start_index < 0 or start_index > len(specs):
        raise RegistryError("恢复位置无效。")
    ok, current = run_specs(registry, specs[start_index:], dry_run=dry_run)
    outcomes = list(previous_outcomes or []) + current
    state = read_state(registry)
    state["registry_version"] = registry["version"]
    state["updated_at"] = _utc_now()
    state.setdefault("runs", {})[task_id] = {
        "status": "dry_run" if dry_run else ("passed" if ok else "failed"),
        "full": full,
        "command_digest": command_digest(specs),
        "outcomes": outcomes,
        "production_mutations_executed": False,
        "external_signoffs_executed": False,
        "simulated_signoffs_counted": False,
    }
    _atomic_write_json(state_path(registry), state)
    print(
        json.dumps(
            state["runs"][task_id],
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0 if ok else 1


def _git_output(*args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
        encoding="utf-8",
        errors="replace",
    )
    if completed.returncode != 0:
        raise RegistryError(f"Git只读快照失败：{' '.join(args)}")
    return completed.stdout.strip()


def collect_snapshot(registry: dict[str, Any]) -> dict[str, Any]:
    dirty = [
        line
        for line in _git_output("status", "--short").splitlines()
        if line.strip()
    ]
    foundation_path = ROOT / registry["policy"]["foundation_path"]
    foundation = json.loads(foundation_path.read_text(encoding="utf-8"))
    asset_drift: list[dict[str, Any]] = []
    for asset in foundation["assets"]:
        path = ROOT / asset["path"]
        current_hash = _sha256_bytes(path.read_bytes()) if path.is_file() else None
        asset_drift.append(
            {
                "path": asset["path"],
                "exists": path.is_file(),
                "baseline_sha256": asset["sha256"],
                "current_sha256": current_hash,
                "changed": current_hash != asset["sha256"],
            }
        )
    snapshot = {
        "schema": SNAPSHOT_SCHEMA,
        "registry_version": registry["version"],
        "captured_at": _utc_now(),
        "git": {
            "head": _git_output("rev-parse", "HEAD"),
            "branch": _git_output("branch", "--show-current"),
            "dirty": bool(dirty),
            "dirty_entries": len(dirty),
            "dirty_worktree_policy": "observe_only_never_revert",
        },
        "asset_drift": asset_drift,
        "safety": {
            "raw_participant_text_recorded": False,
            "secret_values_recorded": False,
            "production_mutations_executed": False,
            "external_signoffs_executed": False,
        },
    }
    _atomic_write_json(snapshot_path(registry), snapshot)
    return snapshot


def report(registry: dict[str, Any]) -> dict[str, Any]:
    evidence_audit = []
    for task in registry["tasks"]:
        evidence_audit.append(
            {
                "task": task["id"],
                "missing_evidence": [
                    path
                    for path in task.get("evidence", [])
                    if not (ROOT / path).exists()
                ],
            }
        )
    return {
        "schema": "safehome.tasks37_38.report.v1",
        "registry_version": registry["version"],
        "tasks_total": len(registry["tasks"]),
        "tasks_engineering_complete": sum(
            bool(task.get("engineering_complete")) for task in registry["tasks"]
        ),
        "next_automatable_task": (next_task(registry) or {}).get("id"),
        "human_external_signoff_complete": False,
        "production_release_approved": False,
        "simulated_agents_count_as_human_signoff": False,
        "participant_entry": registry["owner_decisions"]["participant_ai_entry"],
        "evidence_audit": evidence_audit,
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="任务37/38可恢复执行器")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("plan")
    subparsers.add_parser("report")
    subparsers.add_parser("snapshot")
    verify = subparsers.add_parser("verify")
    verify.add_argument("--task", required=True)
    verify.add_argument("--full", action="store_true")
    verify.add_argument("--dry-run", action="store_true")
    run = subparsers.add_parser("run")
    run.add_argument("--next", action="store_true", required=True)
    run.add_argument("--full", action="store_true")
    run.add_argument("--dry-run", action="store_true")
    resume = subparsers.add_parser("resume")
    resume.add_argument("--full", action="store_true")
    resume.add_argument("--dry-run", action="store_true")
    return parser


def main() -> int:
    try:
        registry = load_registry()
        args = _parser().parse_args()
        if args.command == "plan":
            print(
                json.dumps(
                    {
                        "version": registry["version"],
                        "execution_order": registry["execution_order"],
                        "tasks": registry["tasks"],
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
            return 0
        if args.command == "report":
            print(json.dumps(report(registry), ensure_ascii=False, indent=2))
            return 0
        if args.command == "snapshot":
            snapshot = collect_snapshot(registry)
            print(
                json.dumps(
                    {
                        "path": str(snapshot_path(registry)),
                        "captured_at": snapshot["captured_at"],
                        "git_head": snapshot["git"]["head"],
                        "changed_assets": sum(
                            item["changed"] for item in snapshot["asset_drift"]
                        ),
                        "production_mutations_executed": False,
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
            return 0
        if args.command == "verify":
            return verify_task(
                registry,
                args.task.upper(),
                full=args.full,
                dry_run=args.dry_run,
            )
        if args.command == "run":
            task = next_task(registry)
            if not task:
                print(json.dumps({"status": "no_automatable_task_ready"}))
                return 0
            if not task.get("verify_commands"):
                print(
                    json.dumps(
                        {
                            "status": "implementation_or_verify_commands_required",
                            "task": task["id"],
                        },
                        ensure_ascii=False,
                    )
                )
                return 3
            return verify_task(
                registry,
                task["id"],
                full=args.full,
                dry_run=args.dry_run,
            )

        state = read_state(registry)
        failures = [
            (task_id, record)
            for task_id, record in state.get("runs", {}).items()
            if record.get("status") == "failed"
        ]
        if not failures:
            print(json.dumps({"status": "no_failed_task_to_resume"}))
            return 0
        task_id, record = failures[-1]
        full = bool(args.full or record.get("full"))
        specs = command_specs(_task_map(registry)[task_id], registry, full)
        start_index, previous = resume_point(record, specs)
        return verify_task(
            registry,
            task_id,
            full=full,
            dry_run=args.dry_run,
            start_index=start_index,
            previous_outcomes=previous,
        )
    except RegistryError as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
