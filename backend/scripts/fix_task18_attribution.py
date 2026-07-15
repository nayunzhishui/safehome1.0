"""Restore the source-defined interaction for the 12-scenario attribution form."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
WORKSHEETS_PATH = ROOT / "content" / "assessment_worksheets.json"

OPTION_LABELS = {
    "ASQ_INTERNAL": [
        "完全由于他人或客观因素",
        "大多由于他人或客观因素",
        "较多由于他人或客观因素",
        "两方面相当",
        "较多由于自己",
        "大多由于自己",
        "完全由于自己",
    ],
    "ASQ_STABLE": [
        "完全不会再存在",
        "大多不会再存在",
        "较可能不再存在",
        "两端相当",
        "较可能继续存在",
        "大多会继续存在",
        "总是存在着",
    ],
    "ASQ_GLOBAL": [
        "仅影响这类事件",
        "基本只影响这类事件",
        "较多局限于这类事件",
        "两端相当",
        "也影响一些其他方面",
        "影响大多数其他方面",
        "影响生活所有方面",
    ],
}
QUESTION_TEXT = {
    "ASQ_INTERNAL": "你刚才写下的原因，更接近‘他人或客观因素’还是‘自己’？",
    "ASQ_STABLE": "在将来的同样情境中，你刚才写下的原因还会存在吗？",
    "ASQ_GLOBAL": "你刚才写下的原因只影响这类事件，还是也会影响生活的其他方面？",
}


def main() -> None:
    payload = json.loads(WORKSHEETS_PATH.read_text(encoding="utf-8"))
    worksheet = next(item for item in payload["worksheets"] if item.get("id") == "attribution_style_student_36")
    original = worksheet.get("questions") or []
    if [question.get("id") for question in original] != [f"ASQ{i:02d}" for i in range(1, 37)]:
        raise RuntimeError("归因问卷题号或题数与冻结结构不一致，拒绝自动修改")

    questions = []
    for scenario_index in range(12):
        group = original[scenario_index * 3 : scenario_index * 3 + 3]
        scenario = str(group[0]["prompt"]).split(" 请先想到", 1)[0].strip()
        questions.append(
            {
                "id": f"ASQ_CAUSE{scenario_index + 1:02d}",
                "prompt": f"{scenario} 请写出你认为的一个主要原因。",
                "type": "textarea",
                "required": True,
                "max_length": 200,
            }
        )
        for question in group:
            dimension = question["dimension"]
            question["prompt"] = f"{scenario} {QUESTION_TEXT[dimension]}"
            question["options"] = [
                {"label": f"{value} {label}", "value": str(value), "score": value}
                for value, label in enumerate(OPTION_LABELS[dimension], start=1)
            ]
            questions.append(question)

    worksheet["questions"] = questions
    worksheet["instructions"] = (
        "下面有12个情境。请先想象该情境发生在自己身上，写下一个你认为的主要原因，再围绕这个原因回答三个1到7的问题。"
        "1和7代表两端，中间数字表示接近程度。结果只用于阶段性自我观察。"
    )
    worksheet["scoring"] = (
        "每个情境的三个评分分别记录内外归因、稳定性和整体性。当前仅保存三个维度的原始均值；"
        "积极/消极情境组合与综合解释缺少本地完整计分依据，待心理专业复核，不向用户输出归因类型。"
    )
    worksheet["review_status"] = "content_verified_pending_scoring_and_rights_approval"
    worksheet["enabled_for_user"] = False
    worksheet["review_note"] = "2026-07-11 已与本地旧版 Word 核对12个情境、原因输入和三类专属选项；综合计分、版权和心理解释待审核。"

    WORKSHEETS_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
