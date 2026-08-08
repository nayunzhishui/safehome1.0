"""Print current operations-release artifact hashes without mutating files."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
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
        raw = target.read_bytes()
        rows.append(
            {
                "path": relative,
                "exists": True,
                "sha256": hashlib.sha256(raw).hexdigest(),
                "size_bytes": len(raw),
                "matches_manifest": hashlib.sha256(raw).hexdigest() == item.get("sha256"),
            }
        )
    print("SAFEHOME_RELEASE_HASHES=" + json.dumps(rows, ensure_ascii=False, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
