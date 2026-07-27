import importlib
import json
import sys
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = PROJECT_ROOT / "backend"
CONTENT_PATH = PROJECT_ROOT / "content" / "task37_data_use_governance.json"


def _service():
    sys.path.insert(0, str(BACKEND_ROOT))
    sys.modules.pop("services.task37_data_use_service", None)
    return importlib.import_module("services.task37_data_use_service")


def test_governance_registers_three_domains_and_four_separate_purposes():
    payload = json.loads(CONTENT_PATH.read_text(encoding="utf-8"))

    assert payload["schema_version"] == "safehome.task37-data-use-governance.v1"
    assert set(payload["domains"]) == {"affective_computing", "group_sna", "controlled_ai"}
    assert set(payload["data_purposes"]) == {
        "service_delivery",
        "quality_evaluation",
        "model_training",
        "secondary_research",
    }
    assert payload["data_purposes"]["model_training"]["default_selected"] is False
    assert payload["data_purposes"]["model_training"]["service_access_condition"] is False
    assert payload["data_purposes"]["secondary_research"]["separate_authorization"] is True


def test_all_domains_freeze_intended_and_prohibited_uses():
    payload = json.loads(CONTENT_PATH.read_text(encoding="utf-8"))

    for domain in payload["domains"].values():
        assert domain["intended_uses"]
        assert {
            "clinical_diagnosis",
            "personality_labeling",
            "relationship_quality_ranking",
            "automatic_crisis_action",
        }.issubset(domain["prohibited_uses"])

    risk = payload["domains"]["affective_computing"]["risk_shadow_signal"]
    assert risk == {
        "enabled_for_human_review_queue": True,
        "participant_visible_conclusion": False,
        "automatic_action": False,
        "label": "需要真人了解",
    }


def test_templates_cover_data_model_prompt_and_public_source_cards():
    payload = json.loads(CONTENT_PATH.read_text(encoding="utf-8"))

    assert set(payload["card_templates"]) == {
        "data_card",
        "model_card",
        "prompt_card",
        "public_source_card",
    }
    for template in payload["card_templates"].values():
        assert "id" in template["required_fields"]
        assert "version" in template["required_fields"]
        assert "owner" in template["required_fields"]
        assert "prohibited_uses" in template["required_fields"]
        assert "rollback" in template["required_fields"]


def test_training_real_participant_text_requires_explicit_current_opt_in():
    service = _service()

    with pytest.raises(service.DataUseDenied) as exc_info:
        service.authorize_data_use(
            {
                "domain": "affective_computing",
                "purpose": "model_training",
                "source_kind": "participant_text",
                "contains_identifiable_data": False,
                "consent": {"agreed": False, "version": "2026.07-training-v1"},
            }
        )
    assert exc_info.value.code == "explicit_opt_in_required"

    allowed = service.authorize_data_use(
        {
            "domain": "affective_computing",
            "purpose": "model_training",
            "source_kind": "participant_text",
            "contains_identifiable_data": False,
            "consent": {
                "agreed": True,
                "version": "2026.07-training-v1",
                "purpose": "model_training",
                "revoked": False,
            },
        }
    )
    assert allowed["allowed"] is True
    assert allowed["purpose"] == "model_training"


def test_synthetic_training_does_not_invent_participant_consent_but_requires_rights():
    service = _service()

    with pytest.raises(service.DataUseDenied) as exc_info:
        service.authorize_data_use(
            {
                "domain": "affective_computing",
                "purpose": "model_training",
                "source_kind": "synthetic",
                "rights_status": "unknown",
                "contains_identifiable_data": False,
            }
        )
    assert exc_info.value.code == "source_rights_not_approved"

    allowed = service.authorize_data_use(
        {
            "domain": "affective_computing",
            "purpose": "model_training",
            "source_kind": "synthetic",
            "rights_status": "approved_project_owned",
            "contains_identifiable_data": False,
        }
    )
    assert allowed["allowed"] is True
    assert allowed["consent_basis"] == "not_applicable_no_participant_data"


def test_group_sna_rejects_individual_score_and_relationship_ranking():
    service = _service()

    for requested_use in ("individual_risk_score", "relationship_quality_ranking"):
        with pytest.raises(service.DataUseDenied) as exc_info:
            service.authorize_data_use(
                {
                    "domain": "group_sna",
                    "purpose": "service_delivery",
                    "requested_use": requested_use,
                    "source_kind": "participant_network",
                    "contains_identifiable_data": False,
                    "consent": {
                        "agreed": True,
                        "version": "2026.07-service-v1",
                        "purpose": "service_delivery",
                        "revoked": False,
                    },
                }
            )
        assert exc_info.value.code == "prohibited_use"


def test_unknown_domain_purpose_and_consent_purpose_fail_closed():
    service = _service()

    with pytest.raises(service.DataUseDenied, match="未知计算领域"):
        service.authorize_data_use({"domain": "unknown", "purpose": "service_delivery"})
    with pytest.raises(service.DataUseDenied, match="未知数据用途"):
        service.authorize_data_use({"domain": "controlled_ai", "purpose": "marketing"})
    with pytest.raises(service.DataUseDenied) as exc_info:
        service.authorize_data_use(
            {
                "domain": "controlled_ai",
                "purpose": "quality_evaluation",
                "source_kind": "participant_text",
                "contains_identifiable_data": False,
                "consent": {
                    "agreed": True,
                    "version": "2026.07-training-v1",
                    "purpose": "model_training",
                    "revoked": False,
                },
            }
        )
    assert exc_info.value.code == "consent_purpose_mismatch"


def test_consent_route_accepts_separate_data_purpose_types():
    consent_source = (BACKEND_ROOT / "routes" / "consent.py").read_text(encoding="utf-8")
    for consent_type in (
        "service_data",
        "quality_evaluation",
        "model_training",
        "secondary_research",
    ):
        assert f'"{consent_type}"' in consent_source
