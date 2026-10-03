"""情绪温度计支持性回执与本地日期边界回归。"""

import pytest
import sys
from pathlib import Path


BACKEND = Path(__file__).resolve().parents[1]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))


def test_local_day_key_uses_asia_shanghai_timezone():
    from routes.emotion_thermometer import _local_day_key

    assert _local_day_key("2026-07-05T17:00:00+00:00") == "2026-07-06"
    assert _local_day_key("2026-07-06T01:00:00+08:00") == "2026-07-06"


def test_receipt_contract_is_supportive_and_non_diagnostic():
    source = (BACKEND / "routes" / "emotion_thermometer.py").read_text(encoding="utf-8")
    assert '"receipt"' in source
    assert '"practice_available": True' in source
    assert "不评价好坏" in source
    assert "疗效判断" in source


@pytest.mark.parametrize("value", [True, False, 1.9, "1.9", None, [], 0, 11])
def test_thermometer_rejects_non_integer_or_out_of_range_values(value):
    from routes.emotion_thermometer import _normalize_level
    assert _normalize_level(value) is None


@pytest.mark.parametrize("value, expected", [(1, 1), ("5", 5), (10, 10), (6.0, 6)])
def test_thermometer_preserves_valid_integer_levels(value, expected):
    from routes.emotion_thermometer import _normalize_level
    assert _normalize_level(value) == expected
