import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
REGISTRY = ROOT / "content" / "therapeutic_assessment_pilot_evidence_registry.json"


def test_a3_formative_pilot_matrix_and_human_gates():
    payload = json.loads(REGISTRY.read_text(encoding="utf-8"))
    stage = next(item for item in payload["stages"] if item["id"] == "A3")
    domains = {item["id"] for item in stage["verification_domains"]}
    assert domains == {
        "workflow_state_machine",
        "permission_and_shared_scope",
        "reminders_and_privacy",
        "weak_network_and_recovery",
        "researcher_queue_and_workload",
        "cross_client_consistency",
        "participant_correction_withdrawal_complaint",
    }
    assert stage["entry_dependencies"] == [
        "A0_human_signoff_complete",
        "A1_human_interviews_complete",
        "A2_real_cases_and_supervision_complete",
        "all_severe_issues_closed",
    ]
    assert stage["required_device_matrix"] == ["wechat_devtools", "ios_real_device", "android_real_device"]
    assert stage["real_device_required"] is True
    assert stage["synthetic_or_automation_may_sign"] is False
    assert stage["formative_pilot_complete"] is False
    assert stage["human_entry_dependencies_complete"] is False
    assert stage["production_release_approved"] is False
    for domain in stage["verification_domains"]:
        assert domain["required_evidence"]
        for evidence_ref in domain["evidence_refs"]:
            assert (ROOT / evidence_ref).exists(), evidence_ref


def test_a3_runtime_evidence_covers_recovery_scope_and_issue_closure():
    payload = json.loads(REGISTRY.read_text(encoding="utf-8"))
    stage = next(item for item in payload["stages"] if item["id"] == "A3")
    fields = set(stage["required_runtime_evidence_fields"])
    assert {
        "shared_contract_hash",
        "device_and_os",
        "network_condition",
        "actor_role_and_object_scope",
        "recovery_result",
        "error_or_negative_event",
        "issue_owner",
        "closure_evidence",
    } <= fields
    assert stage["severe_issue_blocks_next_stage"] is True
