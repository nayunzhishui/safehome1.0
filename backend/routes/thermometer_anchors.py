"""B2 温度计刻度说明。

见 docs/11_商业化开发/开发框架.md 第 4 节。骨架：实现前返回 501。
"""

from flask import Blueprint

from routes.auth_utils import AuthError, auth_error_response, require_login
from routes.utils import fail

bp = Blueprint("thermometer_anchors", __name__, url_prefix="/api/thermometer-anchors")


@bp.get("")
def get_anchors():
    """不要求登录。返回 {"version", "bands": [{"min", "max", "label"}], "mine": [...]}，没登录时 mine 为空列表。

    判断有没有登录可以用 routes.auth_utils.get_current_actor（实现时核对它在未登录时的返回）。
    """
    # TODO(B2-后端): load_default_anchors()；登录时再加 get_user_anchors(user_id)
    return fail("not_implemented", "B2 温度计刻度说明尚未实现", status=501)


@bp.put("/me")
def save_my_anchors():
    """保存她自己写的刻度。请求体 {"anchors": [{"level": 8, "text": "..."}]}。"""
    try:
        require_login(allow_legacy_admin=False)
    except AuthError as exc:
        return auth_error_response(exc)
    # TODO(B2-后端): 校验后调用 save_user_anchors(actor["id"], payload["anchors"])
    return fail("not_implemented", "B2 保存自己的刻度尚未实现", status=501)
