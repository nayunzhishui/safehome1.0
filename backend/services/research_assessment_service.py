"""Researcher view of completed scales, scale invitations and scale exports.

Invitations reuse the participant message center instead of a new table:
message_type="assessment_invitation", source_type="assessment_worksheet",
source_id=<worksheet id>. Whether an invitation was answered is derived from
assessment_results (same participant and worksheet, submitted after the
invitation), so there is no second status to keep in sync.

The in-app answer sheet and both CSV exports read answers through
answered_items(), so a new worksheet needs no changes here.
"""

from __future__ import annotations

from typing import Callable

from database import json_loads, new_id, row_to_dict, rows_to_dicts, write_audit_log
from services.assessment_execution_service import effective_item_score
from services.message_service import create_message, public_message


INVITATION_MESSAGE_TYPE = "assessment_invitation"
INVITATION_SOURCE_TYPE = "assessment_worksheet"
INVITATION_SENDER_ROLES = frozenset({"researcher", "supervisor", "admin"})
PARTICIPANT_ROLES = frozenset({"parent", "student", "user"})

_ANSWERED_AFTER_INVITATION = """
    SELECT {column} FROM assessment_results a
    WHERE a.user_id = m.user_id AND a.worksheet_id = m.source_id AND a.created_at >= m.created_at
"""

WorksheetLookup = Callable[[str], "dict | None"]


class ResearchAssessmentError(ValueError):
    def __init__(self, code: str, message: str, status: int = 400) -> None:
        super().__init__(message)
        self.code = code
        self.status = status


def catalog_item(worksheet: dict) -> dict:
    return {
        "id": worksheet.get("id"),
        "title": worksheet.get("display_title") or worksheet.get("source_title") or worksheet.get("id"),
        "category": worksheet.get("category") or "",
        "question_count": len(worksheet.get("questions") or []),
    }


def _is_number(value) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def result_worksheet(row: dict, lookup: WorksheetLookup) -> dict:
    """The worksheet exactly as the participant saw it when submitting.

    Results keep a content snapshot, so later wording edits do not rewrite what
    an old answer meant; the current worksheet is only a fallback.
    """
    snapshot = json_loads(row.get("content_snapshot_json"), {}) or {}
    return snapshot.get("worksheet_payload") or lookup(str(row.get("worksheet_id") or "")) or {}


def answered_items(row: dict, worksheet: dict, *, include_free_text: bool) -> list[dict]:
    """One entry per answered question, in questionnaire order.

    Exports pass include_free_text=False: typed answers can hold names or other
    identifying details, so only their length leaves the system, as in the
    other exports.
    """
    questions = [item for item in worksheet.get("questions") or [] if isinstance(item, dict) and item.get("id")]
    by_id = {item["id"]: item for item in questions}
    order = {item["id"]: number for number, item in enumerate(questions, start=1)}
    dimension_labels = {
        item.get("code") or item.get("key"): item.get("label")
        for item in worksheet.get("dimensions") or []
        if isinstance(item, dict) and item.get("label")
    }
    items = []
    for answer in json_loads(row.get("answers_json"), []) or []:
        if not isinstance(answer, dict):
            continue
        question_id = answer.get("question_id")
        question = by_id.get(question_id) or {}
        value = answer.get("value")
        option = next(
            (item for item in question.get("options") or [] if str(item.get("value")) == str(value)),
            None,
        )
        raw_score = answer.get("score")
        if option is not None:
            label = option.get("label") or str(value)
        elif include_free_text:
            label = "" if value is None else str(value)
        else:
            label = f"（文字作答 {len(str(value or '').strip())} 字，不导出原文）"
        dimension = question.get("dimension") or ""
        items.append({
            "question_no": order.get(question_id, len(questions) + len(items) + 1),
            "question_id": question_id,
            "question_text": answer.get("prompt") or question.get("prompt") or "",
            "dimension": dimension_labels.get(dimension) or dimension,
            "answer_value": "" if option is None else option.get("value"),
            "answer_label": label,
            "raw_score": raw_score if _is_number(raw_score) else "",
            "scored_value": effective_item_score(question, raw_score) if _is_number(raw_score) else "",
        })
    return sorted(items, key=lambda item: item["question_no"])


def _dimension_scores(row: dict) -> list[dict]:
    scores = json_loads(row.get("scores_json"), {}) or {}
    return [item for item in scores.get("dimensions") or [] if isinstance(item, dict)]


def load_assessment_result(conn, user_id: str, result_id: str) -> dict | None:
    row = conn.execute(
        "SELECT * FROM assessment_results WHERE id = ? AND user_id = ?",
        (result_id, user_id),
    ).fetchone()
    return row_to_dict(row) if row else None


def assessment_result_detail(row: dict, lookup: WorksheetLookup) -> dict:
    worksheet = result_worksheet(row, lookup)
    return {
        "id": row.get("id"),
        "worksheet_id": row.get("worksheet_id"),
        "worksheet_title": row.get("worksheet_title") or worksheet.get("display_title") or row.get("worksheet_id"),
        "created_at": row.get("created_at"),
        "total_score": row.get("total_score"),
        "result_summary": row.get("result_summary") or "",
        "dimensions": [
            {"label": item.get("label") or item.get("key"), "score": item.get("score"), "score_range": item.get("score_range")}
            for item in _dimension_scores(row)
        ],
        "answers": [
            {"question_id": item["question_id"], "prompt": item["question_text"], "answer": item["answer_label"]}
            for item in answered_items(row, worksheet, include_free_text=True)
        ],
    }


def item_export_rows(rows, lookup: WorksheetLookup, anonymize: Callable[[str], str]) -> list[dict]:
    """Long table: one row per answered question, any mix of worksheets."""
    export = []
    for source in rows:
        row = dict(source)
        worksheet = result_worksheet(row, lookup)
        for item in answered_items(row, worksheet, include_free_text=False):
            export.append({
                "result_id": row["id"],
                "anonymous_id": anonymize(str(row["user_id"])),
                "worksheet_id": row.get("worksheet_id"),
                "worksheet_title": row.get("worksheet_title") or worksheet.get("display_title") or "",
                **item,
                "total_score": row.get("total_score"),
                "created_at": row.get("created_at"),
            })
    return export


def _unique(name: str, taken: set[str]) -> str:
    candidate, suffix = name, 2
    while candidate in taken:
        candidate, suffix = f"{name} ({suffix})", suffix + 1
    taken.add(candidate)
    return candidate


def wide_export_rows(rows, worksheet: dict, lookup: WorksheetLookup, anonymize: Callable[[str], str]) -> list[dict]:
    """Wide table for one worksheet: one row per answer sheet.

    Columns are total, every dimension score, then every question (header =
    number and wording, cell = the chosen option's score), all taken from the
    worksheet definition so a new scale exports without code changes.
    """
    rows = [dict(item) for item in rows]
    taken = {"result_id", "anonymous_id", "created_at", "total_score"}
    dimension_columns: dict[str, str] = {}
    for row in rows:
        for item in _dimension_scores(row):
            key = str(item.get("key") or item.get("label") or "")
            if key and key not in dimension_columns:
                dimension_columns[key] = _unique(f"维度:{item.get('label') or key}", taken)
    question_columns = {
        question["id"]: _unique(f"Q{number} {str(question.get('prompt') or '').strip()[:40]}".strip(), taken)
        for number, question in enumerate(
            [item for item in worksheet.get("questions") or [] if isinstance(item, dict) and item.get("id")],
            start=1,
        )
    }
    export = []
    for row in rows:
        line = {
            "result_id": row["id"],
            "anonymous_id": anonymize(str(row["user_id"])),
            "created_at": row.get("created_at"),
            "total_score": row.get("total_score"),
        }
        scores = {str(item.get("key") or item.get("label") or ""): item.get("score") for item in _dimension_scores(row)}
        for key, column in dimension_columns.items():
            line[column] = scores.get(key, "")
        answers = {
            item["question_id"]: item["raw_score"] if item["raw_score"] != "" else item["answer_label"]
            for item in answered_items(row, result_worksheet(row, lookup), include_free_text=False)
        }
        for question_id, column in question_columns.items():
            line[column] = answers.get(question_id, "")
        export.append(line)
    return export


def list_assessment_invitations(conn, user_id: str, limit: int = 30) -> list[dict]:
    rows = conn.execute(
        f"""
        SELECT m.id, m.source_id AS worksheet_id, m.title, m.status, m.created_at, m.read_at,
            ({_ANSWERED_AFTER_INVITATION.format(column="a.id")} ORDER BY a.created_at ASC LIMIT 1) AS result_id,
            ({_ANSWERED_AFTER_INVITATION.format(column="MIN(a.created_at)")}) AS completed_at
        FROM messages m
        WHERE m.user_id = ? AND m.message_type = ?
        ORDER BY m.created_at DESC
        LIMIT ?
        """,
        (user_id, INVITATION_MESSAGE_TYPE, limit),
    ).fetchall()
    items = []
    for item in rows_to_dicts(rows):
        if item.get("result_id"):
            item["state"] = "completed"
        elif item.get("status") in {"read", "withdrawn"}:
            item["state"] = item["status"]
        else:
            item["state"] = "sent"
        items.append(item)
    return items


def send_assessment_invitation(conn, actor: dict, user_id: str, worksheet: dict) -> dict:
    worksheet_id = str(worksheet.get("id") or "")
    pending = conn.execute(
        f"""
        SELECT m.id FROM messages m
        WHERE m.user_id = ? AND m.message_type = ? AND m.source_id = ? AND m.status != 'withdrawn'
          AND NOT EXISTS ({_ANSWERED_AFTER_INVITATION.format(column="1")})
        LIMIT 1
        """,
        (user_id, INVITATION_MESSAGE_TYPE, worksheet_id),
    ).fetchone()
    if pending:
        raise ResearchAssessmentError("assessment_invitation_pending", "已经发过这份量表，对方还没填写。", 409)
    item = catalog_item(worksheet)
    body = "\n".join([
        f"研究团队邀请你填写《{item['title']}》，共 {item['question_count']} 题。",
        "填不填由你决定。填好后，结果和你自己在测一测里做的一样，保存在你的记录里，研究团队也能看到。",
        "点下方“去填写”开始。",
    ])
    message = create_message(
        conn,
        user_id,
        f"邀请你填写《{item['title']}》",
        body,
        INVITATION_MESSAGE_TYPE,
        INVITATION_SOURCE_TYPE,
        worksheet_id,
        sender_id=str(actor["id"]),
        sender_role=str(actor.get("original_role") or actor.get("role") or "researcher"),
        idempotency_key=f"assessment-invitation:{new_id('inv')}",
    )
    write_audit_log(
        conn,
        "research_assessment_invitation_sent",
        actor["id"],
        "user",
        user_id,
        {"worksheet_id": worksheet_id, "message_id": message["id"]},
    )
    return public_message(message)
