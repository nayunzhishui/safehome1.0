"""Read-only access to offline aggregate text-analysis outputs."""

from __future__ import annotations

import json
from pathlib import Path

from config import PROJECT_ROOT


OUTPUT_DIR = PROJECT_ROOT / "outputs" / "text_analysis"
ALLOWED_FILES = {
    "features": "text_features_summary.json",
    "network": "social_network_summary.json",
    "summary": "text_analysis_summary.json",
}


def _read_output(filename: str) -> dict:
    path = OUTPUT_DIR / filename
    if not path.exists():
        return {
            "available": False,
            "filename": filename,
            "reason": "offline_output_missing",
            "raw_text_included": False,
        }
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload.pop("records", None)
    payload["available"] = True
    payload["filename"] = filename
    payload["raw_text_included"] = False
    return payload


def load_text_analysis_summary() -> dict:
    return {
        key: _read_output(filename)
        for key, filename in ALLOWED_FILES.items()
    }
