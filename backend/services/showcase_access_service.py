"""Central reversible access switch for supervised project demonstrations."""

from __future__ import annotations

from database import load_content_json


DEFAULTS = {
    "enabled": False,
    "read_only_role_bypass": False,
    "open_programs": False,
    "allow_program_participation": False,
    "open_training_cards": False,
    "open_courses": False,
}


def load_showcase_access() -> dict:
    try:
        payload = load_content_json("showcase_access.json")
    except (FileNotFoundError, OSError, ValueError):
        payload = {}
    return {**DEFAULTS, **payload}


def showcase_enabled() -> bool:
    return bool(load_showcase_access().get("enabled"))


def allow_showcase_read_bypass() -> bool:
    payload = load_showcase_access()
    return bool(payload.get("enabled") and payload.get("read_only_role_bypass"))


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
