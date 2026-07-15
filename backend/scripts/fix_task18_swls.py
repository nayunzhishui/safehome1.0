"""Apply the source-verified SWLS correction without touching other worksheets."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
WORKSHEETS_PATH = ROOT / "content" / "assessment_worksheets.json"

PROMPTS = [
    "大多数情况下，我的生活接近理想状态。",
    "我的生活状态很好。",
    "我对自己的生活感到满意。",
    "到目前为止，我已经得到了我认为生活中最重要的事物。",
    "如果我可以再活一次，我不想改变任何事情。",
]
OPTION_LABELS = ["强烈反对", "不同意", "基本不同意", "中立", "基本同意", "同意", "非常同意"]


def main() -> None:
    payload = json.loads(WORKSHEETS_PATH.read_text(encoding="utf-8"))
    worksheet = next(item for item in payload["worksheets"] if item.get("id") == "swls_life_satisfaction")
    questions = worksheet.get("questions") or []
    if [question.get("id") for question in questions] != [f"SWLS{i:02d}" for i in range(1, 6)]:
        raise RuntimeError("SWLS 题号或题数与冻结结构不一致，拒绝自动修改")

    worksheet["instructions"] = (
        "以下5种说法描述你对生活的整体感受。请根据实际情况，从1（强烈反对）到7（非常同意）中选择最符合的一项。"
        "结果只用于阶段性自我观察。"
    )
    for question, prompt in zip(questions, PROMPTS, strict=True):
        question["prompt"] = prompt
        options = question.get("options") or []
        if len(options) != 7:
            raise RuntimeError(f"{question['id']} 不是7级选项，拒绝自动修改")
        for value, (option, label) in enumerate(zip(options, OPTION_LABELS, strict=True), start=1):
            option.update(label=f"{value} {label}", value=str(value), score=value)

    worksheet["dimensions"][0]["description"] = "5题均按1-7分正向计分，总分为5题得分之和。"
    worksheet["scoring"] = "5题均按1-7分正向计分，总分为5题得分之和；不使用诊断、人格标签或固定结论。"
    worksheet["review_status"] = "content_verified_pending_rights_and_psychology_approval"
    worksheet["enabled_for_user"] = False
    worksheet["review_note"] = "2026-07-11 已与本地 Word 逐项核对5题、选项方向和计分；待版权和心理审核后再开放。"

    WORKSHEETS_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
