"""Admin/researcher read-only text-analysis summaries."""

from flask import Blueprint

from routes.auth_utils import AuthError, auth_error_response, require_role
from routes.utils import ok
from services.text_analysis_service import load_text_analysis_summary


bp = Blueprint("text_analysis", __name__, url_prefix="/api/text-analysis")


@bp.get("/summary")
def text_analysis_summary():
    try:
        actor = require_role("admin", "researcher", allow_legacy_admin=True)
    except AuthError as exc:
        return auth_error_response(exc)
    payload = load_text_analysis_summary()
    return ok(
        {
            "items": payload,
            "actor_id": actor["id"],
            "raw_text_included": False,
            "boundary_notice": "文本分析报告只读取离线聚合结果，不返回原始自由文本；仅供管理员或研究者查看。",
        }
    )
