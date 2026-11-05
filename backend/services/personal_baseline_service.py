"""B3 个人基线：参照物是她自己，不提供常模。

见 docs/11_商业化开发/开发框架.md 第 5 节。只用温度计记录（emotion_thermometer.intensity_level），日期按北京时间。
"""

from __future__ import annotations

WINDOW_DAYS = 28
MIN_DAYS_SINCE_FIRST = 14
MIN_RECORDS = 6
TIMEZONE = "Asia/Shanghai"


def build_personal_baseline(user_id: str, today: str | None = None) -> dict:
    """返回两种形状之一：

    {"available": True, "window_days": 28, "record_count": 12, "median": 5, "q1": 4, "q3": 7}
    {"available": False, "need_days": 5, "need_records": 2}

    条件：第一条温度计记录距今满 14 天，并且近 28 天至少 6 条。today 只给测试用（YYYY-MM-DD）。
    """
    raise NotImplementedError("B3-后端")
