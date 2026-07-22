"""Task 36 deterministic local orchestrator and sanitized baseline collector.

The tool may read public health/error endpoints and execute registered local
verification commands. It never mutates cloud settings, credentials, tunnels,
showcase permissions, release approvals, or production data.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "config" / "task36_registry.json"
STATE_SCHEMA = "safehome.task36.state.v1"
BASELINE_SCHEMA = "safehome.task36.baseline.v1"
SENSITIVE_KEY = re.compile(
    r"(^|_)(secret|password|token|authorization|cookie|openid|phone_number|phone_hash|mobile|credential)(_|$)",
    re.I,
)
SENSITIVE_TEXT = re.compile(
    r"(?i)(authorization\s*[:=]|bearer\s+|appsecret\s*[:=]|password\s*[:=]|token\s*[:=]|openid\s*[:=])"
)


class RegistryError(ValueError):
    pass


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _atomic_write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temp.replace(path)


def load_registry() -> dict:
    try:
        payload = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RegistryError("任务36注册表缺失或不是有效JSON。") from exc
    expected = [f"T36-F{number:02d}" for number in range(20)]
    actual = [item.get("id") for item in payload.get("tasks", [])]
    if payload.get("schema") != "safehome.task36.registry.v1":
        raise RegistryError("任务36注册表schema不兼容。")
    if payload.get("scope") != expected or actual != expected:
        raise RegistryError("任务36注册表必须连续覆盖T36-F00至T36-F19。")
    policy = payload.get("policy", {})
    forbidden_true = (
        "release_approval_mutation_allowed",
        "external_gate_execution_allowed",
        "production_account_mutation_allowed",
        "public_tunnel_start_allowed",
        "wechat_secret_mutation_allowed",
        "showcase_write_scope_expansion_allowed",
        "temporary_showcase_bypass_counts_as_formal_permission_evidence",
    )
    if any(policy.get(key) is not False for key in forbidden_true):
        raise RegistryError("任务36执行器安全策略不得允许外部、凭据、隧道、权限或批准变更。")
    if policy.get("dirty_worktree_policy") != "observe_only_never_revert":
        raise RegistryError("任务36执行器必须只观察dirty工作区，禁止回退文件。")
    required = set(payload.get("required_layers", []))
    if len(required) < 13:
        raise RegistryError("任务36完整实现层级登记不完整。")
    _validate_registered_commands(payload)
    return payload


def _safe_tmp_path(registry: dict, policy_key: str) -> Path:
    target = (ROOT / registry["policy"][policy_key]).resolve()
    allowed = (ROOT / ".codex_tmp").resolve()
    try:
        target.relative_to(allowed)
    except ValueError as exc:
        raise RegistryError("任务36运行产物只能写入.codex_tmp。") from exc
    return target


def state_path(registry: dict) -> Path:
    return _safe_tmp_path(registry, "state_path")


def baseline_path(registry: dict) -> Path:
    return _safe_tmp_path(registry, "baseline_path")


def read_state(registry: dict) -> dict:
    path = state_path(registry)
    if not path.exists():
        return {"schema": STATE_SCHEMA, "runs": {}}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RegistryError("任务36运行状态损坏；请保留原文件并人工复核。") from exc
    if payload.get("schema") != STATE_SCHEMA:
        raise RegistryError("任务36运行状态schema不兼容。")
    return payload


def write_state(registry: dict, state: dict) -> None:
    _atomic_write_json(state_path(registry), state)


def _command_text(command: list[str]) -> str:
    return " ".join(str(item) for item in command)


def _validate_command(registry: dict, command: list[str]) -> None:
    if not command or not all(isinstance(item, str) and item for item in command):
        raise RegistryError("验收命令必须是非空字符串数组。")
    executable = Path(command[0]).name.lower()
    allowed = {item.lower() for item in registry["policy"].get("allowed_command_executables", [])}
    if executable not in allowed:
        raise RegistryError(f"验收命令执行器未获允许：{command[0]}")
    normalized = _command_text(command).lower()
    for term in registry["policy"].get("forbidden_command_terms", []):
        if term.lower() in normalized:
            raise RegistryError(f"验收命令包含禁止操作：{term}")


def _validate_registered_commands(registry: dict) -> None:
    for task in registry.get("tasks", []):
        for command in task.get("verify_commands", []):
            _validate_command(registry, command)
    for spec in registry.get("full_acceptance_commands", []):
        _validate_command(registry, spec.get("command", []))


def _task_map(registry: dict) -> dict[str, dict]:
    return {item["id"]: item for item in registry["tasks"]}


def command_specs(task: dict, registry: dict, full: bool) -> list[dict]:
    specs = [{"cwd": ".", "command": command} for command in task.get("verify_commands", [])]
    if full:
        specs.extend(registry.get("full_acceptance_commands", []))
    for spec in specs:
        _validate_command(registry, spec["command"])
    return specs


def command_digest(specs: list[dict]) -> str:
    normalized = json.dumps(specs, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def run_specs(specs: list[dict], dry_run: bool) -> tuple[bool, list[dict]]:
    outcomes: list[dict] = []
    for spec in specs:
        command = spec["command"]
        cwd = (ROOT / spec.get("cwd", ".")).resolve()
        try:
            cwd.relative_to(ROOT.resolve())
        except ValueError as exc:
            raise RegistryError("验收命令工作目录必须位于项目内。") from exc
        if dry_run:
            outcomes.append({"command": command, "cwd": str(cwd), "status": "dry_run"})
            continue
        completed = subprocess.run(command, cwd=cwd, check=False)
        outcomes.append({"command": command, "cwd": str(cwd), "returncode": completed.returncode})
        if completed.returncode != 0:
            return False, outcomes
    return True, outcomes


def resume_point(record: dict, specs: list[dict]) -> tuple[int, list[dict]]:
    if record.get("command_digest") != command_digest(specs):
        raise RegistryError("注册表命令已变化，不能resume；请重新verify。")
    outcomes = record.get("outcomes", [])
    prefix: list[dict] = []
    for index, outcome in enumerate(outcomes):
        if index >= len(specs) or outcome.get("command") != specs[index].get("command"):
            raise RegistryError("运行记录与当前命令不一致，不能resume。")
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
    task = _task_map(registry).get(task_id)
    if not task:
        raise RegistryError(f"未知任务：{task_id}")
    specs = command_specs(task, registry, full)
    if not specs:
        raise RegistryError(f"{task_id}尚未登记自动验收命令，不能执行。")
    if start_index < 0 or start_index > len(specs):
        raise RegistryError("恢复命令位置无效。")
    ok, current = run_specs(specs[start_index:], dry_run)
    outcomes = list(previous_outcomes or []) + current
    state = read_state(registry)
    state["registry_version"] = registry["version"]
    state["updated_at"] = _utc_now()
    state.setdefault("runs", {})[task_id] = {
        "status": "dry_run" if dry_run else ("passed" if ok else "failed"),
        "full": full,
        "command_digest": command_digest(specs),
        "outcomes": outcomes,
        "release_approved": False,
        "external_gates_executed": False,
        "production_mutations_executed": False,
    }
    write_state(registry, state)
    print(json.dumps(state["runs"][task_id], ensure_ascii=False, indent=2))
    return 0 if ok else 1


def next_task(registry: dict) -> dict | None:
    tasks = _task_map(registry)
    for task in registry["tasks"]:
        if task.get("engineering_complete"):
            continue
        if all(tasks[dependency].get("engineering_complete") for dependency in task.get("dependencies", [])):
            return task
    return None


def _git_output(*args: str) -> str:
    completed = subprocess.run(
        ["git", *args], cwd=ROOT, capture_output=True, text=True, check=False, encoding="utf-8", errors="replace"
    )
    if completed.returncode != 0:
        raise RegistryError(f"Git只读快照失败：{' '.join(args)}")
    return completed.stdout.strip()


def git_snapshot() -> dict:
    dirty_lines = [line for line in _git_output("status", "--short").splitlines() if line]
    return {
        "head": _git_output("rev-parse", "HEAD"),
        "branch": _git_output("branch", "--show-current"),
        "upstream": _git_output("rev-parse", "--abbrev-ref", "@{upstream}"),
        "dirty": bool(dirty_lines),
        "dirty_files": [line[3:] if len(line) > 3 else line for line in dirty_lines],
        "dirty_entries": len(dirty_lines),
        "mutation_policy": "observe_only_never_revert",
    }


def _redact(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: ("[REDACTED]" if SENSITIVE_KEY.search(str(key)) else _redact(item)) for key, item in value.items()}
    if isinstance(value, list):
        return [_redact(item) for item in value]
    if isinstance(value, str) and SENSITIVE_TEXT.search(value):
        return "[REDACTED]"
    return value


def _safe_json_summary(kind: str, payload: Any) -> dict:
    if not isinstance(payload, dict):
        return {"json_type": type(payload).__name__}
    summary: dict[str, Any] = {"top_level_keys": sorted(str(key) for key in payload.keys())}
    if "ok" in payload:
        summary["ok"] = bool(payload.get("ok"))
    request_id = payload.get("request_id") or (payload.get("meta") or {}).get("request_id")
    if request_id:
        summary["request_id_present"] = True
    error = payload.get("error")
    if isinstance(error, dict):
        summary["error"] = {"code": str(error.get("code") or ""), "message_present": bool(error.get("message"))}
    if kind in {"health", "readiness"}:
        database = payload.get("database") if isinstance(payload.get("database"), dict) else {}
        summary["service"] = payload.get("service")
        summary["status"] = payload.get("status")
        summary["version"] = payload.get("version")
        summary["database"] = {
            "provider": database.get("provider"),
            "current_schema_version": database.get("current_schema_version"),
            "expected_schema_version": database.get("expected_schema_version"),
            "schema_version_ok": database.get("schema_version_ok"),
        }
    elif kind == "capabilities":
        data = payload.get("data") if isinstance(payload.get("data"), dict) else payload
        for key in ("wechat_login", "phone_login", "password_login"):
            item = data.get(key) if isinstance(data, dict) else None
            if isinstance(item, dict):
                summary[key] = {"available": bool(item.get("available")), "mode": item.get("mode")}
    return _redact(summary)


def _probe_endpoint(base_url: str, spec: dict, timeout: int) -> dict:
    url = f"{base_url.rstrip('/')}{spec['path']}"
    request = urllib.request.Request(url, method=spec.get("method", "GET"), headers={"Accept": "application/json"})
    try:
        response = urllib.request.urlopen(request, timeout=timeout)
        status = response.status
        headers = response.headers
        body = response.read(262144)
    except urllib.error.HTTPError as exc:
        status = exc.code
        headers = exc.headers
        body = exc.read(262144)
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        return {
            "id": spec["id"],
            "method": spec.get("method", "GET"),
            "path": spec["path"],
            "transport_error": type(exc).__name__,
            "expected_statuses": spec.get("expected_statuses", []),
            "matches_expected_status": False,
        }
    content_type = str(headers.get("Content-Type") or "").split(";", 1)[0].strip().lower()
    result: dict[str, Any] = {
        "id": spec["id"],
        "method": spec.get("method", "GET"),
        "path": spec["path"],
        "http_status": status,
        "content_type": content_type,
        "content_length_observed": len(body),
        "request_id_present": bool(headers.get("X-Request-ID") or headers.get("X-Request-Id")),
        "expected_statuses": spec.get("expected_statuses", []),
        "matches_expected_status": status in spec.get("expected_statuses", []),
    }
    if "json" in content_type:
        try:
            result["response_summary"] = _safe_json_summary(spec.get("kind", "fault"), json.loads(body.decode("utf-8")))
        except (UnicodeDecodeError, json.JSONDecodeError):
            result["json_parse_error"] = True
    else:
        result["non_json_response"] = True
    return _redact(result)


def collect_baseline(registry: dict, base_url: str | None = None) -> dict:
    cloud = registry["baseline"]["cloudbase"]
    effective_base = (base_url or cloud["base_url"]).rstrip("/")
    timeout = int(cloud.get("snapshot_timeout_seconds", 12))
    specs = cloud["endpoints"]
    with ThreadPoolExecutor(max_workers=min(6, len(specs))) as pool:
        probes = list(pool.map(lambda item: _probe_endpoint(effective_base, item, timeout), specs))
    payload = {
        "schema": BASELINE_SCHEMA,
        "registry_version": registry["version"],
        "captured_at": _utc_now(),
        "git": git_snapshot(),
        "cloudbase": {
            "base_url": effective_base,
            "service": cloud.get("service"),
            "environment": cloud.get("environment"),
            "probes": probes,
        },
        "database_contract": registry["baseline"]["database"],
        "roles": registry["roles"],
        "feature_flags": registry["baseline"]["feature_flags"],
        "safety": {
            "secrets_recorded": False,
            "tokens_recorded": False,
            "response_bodies_recorded": False,
            "production_mutations_executed": False,
        },
    }
    serialized = json.dumps(payload, ensure_ascii=False)
    if SENSITIVE_TEXT.search(serialized):
        raise RegistryError("脱敏快照疑似包含敏感值，已阻止写入。")
    _atomic_write_json(baseline_path(registry), payload)
    return payload


def validate_evidence(registry: dict) -> list[dict]:
    return [
        {
            "task": task["id"],
            "missing_evidence": [path for path in task.get("evidence", []) if not (ROOT / path).exists()],
        }
        for task in registry["tasks"]
    ]


def report(registry: dict) -> dict:
    evidence = validate_evidence(registry)
    baseline_exists = baseline_path(registry).exists()
    return {
        "schema": "safehome.task36.report.v1",
        "registry_version": registry["version"],
        "tasks_total": len(registry["tasks"]),
        "tasks_engineering_complete": sum(bool(task.get("engineering_complete")) for task in registry["tasks"]),
        "next_automatable_task": (next_task(registry) or {}).get("id"),
        "baseline_snapshot_exists": baseline_exists,
        "all_current_evidence_present": all(not item["missing_evidence"] for item in evidence if _task_map(registry)[item["task"]].get("engineering_complete")),
        "release_approved": False,
        "external_gates_executed": False,
        "production_mutations_executed": False,
        "temporary_showcase_bypass_counts_as_formal_permission_evidence": False,
        "task_statuses": {task["id"]: task["status"] for task in registry["tasks"]},
        "evidence_audit": evidence,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="任务三十六本地可恢复执行器")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("plan")
    sub.add_parser("report")
    snapshot = sub.add_parser("snapshot")
    snapshot.add_argument("--base-url")
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
        if args.command == "snapshot":
            payload = collect_baseline(registry, args.base_url)
            print(json.dumps({
                "path": str(baseline_path(registry)),
                "captured_at": payload["captured_at"],
                "git_head": payload["git"]["head"],
                "probe_statuses": {item["id"]: item.get("http_status", item.get("transport_error")) for item in payload["cloudbase"]["probes"]},
                "production_mutations_executed": False,
            }, ensure_ascii=False, indent=2))
            return 0
        if args.command == "verify":
            return verify_task(registry, args.task.upper(), full=args.full, dry_run=args.dry_run)
        if args.command == "run":
            task = next_task(registry)
            if not task:
                print(json.dumps({"status": "no_automatable_task_ready"}, ensure_ascii=False))
                return 0
            if not task.get("verify_commands"):
                print(json.dumps({
                    "status": "implementation_or_verify_commands_required",
                    "task": task["id"],
                    "message": "该切片尚未登记验收命令；先完成失败契约和最小实现，不能跳过到后续任务。",
                }, ensure_ascii=False))
                return 3
            return verify_task(registry, task["id"], full=args.full, dry_run=args.dry_run)
        state = read_state(registry)
        failures = [(task_id, item) for task_id, item in state.get("runs", {}).items() if item.get("status") == "failed"]
        if failures:
            task_id, record = failures[-1]
            full = bool(args.full or record.get("full"))
            specs = command_specs(_task_map(registry)[task_id], registry, full)
            start, previous = resume_point(record, specs)
            return verify_task(registry, task_id, full=full, dry_run=args.dry_run, start_index=start, previous_outcomes=previous)
        task = next_task(registry)
        if not task:
            print(json.dumps({"status": "nothing_to_resume"}, ensure_ascii=False))
            return 0
        if not task.get("verify_commands"):
            print(json.dumps({
                "status": "implementation_or_verify_commands_required",
                "task": task["id"],
                "message": "该切片尚无失败运行可恢复，需先完成失败契约和最小实现。",
            }, ensure_ascii=False))
            return 3
        return verify_task(registry, task["id"], full=args.full, dry_run=args.dry_run)
    except RegistryError as exc:
        print(json.dumps({"error": "registry_error", "message": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
