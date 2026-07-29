"""Task37-R04 artifact fingerprint, release note and observation evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
REGISTRY = ROOT / "content" / "task37_release_execution_registry.json"


def _stage() -> dict:
    payload = json.loads(REGISTRY.read_text(encoding="utf-8"))
    return next(item for item in payload["stages"] if item["id"] == "R04")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build() -> dict:
    stage = _stage()
    artifacts = []
    missing = []
    for relative in stage["fingerprint_artifacts"]:
        path = ROOT / relative
        if not path.exists():
            missing.append(relative)
            continue
        artifacts.append({"path": relative, "sha256": _sha256(path), "size_bytes": path.stat().st_size})
    canonical = json.dumps(artifacts, sort_keys=True, separators=(",", ":"))
    try:
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        commit = "unavailable"
    result = {
        "schema": "safehome.task37.r04-release-closure.v1",
        "source_commit": commit,
        "artifacts": artifacts,
        "artifact_set_sha256": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
        "missing_artifacts": missing,
        "release_note_sections": stage["release_note_sections"],
        "observation_windows": stage["observation_windows"],
        "observation_metrics": stage["observation_metrics"],
        "automatic_rollback_thresholds": stage["automatic_rollback_thresholds"],
        "rollback_actions": stage["rollback_actions"],
        "owner_approval_complete": False,
        "post_release_observation_complete": False,
        "production_release_executed": False,
        "production_release_approved": False,
    }
    result["ok"] = not missing and len(artifacts) == len(stage["fingerprint_artifacts"])
    return result


def plan() -> dict:
    stage = _stage()
    return {
        "action": "plan",
        "ok": True,
        "entry_dependencies": stage["entry_dependencies"],
        "owner_approval_required": stage["owner_approval_required"],
        "release_note_sections": stage["release_note_sections"],
        "production_release_executed": False,
    }


def rollback_plan() -> dict:
    stage = _stage()
    return {
        "action": "rollback-plan",
        "ok": True,
        "thresholds": stage["automatic_rollback_thresholds"],
        "actions": stage["rollback_actions"],
        "rollback_executed": False,
        "production_mutation_executed": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["plan", "build", "verify", "rollback-plan"])
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.action == "plan":
        result = plan()
    elif args.action in {"build", "verify"}:
        result = build()
        result["action"] = args.action
    else:
        result = rollback_plan()
    payload = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload + "\n", encoding="utf-8")
    print(payload)
    return 0 if result.get("ok", True) else 1


if __name__ == "__main__":
    raise SystemExit(main())
