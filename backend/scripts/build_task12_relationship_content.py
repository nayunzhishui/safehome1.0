"""Build the three Task 12 relationship-pilot assessments from the audited item map."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONTENT_ROOT = PROJECT_ROOT / "content"
DEFAULT_MAPPING = PROJECT_ROOT / "outputs" / "task12_relationship_profiles" / "item_mapping_preview.csv"
BOUNDARY = (
    "本测评用于大学生关系体验的阶段性自我观察和练习选择，不构成诊断、筛查结论、人格标签或关系成败预测。"
    "如填写内容涉及现实安全风险，请优先联系可信成年人、学校支持人员或专业服务。"
)
SOURCE_ROOT = "D:/codex/workspace/safehome1.0其他内容/夏老师文件/2026年6月18日发给董俊杰的(1)/测评问卷-量表/数据1"


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _upsert(rows: list[dict], key: str, incoming: list[dict]) -> None:
    positions = {row.get(key): index for index, row in enumerate(rows)}
    for row in incoming:
        value = row[key]
        if value in positions:
            rows[positions[value]] = row
        else:
            positions[value] = len(rows)
            rows.append(row)


def _likert(low: str, high: str, count: int) -> list[dict]:
    middle = {
        5: ["比较不符合", "不确定", "比较符合"],
        6: ["大多不符合", "有些不符合", "有些符合", "大多符合"],
        7: ["不同意", "比较不同意", "不确定", "比较同意", "同意"],
        9: ["很不同意", "不同意", "比较不同意", "不确定", "比较同意", "同意", "很同意"],
    }[count]
    return [{"value": index + 1, "label": label} for index, label in enumerate([low, *middle, high])]


REG_LIKERT = _likert("非常不同意", "非常同意", 9)
YSQ_LIKERT = _likert("完全不符合", "完全符合", 6)
YSQ_THEME_LABELS = [
    "被理解与关心担心", "离开与失去担心", "受伤与被利用担心", "自我价值担心", "归属与融入担心",
    "独立应对担心", "安全与灾难担心", "取悦与自我忽略", "情绪需求压抑", "特殊待遇期待",
    "坚持与自我管理", "过度照顾他人", "他人评价关注", "情绪表达抑制", "高标准压力",
    "严厉惩罚倾向", "理想化依赖期待", "冲突回避与屈从",
]
AGREE_LIKERT = _likert("非常不同意", "非常同意", 5)
PROBABILITY_LIKERT = _likert("非常不可能", "非常可能", 5)
FREQUENCY_LIKERT = _likert("从未", "总是", 5)


def _rows(mapping_path: Path) -> dict[str, list[dict]]:
    grouped: dict[str, list[dict]] = {}
    with mapping_path.open(encoding="utf-8-sig", newline="") as source:
        for row in csv.DictReader(source):
            grouped.setdefault(row["scale_id"], []).append(row)
    return grouped


def _items(rows: list[dict], dimension_for, default_likert: list[dict]) -> list[dict]:
    result = []
    for order, row in enumerate(rows, 1):
        code = row["abbreviation"]
        if code.startswith("@"):
            continue
        item = {
            "item_code": code,
            "display_order": order,
            "text": row["original_prompt"].strip(),
            "dimension": dimension_for(code),
            "reverse_scored": False,
        }
        if code.startswith("a") and code[1:].isdigit():
            item["likert"] = PROBABILITY_LIKERT
        elif code.startswith("RAP"):
            item["likert"] = FREQUENCY_LIKERT
        elif default_likert != AGREE_LIKERT:
            item["likert"] = default_likert
        result.append(item)
    return result


def _drafts(grouped: dict[str, list[dict]]) -> list[dict]:
    promotion = {"Q3", "Q5", "Q6", "Q8", "Q12", "Q14", "Q16", "Q17", "Q18"}
    prevention = {"Q1", "Q2", "Q4", "Q7", "Q9", "Q10", "Q11", "Q13", "Q15"}

    def regulatory_dimension(code: str) -> str:
        return "PROM" if code in promotion else "PREV"

    def relationship_dimension(code: str) -> str:
        if code in {"a1", "b1", "a2", "b2", "a3", "b3"}:
            return "BENEFIT"
        if code in {"a4", "b4"}:
            return "REJ_THREAT"
        if code in {"a5", "b5"}:
            return "AUTH_THREAT"
        return next(prefix for prefix in ("SN", "PBC", "BI", "RAP") if code.startswith(prefix))

    common = {
        "audience": "student",
        "theme": "relationship_exploration",
        "enabled": True,
        "review_status": "pilot_review_required",
        "item_status": "audited_local_source",
        "scoring_status": "frozen_task12_formula",
        "source_folder": "数据1",
        "source_files": [
            f"{SOURCE_ROOT}/大学生亲密关系主动性调查问卷.docx",
            f"{SOURCE_ROOT}/原始量表.xlsx",
            f"{SOURCE_ROOT}/调节聚焦问卷计分手册.docx",
        ],
    }
    return [
        {
            **common,
            "scale_id": "regulatory_focus_relationship_18",
            "display_name": "关系情境中的行动关注方式",
            "instructions": "请根据你在关系和生活目标中的通常体验作答。不同分量表分别解释，不计算诊断性总分。",
            "likert": REG_LIKERT,
            "dimension_score_method": "mean",
            "total_score_method": "none",
            "dimensions": [
                {"code": "PROM", "label": "成长与获得关注", "item_codes": sorted(promotion, key=lambda x: int(x[1:])), "calculation": {"type": "mean"}},
                {"code": "PREV", "label": "安全与避免损失关注", "item_codes": sorted(prevention, key=lambda x: int(x[1:])), "calculation": {"type": "mean"}},
            ],
            "items": _items(grouped["regulatory_focus_relationship_18"], regulatory_dimension, REG_LIKERT),
            "scoring_notes": ["PROM 与 PREV 分别取题项均值", "RFD=PROM-PREV 仅供研究画像定位", "数据1实测为1-5，新问卷为1-9，模型接入时必须按元数据换算"],
            "supportive_interpretation_draft": "分别观察成长目标与安全顾虑的关注方式，不把高低解释为好坏。",
            "recommended_card_ids": ["relationship_emotion_observation", "relationship_gentle_expression", "relationship_bounded_micro_action"],
        },
        {
            **common,
            "scale_id": "micro_ysq_relationship_18",
            "display_name": "关系中的常见担心与期待",
            "instructions": "请根据这些描述与你近期关系体验的符合程度作答。结果用于识别可练习的主题，不用于给人格下结论。",
            "likert": YSQ_LIKERT,
            "dimension_score_method": "mean",
            "total_score_method": "none",
            "dimensions": [
                {"code": f"YSQ_THEME{i:02d}", "label": label, "item_codes": [f"YSQ{i}"], "calculation": {"type": "mean"}}
                for i, label in enumerate(YSQ_THEME_LABELS, 1)
            ],
            "items": _items(grouped["micro_ysq_relationship_18"], lambda code: f"YSQ_THEME{int(code[3:]):02d}", YSQ_LIKERT),
            "scoring_notes": ["18题分别保留为18个支持性主题维度", "不按阈值输出人格或图式标签"],
            "supportive_interpretation_draft": "观察哪些关系担心近期较常出现，并寻找可支持的小练习，不输出人格标签。",
            "recommended_card_ids": ["relationship_auto_thought", "relationship_second_explanation", "relationship_self_support"],
        },
        {
            **common,
            "scale_id": "relationship_initiation_intention_action",
            "display_name": "关系主动性：想法、意愿与行动",
            "instructions": "请按题目中的可能性、同意程度或过去一个月的频率作答。开放题在结果页另行选填。",
            "likert": AGREE_LIKERT,
            "dimension_score_method": "mean",
            "total_score_method": "none",
            "dimensions": [
                {"code": "BENEFIT", "label": "主动关系获益信念", "item_codes": ["a1", "b1", "a2", "b2", "a3", "b3"], "calculation": {"type": "mean_of_products", "pairs": [["a1", "b1"], ["a2", "b2"], ["a3", "b3"]]}},
                {"code": "REJ_THREAT", "label": "拒绝相关担心", "item_codes": ["a4", "b4"], "calculation": {"type": "product", "items": ["a4", "b4"]}},
                {"code": "AUTH_THREAT", "label": "失去真实感相关担心", "item_codes": ["a5", "b5"], "calculation": {"type": "product", "items": ["a5", "b5"]}},
                {"code": "AUTH_PROTECT", "label": "真实自我保护线索", "item_codes": ["a5", "b5"], "calculation": {"type": "mean_terms", "terms": [{"item": "a5", "reverse_min": 1, "reverse_max": 5}, {"item": "b5"}]}},
                *[{"code": code, "label": label, "item_codes": [f"{code}{i}" for i in range(1, count + 1)], "calculation": {"type": "mean"}} for code, label, count in [("SN", "重要他人支持感", 4), ("PBC", "关系行动可控感", 6), ("BI", "关系行动意愿", 6), ("RAP", "近月关系行动", 5)]],
            ],
            "derived_dimensions": [{"code": "THREAT", "label": "综合威胁信念", "calculation": {"type": "mean_dimensions", "dimensions": ["REJ_THREAT", "AUTH_THREAT"]}}],
            "items": _items(grouped["relationship_initiation_intention_action"], relationship_dimension, AGREE_LIKERT),
            "scoring_notes": ["获益、威胁与真实自我保护按冻结乘积公式计算", "SN/PBC/BI/RAP分别取均值", "不计算诊断性总分"],
            "supportive_interpretation_draft": "观察关系获益、担心、支持感、可控感、意愿与行动之间的阶段性组合。",
            "recommended_card_ids": ["relationship_open_question", "relationship_gentle_expression", "relationship_bounded_micro_action"],
        },
    ]


def _catalog(drafts: list[dict]) -> list[dict]:
    return [
        {
            "id": draft["scale_id"],
            "display_name": draft["display_name"],
            "audience": "student",
            "audience_class": "student",
            "theme": "relationship_exploration",
            "category": "学生自助",
            "reflex_node": "relationship_support",
            "search_keywords": ["大学生关系", "关系主动性", draft["display_name"]],
            "sensitive_category": "relationship_exploration",
            "source_folder": "数据1",
            "source_files": draft["source_files"],
            "source_type": "authorized_local_research_resource",
            "review_status": "pilot_review_required",
            "enabled": True,
            "first_batch_candidate": True,
            "item_status": draft["item_status"],
            "scoring_status": draft["scoring_status"],
            "recommended_card_ids": draft["recommended_card_ids"],
            "profile_model_id": f"task12_{draft['scale_id']}_profile_v1",
            "boundary_notice": BOUNDARY,
            "result_disclaimer": BOUNDARY,
            "excluded_from_user_flow": False,
            "notes": "任务十二本地研究试点内容；已完成程序化题项与公式核对；关系情境行动关注方式按负责人要求使用1-9计分，并在画像匹配前线性换算至既往1-5训练范围。",
        }
        for draft in drafts
    ]


def _rules(drafts: list[dict]) -> list[dict]:
    rules = []
    for draft in drafts:
        scale_id = draft["scale_id"]
        rules.append(
            {
                "rule_id": f"task12_{scale_id}_support",
                "source_type": "assessment",
                "trigger_condition": {"worksheet_id": scale_id, "risk_level": "low_or_medium"},
                "theme": ["relationship_exploration", "student_support"],
                "recommended_card_ids": draft["recommended_card_ids"],
                "card_roles": [
                    {"card_id": card_id, "role": role}
                    for card_id, role in zip(draft["recommended_card_ids"], ["今日练习", "备用练习", "长期练习"])
                ],
                "reason": "根据本次关系体验记录，推荐从觉察、表达和自我支持中选择一个轻量动作。",
                "today_suggestion": "今天只选择一张卡，完成一个不超过十分钟的小练习。",
                "long_term_suggestion": "后续可结合复测趋势观察变化，不用追求一次完成或固定标签。",
                "not_suitable_when": "若出现自伤、自杀、暴力、胁迫或其他现实安全风险，应优先寻求现实支持和人工帮助。",
                "boundary_notice": BOUNDARY,
                "review_status": "draft",
            }
        )
    return rules


def build_content(content_dir: Path, mapping_path: Path) -> dict[str, int]:
    grouped = _rows(mapping_path)
    drafts = _drafts(grouped)
    catalog = _catalog(drafts)
    rules = _rules(drafts)

    drafts_payload = _read_json(content_dir / "scale_item_drafts.json")
    _upsert(drafts_payload.setdefault("drafts", []), "scale_id", drafts)
    drafts_payload["updated_at"] = "2026-07-10"
    _write_json(content_dir / "scale_item_drafts.json", drafts_payload)

    catalog_payload = _read_json(content_dir / "scales_catalog.json")
    _upsert(catalog_payload.setdefault("scales", []), "id", catalog)
    catalog_payload["updated_at"] = "2026-07-10"
    _write_json(content_dir / "scales_catalog.json", catalog_payload)

    training_payload = _read_json(content_dir / "assessment_training_map.json")
    _upsert(training_payload.setdefault("rules", []), "rule_id", rules)
    training_payload["updated_at"] = "2026-07-10"
    _write_json(content_dir / "assessment_training_map.json", training_payload)
    return {"draft_count": len(drafts), "catalog_count": len(catalog), "rule_count": len(rules)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--content-dir", type=Path, default=CONTENT_ROOT)
    parser.add_argument("--mapping", type=Path, default=DEFAULT_MAPPING)
    args = parser.parse_args()
    print(json.dumps(build_content(args.content_dir, args.mapping), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
