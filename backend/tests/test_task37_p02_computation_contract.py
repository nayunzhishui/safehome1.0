import importlib
import json
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"


def _service():
    sys.path.insert(0, str(BACKEND))
    sys.modules.pop("services.task37_contract_service", None)
    return importlib.import_module("services.task37_contract_service")


def _valid(entity_type: str = "Observation"):
    return {
        "contract_version": "safehome.computation.v1",
        "entity_type": entity_type,
        "id": "artifact-1",
        "purpose": "quality_evaluation",
        "consent_version": "2026.07-quality-v1",
        "source_version": "source-v1",
        "subject_scope": "individual",
        "time_window": {"start": "2026-07-01T00:00:00Z", "end": "2026-07-02T00:00:00Z"},
        "de_identification": "deidentified",
        "payload": {"summary": "非诊断观察"},
    }


def test_registry_has_six_contracts_and_output_governance_fields():
    payload = json.loads((ROOT / "content" / "task37_computation_contract.json").read_text(encoding="utf-8"))
    assert set(payload["entities"]) == {
        "Observation",
        "DerivedFeature",
        "ModelRun",
        "AnalysisArtifact",
        "Citation",
        "HumanReview",
    }
    for field in ("engine_version", "rule_version", "prompt_version", "knowledge_version", "thresholds", "coverage", "unknown_rate", "review_status", "withdrawal_status"):
        assert field in payload["governed_output_fields"]


@pytest.mark.parametrize("entity_type", ["Observation", "DerivedFeature", "ModelRun", "AnalysisArtifact", "Citation", "HumanReview"])
def test_all_six_new_entities_validate(entity_type):
    result = _service().validate_new_record(_valid(entity_type))
    assert result["entity_type"] == entity_type
    assert result["read_only"] is False


def test_unknown_field_version_and_missing_purpose_fail_closed():
    service = _service()
    for mutation, code in (
        ({"extra": True}, "unknown_fields"),
        ({"contract_version": "safehome.computation.v99"}, "unsupported_version"),
        ({"purpose": ""}, "required_field_missing"),
    ):
        record = _valid()
        record.update(mutation)
        with pytest.raises(service.ContractError) as exc:
            service.validate_new_record(record)
        assert exc.value.code == code


def test_legacy_record_is_readable_but_cannot_be_written():
    service = _service()
    legacy = service.read_record({"id": "old-1", "summary": "旧结果"})
    assert legacy["legacy"] is True
    assert legacy["read_only"] is True
    with pytest.raises(service.ContractError) as exc:
        service.validate_new_record({"id": "old-1", "summary": "旧结果"})
    assert exc.value.code == "unsupported_version"


def test_public_summary_endpoint_and_cross_client_contracts(tmp_path, monkeypatch):
    sys.path.insert(0, str(BACKEND))
    from test_consent_route import _fresh_app

    client = _fresh_app(tmp_path, monkeypatch).test_client()
    response = client.get("/api/research/computation-contract/public-status")
    assert response.status_code == 200
    data = response.get_json()["data"]
    assert data["contract_version"] == "safehome.computation.v1"
    assert len(data["entity_types"]) == 6
    assert data["writes_enabled"] is False

    shared = (ROOT / "shared" / "types" / "api.ts").read_text(encoding="utf-8")
    constants = (ROOT / "shared" / "constants" / "api.ts").read_text(encoding="utf-8")
    web = (ROOT / "apps" / "web" / "src" / "services" / "safehomeApi.ts").read_text(encoding="utf-8")
    mini = (ROOT / "apps" / "miniprogram" / "services" / "api.js").read_text(encoding="utf-8")
    assert "ComputationContractPublicStatus" in shared
    assert "computationContract" in constants
    assert "getComputationContractPublicStatus" in web
    assert "getComputationContractPublicStatus" in mini
