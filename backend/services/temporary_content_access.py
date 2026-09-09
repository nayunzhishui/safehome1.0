"""Owner-controlled temporary content access; never changes approval records."""
from flask import current_app, g, has_request_context
FLAGS = {
    "assessments": "TEMPORARY_ASSESSMENTS_OPEN",
    "training_cards": "TEMPORARY_TRAINING_CARDS_OPEN",
    "programs": "TEMPORARY_PROGRAMS_OPEN",
}
NOTICE = "临时开放：本内容仍在逐项核对，不代表版权、专业或伦理审核已完成；仅供自我观察，不用于诊断或治疗。"

def temporary_content_open(kind: str) -> bool:
    if not has_request_context() or current_app.config.get("APP_ENV") != "production":
        return False
    if not current_app.config.get(FLAGS[kind], False):
        return False
    from routes.auth_utils import AuthError, get_current_actor
    if not hasattr(g, "temporary_content_logged_in"):
        try:
            g.temporary_content_logged_in = get_current_actor(allow_legacy_admin=False) is not None
        except AuthError:
            g.temporary_content_logged_in = False
    return g.temporary_content_logged_in

def boundary_with_temporary_notice(kind: str, text: str | None) -> str:
    return (NOTICE + "\n" + (text or "")) if temporary_content_open(kind) else (text or "")
