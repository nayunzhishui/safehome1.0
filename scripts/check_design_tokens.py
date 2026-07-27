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
    values = {f"experience-{name.replace('_', '-')}": value for name, value in tokens["color"].items()}
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
    if app["tabBar"]["selectedColor"].lower() != tokens["color"]["primary"].lower():
        failures.append("miniprogram: tabBar.selectedColor does not match color.primary")

    if failures:
        raise SystemExit("Design token drift:\n- " + "\n- ".join(failures))
    print("Design token contract passed: shared -> Web + miniprogram")


if __name__ == "__main__":
    main()
