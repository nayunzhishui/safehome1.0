"""B3 个人基线、D1 本周同场景记录人数。

见 docs/11_商业化开发/开发框架.md 第 5、9 节。骨架：实现前返回 501。
"""

from flask import Blueprint

from routes.auth_utils import AuthError, auth_error_response, require_login
from routes.utils import fail

bp = Blueprint("insights", __name__, url_prefix="/api/insights")


def _login_error():
    try:
        require_login(allow_legacy_admin=False)
    except AuthError as exc:
        return auth_error_response(exc)
    return None


@bp.get("/baseline")
def get_personal_baseline():
    """个人基线。返回结构见 personal_baseline_service.build_personal_baseline。"""
    error = _login_error()
    if error is not None:
        return error
    # TODO(B3-后端): actor = require_login(...); return ok(build_personal_baseline(actor["id"]))
    return fail("not_implemented", "B3 个人基线尚未实现", status=501)


@bp.get("/peer-scene-counts")
def get_peer_scene_counts():
    """本周各场景记录人数。参数 week=YYYY-MM-DD（北京时间的周一），缺省为本周；N 小于 10 的场景不返回。"""
    error = _login_error()
    if error is not None:
        return error
    # TODO(D1-后端): return ok(count_peers_by_scene(request.args.get("week")))
    return fail("not_implemented", "D1 同场景人数尚未实现", status=501)
