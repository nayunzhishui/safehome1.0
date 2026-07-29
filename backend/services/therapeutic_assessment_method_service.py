"""Controlled method-library access for Task38-F17."""

from __future__ import annotations

import json
from datetime import date

from flask import current_app

from database import get_connection, write_audit_log
from services.therapeutic_assessment_service import TherapeuticAssessmentError


FORMAL_ROLES = {"researcher", "supervisor", "admin"}
PROFESSIONAL_ROLES = {"supervisor", "admin"}
PUBLIC_FIELDS = (
    "id",
    "title",
    "artifact_type",
    "version",
    "applicable_levels",
    "review_status",
    "valid_from",
    "expires_at",
    "access_tier",
    "ordinary_recommendation",
)


def _load_library() -> dict:
    path = (
        current_app.config["CONTENT_DIR"]
        / "therapeutic_assessment_method_library.json"
    )
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise TherapeuticAssessmentError(
            "method_library_unavailable",
            "方法内容库暂时不可用",
            503,
        ) from exc
    if (
        payload.get("schema")
        != "safehome.therapeutic-assessment.method-library.v1"
        or not isinstance(payload.get("items"), list)
    ):
        raise TherapeuticAssessmentError(
            "method_library_invalid",
            "方法内容库版本不兼容",
            503,
        )
    return payload


def _audit(actor: dict, action: str, target_id: str, details: dict) -> None:
    with get_connection() as conn:
        write_audit_log(
            conn,
            action,
            actor["id"],
            "therapeutic_method",
            target_id,
            details,
        )
        conn.commit()


def public_catalog(actor: dict) -> dict:
    payload = _load_library()
    items = [
        {field: item.get(field) for field in PUBLIC_FIELDS}
        for item in payload["items"]
    ]
    _audit(
        actor,
        "therapeutic_method_catalog_viewed",
        "all",
        {"count": len(items), "bodies_exposed": False},
    )
    return {
        "schema": payload["schema"],
        "version": payload.get("version"),
        "count": len(items),
        "items": items,
        "automatic_release_allowed": False,
        "boundary": (
            "目录只说明受控材料及其边界，不提供专业模板正文，"
            "也不构成诊断、测验解释或普通训练推荐。"
        ),
    }


def get_method(actor: dict, item_id: str) -> dict:
    role = str(actor.get("role") or "")
    if role not in FORMAL_ROLES:
        raise TherapeuticAssessmentError(
            "method_library_forbidden",
            "当前账号不能查看方法正文",
            403,
        )
    payload = _load_library()
    item = next(
        (entry for entry in payload["items"] if entry.get("id") == item_id),
        None,
    )
    if item is None:
        raise TherapeuticAssessmentError(
            "method_not_found",
            "未找到对应方法内容",
            404,
        )
    if item.get("access_tier") == "t3_professional" and role not in PROFESSIONAL_ROLES:
        raise TherapeuticAssessmentError(
            "professional_method_forbidden",
            "该材料仅供受控专业工作和督导使用",
            403,
        )
    expires_at = str(item.get("expires_at") or "")
    if expires_at and expires_at < date.today().isoformat():
        raise TherapeuticAssessmentError(
            "method_content_expired",
            "该方法内容已过有效期，等待重新审核",
            409,
        )
    _audit(
        actor,
        "therapeutic_method_viewed",
        item_id,
        {
            "version": item.get("version"),
            "access_tier": item.get("access_tier"),
            "review_status": item.get("review_status"),
        },
    )
    return {
        **item,
        "automatic_release_allowed": False,
        "publication_status": "human_review_required",
    }
