"""Static acceptance audit for Task38-F06 participant flow."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MINI = ROOT / "apps" / "miniprogram"
STEPS = (
    "boundary",
    "issue",
    "recent-event",
    "resources",
    "sharing",
    "summary",
    "feedback-check",
    "action-review",
)


def main() -> int:
    app = json.loads((MINI / "app.json").read_text(encoding="utf-8"))
    pages = set(app.get("pages") or [])
    missing = []
    for step in STEPS:
        prefix = f"pages/therapeutic-assessment-{step}/index"
        if prefix not in pages:
            missing.append(prefix)
        for suffix in (".js", ".json", ".wxml"):
            if not (MINI / f"{prefix}{suffix}").exists():
                missing.append(f"{prefix}{suffix}")
    component = (MINI / "components/therapeutic-flow-step/index.wxml").read_text(encoding="utf-8")
    styles = (MINI / "components/therapeutic-flow-step/index.wxss").read_text(encoding="utf-8")
    factory = (MINI / "utils/therapeuticAssessmentParticipantFlow.js").read_text(encoding="utf-8")
    checks = {
        "eight_routes": not missing,
        "one_primary_step_component": "第 {{stepNumber}} / {{stepTotal}} 步" in component,
        "screen_reader_semantics": all(token in component for token in ('role="radiogroup"', 'aria-checked="', 'aria-live="polite"')),
        "touch_target_44px": "min-height: 88rpx" in styles,
        "comparison_keeps_original": "你的原话" in component and "系统整理" in component,
        "local_draft": "createResilientForm" in factory,
        "cross_device_draft": "saveTherapeuticAssessmentParticipantDraft" in factory,
        "complete_states": all(token in factory for token in ("offline", "expired", "withdrawn")),
        "sensitive_notification_copy_absent": "notification" not in factory.lower(),
    }
    result = {"status": "PASS" if all(checks.values()) else "FAIL", "checks": checks, "missing": missing}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
