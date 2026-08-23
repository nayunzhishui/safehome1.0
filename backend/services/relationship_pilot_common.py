"""Shared domain helpers for the relationship-pilot modules."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from database import json_loads, load_content_json, now_iso, row_to_dict, write_audit_log


RELATIONSHIP_WORKSHEET_IDS = {
    "regulatory_focus_relationship_18",
    "micro_ysq_relationship_18",
    "relationship_initiation_intention_action",
}
SENTENCE_CONTEXTS = {"表白", "争吵", "冷战", "靠近", "边界表达", "被拒绝", "真实表达"}
REPORT_VERSION = "2026.07-relationship-screening-v1"
BOUNDARY = "本报告用于关系体验的阶段性自我观察、访谈准备和项目任务选择，不构成诊断、筛查、人格标签、关系能力评价或疗效证明。"
RESEARCH_ROLES = {"researcher", "admin", "supervisor"}


@dataclass(frozen=True)
class ServiceResult:
    data: Any
    status: int = 200


class RelationshipPilotError(Exception):
    def __init__(self, code: str, message: str, status: int = 400, details: dict | None = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status = status
        self.details = details or {}


def worksheet(worksheet_id: str) -> dict | None:
    for item in load_content_json("assessment_worksheets.json").get("worksheets", []):
        if item.get("id") == worksheet_id:
            return item
    return None


def expand_enrollment(item: dict) -> dict:
    item["dimensions"] = json_loads(item.get("dimensions_json"), [])
    item["radar_features"] = json_loads(item.get("radar_features_json"), [])
    item["profile"] = json_loads(item.get("profile_json"), {})
    return item


def expand_report(item: dict) -> dict:
    item["report"] = json_loads(item.get("report_json"), {})
    return item


def expand_task(item: dict, include_sensitive: bool = True) -> dict:
    item["drawing_data"] = json_loads(item.get("drawing_data_json"), {}) if include_sensitive else {}
    item["answers"] = json_loads(item.get("answers_json"), {}) if include_sensitive else {}
    return item


def minimize_claimable_enrollment(item: dict) -> dict:
    """Return queue metadata without profile, report or task material."""

    minimized = {
        key: item.get(key)
        for key in ("id", "nickname", "status", "review_status", "created_at", "updated_at")
        if key in item
    }
    return {
        **minimized,
        "scope_status": "claimable",
        "profile": {},
        "dimensions": [],
        "radar_features": [],
    }


def own_or_researcher(actor: dict, user_id: str) -> bool:
    return actor.get("role") in RESEARCH_ROLES or str(actor.get("id")) == str(user_id)


def enrollment_by_id(conn, enrollment_id: str) -> dict | None:
    row = conn.execute("SELECT * FROM relationship_pilot_enrollments WHERE id = ?", (enrollment_id,)).fetchone()
    return row_to_dict(row)


def ensure_researcher_assignment(conn, actor: dict, enrollment: dict) -> dict:
    """Require an explicit assignment for cross-participant research writes."""

    if actor.get("role") == "admin":
        return enrollment
    if actor.get("role") not in {"researcher", "supervisor"}:
        return enrollment
    ensure_researcher_access(actor, enrollment, conn=conn)
    return enrollment


def ensure_researcher_access(actor: dict, enrollment: dict, *, conn=None) -> None:
    if actor.get("role") not in RESEARCH_ROLES:
        return
    from services.research_access_service import ResearchAccessError, require_object_scope

    try:
        if conn is not None:
            require_object_scope(conn, actor, enrollment, "research.participant.read")
            return
        from database import get_connection

        with get_connection() as access_conn:
            require_object_scope(access_conn, actor, enrollment, "research.participant.read")
    except ResearchAccessError as exc:
        raise RelationshipPilotError(exc.code, exc.message, exc.status, exc.details) from exc


def dimension_lookup(dimensions: list[dict]) -> dict[str, float]:
    result = {}
    for row in dimensions:
        key = row.get("key") or row.get("code")
        score = row.get("score")
        if key and isinstance(score, (int, float)):
            result[str(key)] = float(score)
    return result


def four_layer_profile(enrollment: dict, rounds_count: int = 1, changes: list[dict] | None = None) -> dict:
    expanded = expand_enrollment(dict(enrollment))
    dimensions = dimension_lookup(expanded["dimensions"])
    profile_name = expanded["profile"].get("profile_name") or "阶段性关系探索位置"
    tensions = []
    if "BI" in dimensions and "RAP" in dimensions and dimensions["BI"] - dimensions["RAP"] >= 0.5:
        tensions.append("行动意愿高于近期实际尝试，可能适合讨论怎样把意愿拆成更小行动。")
    if "THREAT" in dimensions and "BENEFIT" in dimensions and dimensions["THREAT"] > dimensions["BENEFIT"]:
        tensions.append("担心线索与靠近期待同时存在，可能需要兼顾安全感与探索节奏。")
    if not tensions:
        tensions.append("本次未发现需要突出命名的分数张力，仍可结合现实事件继续观察。")
    mechanisms = []
    if "PBC" in dimensions:
        mechanisms.append("行动可控感可能影响把关系意愿转为实际尝试；这只是访谈假设，需要由用户经验核对。")
    if "EMS_M" in dimensions:
        mechanisms.append("关系担心线索可能与安全感和行动节奏有关；不能据此推断人格或因果。")
    if not mechanisms:
        mechanisms.append("当前机制线索不足，不自动推断深层原因。")
    return {
        "basic": {"stage_name": profile_name, "dimensions": expanded["dimensions"], "description": "基础画像描述本次群体相对位置和核心维度。"},
        "tension": {"clues": tensions, "status": "exploratory"},
        "mechanism": {"hypotheses": mechanisms, "status": "requires_user_and_researcher_review"},
        "dynamic": {"rounds_count": rounds_count, "changes": changes or [], "description": "动态画像只记录多次变化，不构成疗效证明。"},
    }


def public_report_payload(item: dict) -> dict:
    report = item.get("report") or {}
    return {
        "title": report.get("title"),
        "status": item.get("status"),
        "version": report.get("version") or item.get("version"),
        "generated_at": report.get("generated_at"),
        "confirmed_at": item.get("confirmed_at"),
        "sent_at": item.get("sent_at"),
        "profile_name": report.get("profile_name"),
        "profile_description": report.get("profile_description"),
        "confidence": report.get("confidence"),
        "interpretation_status": report.get("interpretation_status"),
        "dimensions": report.get("dimensions", []),
        "personalized_interpretation": report.get("personalized_interpretation"),
        "suggested_assessment_questions": report.get("suggested_assessment_questions", []),
        "recommended_project_tasks": report.get("recommended_project_tasks", []),
        "four_layer_profile": report.get("four_layer_profile", {}),
        "boundary_notice": report.get("boundary_notice") or BOUNDARY,
    }
