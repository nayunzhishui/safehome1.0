"""Cross-platform syntax validation for miniprogram JavaScript and JSON assets."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
MINIPROGRAM_ROOT = PROJECT_ROOT / "apps" / "miniprogram"


def main() -> int:
    js_files = sorted(MINIPROGRAM_ROOT.rglob("*.js"))
    json_files = sorted(MINIPROGRAM_ROOT.rglob("*.json"))

    for path in js_files:
        subprocess.run(["node", "--check", str(path)], check=True)
    for path in json_files:
        with path.open("r", encoding="utf-8") as handle:
            json.load(handle)

    print(json.dumps({"ok": True, "js_files": len(js_files), "json_files": len(json_files)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
