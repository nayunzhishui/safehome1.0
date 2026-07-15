"""Public status endpoint for the reversible supervised showcase switch."""

from flask import Blueprint

from routes.utils import ok
from services.showcase_access_service import load_showcase_access


bp = Blueprint("showcase_access", __name__, url_prefix="/api/showcase-access")


@bp.get("")
def get_showcase_access():
    payload = load_showcase_access()
    return ok(
        {
            "enabled": bool(payload.get("enabled")),
            "read_only_role_bypass": bool(payload.get("read_only_role_bypass")),
            "open_programs": bool(payload.get("open_programs")),
            "allow_program_participation": bool(payload.get("allow_program_participation")),
            "open_training_cards": bool(payload.get("open_training_cards")),
            "open_courses": bool(payload.get("open_courses")),
            "notice": payload.get("notice") or "展示模式未开启。",
            "version": payload.get("version"),
        }
    )
