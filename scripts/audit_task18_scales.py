"""Audit assessment worksheets without changing source content."""

from __future__ import annotations

import csv
import json
import re
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKSHEETS_PATH = ROOT / "content" / "assessment_worksheets.json"
CATALOG_PATH = ROOT / "content" / "scales_catalog.json"
CSV_OUTPUT = ROOT / "docs" / "02_专项进度与验收" / "任务十八全量量表内容与治理审计.csv"
MD_OUTPUT = ROOT / "docs" / "02_专项进度与验收" / "任务十八全量量表内容与治理审计_20260711.md"

APPROVED_STATUSES = {
    "approved",
    "pilot_ready",
    "pilot_approved",
    "production_approved",
    "enabled",
    "trial_enabled",
}
GENERIC_INSTRUCTION = "请根据最近一段时间的真实情况填写。结果只用于自我观察、画像候选和练习参考，不用于诊断、筛查或评价人格。"
CONTAMINATION_PATTERNS = {
    "标题混入题项": re.compile(r"Measuring Your|调查量表（|编者：|编制时间"),
    "指导语混入题项": re.compile(r"请仔细阅读|请您仔细阅读|以下\s*\d+\s*种说法|答案没有对错|填写日期"),
    "计分说明混入题项": re.compile(r"反向[计记]分|计算平均分|[计记]分方法|采用\d+级[计记]分|得分范围|总分为|\d\s*=\s*\d"),
    "选项文本混入题项": re.compile(r"非常同意\s+同意|从不如此\s+总是如此|在相应的数字上"),
    "来源信息混入题项": re.compile(r"https?://|北京师范大学|心理学院|\d{4}年"),
}


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _issue(level: str, worksheet_id: str, area: str, location: str, message: str) -> dict[str, str]:
    return {
        "level": level,
        "worksheet_id": worksheet_id,
        "area": area,
        "location": location,
        "message": message,
    }


def audit_worksheet(worksheet: dict, catalog: dict | None) -> list[dict[str, str]]:
    worksheet_id = str(worksheet.get("id") or "missing")
    issues: list[dict[str, str]] = []
    review_status = str(worksheet.get("review_status") or "missing")
    enabled = worksheet.get("enabled_for_user") is True

    if enabled and review_status not in APPROVED_STATUSES:
        issues.append(_issue("blocker", worksheet_id, "governance", "worksheet", f"enabled_for_user=true，但 review_status={review_status}"))
    if catalog and bool(catalog.get("enabled")) != enabled:
        issues.append(_issue("error", worksheet_id, "governance", "catalog", "worksheet 与 scales_catalog 的启用状态不一致"))

    instructions = str(worksheet.get("instructions") or worksheet.get("instruction") or "").strip()
    if not instructions:
        issues.append(_issue("error", worksheet_id, "instruction", "worksheet", "缺少量表指导语"))
    elif instructions == GENERIC_INSTRUCTION:
        issues.append(_issue("warning", worksheet_id, "instruction", "worksheet", "仍使用统一指导语，需按原量表时间范围和作答方式复核"))

    questions = worksheet.get("questions") or []
    question_ids = [str(question.get("id") or "") for question in questions]
    duplicates = sorted(item for item, count in Counter(question_ids).items() if item and count > 1)
    if not questions:
        issues.append(_issue("blocker", worksheet_id, "question", "worksheet", "无题项"))
    if "" in question_ids:
        issues.append(_issue("error", worksheet_id, "question", "worksheet", "存在无 id 题项"))
    if duplicates:
        issues.append(_issue("error", worksheet_id, "question", "worksheet", f"题项 id 重复：{', '.join(duplicates)}"))

    for question in questions:
        question_id = str(question.get("id") or "missing")
        prompt = str(question.get("prompt") or question.get("text") or "").strip()
        if not prompt:
            issues.append(_issue("error", worksheet_id, "question", question_id, "题干为空"))
        for label, pattern in CONTAMINATION_PATTERNS.items():
            if pattern.search(prompt):
                issues.append(_issue("error", worksheet_id, "question", question_id, label))

        options = question.get("options") or []
        if not options and question.get("type") in {"text", "textarea", "free_text"}:
            continue
        if len(options) < 2:
            issues.append(_issue("error", worksheet_id, "option", question_id, "有效选项少于 2 个"))
            continue
        values = [str(option.get("value")) for option in options]
        labels = [str(option.get("label") or "").strip() for option in options]
        if len(values) != len(set(values)):
            issues.append(_issue("error", worksheet_id, "option", question_id, "选项 value 重复"))
        if any(not label for label in labels):
            issues.append(_issue("error", worksheet_id, "option", question_id, "存在空选项标签"))
        embedded_choices = re.search(r"（1）.+（2）.+（3）", prompt)
        if embedded_choices and not any(choice in "".join(labels) for choice in ("一个也没有", "1—2个", "3—5个")):
            issues.append(_issue("error", worksheet_id, "option", question_id, "题干自带专属选项，但页面仍使用统一选项模板"))

    dimensions = worksheet.get("dimensions") or []
    dimension_item_ids = [str(item_id) for dimension in dimensions for item_id in (dimension.get("item_ids") or [])]
    scored_question_ids = {
        str(question.get("id"))
        for question in questions
        if question.get("options") and question.get("id")
    }
    unknown_ids = sorted(set(dimension_item_ids) - set(question_ids))
    uncovered_ids = sorted(scored_question_ids - set(dimension_item_ids))
    if unknown_ids:
        issues.append(_issue("error", worksheet_id, "dimension", "worksheet", f"维度引用不存在题项：{', '.join(unknown_ids)}"))
    if questions and dimensions and uncovered_ids:
        issues.append(_issue("warning", worksheet_id, "dimension", "worksheet", f"未进入任何维度的题项：{', '.join(uncovered_ids)}"))
    if questions and not dimensions:
        issues.append(_issue("warning", worksheet_id, "dimension", "worksheet", "缺少维度定义"))

    scoring = str(worksheet.get("scoring") or "").strip()
    if not scoring:
        issues.append(_issue("error", worksheet_id, "scoring", "worksheet", "缺少计分规则说明"))
    elif re.search(r"需人工复核|当前只记录|待.*复核|缺少.*依据|候选", scoring):
        issues.append(_issue("blocker", worksheet_id, "scoring", "worksheet", "计分规则明确标记为待人工复核"))

    return issues


def audit() -> dict:
    worksheets = _load(WORKSHEETS_PATH).get("worksheets", [])
    catalog = {item.get("id"): item for item in _load(CATALOG_PATH).get("scales", [])}
    issues = [issue for worksheet in worksheets for issue in audit_worksheet(worksheet, catalog.get(worksheet.get("id")))]
    issue_counts = Counter(issue["level"] for issue in issues)
    affected = sorted(set(issue["worksheet_id"] for issue in issues))
    return {
        "generated_at": "2026-07-12",
        "worksheet_count": len(worksheets),
        "affected_count": len(affected),
        "issue_counts": dict(sorted(issue_counts.items())),
        "issues": issues,
    }


def write_reports(payload: dict) -> None:
    CSV_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with CSV_OUTPUT.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["level", "worksheet_id", "area", "location", "message"])
        writer.writeheader()
        writer.writerows(payload["issues"])

    counts = payload["issue_counts"]
    lines = [
        "# 任务十八全量量表内容与治理审计",
        "",
        "生成日期：2026-07-12",
        "",
        "## 1. 结论",
        "",
        f"- 共审计 {payload['worksheet_count']} 份 worksheet，{payload['affected_count']} 份存在至少一项待处理问题。",
        f"- blocker={counts.get('blocker', 0)}，error={counts.get('error', 0)}，warning={counts.get('warning', 0)}。",
        "- blocker 未清零前，该量表不得面向普通用户开放；内容修正通过也不等同于版权、心理或伦理签字通过。",
        "- CSV 是逐项整改清单，本文件按量表汇总，二者均由同一审计脚本生成。",
        "",
        "## 2. 逐量表问题",
        "",
    ]
    grouped: dict[str, list[dict[str, str]]] = {}
    for issue in payload["issues"]:
        grouped.setdefault(issue["worksheet_id"], []).append(issue)
    for worksheet_id in sorted(grouped):
        lines.append(f"### {worksheet_id}")
        lines.append("")
        for issue in grouped[worksheet_id]:
            lines.append(f"- [{issue['level']}] {issue['area']} / {issue['location']}：{issue['message']}")
        lines.append("")
    MD_OUTPUT.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> None:
    payload = audit()
    write_reports(payload)
    print(json.dumps({key: value for key, value in payload.items() if key != "issues"}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
