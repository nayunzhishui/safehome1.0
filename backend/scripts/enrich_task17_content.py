"""Idempotently add Task 17 governance metadata to content files."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONTENT_DIR = PROJECT_ROOT / "content"
CONTROLLED_CARD_IDS = {
    "sandplay_expression_01",
    "repair_after_rupture",
    "parent_after_conflict_repair",
}


def _read(filename: str) -> dict[str, Any]:
    return json.loads((CONTENT_DIR / filename).read_text(encoding="utf-8"))


def _write(filename: str, payload: dict[str, Any]) -> None:
    (CONTENT_DIR / filename).write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _mechanism(card: dict[str, Any]) -> str:
    text = " ".join(
        str(value)
        for value in (
            card.get("id"),
            card.get("type"),
            card.get("target_skill"),
            card.get("purpose"),
            " ".join(card.get("tags") or []),
        )
    ).lower()
    rules = (
        ("relationship_repair", ("repair", "修复", "冲突")),
        ("relationship_validation", ("validation", "nonjudgment", "确认", "开放问题", "倾听")),
        ("self_compassion", ("self_compassion", "self_support", "scs", "自我关怀", "自我支持")),
        ("behavior_change", ("behavior", "micro_start", "行动", "启动", "请求")),
        ("body_regulation", ("body", "grounding", "身体", "呼吸")),
        ("cognitive_flexibility", ("cognitive", "thought", "reappraisal", "想法", "解释")),
        ("emotion_awareness", ("emotion", "naming", "mindful", "觉察", "情绪")),
    )
    for code, keywords in rules:
        if any(keyword in text for keyword in keywords):
            return code
    return "supportive_practice"


def enrich_training_cards() -> None:
    payload = _read("training_cards.json")
    if payload.get("version") == "2026.07-training-cards-v3":
        payload["version"] = "2026.07-task17-governance-v1"
    payload.setdefault("governance_notice", "新增机制、剂量和安全字段为项目草案，正式试点前仍需心理负责人逐卡审核。")
    for card in payload.get("cards", []):
        duration = int(card.get("duration_minutes") or 5)
        controlled = card.get("id") in CONTROLLED_CARD_IDS
        additions = {
                "user_facing_title": card.get("title"),
                "mechanism_code": _mechanism(card),
                "target_constructs": [card.get("target_skill") or _mechanism(card)],
                "indications": list(card.get("suitable_for") or [card.get("suitable_scene") or "低风险支持性练习场景"]),
                "contraindications": list(card.get("not_suitable_for") or ["现实安全风险或需要立即人工支持的情况"]),
                "minimum_dose": {
                    "single_session_minutes": duration,
                    "suggested_frequency": "每周2至3次，可按个人节奏调整",
                    "initial_cycle_days": 7,
                },
                "completion_criteria": "完成至少一个核心步骤，并记录一句练习后的观察；页面浏览不计为完成。",
                "progression_criteria": "能够在低风险真实场景中重复完成后，再自主选择继续、巩固或更换练习；不适增加时降低难度或暂停。",
                "stop_rules": list(
                    dict.fromkeys(
                        [
                            *(card.get("not_suitable_for") or []),
                            "练习中不适明显增加、无法保持基本安全或出现自伤、他伤、暴力线索时立即停止并寻求现实支持。",
                        ]
                    )
                ),
                "fidelity_check": list((card.get("steps") or [])[:2]),
                "outcome_links": ["practice_completion", "self_rated_helpfulness", "post_practice_note"],
                "evidence_level": "project_draft",
                "safety_level": "controlled" if controlled else "standard",
                "release_policy": "manual_context_required" if controlled else "shared_choice_candidate",
                "governance_review_status": "manual_review_required",
            }
        for key, value in additions.items():
            card.setdefault(key, value)
    _write("training_cards.json", payload)


def enrich_training_map() -> None:
    payload = _read("assessment_training_map.json")
    if payload.get("version") == "2026.07-assessment-training-map-v2":
        payload["version"] = "2026.07-task17-candidate-map-v1"
    payload.setdefault("selection_policy", "每条规则只生成候选练习，用户可自主选择、稍后决定或由研究者受控调整。")
    for rule in payload.get("rules", []):
        additions = {
                "rule_version": "2026.07-task17-v1",
                "recommendation_mode": "candidate_set",
                "selection_policy": "shared_choice",
                "recommendation_source": "assessment_rule",
                "approval_status": "draft_requires_psychology_review",
                "allow_controlled_cards": False,
                "max_candidates": 3,
            }
        for key, value in additions.items():
            rule.setdefault(key, value)
    _write("assessment_training_map.json", payload)


def main() -> int:
    enrich_training_cards()
    enrich_training_map()
    print("Task 17 training-card governance metadata enriched.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
