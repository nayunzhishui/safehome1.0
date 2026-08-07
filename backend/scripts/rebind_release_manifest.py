"""Rebind only hash/size fields in the operations release manifest.

This tool deliberately cannot approve production release or change artifact
paths/types. It exists to make artifact drift explicit and reproducible after
reviewed source changes.

Examples:
    python backend/scripts/rebind_release_manifest.py --check
    python backend/scripts/rebind_release_manifest.py --apply
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "content" / "operations_release_manifest.json"


def _bound_payload(payload: dict) -> tuple[dict, list[dict]]:
    result = json.loads(json.dumps(payload))
    changes: list[dict] = []
    for artifact in result.get("artifacts", []):
        relative = str(artifact.get("path") or "")
        target = ROOT / relative
        if not target.is_file():
            raise FileNotFoundError(f"发布制品不存在: {relative}")
        raw = target.read_bytes()
        new_hash = hashlib.sha256(raw).hexdigest()
        new_size = len(raw)
        if artifact.get("sha256") != new_hash or artifact.get("size_bytes") != new_size:
            changes.append(
                {
                    "path": relative,
                    "old_sha256": artifact.get("sha256"),
                    "new_sha256": new_hash,
                    "old_size_bytes": artifact.get("size_bytes"),
                    "new_size_bytes": new_size,
                }
            )
        artifact["sha256"] = new_hash
        artifact["size_bytes"] = new_size

    # Safety invariant: a hash refresh can never turn a branch into an approved
    # production release. Existing false stays false; true is rejected.
    if result.get("production_release_approved") is True:
        raise RuntimeError("拒绝重绑：manifest 当前标记 production_release_approved=true，需要人工发布流程处理")
    result["production_release_approved"] = False
    return result, changes


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    before = json.loads(MANIFEST.read_text(encoding="utf-8"))
    after, changes = _bound_payload(before)
    print(json.dumps({"changed": bool(changes), "changes": changes}, ensure_ascii=False, indent=2))
    if args.check:
        return 1 if changes else 0
    if changes:
        MANIFEST.write_text(json.dumps(after, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
