"""Recoverable Task36 F19 full acceptance and external-gate evidence runner."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "config" / "task36_acceptance_manifest.json"
REGISTRY_PATH = ROOT / "config" / "task36_registry.json"
DEFAULT_OUTPUT = ROOT / ".codex_tmp" / "task36_f19_acceptance.json"
ALLOWED_EXECUTABLES = {"python", "python.exe", "node", "node.exe", "npm.cmd"}
FORBIDDEN_TERMS = {
    "git reset",
    "git checkout --",
    "git clean",
    "cloudflared tunnel run",
    "cloudflared tunnel --url",
    "bootstrap_researcher.py apply",
    "bootstrap_researcher.py rotate",
    "TRUST_CLOUDBASE_IDENTITY_HEADERS=1",
    "WECHAT_APP_SECRET=",
}


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_manifest(manifest: dict) -> list[str]:
    issues: list[str] = []
    if manifest.get("schema") != "safehome.task36.acceptance_manifest.v1":
        issues.append("invalid_schema")
    expected_tasks = {f"T36-F{index:02d}" for index in range(20)}
    if set(manifest.get("required_tasks", [])) != expected_tasks:
        issues.append("task_scope_incomplete")
    ids: set[str] = set()
    for item in [*manifest.get("commands", []), *manifest.get("external_observation_commands", [])]:
        command = [str(value) for value in item.get("command", [])]
        command_text = " ".join(command)
        if not item.get("id") or item["id"] in ids:
            issues.append("duplicate_or_missing_command_id")
        ids.add(str(item.get("id", "")))
        if not command or command[0].lower() not in ALLOWED_EXECUTABLES:
            issues.append(f"executable_not_allowed:{item.get('id')}")
        if any(term.lower() in command_text.lower() for term in FORBIDDEN_TERMS):
            issues.append(f"forbidden_command:{item.get('id')}")
        cwd = (ROOT / str(item.get("cwd", "."))).resolve()
        if ROOT not in [cwd, *cwd.parents]:
            issues.append(f"cwd_outside_repo:{item.get('id')}")
    policy = manifest.get("policy", {})
    if any(
        policy.get(key) is not False
        for key in (
            "release_approved",
            "external_gate_execution_allowed",
            "production_mutation_allowed",
            "wechat_secret_mutation_allowed",
            "public_tunnel_start_allowed",
            "temporary_showcase_bypass_counts_as_formal_permission_evidence",
            "store_command_output_text",
        )
    ):
        issues.append("unsafe_policy")
    return issues


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def write_evidence(path: Path, evidence: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def command_result(item: dict) -> dict:
    started = time.monotonic()
    command = [str(value) for value in item["command"]]
    cwd = (ROOT / str(item.get("cwd", "."))).resolve()
    try:
        completed = subprocess.run(
            command,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=int(item.get("timeout_seconds", 600)),
            check=False,
        )
        returncode = int(completed.returncode)
        stdout = completed.stdout
        stderr = completed.stderr
        timed_out = False
    except subprocess.TimeoutExpired as error:
        returncode = 124
        stdout = error.stdout or b""
        stderr = error.stderr or b""
        timed_out = True
    return {
        "id": item["id"],
        "category": item["category"],
        "command": command,
        "cwd": str(item.get("cwd", ".")),
        "required": bool(item.get("required", True)),
        "returncode": returncode,
        "timed_out": timed_out,
        "duration_ms": int((time.monotonic() - started) * 1000),
        "stdout_bytes": len(stdout),
        "stderr_bytes": len(stderr),
        "stdout_sha256": sha256_bytes(stdout),
        "stderr_sha256": sha256_bytes(stderr),
        "output_text_stored": False,
        "passed": returncode == 0,
    }


def documentation_result(manifest: dict) -> dict:
    missing = [
        relative
        for relative in manifest.get("required_paths", [])
        if not (ROOT / relative).is_file()
    ]
    return {
        "id": "documentation_paths",
        "category": "documentation",
        "required": True,
        "missing_paths": missing,
        "passed": not missing,
        "output_text_stored": False,
    }


def registry_result() -> dict:
    registry = load_json(REGISTRY_PATH)
    incomplete = [
        item["id"]
        for item in registry.get("tasks", [])
        if item["id"] != "T36-F19" and not item.get("engineering_complete")
    ]
    return {
        "id": "task36_registry_f00_f18",
        "category": "documentation",
        "required": True,
        "incomplete_tasks": incomplete,
        "passed": not incomplete,
        "release_approved": False,
    }


def initial_evidence(manifest: dict) -> dict:
    return {
        "schema": "safehome.task36.acceptance_evidence.v1",
        "manifest_version": manifest["version"],
        "status": "running",
        "started_at_epoch": int(time.time()),
        "completed_at_epoch": None,
        "results": [],
        "category_status": {},
        "external_gates": [
            {"id": gate, "status": "evidence_pending", "executed": False, "approved": False}
            for gate in manifest.get("external_gates", [])
        ],
        "release_approved": False,
        "external_gates_executed": False,
        "production_mutations_executed": False,
        "wechat_secret_mutated": False,
        "public_tunnel_started": False,
        "temporary_showcase_bypass_counts_as_formal_permission_evidence": False,
    }


def run(output: Path, *, resume: bool, include_cloud_probe: bool) -> dict:
    manifest = load_json(MANIFEST_PATH)
    issues = validate_manifest(manifest)
    if issues:
        raise RuntimeError("acceptance manifest invalid: " + ", ".join(issues))
    if resume and output.exists():
        evidence = load_json(output)
        evidence["status"] = "running"
        evidence["completed_at_epoch"] = None
    else:
        evidence = initial_evidence(manifest)
    previous = {
        item["id"]: item
        for item in evidence.get("results", [])
        if item.get("passed")
    }
    commands = list(manifest["commands"])
    if include_cloud_probe:
        commands.extend(manifest.get("external_observation_commands", []))
    results: list[dict] = []
    for item in commands:
        result = previous.get(item["id"]) if resume else None
        if result is None:
            result = command_result(item)
        results.append(result)
        evidence["results"] = results
        write_evidence(output, evidence)
        if item.get("required", True) and not result["passed"]:
            break
    if len(results) == len(commands) and all(
        result["passed"] or not result.get("required", True)
        for result in results
    ):
        results.extend([documentation_result(manifest), registry_result()])
    categories = sorted({result["category"] for result in results})
    evidence["results"] = results
    evidence["category_status"] = {
        category: (
            "passed"
            if all(
                result["passed"] or not result.get("required", True)
                for result in results
                if result["category"] == category
            )
            else "failed"
        )
        for category in categories
    }
    required_results = [result for result in results if result.get("required", True)]
    evidence["status"] = (
        "passed"
        if len(results) >= len(commands) + 2 and all(result["passed"] for result in required_results)
        else "failed"
    )
    evidence["completed_at_epoch"] = int(time.time())
    write_evidence(output, evidence)
    return evidence


def verify(output: Path) -> dict:
    evidence = load_json(output)
    manifest = load_json(MANIFEST_PATH)
    required_ids = {item["id"] for item in manifest["commands"] if item.get("required", True)}
    passed_ids = {
        item["id"]
        for item in evidence.get("results", [])
        if item.get("required", True) and item.get("passed")
    }
    gates_pending = all(
        item.get("status") == "evidence_pending"
        and item.get("executed") is False
        and item.get("approved") is False
        for item in evidence.get("external_gates", [])
    )
    ok = (
        evidence.get("schema") == "safehome.task36.acceptance_evidence.v1"
        and evidence.get("status") == "passed"
        and required_ids <= passed_ids
        and {"documentation_paths", "task36_registry_f00_f18"} <= passed_ids
        and gates_pending
        and evidence.get("release_approved") is False
        and evidence.get("production_mutations_executed") is False
    )
    return {
        "ok": ok,
        "status": evidence.get("status"),
        "required_commands_passed": sorted(required_ids & passed_ids),
        "required_commands_missing": sorted(required_ids - passed_ids),
        "external_gates_pending": gates_pending,
        "release_approved": False,
        "production_mutations_executed": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["plan", "run", "verify", "evidence"])
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--include-cloud-probe", action="store_true")
    args = parser.parse_args()
    output = args.output.resolve()
    if args.action == "plan":
        payload = {
            "manifest": load_json(MANIFEST_PATH),
            "issues": validate_manifest(load_json(MANIFEST_PATH)),
            "production_mutations_executed": False,
        }
    elif args.action == "run":
        payload = run(output, resume=args.resume, include_cloud_probe=args.include_cloud_probe)
    elif args.action == "verify":
        payload = verify(output)
    else:
        payload = load_json(output)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload.get("ok", payload.get("status") != "failed") else 1


if __name__ == "__main__":
    raise SystemExit(main())
