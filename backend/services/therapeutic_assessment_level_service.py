"""Versioned public naming and service-level contract for therapeutic assessment."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATH = ROOT / "content" / "therapeutic_assessment_service_levels.json"


@lru_cache(maxsize=1)
def registry() -> dict:
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))


def level(level_id: str) -> dict:
    item = next((entry for entry in registry()["levels"] if entry["id"] == level_id), None)
    if item is None:
        item = next(entry for entry in registry()["levels"] if entry["id"] == registry()["default_level"])
    return dict(item)


def public_status() -> dict:
    payload = registry()
    return {
        "schema": payload["schema"],
        "version": payload["version"],
        "levels": [dict(item) for item in payload["levels"]],
        "current_default": level(payload["default_level"]),
        "production_max_without_human_chain": payload["production_max_without_human_chain"],
        "public_terms": list(payload["public_terms"]),
        "boundary_notice": "当前级别说明服务范围，不代表诊断、治疗承诺、疗效证明或人工资质已经通过。",
    }
