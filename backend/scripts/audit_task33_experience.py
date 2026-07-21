"""Run deterministic Task 33 source-level accessibility and UX gates."""

from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MINI = ROOT / "apps" / "miniprogram"
WEB = ROOT / "apps" / "web" / "src"
REGISTRY = ROOT / "content" / "ux_experience_registry.json"
TOKENS = ROOT / "shared" / "design" / "experience-tokens.json"


def _rgb(value: str) -> tuple[int, int, int]:
    value = value.lstrip("#")
    return tuple(int(value[index:index + 2], 16) for index in (0, 2, 4))


def _luminance(value: str) -> float:
    channels = []
    for channel in _rgb(value):
        normalized = channel / 255
        channels.append(normalized / 12.92 if normalized <= 0.04045 else ((normalized + 0.055) / 1.055) ** 2.4)
    return channels[0] * 0.2126 + channels[1] * 0.7152 + channels[2] * 0.0722


def contrast(a: str, b: str) -> float:
    high, low = sorted((_luminance(a), _luminance(b)), reverse=True)
    return round((high + 0.05) / (low + 0.05), 2)


def audit() -> dict:
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    tokens = json.loads(TOKENS.read_text(encoding="utf-8"))
    app = json.loads((MINI / "app.json").read_text(encoding="utf-8"))
    web_source = "\n".join(path.read_text(encoding="utf-8") for path in WEB.rglob("*.tsx"))
    web_css = (WEB / "styles.css").read_text(encoding="utf-8")
    mini_css = (MINI / "app.wxss").read_text(encoding="utf-8")
    issues: dict[str, list[str]] = {name: [] for name in registry["automated_gates"]}

    mini_registry = {item["path"] for item in registry["pages"] if item["platform"] == "miniprogram"}
    if set(app["pages"]) != mini_registry:
        issues["accessible_name"].append("miniprogram_page_inventory_drift")

    if "--safe-touch: 88rpx" not in mini_css or "--safe-touch: 44px" not in web_css:
        issues["touch_target"].append("shared_touch_target_missing")

    colors = tokens["color"]
    if contrast(colors["ink"], colors["surface"]) < 4.5 or contrast(colors["muted"], colors["surface"]) < 4.5:
        issues["contrast"].append("core_text_contrast_below_wcag_aa")

    if ":focus-visible" not in web_css or "--safe-focus" not in web_css:
        issues["focus_visible"].append("web_focus_style_missing")
    if "prefers-reduced-motion: reduce" not in web_css or "prefers-reduced-motion: reduce" not in mini_css:
        issues["reduced_motion"].append("reduced_motion_missing")
    if "overflow-x: clip" not in web_css or "overflow-x: hidden" not in mini_css:
        issues["horizontal_overflow"].append("global_overflow_guard_missing")

    empty_button = re.compile(r"<button\b[^>]*>\s*</button>", re.I | re.S)
    for path in MINI.rglob("*.wxml"):
        source = path.read_text(encoding="utf-8")
        if empty_button.search(source):
            issues["accessible_name"].append(f"empty_button:{path.relative_to(ROOT)}")
        for canvas in re.findall(r"<canvas\b.*?</canvas>", source, flags=re.I | re.S):
            if "aria-label=" not in canvas and "aria-hidden=" not in canvas:
                issues["accessible_name"].append(f"unlabeled_canvas:{path.relative_to(ROOT)}")

    if "<h1" not in web_source or "<h2" not in web_source:
        issues["heading_order"].append("web_heading_structure_missing")
    if "<label" not in web_source or "aria-label" not in web_source:
        issues["form_association"].append("web_form_labels_missing")

    results = {
        name: {
            "status": "failed" if found else "passed",
            "checked": len(app["pages"]) + sum(1 for _ in WEB.rglob("*.tsx")),
            "issues": len(found),
            "artifact": "backend/scripts/audit_task33_experience.py",
        }
        for name, found in issues.items()
    }
    return {
        "ok": not any(issues.values()),
        "environment": "local_automated",
        "platform": "cross_platform",
        "viewport": "source_and_token_matrix",
        "registry_version": registry["version"],
        "results": results,
        "details": issues,
        "manual_gates_pending": [item["gate"] for item in registry["external_gates"]],
    }


def main() -> None:
    result = audit()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if not result["ok"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
