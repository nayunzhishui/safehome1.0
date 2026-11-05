"""B6 内容分流：一条内容之后的“下一步”。

见 docs/11_商业化开发/开发框架.md 第 8 节。骨架：实现前返回 501。
"""

from flask import Blueprint

from routes.utils import fail

bp = Blueprint("content_map", __name__, url_prefix="/api/content-map")


@bp.get("/next-step")
def get_next_step():
    """GET /api/content-map/next-step?id=video:v001。不要求登录，只返回已发布的条目。

    页面在高风险时不调用这个接口，直接显示求助入口；接口也接受 risk_level=high，这时返回空列表。
    """
    # TODO(B6-后端): content_map_service.get_next_steps(request.args.get("id"), request.args.get("risk_level"))
    return fail("not_implemented", "B6 内容分流尚未实现", status=501)
