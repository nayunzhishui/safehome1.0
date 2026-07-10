import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _auditor():
    path = ROOT / "backend" / "scripts" / "audit_miniprogram_frontend.py"
    spec = importlib.util.spec_from_file_location("miniprogram_frontend_auditor", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_miniprogram_pages_components_and_sensitive_ui_contracts():
    result = _auditor().audit()
    assert result["pages"] >= 37
    assert result["canvas_count"] >= 6
    assert result["ok"] is True, result["issues"]
