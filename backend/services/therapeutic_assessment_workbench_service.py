"""Researcher evidence workbench with scoped reads and recoverable drafts."""

from __future__ import annotations

from database import (
    get_connection,
    json_dumps,
    json_loads,
    new_id,
    now_iso,
    row_to_dict,
    rows_to_dicts,
    write_audit_log,
)
from services.therapeutic_assessment_evidence_service import (
    _present as present_evidence,
    summarize_evidence,
)
from services.therapeutic_assessment_service import (
    TherapeuticAssessmentError,
    _assert_researcher,
    _case_row,
    _idempotency,
    _present_case,
)


ALLOWED_KINDS = {"O", "P", "H", "U"}
ALLOWED_REVIEW_STATUSES = {
    "recorded",
    "candidate",
    "draft",
    "human_reviewed",
    "changes_requested",
    "participant_checked",
}
ALLOWED_VISIBILITY = {"participant", "research_team", "supervisor"}


def _filters(query: dict) -> dict:
    kind = str(query.get("kind") or "").upper()
    review_status = str(query.get("review_status") or "")
    visibility = str(query.get("visibility") or "")
    if kind and kind not in ALLOWED_KINDS:
        raise TherapeuticAssessmentError("validation_error", "kind过滤条件无效。")
    if review_status and review_status not in ALLOWED_REVIEW_STATUSES:
        raise TherapeuticAssessmentError("validation_error", "review_status过滤条件无效。")
    if visibility and visibility not in ALLOWED_VISIBILITY:
        raise TherapeuticAssessmentError("validation_error", "visibility过滤条件无效。")
    return {"kind": kind, "review_status": review_status, "visibility": visibility}


def _page(query: dict) -> tuple[int, int]:
    try:
        page = int(query.get("page") or 1)
        page_size = int(query.get("page_size") or 10)
    except (TypeError, ValueError) as exc:
        raise TherapeuticAssessmentError("validation_error", "分页参数必须为整数。") from exc
    if page < 1 or page_size < 1 or page_size > 50:
        raise TherapeuticAssessmentError("validation_error", "分页参数超出允许范围。")
    return page, page_size


def _present_draft(row: dict | None, case_id: str, researcher_id: str) -> dict:
    if row is None:
        return {
            "id": None,
            "case_id": case_id,
            "researcher_user_id": researcher_id,
            "internal_notes": "",
            "participant_visible_draft": "",
            "filters": {},
            "selected_evidence_id": None,
            "version": 0,
            "updated_at": None,
        }
    item = dict(row)
    item["filters"] = json_loads(item.pop("filters_json", None), {})
    return item


def get_workbench(actor: dict, case_id: str, query: dict) -> dict:
    filters = _filters(query)
    page, page_size = _page(query)
    clauses = ["case_id = ?"]
    params: list[object] = [case_id]
    if filters["kind"]:
        clauses.append("kind = ?")
        params.append(filters["kind"])
    if filters["review_status"]:
        clauses.append("review_status = ?")
        params.append(filters["review_status"])
    if filters["visibility"]:
        clauses.append("visibility_scope_json LIKE ?")
        params.append(f'%"{filters["visibility"]}"%')
    where = " AND ".join(clauses)
    offset = (page - 1) * page_size

    with get_connection() as conn:
        case = _case_row(conn, case_id)
        _assert_researcher(conn, actor, case)
        total = int(
            conn.execute(
                f"SELECT COUNT(*) AS count FROM therapeutic_assessment_evidence_items WHERE {where}",
                tuple(params),
            ).fetchone()["count"]
        )
        rows = rows_to_dicts(
            conn.execute(
                f"""
                SELECT * FROM therapeutic_assessment_evidence_items
                WHERE {where}
                ORDER BY observed_at DESC, created_at DESC, id DESC
                LIMIT ? OFFSET ?
                """,
                (*params, page_size, offset),
            ).fetchall()
        )
        summary_items = [
            present_evidence(row)
            for row in rows_to_dicts(
                conn.execute(
                    "SELECT * FROM therapeutic_assessment_evidence_items WHERE case_id = ?",
                    (case_id,),
                ).fetchall()
            )
        ]
        draft = conn.execute(
            """
            SELECT * FROM therapeutic_assessment_researcher_workbench_drafts
            WHERE case_id = ? AND researcher_user_id = ?
            """,
            (case_id, str(actor["id"])),
        ).fetchone()
        write_audit_log(
            conn,
            "therapeutic_assessment_workbench_viewed",
            str(actor["id"]),
            "therapeutic_assessment_case",
            case_id,
            {"page": page, "page_size": page_size, "filters": filters, "returned": len(rows)},
        )
        conn.commit()
        return {
            "case": _present_case(conn, case, actor),
            "evidence_items": [present_evidence(row) for row in rows],
            "evidence_total": total,
            "evidence_summary": summarize_evidence(summary_items),
            "page": page,
            "page_size": page_size,
            "has_more": offset + len(rows) < total,
            "filters": filters,
            "draft": _present_draft(row_to_dict(draft), case_id, str(actor["id"])),
        }


def save_workbench_draft(actor: dict, case_id: str, payload: dict, idempotency_key: str) -> dict:
    key = _idempotency(idempotency_key)
    expected_version = payload.get("expected_version")
    if not isinstance(expected_version, int) or expected_version < 0:
        raise TherapeuticAssessmentError("validation_error", "expected_version必须为非负整数。")
    internal_notes = str(payload.get("internal_notes") or "").strip()
    participant_visible = str(payload.get("participant_visible_draft") or "").strip()
    if len(internal_notes) > 12000 or len(participant_visible) > 6000:
        raise TherapeuticAssessmentError("validation_error", "工作台草稿长度超出允许范围。")
    filters = _filters(payload.get("filters") if isinstance(payload.get("filters"), dict) else {})
    selected_evidence_id = str(payload.get("selected_evidence_id") or "").strip() or None
    actor_id = str(actor["id"])
    timestamp = now_iso()

    with get_connection() as conn:
        case = _case_row(conn, case_id)
        _assert_researcher(conn, actor, case)
        from services.therapeutic_assessment_competency_service import (
            assert_task_authorized,
        )

        assert_task_authorized(conn, actor, case, "workbench_draft")
        prior_event = conn.execute(
            """
            SELECT d.* FROM therapeutic_assessment_researcher_workbench_draft_events e
            JOIN therapeutic_assessment_researcher_workbench_drafts d ON d.id = e.draft_id
            WHERE e.researcher_user_id = ? AND e.idempotency_key = ?
            """,
            (actor_id, key),
        ).fetchone()
        if prior_event is not None:
            prior = row_to_dict(prior_event)
            if str(prior["case_id"]) != case_id:
                raise TherapeuticAssessmentError("idempotency_conflict", "该提交标识已用于其它记录。", 409)
            return _present_draft(prior, case_id, actor_id)
        if selected_evidence_id:
            belongs = conn.execute(
                "SELECT id FROM therapeutic_assessment_evidence_items WHERE id = ? AND case_id = ?",
                (selected_evidence_id, case_id),
            ).fetchone()
            if belongs is None:
                raise TherapeuticAssessmentError("validation_error", "所选证据不属于当前记录。")
        current = conn.execute(
            """
            SELECT * FROM therapeutic_assessment_researcher_workbench_drafts
            WHERE case_id = ? AND researcher_user_id = ?
            """,
            (case_id, actor_id),
        ).fetchone()
        if current is None:
            if expected_version != 0:
                raise TherapeuticAssessmentError("version_conflict", "工作台草稿已变化，请刷新后重试。", 409)
            draft_id = new_id("ta_workbench_draft")
            result_version = 1
            conn.execute(
                """
                INSERT INTO therapeutic_assessment_researcher_workbench_drafts (
                    id, case_id, researcher_user_id, internal_notes,
                    participant_visible_draft, filters_json, selected_evidence_id,
                    version, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?, ?)
                """,
                (
                    draft_id,
                    case_id,
                    actor_id,
                    internal_notes,
                    participant_visible,
                    json_dumps(filters),
                    selected_evidence_id,
                    timestamp,
                    timestamp,
                ),
            )
        else:
            current_dict = row_to_dict(current)
            if int(current_dict["version"]) != expected_version:
                raise TherapeuticAssessmentError("version_conflict", "工作台草稿已变化，请刷新后重试。", 409)
            draft_id = str(current_dict["id"])
            result_version = expected_version + 1
            cursor = conn.execute(
                """
                UPDATE therapeutic_assessment_researcher_workbench_drafts
                SET internal_notes = ?, participant_visible_draft = ?, filters_json = ?,
                    selected_evidence_id = ?, version = version + 1, updated_at = ?
                WHERE id = ? AND version = ?
                """,
                (
                    internal_notes,
                    participant_visible,
                    json_dumps(filters),
                    selected_evidence_id,
                    timestamp,
                    draft_id,
                    expected_version,
                ),
            )
            if cursor.rowcount != 1:
                raise TherapeuticAssessmentError("version_conflict", "工作台草稿已变化，请刷新后重试。", 409)
        conn.execute(
            """
            INSERT INTO therapeutic_assessment_researcher_workbench_draft_events (
                id, draft_id, researcher_user_id, result_version, idempotency_key, created_at
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (new_id("ta_workbench_event"), draft_id, actor_id, result_version, key, timestamp),
        )
        write_audit_log(
            conn,
            "therapeutic_assessment_workbench_draft_saved",
            actor_id,
            "therapeutic_assessment_case",
            case_id,
            {
                "draft_id": draft_id,
                "version": result_version,
                "internal_length": len(internal_notes),
                "participant_visible_length": len(participant_visible),
            },
        )
        conn.commit()
        saved = conn.execute(
            "SELECT * FROM therapeutic_assessment_researcher_workbench_drafts WHERE id = ?",
            (draft_id,),
        ).fetchone()
        return _present_draft(row_to_dict(saved), case_id, actor_id)
