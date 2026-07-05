"""Import assessment worksheet definitions from content JSON into the database."""

from __future__ import annotations

import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from database import get_connection, init_db, json_dumps, load_content_json, now_iso


WORKSHEET_COLUMNS = [
    "id",
    "display_title",
    "source_title",
    "source_file",
    "category",
    "audience_class",
    "reflex_node",
    "questions_json",
    "dimensions_json",
    "dimension_score_method",
    "scoring_notes_json",
    "search_keywords_json",
    "boundary_notice",
    "result_disclaimer",
    "instructions",
    "sensitive_category",
    "profile_model_id",
    "enabled_for_user",
    "review_status",
    "review_note",
    "source_version",
    "source_type",
    "audience",
    "audience_class_detail",
    "recommended_card_ids_json",
    "sections_json",
    "scoring",
    "pages",
    "_meta_json",
    "created_at",
    "updated_at",
]


def _as_sensitive_category(value) -> str:
    if isinstance(value, bool):
        return "screening_or_health" if value else "none"
    return str(value or "none")


def worksheet_to_row(worksheet: dict, timestamp: str) -> dict:
    return {
        "id": worksheet["id"],
        "display_title": worksheet.get("display_title") or worksheet.get("source_title") or worksheet["id"],
        "source_title": worksheet.get("source_title"),
        "source_file": worksheet.get("source_file"),
        "category": worksheet.get("category"),
        "audience_class": worksheet.get("audience_class"),
        "reflex_node": worksheet.get("reflex_node"),
        "questions_json": json_dumps(worksheet.get("questions", [])),
        "dimensions_json": json_dumps(worksheet.get("dimensions", [])),
        "dimension_score_method": worksheet.get("dimension_score_method") or "sum",
        "scoring_notes_json": json_dumps(worksheet.get("scoring_notes", {})),
        "search_keywords_json": json_dumps(worksheet.get("search_keywords", [])),
        "boundary_notice": worksheet.get("boundary_notice"),
        "result_disclaimer": worksheet.get("result_disclaimer"),
        "instructions": worksheet.get("instructions"),
        "sensitive_category": _as_sensitive_category(worksheet.get("sensitive_category")),
        "profile_model_id": worksheet.get("profile_model_id"),
        "enabled_for_user": 1 if worksheet.get("enabled_for_user", True) else 0,
        "review_status": worksheet.get("review_status") or "approved",
        "review_note": worksheet.get("review_note"),
        "source_version": worksheet.get("source_version"),
        "source_type": worksheet.get("source_type"),
        "audience": worksheet.get("audience"),
        "audience_class_detail": worksheet.get("audience_class_detail"),
        "recommended_card_ids_json": json_dumps(worksheet.get("recommended_card_ids", [])),
        "sections_json": json_dumps(worksheet.get("sections", [])),
        "scoring": worksheet.get("scoring"),
        "pages": worksheet.get("pages"),
        "_meta_json": json_dumps(worksheet.get("_meta", {})),
        "created_at": timestamp,
        "updated_at": timestamp,
    }


def row_changed(existing: dict, new_row: dict) -> bool:
    comparable = [column for column in WORKSHEET_COLUMNS if column not in {"created_at", "updated_at"}]
    for column in comparable:
        if str(existing.get(column) or "") != str(new_row.get(column) or ""):
            return True
    return False


def upsert_worksheet(conn, row: dict) -> str:
    existing = conn.execute("SELECT * FROM assessment_worksheets WHERE id = ?", (row["id"],)).fetchone()
    provider = getattr(conn, "provider", "sqlite")
    if existing is not None:
        existing_dict = dict(existing)
        if not row_changed(existing_dict, row):
            return "skipped"
        row["created_at"] = existing_dict.get("created_at") or row["created_at"]

    params = [row[column] for column in WORKSHEET_COLUMNS]
    placeholders = ", ".join("?" for _ in WORKSHEET_COLUMNS)
    column_sql = ", ".join(WORKSHEET_COLUMNS)
    update_columns = [column for column in WORKSHEET_COLUMNS if column not in {"id", "created_at"}]
    if provider == "mysql":
        updates = ", ".join(f"{column}=VALUES({column})" for column in update_columns)
        conn.execute(
            f"""
            INSERT INTO assessment_worksheets ({column_sql})
            VALUES ({placeholders})
            ON DUPLICATE KEY UPDATE {updates}
            """,
            params,
        )
    else:
        updates = ", ".join(f"{column}=excluded.{column}" for column in update_columns)
        conn.execute(
            f"""
            INSERT INTO assessment_worksheets ({column_sql})
            VALUES ({placeholders})
            ON CONFLICT(id) DO UPDATE SET {updates}
            """,
            params,
        )
    return "updated" if existing is not None else "created"


def import_worksheets() -> dict[str, int]:
    init_db()
    payload = load_content_json("assessment_worksheets.json")
    stats = {"created": 0, "updated": 0, "skipped": 0}
    timestamp = now_iso()
    with get_connection() as conn:
        for worksheet in payload.get("worksheets", []):
            if not isinstance(worksheet, dict) or not worksheet.get("id"):
                continue
            action = upsert_worksheet(conn, worksheet_to_row(worksheet, timestamp))
            stats[action] += 1
        conn.commit()
    return stats


def main() -> None:
    stats = import_worksheets()
    print(
        "assessment_worksheets import: "
        f"created={stats['created']} updated={stats['updated']} skipped={stats['skipped']}"
    )


if __name__ == "__main__":
    main()
