"""SafeHome tasks 23-34 deterministic verification orchestrator.

This tool executes only registered local checks. It never edits plan status,
signs external gates, publishes to production, or changes cloud resources.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "config" / "task23_34_registry.json"


class RegistryError(ValueError):
    pass


def load_registry() -> dict:
    payload = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    expected = [f"T{number}" for number in range(23, 35)]
    actual = [item.get("id") for item in payload.get("tasks", [])]
    if payload.get("scope") != expected or actual != expected:
        raise RegistryError("任务注册表必须按T23至T34连续登记。")
    if payload.get("policy", {}).get("release_approval_mutation_allowed") is not False:
        raise RegistryError("执行器不得修改发布批准。")
    if payload.get("policy", {}).get("external_gate_execution_allowed") is not False:
        raise RegistryError("执行器不得执行人工或外部门禁。")
    required = set(payload.get("required_layers", []))
    if len(required) < 13:
        raise RegistryError("完整实现层级登记不完整。")
    return payload


def state_path(registry: dict) -> Path:
    target = (ROOT / registry["policy"]["state_path"]).resolve()
    allowed = (ROOT / ".codex_tmp").resolve()
    try:
        target.relative_to(allowed)
    except ValueError as exc:
        raise RegistryError("运行状态只能写入.codex_tmp。") from exc
    return target


def read_state(registry: dict) -> dict:
    path = state_path(registry)
    if not path.exists():
        return {"schema": "safehome.tasks23_34.state.v1", "runs": {}}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RegistryError("运行状态损坏；请保留文件并人工复核后再继续。") from exc
    if payload.get("schema") != "safehome.tasks23_34.state.v1":
        raise RegistryError("运行状态schema不兼容。")
    return payload


def write_state(registry: dict, state: dict) -> None:
    path = state_path(registry)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(".tmp")
    temp.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temp.replace(path)


def task_map(registry: dict) -> dict[str, dict]:
    return {item["id"]: item for item in registry["tasks"]}


def validate_evidence_and_commits(registry: dict) -> list[dict]:
    results = []
    for task in registry["tasks"]:
        missing = [path for path in task.get("evidence", []) if not (ROOT / path).exists()]
        commit = task.get("commit") or ""
        commit_ok = subprocess.run(
            ["git", "merge-base", "--is-ancestor", commit, "HEAD"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        ).returncode == 0
        results.append({"task": task["id"], "missing_evidence": missing, "commit_is_ancestor": commit_ok})
    return results


def command_specs(task: dict, registry: dict, full: bool) -> list[dict]:
    specs = [{"cwd": ".", "command": command} for command in task.get("verify_commands", [])]
    if full:
        specs.extend(registry.get("full_acceptance_commands", []))
    return specs


def run_specs(specs: list[dict], dry_run: bool) -> tuple[bool, list[dict]]:
    outcomes = []
    for spec in specs:
        command = spec["command"]
        cwd = (ROOT / spec.get("cwd", ".")).resolve()
        if dry_run:
            outcomes.append({"command": command, "cwd": str(cwd), "status": "dry_run"})
            continue
        completed = subprocess.run(command, cwd=cwd, check=False)
        outcome = {"command": command, "cwd": str(cwd), "returncode": completed.returncode}
        outcomes.append(outcome)
        if completed.returncode != 0:
            return False, outcomes
    return True, outcomes


def resume_point(record: dict, specs: list[dict]) -> tuple[int, list[dict]]:
    outcomes = record.get("outcomes", [])
    prefix = []
    for index, outcome in enumerate(outcomes):
        if index >= len(specs) or outcome.get("command") != specs[index].get("command"):
            raise RegistryError("注册表命令已变化，不能沿用旧失败点；请重新verify。")
        if outcome.get("returncode") != 0:
            return index, prefix
        prefix.append(outcome)
    return len(prefix), prefix


def verify_task(
    registry: dict,
    task_id: str,
    *,
    full: bool,
    dry_run: bool,
    start_index: int = 0,
    previous_outcomes: list[dict] | None = None,
) -> int:
    tasks = task_map(registry)
    if task_id not in tasks:
        raise RegistryError(f"未知任务：{task_id}")
    task = tasks[task_id]
    specs = command_specs(task, registry, full)
    if start_index < 0 or start_index > len(specs):
        raise RegistryError("恢复命令位置无效。")
    ok, current_outcomes = run_specs(specs[start_index:], dry_run)
    outcomes = list(previous_outcomes or []) + current_outcomes
    state = read_state(registry)
    state["registry_version"] = registry["version"]
    state["updated_at"] = datetime.now(timezone.utc).isoformat()
    state.setdefault("runs", {})[task_id] = {
        "status": "dry_run" if dry_run else ("passed" if ok else "failed"),
        "full": full,
        "outcomes": outcomes,
        "release_approved": False,
        "external_gates_executed": False,
    }
    write_state(registry, state)
    print(json.dumps(state["runs"][task_id], ensure_ascii=False, indent=2))
    return 0 if ok else 1


def next_task(registry: dict) -> dict | None:
    tasks = task_map(registry)
    for task in registry["tasks"]:
        if task["engineering_complete"]:
            continue
        if all(tasks[dependency]["engineering_complete"] for dependency in task.get("dependencies", [])):
            return task
    return None


def report(registry: dict) -> dict:
    evidence = validate_evidence_and_commits(registry)
    tracked = [task for task in registry["tasks"] if task["id"] >= "T25"]
    return {
        "schema": "safehome.tasks23_34.report.v1",
        "registry_version": registry["version"],
        "tasks_total": len(registry["tasks"]),
        "tasks_t25_t34_engineering_complete": sum(bool(task["engineering_complete"]) for task in tracked),
        "tasks_t25_t34_total": len(tracked),
        "all_t25_t34_engineering_complete": all(task["engineering_complete"] for task in tracked),
        "all_commits_reachable": all(item["commit_is_ancestor"] for item in evidence),
        "all_evidence_present": all(not item["missing_evidence"] for item in evidence),
        "release_approved": False,
        "external_gates_executed": False,
        "temporary_showcase_bypass_counts_as_permission_evidence": False,
        "task_statuses": {task["id"]: task["status"] for task in registry["tasks"]},
        "evidence_audit": evidence,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="任务二十三至三十四本地验收编排器")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("plan")
    sub.add_parser("report")
    run = sub.add_parser("run")
    run.add_argument("--next", action="store_true", required=True)
    run.add_argument("--full", action="store_true")
    run.add_argument("--dry-run", action="store_true")
    resume = sub.add_parser("resume")
    resume.add_argument("--full", action="store_true")
    resume.add_argument("--dry-run", action="store_true")
    verify = sub.add_parser("verify")
    verify.add_argument("--task", required=True)
    verify.add_argument("--full", action="store_true")
    verify.add_argument("--dry-run", action="store_true")
    return parser


def main() -> int:
    try:
        registry = load_registry()
        args = build_parser().parse_args()
        if args.command == "plan":
            print(json.dumps({"version": registry["version"], "tasks": registry["tasks"]}, ensure_ascii=False, indent=2))
            return 0
        if args.command == "report":
            print(json.dumps(report(registry), ensure_ascii=False, indent=2))
            return 0
        if args.command == "verify":
            return verify_task(registry, args.task.upper(), full=args.full, dry_run=args.dry_run)
        if args.command == "run":
            task = next_task(registry)
            if not task:
                print(json.dumps({"status": "no_engineering_task_ready"}, ensure_ascii=False))
                return 0
            return verify_task(registry, task["id"], full=args.full, dry_run=args.dry_run)
        state = read_state(registry)
        failed = [(task_id, item) for task_id, item in state.get("runs", {}).items() if item.get("status") == "failed"]
        if failed:
            task_id, record = failed[-1]
            full = bool(args.full or record.get("full"))
            specs = command_specs(task_map(registry)[task_id], registry, full)
            start_index, previous = resume_point(record, specs)
            return verify_task(
                registry,
                task_id,
                full=full,
                dry_run=args.dry_run,
                start_index=start_index,
                previous_outcomes=previous,
            )
        task_id = (next_task(registry) or {}).get("id")
        if not task_id:
            print(json.dumps({"status": "nothing_to_resume"}, ensure_ascii=False))
            return 0
        return verify_task(registry, task_id, full=args.full, dry_run=args.dry_run)
    except RegistryError as exc:
        print(json.dumps({"error": "registry_error", "message": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
