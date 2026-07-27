"""Machine audit for Task 38 F01 service levels and public naming."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
REGISTRY = ROOT / "content" / "therapeutic_assessment_service_levels.json"


def main() -> int:
    payload = json.loads(REGISTRY.read_text(encoding="utf-8"))
    mini = (ROOT / "apps/miniprogram/pages/therapeutic-assessment/index.wxml").read_text(encoding="utf-8")
    web = (ROOT / "apps/web/src/pages/TherapeuticAssessmentWorkbench.tsx").read_text(encoding="utf-8")
    checks = {
        "four_levels": [item["id"] for item in payload.get("levels", [])] == ["L0", "L1", "L2", "L3"],
        "default_l0": payload.get("default_level") == "L0",
        "l0_not_formal": payload["levels"][0].get("formal_ta") is False,
        "l1_not_formal": payload["levels"][1].get("formal_ta") is False,
        "l3_formal": payload["levels"][3].get("formal_ta") is True,
        "production_l1_l3_disabled": payload.get("release", {}).get("l1_l3_production_enabled") is False,
        "mini_public_name": 'aria-label="支持性评估"' in mini,
        "web_public_name": "协作式评估工作台" in web,
        "level_visible_both": "service_level.display_name" in mini and "service_level.display_name" in web,
    }
    failed = sorted(key for key, value in checks.items() if not value)
    print(json.dumps({"task": "T38-F01", "checks": checks, "failed": failed}, ensure_ascii=False))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
