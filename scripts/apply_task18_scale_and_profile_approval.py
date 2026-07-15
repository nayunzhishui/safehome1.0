"""Apply the project-owner Task 18 scale and profile pilot approval decisions."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "content"
APPROVAL_EVIDENCE = "docs/02_专项进度与验收/任务十八项目负责人量表与画像试点批准记录_20260712.md"
APPROVAL = {
    "reviewer": "项目负责人（用户明确批准）",
    "reviewed_at": "2026-07-12",
    "evidence_path": APPROVAL_EVIDENCE,
    "scope": "pilot_release",
}

HPLP_ITEMS = [
    "选择低脂肪、低饱和脂肪和低胆固醇的食物",
    "有任何不正常的症状和体征时，向卫生专业人员咨询",
    "遵循一个制定好的运动计划",
    "感觉自己在积极地成长和变化",
    "很乐意称赞别人的成功",
    "限制糖和含糖食物的使用",
    "阅读或观看有关健康促进的杂志或电视内容",
    "每周最少参加三次剧烈运动（如快步走、骑自行车、有氧舞蹈、爬楼梯，每次20分钟或以上）",
    "每天找一些时间放松自己",
    "相信自己的人生是有目标的",
    "维持有意义的人际关系",
    "每天吃面包、米饭、面食和谷类食物",
    "向健康专业人员提问，以理解专业人员的指导",
    "参加一些轻度至中度的身体活动（如散步30-40分钟，每周5次或以上）",
    "接受生活中自己不能改变的事情",
    "对未来充满期待",
    "乐于和好朋友在一起",
    "每天吃水果",
    "当不信任卫生专业人士的建议时，寻求另一位专业人士的建议",
    "参加一些娱乐活动（如游泳、跳舞、骑自行车）",
    "睡前想一些开心的事情",
    "自愿给别人关心、爱和温暖",
    "每天吃蔬菜",
    "与专业人士讨论健康问题",
    "每周至少做三次伸展运动",
    "用适合自己的方式缓解压力",
    "向人生的长期目标努力",
    "每月至少一次自检自己的身体",
    "从日常生活中得到身体锻炼（如饭后散步、尽量走楼梯而不坐电梯、少坐车多走路）",
    "每天吃肉、家禽、鱼、干豆类、鸡蛋和坚果类食物",
    "向卫生专业人员咨询如何自我保健",
    "运动时会测量自己的脉搏",
    "知道生命中什么对自己重要",
    "从人际网络中得到人际支持",
    "阅读包装食品的标签",
    "参加健康保健的教育活动",
    "运动时达到自己的心率目标",
    "让自己安静下来，避免过度疲劳",
    "每天吃早餐",
    "必要时寻求指导和咨询",
]

HPLP_DIMENSIONS = [
    ("NUTRITION", "营养", [1, 6, 12, 18, 23, 30, 35, 39]),
    ("HEALTH_RESPONSIBILITY", "健康责任", [2, 7, 13, 19, 24, 28, 31, 36, 40]),
    ("PHYSICAL_ACTIVITY", "身体活动", [3, 8, 14, 20, 25, 29, 32, 37]),
    ("SPIRITUAL_GROWTH", "精神成长", [4, 10, 16, 27, 33]),
    ("INTERPERSONAL_RELATIONS", "人际关系", [5, 11, 17, 22, 34]),
    ("STRESS_MANAGEMENT", "压力管理", [9, 15, 21, 26, 38]),
]

SPECIFIC_INSTRUCTIONS = {
    "emotion_regulation_erq": "请根据自己通常调节情绪的方式作答，选择每句话与日常情况的符合程度。结果只用于观察调节策略，不评价方式好坏。",
    "parent_reflective_functioning_prfq": "请根据自己理解孩子想法、感受和行为原因时的通常情况作答。没有标准答案，请选择最符合近期亲子互动的程度。",
    "mindful_attention_awareness_maas": "请根据近期日常生活中这些情况出现的频率作答，从“几乎总是”到“几乎从不”选择最符合的一项。",
    "emotional_resilience_11": "请根据近期面对情绪波动、压力或挫折时的实际反应作答，选择每句话与自己的符合程度。",
    "study_engagement_uwes_s_17": "请根据近期学习时的活力、投入和专注体验作答，选择相应情况出现的频率。",
    "cd_risc10_brief_resilience": "请根据近期面对困难、变化或压力时的真实感受作答，选择每句话与自己的符合程度。",
    "parental_burnout_pba": "请根据近期承担养育责任时相关体验出现的频率作答。结果只用于识别可支持的位置，不评价家长能力。",
    "acceptance_action_aaq2": "请根据近期面对不舒服想法和感受时的通常体验作答，选择每句话与自己的符合程度。",
    "rsca_adolescent_resilience": "请根据近期面对学习、家庭和同伴压力时的真实情况作答，选择每句话与自己的符合程度。",
    "academic_buoyancy_4": "请根据近期处理日常学习挫折、作业压力和考试失误时的实际情况作答。",
    "afq_y8_avoidance_fusion": "请根据近期被想法或感受影响、以及回避不舒服体验的实际频率作答。",
    "cfi2_cognitive_flexibility": "请根据近期遇到问题或变化时看待替代方案、调整想法和采取行动的实际情况作答。",
    "regulatory_focus_general_18": "请根据自己通常追求目标、争取进步和避免损失时的行为倾向作答。结果只表示阶段性策略线索。",
    "gad7_anxiety": "请根据过去两周内下列感受困扰自己的频率作答。结果只作支持性观察；若持续困扰生活，请寻求专业帮助。",
    "phq9_cesd10_depression": "请按题目所示时间范围，选择相关感受或行为出现的频率。结果不构成诊断；涉及安全风险时请及时联系可信人员或专业服务。",
    "epq_emotional_stability_24": "请根据自己通常的情绪反应和行为情况作答，选择“是”或“否”。结果只用于阶段性观察，不形成固定人格标签。",
    "emotional_intelligence_eis_33": "请根据近期识别、理解和调节自己及他人情绪时的实际情况作答。",
    "regulatory_focus_relationship_18": "请根据近期在亲密关系中靠近目标、表达需要和避免关系损失时的通常倾向作答。",
    "relationship_initiation_intention_action": "请根据近期在关系中表达、靠近和采取行动时的真实想法与行为作答。",
}


def load(name: str):
    return json.loads((CONTENT / name).read_text(encoding="utf-8"))


def save(name: str, payload) -> None:
    (CONTENT / name).write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def question_options() -> list[dict]:
    return [
        {"label": "1 从不", "value": "1", "score": 1},
        {"label": "2 偶尔", "value": "2", "score": 2},
        {"label": "3 经常", "value": "3", "score": 3},
        {"label": "4 总是", "value": "4", "score": 4},
    ]


def dimension_for_item(number: int) -> str:
    return next(code for code, _label, numbers in HPLP_DIMENSIONS if number in numbers)


def build_hplp_questions() -> list[dict]:
    return [
        {
            "id": f"HPLP{number:02d}",
            "prompt": prompt,
            "type": "scale",
            "required": True,
            "dimension": dimension_for_item(number),
            "reverse_scored": False,
            "options": question_options(),
        }
        for number, prompt in enumerate(HPLP_ITEMS, 1)
    ]


def worksheet_dimensions() -> list[dict]:
    return [
        {
            "code": code,
            "label": label,
            "item_ids": [f"HPLP{number:02d}" for number in numbers],
            "reverse_item_codes": [],
            "description": "所属题项取均值，保留原量尺1-4分。",
        }
        for code, label, numbers in HPLP_DIMENSIONS
    ]


def draft_dimensions() -> list[dict]:
    return [
        {
            "code": code,
            "label": label,
            "item_codes": [f"HPLP{number:02d}" for number in numbers],
            "note": "所属题项取均值，保留原量尺1-4分。",
        }
        for code, label, numbers in HPLP_DIMENSIONS
    ]


def approve_worksheets() -> set[str]:
    payload = load("assessment_worksheets.json")
    ids: set[str] = set()
    for item in payload["worksheets"]:
        ids.add(item["id"])
        item["review_status"] = "pilot_approved"
        item["enabled_for_user"] = True
        item["approval"] = dict(APPROVAL)
        item["review_note"] = "项目负责人已批准进入试点；结果仅作支持性观察，不构成诊断、筛查或固定标签。"
        if item["id"] in SPECIFIC_INSTRUCTIONS:
            item["instructions"] = SPECIFIC_INSTRUCTIONS[item["id"]]
        if item["id"] == "mindful_attention_awareness_maas":
            item["dimension_score_method"] = "mean"
            item["total_score_method"] = "none"
            item["dimensions"][0]["label"] = "日常觉察"
            item["dimensions"][0]["description"] = "15题取均值，保留原量尺1-6分。"
            item["scoring"] = "15题均按1-6分计分并取平均值，不另作反向处理；均值越高表示本次自报中日常注意与觉察更充分。结果只作阶段性观察。"
        if item["id"] == "attribution_style_student_36":
            item["dimension_score_method"] = "mean"
            item["total_score_method"] = "none"
            for dimension in item["dimensions"]:
                dimension["description"] = "所属12个情境评分取均值，保留原量尺1-7分。"
            item["scoring"] = "12个情境分别记录内外归因、稳定性和整体性三个1-7分评分；三个维度各取12题均值，不计算总分，也不自动生成积极、消极或人格类型。自由填写的原因文本仅作本人回顾和研究者支持性访谈线索。"
        if item["id"] == "student_profile_v1":
            item["dimensions"] = [
                {"code": "test_anxiety", "label": "学习评价压力", "item_ids": ["test_anxiety"], "reverse_item_codes": [], "description": "单项阶段性观察"},
                {"code": "uncertainty_intolerance", "label": "不确定情境压力", "item_ids": ["iu_score"], "reverse_item_codes": [], "description": "单项阶段性观察"},
                {"code": "pressure_alert", "label": "压力警觉", "item_ids": ["fear_score"], "reverse_item_codes": [], "description": "单项阶段性观察"},
                {"code": "self_support", "label": "自我支持", "item_ids": ["self_compassion"], "reverse_item_codes": [], "description": "单项阶段性观察"},
            ]
            item["derived_dimensions"] = []
            item["dimension_score_method"] = "mean"
            item["total_score_method"] = "none"
        if item["id"] != "hplp_c_health_promoting_lifestyle":
            continue
        item.update(
            {
                "source_file": "5_牛至旭_中年女性自我关怀现状及其对主观幸福感的影响/数据和问卷/问卷/四个量表文字版.docx",
                "source_title": "健康促进生活方式量表（HPLP，40题）",
                "display_title": "健康促进生活方式量表（HPLP，40题）",
                "search_keywords": ["HPLP", "HPLP-II", "健康促进生活方式", "生活习惯"],
                "instructions": "以下陈述涉及日常健康促进习惯。请按最近一段时间的实际频率选择“从不、偶尔、经常或总是”。结果用于支持性自我观察和练习参考，不替代医学建议。",
                "sections": [{"title": "填写说明", "content": "共40题，所有题项均按1-4分正向计分；六个维度和综合观察均使用均值。"}],
                "questions": build_hplp_questions(),
                "dimensions": worksheet_dimensions(),
                "derived_dimensions": [{
                    "code": "HPLP_TOTAL",
                    "label": "健康促进生活方式综合观察",
                    "calculation": {"type": "mean_dimensions", "dimensions": [row[0] for row in HPLP_DIMENSIONS]},
                }],
                "dimension_score_method": "mean",
                "total_score_method": "none",
                "scoring": "40题均按1-4分正向计分。营养8题、健康责任9题、身体活动8题、精神成长5题、人际关系5题、压力管理5题分别取均值；综合观察为六维均值的平均值。分数越高表示该类健康促进行为在本次自报中出现得越频繁，不作诊断或医学风险判断。",
                "source_version": "2026.07-hplp-40-niu-zhixu-canonical",
                "profile_model_id": None,
                "_meta": {
                    "canonical_source": "5_牛至旭资料中的40题版本",
                    "dimension_reference": "HPLP-II官方六维计分说明，按本地40题保留项映射",
                    "official_scoring_url": "https://deepblue.lib.umich.edu/bitstream/handle/2027.42/85349/HPLP_II-Scoring_Instructions.pdf",
                    "version_conflict_resolution": "按用户指定采用牛至旭40题版本；原42题草稿退出运行口径。",
                },
            }
        )
    save("assessment_worksheets.json", payload)
    return ids


def approve_catalog(worksheet_ids: set[str]) -> None:
    payload = load("scales_catalog.json")
    for item in payload["scales"]:
        if item["id"] not in worksheet_ids:
            item["approval"] = dict(APPROVAL)
            item["approval_status"] = "project_owner_approved_waiting_technical_chain"
            continue
        item["review_status"] = "pilot_approved"
        item["enabled"] = True
        item["excluded_from_user_flow"] = False
        item["not_open_reason"] = None
        item["exclusion_reason"] = None
        item["approval"] = dict(APPROVAL)
        if item["id"] == "hplp_c_health_promoting_lifestyle":
            item.update(
                {
                    "display_name": "健康促进生活方式量表（HPLP，40题）",
                    "search_keywords": ["HPLP", "HPLP-II", "健康促进生活方式", "生活习惯"],
                    "source_folder": "既往调研数据/5 牛至旭【中年女性自我关怀现状及其对主观幸福感的影响】/数据和问卷/问卷",
                    "source_files": ["四个量表文字版.docx", "健康促进生活方式量表-HPLP-R-II-40题.docx"],
                    "item_status": "verified_40_items",
                    "scoring_status": "six_dimensions_verified",
                    "notes": "采用用户指定的牛至旭40题版本；六维题号按HPLP-II官方计分说明映射，原42题草稿不再用于运行。",
                }
            )
    save("scales_catalog.json", payload)


def approve_drafts(worksheet_ids: set[str]) -> None:
    payload = load("scale_item_drafts.json")
    rows = payload if isinstance(payload, list) else payload.get("scales") or payload.get("drafts")
    for item in rows:
        if item["scale_id"] not in worksheet_ids:
            continue
        item["enabled"] = True
        item["review_status"] = "pilot_approved"
        item["approval"] = dict(APPROVAL)
        if item["scale_id"] != "hplp_c_health_promoting_lifestyle":
            continue
        item.update(
            {
                "display_name": "健康促进生活方式量表（HPLP，40题）",
                "source_folder": "既往调研数据/5 牛至旭【中年女性自我关怀现状及其对主观幸福感的影响】/数据和问卷/问卷",
                "source_files": ["四个量表文字版.docx", "健康促进生活方式量表-HPLP-R-II-40题.docx"],
                "item_status": "verified_40_items",
                "scoring_status": "six_dimensions_verified",
                "instructions": "请按最近一段时间的实际频率选择。共40题，所有题项按1-4分正向计分。",
                "dimensions": draft_dimensions(),
                "items": [
                    {
                        "item_code": f"HPLP{number:02d}",
                        "display_order": number,
                        "text": prompt,
                        "dimension": dimension_for_item(number),
                        "reverse_scored": False,
                    }
                    for number, prompt in enumerate(HPLP_ITEMS, 1)
                ],
                "scoring_notes": [
                    "六个维度分别取所属题项均值；综合观察为六维均值的平均值。",
                    "采用牛至旭资料中的40题版本，原42题草稿退出运行口径。",
                ],
            }
        )
    save("scale_item_drafts.json", payload)


def artifact_hash(model: dict) -> str:
    material = {key: value for key, value in model.items() if key != "artifact_hash"}
    canonical = json.dumps(material, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def recursive_replace(value, mapping: dict[str, str]):
    if isinstance(value, dict):
        return {mapping.get(key, key): recursive_replace(item, mapping) for key, item in value.items()}
    if isinstance(value, list):
        return [recursive_replace(item, mapping) for item in value]
    if isinstance(value, str):
        for old in sorted(mapping, key=len, reverse=True):
            value = value.replace(old, mapping[old])
        return value
    return value


def approve_profiles() -> None:
    paths = sorted((CONTENT / "profiles").glob("*.json"))
    canonical_hplp_id = None
    for path in paths:
        model = json.loads(path.read_text(encoding="utf-8"))
        if path.name == "profile_005_e6d75f52a4.json":
            mapping = {}
            for feature in model.get("features", []):
                match = re.search(r"Row(\d+)$", str(feature.get("source_variable") or ""))
                if not match:
                    continue
                number = int(match.group(1))
                mapping[str(feature["feature_id"])] = f"HPLP{number:02d}"
            model = recursive_replace(model, mapping)
            for feature in model.get("features", []):
                match = re.search(r"Row(\d+)$", str(feature.get("source_variable") or ""))
                if match:
                    number = int(match.group(1))
                    feature["question_no"] = number
                    feature["feature_id"] = f"HPLP{number:02d}"
                    feature["worksheet_question_id"] = f"HPLP{number:02d}"
            canonical_hplp_id = model["model_id"]
        model["approval"] = dict(APPROVAL)
        if path.name == "profile_007_9b08783201.json":
            model["admission_status"] = "deprecated"
            model["interpretation_approval_status"] = "pilot_approved"
            model["worksheet_id"] = None
            model["worksheet_link_status"] = "replaced_by_canonical_model"
            model["replacement_model_id"] = canonical_hplp_id
            model["approval_note"] = "已审核并保留作历史对照；运行时统一采用用户指定的牛至旭HPLP模型。"
        else:
            model["admission_status"] = "pilot_approved"
            model["interpretation_approval_status"] = "pilot_approved"
            model["worksheet_id"] = model.get("scale_id")
            model["worksheet_link_status"] = "confirmed"
            model["approval_note"] = "项目负责人于2026-07-12批准进入试点；低置信度、离群、数据不足和高风险状态仍保持阻断。"
        model["artifact_hash"] = artifact_hash(model)
        path.write_text(json.dumps(model, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    worksheets = load("assessment_worksheets.json")
    hplp = next(item for item in worksheets["worksheets"] if item["id"] == "hplp_c_health_promoting_lifestyle")
    hplp["profile_model_id"] = canonical_hplp_id
    save("assessment_worksheets.json", worksheets)


def main() -> int:
    worksheet_ids = approve_worksheets()
    approve_catalog(worksheet_ids)
    approve_drafts(worksheet_ids)
    approve_profiles()
    print(json.dumps({"approved_worksheets": len(worksheet_ids), "hplp_items": len(HPLP_ITEMS)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
