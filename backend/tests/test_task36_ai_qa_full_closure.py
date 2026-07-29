import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_f15_governance_keeps_participant_and_external_provider_closed():
    governance = json.loads((ROOT / "content" / "ai_qa_governance.json").read_text(encoding="utf-8"))
    controls = governance["engineering_controls"]
    assert controls["roles"] == ["researcher", "supervisor", "admin"]
    assert controls["approved_knowledge_only"] is True
    assert controls["citation_and_version_required"] is True
    assert controls["uncertainty_required"] is True
    assert controls["participant_formal_feedback_write_allowed"] is False
    assert controls["provider_adapter"]["external_enabled"] is False
    assert controls["participant_enabled"] is False
    assert "diagnosis" in controls["fixed_refusal_categories"]
    assert "prompt_injection" in controls["fixed_refusal_categories"]


def test_f15_source_contains_provider_and_deletion_guards():
    service = (ROOT / "backend" / "services" / "ai_qa_service.py").read_text(encoding="utf-8")
    assert "AI_QA_PROVIDER_RETRIES" in service
    assert "AI_QA_TIMEOUT_MS" in service
    assert "claim_circuit_permission" in service
    assert "record_circuit_outcome" in service
    assert "AI_QA_DAILY_BUDGET_MICROS" in service
    assert "purge_expired_synthetic_data" in service
    assert "formal_feedback_write_allowed" in service
    assert "uncertainty" in service
