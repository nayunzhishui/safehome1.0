"""Audit every assessment worksheet for structural and human-review gaps."""

from __future__ import annotations

import csv
import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONTENT_ROOT = PROJECT_ROOT / "content"
WORKSHEETS_PATH = CONTENT_ROOT / "assessment_worksheets.json"
TASK10_OUTPUT_PATH = PROJECT_ROOT / "docs" / "02_专项进度与验收" / "任务十量表题项选项自动审核.csv"
TASK12_OUTPUT_PATH = PROJECT_ROOT / "docs" / "02_专项进度与验收" / "任务十二全量量表题项选项计分审核.csv"


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


def build_audit_rows(
    worksheets: list[dict],
    *,
    drafts: dict[str, dict],
    catalog: dict[str, dict],
) -> list[dict]:
    rows: list[dict] = []
    for worksheet in worksheets:
        worksheet_id = str(worksheet.get("id") or "")
        questions = worksheet.get("questions") or []
        option_count, empty_option_count, long_option_count = _option_stats(questions)
        reverse_count = sum(1 for question in questions if question.get("reverse_scored"))
        dimensions = worksheet.get("dimensions") or []
        scoring = str(worksheet.get("scoring") or "").strip()
        source_file = str(worksheet.get("source_file") or "").strip()
        review_status = str(worksheet.get("review_status") or "").strip()
        draft_count = len((drafts.get(worksheet_id) or {}).get("items") or [])
        sensitive = worksheet.get("sensitive_category") or "none"
        has_boundary = bool(worksheet.get("boundary_notice") and worksheet.get("result_disclaimer"))
        structural_gaps: list[str] = []
        if not questions:
            structural_gaps.append("无题项")
        if empty_option_count:
            structural_gaps.append("存在空选项")
        if not scoring:
            structural_gaps.append("计分文本为空")
        if not source_file:
            structural_gaps.append("source_file为空")
        if not review_status:
            structural_gaps.append("review_status为空")
        if not has_boundary:
            structural_gaps.append("边界文案不完整")
        if draft_count and draft_count != len(questions):
            structural_gaps.append("草稿与worksheet题数不一致")
        rows.append(
            {
                "worksheet_id": worksheet_id,
                "量表名称": worksheet.get("display_title") or worksheet.get("source_title") or worksheet_id,
                "enabled_for_user": bool(worksheet.get("enabled_for_user")),
                "题项数": len(questions),
                "草稿题项数": draft_count,
                "题项数与草稿一致": "是" if draft_count == len(questions) and draft_count > 0 else ("不适用" if not draft_count else "否"),
                "选项总数": option_count,
                "空选项数": empty_option_count,
                "长选项数": long_option_count,
                "反向题数": reverse_count,
                "维度数": len(dimensions),
                "计分是否为空": "否" if scoring else "是",
                "计分文本含人工复核": "是" if "人工复核" in scoring or "待复核" in scoring else "否",
                "source_file是否为空": "否" if source_file else "是",
                "review_status": review_status or "缺失",
                "台账存在": "是" if worksheet_id in catalog else "否",
                "敏感类别": sensitive,
                "边界文案完整": "是" if has_boundary else "否",
                "profile_model_id": worksheet.get("profile_model_id") or "",
                "自动审核状态": "结构通过，待人工验收" if not structural_gaps else "；".join(structural_gaps),
                "人工验收重点": "题干逐字一致、题序、选项分值、反向题、维度、授权和非诊断解释",
            }
        )
    return rows


def _write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0].keys()) if rows else [])
        if rows:
            writer.writeheader()
            writer.writerows(rows)


def main() -> int:
    worksheets_payload = json.loads(WORKSHEETS_PATH.read_text(encoding="utf-8"))
    drafts_payload = json.loads((CONTENT_ROOT / "scale_item_drafts.json").read_text(encoding="utf-8"))
    catalog_payload = json.loads((CONTENT_ROOT / "scales_catalog.json").read_text(encoding="utf-8"))
    worksheets = worksheets_payload.get("worksheets", [])
    drafts = {item.get("scale_id"): item for item in drafts_payload.get("drafts", []) if item.get("scale_id")}
    catalog = {item.get("id"): item for item in catalog_payload.get("scales", []) if item.get("id")}
    rows = build_audit_rows(worksheets, drafts=drafts, catalog=catalog)
    _write_csv(TASK12_OUTPUT_PATH, rows)
    _write_csv(TASK10_OUTPUT_PATH, [row for row in rows if row["enabled_for_user"]])
    gap_count = sum(1 for row in rows if row["自动审核状态"] != "结构通过，待人工验收")
    print(
        json.dumps(
            {
                "task12_output": str(TASK12_OUTPUT_PATH),
                "task10_compat_output": str(TASK10_OUTPUT_PATH),
                "count": len(rows),
                "structural_gap_count": gap_count,
            },
            ensure_ascii=False,
        )
    )
    return 0 if gap_count == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
