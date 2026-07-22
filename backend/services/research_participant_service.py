"""Role-scoped participant summaries and lazy, paged research modules."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

from database import json_loads, list_database_columns, list_database_tables, rows_to_dicts


@dataclass(frozen=True)
class ModuleSpec:
    label: str
    table: str
    fields: tuple[str, ...]
    type_field: str | None = None
    status_field: str | None = None
    sensitive: bool = False
    fixed_where: str = ""
    fixed_params: tuple[str, ...] = ()
    json_fields: tuple[str, ...] = ()


MODULE_SPECS: dict[str, ModuleSpec] = {
    "assessments": ModuleSpec(
        "支持性测评", "assessment_results",
        ("id", "worksheet_id", "worksheet_title", "category", "total_score", "result_summary", "profile_model_id", "profile_cluster_id", "profile_confidence", "created_at"),
        type_field="category", sensitive=True,
    ),
    "measurements": ModuleSpec(
        "测一测", "emotion_thermometer",
        ("id", "intensity_level", "valence_level", "arousal_level", "control_level", "emotion_label", "brief_text", "created_at"),
        type_field="emotion_label", sensitive=True,
    ),
    "diaries": ModuleSpec(
        "情绪日记", "emotion_diaries",
        ("id", "event_time", "scene", "event_description", "parent_emotion", "parent_emotion_intensity", "child_emotion", "child_emotion_intensity", "automatic_thought", "body_sensation", "behavior", "created_at"),
        type_field="scene", sensitive=True,
    ),
    "training": ModuleSpec(
        "训练记录", "checkins",
        ("id", "card_id", "completed", "emotion_before", "emotion_after", "reflection", "helpfulness_rating", "skip_reason", "created_at"),
        type_field="card_id", status_field="completed", sensitive=True,
    ),
    "stage_reports": ModuleSpec(
        "阶段报告", "relationship_screening_reports",
        ("id", "enrollment_id", "version", "status", "report_json", "confirmed_at", "created_at", "updated_at"),
        status_field="status", sensitive=True, json_fields=("report_json",),
    ),
    "relationship_pilot": ModuleSpec(
        "关系探索试点", "relationship_pilot_tasks",
        ("id", "enrollment_id", "task_type", "narration", "answers_json", "risk_level", "review_status", "created_at", "updated_at"),
        type_field="task_type", status_field="review_status", sensitive=True, json_fields=("answers_json",),
    ),
    "project_tests": ModuleSpec(
        "项目测试", "records",
        ("id", "source_id", "data_json", "created_at", "updated_at"),
        type_field="source_id", sensitive=True, fixed_where="module_type = ?", fixed_params=("program_entry",), json_fields=("data_json",),
    ),
    "messages": ModuleSpec(
        "消息", "messages",
        ("id", "sender_role", "message_type", "title", "body", "source_type", "source_id", "status", "created_at", "read_at"),
        type_field="message_type", status_field="status", sensitive=True,
    ),
    "human_support": ModuleSpec(
        "人工支持", "supervision_requests",
        ("id", "source_type", "source_id", "source_title", "message", "risk_hint", "risk_level", "status", "supervisor_reply", "created_at", "replied_at"),
        type_field="source_type", status_field="status", sensitive=True,
    ),
}


def anonymous_id(user_id: str) -> str:
    return f"anon_{hashlib.sha256(user_id.encode('utf-8')).hexdigest()[:12]}"


def _table_columns(conn, table: str) -> set[str]:
    return {str(row["name"]) for row in list_database_columns(conn, table)}


def _table_exists(conn, table: str) -> bool:
    return table in {str(row["name"]) for row in list_database_tables(conn)}


def _available_fields(conn, spec: ModuleSpec) -> list[str]:
    columns = _table_columns(conn, spec.table)
    return [field for field in spec.fields if field in columns]


def module_catalog(conn, user_id: str) -> list[dict]:
    items = []
    for key, spec in MODULE_SPECS.items():
        if not _table_exists(conn, spec.table):
            count = 0
        else:
            clauses = ["user_id = ?"]
            params: list[object] = [user_id]
            if spec.fixed_where:
                clauses.append(spec.fixed_where)
                params.extend(spec.fixed_params)
            count = int(conn.execute(f"SELECT COUNT(*) AS count FROM {spec.table} WHERE {' AND '.join(clauses)}", tuple(params)).fetchone()["count"])
        items.append({"key": key, "label": spec.label, "count": count, "sensitive": spec.sensitive})
    items.append({"key": "timeline", "label": "时间线", "count": sum(item["count"] for item in items), "sensitive": False})
    return items


def participant_summary(conn, user_id: str) -> dict | None:
    user = conn.execute(
        "SELECT id AS user_id, nickname, role, status, created_at, updated_at FROM users WHERE id = ? AND COALESCE(status, 'active') != 'deleted'",
        (user_id,),
    ).fetchone()
    if user is None:
        return None
    enrollment = conn.execute(
        "SELECT id, status, review_status, assigned_researcher_id, created_at FROM relationship_pilot_enrollments WHERE user_id = ? ORDER BY created_at DESC LIMIT 1",
        (user_id,),
    ).fetchone()
    assignment = None
    if enrollment and _table_exists(conn, "research_scope_assignments"):
        assignment = conn.execute(
            "SELECT actor_id, assignment_role, status, updated_at FROM research_scope_assignments WHERE enrollment_id = ? ORDER BY updated_at DESC LIMIT 1",
            (enrollment["id"],),
        ).fetchone()
    catalog = module_catalog(conn, user_id)
    return {
        "participant": {**dict(user), "anonymous_id": anonymous_id(user_id)},
        "enrollment": dict(enrollment) if enrollment else None,
        "assignment": dict(assignment) if assignment else None,
        "modules": catalog,
        "audit_summary": {
            "related_event_count": int(conn.execute("SELECT COUNT(*) AS count FROM audit_logs WHERE target_id = ? OR actor_id = ?", (user_id, user_id)).fetchone()["count"])
        },
        "boundary_notice": "原始填写仅供授权研究审阅，不得直接改写；研究者备注、反馈版本与处置状态另存并保留审计。",
    }


def _normalize_rows(rows: list[dict], json_fields: tuple[str, ...]) -> list[dict]:
    normalized = []
    for row in rows:
        item = dict(row)
        for field in json_fields:
            if field in item:
                value = json_loads(item.pop(field), {})
                if field == "data_json" and isinstance(value, dict):
                    item.update(value)
                else:
                    item[field.removesuffix("_json")] = value
        normalized.append(item)
    return normalized


def list_module(
    conn,
    user_id: str,
    module_key: str,
    *,
    page: int,
    page_size: int,
    date_from: str = "",
    date_to: str = "",
    item_type: str = "",
    status: str = "",
    batch: str = "",
) -> dict:
    if module_key == "timeline":
        return _timeline(conn, user_id, page=page, page_size=page_size, date_from=date_from, date_to=date_to, item_type=item_type)
    spec = MODULE_SPECS.get(module_key)
    if spec is None:
        raise KeyError(module_key)
    if not _table_exists(conn, spec.table):
        return _page_payload(module_key, spec.label, [], 0, page, page_size, spec.sensitive)
    fields = _available_fields(conn, spec)
    clauses = ["user_id = ?"]
    params: list[object] = [user_id]
    if spec.fixed_where:
        clauses.append(spec.fixed_where)
        params.extend(spec.fixed_params)
    columns = _table_columns(conn, spec.table)
    if date_from and "created_at" in columns:
        clauses.append("created_at >= ?")
        params.append(date_from)
    if date_to and "created_at" in columns:
        clauses.append("created_at <= ?")
        params.append(date_to)
    if item_type and spec.type_field and spec.type_field in columns:
        clauses.append(f"{spec.type_field} = ?")
        params.append(item_type)
    if status and spec.status_field and spec.status_field in columns:
        if spec.status_field == "completed":
            clauses.append("completed = ?")
            params.append(1 if status in {"completed", "1", "true"} else 0)
        else:
            clauses.append(f"{spec.status_field} = ?")
            params.append(status)
    if batch:
        if "study_batch" in columns:
            clauses.append("study_batch = ?")
            params.append(batch)
        elif "data_json" in columns:
            clauses.append("data_json LIKE ?")
            params.append(f'%"study_batch":"{batch}"%')
    where = " AND ".join(clauses)
    total = int(conn.execute(f"SELECT COUNT(*) AS count FROM {spec.table} WHERE {where}", tuple(params)).fetchone()["count"])
    offset = (page - 1) * page_size
    rows = rows_to_dicts(conn.execute(
        f"SELECT {', '.join(fields)} FROM {spec.table} WHERE {where} ORDER BY created_at DESC, id DESC LIMIT ? OFFSET ?",
        tuple([*params, page_size, offset]),
    ).fetchall())
    return _page_payload(module_key, spec.label, _normalize_rows(rows, spec.json_fields), total, page, page_size, spec.sensitive)


def _timeline(conn, user_id: str, *, page: int, page_size: int, date_from: str, date_to: str, item_type: str) -> dict:
    events = []
    for key, spec in MODULE_SPECS.items():
        if item_type and key != item_type:
            continue
        if not _table_exists(conn, spec.table):
            continue
        columns = _table_columns(conn, spec.table)
        if not {"id", "user_id", "created_at"}.issubset(columns):
            continue
        clauses = ["user_id = ?"]
        params: list[object] = [user_id]
        if spec.fixed_where:
            clauses.append(spec.fixed_where)
            params.extend(spec.fixed_params)
        if date_from:
            clauses.append("created_at >= ?")
            params.append(date_from)
        if date_to:
            clauses.append("created_at <= ?")
            params.append(date_to)
        rows = conn.execute(
            f"SELECT id, created_at FROM {spec.table} WHERE {' AND '.join(clauses)} ORDER BY created_at DESC LIMIT 500",
            tuple(params),
        ).fetchall()
        events.extend({"id": row["id"], "module": key, "module_label": spec.label, "created_at": row["created_at"]} for row in rows)
    events.sort(key=lambda item: (str(item.get("created_at") or ""), str(item.get("id") or "")), reverse=True)
    total = len(events)
    offset = (page - 1) * page_size
    return _page_payload("timeline", "时间线", events[offset:offset + page_size], total, page, page_size, False)


def _page_payload(module_key: str, label: str, items: list[dict], total: int, page: int, page_size: int, sensitive: bool) -> dict:
    return {
        "module": module_key,
        "module_label": label,
        "items": items,
        "count": len(items),
        "total": total,
        "page": page,
        "page_size": page_size,
        "has_more": (page - 1) * page_size + len(items) < total,
        "sensitive": sensitive,
        "timezone": "Asia/Shanghai",
    }
