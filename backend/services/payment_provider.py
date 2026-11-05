"""B5 支付方式。订单逻辑只依赖 PaymentProvider，换支付方式不用改订单代码。

见 docs/11_商业化开发/开发框架.md 第 7.1、7.2 节。
"""

from __future__ import annotations


class PaymentProvider:
    name = "base"

    def create_payment(self, order: dict) -> dict:
        """返回前端调起支付需要的参数。"""
        raise NotImplementedError

    def verify_notification(self, headers: dict, body: bytes) -> dict:
        """验签并解析支付通知，返回 {"out_trade_no", "provider_txn_id", "paid": bool}；验签失败抛 ValueError。"""
        raise NotImplementedError

    def query(self, out_trade_no: str) -> dict:
        raise NotImplementedError

    def refund(self, order: dict, reason: str) -> dict:
        raise NotImplementedError


class MockPaymentProvider(PaymentProvider):
    """测试环境用。create_payment 返回 {"provider": "mock"}；支付成功由 POST /api/commerce/mock/pay 触发。"""

    name = "mock"
    # TODO(B5-后端(2)): 实现四个方法


class WechatVirtualPaymentProvider(PaymentProvider):
    """小程序虚拟支付。主体迁移、虚拟支付开通、session_key 问题解决之后再实现（B5-后端(3)）。

    开通时逐项以官方文档核对：
    - signData：offerId、buyQuantity、env、currencyType、productId、goodsPrice、outTradeNo、attach；
    - paySig：AppKey 对 "requestVirtualPayment&" 加 signData 做 HMAC-SHA256；
    - signature：用户的 session_key 对 signData 签名；
    - mode："short_series_goods"；
    - 发货通知走小程序消息推送。
    AppKey 和 session_key 只从环境变量和登录态取，不写进代码、日志和审计。
    """

    name = "wechat_virtual"


def get_provider(app_env: str) -> PaymentProvider:
    """非生产环境返回 MockPaymentProvider；生产环境在 B5-后端(3) 完成前抛错。"""
    raise NotImplementedError("B5-后端(2)")
