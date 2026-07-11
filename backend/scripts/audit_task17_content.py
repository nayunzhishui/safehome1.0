"""Audit Task 17 training-card, course, and pilot-program content."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONTENT_DIR = PROJECT_ROOT / "content"
DEFAULT_OUTPUT = PROJECT_ROOT / "outputs" / "task17_content_baseline.json"

ACRONYM_PATTERN = re.compile(r"\b(?:PRFQ|ERQ|SCS|MAAS|UP|CBT|GMM|KMEANS)\b", re.IGNORECASE)
COURSE_REQUIRED_FIELDS = (
    "learning_objectives",
    "core_concept",
    "common_misconceptions",
    "worked_example",
    "counter_example",
    "knowledge_checks",
    "guided_practice",
    "transfer_task",
    "reflection_prompts",
    "booster_plan",
    "audience_adaptation",
    "review_status",
)
CARD_GOVERNANCE_FIELDS = (
    "mechanism_code",
    "target_constructs",
    "indications",
    "contraindications",
    "minimum_dose",
    "completion_criteria",
    "progression_criteria",
    "stop_rules",
    "fidelity_check",
    "outcome_links",
    "evidence_level",
    "user_facing_title",
)
PROGRAM_PROTOCOL_FIELDS = (
    "protocol_version",
    "inclusion_criteria",
    "exclusion_criteria",
    "pause_criteria",
    "exit_criteria",
    "minimum_dose",
    "completion_definition",
    "adverse_response_plan",
    "protocol_deviation_rule",
    "approval",
)


def _load(content_dir: Path, filename: str) -> dict[str, Any]:
    return json.loads((content_dir / filename).read_text(encoding="utf-8"))


def _contains_three_dots(value: Any) -> bool:
    if isinstance(value, str):
        return "..." in value
    if isinstance(value, list):
        return any(_contains_three_dots(item) for item in value)
    if isinstance(value, dict):
        return any(_contains_three_dots(item) for item in value.values())
    return False


def _missing_fields(item: dict[str, Any], fields: tuple[str, ...]) -> list[str]:
    return [field for field in fields if item.get(field) in (None, "", [])]


def _mechanism_for(card: dict[str, Any]) -> str:
    text = " ".join(
        str(value)
        for value in (
            card.get("id"),
            card.get("target_skill"),
            card.get("purpose"),
            " ".join(card.get("tags") or []),
        )
    ).lower()
    rules = (
        ("relationship_repair", ("repair", "修复", "冲突")),
        ("relationship_validation", ("validation", "nonjudgment", "确认", "倾听", "开放问题")),
        ("self_compassion", ("self_compassion", "self_support", "scs", "自我关怀", "自我支持")),
        ("behavior_change", ("behavior", "micro_start", "行动", "启动", "请求")),
        ("body_regulation", ("body", "grounding", "身体", "呼吸")),
        ("cognitive_flexibility", ("cognitive", "thought", "reappraisal", "想法", "解释")),
        ("emotion_awareness", ("emotion", "naming", "mindful", "觉察", "情绪")),
    )
    for mechanism, keywords in rules:
        if any(keyword in text for keyword in keywords):
            return mechanism
    return "other_support"


def build_audit(content_dir: Path = DEFAULT_CONTENT_DIR) -> dict[str, Any]:
    cards_payload = _load(content_dir, "training_cards.json")
    courses_payload = _load(content_dir, "courses.json")
    programs_payload = _load(content_dir, "programs.json")
    mapping_payload = _load(content_dir, "assessment_training_map.json")

    cards = cards_payload.get("cards", [])
    courses = courses_payload.get("courses", [])
    programs = programs_payload.get("programs", [])
    rules = mapping_payload.get("rules", [])
    card_ids = {card.get("id") for card in cards}

    duplicate_tags = []
    truncated_cards = []
    acronym_titles = []
    missing_boundaries = []
    mechanism_counts: Counter[str] = Counter()
    for card in cards:
        card_id = card.get("id")
        tags = card.get("tags") or []
        duplicates = sorted(tag for tag, count in Counter(tags).items() if count > 1)
        if duplicates:
            duplicate_tags.append({"card_id": card_id, "tags": duplicates})
        if _contains_three_dots(card):
            truncated_cards.append(card_id)
        if ACRONYM_PATTERN.search(str(card.get("title") or "")):
            acronym_titles.append(card_id)
        if not str(card.get("boundary_notice") or "").strip():
            missing_boundaries.append(card_id)
        mechanism_counts[_mechanism_for(card)] += 1

    references: dict[str, set[str]] = {card_id: set() for card_id in card_ids}
    invalid_references: list[dict[str, str]] = []

    def add_reference(source: str, card_id: str) -> None:
        if card_id in references:
            references[card_id].add(source)
        else:
            invalid_references.append({"source": source, "card_id": card_id})

    for course in courses:
        for card_id in course.get("relation_to_cards_or_programs") or []:
            add_reference(f"course:{course.get('id')}", card_id)
    for program in programs:
        for card_id in program.get("recommended_card_ids") or []:
            add_reference(f"program:{program.get('id')}", card_id)
    for rule in rules:
        for card_id in rule.get("recommended_card_ids") or []:
            add_reference(f"mapping:{rule.get('rule_id')}", card_id)

    course_gaps = [
        {"course_id": course.get("id"), "missing_fields": missing_fields}
        for course in courses
        if (missing_fields := _missing_fields(course, COURSE_REQUIRED_FIELDS))
    ]
    program_gaps = [
        {
            "program_id": program.get("id"),
            "review_status": program.get("review_status"),
            "measurement_status": (program.get("measurement_plan") or {}).get("status"),
            "missing_protocol_fields": missing_fields,
        }
        for program in programs
        if (missing_fields := _missing_fields(program, PROGRAM_PROTOCOL_FIELDS))
    ]

    return {
        "schema_version": "task17-baseline-v1",
        "source_versions": {
            "training_cards": cards_payload.get("version"),
            "courses": courses_payload.get("version"),
            "programs": programs_payload.get("version"),
            "assessment_training_map": mapping_payload.get("version"),
        },
        "counts": {
            "training_cards": len(cards),
            "enabled_training_cards": sum(bool(card.get("enabled", True)) for card in cards),
            "courses": len(courses),
            "programs": len(programs),
            "mapping_rules": len(rules),
        },
        "training_card_quality": {
            "duplicate_tags": duplicate_tags,
            "cards_with_three_dots": sorted(truncated_cards),
            "user_titles_with_internal_acronyms": sorted(acronym_titles),
            "cards_without_boundary_notice": sorted(missing_boundaries),
            "cards_missing_governance_fields": [
                {"card_id": card.get("id"), "missing_fields": missing_fields}
                for card in cards
                if (missing_fields := _missing_fields(card, CARD_GOVERNANCE_FIELDS))
            ],
        },
        "mechanism_coverage": dict(sorted(mechanism_counts.items())),
        "references": {
            "invalid": sorted(invalid_references, key=lambda item: (item["source"], item["card_id"])),
            "unreferenced_card_ids": sorted(card_id for card_id, sources in references.items() if not sources),
            "reference_counts": dict(sorted((card_id, len(sources)) for card_id, sources in references.items())),
        },
        "course_structure_gaps": course_gaps,
        "program_protocol_gaps": program_gaps,
        "program_governance": [
            {
                "program_id": program.get("id"),
                "protocol_version": program.get("protocol_version"),
                "review_status": program.get("review_status"),
                "measurement_status": (program.get("measurement_plan") or {}).get("status"),
                "approval_statuses": {
                    role: ((program.get("approval") or {}).get(role) or {}).get("status")
                    for role in ("research", "psychology", "ethics")
                },
            }
            for program in programs
        ],
        "classification": {
            "automatic_fixes": ["duplicate_tags", "verified_truncated_text", "invalid_references"],
            "psychology_review": ["mechanism_codes", "dose", "contraindications", "stop_rules", "course_content"],
            "research_review": ["program_protocol", "outcomes", "measurement_windows", "approval_status"],
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--content-dir", type=Path, default=DEFAULT_CONTENT_DIR)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--check", action="store_true", help="Do not write output; fail only on invalid references.")
    args = parser.parse_args()

    audit = build_audit(args.content_dir)
    if not args.check:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"Task 17 baseline written: {args.output}")
    print(json.dumps(audit["counts"], ensure_ascii=False))
    return 1 if audit["references"]["invalid"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
