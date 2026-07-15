import importlib.util
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = PROJECT_ROOT / "backend" / "scripts" / "audit_task17_content.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("audit_task17_content", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


def test_task17_baseline_covers_all_current_content():
    module = _load_module()
    audit = module.build_audit(PROJECT_ROOT / "content")

    assert audit["counts"]["training_cards"] == 42
    assert audit["counts"]["courses"] == 5
    assert audit["counts"]["programs"] == 3
    assert audit["training_card_quality"]["cards_missing_governance_fields"] == []
    assert audit["course_structure_gaps"] == []
    assert audit["program_protocol_gaps"] == []
    assert all(item["review_status"] == "pilot_draft" for item in audit["program_governance"])


def test_task17_baseline_has_no_invalid_card_references():
    module = _load_module()
    audit = module.build_audit(PROJECT_ROOT / "content")

    assert audit["references"]["invalid"] == []
    assert audit == module.build_audit(PROJECT_ROOT / "content")


def test_task17_card_quality_deterministic_fixes_are_clean():
    module = _load_module()
    audit = module.build_audit(PROJECT_ROOT / "content")
    quality = audit["training_card_quality"]

    assert quality["duplicate_tags"] == []
    assert quality["cards_with_three_dots"] == []
    assert quality["user_titles_with_internal_acronyms"] == []
