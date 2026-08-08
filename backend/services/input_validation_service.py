"""Central input-boundary helpers for participant-facing write APIs.

The project previously validated required fields but many free-text fields had
no consistent maximum length.  This module keeps validation deterministic and
small so routes can fail before DB writes, risk analysis, or downstream model
processing.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FieldLimit:
    maximum: int
    minimum: int = 0


TEXT_LIMITS = {
    "scene": FieldLimit(120, 1),
    "event_description": FieldLimit(4000, 1),
    "parent_emotion": FieldLimit(80, 1),
    "child_emotion": FieldLimit(80),
    "automatic_thought": FieldLimit(2000),
    "body_sensation": FieldLimit(1000),
    "behavior": FieldLimit(2000),
    "raw_text": FieldLimit(5000),
    "supervision_message": FieldLimit(5000, 1),
    "supervision_contact": FieldLimit(256),
    "risk_hint": FieldLimit(1000),
    "supervisor_reply": FieldLimit(5000, 1),
    "review_note": FieldLimit(5000),
    "action_taken": FieldLimit(1000),
    "closed_reason": FieldLimit(1000),
}


class InputValidationError(ValueError):
    def __init__(self, field: str, message: str, code: str = "validation_error") -> None:
        super().__init__(message)
        self.field = field
        self.message = message
        self.code = code


def bounded_text(
    value,
    field: str,
    *,
    limit_key: str | None = None,
    allow_none: bool = True,
    strip: bool = True,
) -> str | None:
    if value is None:
        if allow_none:
            return None
        raise InputValidationError(field, f"{field} 不能为空")
    text = str(value)
    if strip:
        text = text.strip()
    limit = TEXT_LIMITS.get(limit_key or field)
    if limit:
        if len(text) < limit.minimum:
            raise InputValidationError(field, f"{field} 内容不能为空")
        if len(text) > limit.maximum:
            raise InputValidationError(field, f"{field} 最多允许 {limit.maximum} 个字符")
    return text


def bounded_int(value, field: str, *, minimum: int, maximum: int, default: int | None = None) -> int | None:
    if value in (None, ""):
        return default
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise InputValidationError(field, f"{field} 必须是整数") from exc
    if parsed < minimum or parsed > maximum:
        raise InputValidationError(field, f"{field} 必须在 {minimum} 到 {maximum} 之间")
    return parsed


def validate_diary_payload(payload: dict) -> dict:
    """Return a normalized copy of one emotion-diary payload."""
    result = dict(payload)
    result["scene"] = bounded_text(payload.get("scene"), "scene", allow_none=False)
    result["event_description"] = bounded_text(
        payload.get("event_description"), "event_description", allow_none=False
    )
    result["parent_emotion"] = bounded_text(
        payload.get("parent_emotion"), "parent_emotion", allow_none=False
    )
    for field in ("child_emotion", "automatic_thought", "body_sensation", "behavior", "raw_text"):
        result[field] = bounded_text(payload.get(field), field)
    result["parent_emotion_intensity"] = bounded_int(
        payload.get("parent_emotion_intensity"),
        "parent_emotion_intensity",
        minimum=0,
        maximum=10,
        default=5,
    )
    result["child_emotion_intensity"] = bounded_int(
        payload.get("child_emotion_intensity"),
        "child_emotion_intensity",
        minimum=0,
        maximum=10,
        default=None,
    )
    return result


def validate_supervision_payload(payload: dict) -> dict:
    result = dict(payload)
    result["message"] = bounded_text(
        payload.get("message"), "message", limit_key="supervision_message", allow_none=False
    )
    result["contact"] = bounded_text(payload.get("contact"), "contact", limit_key="supervision_contact")
    result["risk_hint"] = bounded_text(payload.get("risk_hint"), "risk_hint")
    if payload.get("source_title") is not None:
        result["source_title"] = str(payload.get("source_title") or "").strip()[:120]
    return result


def validate_review_fields(payload: dict) -> dict:
    result = dict(payload)
    for field in ("review_note", "action_taken", "closed_reason"):
        result[field] = bounded_text(payload.get(field), field)
    return result
