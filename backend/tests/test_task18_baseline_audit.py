import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def load_audit_module():
    path = ROOT / "scripts" / "audit_task18_baseline.py"
    spec = importlib.util.spec_from_file_location("task18_baseline_audit", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_task18_baseline_maps_all_screenshot_evidence_and_requirements():
    module = load_audit_module()

    assert len(module.SCREENSHOT_MAP) == 21
    assert len(module.REQUIREMENTS) == 12
    assert len(set(module.SCREENSHOT_MAP)) == 21


def test_task18_baseline_inventory_exposes_governance_conflicts():
    module = load_audit_module()
    payload = module.audit()

    inventory = payload["inventory"]
    assert inventory["worksheets"]["total"] > 0
    assert inventory["training_cards"]["total"] > 0
    assert inventory["courses"]["total"] > 0
    assert inventory["programs"]["total"] == 3
    assert isinstance(inventory["worksheets"]["governance_conflicts"], list)
    assert payload["release_policy"]["keep_hidden"]
