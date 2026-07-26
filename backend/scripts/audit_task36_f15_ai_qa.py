"""Static acceptance for the T36-F15 controlled AI QA sandbox."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    governance = json.loads((ROOT / "content" / "ai_qa_governance.json").read_text(encoding="utf-8"))
    controls = governance["engineering_controls"]
    assert controls["participant_enabled"] is False
    assert controls["provider_adapter"]["external_enabled"] is False
    assert controls["approved_knowledge_only"] is True
    assert controls["citation_and_version_required"] is True
    assert controls["uncertainty_required"] is True
    assert controls["participant_formal_feedback_write_allowed"] is False
    print("T36-F15 controlled AI QA audit: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
