from __future__ import annotations

import importlib.util
from pathlib import Path
from zipfile import ZipFile


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _load_script(name: str):
    path = PROJECT_ROOT / "backend" / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"task12_{name}", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


_scale_audit = _load_script("audit_task12_scale_sources")
_content_audit = _load_script("audit_assessment_content")
build_scale_audits = _scale_audit.build_scale_audits
load_acceptance_rows = _scale_audit.load_acceptance_rows
render_acceptance_matrix = _scale_audit.render_acceptance_matrix
build_audit_rows = _content_audit.build_audit_rows


def _write_minimal_xlsx(path: Path) -> None:
    shared = [
        "量表ID",
        "量表名称",
        "来源文件夹",
        "来源文件",
        "预期题项数",
        "草稿题项数",
        "小程序题项数",
        "敏感类别",
        "big_five_bfi_60",
        "大五人格问卷（60题简版）",
        "大五人格",
        "大五人格问卷.doc",
        "personality",
    ]
    shared_xml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        + "".join(f"<si><t>{value}</t></si>" for value in shared)
        + "</sst>"
    )
    sheet_xml = """<?xml version="1.0" encoding="UTF-8"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <sheetData>
    <row r="1">
      <c r="A1" t="s"><v>0</v></c><c r="B1" t="s"><v>1</v></c>
      <c r="C1" t="s"><v>2</v></c><c r="D1" t="s"><v>3</v></c>
      <c r="E1" t="s"><v>4</v></c><c r="F1" t="s"><v>5</v></c>
      <c r="G1" t="s"><v>6</v></c><c r="H1" t="s"><v>7</v></c>
    </row>
    <row r="2">
      <c r="A2" t="s"><v>8</v></c><c r="B2" t="s"><v>9</v></c>
      <c r="C2" t="s"><v>10</v></c><c r="D2" t="s"><v>11</v></c>
      <c r="E2"><v>60</v></c><c r="F2"><v>60</v></c><c r="G2"><v>60</v></c>
      <c r="H2" t="s"><v>12</v></c>
    </row>
  </sheetData>
</worksheet>"""
    workbook_xml = """<?xml version="1.0" encoding="UTF-8"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"
 xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <sheets><sheet name="验收总览" sheetId="1" r:id="rId1"/></sheets>
</workbook>"""
    rels_xml = """<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="/xl/worksheets/sheet1.xml"/>
</Relationships>"""
    with ZipFile(path, "w") as archive:
        archive.writestr("xl/sharedStrings.xml", shared_xml)
        archive.writestr("xl/workbook.xml", workbook_xml)
        archive.writestr("xl/_rels/workbook.xml.rels", rels_xml)
        archive.writestr("xl/worksheets/sheet1.xml", sheet_xml)


def test_load_acceptance_rows_reads_named_sheet_without_excel_dependency(tmp_path: Path):
    workbook = tmp_path / "acceptance.xlsx"
    _write_minimal_xlsx(workbook)

    rows = load_acceptance_rows(workbook)

    assert rows == [
        {
            "量表ID": "big_five_bfi_60",
            "量表名称": "大五人格问卷（60题简版）",
            "来源文件夹": "大五人格",
            "来源文件": "大五人格问卷.doc",
            "预期题项数": 60,
            "草稿题项数": 60,
            "小程序题项数": 60,
            "敏感类别": "personality",
        }
    ]


def test_build_scale_audits_reports_content_and_source_gaps(tmp_path: Path):
    content_dir = tmp_path / "content"
    source_root = tmp_path / "sources"
    content_dir.mkdir()
    (source_root / "大五人格").mkdir(parents=True)
    (source_root / "大五人格" / "大五人格问卷.doc").write_text("source", encoding="utf-8")
    (content_dir / "scale_item_drafts.json").write_text(
        '{"drafts":[{"scale_id":"big_five_bfi_60","items":[{},{}]}]}', encoding="utf-8"
    )
    (content_dir / "assessment_worksheets.json").write_text(
        '{"worksheets":[{"id":"big_five_bfi_60","questions":[{}]}]}', encoding="utf-8"
    )
    (content_dir / "scales_catalog.json").write_text(
        '{"scales":[{"id":"big_five_bfi_60","review_status":"pilot_review_required"}]}',
        encoding="utf-8",
    )
    rows = [
        {
            "量表ID": "big_five_bfi_60",
            "量表名称": "大五人格问卷（60题简版）",
            "来源文件夹": "大五人格",
            "来源文件": "大五人格问卷.doc；不存在.pdf",
            "预期题项数": 60,
            "敏感类别": "personality",
        }
    ]

    audits = build_scale_audits(rows, content_dir=content_dir, source_root=source_root)

    assert audits[0]["draft_count"] == 2
    assert audits[0]["worksheet_count"] == 1
    assert audits[0]["found_sources"] == ["大五人格问卷.doc"]
    assert audits[0]["missing_sources"] == ["不存在.pdf"]
    assert audits[0]["gap_types"] == ["题项数与验收预期不一致", "存在未找到的登记来源文件", "需人工逐题和计分复核"]
    assert "big_five_bfi_60" in render_acceptance_matrix(audits)


def test_build_assessment_audit_rows_covers_disabled_and_scoring_metadata():
    worksheets = [
        {
            "id": "disabled_scale",
            "display_title": "暂未开放量表",
            "enabled_for_user": False,
            "questions": [
                {
                    "id": "Q1",
                    "reverse_scored": True,
                    "options": [{"label": "较符合", "value": "4", "score": 4}],
                }
            ],
            "dimensions": [{"code": "D1", "item_codes": ["Q1"]}],
            "scoring": "各题相加，仍需人工复核。",
            "source_file": "source.docx",
            "review_status": "metadata_only",
            "boundary_notice": "只用于自我观察，不构成诊断。",
            "result_disclaimer": "只用于自我观察，不构成诊断。",
        }
    ]
    drafts = {"disabled_scale": {"items": [{}]}}
    catalog = {"disabled_scale": {"id": "disabled_scale"}}

    rows = build_audit_rows(worksheets, drafts=drafts, catalog=catalog)

    assert rows[0]["enabled_for_user"] is False
    assert rows[0]["反向题数"] == 1
    assert rows[0]["维度数"] == 1
    assert rows[0]["草稿题项数"] == 1
    assert rows[0]["题项数与草稿一致"] == "是"
    assert rows[0]["计分文本含人工复核"] == "是"
