"""Central reversible access switch for supervised project demonstrations."""

from __future__ import annotations

from flask import current_app, g, request

from database import get_connection, load_content_json, write_audit_log


DEFAULTS = {
    "enabled": False,
    "read_only_role_bypass": False,
    "researcher_platform_full_access": False,
    "open_programs": False,
    "allow_program_participation": False,
    "open_training_cards": False,
    "open_courses": False,
    "allowed_profiles": ["development", "testing", "validation"],
}


def load_showcase_access() -> dict:
    try:
        payload = load_content_json("showcase_access.json")
    except (FileNotFoundError, OSError, ValueError):
        payload = {}
    merged = {**DEFAULTS, **payload}
    profile = str(current_app.config.get("APP_ENV") or "development").strip().lower()
    allowed_profiles = {str(item).strip().lower() for item in merged.get("allowed_profiles") or []}
    if profile not in allowed_profiles:
        return {
            **merged,
            **{key: False for key in DEFAULTS if key != "allowed_profiles"},
            "notice": "Showcase 在当前环境不可用；正式角色与权限保持不变。",
            "effective_profile": profile,
            "blocked_by_profile": True,
        }
    return {**merged, "effective_profile": profile, "blocked_by_profile": False}


def allow_showcase_read_bypass() -> bool:
    payload = load_showcase_access()
    return bool(payload.get("enabled") and payload.get("read_only_role_bypass"))


def allow_showcase_researcher_platform_full_access() -> bool:
    """Allow any signed-in account to exercise researcher-platform flows.

    This is a reversible development-only gate. It does not open unrelated
    administrative, export, account-management, or content-publishing APIs.
    """

    payload = load_showcase_access()
    return bool(payload.get("enabled") and payload.get("researcher_platform_full_access"))


def record_showcase_elevation_decision(actor: dict, *, allowed: bool) -> None:
    """Audit the one real temporary-role decision made by F05."""
    with get_connection() as conn:
        write_audit_log(
            conn,
            "showcase_elevation_granted" if allowed else "showcase_elevation_blocked",
            actor_id=str(actor.get("id") or "") or None,
            target_type="showcase_access",
            target_id=request.path,
            metadata={
                "actor_role": str(actor.get("role") or ""),
                "method": request.method,
                "request_id": str(getattr(g, "request_id", "") or request.headers.get("X-Request-ID") or "unknown"),
                "effective_profile": str(current_app.config.get("APP_ENV") or "development"),
            },
        )
        conn.commit()


def showcase_programs_open() -> bool:
    payload = load_showcase_access()
    return bool(payload.get("enabled") and payload.get("open_programs"))


def allow_showcase_program_participation() -> bool:
    payload = load_showcase_access()
    return bool(payload.get("enabled") and payload.get("allow_program_participation"))


def showcase_training_cards_open() -> bool:
    payload = load_showcase_access()
    return bool(payload.get("enabled") and payload.get("open_training_cards"))


def showcase_courses_open() -> bool:
    payload = load_showcase_access()
    return bool(payload.get("enabled") and payload.get("open_courses"))
