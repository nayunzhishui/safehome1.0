"""D1 本周记过同一场景的人数（“本周有 N 位妈妈也记了作业”）。

见 docs/11_商业化开发/开发框架.md 第 9 节。
"""

from __future__ import annotations

MIN_N = 10
CACHE_SECONDS = 3600
TIMEZONE = "Asia/Shanghai"


def count_peers_by_scene(week_start: str | None = None) -> dict:
    """返回 {"week_start", "min_n": 10, "items": [{"scene", "n"}]}，n 小于 MIN_N 的场景不返回。

    北京时间周一到周日；请求时现算，进程内缓存 CACHE_SECONDS 秒；不建新表。
    """
    raise NotImplementedError("D1-后端")
