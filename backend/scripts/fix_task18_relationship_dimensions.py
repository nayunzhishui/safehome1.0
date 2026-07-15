"""Restore item-level supportive dimensions for the Micro YSQ relationship worksheet."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
WORKSHEETS_PATH = ROOT / "content" / "assessment_worksheets.json"
DRAFTS_PATH = ROOT / "content" / "scale_item_drafts.json"
CATALOG_PATH = ROOT / "content" / "scales_catalog.json"

THEME_LABELS = [
    "被理解与关心担心", "离开与失去担心", "受伤与被利用担心", "自我价值担心", "归属与融入担心",
    "独立应对担心", "安全与灾难担心", "取悦与自我忽略", "情绪需求压抑", "特殊待遇期待",
    "坚持与自我管理", "过度照顾他人", "他人评价关注", "情绪表达抑制", "高标准压力",
    "严厉惩罚倾向", "理想化依赖期待", "冲突回避与屈从",
]


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    worksheets_payload = _load(WORKSHEETS_PATH)
    worksheet = next(item for item in worksheets_payload["worksheets"] if item.get("id") == "micro_ysq_relationship_18")
    if [question.get("id") for question in worksheet.get("questions", [])] != [f"YSQ{i}" for i in range(1, 19)]:
        raise RuntimeError("Micro YSQ 题号或题数与冻结结构不一致，拒绝自动修改")

    dimensions = []
    for index, (question, label) in enumerate(zip(worksheet["questions"], THEME_LABELS, strict=True), start=1):
        code = f"YSQ_THEME{index:02d}"
        question["dimension"] = code
        dimensions.append(
            {
                "code": code,
                "label": label,
                "item_ids": [question["id"]],
                "reverse_item_codes": [],
                "description": "单题主题得分，仅用于识别近期可关注线索。",
                "calculation": {"type": "mean"},
            }
        )
    worksheet["dimensions"] = dimensions
    worksheet["instructions"] = (
        "请根据这些描述与你近期关系体验的符合程度作答。每题对应一个可观察主题，结果用于寻找可练习线索，"
        "不用于诊断、人格判断或图式标签。"
    )
    worksheet["scoring"] = (
        "18题各自保留为一个支持性主题维度，分值为该题1-6原始得分；聚类继续使用18个题项级特征。"
        "不计算诊断性总分，不把单题高分解释为固定特征。"
    )
    worksheet["review_status"] = "content_verified_pending_rights_and_psychology_approval"
    worksheet["enabled_for_user"] = False
    worksheet["review_note"] = "18个题项级聚类特征已同步为18个支持性主题维度；主题命名、版权和心理解释待审核。"

    drafts_payload = _load(DRAFTS_PATH)
    draft = next(item for item in drafts_payload["drafts"] if item.get("scale_id") == "micro_ysq_relationship_18")
    draft["dimensions"] = [
        {
            "code": dimension["code"],
            "label": dimension["label"],
            "item_codes": dimension["item_ids"],
            "calculation": {"type": "mean"},
        }
        for dimension in dimensions
    ]
    for item, dimension in zip(draft["items"], dimensions, strict=True):
        item["dimension"] = dimension["code"]
    draft.update(
        enabled=False,
        review_status="content_verified_pending_rights_and_psychology_approval",
        scoring_status="verified_item_level_dimensions_pending_interpretation_review",
        instructions=worksheet["instructions"],
        scoring_notes=[worksheet["scoring"]],
    )

    catalog_payload = _load(CATALOG_PATH)
    catalog = next(item for item in catalog_payload["scales"] if item.get("id") == "micro_ysq_relationship_18")
    catalog.update(
        enabled=False,
        excluded_from_user_flow=True,
        review_status="content_verified_pending_rights_and_psychology_approval",
        item_status="verified_item_level_dimensions",
        scoring_status="verified_item_level_dimensions_pending_interpretation_review",
        not_open_reason="18个题项级维度已接通；主题命名、版权和心理解释仍待审核。",
        exclusion_reason="pending_rights_and_psychology_approval",
        notes="聚类和结果统一使用18个题项级支持性主题，不再压缩为单一均值维度。",
    )

    _write(WORKSHEETS_PATH, worksheets_payload)
    _write(DRAFTS_PATH, drafts_payload)
    _write(CATALOG_PATH, catalog_payload)


if __name__ == "__main__":
    main()
