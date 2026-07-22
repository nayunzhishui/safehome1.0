import importlib.util
import json
import subprocess
import sys
from datetime import datetime, timezone
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


def test_prepare_supports_explicit_admin_account_without_logging_password(tmp_path):
    module = load_module()
    receipt_path = module.prepare(
        tmp_path / "admin.json",
        username="safehome1.0",
        role="admin",
        nickname="安心陪伴管理员",
    )
    payload = json.loads(receipt_path.read_text(encoding="utf-8"))

    assert payload["username"] == "safehome1.0"
    assert payload["role"] == "admin"
    assert payload["nickname"] == "安心陪伴管理员"
    assert len(payload["password"]) >= 20


def test_prepare_rejects_public_participant_roles(tmp_path):
    module = load_module()
    try:
        module.prepare(tmp_path / "parent.json", username="unsafe-parent", role="parent")
    except ValueError as exc:
        assert "只允许" in str(exc)
    else:
        raise AssertionError("bootstrap must not create participant roles")


def test_prepare_records_expiring_receipt_environment_and_explicit_operation(tmp_path):
    module = load_module()
    receipt_path = module.prepare(
        tmp_path / "researcher.json",
        target_environment="test_cloud",
        operation="create",
    )
    payload = json.loads(receipt_path.read_text(encoding="utf-8"))

    assert payload["schema"] == "safehome.one_time_credential.v1"
    assert payload["receipt_id"].startswith("credential_receipt_")
    assert payload["target_environment"] == "test_cloud"
    assert payload["operation"] == "create"
    created = datetime.fromisoformat(payload["created_at"])
    expires = datetime.fromisoformat(payload["expires_at"])
    assert created.tzinfo == timezone.utc
    assert expires.tzinfo == timezone.utc
    assert 23 * 60 * 60 <= (expires - created).total_seconds() <= 24 * 60 * 60


def test_apply_rejects_expired_receipt_before_network_call(tmp_path):
    module = load_module()
    receipt_path = module.prepare(tmp_path / "expired.json", target_environment="production")
    payload = json.loads(receipt_path.read_text(encoding="utf-8"))
    payload["expires_at"] = "2020-01-01T00:00:00+00:00"
    receipt_path.write_text(json.dumps(payload), encoding="utf-8")

    try:
        module.apply(receipt_path, module.DEFAULT_BASE_URL, "admin-token-placeholder")
    except ValueError as exc:
        assert "已过期" in str(exc)
    else:
        raise AssertionError("expired receipt must be rejected before provisioning")


def test_rotate_requires_receipt_explicitly_prepared_for_rotation(tmp_path):
    module = load_module()
    create_receipt = module.prepare(tmp_path / "create.json", operation="create")
    try:
        module.rotate(create_receipt, "http://127.0.0.1:5050", "local-admin-token")
    except ValueError as exc:
        assert "rotate" in str(exc)
    else:
        raise AssertionError("rotation must require an explicit rotate receipt")


def test_verify_and_revoke_require_admin_token_without_reading_receipt(tmp_path):
    module = load_module()
    for operation in (
        lambda: module.verify("safehome_researcher_01", "http://127.0.0.1:5050", ""),
        lambda: module.revoke("safehome_researcher_01", "http://127.0.0.1:5050", ""),
    ):
        try:
            operation()
        except ValueError as exc:
            assert "ADMIN_EXPORT_TOKEN" in str(exc)
        else:
            raise AssertionError("admin token must be required")


def test_cli_exposes_prepare_apply_verify_revoke_and_rotate_commands():
    script = ROOT / "backend/scripts/bootstrap_researcher.py"
    completed = subprocess.run(
        [sys.executable, str(script), "--help"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0
    for command in ("prepare", "apply", "verify", "revoke", "rotate"):
        assert command in completed.stdout
