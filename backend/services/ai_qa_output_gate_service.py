"""Structured AI output contract and server-owned five-gate evaluation."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Literal

from jsonschema import Draft202012Validator
from pydantic import BaseModel, Extra, ValidationError, constr, validator

from services.ai_qa_prompt import validate_output


OUTPUT_SCHEMA_VERSION = "safehome.ai-qa-output.v1"
FIVE_GATES = (
    "minimum_input",
    "permission",
    "source",
    "language",
    "responsibility",
)
APPROVED_RIGHTS = {
    "owned",
    "licensed",
    "public_domain",
    "permission_recorded",
}
DIAGNOSTIC_TERMS = (
    "确诊",
    "诊断为",
    "抑郁症",
    "焦虑症",
    "多动症",
    "自闭症",
    "人格障碍",
)
GUARANTEE_TERMS = ("保证", "一定会改善", "必然改善", "肯定会好", "保证治愈")
BLAME_TERMS = (
    "都是你",
    "你不够努力",
    "是你的错",
    "家长太差",
    "孩子故意",
)
RISK_CONCLUSION_TERMS = (
    "马上会伤害",
    "一定会自杀",
    "肯定会失控",
    "必然伤害",
)
CONCLUSION_TERMS = (
    "人格类型就是",
    "人格类型是",
    "就是回避型",
    "就是焦虑型",
    "肯定是",
)


class AiQaStructuredOutput(BaseModel):
    schema_version: Literal["safehome.ai-qa-output.v1"]
    answer: constr(strip_whitespace=True, min_length=1, max_length=3000)
    citation_refs: list[constr(regex=r"^S[1-9][0-9]*$")]
    uncertainty: Literal["low", "medium", "high"]
    evidence_status: Literal["sufficient", "insufficient"]
    boundary_notice: constr(
        strip_whitespace=True,
        min_length=1,
        max_length=500,
    )
    human_verification_required: Literal[True]

    class Config:
        extra = Extra.forbid

    @validator("citation_refs", allow_reuse=True)
    def _citation_refs_valid(cls, value):
        if not value or len(value) > 10 or len(value) != len(set(value)):
            raise ValueError("citation_refs must contain 1-10 unique refs")
        return value


def _schema_path() -> Path:
    return (
        Path(__file__).resolve().parents[2]
        / "content"
        / "ai_qa_output_contract.schema.json"
    )


def load_output_schema() -> dict[str, Any]:
    return json.loads(_schema_path().read_text(encoding="utf-8"))


def get_output_gate_policy() -> dict[str, Any]:
    return {
        "schema_version": OUTPUT_SCHEMA_VERSION,
        "gates": list(FIVE_GATES),
        "structured_validation": ["pydantic", "json_schema"],
        "retry_allowed": False,
        "fixed_degradation": True,
        "grounding_method": "lexical_overlap_heuristic_v1",
        "grounding_is_factuality_check": False,
        "human_verification_required": True,
    }


def _matches(text: str, terms: tuple[str, ...]) -> bool:
    normalized = str(text or "").lower()
    return any(term.lower() in normalized for term in terms)


def _source_authorized(source: dict[str, Any]) -> bool:
    return bool(
        source.get("governance_status") == "published"
        and source.get("rights_status") in APPROVED_RIGHTS
        and source.get("review_status") == "approved"
        and source.get("version_id")
        and source.get("release_id")
        and source.get("source_ref")
    )


def _empty_result(violations: list[str]) -> dict[str, Any]:
    return {
        "ok": False,
        "candidate": None,
        "gates": {gate: "blocked" for gate in FIVE_GATES},
        "violations": sorted(set(violations)),
        "grounding": {
            "method": "lexical_overlap_heuristic_v1",
            "ratio": 0.0,
            "heuristic_not_factuality": True,
        },
        "retry_allowed": False,
        "fixed_degradation_required": True,
        "schema_version": OUTPUT_SCHEMA_VERSION,
    }


def evaluate_ai_output(
    raw_output: object,
    citations: list[dict[str, Any]],
    context: dict[str, Any],
) -> dict[str, Any]:
    if isinstance(raw_output, str):
        try:
            payload = json.loads(raw_output)
        except json.JSONDecodeError:
            return _empty_result(["invalid_json"])
    elif isinstance(raw_output, dict):
        payload = raw_output
    else:
        return _empty_result(["invalid_json"])

    schema_errors = sorted(
        Draft202012Validator(load_output_schema()).iter_errors(payload),
        key=lambda item: list(item.path),
    )
    try:
        candidate = AiQaStructuredOutput.parse_obj(payload)
    except ValidationError:
        candidate = None
    if schema_errors or candidate is None:
        return _empty_result(["schema_validation_failed"])

    item = candidate.dict()
    violations: list[str] = []
    gates = {gate: "passed" for gate in FIVE_GATES}

    if (
        not item["answer"]
        or not item["boundary_notice"]
        or item["human_verification_required"] is not True
    ):
        gates["minimum_input"] = "blocked"
        violations.append("minimum_input_incomplete")

    if not all(
        context.get(key) is True
        for key in (
            "permission_granted",
            "consent_active",
            "recipient_matches_scope",
        )
    ):
        gates["permission"] = "blocked"
        violations.append("permission_or_scope_denied")

    expected_refs = {
        f"S{index}" for index in range(1, len(citations) + 1)
    }
    answer_refs = {
        f"S{value}" for value in re.findall(r"\[S(\d+)\]", item["answer"])
    }
    submitted_refs = set(item["citation_refs"])
    if (
        not submitted_refs
        or not submitted_refs.issubset(expected_refs)
        or submitted_refs != answer_refs
    ):
        gates["source"] = "blocked"
        violations.append("citation_reference_invalid")
    if not citations or any(
        not _source_authorized(source) for source in citations
    ):
        gates["source"] = "blocked"
        violations.append("source_not_authorized")

    language_checks = (
        ("diagnostic_language", DIAGNOSTIC_TERMS),
        ("guarantee_language", GUARANTEE_TERMS),
        ("blame_language", BLAME_TERMS),
        ("risk_conclusion_language", RISK_CONCLUSION_TERMS),
        ("conclusion_language", CONCLUSION_TERMS),
    )
    for code, terms in language_checks:
        if _matches(item["answer"], terms):
            violations.append(code)
            gates["language"] = "blocked"
    grounding = validate_output(item["answer"], citations)
    if not grounding["ok"]:
        gates["language"] = "blocked"
        violations.extend(grounding["violations"])

    if (
        not str(context.get("responsible_role") or "").strip()
        or str(context.get("publisher_id") or "")
        != str(context.get("actor_id") or "")
        or context.get("automatic_adoption_allowed") is not False
        or item["human_verification_required"] is not True
    ):
        gates["responsibility"] = "blocked"
        violations.append("responsibility_chain_incomplete")

    return {
        "ok": not violations,
        "candidate": item,
        "gates": gates,
        "violations": sorted(set(violations)),
        "grounding": {
            "method": grounding["grounding_method"],
            "ratio": grounding["grounding_ratio"],
            "heuristic_not_factuality": True,
        },
        "retry_allowed": False,
        "fixed_degradation_required": bool(violations),
        "schema_version": OUTPUT_SCHEMA_VERSION,
    }
