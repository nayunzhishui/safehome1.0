"""Build Task 12 acceptance and local-source audit artifacts.

The script deliberately separates structural automation from human review. It
can prove that files and content records exist and compare item counts, but it
never upgrades a scale to approved or claims wording/scoring correctness.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ACCEPTANCE_WORKBOOK = Path(r"D:\桌面\Desktop\补录12量表人工验收表.xlsx")
DEFAULT_SOURCE_ROOT = Path(
    r"D:\codex\workspace\safehome1.0其他内容\夏老师文件\2026年6月18日发给董俊杰的(1)\测评问卷-量表"
)
DEFAULT_MATRIX_OUTPUT = PROJECT_ROOT / "docs" / "02_专项进度与验收" / "任务十二补录12量表审核矩阵.md"
DEFAULT_SOURCE_OUTPUT = PROJECT_ROOT / "docs" / "02_专项进度与验收" / "任务十二补录12量表本地来源抽取表.md"

MAIN_NS = {"x": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
REL_NS = {"r": "http://schemas.openxmlformats.org/package/2006/relationships"}
OFFICE_REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
REQUIRED_IDS = {
    "big_five_bfi_60",
    "sleep_isi_psqi",
    "attribution_style_student_36",
    "ghq12_general_health",
    "epq_emotional_stability_24",
    "phq9_cesd10_depression",
    "gad7_anxiety",
    "perceived_social_support_psss",
    "cognitive_curiosity_student",
    "emotional_intelligence_eis_33",
    "family_cohesion_adaptability",
    "parental_autonomy_support",
}


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _shared_strings(archive: ZipFile) -> list[str]:
    try:
        root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
    except KeyError:
        return []
    return ["".join(node.text or "" for node in item.findall(".//x:t", MAIN_NS)) for item in root.findall("x:si", MAIN_NS)]


def _sheet_path(archive: ZipFile, sheet_name: str) -> str:
    workbook = ET.fromstring(archive.read("xl/workbook.xml"))
    relationship_id = None
    relation_attribute = f"{{{OFFICE_REL}}}id"
    for sheet in workbook.findall(".//x:sheet", MAIN_NS):
        if sheet.attrib.get("name") == sheet_name:
            relationship_id = sheet.attrib.get(relation_attribute)
            break
    if not relationship_id:
        raise ValueError(f"workbook does not contain sheet: {sheet_name}")
    relationships = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
    for relation in relationships.findall("r:Relationship", REL_NS):
        if relation.attrib.get("Id") == relationship_id:
            target = relation.attrib["Target"].replace("\\", "/").lstrip("/")
            return target if target.startswith("xl/") else f"xl/{target}"
    raise ValueError(f"missing worksheet relationship for: {sheet_name}")


def _column_index(reference: str) -> int:
    letters = re.match(r"[A-Z]+", reference.upper())
    if not letters:
        return 0
    value = 0
    for letter in letters.group(0):
        value = value * 26 + ord(letter) - ord("A") + 1
    return value - 1


def _cell_value(cell: ET.Element, shared: list[str]):
    cell_type = cell.attrib.get("t")
    if cell_type == "inlineStr":
        return "".join(node.text or "" for node in cell.findall(".//x:t", MAIN_NS))
    value_node = cell.find("x:v", MAIN_NS)
    if value_node is None or value_node.text is None:
        return None
    raw = value_node.text
    if cell_type == "s":
        return shared[int(raw)]
    if cell_type == "b":
        return raw == "1"
    try:
        number = float(raw)
        return int(number) if number.is_integer() else number
    except ValueError:
        return raw


def read_xlsx_rows(path: Path, sheet_name: str) -> list[list[object]]:
    """Read cell values from a named XLSX sheet using only the stdlib."""
    with ZipFile(path) as archive:
        shared = _shared_strings(archive)
        root = ET.fromstring(archive.read(_sheet_path(archive, sheet_name)))
    output: list[list[object]] = []
    for row in root.findall(".//x:sheetData/x:row", MAIN_NS):
        values: list[object] = []
        for cell in row.findall("x:c", MAIN_NS):
            index = _column_index(cell.attrib.get("r", "A1"))
            while len(values) <= index:
                values.append(None)
            values[index] = _cell_value(cell, shared)
        output.append(values)
    return output


def load_acceptance_rows(path: Path) -> list[dict]:
    rows = read_xlsx_rows(path, "验收总览")
    header_index = next((index for index, row in enumerate(rows) if "量表ID" in row), None)
    if header_index is None:
        raise ValueError("验收总览中未找到量表ID表头")
    headers = [str(value).strip() if value is not None else "" for value in rows[header_index]]
    records: list[dict] = []
    for row in rows[header_index + 1 :]:
        record = {header: row[index] if index < len(row) else None for index, header in enumerate(headers) if header}
        if record.get("量表ID"):
            records.append(record)
    return records


def _split_source_names(value: object) -> list[str]:
    return [item.strip() for item in re.split(r"[；;]", str(value or "")) if item.strip()]


def _source_index(source_root: Path) -> dict[str, list[Path]]:
    index: dict[str, list[Path]] = {}
    for path in source_root.rglob("*"):
        if path.is_file():
            index.setdefault(path.name.casefold(), []).append(path)
    return index


def _choose_source(candidates: list[Path], folder_hint: str) -> Path:
    hint = folder_hint.replace("\\", "/").casefold()
    for candidate in candidates:
        if hint and hint in candidate.parent.as_posix().casefold():
            return candidate
    return candidates[0]


def build_scale_audits(rows: list[dict], *, content_dir: Path, source_root: Path) -> list[dict]:
    drafts = {item["scale_id"]: item for item in _load_json(content_dir / "scale_item_drafts.json").get("drafts", [])}
    worksheets = {item["id"]: item for item in _load_json(content_dir / "assessment_worksheets.json").get("worksheets", [])}
    catalog = {item["id"]: item for item in _load_json(content_dir / "scales_catalog.json").get("scales", [])}
    sources = _source_index(source_root)
    audits: list[dict] = []
    for row in rows:
        scale_id = str(row.get("量表ID") or "").strip()
        source_names = _split_source_names(row.get("来源文件"))
        found_paths: list[Path] = []
        missing_names: list[str] = []
        for name in source_names:
            candidates = sources.get(Path(name).name.casefold(), [])
            if candidates:
                found_paths.append(_choose_source(candidates, str(row.get("来源文件夹") or "")))
            else:
                missing_names.append(name)
        draft_count = len((drafts.get(scale_id) or {}).get("items") or [])
        worksheet_count = len((worksheets.get(scale_id) or {}).get("questions") or [])
        expected = row.get("预期题项数")
        expected_count = expected if isinstance(expected, int) else None
        gap_types: list[str] = []
        if expected_count is None:
            gap_types.append("验收表未给出可比较的预期题项数")
        elif draft_count != expected_count or worksheet_count != expected_count:
            gap_types.append("题项数与验收预期不一致")
        if missing_names:
            gap_types.append("存在未找到的登记来源文件")
        review_status = str((catalog.get(scale_id) or {}).get("review_status") or "missing_catalog")
        if review_status != "fully_approved":
            gap_types.append("需人工逐题和计分复核")
        audits.append(
            {
                "scale_id": scale_id,
                "display_name": row.get("量表名称") or (catalog.get(scale_id) or {}).get("display_name") or "",
                "source_folder": row.get("来源文件夹") or "",
                "source_names": source_names,
                "found_sources": [path.name for path in found_paths],
                "found_paths": [path for path in found_paths],
                "missing_sources": missing_names,
                "expected_count": expected,
                "draft_count": draft_count,
                "worksheet_count": worksheet_count,
                "sensitive_category": row.get("敏感类别") or (catalog.get(scale_id) or {}).get("sensitive_category") or "none",
                "review_status": review_status,
                "gap_types": gap_types or ["无结构性缺口"],
            }
        )
    return audits


def _next_action(audit: dict) -> str:
    if audit["draft_count"] == 0 or audit["worksheet_count"] == 0:
        return "先补可靠题项、选项和计分依据；未确认前继续隐藏入口。"
    if audit["missing_sources"]:
        return "补齐登记来源或修正来源文件名，再逐题人工验收。"
    return "结构已接入；逐题核对文字、题序、选项、反向题、维度与授权。"


def render_acceptance_matrix(audits: list[dict]) -> str:
    lines = [
        "# 任务十二补录12量表审核矩阵",
        "",
        "生成方式：`python backend/scripts/audit_task12_scale_sources.py`。本表只确认结构和来源可定位性，不替代题项原文、授权、计分和伦理人工验收。",
        "",
        "| 量表ID | 量表名称 | 来源文件夹 | 预期/草稿/小程序题数 | 当前状态 | 缺口类型 | 下一步动作 |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for audit in audits:
        counts = f"{audit['expected_count']}/{audit['draft_count']}/{audit['worksheet_count']}"
        gaps = "；".join(audit["gap_types"])
        lines.append(
            f"| `{audit['scale_id']}` | {audit['display_name']} | {audit['source_folder']} | {counts} | "
            f"{audit['review_status']} | {gaps} | {_next_action(audit)} |"
        )
    lines.extend(
        [
            "",
            "## 自动化结论",
            "",
            f"- 验收表量表数：{len(audits)}。",
            f"- 已有草稿和小程序题项的量表：{sum(1 for item in audits if item['draft_count'] and item['worksheet_count'])}。",
            f"- 仍缺题项链路的量表：{sum(1 for item in audits if not item['draft_count'] or not item['worksheet_count'])}。",
            "- 所有量表仍需人工复核，脚本不会把 `pilot_review_required` 或 `metadata_only` 自动升级为已批准。",
            "",
        ]
    )
    return "\n".join(lines)


def _probe_note(path: Path) -> str:
    suffix = path.suffix.casefold()
    if suffix == ".docx":
        try:
            with ZipFile(path) as archive:
                root = ET.fromstring(archive.read("word/document.xml"))
            ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
            paragraphs = ["".join(node.text or "" for node in p.findall(".//w:t", ns)).strip() for p in root.findall(".//w:p", ns)]
            paragraphs = [item for item in paragraphs if item]
            return f"可自动读取 DOCX，共 {len(paragraphs)} 个非空段落；题项和计分仍需人工逐字核对。"
        except Exception as exc:
            return f"DOCX 读取失败：{type(exc).__name__}。"
    if suffix == ".sps":
        raw = path.read_bytes()
        for encoding in ("utf-8-sig", "gb18030", "utf-16"):
            try:
                text = raw.decode(encoding)
                return f"可读取 SPSS 语法，共 {len(text.splitlines())} 行；可核对变量和公式，但通常不含完整题干。"
            except UnicodeDecodeError:
                continue
        return "SPSS 语法编码未识别，需人工打开。"
    if suffix == ".xlsx":
        try:
            with ZipFile(path) as archive:
                workbook = ET.fromstring(archive.read("xl/workbook.xml"))
            names = [sheet.attrib.get("name", "") for sheet in workbook.findall(".//x:sheet", MAIN_NS)]
            return f"可读取 XLSX，工作表：{'、'.join(names)}；复杂计分公式仍需人工复核。"
        except Exception as exc:
            return f"XLSX 读取失败：{type(exc).__name__}。"
    if suffix == ".doc":
        return "旧版 DOC；项目脚本可调用 LibreOffice 转换，转换结果仍需和原文件人工对照。"
    if suffix == ".pdf":
        return "PDF 可做文本抽取；扫描页、选项布局和页码需人工打开复核。"
    if suffix == ".sav":
        return "SPSS SAV 可读取变量标签；题项文字和维度需与语法/问卷交叉复核。"
    if suffix in {".jpg", ".jpeg", ".png", ".gif"}:
        return "图片来源需 OCR 后人工逐字复核，不直接自动写入正式题库。"
    return f"{suffix or '未知格式'} 仅完成文件定位，需人工复核。"


def render_source_report(audits: list[dict], source_root: Path) -> str:
    lines = [
        "# 任务十二补录12量表本地来源抽取表",
        "",
        f"本地来源根目录：`{source_root}`。自动化只记录可读取性与结构证据，不把抽取文本直接认定为正式题项。",
        "",
        "| 量表ID | 登记来源 | 本地定位 | 自动读取结果 | 仍需人工验收 |",
        "| --- | --- | --- | --- | --- |",
    ]
    for audit in audits:
        registered = "；".join(audit["source_names"]) or "未登记"
        located = "；".join(path.relative_to(source_root).as_posix() for path in audit["found_paths"]) or "未找到"
        probe = "；".join(_probe_note(path) for path in audit["found_paths"]) or "没有可自动读取的本地文件。"
        human = "题干逐字一致、题序、选项分值、反向题、维度、授权和用户端开放边界。"
        lines.append(f"| `{audit['scale_id']}` | {registered} | {located} | {probe} | {human} |")
    lines.extend(
        [
            "",
            "## 关键缺口",
            "",
            "- `sleep_isi_psqi`：本地有 ISI/PSQI 说明、旧版 Word、PDF 和表格，但复杂题项与计分尚未形成可靠统一版本。",
            "- `cognitive_curiosity_student`：本地 SPSS 语法可确认计分变量，未发现可直接核对的中文完整题干。",
            "- `family_cohesion_adaptability`：本地仅确认分类语法，未发现完整题项正文。",
            "- `parental_autonomy_support`：`9题项.docx` 可读取，但既有审查仅发现来源引用，未确认 9 条正式题干。",
            "- 以上四项保持 `metadata_only` 和隐藏入口，直到可靠来源、授权和人工核对完成。",
            "",
        ]
    )
    return "\n".join(lines)


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--acceptance-workbook", type=Path, default=DEFAULT_ACCEPTANCE_WORKBOOK)
    parser.add_argument("--source-root", type=Path, default=DEFAULT_SOURCE_ROOT)
    parser.add_argument("--content-dir", type=Path, default=PROJECT_ROOT / "content")
    parser.add_argument("--matrix-output", type=Path, default=DEFAULT_MATRIX_OUTPUT)
    parser.add_argument("--source-output", type=Path, default=DEFAULT_SOURCE_OUTPUT)
    args = parser.parse_args()
    rows = load_acceptance_rows(args.acceptance_workbook)
    actual_ids = {str(row.get("量表ID") or "").strip() for row in rows}
    if actual_ids != REQUIRED_IDS:
        missing = sorted(REQUIRED_IDS - actual_ids)
        extra = sorted(actual_ids - REQUIRED_IDS)
        raise SystemExit(f"验收表ID不一致 missing={missing} extra={extra}")
    audits = build_scale_audits(rows, content_dir=args.content_dir, source_root=args.source_root)
    _write(args.matrix_output, render_acceptance_matrix(audits))
    _write(args.source_output, render_source_report(audits, args.source_root))
    print(f"task12_scale_audit_ok scales={len(audits)} matrix={args.matrix_output} sources={args.source_output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
