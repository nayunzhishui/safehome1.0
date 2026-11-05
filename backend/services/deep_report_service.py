"""B4 深度报告。

见 docs/11_商业化开发/开发框架.md 第 6 节。
原则：每一节有自己的门槛；用中位数不用平均数；不说“最有效”，只说“练完平均降了几分（几次）”；
30 天内有高风险记录时先给支持信息、不出现购买；生成一次存一份快照（records，module_type = "deep_report"），
同一天重复请求返回同一份快照。时间一律按北京时间。
"""

from __future__ import annotations

REPORT_VERSION = "deep-v1"
RECORD_MODULE_TYPE = "deep_report"
WINDOW_DAYS = 30
TIMEZONE = "Asia/Shanghai"
MIN_RECORDS_TO_SELL = 8
SMALL_CHANGE_POINTS = 1
SECTION_THRESHOLDS = {
    "scene_time": {"min_diaries": 8},
    "scene_words": {"min_diaries": 8},
    "scene_cards": {"min_practices_per_scene_card": 3},
    "worksheet_compare": {"min_results": 2, "min_days_apart": 14},
    "vs_previous": {"min_records_previous_window": 8},
}
# (key, 开始小时, 结束小时)；late_night 跨零点
TIME_SLOTS = (
    ("morning", 6, 9),
    ("daytime", 9, 17),
    ("evening", 17, 20),
    ("night", 20, 23),
    ("late_night", 23, 6),
)


def build_preview(user_id: str) -> dict:
    """返回 {"eligible", "record_count", "threshold", "sections_available": [...], "entitled", "commerce_enabled"}。"""
    raise NotImplementedError("B4-后端")


def generate_or_get_today(user_id: str) -> dict:
    """当天已有快照就直接返回；没有就调用 build_deep_report 生成，存进 records。"""
    raise NotImplementedError("B4-后端")


def get_latest(user_id: str) -> dict | None:
    raise NotImplementedError("B4-后端")


def build_deep_report(user_id: str, end_date: str | None = None) -> dict:
    """返回开发框架第 6.3 节的快照结构。end_date 只给测试用（YYYY-MM-DD）。"""
    raise NotImplementedError("B4-后端")


def _scene_time(diaries: list[dict]) -> dict:
    """场景 × 时段。时段按 TIME_SLOTS；用日记的 event_time，没有再用 created_at，都换成北京时间。"""
    raise NotImplementedError("B4-后端")


def _scene_words(diaries: list[dict]) -> dict:
    """每个场景最常出现的情绪词（emotion_diaries.parent_emotion）和强度中位数。"""
    raise NotImplementedError("B4-后端")


def _scene_cards(checkins: list[dict], diaries_by_id: dict[str, dict]) -> dict:
    """练习通过 checkins.diary_id 关联到日记场景；同一场景同一张卡至少 3 次才列出，给降幅中位数和次数。"""
    raise NotImplementedError("B4-后端")


def _worksheet_compare(results: list[dict]) -> dict:
    """同一 worksheet_id 最早和最近两次；能不能比用 progress_summary_service.assessments_comparable 判断。"""
    raise NotImplementedError("B4-后端")


def _vs_previous(current: list[int], previous: list[int]) -> dict:
    """只看中位数差和条数差；差值不超过 SMALL_CHANGE_POINTS 时 label 写“变化不大”。"""
    raise NotImplementedError("B4-后端")


def _own_words(diaries: list[dict]) -> dict:
    """日记里她自己写的原句，只按场景列出，不做自动归类。"""
    raise NotImplementedError("B4-后端")


def _support_first(user_id: str, start: str, end: str) -> bool:
    """窗口内有高风险记录时返回 True：第一节换成支持信息和求助入口，整份报告不出现购买引导。"""
    raise NotImplementedError("B4-后端")
