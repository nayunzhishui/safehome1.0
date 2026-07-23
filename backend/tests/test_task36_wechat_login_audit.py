import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_task36_wechat_login_audit_is_redacted_and_passes():
    result = subprocess.run(
        [sys.executable, "scripts/audit_task36_wechat_login.py"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert payload["status"] == "passed"
    assert payload["engineering_complete"] is True
    assert payload["release_approved"] is False
    assert payload["production_mutations_executed"] is False
    assert payload["checks"]["project_identity"]["passed"] is True
    assert payload["checks"]["explicit_header_trust"]["passed"] is True
    assert payload["checks"]["password_fallback"]["passed"] is True
    assert payload["checks"]["capability_contract"]["passed"] is True
    assert payload["external_gates_pending"] == [
        "cloudbase_security_package_release",
        "public_header_spoof_negative_probe",
        "cloudbase_egress_or_vpc_nat",
        "wechat_devtools_first_and_repeat_login",
        "android_ios_real_device",
        "disabled_account_and_token_expiry",
    ]
    serialized = json.dumps(payload, ensure_ascii=False)
    assert "WECHAT_SECRET" not in serialized
    assert "AppSecret" not in serialized
    assert "openid" not in serialized.lower()


def test_task36_registry_marks_header_trust_as_frozen_false():
    registry = json.loads((ROOT / "config" / "task36_registry.json").read_text(encoding="utf-8"))
    flags = {item["id"]: item for item in registry["baseline"]["feature_flags"]}
    trust = flags["trust_cloudbase_identity_headers"]

    assert trust["frozen_value"] is False
    assert trust["formal_permission_evidence"] is False
    assert "TRUST_CLOUDBASE_IDENTITY_HEADERS=1" in registry["policy"]["forbidden_command_terms"]
