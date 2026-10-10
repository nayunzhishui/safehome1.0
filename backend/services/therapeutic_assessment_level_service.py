"""Versioned public naming and service-level contract for therapeutic assessment."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from flask import current_app, has_app_context

from config import Config


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


def _app_env() -> str:
    if has_app_context():
        return str(current_app.config.get("APP_ENV") or "development").lower()
    return str(getattr(Config, "APP_ENV", "development") or "development").lower()


def human_review_intake_open() -> bool:
    """Whether participants may start a new L1–L3 human-review case.

    Human review needs named staff and committed response times.  Production
    keeps new intake closed until the release flag records that arrangement;
    local and synthetic environments stay open for verification.
    """

    if _app_env() != "production":
        return True
    return bool((registry().get("release") or {}).get("l1_l3_production_enabled"))


def public_status() -> dict:
    payload = registry()
    return {
        "human_review_open": human_review_intake_open(),
        "schema": payload["schema"],
        "version": payload["version"],
        "levels": [dict(item) for item in payload["levels"]],
        "current_default": level(payload["default_level"]),
        "production_max_without_human_chain": payload["production_max_without_human_chain"],
        "public_terms": list(payload["public_terms"]),
        "boundary_notice": "当前级别说明服务范围，不代表诊断、治疗承诺、疗效证明或人工资质已经通过。",
    }
