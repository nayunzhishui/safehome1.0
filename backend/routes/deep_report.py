"""B4 深度报告。

见 docs/11_商业化开发/开发框架.md 第 6 节。骨架：实现前返回 501。

实现时加上的规则：
- 生产环境（APP_ENV=production）在 COMMERCE_ENABLED 打开之前，三个接口都返回 404；
- POST 没有权益时返回 403，code 为 entitlement_required；
- 同一天重复 POST，返回当天已经生成的快照。
"""

from flask import Blueprint

from routes.auth_utils import AuthError, auth_error_response, require_login
from routes.utils import fail

bp = Blueprint("deep_report", __name__, url_prefix="/api/deep-report")


def _login_error():
    try:
        require_login(allow_legacy_admin=False)
    except AuthError as exc:
        return auth_error_response(exc)
    return None


@bp.get("/preview")
def get_preview():
    """能不能生成、能生成哪几节、有没有权益。返回结构见 deep_report_service.build_preview。"""
    error = _login_error()
    if error is not None:
        return error
    return fail("not_implemented", "B4 深度报告预览尚未实现", status=501)


@bp.post("")
def generate_report():
    """生成，或返回当天已有的快照。快照结构见开发框架第 6.3 节。"""
    error = _login_error()
    if error is not None:
        return error
    return fail("not_implemented", "B4 深度报告生成尚未实现", status=501)


@bp.get("/latest")
def get_latest_report():
    """最近一份快照；没有时返回 data 为 null。"""
    error = _login_error()
    if error is not None:
        return error
    return fail("not_implemented", "B4 最近一份深度报告尚未实现", status=501)
