"""B6 内容地图。

见 docs/11_商业化开发/开发框架.md 第 8 节。
编号格式“类型:id”。card 在 training_cards.json，course 在 courses.json，worksheet 在 assessment_worksheets.json，
video、article、story 在 content_map.json 自己的条目里。
"""

from __future__ import annotations

CONTENT_MAP_FILE = "content_map.json"
CONTENT_TYPES = ("card", "course", "video", "article", "story", "worksheet")
STEPS = {1: "知道", 2: "理解", 3: "会做", 4: "一起做", 5: "个别辅导"}
SCENES = ("作业拖延", "睡前冲突", "手机使用", "出门准备", "亲子沟通", "其他")
ECO_LAYERS = ("family", "family_school", "parent_work", "wider_environment")
SOURCE_TYPES = ("real", "literature", "ai")


def parse_content_id(content_id: str) -> tuple[str, str]:
    """"card:three_second_pause" → ("card", "three_second_pause")；格式不对或类型不在 CONTENT_TYPES 里抛 ValueError。"""
    raise NotImplementedError("B6-后端")


def load_content_map() -> dict:
    raise NotImplementedError("B6-后端")


def get_next_steps(content_id: str, risk_level: str | None = None) -> list[dict]:
    """只返回已发布的条目；risk_level 为 high 时返回空列表，由页面显示求助入口。"""
    raise NotImplementedError("B6-后端")


def validate_references() -> list[str]:
    """返回问题列表：编号不存在、缺少下一步、出现绕圈。空列表表示通过。"""
    raise NotImplementedError("B6-后端")
