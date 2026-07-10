import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _generator():
    path = ROOT / "backend" / "scripts" / "generate_relationship_ui_contract.py"
    spec = importlib.util.spec_from_file_location("relationship_ui_generator", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_relationship_ui_generated_helpers_are_up_to_date():
    module = _generator()
    for path, expected in module.outputs().items():
        assert path.read_text(encoding="utf-8") == expected
