"""B5 订单和权益。

见 docs/11_商业化开发/开发框架.md 第 7 节。
- 金额只认 content/commerce_skus.json，前端传来的金额一律忽略；
- 订单状态只允许 ALLOWED_TRANSITIONS 里的转换，每次转换写审计 commerce_order_<状态>；
- 支付通知按 out_trade_no 调 reserve_idempotency 防重复，重复通知不重复发货；
- 发货就是写 entitlements，退款把对应权益改成 revoked。
"""

from __future__ import annotations

SKUS_FILE = "commerce_skus.json"
ORDER_STATUSES = ("created", "paid", "delivered", "refunded", "closed")
ALLOWED_TRANSITIONS = {
    "created": {"paid", "closed"},
    "paid": {"delivered", "refunded"},
    "delivered": {"refunded"},
}
ENTITLEMENT_TYPES = ("deep_report", "four_week_plan", "full_courses")
ORDER_TIMEOUT_MINUTES = 30
NOTIFY_IDEMPOTENCY_ENDPOINT = "commerce_notify"


class CommerceError(ValueError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


def load_skus(include_off_sale: bool = False) -> list[dict]:
    raise NotImplementedError("B5-后端(2)")


def create_order(user_id: str, sku_id: str, platform: str, provider) -> dict:
    """建单（created），返回 {"order_id", "status", "payment": provider.create_payment(order)}。"""
    raise NotImplementedError("B5-后端(2)")


def get_order(user_id: str, order_id: str) -> dict | None:
    raise NotImplementedError("B5-后端(2)")


def handle_payment_success(out_trade_no: str, provider_txn_id: str, raw_payload: dict) -> dict:
    """防重复 → paid → 写权益 → delivered。重复通知直接返回已有结果。raw_payload 只存摘要，不存密钥和签名原文。"""
    raise NotImplementedError("B5-后端(2)")


def refund_order(actor_id: str, order_id: str, reason: str) -> dict:
    raise NotImplementedError("B5-后端(2)")


def close_expired_orders(now: str | None = None) -> int:
    """created 超过 ORDER_TIMEOUT_MINUTES 分钟的订单改成 closed，返回条数。"""
    raise NotImplementedError("B5-后端(2)")


def get_active_entitlements(user_id: str) -> list[dict]:
    raise NotImplementedError("B5-后端(2)")


def has_entitlement(user_id: str, entitlement_type: str) -> bool:
    raise NotImplementedError("B5-后端(2)")
