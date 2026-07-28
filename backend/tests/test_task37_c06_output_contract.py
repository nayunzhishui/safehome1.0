import json
import sys
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = PROJECT_ROOT / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))


def _citation(**overrides):
    item = {
        "content_id": "pause",
        "version_id": "version-approved",
        "release_id": "release-approved",
        "source_ref": "safehome://training_cards/pause",
        "governance_status": "published",
        "rights_status": "owned",
        "review_status": "approved",
        "title": "三秒暂停",
        "excerpt": "情绪升高时先暂停，慢慢呼气，再选择一个低负担回应。",
    }
    item.update(overrides)
    return item


def _output(**overrides):
    item = {
        "schema_version": "safehome.ai-qa-output.v1",
        "answer": "[S1] 已批准材料建议情绪升高时先暂停并慢慢呼气。",
        "citation_refs": ["S1"],
        "uncertainty": "medium",
        "evidence_status": "sufficient",
        "boundary_notice": "这是供研究者核对的支持性草稿，不构成诊断或治疗建议。",
        "human_verification_required": True,
    }
    item.update(overrides)
    return item


def _context(**overrides):
    item = {
        "permission_granted": True,
        "consent_active": True,
        "recipient_matches_scope": True,
        "responsible_role": "ai_safety_pipeline",
        "publisher_id": "researcher-c06",
        "actor_id": "researcher-c06",
        "automatic_adoption_allowed": False,
    }
    item.update(overrides)
    return item


def test_valid_structured_output_passes_all_five_gates():
    from services.ai_qa_output_gate_service import evaluate_ai_output

    result = evaluate_ai_output(
        json.dumps(_output(), ensure_ascii=False),
        [_citation()],
        _context(),
    )

    assert result["ok"] is True
    assert result["candidate"]["answer"].startswith("[S1]")
    assert result["gates"] == {
        "minimum_input": "passed",
        "permission": "passed",
        "source": "passed",
        "language": "passed",
        "responsibility": "passed",
    }
    assert result["grounding"]["heuristic_not_factuality"] is True


def test_non_json_extra_fields_and_missing_contract_fail_minimum_gate():
    from services.ai_qa_output_gate_service import evaluate_ai_output

    malformed = evaluate_ai_output(
        "这不是JSON",
        [_citation()],
        _context(),
    )
    extra = evaluate_ai_output(
        json.dumps(_output(system_prompt="secret"), ensure_ascii=False),
        [_citation()],
        _context(),
    )

    assert malformed["ok"] is False
    assert malformed["gates"]["minimum_input"] == "blocked"
    assert "invalid_json" in malformed["violations"]
    assert extra["ok"] is False
    assert "schema_validation_failed" in extra["violations"]


def test_permission_gate_cannot_be_satisfied_by_model_output():
    from services.ai_qa_output_gate_service import evaluate_ai_output

    result = evaluate_ai_output(
        json.dumps(_output(), ensure_ascii=False),
        [_citation()],
        _context(permission_granted=False),
    )

    assert result["gates"]["permission"] == "blocked"
    assert "permission_or_scope_denied" in result["violations"]


def test_source_gate_rejects_missing_mismatched_or_unauthorized_citations():
    from services.ai_qa_output_gate_service import evaluate_ai_output

    missing = evaluate_ai_output(
        json.dumps(_output(citation_refs=["S2"]), ensure_ascii=False),
        [_citation()],
        _context(),
    )
    unauthorized = evaluate_ai_output(
        json.dumps(_output(), ensure_ascii=False),
        [_citation(governance_status="draft")],
        _context(),
    )

    assert missing["gates"]["source"] == "blocked"
    assert "citation_reference_invalid" in missing["violations"]
    assert unauthorized["gates"]["source"] == "blocked"
    assert "source_not_authorized" in unauthorized["violations"]


@pytest.mark.parametrize(
    ("answer", "expected"),
    [
        ("[S1] 可以确诊你有抑郁症。", "diagnostic_language"),
        ("[S1] 保证坚持练习一定会改善。", "guarantee_language"),
        ("[S1] 都是你不够努力造成的。", "blame_language"),
        ("[S1] 你马上会伤害别人。", "risk_conclusion_language"),
        ("[S1] 你的人格类型就是回避型。", "conclusion_language"),
    ],
)
def test_language_gate_blocks_each_forbidden_output_family(answer, expected):
    from services.ai_qa_output_gate_service import evaluate_ai_output

    result = evaluate_ai_output(
        json.dumps(_output(answer=answer), ensure_ascii=False),
        [_citation()],
        _context(),
    )

    assert result["gates"]["language"] == "blocked"
    assert expected in result["violations"]


def test_responsibility_gate_requires_server_owned_chain_and_human_review_flag():
    from services.ai_qa_output_gate_service import evaluate_ai_output

    result = evaluate_ai_output(
        json.dumps(_output(), ensure_ascii=False),
        [_citation()],
        _context(publisher_id="other-actor"),
    )

    assert result["gates"]["responsibility"] == "blocked"
    assert "responsibility_chain_incomplete" in result["violations"]


def test_contract_schema_is_versioned_and_forbids_additional_properties():
    schema = json.loads(
        (
            PROJECT_ROOT
            / "content"
            / "ai_qa_output_contract.schema.json"
        ).read_text(encoding="utf-8")
    )

    assert schema["$id"] == "safehome.ai-qa-output.v1"
    assert schema["additionalProperties"] is False
    assert set(schema["required"]) == {
        "schema_version",
        "answer",
        "citation_refs",
        "uncertainty",
        "evidence_status",
        "boundary_notice",
        "human_verification_required",
    }
