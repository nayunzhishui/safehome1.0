"""Run bounded RC0810-F23 security mutants in an isolated source copy."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_POLICY = ROOT / "config" / "rc0810" / "f23_mutation_policy.json"
COPY_DIRS = ("backend", "content", "config", "shared", "scripts")


class MutationContractError(ValueError):
    pass


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _read_policy(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema") != "safehome.rc0810.f23-mutation-policy.v1":
        raise MutationContractError("unsupported F23 mutation policy schema")
    mutants = payload.get("mutants")
    if not isinstance(mutants, list) or not mutants:
        raise MutationContractError("mutation policy must declare targets")
    ids = [str(item.get("id") or "") for item in mutants]
    if any(not item for item in ids) or len(ids) != len(set(ids)):
        raise MutationContractError("mutation ids must be non-empty and unique")
    return payload


def _ignore(_directory: str, names: list[str]) -> set[str]:
    ignored = {
        name
        for name in names
        if name in {"__pycache__", "node_modules", "dist", "build", ".pytest_cache"}
        or name.endswith((".sqlite", ".sqlite3", ".db", ".pyc"))
    }
    return ignored


def _copy_runtime(destination: Path) -> None:
    for directory in COPY_DIRS:
        source = ROOT / directory
        if source.exists():
            shutil.copytree(source, destination / directory, ignore=_ignore)


def _git_commit() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else "unavailable"


def _snapshot(mutants: list[dict[str, Any]]) -> tuple[dict[str, str], str]:
    hashes: dict[str, str] = {}
    for relative in sorted({str(item["path"]) for item in mutants}):
        path = ROOT / relative
        if not path.is_file() or not path.resolve().is_relative_to(ROOT.resolve()):
            raise MutationContractError(f"mutation path is unavailable: {relative}")
        hashes[relative] = _sha256(path.read_bytes())
    digest_input = "\n".join(f"{path}\0{value}" for path, value in hashes.items())
    return hashes, _sha256(digest_input.encode("utf-8"))


def _classification(returncode: int, output: str, pytest_node: str) -> str:
    normalized = output.replace("\\", "/")
    if returncode == 1 and f"FAILED {pytest_node}" in normalized and "1 failed" in normalized:
        return "killed"
    if returncode == 0:
        return "survived"
    return "invalid_run"


def run_mutations(policy_path: Path = DEFAULT_POLICY) -> dict[str, Any]:
    try:
        from scripts.run_rc0810_f23_fuzz import (
            DEFAULT_CONTRACT,
            DEFAULT_CORPUS,
            build_cases,
        )
    except ModuleNotFoundError:
        from run_rc0810_f23_fuzz import (  # type: ignore[no-redef]
            DEFAULT_CONTRACT,
            DEFAULT_CORPUS,
            build_cases,
        )

    policy = _read_policy(Path(policy_path))
    mutants = policy["mutants"]
    fuzz_cases = build_cases(DEFAULT_CONTRACT, DEFAULT_CORPUS)
    file_hashes, snapshot_sha256 = _snapshot(mutants)
    results: list[dict[str, Any]] = []
    timeout = int(policy.get("timeout_seconds_per_mutant") or 120)
    with tempfile.TemporaryDirectory(prefix="safehome-rc0810-f23-") as temporary:
        isolated_root = Path(temporary)
        _copy_runtime(isolated_root)
        for mutant in mutants:
            relative = str(mutant["path"])
            target = isolated_root / relative
            original = target.read_text(encoding="utf-8")
            find = str(mutant.get("find") or "")
            replacement = str(mutant.get("replace") or "")
            if not find or original.count(find) != 1:
                raise MutationContractError(
                    f"mutant {mutant['id']} expected exactly one source match"
                )
            target.write_text(original.replace(find, replacement, 1), encoding="utf-8")
            environment = dict(os.environ)
            environment["RC0810_MUTATION_CHILD"] = "1"
            environment["PYTHONPATH"] = os.pathsep.join(
                [str(isolated_root), str(isolated_root / "backend")]
            )
            try:
                completed = subprocess.run(
                    [sys.executable, "-m", "pytest", str(mutant["pytest_node"]), "-q"],
                    cwd=isolated_root,
                    env=environment,
                    text=True,
                    capture_output=True,
                    timeout=timeout,
                    check=False,
                )
                combined = f"{completed.stdout}\n{completed.stderr}"
                classification = _classification(
                    completed.returncode, combined, str(mutant["pytest_node"])
                )
                returncode = completed.returncode
            except subprocess.TimeoutExpired:
                classification = "invalid_run"
                returncode = 124
            finally:
                target.write_text(original, encoding="utf-8")
            results.append(
                {
                    "id": mutant["id"],
                    "gate": mutant["gate"],
                    "path": relative,
                    "pytest_node": mutant["pytest_node"],
                    "classification": classification,
                    "returncode": returncode,
                }
            )
    killed = sum(item["classification"] == "killed" for item in results)
    return {
        "schema": "safehome.rc0810.f23-mutation-report.v1",
        "seed": int(policy.get("seed") or 0),
        "source_base_commit": _git_commit(),
        "source_files_sha256": file_hashes,
        "source_snapshot_sha256": snapshot_sha256,
        "api_contract_sha256": _sha256(DEFAULT_CONTRACT.read_bytes()),
        "fuzz_corpus_sha256": _sha256(DEFAULT_CORPUS.read_bytes()),
        "fuzz_case_count": len(fuzz_cases),
        "fuzz_case_ids": [item["case_id"] for item in fuzz_cases],
        "mutant_count": len(results),
        "killed_count": killed,
        "surviving_count": sum(item["classification"] == "survived" for item in results),
        "invalid_run_count": sum(item["classification"] == "invalid_run" for item in results),
        "all_killed": killed == len(results),
        "results": results,
        "schema_contract_gaps": [
            {
                "id": "F23-SCHEMA-01",
                "status": "open_for_followup",
                "operation_id": "therapeutic_assessment.post_case_route.post",
                "finding": "运行时要求JSON字段与Idempotency-Key，但当前API契约仍登记空body_fields且idempotency=false。",
                "production_gate_blocking": True,
            }
        ],
        "replay_command": "python scripts/run_rc0810_f23_mutation.py --report docs/02_专项进度与验收/rc0810_f23_mutation_report.json",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--policy", type=Path, default=DEFAULT_POLICY)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    report = run_mutations(args.policy)
    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0 if report["all_killed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
