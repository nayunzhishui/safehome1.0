"""Read-only structural accessibility and page-state audit for the miniprogram."""

from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MINI = ROOT / "apps" / "miniprogram"


def main() -> None:
    app = json.loads((MINI / "app.json").read_text(encoding="utf-8"))
    failures: list[str] = []
    page_state_count = 0

    for page in app["pages"]:
        path = MINI / f"{page}.wxml"
        source = path.read_text(encoding="utf-8")
        if "aria-label=" not in source:
            failures.append(f"{page}: missing accessible name")
        page_state_count += int("<page-state" in source)
        for tag in re.findall(r"<view\b[^>]*(?:bindtap|catchtap)[^>]*>", source):
            if "role=" not in tag or "aria-label=" not in tag:
                failures.append(f"{page}: interactive view missing role or aria-label")

    if failures:
        raise SystemExit("Miniprogram UI governance failed:\n- " + "\n- ".join(failures))
    print(f"Miniprogram UI governance passed: {len(app['pages'])} pages named, {page_state_count} pages use page-state")


if __name__ == "__main__":
    main()
