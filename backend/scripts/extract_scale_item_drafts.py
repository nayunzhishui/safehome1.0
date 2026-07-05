"""Extract scale item drafts from local questionnaire source files.

The script is intentionally conservative: it only writes item drafts when the
item text can be read from a local source file. Sources that need manual review
are written to docs/量表待人工录入清单.md instead of being guessed.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable
from xml.etree import ElementTree as ET
from zipfile import ZipFile

try:
    from pypdf import PdfReader
except ImportError:  # pragma: no cover - local runtime fallback
    PdfReader = None


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONTENT_ROOT = PROJECT_ROOT / "content"
DOCS_ROOT = PROJECT_ROOT / "docs"
SOURCE_ROOT = Path(
    r"D:\codex\workspace\safehome1.0其他内容\夏老师文件\2026年6月18日发给董俊杰的(1)\测评问卷-量表"
)

NON_DIAGNOSTIC_NOTICE = "本结果只用于自我观察和练习参考，不构成诊断、筛查结论或人格标签。"
SENSITIVE_NOTICE = "该量表含健康、筛查或人格语义，开放前必须展示非诊断免责声明，并保留人工复核入口。"
PRESERVE_CURATED_DRAFT_IDS = {"parent_reflective_functioning_prfq", "emotion_regulation_erq_gross"}


@dataclass
class ScaleSpec:
    scale_id: str
    display_name: str
    source_folder: str
    source_files: list[str]
    source_type: str
    audience: str
    audience_class: str
    category: str
    theme: str
    reflex_node: str
    search_keywords: list[str]
    sensitive_category: str
    item_code_prefix: str
    likert: list[dict]
    expected_count: int
    extraction: dict
    dimensions: list[dict] = field(default_factory=list)
    reverse_item_numbers: set[int] = field(default_factory=set)
    scoring_notes: list[str] = field(default_factory=list)
    supportive_interpretation_draft: str = NON_DIAGNOSTIC_NOTICE
    enabled: bool = False
    first_batch_candidate: bool = False
    review_status: str = "item_draft_pending_human_review"
    scoring_status: str = "pending_review"
    recommended_card_ids: list[str] = field(default_factory=list)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def normalize_line(value: str) -> str:
    value = re.sub(r"\s+", " ", value or "").strip()
    value = value.replace("．", ".").replace("、", ".")
    return value


def read_docx_lines(path: Path) -> list[str]:
    with ZipFile(path) as archive:
        xml = archive.read("word/document.xml")
    root = ET.fromstring(xml)
    ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    lines: list[str] = []
    for paragraph in root.findall(".//w:p", ns):
        texts = [node.text or "" for node in paragraph.findall(".//w:t", ns)]
        line = normalize_line("".join(texts))
        if line:
            lines.append(line)
    return lines


def read_pdf_lines(path: Path) -> list[str]:
    if PdfReader is None:
        raise RuntimeError("pypdf is not available; cannot extract PDF text")
    reader = PdfReader(str(path))
    lines: list[str] = []
    for page in reader.pages:
        text = page.extract_text() or ""
        lines.extend(normalize_line(line) for line in text.splitlines() if normalize_line(line))
    return lines


def read_legacy_doc_lines(path: Path) -> list[str]:
    """Convert an old .doc file locally before reading it as docx.

    The source directory contains several Word 97-2003 files. They are only
    accepted when LibreOffice can convert them into readable text; otherwise
    the caller treats the source as not safely extractable.
    """
    soffice = shutil.which("soffice") or shutil.which("soffice.com")
    if not soffice:
        raise RuntimeError("LibreOffice/soffice is not available; cannot extract legacy .doc")
    out_dir = PROJECT_ROOT / ".tmp" / "scale_docx_convert"
    out_dir.mkdir(parents=True, exist_ok=True)
    target = out_dir / f"{path.stem}.docx"
    if target.exists():
        target.unlink()
    before = {candidate.resolve() for candidate in out_dir.glob("*.docx")}
    result = subprocess.run(
        [soffice, "--headless", "--convert-to", "docx", "--outdir", str(out_dir), str(path)],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="ignore",
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"LibreOffice conversion failed for {path.name}: {result.stderr or result.stdout}")
    candidates = [target] if target.exists() else []
    if not candidates:
        candidates = sorted(
            [candidate for candidate in out_dir.glob("*.docx") if candidate.resolve() not in before],
            key=lambda candidate: candidate.stat().st_mtime,
            reverse=True,
        )
    if not candidates:
        raise RuntimeError(f"LibreOffice did not create a docx for {path.name}")
    return read_docx_lines(candidates[0])


def read_sav_variable_labels(relative_path: str, prefix: str, expected_count: int) -> list[tuple[int, str]]:
    try:
        import pyreadstat
    except ImportError as exc:  # pragma: no cover - local runtime dependent
        raise RuntimeError("pyreadstat is not available; cannot extract .sav variable labels") from exc

    path = SOURCE_ROOT / relative_path
    _, meta = pyreadstat.read_sav(str(path), metadataonly=True)
    labels_by_name = {
        (name or "").lower(): label or ""
        for name, label in zip(meta.column_names, meta.column_labels)
    }
    items: list[tuple[int, str]] = []
    for number in range(1, expected_count + 1):
        label = labels_by_name.get(f"{prefix.lower()}{number}")
        if not label:
            continue
        text = re.sub(rf"^{number}\s*[.、．:：]\s*", "", normalize_line(label)).strip()
        if text:
            items.append((number, text))
    return items


def read_source_lines(relative_path: str) -> list[str]:
    path = SOURCE_ROOT / relative_path
    suffix = path.suffix.lower()
    if suffix == ".docx":
        return read_docx_lines(path)
    if suffix == ".doc":
        return read_legacy_doc_lines(path)
    if suffix == ".pdf":
        return read_pdf_lines(path)
    raise ValueError(f"unsupported source type: {path}")


def cut_lines(lines: list[str], start: str | None = None, end: str | None = None) -> list[str]:
    start_index = 0
    if start:
        for index, line in enumerate(lines):
            if start in line:
                start_index = index
                break
    end_index = len(lines)
    if end:
        for index, line in enumerate(lines[start_index + 1 :], start_index + 1):
            if end in line:
                end_index = index
                break
    return lines[start_index:end_index]


def is_option_line(line: str) -> bool:
    compact = line.replace(" ", "")
    return bool(re.fullmatch(r"[0-9]{1,2}", compact)) or bool(re.fullmatch(r"(?:[0-9]\s*){2,8}", line))


def clean_item_text(text: str) -> str:
    text = re.sub(r"^_+\s*", "", text.strip())
    text = re.sub(r"\s+[0-9](?:\s+[0-9]){1,8}\s*$", "", text)
    text = re.sub(r"^[.。:：\s]+", "", text)
    return text.strip()


def looks_like_item_text(line: str) -> bool:
    if not line or is_option_line(line):
        return False
    if any(token in line for token in ["计分", "参考文献", "使用手册", "量表正文", "指导语", "姓名", "性别"]):
        return False
    return len(line) >= 3


def is_numbered_item_line(line: str, expected_count: int) -> bool:
    numbered = re.match(r"^(?P<number>\d{1,2})[.、．:：]?\s*(?P<text>.+)$", normalize_line(line))
    return bool(
        numbered
        and int(numbered.group("number")) <= expected_count
        and looks_like_item_text(numbered.group("text"))
    )


def extract_numbered_items(
    lines: list[str],
    expected_count: int,
    start: str | None = None,
    end: str | None = None,
    allow_unnumbered: bool = False,
) -> list[tuple[int, str]]:
    section = cut_lines(lines, start=start, end=end)
    items: list[tuple[int, str]] = []
    current_number: int | None = None
    current_text: list[str] = []

    def flush() -> None:
        nonlocal current_number, current_text
        if current_number is None:
            return
        text = clean_item_text("".join(current_text))
        if text:
            items.append((current_number, text))
        current_number = None
        current_text = []

    index = 0
    last_was_option = False
    while index < len(section):
        line = normalize_line(section[index])
        numbered = re.match(r"^(?P<number>\d{1,2})[.、．:：]?\s*(?P<text>.+)$", line)
        if numbered and int(numbered.group("number")) <= expected_count and looks_like_item_text(numbered.group("text")):
            flush()
            current_number = int(numbered.group("number"))
            current_text = [numbered.group("text")]
            last_was_option = False
            index += 1
            continue

        if re.fullmatch(r"\d{1,2}", line):
            number = int(line)
            next_line = section[index + 1] if index + 1 < len(section) else ""
            if (
                number <= expected_count
                and looks_like_item_text(next_line)
                and not is_numbered_item_line(next_line, expected_count)
            ):
                flush()
                current_number = number
                current_text = [next_line]
                last_was_option = False
                index += 2
                continue
            last_was_option = True
            index += 1
            continue

        if current_number is not None and looks_like_item_text(line):
            if (
                allow_unnumbered
                and last_was_option
                and clean_item_text("".join(current_text)).endswith(("。", "！", "？", ".", "!", "?"))
                and current_number < expected_count
            ):
                next_number = current_number + 1
                flush()
                current_number = next_number
                current_text = [line]
            else:
                current_text.append(line)
            last_was_option = False
            index += 1
            continue
        if not is_option_line(line):
            last_was_option = False
        index += 1
    flush()

    deduped: dict[int, str] = {}
    for number, text in items:
        if 1 <= number <= expected_count and number not in deduped:
            deduped[number] = text
    return [(number, deduped[number]) for number in sorted(deduped)]


def extract_sequential_items(
    lines: list[str],
    expected_count: int,
    start: str | None = None,
    end: str | None = None,
) -> list[tuple[int, str]]:
    section = cut_lines(lines, start=start, end=end)
    items: list[tuple[int, str]] = []
    for line in section:
        cleaned = clean_item_text(line)
        if not looks_like_item_text(cleaned):
            continue
        if is_numbered_item_line(cleaned, expected_count):
            numbered = re.match(r"^(?P<number>\d{1,2})[.、．:：]?\s*(?P<text>.+)$", cleaned)
            if numbered:
                items.append((int(numbered.group("number")), clean_item_text(numbered.group("text"))))
                continue
        if re.match(r"^_+", cleaned):
            cleaned = clean_item_text(cleaned)
        if len(items) < expected_count:
            items.append((len(items) + 1, cleaned))
        if len(items) >= expected_count:
            break
    return items


def extract_blob_numbered_items(
    lines: list[str],
    expected_count: int,
    start: str | None = None,
    end: str | None = None,
) -> list[tuple[int, str]]:
    text = " ".join(cut_lines(lines, start=start, end=end))
    text = re.sub(r"\s+", " ", text)
    matches = list(re.finditer(r"(?:_+\s*)?(?P<number>\d{1,2})[.、．:：]\s*(?P<text>.*?)(?=(?:_+\s*)?\d{1,2}[.、．:：]|$)", text))
    items: list[tuple[int, str]] = []
    for match in matches:
        number = int(match.group("number"))
        if not 1 <= number <= expected_count:
            continue
        item_text = clean_item_text(match.group("text"))
        if item_text:
            items.append((number, item_text))
    deduped: dict[int, str] = {}
    for number, item_text in items:
        deduped.setdefault(number, item_text)
    return [(number, deduped[number]) for number in sorted(deduped)]


def extract_attribution_style_items(
    lines: list[str],
    expected_count: int,
    start: str | None = None,
    end: str | None = None,
) -> list[tuple[int, str]]:
    section = cut_lines(lines, start=start, end=end)
    scenarios: list[tuple[int, str]] = []
    for line in section:
        matched = re.match(r"^(?P<number>\d{1,2})[.、．]\s*(?P<text>.+)$", normalize_line(line))
        if not matched:
            continue
        number = int(matched.group("number"))
        text = clean_item_text(matched.group("text"))
        if 1 <= number <= 12 and text and not any(token in text for token in ["您的", "专业", "性别", "年级"]):
            scenarios.append((number, text))

    question_templates = [
        ("这一原因是由于你自己还是由于别人或客观因素？1 表示由于他人，7 表示由于自己。", "INTERNAL"),
        ("在将来的同样情境中，这一原因是否还会存在？1 表示不再会存在，7 表示总是存在着。", "STABLE"),
        ("这一原因是否仅影响这类事件，或者它也影响你生活的其他方面？1 表示仅影响这类事件，7 表示影响所有方面。", "GLOBAL"),
    ]
    items: list[tuple[int, str]] = []
    for scenario_number, scenario in scenarios[:12]:
        for offset, (question, _) in enumerate(question_templates, start=1):
            item_number = (scenario_number - 1) * 3 + offset
            items.append((item_number, f"情境{scenario_number}：{scenario} 请先想到一个你认为的主要原因，然后回答：{question}"))
    return items[:expected_count]


def likert(start: int, end: int, labels: list[str]) -> list[dict]:
    return [{"value": value, "label": labels[value - start]} for value in range(start, end + 1)]


def dimension_for_item(spec: ScaleSpec, item_code: str) -> str:
    for dimension in spec.dimensions:
        if item_code in set(dimension.get("item_codes", [])):
            return dimension["code"]
    return spec.dimensions[0]["code"] if spec.dimensions else "TOTAL"


def build_items(spec: ScaleSpec, extracted: list[tuple[int, str]]) -> list[dict]:
    items = []
    for number, text in extracted:
        item_code = f"{spec.item_code_prefix}{number:02d}"
        items.append(
            {
                "item_code": item_code,
                "display_order": number,
                "text": text,
                "dimension": dimension_for_item(spec, item_code),
                "reverse_scored": number in spec.reverse_item_numbers,
            }
        )
    return items


def build_draft(spec: ScaleSpec, extracted: list[tuple[int, str]]) -> dict:
    return {
        "scale_id": spec.scale_id,
        "display_name": spec.display_name,
        "source_folder": spec.source_folder,
        "source_files": spec.source_files,
        "audience": spec.audience,
        "theme": spec.theme,
        "enabled": spec.enabled,
        "review_status": spec.review_status,
        "item_status": "draft_extracted",
        "scoring_status": spec.scoring_status,
        "instructions": "本草稿由本地量表源文件抽取，正式开放前必须人工核对题项原文、计分规则、授权范围和结果解释边界。",
        "likert": spec.likert,
        "dimensions": spec.dimensions or [
            {
                "code": "TOTAL",
                "label": "总分",
                "item_codes": [f"{spec.item_code_prefix}{number:02d}" for number, _ in extracted],
                "note": "当前只记录题项集合；维度解释和计分方向需人工复核。",
            }
        ],
        "items": build_items(spec, extracted),
        "scoring_notes": spec.scoring_notes or ["已录入题项；正式计分口径需按量表内容报告和源文件继续复核。"],
        "supportive_interpretation_draft": spec.supportive_interpretation_draft,
        "recommended_card_ids": spec.recommended_card_ids,
    }


def catalog_entry(spec: ScaleSpec, item_status: str, notes: str) -> dict:
    return {
        "id": spec.scale_id,
        "display_name": spec.display_name,
        "audience": spec.audience,
        "audience_class": spec.audience_class,
        "category": spec.category,
        "theme": spec.theme,
        "reflex_node": spec.reflex_node,
        "search_keywords": spec.search_keywords,
        "sensitive_category": spec.sensitive_category,
        "source_folder": spec.source_folder,
        "source_files": spec.source_files,
        "source_type": spec.source_type,
        "review_status": "pilot_review_required" if spec.enabled else "metadata_only",
        "enabled": spec.enabled,
        "excluded_from_user_flow": False if spec.enabled else True,
        "not_open_reason": "" if spec.enabled else "题项或计分规则未完成复核，暂不开放填写。",
        "exclusion_reason": "" if spec.enabled else "题项或计分规则未完成复核，暂不开放填写。",
        "first_batch_candidate": spec.first_batch_candidate,
        "item_status": item_status,
        "scoring_status": spec.scoring_status,
        "boundary_notice": SENSITIVE_NOTICE if spec.sensitive_category != "none" else NON_DIAGNOSTIC_NOTICE,
        "result_disclaimer": SENSITIVE_NOTICE if spec.sensitive_category != "none" else NON_DIAGNOSTIC_NOTICE,
        "recommended_card_ids": spec.recommended_card_ids,
        "notes": notes,
    }


def upsert_by_key(items: list[dict], key: str, new_item: dict) -> None:
    for index, item in enumerate(items):
        if item.get(key) == new_item.get(key):
            merged = {**item, **new_item}
            items[index] = merged
            return
    items.append(new_item)


def default_fields_for_catalog(scale: dict) -> dict:
    text = " ".join(str(scale.get(field, "")) for field in ["id", "display_name", "theme", "source_folder"])
    sensitive = "screening_or_health" if any(token in text.lower() for token in ["gad", "phq", "cesd", "dass", "isi", "psqi", "ghq"]) else "none"
    if "大五" in text or "人格" in text or "epq" in text.lower():
        sensitive = "personality"
    return {
        "audience_class": scale.get("audience") or "adult",
        "category": scale.get("category") or "成人自助",
        "reflex_node": scale.get("reflex_node") or "reflection",
        "search_keywords": scale.get("search_keywords") or [scale.get("display_name", ""), scale.get("theme", "")],
        "sensitive_category": scale.get("sensitive_category") or sensitive,
        "boundary_notice": scale.get("boundary_notice")
        or (SENSITIVE_NOTICE if sensitive != "none" else NON_DIAGNOSTIC_NOTICE),
        "result_disclaimer": scale.get("result_disclaimer")
        or (SENSITIVE_NOTICE if sensitive != "none" else NON_DIAGNOSTIC_NOTICE),
    }


def scale_specs() -> list[ScaleSpec]:
    five = likert(1, 5, ["完全不符合", "比较不符合", "说不清", "比较符合", "完全符合"])
    return [
        ScaleSpec(
            scale_id="parental_burnout_pba",
            display_name="父母养育倦怠问卷",
            source_folder="家长自主量表/父母养育倦怠问卷",
            source_files=["Parental Burnout Assessment with scoring.docx"],
            source_type="authorized_resource",
            audience="parent",
            audience_class="parent",
            category="家长自助",
            theme="parenting_stress",
            reflex_node="reaction",
            search_keywords=["父母养育倦怠", "PBA", "家长压力", "照顾耗竭"],
            sensitive_category="parenting_stress",
            item_code_prefix="PBA",
            likert=likert(0, 6, ["从不", "一年几次", "一个月或者不到一个月一次", "一个月几次", "一周一次", "一周几次", "每天"]),
            expected_count=23,
            extraction={"file": r"家长自主量表\父母养育倦怠问卷\Parental Burnout Assessment with scoring.docx"},
            scoring_status="partial_rule_pending_dimension_review",
            recommended_card_ids=["three_second_pause", "nonjudgmental_response"],
            scoring_notes=["本地文件可读到 0-6 频率选项和题项；维度、阈值和正式解释需人工复核。"],
        ),
        ScaleSpec(
            scale_id="rsca_adolescent_resilience",
            display_name="青少年心理韧性量表（RSCA）",
            source_folder="学生自助量表/2022年6月施测学生问卷",
            source_files=["2022年6月施测的学生问卷及计分规则-高一年级745与高二年级963均施测.docx"],
            source_type="authorized_resource",
            audience="student",
            audience_class="student",
            category="学生自助",
            theme="resilience",
            reflex_node="resource",
            search_keywords=["青少年心理韧性", "RSCA", "学生韧性"],
            sensitive_category="none",
            item_code_prefix="RSCA",
            likert=five,
            expected_count=27,
            extraction={"file": r"学生自助量表\2022年6月施测的学生问卷及计分规则-高一年级745与高二年级963均施测.docx", "start": "1. 失败总是", "end": "2 计分规则"},
            reverse_item_numbers={1, 2, 5, 6, 9, 12, 15, 16, 17, 21, 26, 27},
            scoring_status="partial_rule_pending_dimension_mapping",
            scoring_notes=["源文件写明 27 题、1-5 分，1、2、5、6、9、12、15、16、17、21、26、27 为反向计分；精确维度题项映射仍需人工复核。"],
        ),
        ScaleSpec(
            scale_id="academic_buoyancy_4",
            display_name="学业复原力/学业浮力量表",
            source_folder="学生自助量表/2022年6月施测学生问卷",
            source_files=["2022年6月施测的学生问卷及计分规则-高一年级745与高二年级963均施测.docx"],
            source_type="authorized_resource",
            audience="student",
            audience_class="student",
            category="学生自助",
            theme="academic_resilience",
            reflex_node="resource",
            search_keywords=["学业浮力", "学业复原力", "Academic Buoyancy"],
            sensitive_category="none",
            item_code_prefix="AB",
            likert=five,
            expected_count=4,
            extraction={"file": r"学生自助量表\2022年6月施测的学生问卷及计分规则-高一年级745与高二年级963均施测.docx", "start": "1. 我善于应对学业", "end": "2 计分规则", "allow_unnumbered": True},
            scoring_status="rule_available_pending_review",
            scoring_notes=["源文件写明 4 题、1-5 分，分数用于观察日常学业压力下的应对能力。"],
        ),
        ScaleSpec(
            scale_id="afq_y8_avoidance_fusion",
            display_name="青少年回避与融合问卷（AFQ-Y8）",
            source_folder="学生自助量表/2022年6月施测学生问卷",
            source_files=["2022年6月施测的学生问卷及计分规则-高一年级745与高二年级963均施测.docx"],
            source_type="authorized_resource",
            audience="student",
            audience_class="student",
            category="学生自助",
            theme="psychological_flexibility",
            reflex_node="fusion",
            search_keywords=["AFQ-Y8", "回避融合", "心理灵活性"],
            sensitive_category="none",
            item_code_prefix="AFQY",
            likert=five,
            expected_count=8,
            extraction={"file": r"学生自助量表\2022年6月施测的学生问卷及计分规则-高一年级745与高二年级963均施测.docx", "start": "1. 直到我可以感到快乐", "end": "2 计分规则"},
            scoring_status="rule_available_pending_review",
            scoring_notes=["源文件写明 8 题、1-5 分，分数越高心理僵化程度越高、心理灵活性越低；结果解释必须支持性改写。"],
        ),
        ScaleSpec(
            scale_id="cfi2_cognitive_flexibility",
            display_name="认知灵活性问卷中文版（CFI-2）",
            source_folder="学生自助量表/2022年6月施测学生问卷",
            source_files=["2022年6月施测的学生问卷及计分规则-高一年级745与高二年级963均施测.docx"],
            source_type="authorized_resource",
            audience="student",
            audience_class="student",
            category="学生自助",
            theme="cognitive_flexibility",
            reflex_node="transformation",
            search_keywords=["认知灵活性", "CFI-2", "灵活选择", "灵活效能"],
            sensitive_category="none",
            item_code_prefix="CFI",
            likert=five,
            expected_count=12,
            extraction={"file": r"学生自助量表\2022年6月施测的学生问卷及计分规则-高一年级745与高二年级963均施测.docx", "start": "1. 我能以多种不同的方式表达", "end": "2 计分方式"},
            dimensions=[
                {"code": "CFI_CHOICE", "label": "灵活选择", "item_codes": ["CFI01", "CFI02", "CFI03", "CFI05", "CFI06", "CFI10"], "reverse_item_codes": ["CFI02", "CFI03", "CFI05", "CFI10"]},
                {"code": "CFI_WILLINGNESS", "label": "灵活意愿", "item_codes": ["CFI04", "CFI11", "CFI12"]},
                {"code": "CFI_EFFICACY", "label": "灵活效能", "item_codes": ["CFI07", "CFI08", "CFI09"]},
            ],
            reverse_item_numbers={2, 3, 5, 10},
            scoring_status="rule_available_pending_review",
            scoring_notes=["源文件写明三个因子：灵活选择 1、2、3、5、6、10；灵活意愿 4、11、12；灵活效能 7、8、9；2、3、5、10 反向计分。"],
            recommended_card_ids=["cognitive_flexibility", "alternative_behavior"],
        ),
        ScaleSpec(
            scale_id="emotional_resilience_11",
            display_name="青少年情绪弹性问卷",
            source_folder="学生自助量表/2022年6月施测学生问卷",
            source_files=["2022年6月施测的学生问卷及计分规则-高一年级745与高二年级963均施测.docx", "青少年情绪弹性问卷.docx"],
            source_type="authorized_resource",
            audience="student",
            audience_class="student",
            category="学生自助",
            theme="emotion_resilience",
            reflex_node="reaction",
            search_keywords=["情绪弹性", "情绪恢复", "积极情绪"],
            sensitive_category="none",
            item_code_prefix="ERES",
            likert=likert(1, 6, ["完全不符合", "基本不符合", "不太符合", "有些符合", "基本符合", "完全符合"]),
            expected_count=11,
            extraction={"file": r"学生自助量表\2022年6月施测的学生问卷及计分规则-高一年级745与高二年级963均施测.docx", "start": "1. 心情不佳时", "end": "2 计分规则"},
            dimensions=[
                {"code": "ERES_POSITIVE", "label": "积极情绪能力", "item_codes": ["ERES01", "ERES03", "ERES04", "ERES08", "ERES09"]},
                {"code": "ERES_RECOVERY", "label": "情绪恢复能力", "item_codes": ["ERES02", "ERES05", "ERES06", "ERES07", "ERES10", "ERES11"]},
            ],
            enabled=True,
            first_batch_candidate=True,
            scoring_status="rule_available_pending_review",
            scoring_notes=["源文件写明积极情绪能力项目为 1、3、4、8、9；情绪恢复能力项目为 2、5、6、7、10、11。"],
            recommended_card_ids=["student_emotion_naming", "self_support_statement"],
        ),
        ScaleSpec(
            scale_id="study_engagement_uwes_s_17",
            display_name="学习投入量表（UWES-S 中文版）",
            source_folder="学生自助量表/学习投入量表",
            source_files=["学习投入量表.docx"],
            source_type="authorized_resource",
            audience="student",
            audience_class="student",
            category="学生自助",
            theme="study_engagement",
            reflex_node="behavior",
            search_keywords=["学习投入", "UWES-S", "活力", "奉献", "专注"],
            sensitive_category="none",
            item_code_prefix="UWES",
            likert=likert(1, 7, ["从来没有", "几乎没有", "经常没有", "不确定", "偶尔", "经常", "总是"]),
            expected_count=17,
            extraction={"file": r"学生自助量表\学习投入量表\学习投入量表.docx", "start": "1. 早晨一起床", "end": "2计分方式"},
            dimensions=[
                {"code": "UWES_VIGOR", "label": "活力", "item_codes": [f"UWES{i:02d}" for i in range(1, 7)]},
                {"code": "UWES_DEDICATION", "label": "奉献", "item_codes": [f"UWES{i:02d}" for i in range(7, 12)]},
                {"code": "UWES_ABSORPTION", "label": "专注", "item_codes": [f"UWES{i:02d}" for i in range(12, 18)]},
            ],
            enabled=True,
            first_batch_candidate=True,
            scoring_status="rule_available_pending_review",
            scoring_notes=["源文件写明 17 题、7 点计分，1-6 活力、7-11 奉献、12-17 专注。"],
            recommended_card_ids=["student_emotion_naming", "cbt_auto_thought_student"],
        ),
        ScaleSpec(
            scale_id="cd_risc10_brief_resilience",
            display_name="简式心理韧性量表（CD-RISC-10）",
            source_folder="基于情绪反射弧的分类",
            source_files=["简式心理韧性量表-10题.docx"],
            source_type="authorized_resource",
            audience="adult",
            audience_class="adult",
            category="成人自助",
            theme="resilience",
            reflex_node="resource",
            search_keywords=["CD-RISC-10", "简式心理韧性", "韧性"],
            sensitive_category="none",
            item_code_prefix="CDRISC",
            likert=likert(0, 4, ["从不", "很少", "有时", "经常", "几乎总是"]),
            expected_count=10,
            extraction={"file": r"基于情绪反射弧的分类\简式心理韧性量表-10题.docx", "start": "1. 当事情发生变化", "end": "2 计分规则"},
            enabled=True,
            first_batch_candidate=True,
            scoring_status="rule_available_pending_review",
            scoring_notes=["源文件写明 CD-RISC-10 为单维结构，0-4 分，总分 0-40，分数越高代表心理韧性水平越高。"],
            recommended_card_ids=["cognitive_flexibility", "self_support_statement"],
        ),
        ScaleSpec(
            scale_id="acceptance_action_aaq2",
            display_name="接纳与行动问卷（AAQ-II）",
            source_folder="基于情绪反射弧的分类/接纳行动问卷AAQ",
            source_files=["2-1-接纳与行动问卷第二版AAQII.docx"],
            source_type="authorized_resource",
            audience="adult",
            audience_class="adult",
            category="成人自助",
            theme="psychological_flexibility",
            reflex_node="acceptance",
            search_keywords=["AAQ-II", "接纳行动", "心理灵活性"],
            sensitive_category="none",
            item_code_prefix="AAQ",
            likert=likert(1, 7, ["从未", "很少", "偶尔", "有时", "经常", "几乎总是", "总是"]),
            expected_count=7,
            extraction={"file": r"基于情绪反射弧的分类\接纳行动问卷AAQ\2-1-接纳与行动问卷第二版AAQII.docx", "start": "1. 痛苦的经历", "end": None},
            scoring_status="rule_available_pending_review",
            scoring_notes=["本地文件可读到 7 个题项和 1-7 选项；正式分数解释需继续核对。"],
            recommended_card_ids=["cognitive_flexibility", "alternative_behavior"],
        ),
        ScaleSpec(
            scale_id="regulatory_focus_general_18",
            display_name="一般调节聚焦问卷",
            source_folder="基于情绪反射弧的分类",
            source_files=["一般调节聚焦问卷-孙天娇要来的.docx"],
            source_type="authorized_resource",
            audience="adult",
            audience_class="adult",
            category="成人自助",
            theme="regulatory_focus",
            reflex_node="motivation",
            search_keywords=["调节聚焦", "促进定向", "预防定向"],
            sensitive_category="none",
            item_code_prefix="RFQG",
            likert=likert(1, 7, ["非常不符合", "比较不符合", "有些不符合", "一般", "有些符合", "比较符合", "非常符合"]),
            expected_count=18,
            extraction={"file": r"基于情绪反射弧的分类\一般调节聚焦问卷-孙天娇要来的.docx", "start": "我很在乎", "end": None, "mode": "sequential"},
            scoring_status="pending_dimension_mapping",
            scoring_notes=["本地文件可读到 18 个题项和 1-7 选项；促进/预防维度题项映射需人工复核。"],
        ),
        ScaleSpec(
            scale_id="self_compassion_scs_cn",
            display_name="自我关怀量表（SCS 中文版）",
            source_folder="基于情绪反射弧的分类/自我关怀",
            source_files=["ChineseSCS-26题自我关怀量表.pdf"],
            source_type="authorized_resource",
            audience="adult",
            audience_class="adult",
            category="成人自助",
            theme="self_compassion",
            reflex_node="acceptance",
            search_keywords=["自我关怀", "自悯", "SCS"],
            sensitive_category="none",
            item_code_prefix="SCS",
            likert=likert(1, 5, ["从不如此", "很少如此", "有时如此", "经常如此", "总是如此"]),
            expected_count=26,
            extraction={"file": r"基于情绪反射弧的分类\自我关怀\ChineseSCS-26题自我关怀量表.pdf", "start": "_____ 1.", "mode": "blob"},
            dimensions=[
                {"code": "SCS_SK", "label": "善待自己", "item_codes": ["SCS05", "SCS12", "SCS19", "SCS23", "SCS26"]},
                {"code": "SCS_SJ", "label": "自我批评", "item_codes": ["SCS01", "SCS08", "SCS11", "SCS16", "SCS21"], "reverse_item_codes": ["SCS01", "SCS08", "SCS11", "SCS16", "SCS21"]},
                {"code": "SCS_CH", "label": "共同人性", "item_codes": ["SCS03", "SCS07", "SCS10", "SCS15"]},
                {"code": "SCS_ISO", "label": "自我隔离", "item_codes": ["SCS04", "SCS13", "SCS18", "SCS25"], "reverse_item_codes": ["SCS04", "SCS13", "SCS18", "SCS25"]},
                {"code": "SCS_MIND", "label": "静观当下", "item_codes": ["SCS09", "SCS14", "SCS17", "SCS22"]},
                {"code": "SCS_OVER", "label": "过度沉迷", "item_codes": ["SCS02", "SCS06", "SCS20", "SCS24"], "reverse_item_codes": ["SCS02", "SCS06", "SCS20", "SCS24"]},
            ],
            reverse_item_numbers={1, 2, 4, 6, 8, 11, 13, 16, 18, 20, 21, 24, 25},
            enabled=True,
            first_batch_candidate=True,
            scoring_status="rule_available_pending_review",
            scoring_notes=["PDF 写明六个维度题项，负向维度自我批评、自我隔离、过度沉迷先 1-5 反向后再参与总自我关怀均分。"],
            recommended_card_ids=["self_support_statement", "three_second_pause"],
        ),
        ScaleSpec(
            scale_id="mindful_attention_awareness_maas",
            display_name="正念注意觉知量表（MAAS）",
            source_folder="基于情绪反射弧的分类/正念觉知相关量表",
            source_files=["正念注意觉知量表 答题纸.pdf"],
            source_type="authorized_resource",
            audience="adult",
            audience_class="adult",
            category="成人自助",
            theme="mindfulness",
            reflex_node="awareness",
            search_keywords=["正念注意觉知", "MAAS", "觉察"],
            sensitive_category="none",
            item_code_prefix="MAAS",
            likert=likert(1, 6, ["几乎总是", "很频繁", "较频繁", "较少", "很少", "几乎从不"]),
            expected_count=15,
            extraction={"file": r"基于情绪反射弧的分类\正念觉知相关量表\正念注意觉知量表 答题纸.pdf", "start": "1、有时我体验", "end": None},
            enabled=True,
            first_batch_candidate=True,
            scoring_status="rule_available_pending_review",
            scoring_notes=["本地答题纸可读到 15 题和 1-6 选项；正式均分/总分解释需人工复核。"],
            recommended_card_ids=["emotion_naming", "three_second_pause"],
        ),
        ScaleSpec(
            scale_id="fmi_12_mindfulness",
            display_name="弗赖堡正念调查量表（FMI-12）",
            source_folder="基于情绪反射弧的分类/正念觉知相关量表",
            source_files=["弗赖堡正念调查量表FMI.pdf"],
            source_type="authorized_resource",
            audience="adult",
            audience_class="adult",
            category="成人自助",
            theme="mindfulness",
            reflex_node="awareness",
            search_keywords=["FMI", "弗赖堡正念", "觉知", "接受"],
            sensitive_category="none",
            item_code_prefix="FMI",
            likert=likert(1, 4, ["很少", "有时", "经常", "总是"]),
            expected_count=12,
            extraction={"file": r"基于情绪反射弧的分类\正念觉知相关量表\弗赖堡正念调查量表FMI.pdf", "start": "1、 我对当前", "end": "使用手册"},
            scoring_status="rule_available_pending_review",
            scoring_notes=["PDF 使用手册写明 12 题、1-4 分，总分为各题相加；觉知/接受精确题项映射需人工复核。"],
            recommended_card_ids=["emotion_naming", "three_second_pause"],
        ),
        ScaleSpec(
            scale_id="swls_life_satisfaction",
            display_name="生活满意度量表（SWLS）",
            source_folder="基于情绪反射弧的分类/主观幸福感-生活满意度",
            source_files=["生活满意度量表(SWLS).docx"],
            source_type="authorized_resource",
            audience="adult",
            audience_class="adult",
            category="成人自助",
            theme="wellbeing",
            reflex_node="outcome",
            search_keywords=["SWLS", "生活满意度", "主观幸福感"],
            sensitive_category="wellbeing",
            item_code_prefix="SWLS",
            likert=likert(1, 7, ["非常同意", "同意", "有些同意", "中立", "有些不同意", "不同意", "强烈反对"]),
            expected_count=5,
            extraction={"file": r"基于情绪反射弧的分类\主观幸福感-生活满意度\生活满意度量表(SWLS).docx", "start": "______一般情况下", "end": "说明", "mode": "sequential"},
            scoring_status="rule_available_pending_review",
            scoring_notes=["本地文件可读到 5 个题项和 1-7 选项；源文件包含等级解释，用户端必须改写为非诊断、非标签化表达。"],
        ),
        ScaleSpec(
            scale_id="hplp_c_health_promoting_lifestyle",
            display_name="健康促进生活方式量表（HPLP-C）",
            source_folder="基于情绪反射弧的分类/健康促进生活方式量表",
            source_files=["健康促进生活方式量表(HPLP-C).docx"],
            source_type="authorized_resource",
            audience="adult",
            audience_class="adult",
            category="成人自助",
            theme="health_lifestyle",
            reflex_node="behavior",
            search_keywords=["HPLP-C", "健康促进生活方式", "生活习惯"],
            sensitive_category="health_lifestyle",
            item_code_prefix="HPLP",
            likert=likert(1, 4, ["从不", "偶尔", "经常", "总是"]),
            expected_count=42,
            extraction={"file": r"基于情绪反射弧的分类\健康促进生活方式量表\健康促进生活方式量表(HPLP-C).docx", "start": "序号", "end": None},
            scoring_status="partial_rule_pending_dimension_review",
            scoring_notes=["本地文件可读到 42 个题项和 1-4 选项；维度归属、是否适合用户端开放和健康建议边界需人工复核。"],
        ),
        ScaleSpec(
            scale_id="big_five_bfi_60",
            display_name="大五人格问卷（60题简版）",
            source_folder="基于情绪反射弧的分类/大五人格",
            source_files=["大五人格问卷(简版)记分+纬度解释.doc"],
            source_type="authorized_resource",
            audience="adult",
            audience_class="adult",
            category="成人自助",
            theme="personality_observation",
            reflex_node="trait_observation",
            search_keywords=["大五人格", "BFI", "人格", "外倾性", "神经质"],
            sensitive_category="personality",
            item_code_prefix="BFI",
            likert=five,
            expected_count=60,
            extraction={"file": r"基于情绪反射弧的分类\大五人格\大五人格问卷(简版)记分+纬度解释.doc", "start": "我不是一个充满烦恼的人。", "end": "神经质：", "mode": "sequential"},
            dimensions=[
                {"code": "BFI_NEUROTICISM", "label": "神经质/情绪敏感", "item_codes": [f"BFI{i:02d}" for i in [1, 6, 11, 16, 21, 26, 31, 36, 41, 46, 51, 56]], "reverse_item_codes": ["BFI01", "BFI06", "BFI21", "BFI31"]},
                {"code": "BFI_EXTRAVERSION", "label": "外倾性", "item_codes": [f"BFI{i:02d}" for i in [2, 7, 12, 18, 22, 27, 32, 37, 42, 47, 52, 57]], "reverse_item_codes": ["BFI18", "BFI22", "BFI47"]},
                {"code": "BFI_OPENNESS", "label": "开放性", "item_codes": [f"BFI{i:02d}" for i in [3, 8, 13, 17, 23, 28, 33, 38, 43, 48, 53, 58]], "reverse_item_codes": ["BFI03", "BFI13", "BFI28", "BFI43", "BFI53", "BFI58"]},
                {"code": "BFI_AGREEABLENESS", "label": "宜人性", "item_codes": [f"BFI{i:02d}" for i in [4, 9, 14, 19, 24, 29, 34, 39, 44, 49, 54, 59]], "reverse_item_codes": ["BFI04", "BFI09", "BFI14", "BFI19", "BFI24", "BFI44", "BFI49", "BFI54"]},
                {"code": "BFI_CONSCIENTIOUSNESS", "label": "尽责性", "item_codes": [f"BFI{i:02d}" for i in [5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60]], "reverse_item_codes": ["BFI20", "BFI30", "BFI60"]},
            ],
            reverse_item_numbers={1, 3, 4, 6, 9, 13, 14, 18, 19, 20, 21, 22, 24, 28, 30, 31, 43, 44, 47, 49, 53, 54, 58, 60},
            enabled=True,
            first_batch_candidate=True,
            scoring_status="partial_rule_pending_dimension_review",
            scoring_notes=["源文件含 60 个中文题项和五个维度计分键；维度归属和反向题已按源文件文字初录，仍需人工逐项核对。用户端结果不得输出人格定性标签。"],
        ),
        ScaleSpec(
            scale_id="attribution_style_student_36",
            display_name="归因方式问卷（学生用）",
            source_folder="基于情绪反射弧的分类/归因风格问卷",
            source_files=["归因方式问卷(学生用).doc"],
            source_type="authorized_resource",
            audience="student",
            audience_class="student",
            category="学生自助",
            theme="attribution_style",
            reflex_node="appraisal",
            search_keywords=["归因方式", "归因风格", "学生归因"],
            sensitive_category="none",
            item_code_prefix="ASQ",
            likert=likert(1, 7, ["左端非常符合", "偏向左端", "略偏左端", "中间", "略偏右端", "偏向右端", "右端非常符合"]),
            expected_count=36,
            extraction={"file": r"基于情绪反射弧的分类\归因风格问卷\归因方式问卷(学生用).doc", "start": "该问卷的每一个条目", "end": None, "mode": "attribution"},
            dimensions=[
                {"code": "ASQ_INTERNAL", "label": "内外归因", "item_codes": [f"ASQ{i:02d}" for i in range(1, 37, 3)]},
                {"code": "ASQ_STABLE", "label": "稳定性归因", "item_codes": [f"ASQ{i:02d}" for i in range(2, 37, 3)]},
                {"code": "ASQ_GLOBAL", "label": "整体性归因", "item_codes": [f"ASQ{i:02d}" for i in range(3, 37, 3)]},
            ],
            enabled=True,
            first_batch_candidate=True,
            scoring_status="partial_rule_pending_open_reason_support",
            scoring_notes=["源文件为 12 个情境，每个情境包含一个开放式主要原因和 3 个 1-7 归因判断。本轮将 3 个判断题拆为 36 个可填写题项；开放式主要原因暂未进入现有单选题库。"],
        ),
        ScaleSpec(
            scale_id="ghq12_general_health",
            display_name="一般健康问卷（GHQ-12）",
            source_folder="基于情绪反射弧的分类/心理健康自评问卷【GHQ12]",
            source_files=["一般健康问卷GHQ-12.docx"],
            source_type="authorized_resource",
            audience="adult",
            audience_class="adult",
            category="成人自助",
            theme="mental_health_observation",
            reflex_node="state_observation",
            search_keywords=["GHQ-12", "一般健康问卷", "心理健康自评"],
            sensitive_category="screening_or_health",
            item_code_prefix="GHQ",
            likert=likert(1, 4, ["从不", "很少", "有时", "经常"]),
            expected_count=12,
            extraction={"file": r"基于情绪反射弧的分类\心理健康自评问卷【GHQ12]\一般健康问卷GHQ-12.docx", "start": "1.能集中精力", "end": "一、计分方式"},
            reverse_item_numbers={1, 3, 4, 7, 8, 12},
            enabled=True,
            first_batch_candidate=True,
            scoring_status="rule_available_pending_sensitive_review",
            scoring_notes=["源文件写明 12 题、1-4 分和积极项目 1、3、4、7、8、12；用户端不得给出心理健康筛查结论。"],
        ),
        ScaleSpec(
            scale_id="epq_emotional_stability_24",
            display_name="EPQ 情绪稳定性量表",
            source_folder="基于情绪反射弧的分类/情绪稳定性-EPQ",
            source_files=["EPQ 情绪稳定性量表.docx"],
            source_type="authorized_resource",
            audience="adult",
            audience_class="adult",
            category="成人自助",
            theme="emotion_stability",
            reflex_node="trait_observation",
            search_keywords=["EPQ", "情绪稳定性", "艾森克"],
            sensitive_category="personality",
            item_code_prefix="EPQ",
            likert=likert(0, 1, ["否", "是"]),
            expected_count=24,
            extraction={"file": r"基于情绪反射弧的分类\情绪稳定性-EPQ\EPQ 情绪稳定性量表.docx", "start": "1你的情绪时常波动吗？", "end": None},
            enabled=True,
            first_batch_candidate=True,
            scoring_status="pending_sensitive_review",
            scoring_notes=["源文件可读到 24 个是/否题项；计分方向、常模和解释边界必须人工复核，用户端不得输出人格定性。"],
        ),
        ScaleSpec(
            scale_id="gad7_anxiety",
            display_name="GAD-7 焦虑相关自评量表",
            source_folder="基于情绪反射弧的分类/焦虑测评-GAD-7",
            source_files=["(完整版)广泛性焦虑障碍量表(GAD-7).doc"],
            source_type="authorized_resource",
            audience="adult",
            audience_class="adult",
            category="成人自助",
            theme="anxiety_observation",
            reflex_node="state_observation",
            search_keywords=["GAD-7", "焦虑", "广泛性焦虑"],
            sensitive_category="screening_or_health",
            item_code_prefix="GAD",
            likert=likert(0, 3, ["完全不会", "好几天", "超过一周", "几乎每天"]),
            expected_count=7,
            extraction={"file": r"基于情绪反射弧的分类\焦虑测评-GAD-7\(完整版)广泛性焦虑障碍量表(GAD-7).doc", "start": "1：感觉", "end": "总分"},
            enabled=True,
            first_batch_candidate=True,
            scoring_status="rule_available_pending_sensitive_review",
            scoring_notes=["源文件可读到 7 题和 0-3 计分；源文件含诊断分级文字，用户端必须改为非诊断、非筛查说明。"],
        ),
        ScaleSpec(
            scale_id="phq9_cesd10_depression",
            display_name="PHQ-9 抑郁相关自评量表（CES-D10待复核）",
            source_folder="基于情绪反射弧的分类/抑郁测评-CESD10-PHQ9",
            source_files=["精选-PHQ-9抑郁症筛查量表.doc", "cesd-10-流调中心抑郁水平评定.jpg"],
            source_type="authorized_resource",
            audience="adult",
            audience_class="adult",
            category="成人自助",
            theme="depression_observation",
            reflex_node="state_observation",
            search_keywords=["PHQ-9", "CES-D10", "抑郁", "情绪低落"],
            sensitive_category="screening_or_health",
            item_code_prefix="PHQ",
            likert=likert(0, 3, ["没有", "有几天", "一半以上时间", "几乎每天"]),
            expected_count=9,
            extraction={"file": r"基于情绪反射弧的分类\抑郁测评-CESD10-PHQ9\精选-PHQ-9抑郁症筛查量表.doc", "start": "1", "end": "总分"},
            enabled=True,
            first_batch_candidate=True,
            scoring_status="rule_available_pending_sensitive_review",
            scoring_notes=["本轮只录入 PHQ-9 主版本；CES-D10 来源为图片，需人工/OCR 复核后另行录入。源文件含诊断分级文字，用户端必须改为非诊断说明。"],
        ),
        ScaleSpec(
            scale_id="perceived_social_support_psss",
            display_name="领悟社会支持量表（PSSS）",
            source_folder="基于情绪反射弧的分类/领悟社会支持",
            source_files=["肖水源的社会支持评定量表与姜乾金的领悟社会支持量表.doc"],
            source_type="authorized_resource",
            audience="adult",
            audience_class="adult",
            category="成人自助",
            theme="social_support",
            reflex_node="resource",
            search_keywords=["领悟社会支持", "PSSS", "社会支持"],
            sensitive_category="none",
            item_code_prefix="PSSS",
            likert=likert(1, 7, ["极不同意", "很不同意", "稍不同意", "中立", "稍同意", "很同意", "极同意"]),
            expected_count=12,
            extraction={"file": r"基于情绪反射弧的分类\领悟社会支持\肖水源的社会支持评定量表与姜乾金的领悟社会支持量表.doc", "start": "1．在我遇到问题", "end": "【适合人群】"},
            dimensions=[
                {"code": "PSSS_OTHER", "label": "其他支持", "item_codes": ["PSSS01", "PSSS02", "PSSS05", "PSSS10"]},
                {"code": "PSSS_FAMILY", "label": "家庭支持", "item_codes": ["PSSS03", "PSSS04", "PSSS08", "PSSS11"]},
                {"code": "PSSS_FRIEND", "label": "朋友支持", "item_codes": ["PSSS06", "PSSS07", "PSSS09", "PSSS12"]},
            ],
            enabled=True,
            first_batch_candidate=True,
            scoring_status="rule_available_pending_review",
            scoring_notes=["源文件可读到 PSSS 12 题和 1-7 选项；同文件中的 SSRS 不与 PSSS 混合录入。"],
        ),
        ScaleSpec(
            scale_id="emotional_intelligence_eis_33",
            display_name="青少年情绪智力量表（EIS）",
            source_folder="学生自助量表/青少年情绪智力量表（EIS）",
            source_files=["青少年情绪智力质量EIS.sav", "指标值计算-中学生情绪智力量表（EIS）.sps"],
            source_type="authorized_resource",
            audience="student",
            audience_class="student",
            category="学生自助",
            theme="emotional_intelligence",
            reflex_node="emotion_skill",
            search_keywords=["EIS", "青少年情绪智力", "情绪能力"],
            sensitive_category="none",
            item_code_prefix="EIS",
            likert=five,
            expected_count=33,
            extraction={"file": r"学生自助量表\青少年情绪智力量表（EIS）\青少年情绪智力质量EIS.sav", "mode": "sav_labels", "prefix": "eis"},
            dimensions=[
                {"code": "EIS_EFEEL", "label": "情绪感知能力", "item_codes": [f"EIS{i:02d}" for i in [1, 5, 9, 15, 17, 19, 22, 25, 26, 29, 32, 33]], "reverse_item_codes": ["EIS05", "EIS33"]},
                {"code": "EIS_ESELF", "label": "理解和推理自身情绪的能力", "item_codes": [f"EIS{i:02d}" for i in [2, 6, 7, 10, 12, 14, 21, 28]], "reverse_item_codes": ["EIS28"]},
                {"code": "EIS_EOTHER", "label": "理解和推理他人情绪的能力", "item_codes": [f"EIS{i:02d}" for i in [4, 11, 13, 16, 24, 30]]},
                {"code": "EIS_EAPPLY", "label": "情绪运用/表达能力", "item_codes": [f"EIS{i:02d}" for i in [3, 8, 18, 20, 23, 27, 31]]},
            ],
            reverse_item_numbers={5, 28, 33},
            enabled=True,
            first_batch_candidate=True,
            scoring_status="rule_available_pending_review",
            scoring_notes=["题项来自 EIS .sav 变量标签；维度和反向题来自同目录 SPSS 计分脚本。"],
        ),
    ]


MANUAL_REVIEW_ITEMS = [
    ("parental_autonomy_support", "父母自主支持量表", "9题项.docx 当前只读到来源引用，未确认题项正文。"),
    ("family_cohesion_adaptability", "家庭亲密度与适应性量表", "当前只看到 sps 分类脚本，未确认完整题项。"),
    ("sleep_isi_psqi", "ISI/PSQI 睡眠相关量表", "ISI 说明文件仅包含 7 个评价领域和总分范围，未给出逐题原文；PSQI 为复杂计分问卷，本轮不硬录。"),
    ("cognitive_curiosity_student", "认知好奇量表-自评", "当前目录只有论文和 SPSS 计分脚本，未发现 10 个中文题项原文。"),
    ("cesd10_depression", "CES-D10 抑郁相关量表", "当前来源为 jpg 图片，未做 OCR/人工核对，暂不录入题项。"),
    ("big_five_tipi", "10 项目大五人格量表（TIPI-10）", "目录内 TIPI-10 主要为英文题项；本轮主版本改录中文 60 题版，TIPI-10 暂列复核。"),
    ("who5_wellbeing", "WHO-5 身心健康指标", "本地 .doc 为旧格式，当前脚本未能可靠抽取题项；需人工打开复核。"),
]


MANUAL_CATALOG_ENTRIES = [
    {
        "id": "sleep_isi_psqi",
        "display_name": "失眠与睡眠质量量表（ISI/PSQI，题项待人工补录）",
        "audience": "adult",
        "audience_class": "adult",
        "category": "成人自助",
        "theme": "sleep_health",
        "reflex_node": "state_observation",
        "search_keywords": ["ISI", "PSQI", "失眠", "睡眠质量"],
        "sensitive_category": "screening_or_health",
        "source_folder": "基于情绪反射弧的分类/失眠量表-ISI-PSQI",
        "source_files": ["失眠严重指数量表说明.docx", "匹兹堡睡眠质量指数问卷--(附评分标准).doc", "ISI2001.pdf"],
        "source_type": "authorized_resource",
        "review_status": "metadata_only",
        "enabled": False,
        "excluded_from_user_flow": True,
        "item_status": "missing_item_text",
        "scoring_status": "partial_rule_without_item_text",
        "boundary_notice": SENSITIVE_NOTICE,
        "result_disclaimer": SENSITIVE_NOTICE,
        "notes": "本轮仅确认 ISI 7 个评价领域和总分范围，未确认逐题原文；PSQI 需按复杂计分表人工复核。",
    },
    {
        "id": "cognitive_curiosity_student",
        "display_name": "认知好奇量表-自评（题项待人工补录）",
        "audience": "student",
        "audience_class": "student",
        "category": "学生自助",
        "theme": "cognitive_curiosity",
        "reflex_node": "motivation",
        "search_keywords": ["认知好奇", "兴趣型认知好奇", "剥夺型认知好奇"],
        "sensitive_category": "none",
        "source_folder": "学生自助量表/认知好奇量表-自评",
        "source_files": ["指标值计算-学生自评认知好奇总分与因子分 - 初中.sps", "指标值计算-学生自评认知好奇总分与因子分-高中.sps"],
        "source_type": "authorized_resource",
        "review_status": "metadata_only",
        "enabled": False,
        "excluded_from_user_flow": True,
        "item_status": "missing_item_text",
        "scoring_status": "partial_rule_without_item_text",
        "boundary_notice": NON_DIAGNOSTIC_NOTICE,
        "result_disclaimer": NON_DIAGNOSTIC_NOTICE,
        "notes": "SPSS 脚本可确认 10 题总分与兴趣型/剥夺型维度，但未包含题项原文。",
    },
    {
        "id": "parental_autonomy_support",
        "display_name": "父母自主支持量表（题项待人工补录）",
        "audience": "parent",
        "audience_class": "parent",
        "category": "家长自助",
        "theme": "parental_autonomy_support",
        "reflex_node": "support",
        "search_keywords": ["父母自主支持", "自主支持", "亲子支持"],
        "sensitive_category": "none",
        "source_folder": "家长自主量表/父母自主支持量表",
        "source_files": ["9题项.docx"],
        "source_type": "authorized_resource",
        "review_status": "metadata_only",
        "enabled": False,
        "excluded_from_user_flow": True,
        "item_status": "missing_item_text",
        "scoring_status": "missing_item_text",
        "boundary_notice": NON_DIAGNOSTIC_NOTICE,
        "result_disclaimer": NON_DIAGNOSTIC_NOTICE,
        "notes": "9题项.docx 当前只读到来源引用，未确认题项正文。",
    },
    {
        "id": "family_cohesion_adaptability",
        "display_name": "家庭亲密度与适应性量表（题项待人工补录）",
        "audience": "parent",
        "audience_class": "parent",
        "category": "家长自助",
        "theme": "family_functioning",
        "reflex_node": "family_context",
        "search_keywords": ["家庭亲密度", "家庭适应性", "FACES"],
        "sensitive_category": "family_functioning",
        "source_folder": "家长自主量表/家庭亲密度与适应性量表",
        "source_files": ["家庭亲密度与适应性分类.sps"],
        "source_type": "authorized_resource",
        "review_status": "metadata_only",
        "enabled": False,
        "excluded_from_user_flow": True,
        "item_status": "missing_item_text",
        "scoring_status": "classification_script_without_items",
        "boundary_notice": NON_DIAGNOSTIC_NOTICE,
        "result_disclaimer": NON_DIAGNOSTIC_NOTICE,
        "notes": "当前只看到分类脚本，未发现完整题项原文。",
    },
]


def extract_for_spec(spec: ScaleSpec) -> list[tuple[int, str]]:
    mode = spec.extraction.get("mode", "numbered")
    if mode == "sav_labels":
        return read_sav_variable_labels(spec.extraction["file"], spec.extraction["prefix"], spec.expected_count)

    lines = read_source_lines(spec.extraction["file"])
    if mode == "blob":
        return extract_blob_numbered_items(lines, spec.expected_count, spec.extraction.get("start"), spec.extraction.get("end"))
    if mode == "attribution":
        return extract_attribution_style_items(lines, spec.expected_count, spec.extraction.get("start"), spec.extraction.get("end"))
    if mode == "sequential":
        return extract_sequential_items(lines, spec.expected_count, spec.extraction.get("start"), spec.extraction.get("end"))
    return extract_numbered_items(
        lines,
        spec.expected_count,
        spec.extraction.get("start"),
        spec.extraction.get("end"),
        bool(spec.extraction.get("allow_unnumbered")),
    )


def write_manual_review_doc(rows: list[tuple[str, str, str]], extracted_results: list[tuple[ScaleSpec, int, str]]) -> None:
    lines = [
        "# 量表待人工录入清单",
        "",
        "更新日期：2026-06-29",
        "",
        "本清单由 `backend/scripts/extract_scale_item_drafts.py` 生成。原则：能从本地 docx/pdf 明确读到的题项进入 `content/scale_item_drafts.json`；无法可靠读取的题项不臆造，进入本清单等待人工打开源文件核对。",
        "",
        "## 已自动抽取但仍需人工复核",
        "",
        "| 量表ID | 量表名 | 抽取题数 | 复核重点 |",
        "| --- | --- | ---: | --- |",
    ]
    for spec, count, status in extracted_results:
        lines.append(f"| `{spec.scale_id}` | {spec.display_name} | {count} | {status} |")
    lines.extend(["", "## 未可靠抽取题项", "", "| 量表ID | 量表名 | 原因 |", "| --- | --- | --- |"])
    for scale_id, display_name, reason in rows:
        lines.append(f"| `{scale_id}` | {display_name} | {reason} |")
    lines.append("")
    (DOCS_ROOT / "量表待人工录入清单.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--strict", action="store_true", help="fail if a configured scale extracts fewer than expected items")
    args = parser.parse_args()

    drafts_payload = load_json(CONTENT_ROOT / "scale_item_drafts.json")
    catalog_payload = load_json(CONTENT_ROOT / "scales_catalog.json")
    drafts = drafts_payload.setdefault("drafts", [])
    catalog_scales = catalog_payload.setdefault("scales", [])

    extracted_results: list[tuple[ScaleSpec, int, str]] = []
    errors: list[str] = []

    for scale in catalog_scales:
        scale.update(default_fields_for_catalog(scale))

    for spec in scale_specs():
        try:
            extracted = extract_for_spec(spec)
        except Exception as exc:  # pragma: no cover - local source dependent
            errors.append(f"{spec.scale_id}: {exc}")
            extracted = []

        count = len(extracted)
        if count != spec.expected_count:
            status = f"抽取 {count}/{spec.expected_count}，需人工复核后再开放。"
            if args.strict:
                errors.append(f"{spec.scale_id}: expected {spec.expected_count}, got {count}")
        else:
            status = "题项数量符合预期；仍需逐题核对原文、授权和计分解释。"

        if count:
            if spec.scale_id not in PRESERVE_CURATED_DRAFT_IDS:
                upsert_by_key(drafts, "scale_id", build_draft(spec, extracted))
            item_status = "draft_extracted" if count == spec.expected_count else "partial_draft_extracted"
            notes = f"已由抽取脚本从本地源文件读取 {count}/{spec.expected_count} 个题项；正式开放前仍需人工复核。"
            upsert_by_key(catalog_scales, "id", catalog_entry(spec, item_status, notes))
        extracted_results.append((spec, count, status))

    for entry in MANUAL_CATALOG_ENTRIES:
        entry.setdefault("not_open_reason", "题项原文未确认，暂不开放填写。")
        entry.setdefault("exclusion_reason", "题项原文未确认，暂不开放填写。")
        upsert_by_key(catalog_scales, "id", entry)

    drafts_payload["updated_at"] = "2026-06-29"
    catalog_payload["updated_at"] = "2026-06-29"
    write_json(CONTENT_ROOT / "scale_item_drafts.json", drafts_payload)
    write_json(CONTENT_ROOT / "scales_catalog.json", catalog_payload)
    write_manual_review_doc(MANUAL_REVIEW_ITEMS, extracted_results)

    if errors:
        for error in errors:
            print(error)
        return 1 if args.strict else 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
