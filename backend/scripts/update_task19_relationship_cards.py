"""Install the eight relationship-growth cards supplied for Task 19."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CONTENT = ROOT / "content"
BOUNDARY = "这张训练卡只提供关系情境中的支持性练习和自我观察，不构成诊断、治疗、危机干预或关系成败判断。"
STOP = ["练习中不适明显增加时暂停或降低难度。", "出现自伤、他伤、暴力、胁迫或现实安全风险时停止练习并优先寻求现实支持。"]


def _card(card_id: str, title: str, purpose: str, minutes: int, scenes: list[str], tags: list[str], steps: list[str], example: str, reflections: list[str], reminder: str) -> dict:
    return {
        "id": card_id,
        "type": "relationship_growth",
        "title": title,
        "user_facing_title": title,
        "purpose": purpose,
        "today_goal": purpose,
        "tags": ["relationship_growth", *tags],
        "steps": steps,
        "example": example,
        "example_phrase": example,
        "duration_minutes": minutes,
        "theory_source": "支持性认知行为练习与情绪调节",
        "target_skill": card_id,
        "mechanism_code": "relationship_growth_practice",
        "target_constructs": tags,
        "suitable_for": scenes,
        "suitable_scene": "；".join(scenes),
        "indications": scenes,
        "not_suitable_for": STOP,
        "contraindications": STOP,
        "reflection_questions": reflections,
        "review_status": "pilot_ready",
        "reviewer_note": f"来源于项目负责人提供的关系成长训练卡文档。{reminder}",
        "enabled": True,
        "before_note_prompt": "开始前先给当前感受或困难程度评分；不要默认选择。",
        "after_note_prompt": "结束后记录完成、部分完成、没有完成，以及这次练习留下的一点观察。",
        "boundary_notice": BOUNDARY,
        "pre_practice_prompt": f"今天只练一个小步：{steps[0]}",
        "emotion_word_prompt": "开始前给此刻感受起一个日常、具体的名字；说不准也可以。",
        "new_response_prompt": purpose,
        "post_practice_prompt": reminder,
        "one_sentence_note_prompt": "用一句话写下这次练习留下的观察，不急着总结成结论。",
        "minimum_dose": {"single_session_minutes": minutes, "suggested_frequency": "按需要练习，可重复3至7次观察变化", "initial_cycle_days": 7},
        "completion_criteria": "完成至少一个核心步骤并主动保存记录；部分完成或没有完成也是有效记录，页面浏览不计完成。",
        "progression_criteria": "能在低压力场景重复完成后，再自主选择继续、替换或提高一点难度。",
        "stop_rules": STOP,
        "fidelity_check": steps[:2],
        "outcome_links": ["practice_completion", "self_rated_helpfulness", "post_practice_note"],
        "evidence_level": "project_draft",
        "safety_level": "standard",
        "release_policy": "shared_choice_candidate",
        "governance_review_status": "manual_review_required",
    }


CARDS = [
    _card("relationship_self_support", "自我支持卡：把责备换成支持句", "把责备改写成具体、能支持下一步行动的话。", 5, ["表现不如预期", "主动后觉得尴尬", "不断责备自己"], ["self_support", "self_blame"], ["写下脑中真实出现的责备句。", "区分实际发生的事实、当前感受和真正担心。", "用“我感到……因为……这不代表……接下来我可以……”改写，并补一个小行动。"], "我现在有些失望，因为刚才没把想法说清楚。这不代表我不擅长与人交往。接下来我先写下一句真正想表达的话。", ["练习前后自责或难受程度是多少？", "这次练习有帮助、一般、暂时没帮助，还是没有完成？", "下一步准备做哪件小事？"], "支持自己不等于否认问题，而是为处理问题保留力量。"),
    _card("relationship_emotion_observation", "一分钟情绪观察卡", "不急着解决情绪，观察它一分钟发生了什么变化。", 1, ["情绪突然升高", "脑子很乱", "等待回复时冲动"], ["emotion_observation", "pause"], ["前20秒观察胸口、胃部、肩膀、喉咙或手心的感觉。", "中间20秒给感受起一个名字，说不准也可以。", "最后20秒允许它暂时存在，再决定是否行动。"], "我注意到胸口有点紧，可能是紧张，也有一点期待。我先等一分钟，再决定要不要回复。", ["最明显的身体位置在哪里？", "最接近的情绪词是什么？", "一分钟后强度升高、差不多还是降低？"], "观察不是为了马上消除情绪，而是留出选择行动的空间。"),
    _card("relationship_emotion_naming", "情绪命名卡：说出现在最明显的感受", "把“很难受”拆成一至两个更具体的情绪词。", 3, ["情绪混乱", "想靠近又想退缩", "冲突后说不清感受"], ["emotion_naming", "relationship_trigger"], ["只写具体发生的事实，不解释对方动机。", "选择一至两个最接近的情绪词。", "用“我感到……可能是因为我在意……”写下线索。"], "我感到焦虑和失落，可能是因为我很在意自己有没有被认真回应。", ["事件事实是什么？", "最明显的一至两个情绪是什么？", "这份情绪可能在提醒我在意什么？"], "情绪是一种线索，不是对事实的最终判断。"),
    _card("relationship_auto_thought", "自动想法卡：把担心写成一句话", "看见关系情境中一闪而过、会推动行动或回避的那句话。", 5, ["反复脑补", "突然想逃", "想删除消息或连续追问"], ["automatic_thought", "rejection_expectation"], ["写下刚才发生的具体情境。", "写下脑海最先跳出的第一反应原句。", "记录这句话带来的身体感受和行动冲动。"], "情境：对方没有及时回复。自动想法：我是不是表现得太主动了。行动冲动：想撤回消息。", ["具体情境是什么？", "自动想法原句是什么？", "我最后做了什么？"], "这张卡只负责看见自动想法，暂时不要求判断它对不对。"),
    _card("relationship_second_explanation", "给想法找第二种说法", "不强迫乐观，只为同一件事保留另一种可能解释。", 5, ["认定自己被讨厌", "把一次失误理解成关系彻底结束"], ["cognitive_flexibility", "second_explanation"], ["写下可以确认的事实。", "写下原来的解释。", "再写一种同样可能、但更温和的解释。", "在仍不确定时，选择一个不过度反应的小行动。"], "这次交流没有达到我的期待，但一次交流还不足以说明整段关系会怎样。", ["事实是什么？", "原来的解释是什么？", "第二种可能解释和小行动是什么？"], "第二种说法不是证明原想法一定错，而是增加解释弹性。"),
    _card("relationship_gentle_expression", "温和表达卡：说出感受和需要", "用一句不攻击、不讨好也不隐藏自己的话表达感受或需要。", 5, ["不敢拒绝", "总是附和", "担心表达后破坏关系"], ["boundary_expression", "gentle_communication"], ["描述具体情境，避免“总是”“从来不”。", "说出自己的感受或状态。", "提出一个具体、可协商的请求。"], "当临时改变见面时间时，我会有一点着急，也需要重新安排时间。下次可以提前告诉我吗？", ["我想表达的情境是什么？", "我的感受或状态是什么？", "我的需要或请求是什么？"], "表达不等于要求对方同意；双方都可以表达自己的情况。"),
    _card("relationship_open_question", "一个开放问题卡", "一次只问一个不能只用“是/不是”回答的问题，让交流自然展开。", 5, ["想认识对方但不知道说什么", "聊天容易停在表面"], ["open_question", "low_pressure_connection"], ["从共同课程、活动、兴趣或最近经历中选一个主题。", "问一个开放问题。", "根据回答追问一次，然后认真听完。"], "你最近最期待的一件事是什么？原来是这样，你最喜欢其中哪一点？", ["我选择的共同主题是什么？", "我问出的开放问题是什么？", "对方回答中哪一点让我印象最深？"], "开放问题不是套取信息；问出一个并听完回答就算完成。"),
    _card("relationship_bounded_micro_action", "带边界的微行动卡", "选一个足够小的关系行动，并提前写清节奏和停止条件。", 10, ["有意愿但一直没有行动", "目标太大", "担心靠近后失去自己"], ["micro_action", "boundary"], ["写下自己想靠近的方向。", "把行动缩小到大概可以试试的一步。", "写下边界或停止条件。", "写下具体完成时间和情境。"], "方向：增加自然交流。微行动：回复一次共同活动动态。边界：只发一条，不连续追问。", ["本次微行动是什么？", "边界或停止条件是什么？", "我完成、部分完成还是没有完成？", "我从这次尝试中发现了什么？"], "成功标准是完成自己选择的小步，不以对方是否回应判断。"),
]


RECOMMENDATIONS = {
    "regulatory_focus_relationship_18": ["relationship_emotion_observation", "relationship_gentle_expression", "relationship_bounded_micro_action"],
    "micro_ysq_relationship_18": ["relationship_auto_thought", "relationship_second_explanation", "relationship_self_support"],
    "relationship_initiation_intention_action": ["relationship_open_question", "relationship_gentle_expression", "relationship_bounded_micro_action"],
}


def _read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def apply() -> dict[str, int]:
    cards_path = CONTENT / "training_cards.json"
    cards_payload = _read(cards_path)
    positions = {item.get("id"): index for index, item in enumerate(cards_payload["cards"])}
    for card in CARDS:
        if card["id"] in positions:
            cards_payload["cards"][positions[card["id"]]] = card
        else:
            cards_payload["cards"].append(card)
    cards_payload["updated_at"] = "2026-07-15"
    _write(cards_path, cards_payload)

    for filename, collection, key in [
        ("assessment_worksheets.json", "worksheets", "id"),
        ("scales_catalog.json", "scales", "id"),
    ]:
        path = CONTENT / filename
        payload = _read(path)
        for item in payload[collection]:
            if item.get(key) in RECOMMENDATIONS:
                item["recommended_card_ids"] = RECOMMENDATIONS[item[key]]
        payload["updated_at"] = "2026-07-15"
        _write(path, payload)

    map_path = CONTENT / "assessment_training_map.json"
    map_payload = _read(map_path)
    for rule in map_payload["rules"]:
        worksheet_id = (rule.get("trigger_condition") or {}).get("worksheet_id")
        if worksheet_id not in RECOMMENDATIONS:
            continue
        ids = RECOMMENDATIONS[worksheet_id]
        rule["recommended_card_ids"] = ids
        roles = ["今日练习", "备用练习", "长期练习"]
        rule["card_roles"] = [{"card_id": card_id, "role": role} for card_id, role in zip(ids, roles)]
        rule["reason"] = "根据本次关系情境回答，可从情绪觉察、想法弹性、温和表达或带边界的小行动中选择一个低负担练习。"
    map_payload["updated_at"] = "2026-07-15"
    _write(map_path, map_payload)

    programs_path = CONTENT / "programs.json"
    programs_payload = _read(programs_path)
    for program in programs_payload.get("programs", []):
        if program.get("id") == "self_compassion_relationship_growth":
            program["recommended_card_ids"] = [card["id"] for card in CARDS]
    programs_payload["updated_at"] = "2026-07-15"
    _write(programs_path, programs_payload)
    return {"cards": len(CARDS), "mapped_scales": len(RECOMMENDATIONS)}


if __name__ == "__main__":
    print(json.dumps(apply(), ensure_ascii=False))
