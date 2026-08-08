"""Print current operations-release artifact hashes without mutating files."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from services.artifact_integrity_service import artifact_sha256, artifact_size_bytes  # noqa: E402

CONTENT = ROOT / "content"
MANIFEST = CONTENT / "operations_release_manifest.json"


def main() -> int:
    payload = json.loads(MANIFEST.read_text(encoding="utf-8"))
    rows = []
    for item in payload.get("artifacts", []):
        relative = str(item.get("path") or "")
        target = ROOT / relative
        if not target.is_file():
            rows.append({"path": relative, "exists": False})
            continue
        digest = artifact_sha256(target)
        rows.append(
            {
                "path": relative,
                "exists": True,
                "sha256": digest,
                "size_bytes": artifact_size_bytes(target),
                "matches_manifest": digest == item.get("sha256"),
            }
        )
    print("SAFEHOME_RELEASE_HASHES=" + json.dumps(rows, ensure_ascii=False, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
