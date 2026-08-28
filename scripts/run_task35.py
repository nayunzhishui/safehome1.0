"""Task 35 machine-readable verifier.

This runner verifies frozen engineering evidence only. It never downloads data,
trains on external text, signs a human gate, or enables production replacement.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from services.artifact_integrity_service import artifact_sha256


REGISTRY_PATH = ROOT / "config" / "task35_registry.json"
MANIFEST_PATH = ROOT / "content" / "offline_baseline_manifest.json"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def verify() -> dict:
    registry = _load(REGISTRY_PATH)
    manifest = _load(MANIFEST_PATH)
    failures: list[dict[str, str]] = []
    for task in registry["tasks"]:
        for relative in task.get("evidence", []):
            if not (ROOT / relative).is_file():
                failures.append({"task": task["id"], "path": relative, "reason": "missing"})
    for artifact in manifest["artifacts"]:
        path = ROOT / artifact["path"]
        if not path.is_file():
            failures.append({"task": "T35-F00", "path": artifact["path"], "reason": "missing"})
            continue
        normalized_hash = artifact_sha256(path)
        if artifact["sha256"] != normalized_hash:
            failures.append({"task": "T35-F00", "path": artifact["path"], "reason": "sha256_mismatch"})
    return {
        "schema": "safehome.task35.verify.v1",
        "status": "passed" if not failures else "failed",
        "engineering_task_count": len(registry["tasks"]),
        "production_replacement_allowed": False,
        "external_download_started": False,
        "human_gate_signed": False,
        "failures": failures,
    }


def report() -> dict:
    registry = _load(REGISTRY_PATH)
    counts: dict[str, int] = {}
    for task in registry["tasks"]:
        prefix = str(task["status"]).split("_", 1)[0]
        counts[prefix] = counts.get(prefix, 0) + 1
    return {
        "schema": "safehome.task35.report.v1",
        "version": registry["version"],
        "counts": counts,
        "tasks": [{"id": item["id"], "status": item["status"]} for item in registry["tasks"]],
        "engineering_complete_is_not_production_approval": True,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("plan", "run", "resume", "verify", "report"))
    args = parser.parse_args()
    result = report() if args.command in {"plan", "report"} else verify()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result.get("status") == "failed":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
