"""Static closure audit for Task36 F17."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    registry = json.loads(
        (ROOT / "content" / "task36_reliability_security_registry.json").read_text(encoding="utf-8")
    )
    expected = {"messages", "checkins", "login", "research_analysis", "ai_qa", "therapeutic_assessment"}
    actual = {item["id"] for item in registry["journeys"]}
    assert actual == expected
    assert all(not value for value in registry["production_defaults"].values())
    assert registry["temporary_showcase_exception_is_evidence"] is False
    assert registry["formal_permission_acceptance_passed"] is False
    assert registry["production_release_approved"] is False
    assert {"password", "token", "cookie", "participant_text"} <= set(registry["forbidden_evidence_fields"])
    print("T36-F17 reliability/security closure audit: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
