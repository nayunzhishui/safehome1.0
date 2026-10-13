"""Fail when the shared experience-token contract drifts from either client."""

from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TOKEN_PATH = ROOT / "shared" / "design" / "experience-tokens.json"
MINI_CSS = ROOT / "apps" / "miniprogram" / "app.wxss"
WEB_CSS = ROOT / "apps" / "web" / "src" / "styles.css"
APP_JSON = ROOT / "apps" / "miniprogram" / "app.json"


def _variables(source: str) -> dict[str, str]:
    return {
        name: value.strip()
        for name, value in re.findall(r"--(experience-[a-z-]+)\s*:\s*([^;]+);", source)
    }


def _expected(tokens: dict, client: str) -> dict[str, str]:
    unit = "rpx" if client == "miniprogram" else "px"
    size_key = "miniprogram_rpx" if client == "miniprogram" else "web_px"
    palette = tokens.get("miniprogram_color", tokens["color"]) if client == "miniprogram" else tokens["color"]
    values = {f"experience-{name.replace('_', '-')}": value for name, value in palette.items()}
    values["experience-touch"] = f'{tokens["touch_target"][size_key]}{unit}'
    for name, config in tokens["type"].items():
        values[f"experience-font-{name.replace('_', '-')}"] = f"{config[size_key]}{unit}"
    return values


def main() -> None:
    tokens = json.loads(TOKEN_PATH.read_text(encoding="utf-8"))
    failures: list[str] = []
    for client, path in (("miniprogram", MINI_CSS), ("web", WEB_CSS)):
        actual = _variables(path.read_text(encoding="utf-8"))
        for name, expected in _expected(tokens, client).items():
            if actual.get(name) != expected:
                failures.append(f"{client}: --{name} expected {expected!r}, got {actual.get(name)!r}")

    app = json.loads(APP_JSON.read_text(encoding="utf-8"))
    mini_primary = tokens.get("miniprogram_color", tokens["color"])["primary"]
    if app["tabBar"]["selectedColor"].lower() != mini_primary.lower():
        failures.append("miniprogram: tabBar.selectedColor does not match the miniprogram primary colour")

    if failures:
        raise SystemExit("Design token drift:\n- " + "\n- ".join(failures))
    print("Design token contract passed: shared -> Web + miniprogram")


if __name__ == "__main__":
    main()
