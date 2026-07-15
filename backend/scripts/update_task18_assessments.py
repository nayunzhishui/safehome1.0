"""Open reviewed scales and add public-source worksheets for task 18."""

from __future__ import annotations

import json
from pathlib import Path

from backend.scripts import build_worksheets


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONTENT_ROOT = PROJECT_ROOT / "content"
UPDATED_AT = "2026-07-11"
VERSION = "2026.07-task18-reviewed-scales-v1"

COMMON_BOUNDARY = (
    "本测评只用于阶段性自我观察和练习参考，不构成诊断、筛查结论或人格标签，"
    "也不替代心理咨询、危机干预或医学建议。"
)


def load(name: str) -> dict:
    return json.loads((CONTENT_ROOT / name).read_text(encoding="utf-8"))


def write(name: str, payload: dict) -> None:
    (CONTENT_ROOT / name).write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def index(items: list[dict], key: str) -> dict[str, dict]:
    return {item[key]: item for item in items}


def dimension(code: str, label: str, item_numbers: list[int], prefix: str, note: str) -> dict:
    return {
        "code": code,
        "label": label,
        "item_codes": [f"{prefix}{number:02d}" for number in item_numbers],
        "note": note,
    }


def assign_dimensions(draft: dict, dimensions: list[dict]) -> None:
    item_dimension = {
        item_code: dimension_row["code"]
        for dimension_row in dimensions
        for item_code in dimension_row["item_codes"]
    }
    draft["dimensions"] = dimensions
    for item in draft["items"]:
        item["dimension"] = item_dimension[item["item_code"]]


def update_drafts(payload: dict) -> None:
    drafts = index(payload["drafts"], "scale_id")

    pba = drafts["parental_burnout_pba"]
    assign_dimensions(
        pba,
        [
            dimension("EXHAUSTION", "养育角色耗竭", [3, 9, 1, 10, 21, 4, 15, 8, 23], "PBA", "9题求和"),
            dimension("CONTRAST", "与过去养育自我的反差", [5, 13, 17, 18, 19, 2], "PBA", "6题求和"),
            dimension("SATURATION", "养育厌倦感", [6, 16, 7, 12, 11], "PBA", "5题求和"),
            dimension("DISTANCING", "与孩子的情感疏离", [14, 22, 20], "PBA", "3题求和"),
        ],
    )
    pba.update(
        enabled=True,
        review_status="pilot_review_required",
        scoring_status="verified_local_four_dimension_sum",
        scoring_notes=[
            "23题均按0-6频率计分，无反向题；总分为23题之和，范围0-138；四个维度分别求和。",
            "结果仅用于观察养育压力相关体验，不使用诊断阈值，不评价家长好坏。",
        ],
        recommended_card_ids=["three_second_pause", "parent_body_grounding", "parent_repair_question"],
    )

    rsca = drafts["rsca_adolescent_resilience"]
    assign_dimensions(
        rsca,
        [
            dimension("GOAL_FOCUS", "目标专注", [3, 4, 11, 20, 24], "RSCA", "5题求和"),
            dimension("EMOTION_CONTROL", "情绪控制", [1, 2, 5, 21, 23, 27], "RSCA", "6题求和"),
            dimension("POSITIVE_COGNITION", "积极认知", [10, 13, 14, 25], "RSCA", "4题求和"),
            dimension("FAMILY_SUPPORT", "家庭支持", [8, 15, 16, 17, 19, 22], "RSCA", "6题求和"),
            dimension("INTERPERSONAL_ASSISTANCE", "人际协助", [6, 7, 9, 12, 18, 26], "RSCA", "6题求和"),
        ],
    )
    rsca.update(
        enabled=True,
        review_status="pilot_review_required",
        scoring_status="verified_27_item_five_dimension_rule",
        scoring_notes=[
            "27题按1-5分计分；1、2、5、6、9、12、15、16、17、21、26、27题反向计分。",
            "五个维度分别求和；前三个维度构成个人力，后两个维度构成支持力；总分为27题校正后得分之和。",
        ],
        recommended_card_ids=["rsca_emotion_regulation", "rsca_positive_cognition", "self_support_statement"],
    )

    regulatory = drafts["regulatory_focus_general_18"]
    texts = [
        "在生活中，我通常会注意防范消极的事件发生。",
        "我很担心自己不能尽到该有的责任和义务。",
        "我时常思考如何去实现自己的愿望和抱负。",
        "我时常害怕自己将来会变成现在所讨厌的那种人。",
        "我时常会想象未来理想中的自己是什么样子。",
        "在有助于未来成功的事情上，我会很看重。",
        "我经常担心自己不能完成学业目标。",
        "我经常想怎样能让学业成功。",
        "我经常会假想一些可怕的坏事情发生在自己身上。",
        "我经常想如何去预防生活中的失败。",
        "相比于获得收益，我更在意避免损失。",
        "我当前在校的主要目标是达成学业抱负。",
        "我当前在校的主要目标是避免学业失败。",
        "我是个追求‘理想自我’的人，即实现自己的希望、愿望和抱负。",
        "我是个寻求‘应当自我’的人，即履行自己的职责、责任和义务。",
        "通常我更注重在生活中获得积极结果。",
        "我经常会假想一些期望中的好事会发生在自己身上。",
        "总体来说，我更倾向于取得成功而不是避免失败。",
    ]
    promotion_numbers = [3, 5, 6, 8, 12, 14, 16, 17, 18]
    prevention_numbers = [1, 2, 4, 7, 9, 10, 11, 13, 15]
    regulatory["items"] = [
        {
            "item_code": f"RFQG{number:02d}",
            "display_order": number,
            "text": text,
            "dimension": "PROMOTION" if number in promotion_numbers else "PREVENTION",
            "reverse_scored": False,
        }
        for number, text in enumerate(texts, start=1)
    ]
    regulatory["dimensions"] = [
        dimension("PROMOTION", "促进聚焦", promotion_numbers, "RFQG", "9题均值"),
        dimension("PREVENTION", "预防聚焦", prevention_numbers, "RFQG", "9题均值"),
    ]
    regulatory.update(
        enabled=True,
        review_status="pilot_review_required",
        scoring_status="verified_lockwood_two_dimension_mean",
        dimension_score_method="mean",
        total_score_method="none",
        scoring_notes=[
            "18题采用1-7分；促进聚焦与预防聚焦各9题，分别取均值，不计算诊断性总分。",
            "两个维度可以同时较高或较低，不把差值解释为固定人格类型。",
        ],
        recommended_card_ids=["exam_micro_start", "cognitive_flexibility", "self_support_statement"],
    )


def open_catalog_scale(scale: dict, scoring_status: str, note: str) -> None:
    scale.update(
        enabled=True,
        review_status="pilot_review_required",
        item_status="audited_source",
        scoring_status=scoring_status,
        excluded_from_user_flow=False,
        notes=note,
    )
    scale.pop("not_open_reason", None)
    scale.pop("exclusion_reason", None)


def catalog_entry(
    scale_id: str,
    display_name: str,
    audience: str,
    theme: str,
    category: str,
    source_files: list[str],
    source_type: str,
    recommended_card_ids: list[str],
    sensitive_category: str = "none",
) -> dict:
    return {
        "id": scale_id,
        "display_name": display_name,
        "audience": audience,
        "audience_class": audience,
        "theme": theme,
        "category": category,
        "reflex_node": "state_observation",
        "search_keywords": [display_name, scale_id],
        "sensitive_category": sensitive_category,
        "source_folder": "公开来源与项目人工复核",
        "source_files": source_files,
        "source_type": source_type,
        "review_status": "pilot_review_required",
        "enabled": True,
        "first_batch_candidate": True,
        "item_status": "audited_public_source",
        "scoring_status": "verified_public_scoring_rule",
        "recommended_card_ids": recommended_card_ids,
        "boundary_notice": COMMON_BOUNDARY,
        "result_disclaimer": COMMON_BOUNDARY,
        "excluded_from_user_flow": False,
        "notes": "题项和计分已与公开来源核对；当前仅按支持性、非诊断方式用于受控试点。",
    }


def update_catalog(payload: dict) -> None:
    scales = payload["scales"]
    by_id = index(scales, "id")
    if "rfq8_reflective_functioning" not in by_id:
        rfq8_entry = catalog_entry(
            "rfq8_reflective_functioning",
            "反思功能问卷8题（RFQ-8）",
            "parent",
            "reflective_functioning",
            "家长自助",
            [
                "家长自主量表/反思功能测评/反思功能量表-8题项.docx",
                "https://peerj.com/articles/5756/",
            ],
            "authorized_local_resource_with_public_scoring_reference",
            ["emotion_naming", "nonjudgmental_response", "one_open_question"],
        )
        scales.append(rfq8_entry)
        by_id[rfq8_entry["id"]] = rfq8_entry
    open_catalog_scale(
        by_id["parental_burnout_pba"],
        "verified_local_four_dimension_sum",
        "本地中文版Word含23题、四维SPSS公式和0-6计分；按负责人决定开放受控试点。",
    )
    open_catalog_scale(
        by_id["rsca_adolescent_resilience"],
        "verified_27_item_five_dimension_rule",
        "本地27题与公开原始论文口径交叉核对；修正来源说明中的维度漏项后开放受控试点。",
    )
    open_catalog_scale(
        by_id["regulatory_focus_general_18"],
        "verified_lockwood_two_dimension_mean",
        "已移除抽取时误录的标题/指导语，恢复18个正式题项和促进/预防各9题结构。",
    )
    open_catalog_scale(
        by_id["rfq8_reflective_functioning"],
        "verified_original_two_subscale_recoding",
        "本地中文8题与公开RFQ-8计分表交叉核对；使用RFQc/RFQu非线性重编码均值。",
    )

    new_entries = [
        catalog_entry(
            "who5_wellbeing",
            "WHO-5身心健康指标",
            "student",
            "wellbeing",
            "学生自助",
            [
                "本地主观幸福感-生活满意度/(完整版)心理领域--WHO-5量表.doc",
                "https://www.who.int/publications/m/item/WHO-UCN-MSD-MHE-2024.01",
            ],
            "WHO_CC_BY_NC_SA_3_0",
            ["emotion_naming", "self_support_statement", "cognitive_flexibility"],
            "screening_or_health",
        ),
        catalog_entry(
            "cognitive_curiosity_student",
            "认知好奇量表（中文初中生版ECS-C）",
            "student",
            "cognitive_curiosity",
            "学生自助",
            [
                "本地认知好奇SPSS计分脚本",
                "https://rlrw.nju.edu.cn/_upload/article/files/a1/c0/bd0ca56c40be8a8e5fa98241b588/fbbad131-99dd-4acf-98f1-bc8d298df3f6.pdf",
            ],
            "public_research_education_resource",
            ["exam_micro_start", "student_two_thoughts", "self_support_statement"],
        ),
        catalog_entry(
            "big_five_tipi_10",
            "10项目大五人格量表（TIPI）",
            "adult",
            "personality",
            "成人自助",
            [
                "本地10项目大五人格量表的题目-英文.docx",
                "https://gosling.psy.utexas.edu/scales-weve-developed/ten-item-personality-measure-tipi/",
            ],
            "author_public_use",
            ["self_support_statement"],
            "personality",
        ),
    ]
    for entry in new_entries:
        if entry["id"] in by_id:
            by_id[entry["id"]].update(entry)
        else:
            scales.append(entry)
            by_id[entry["id"]] = entry

    # These remain closed because version/rights or exact dimension mapping is unresolved.
    for scale_id, reason in {
        "hplp_c_health_promoting_lifestyle": "42题正文已找到，但本地SPSS维度题号与当前题序不一致，暂不开放。",
        "sleep_isi_psqi": "ISI与PSQI必须拆表，PSQI边界公式和中文电子化授权未闭环，暂不开放。",
        "parental_autonomy_support": "公开POPS候选版本与本地9题来源未完成母亲/父亲版及中文译本对应，暂不开放。",
        "family_cohesion_adaptability": "FACES II-CV分类阈值已找到，但完整中文题项和权利链路未闭环，暂不开放。",
        "big_five_tipi_10": "英文原版题项与五维计分已核对；当前中文翻译版本仍待心理专业复核，暂不开放。",
    }.items():
        scale = by_id[scale_id]
        scale.update(
            enabled=False,
            excluded_from_user_flow=True,
            not_open_reason=reason,
            exclusion_reason=reason,
        )

    payload["version"] = VERSION
    payload["updated_at"] = UPDATED_AT


def question(item_id: str, text: str, dimension_code: str, options: list[tuple[int, str]], reverse: bool = False) -> dict:
    return {
        "id": item_id,
        "prompt": text,
        "type": "scale",
        "required": True,
        "dimension": dimension_code,
        "reverse_scored": reverse,
        "options": [
            {"label": f"{value} {label}", "value": str(value), "score": value}
            for value, label in options
        ],
    }


def base_worksheet(
    worksheet_id: str,
    title: str,
    category: str,
    audience: str,
    source_file: str,
    source_type: str,
    questions: list[dict],
    dimensions: list[dict],
    scoring: str,
    cards: list[str],
    total_score_method: str = "sum",
    dimension_score_method: str = "sum",
    sensitive_category: str = "none",
) -> dict:
    return {
        "id": worksheet_id,
        "source_file": source_file,
        "source_title": title,
        "display_title": title,
        "category": category,
        "audience": audience,
        "audience_class": audience,
        "reflex_node": "state_observation",
        "search_keywords": [title, worksheet_id],
        "sensitive_category": sensitive_category,
        "pages": 1,
        "instructions": "请按最近两周或日常真实情况填写。结果仅用于自我观察和练习参考。",
        "sections": [{"title": "填写说明", "content": COMMON_BOUNDARY}],
        "questions": questions,
        "dimensions": dimensions,
        "derived_dimensions": [],
        "dimension_score_method": dimension_score_method,
        "total_score_method": total_score_method,
        "scoring": scoring,
        "recommended_card_ids": cards,
        "source_version": VERSION,
        "source_type": source_type,
        "review_status": "pilot_review_required",
        "enabled_for_user": True,
        "review_note": "题项和计分已与公开来源核对；当前仅用于受控试点，仍保留人工复核。",
        "boundary_notice": COMMON_BOUNDARY,
        "result_disclaimer": COMMON_BOUNDARY,
        "_meta": {"total_score_method": total_score_method, "derived_dimensions": []},
    }


def public_worksheets() -> list[dict]:
    who_options = [(5, "一直"), (4, "大部分时间"), (3, "超过一半时间"), (2, "少于一半时间"), (1, "小部分时间"), (0, "没有")]
    who_texts = [
        "我感觉快乐，心情舒畅。",
        "我感觉宁静和放松。",
        "我感觉充满活力，精力充沛。",
        "我睡醒时感到清新，得到足够休息。",
        "我每天的生活充满了有趣的事情。",
    ]
    who = base_worksheet(
        "who5_wellbeing",
        "WHO-5身心健康指标",
        "学生自助",
        "student",
        "本地主观幸福感-生活满意度/(完整版)心理领域--WHO-5量表.doc；WHO官方2024版本",
        "WHO_CC_BY_NC_SA_3_0",
        [question(f"WHO5{number:02d}", text, "WELLBEING", who_options) for number, text in enumerate(who_texts, 1)],
        [{"code": "WELLBEING", "label": "身心健康感受", "item_ids": [f"WHO5{i:02d}" for i in range(1, 6)], "reverse_item_codes": [], "description": "5题原始分求和"}],
        "5题各0-5分，原始总分0-25；需要百分制时乘4。低分仅提示进一步关注，不输出疾病判断。",
        ["emotion_naming", "self_support_statement", "cognitive_flexibility"],
        sensitive_category="screening_or_health",
    )

    ecs_options = [(1, "几乎从不"), (2, "有时"), (3, "经常"), (4, "几乎总是")]
    ecs_texts = [
        "喜欢探索新想法。",
        "喜欢学习自己不熟悉的科目。",
        "发现学习新知识是充满吸引力的。",
        "学习新东西时喜欢去发现有关它的更多东西。",
        "喜欢讨论抽象概念。",
        "遇到问题必须先解决才能休息，甚至为此花费几个小时。",
        "抽象的概念性问题会让我持续思索如何解答。",
        "如果无法解决问题，我会感到挫败，因此我就更加努力地去学习。",
        "在我认为必须解决的问题上会表现得像个工作狂。",
        "为解决问题我需要思考很长时间。",
    ]
    interest = [1, 2, 3, 4, 5, 7]
    deprivation = [6, 8, 9, 10]
    ecs = base_worksheet(
        "cognitive_curiosity_student",
        "认知好奇量表（中文初中生版ECS-C）",
        "学生自助",
        "student",
        "南京大学社会学院心理系公开中文初中生版；本地SPSS公式",
        "public_research_education_resource",
        [
            question(
                f"ECS{number:02d}",
                text,
                "INTEREST" if number in interest else "DEPRIVATION",
                ecs_options,
            )
            for number, text in enumerate(ecs_texts, 1)
        ],
        [
            {"code": "INTEREST", "label": "兴趣型认知好奇", "item_ids": [f"ECS{i:02d}" for i in interest], "reverse_item_codes": [], "description": "6题求和"},
            {"code": "DEPRIVATION", "label": "剥夺型认知好奇", "item_ids": [f"ECS{i:02d}" for i in deprivation], "reverse_item_codes": [], "description": "4题求和"},
        ],
        "10题均正向计分；总分10-40，兴趣型6-24，剥夺型4-16。分数用于观察好奇方式，不评价学习能力。",
        ["exam_micro_start", "student_two_thoughts", "self_support_statement"],
    )

    tipi_options = [(1, "非常不同意"), (2, "比较不同意"), (3, "有点不同意"), (4, "中立"), (5, "有点同意"), (6, "比较同意"), (7, "非常同意")]
    tipi_texts = [
        "外向的、热情的。", "挑剔的、爱争论的。", "可靠的、自律的。", "焦虑的、易心烦的。",
        "愿意接触新事物的、思维复杂的。", "内敛的、安静的。", "有同情心的、温暖的。",
        "缺乏条理的、粗心的。", "冷静的、情绪稳定的。", "传统的、缺乏创造性的。",
    ]
    tipi_questions = [question(f"TIPI{i:02d}", text, "ITEM", tipi_options) for i, text in enumerate(tipi_texts, 1)]
    terms = lambda *pairs: {"type": "mean_terms", "terms": [{"item": f"TIPI{item:02d}", **({"reverse_min": 1, "reverse_max": 7} if reverse else {})} for item, reverse in pairs]}
    tipi_dimensions = [
        {"code": "EXTRAVERSION", "label": "外向性", "item_ids": ["TIPI01", "TIPI06"], "reverse_item_codes": ["TIPI06"], "description": "两题均值", "calculation": terms((1, False), (6, True))},
        {"code": "AGREEABLENESS", "label": "宜人性", "item_ids": ["TIPI02", "TIPI07"], "reverse_item_codes": ["TIPI02"], "description": "两题均值", "calculation": terms((2, True), (7, False))},
        {"code": "CONSCIENTIOUSNESS", "label": "尽责性", "item_ids": ["TIPI03", "TIPI08"], "reverse_item_codes": ["TIPI08"], "description": "两题均值", "calculation": terms((3, False), (8, True))},
        {"code": "EMOTIONAL_STABILITY", "label": "情绪稳定性", "item_ids": ["TIPI04", "TIPI09"], "reverse_item_codes": ["TIPI04"], "description": "两题均值", "calculation": terms((4, True), (9, False))},
        {"code": "OPENNESS", "label": "开放性", "item_ids": ["TIPI05", "TIPI10"], "reverse_item_codes": ["TIPI10"], "description": "两题均值", "calculation": terms((5, False), (10, True))},
    ]
    tipi = base_worksheet(
        "big_five_tipi_10",
        "10项目大五人格量表（TIPI）",
        "成人自助",
        "adult",
        "Gosling Lab官方TIPI英文原版；中文翻译待心理复核",
        "author_public_use",
        tipi_questions,
        tipi_dimensions,
        "1-7分；2、4、6、8、10按8-原分反向后，各维度取两题均值。不计算人格总分，不输出人格类型。",
        ["self_support_statement"],
        total_score_method="none",
        dimension_score_method="mean",
        sensitive_category="personality",
    )
    tipi.update(
        instructions=(
            "以下成对特征可能适用于你，也可能不适用。请判断每一对特征整体上与你的符合程度；"
            "即使其中一个特征比另一个更符合，也请对整对特征作答。结果只用于阶段性自我观察，不构成人格标签。"
        ),
        review_status="content_verified_pending_chinese_translation_review",
        enabled_for_user=False,
        review_note="英文原版题项和五维计分已核对；中文翻译待心理专业复核后再开放。",
    )
    return [who, ecs, tipi]


def update_rfq8(worksheet: dict) -> None:
    certainty_map = {str(i): value for i, value in enumerate([3, 2, 1, 0, 0, 0, 0], start=1)}
    uncertainty_map = {str(i): value for i, value in enumerate([0, 0, 0, 0, 1, 2, 3], start=1)}
    certainty_items = [1, 2, 3, 4, 5, 6]
    uncertainty_items = [2, 4, 5, 6, 7, 8]
    worksheet.update(
        review_status="pilot_review_required",
        enabled_for_user=True,
        dimensions=[
            {
                "code": "RFQC",
                "label": "对心理状态的过度确定倾向",
                "item_ids": [f"RFQ{i:02d}" for i in certainty_items],
                "reverse_item_codes": [],
                "description": "6项重编码后均值",
                "calculation": {"type": "mapped_mean_terms", "terms": [{"item": f"RFQ{i:02d}", "map": certainty_map} for i in certainty_items]},
            },
            {
                "code": "RFQU",
                "label": "对心理状态的不确定倾向",
                "item_ids": [f"RFQ{i:02d}" for i in uncertainty_items],
                "reverse_item_codes": ["RFQ07"],
                "description": "6项重编码后均值",
                "calculation": {
                    "type": "mapped_mean_terms",
                    "terms": [
                        {"item": f"RFQ{i:02d}", "map": certainty_map if i == 7 else uncertainty_map}
                        for i in uncertainty_items
                    ],
                },
            },
        ],
        dimension_score_method="mean",
        total_score_method="none",
        scoring="7点作答不直接相加。RFQc使用1→3、2→2、3→1、4-7→0；RFQu使用1-4→0、5→1、6→2、7→3，题7反向重编码；两个分量表各取6项均值。",
        recommended_card_ids=["emotion_naming", "nonjudgmental_response", "one_open_question"],
        review_note="本地中文8题与公开RFQ-8计分表交叉核对；量表计分存在方法学争议，因此只做受控试点和支持性解释。",
        boundary_notice=COMMON_BOUNDARY,
        result_disclaimer=COMMON_BOUNDARY,
        source_version=VERSION,
        _meta={"total_score_method": "none", "derived_dimensions": []},
    )
    for item in worksheet["questions"]:
        item["dimension"] = "ITEM"


def recommendation_rule(rule_id: str, worksheet_id: str, cards: list[str], reason: str) -> dict:
    roles = ["今日练习", "备用练习", "长期练习"]
    return {
        "rule_id": rule_id,
        "source_type": "assessment",
        "trigger_condition": {"worksheet_id": worksheet_id, "risk_level": "low_or_medium"},
        "theme": ["supportive_assessment", worksheet_id],
        "recommended_card_ids": cards,
        "card_roles": [{"card_id": card_id, "role": roles[index]} for index, card_id in enumerate(cards)],
        "reason": reason,
        "today_suggestion": "今天只选择一张卡，完成一个不超过十分钟的小练习。",
        "long_term_suggestion": "后续结合记录与复测趋势观察变化，不追求一次完成或固定标签。",
        "not_suitable_when": "若出现自伤、自杀、暴力、胁迫或其他现实安全风险，应优先寻求现实支持和人工帮助。",
        "boundary_notice": COMMON_BOUNDARY,
        "review_status": "draft",
        "rule_version": VERSION,
        "recommendation_mode": "candidate_set",
        "selection_policy": "shared_choice",
        "recommendation_source": "assessment_rule",
        "approval_status": "draft_requires_psychology_review",
        "allow_controlled_cards": False,
        "max_candidates": 3,
    }


def update_training_map(payload: dict) -> None:
    specs = [
        ("task18_pba_support", "parental_burnout_pba", ["three_second_pause", "parent_body_grounding", "parent_repair_question"], "从暂停、身体落地和修复问题中提供家长可选择的轻量支持。"),
        ("task18_rsca_support", "rsca_adolescent_resilience", ["rsca_emotion_regulation", "rsca_positive_cognition", "self_support_statement"], "围绕情绪调节、积极认知与自我支持提供候选练习。"),
        ("task18_general_regulatory_focus_support", "regulatory_focus_general_18", ["exam_micro_start", "cognitive_flexibility", "self_support_statement"], "不按促进/预防高低贴标签，只提供目标拆分和灵活行动练习。"),
        ("task18_rfq8_support", "rfq8_reflective_functioning", ["emotion_naming", "nonjudgmental_response", "one_open_question"], "用情绪命名、减少判断和开放式提问支持反思，不推断他人内心。"),
        ("task18_who5_support", "who5_wellbeing", ["emotion_naming", "self_support_statement", "cognitive_flexibility"], "根据近期身心感受提供低负担练习，不用分数替代专业评估。"),
        ("task18_ecs_support", "cognitive_curiosity_student", ["exam_micro_start", "student_two_thoughts", "self_support_statement"], "把好奇和问题投入转化为可停下、可拆分的小任务。"),
    ]
    rules = payload["rules"]
    by_id = index(rules, "rule_id")
    for spec in specs:
        row = recommendation_rule(*spec)
        if row["rule_id"] in by_id:
            by_id[row["rule_id"]].update(row)
        else:
            rules.append(row)
    payload["version"] = VERSION
    payload["updated_at"] = UPDATED_AT


def main() -> int:
    drafts = load("scale_item_drafts.json")
    catalog = load("scales_catalog.json")
    training_map = load("assessment_training_map.json")

    update_drafts(drafts)
    update_catalog(catalog)
    write("scale_item_drafts.json", drafts)
    write("scales_catalog.json", catalog)

    built = build_worksheets.build_worksheets(CONTENT_ROOT)["payload"]
    worksheets = built["worksheets"]
    by_id = index(worksheets, "id")
    update_rfq8(by_id["rfq8_reflective_functioning"])
    for worksheet in public_worksheets():
        if worksheet["id"] in by_id:
            by_id[worksheet["id"]].update(worksheet)
        else:
            worksheets.append(worksheet)
            by_id[worksheet["id"]] = worksheet
    built["version"] = VERSION
    built["updated_at"] = UPDATED_AT
    write("assessment_worksheets.json", built)

    update_training_map(training_map)
    write("assessment_training_map.json", training_map)

    print(
        json.dumps(
            {
                "worksheets": len(worksheets),
                "enabled_worksheets": sum(item.get("enabled_for_user", True) for item in worksheets),
                "catalog_scales": len(catalog["scales"]),
                "training_rules": len(training_map["rules"]),
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
