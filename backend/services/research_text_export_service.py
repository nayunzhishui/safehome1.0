"""Owner-only export of what participants wrote, with identifiers masked.

Every other export keeps free text out (lengths only). This one exists for
later qualitative or text analysis, so the export route asks for an explicit
confirmation each time and audits it. Phone numbers, emails, ID numbers and IP
addresses are masked; names and schools cannot be recognised automatically.

Sources follow the user-written fields of the offline text contract
(analysis/text_analysis). System and supervisor text, contact fields and
human-support requests (crisis details plus contact) stay out. To add a source,
add one TextSource entry here and its label in the mini program export panel.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from services.ai_qa_input_security_service import mask_identifiers
from services.research_assessment_service import WorksheetLookup, answered_items, result_worksheet


@dataclass(frozen=True)
class TextSource:
    label: str
    table: str
    context_fields: tuple[str, ...]
    text_fields: tuple[str, ...]


TEXT_SOURCES: dict[str, TextSource] = {
    "diaries": TextSource(
        "情绪日记",
        "emotion_diaries",
        ("event_time", "scene", "parent_emotion", "parent_emotion_intensity", "child_emotion", "child_emotion_intensity"),
        ("event_description", "automatic_thought", "body_sensation", "behavior", "raw_text"),
    ),
    "checkins": TextSource(
        "练习感想",
        "checkins",
        ("card_id", "emotion_before", "emotion_after", "helpfulness_rating"),
        ("reflection",),
    ),
    "thermometer": TextSource(
        "情绪温度计备注",
        "emotion_thermometer",
        ("emotion_label", "intensity_level", "valence_level", "arousal_level", "control_level"),
        ("brief_text",),
    ),
}
# Typed answers inside scales live in assessment_results.answers_json.
ASSESSMENT_TEXT_SOURCE = "assessment_answers"


def is_text_source(key: str) -> bool:
    return key in TEXT_SOURCES or key == ASSESSMENT_TEXT_SOURCE


def record_text_rows(source: TextSource, rows, anonymize: Callable[[str], str]) -> list[dict]:
    """One row per record that has any text: context columns, then masked text columns."""
    export = []
    for raw in rows:
        row = dict(raw)
        texts: dict[str, str] = {}
        masked = 0
        for field in source.text_fields:
            if field in row:
                value, count = mask_identifiers(row.get(field))
                texts[field] = value.strip()
                masked += count
        if not any(texts.values()):
            continue
        export.append({
            "record_id": row["id"],
            "anonymous_id": anonymize(str(row["user_id"])),
            **{field: row.get(field) for field in source.context_fields if field in row},
            **texts,
            "identifiers_masked": masked,
            "created_at": row.get("created_at"),
        })
    return export


def assessment_text_rows(rows, lookup: WorksheetLookup, anonymize: Callable[[str], str]) -> list[dict]:
    """One row per typed (non-option) answer inside a scale."""
    export = []
    for raw in rows:
        row = dict(raw)
        worksheet = result_worksheet(row, lookup)
        for item in answered_items(row, worksheet, include_free_text=True):
            if item["answer_value"] != "":
                continue
            text, masked = mask_identifiers(item["answer_label"])
            if not text.strip():
                continue
            export.append({
                "result_id": row["id"],
                "anonymous_id": anonymize(str(row["user_id"])),
                "worksheet_id": row.get("worksheet_id"),
                "worksheet_title": row.get("worksheet_title") or worksheet.get("display_title") or "",
                "question_no": item["question_no"],
                "question_text": item["question_text"],
                "answer_text": text.strip(),
                "identifiers_masked": masked,
                "created_at": row.get("created_at"),
            })
    return export
