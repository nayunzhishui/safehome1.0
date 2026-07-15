import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def load_module():
    path = ROOT / "backend/scripts/bootstrap_researcher.py"
    spec = importlib.util.spec_from_file_location("bootstrap_researcher", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_prepare_researcher_receipt_uses_fixed_username_and_strong_one_time_password(tmp_path):
    module = load_module()
    receipt_path = module.prepare(tmp_path / "researcher.json")
    payload = json.loads(receipt_path.read_text(encoding="utf-8"))

    assert payload["username"] == "safehome_researcher_01"
    assert payload["role"] == "researcher"
    assert payload["status"] == "pending_cloud_provision"
    assert len(payload["password"]) >= 20
    assert payload["password"] != "password123"


def test_apply_researcher_receipt_requires_admin_token(tmp_path):
    module = load_module()
    receipt_path = module.prepare(tmp_path / "researcher.json")

    try:
        module.apply(receipt_path, "https://example.invalid", "")
    except ValueError as exc:
        assert "ADMIN_EXPORT_TOKEN" in str(exc)
    else:
        raise AssertionError("missing admin token must block researcher provisioning")
