"""Audit enabled assessment worksheet content for manual review."""

from __future__ import annotations

import csv
import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
WORKSHEETS_PATH = PROJECT_ROOT / "content" / "assessment_worksheets.json"
OUTPUT_PATH = PROJECT_ROOT / "docs" / "02_专项进度与验收" / "任务十量表题项选项自动审核.csv"


def _option_stats(questions: list[dict]) -> tuple[int, int, int]:
    option_count = 0
    empty_option_count = 0
    long_option_count = 0
    for question in questions:
        options = question.get("options") or []
        option_count += len(options)
        for option in options:
            label = str(option.get("label") or "")
            if not label.strip():
                empty_option_count += 1
            if len(label) >= 18:
                long_option_count += 1
    return option_count, empty_option_count, long_option_count


def main() -> int:
    payload = json.loads(WORKSHEETS_PATH.read_text(encoding="utf-8"))
    rows = []
    for worksheet in payload.get("worksheets", []):
        if not worksheet.get("enabled_for_user"):
            continue
        questions = worksheet.get("questions") or []
        option_count, empty_option_count, long_option_count = _option_stats(questions)
        sensitive = worksheet.get("sensitive_category") or "none"
        has_boundary = bool(worksheet.get("boundary_notice") and worksheet.get("result_disclaimer"))
        rows.append(
            {
                "worksheet_id": worksheet.get("id"),
                "量表名称": worksheet.get("display_title") or worksheet.get("source_title") or worksheet.get("id"),
                "enabled_for_user": worksheet.get("enabled_for_user"),
                "题项数": len(questions),
                "选项总数": option_count,
                "空选项数": empty_option_count,
                "长选项数": long_option_count,
                "敏感类别": sensitive,
                "边界文案完整": "是" if has_boundary else "否",
                "计分状态": "需人工复核",
                "建议": "真机重点验收长选项显示" if long_option_count else "按人工清单核对题项和计分",
            }
        )
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()) if rows else [])
        if rows:
            writer.writeheader()
            writer.writerows(rows)
    print(json.dumps({"output": str(OUTPUT_PATH), "count": len(rows)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
