"""Audit mini-program page/component structure and high-risk UI regressions."""

from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MINIPROGRAM = ROOT / "apps" / "miniprogram"
REQUIRED_PAGE_SUFFIXES = (".js", ".json", ".wxml", ".wxss")
INTERNAL_TEXT_PATTERNS = ("WECHAT_SECRET", "WECHAT_APPID", "debugMessage", "model_center", "cluster_centers")
EVENT_PATTERN = re.compile(r"(?:bind|catch)(?:tap|input|change|getphonenumber|touchstart|touchmove|touchend|submit)=[\"']([A-Za-z_$][\w$]*)[\"']")
CANVAS_PATTERN = re.compile(r"<canvas\b.*?</canvas>", re.IGNORECASE | re.DOTALL)
EMPTY_BUTTON_PATTERN = re.compile(r"<button\b[^>]*>\s*</button>", re.IGNORECASE | re.DOTALL)


def _component_base(page_base: Path, value: str) -> Path | None:
    if not value or value.startswith("plugin://") or "{{" in value:
        return None
    if value.startswith("/"):
        return MINIPROGRAM / value.lstrip("/")
    return (page_base.parent / value).resolve()


def audit() -> dict:
    app = json.loads((MINIPROGRAM / "app.json").read_text(encoding="utf-8"))
    pages = app.get("pages", [])
    issues: list[str] = []
    component_refs = 0
    canvas_count = 0

    for page in pages:
        base = MINIPROGRAM / page
        for suffix in REQUIRED_PAGE_SUFFIXES:
            if not base.with_suffix(suffix).exists():
                issues.append(f"missing_page_file:{page}{suffix}")
        json_path = base.with_suffix(".json")
        wxml_path = base.with_suffix(".wxml")
        js_path = base.with_suffix(".js")
        if not json_path.exists() or not wxml_path.exists() or not js_path.exists():
            continue
        config = json.loads(json_path.read_text(encoding="utf-8"))
        for name, value in (config.get("usingComponents") or {}).items():
            component_refs += 1
            component = _component_base(base, value)
            if component is None:
                continue
            for suffix in REQUIRED_PAGE_SUFFIXES:
                if not component.with_suffix(suffix).exists():
                    issues.append(f"missing_component_file:{page}:{name}:{value}{suffix}")
        wxml = wxml_path.read_text(encoding="utf-8")
        js = js_path.read_text(encoding="utf-8")
        for pattern in INTERNAL_TEXT_PATTERNS:
            if pattern in wxml:
                issues.append(f"internal_text_exposed:{page}:{pattern}")
        if EMPTY_BUTTON_PATTERN.search(wxml):
            issues.append(f"empty_button:{page}")
        for canvas_tag in CANVAS_PATTERN.findall(wxml):
            canvas_count += 1
            if "aria-label=" not in canvas_tag and "aria-hidden=" not in canvas_tag:
                issues.append(f"canvas_without_text_alternative:{page}")
        if page.startswith("pages/relationship-"):
            for handler in EVENT_PATTERN.findall(wxml):
                if not re.search(rf"\b{re.escape(handler)}\s*\(", js):
                    issues.append(f"missing_relationship_handler:{page}:{handler}")

    return {
        "ok": not issues,
        "pages": len(pages),
        "component_references": component_refs,
        "canvas_count": canvas_count,
        "issues": issues,
    }


def main() -> None:
    result = audit()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if not result["ok"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
