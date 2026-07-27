"""受控AI问答的可审计提示词、引用契约和词面支撑检查。"""

from __future__ import annotations

import re


PROMPT_TEMPLATE_VERSION = "safehome-ai-qa-prompt-v2"
ALLOWED_INTENTS = (
    "organize_material",
    "draft_question",
    "flag_insufficient_evidence",
    "discussion_checklist",
)

SYSTEM_PROMPT = """你是“安心家”研究者侧的受控内容助手。
你只能整理已批准材料、草拟待讨论问题、提醒证据不足或生成讨论清单。
不得给出诊断、临床结论、预后、用药、法律判断或治疗保证。
每条关键说法必须使用[S1]这样的编号引用已批准来源；来源不足时必须明确拒答。
措辞保持非诊断、支持性、非评判，输出只是供研究者核对的草稿。"""

CONCLUSION_TERMS = (
    "确诊",
    "诊断为",
    "可以诊断",
    "符合抑郁",
    "符合焦虑",
    "抑郁症",
    "焦虑症",
    "多动症",
    "自闭症",
    "对立违抗",
    "回避型依恋",
    "焦虑型依恋",
    "人格障碍",
    "人格类型是",
    "一定会",
    "保证治愈",
    "保证改善",
    "必然",
    "肯定是",
    "确定是",
    "typical of",
    "diagnos",
    "you have depression",
    "you have anxiety",
    "personality disorder",
    "system prompt",
    "api key",
    "管理员密钥",
)


def build_system_prompt() -> str:
    return SYSTEM_PROMPT


def build_user_prompt(question: str, sources: list[dict]) -> str:
    lines = ["【问题】", str(question or "").strip(), "", "【已批准来源】"]
    for index, source in enumerate(sources, 1):
        title = str(source.get("title") or source.get("content_id") or f"来源{index}")
        excerpt = str(source.get("excerpt") or "").strip()[:360]
        lines.append(f"[S{index}] {title}：{excerpt}")
    lines.extend(["", "只基于上述来源整理，并为关键说法标注有效的[S编号]。"])
    return "\n".join(lines)


def _lexical_units(text: str) -> list[str]:
    normalized = str(text or "")
    units: list[str] = []
    for segment in re.findall(r"[\u4e00-\u9fff]{2,}", normalized):
        units.extend(segment[index : index + 2] for index in range(len(segment) - 1))
    units.extend(re.findall(r"[a-zA-Z]{3,}", normalized.lower()))
    return units


def contains_conclusion(text: str) -> list[str]:
    lowered = str(text or "").lower()
    return [term for term in CONCLUSION_TERMS if term.lower() in lowered]


def grounding_ratio(answer: str, sources: list[dict]) -> float:
    """词面重叠启发式，仅用于阻断明显无来源内容，不代表事实正确性。"""
    source_text = " ".join(
        f"{source.get('title') or ''} {source.get('excerpt') or ''}"
        for source in sources
    )
    source_units = set(_lexical_units(source_text))
    answer_units = _lexical_units(answer)
    if not source_units or not answer_units:
        return 0.0
    return round(sum(unit in source_units for unit in answer_units) / len(answer_units), 3)


def validate_output(answer: str, sources: list[dict], *, min_grounding: float = 0.15) -> dict:
    violations: list[str] = []
    conclusion_hits = contains_conclusion(answer)
    if conclusion_hits:
        violations.append("conclusion_language")
    if not sources:
        violations.append("missing_approved_citation")

    citation_numbers = [int(value) for value in re.findall(r"\[S(\d+)\]", str(answer or ""))]
    if not citation_numbers:
        violations.append("missing_citation_marker")
    elif any(number < 1 or number > len(sources) for number in citation_numbers):
        violations.append("invalid_citation_marker")

    ratio = grounding_ratio(answer, sources)
    if ratio < min_grounding:
        violations.append("low_grounding")
    return {
        "ok": not violations,
        "violations": sorted(set(violations)),
        "grounding_ratio": ratio,
        "grounding_method": "lexical_overlap_heuristic_v1",
        "conclusion_hits": conclusion_hits,
        "prompt_template_version": PROMPT_TEMPLATE_VERSION,
    }
