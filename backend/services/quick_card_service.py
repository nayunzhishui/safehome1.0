"""B1 急救卡配置。

见 docs/11_商业化开发/开发框架.md 第 3 节。
只返回卡名、分组、时长和音频文件 ID，不返回卡片正文：正文由 GET /api/cards 提供，前端不能写死正文（第 1.6 节）。
"""

from __future__ import annotations

QUICK_CARDS_FILE = "quick_cards.json"
GROUP_KEYS = ("heat", "after")


class QuickCardConfigError(ValueError):
    """quick_cards.json 引用了不存在或未发布（不是 production_approved）的卡。"""


def load_quick_cards() -> dict:
    """读 content/quick_cards.json，按 training_cards.json 补上卡名和时长。

    返回：
    {"version": "...", "ai_notice": "...",
     "groups": [{"key": "heat", "label": "我现在很火",
                 "cards": [{"id": "three_second_pause", "title": "开口前停三秒",
                            "duration_minutes": 1, "audio_file_id": ""}]}]}
    """
    # TODO(B1-后端): 用 Config.CONTENT_DIR 读两个文件；可以按文件修改时间缓存
    raise NotImplementedError("B1-后端")
