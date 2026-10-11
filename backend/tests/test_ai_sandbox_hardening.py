import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))


def test_every_ai_message_requires_explicit_synthetic_marker():
    from services.ai_qa_input_security_service import InputSecurityError, validate_message_payload

    for payload in ({"text": "整理合成案例"}, {"text": "整理合成案例", "synthetic_data": False}):
        with pytest.raises(InputSecurityError) as exc_info:
            validate_message_payload(payload, app_env="testing")
        assert exc_info.value.code == "synthetic_data_required"
        assert exc_info.value.details["participant_data_allowed"] is False

    accepted = validate_message_payload(
        {"text": "整理合成案例", "synthetic_data": True},
        app_env="testing",
    )
    assert accepted["synthetic_data"] is True


def test_ai_input_policy_explicitly_forbids_participant_data():
    from services.ai_qa_input_security_service import get_input_security_policy

    policy = get_input_security_policy()
    assert policy["participant_data_allowed"] is False
    assert policy["synthetic_data_required_every_message"] is True
    assert policy["write_tools_allowed"] is False
    assert policy["cross_session_memory"] is False


def test_provider_input_still_deidentifies_direct_identifiers():
    from services.ai_qa_input_security_service import prepare_provider_input

    result = prepare_provider_input(
        "合成案例手机号13800138000，邮箱example@example.com",
        [],
        audience="researcher",
    )
    assert "13800138000" not in result["question"]
    assert "example@example.com" not in result["question"]
    assert result["privacy"]["deidentified_count"] == 2
    assert result["privacy"]["participant_data_allowed"] is False
