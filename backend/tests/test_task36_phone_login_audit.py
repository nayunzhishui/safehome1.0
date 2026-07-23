import json
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_task36_phone_login_audit_is_redacted_and_passes():
    result = subprocess.run(
        [sys.executable, "scripts/audit_task36_phone_login.py"],
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
    assert payload["checks"]["privacy_minimization"]["passed"] is True
    assert payload["checks"]["account_conflict"]["passed"] is True
    assert payload["checks"]["capability_gating"]["passed"] is True
    assert payload["checks"]["authorization_recovery"]["passed"] is True
    assert payload["external_gates_pending"] == [
        "wechat_phone_qualification",
        "wechat_privacy_guideline_approval",
        "cloudbase_token_or_secret_configuration",
        "cloudbase_release",
        "wechat_devtools_authorize_deny_expired",
        "android_ios_real_device",
    ]
    serialized = json.dumps(payload, ensure_ascii=False)
    assert "WECHAT_SECRET" not in serialized
    assert "access_token" not in serialized
    assert re.search(r"(?<!\d)1[3-9]\d{9}(?!\d)", serialized) is None
