"""What each scale dimension looks at, and a short hint for where this answer falls.

Bands come from, in order: published cut-offs written in the guide, a profile
model's dimension norms (mean ± 0.5 SD), or the scale midpoint with a middle zone
of 10% of the range on each side. Training-card rules use the same thresholds, so
the result page never calls a score "middle" while the cards treat it as low.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from config import Config
from database import load_content_json

GUIDES_FILE = "assessment_dimension_guides.json"
NORM_Z = 0.5
MIDDLE_ZONE_RATIO = 0.1
# Profile models fitted on rescaled answers: map the norm back onto the stored raw
# scale. regulatory_focus_relationship_18 feeds the model 1 + (raw - 1) * 4 / 8.
NORM_TO_RAW = {"regulatory_focus_relationship_18": (2.0, -1.0)}


def _number(value) -> float | None:
    return float(value) if isinstance(value, (int, float)) and not isinstance(value, bool) else None


@lru_cache(maxsize=64)
def _norms(content_dir: str, worksheet_id: str) -> dict[str, tuple[float, float]]:
    directory = Path(content_dir) / "profiles"
    best: dict | None = None
    for path in sorted(directory.glob("*.json")) if directory.exists() else []:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if payload.get("worksheet_id") != worksheet_id or not (payload.get("radar_support") or {}).get("dimensions"):
            continue
        if best is None or int(payload.get("n_cases") or 0) > int(best.get("n_cases") or 0):
            best = payload
    if not best:
        return {}
    scale, offset = NORM_TO_RAW.get(worksheet_id, (1.0, 0.0))
    norms = {}
    for item in best["radar_support"]["dimensions"]:
        mean, std = _number(item.get("mean")), _number(item.get("std"))
        if item.get("code") and mean is not None and std and std > 0:
            norms[str(item["code"])] = (mean * scale + offset, std * scale)
    return norms


def dimension_norms(worksheet_id: str) -> dict[str, tuple[float, float]]:
    return _norms(str(Config.CONTENT_DIR), str(worksheet_id or ""))


def dimension_thresholds(worksheet: dict, code: str, score_range: tuple[float, float] | None = None, worksheet_id: str = "") -> dict | None:
    norm = dimension_norms(worksheet.get("id") or worksheet_id).get(code)
    if norm:
        mean, std = norm
        return {"support_below": round(mean - NORM_Z * std, 6), "high_above": round(mean + NORM_Z * std, 6), "basis": "norm"}
    # Imported here: the execution service imports training rules, which import this module.
    from services.assessment_execution_service import dimension_score_bounds

    bounds = score_range or dimension_score_bounds(worksheet).get(code)
    if not bounds or bounds[1] <= bounds[0]:
        return None
    middle = (bounds[0] + bounds[1]) / 2
    half = (bounds[1] - bounds[0]) * MIDDLE_ZONE_RATIO
    return {"support_below": round(middle - half, 6), "high_above": round(middle + half, 6), "basis": "scale_midpoint"}


def classify(worksheet: dict, code: str, score: float, guide: dict | None = None, score_range: tuple[float, float] | None = None) -> tuple[str, str] | None:
    cutoffs = (guide or {}).get("cutoffs")
    if cutoffs:
        if "low_below" in cutoffs and score < cutoffs["low_below"]:
            return "low", "cutoffs"
        if "high_at_least" in cutoffs and score >= cutoffs["high_at_least"]:
            return "high", "cutoffs"
        return "middle", "cutoffs"
    thresholds = dimension_thresholds(worksheet, code, score_range)
    if not thresholds:
        return None
    if score < thresholds["support_below"]:
        return "low", thresholds["basis"]
    if score > thresholds["high_above"]:
        return "high", thresholds["basis"]
    return "middle", thresholds["basis"]


def build_dimension_guides(worksheet: dict, dimensions: list) -> dict:
    """Definition, band and hint for each stored dimension of one result."""

    guides = load_content_json(GUIDES_FILE)
    entries = (guides.get("worksheets") or {}).get(worksheet.get("id"), {})
    items = []
    for dimension in dimensions if isinstance(dimensions, list) else []:
        code = str((dimension or {}).get("key") or "")
        guide = entries.get(code)
        if not guide:
            continue
        score = _number(dimension.get("score"))
        stored_range = dimension.get("score_range") or {}
        low, high = _number(stored_range.get("minimum")), _number(stored_range.get("maximum"))
        classified = classify(worksheet, code, score, guide, (low, high) if low is not None and high is not None else None) if score is not None else None
        band, basis = classified or (None, None)
        hints = guide.get("hints") or {}
        own_middle = band == "middle" and bool(hints.get("middle"))
        hint = hints.get(band) if band in {"low", "high"} or own_middle else (guides.get("middle_hint") if band == "middle" else None)
        labels = guide.get("band_labels") or guides.get("band_labels") or {}
        items.append(
            {
                "key": code,
                "definition": guide.get("definition"),
                "band": band,
                "band_label": labels.get(band) if band in {"low", "high"} or own_middle else None,
                "hint": hint,
                "basis": basis,
                "composite": bool(guide.get("composite")),
            }
        )
    return {"version": guides.get("version"), "boundary": guides.get("boundary"), "items": items}
