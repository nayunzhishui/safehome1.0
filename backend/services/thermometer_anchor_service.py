"""B2 温度计刻度说明。

见 docs/11_商业化开发/开发框架.md 第 4 节。
默认三档来自 content/thermometer_anchors.json。她自己写的刻度存在 records 表，
module_type = "thermometer_anchor"，每人只留一条，更新时覆盖。
"""

from __future__ import annotations

ANCHORS_FILE = "thermometer_anchors.json"
RECORD_MODULE_TYPE = "thermometer_anchor"
MAX_ANCHORS = 3
MAX_TEXT_LENGTH = 40
LEVEL_MIN, LEVEL_MAX = 0, 10


class AnchorValidationError(ValueError):
    """level 不在 0–10、text 超过 40 个字，或者条数超过 3 条。"""


def load_default_anchors() -> dict:
    """返回 {"version", "bands": [{"min", "max", "label"}]}。"""
    raise NotImplementedError("B2-后端")


def get_user_anchors(user_id: str) -> list[dict]:
    """返回 [{"level": 8, "text": "..."}]；没有就返回空列表。"""
    raise NotImplementedError("B2-后端")


def save_user_anchors(user_id: str, anchors: list[dict]) -> list[dict]:
    """校验后覆盖保存；写审计 thermometer_anchor_saved，metadata 只记条数，不记文字。返回保存后的列表。"""
    raise NotImplementedError("B2-后端")
