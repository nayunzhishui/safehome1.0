"""Read-only access to offline aggregate text-analysis outputs."""

from __future__ import annotations

import json
from pathlib import Path

from config import PROJECT_ROOT


OUTPUT_DIR = PROJECT_ROOT / "outputs" / "text_analysis"
ALLOWED_FILES = {
    "features": "text_features_summary.json",
    "semantic_network": "semantic_network_summary.json",
    "family_topology": "family_topology_audit_summary.json",
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
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {
            "available": False,
            "filename": filename,
            "reason": "offline_output_invalid",
            "quality_status": "validation_failed",
            "privacy_gate_passed": False,
            "raw_text_included": False,
        }
    payload.pop("records", None)
    record_count = payload.get("record_count", payload.get("input_edge_count", 0))
    quality_status = payload.get("quality_status")
    if not quality_status:
        quality_status = "empty" if not record_count else "validation_failed"
    privacy_passed = payload.get("privacy_gate_passed", payload.get("raw_text_included") is False)
    payload["quality_status"] = quality_status
    payload["privacy_gate_passed"] = bool(privacy_passed)
    payload["available"] = quality_status == "valid" and bool(privacy_passed)
    if quality_status != "valid":
        payload.setdefault("reason", f"offline_output_{quality_status}")
    payload["filename"] = filename
    payload["raw_text_included"] = False
    return payload


def load_text_analysis_summary() -> dict:
    return {
        key: _read_output(filename)
        for key, filename in ALLOWED_FILES.items()
    }
