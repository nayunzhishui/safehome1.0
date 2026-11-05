"""B5 付费（先在测试环境走通）。

见 docs/11_商业化开发/开发框架.md 第 7 节。
COMMERCE_ENABLED 关闭时，所有 /api/commerce/* 都返回 404。config.py 加上这个开关之前读到的是 None，同样按关闭处理。
骨架：开关打开后，实现前返回 501。
"""

from flask import Blueprint, current_app

from routes.auth_utils import AuthError, auth_error_response, require_login, require_role
from routes.utils import fail

bp = Blueprint("commerce", __name__, url_prefix="/api/commerce")


@bp.before_request
def _hide_when_disabled():
    if not current_app.config.get("COMMERCE_ENABLED"):
        return fail("not_found", "接口不存在", status=404)
    return None


def _login_error():
    try:
        require_login(allow_legacy_admin=False)
    except AuthError as exc:
        return auth_error_response(exc)
    return None


def _not_implemented(name: str):
    return fail("not_implemented", f"B5 {name} 尚未实现", status=501)


@bp.get("/skus")
def list_skus():
    """上架的商品。commerce_service.load_skus()。"""
    error = _login_error()
    if error is not None:
        return error
    return _not_implemented("商品清单")


@bp.post("/orders")
def create_order():
    """请求体 {"sku_id", "platform"}。金额按 commerce_skus.json 计算，前端传来的金额一律忽略。"""
    error = _login_error()
    if error is not None:
        return error
    return _not_implemented("下单")


@bp.get("/orders/<order_id>")
def get_order(order_id: str):
    """订单状态和已发放的权益；只能查自己的订单，查不到返回 404。"""
    error = _login_error()
    if error is not None:
        return error
    return _not_implemented("查询订单")


@bp.get("/entitlements/me")
def list_my_entitlements():
    """我的有效权益。commerce_service.get_active_entitlements(user_id)。"""
    error = _login_error()
    if error is not None:
        return error
    return _not_implemented("我的权益")


@bp.post("/notify/wechat-virtual")
def wechat_virtual_notify():
    """微信服务器推送的发货通知。不要求登录，靠验签（WechatVirtualPaymentProvider.verify_notification）。"""
    return _not_implemented("虚拟支付通知")


@bp.post("/mock/pay")
def mock_pay():
    """只在非生产环境可用：模拟支付成功，走 commerce_service.handle_payment_success 同一条发货逻辑。"""
    error = _login_error()
    if error is not None:
        return error
    return _not_implemented("模拟支付")


@bp.post("/orders/<order_id>/refund")
def refund_order(order_id: str):
    """只给 admin：标记退款并收回权益。"""
    try:
        require_role("admin", allow_legacy_admin=False)
    except AuthError as exc:
        return auth_error_response(exc)
    return _not_implemented("退款")
