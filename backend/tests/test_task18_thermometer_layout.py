import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_supplemental_observation_values_are_outside_slider_tracks():
    wxml = (ROOT / "apps/miniprogram/pages/thermometer/index.wxml").read_text(encoding="utf-8")

    assert wxml.count('class="micro-value"') == 3
    assert wxml.count('class="micro-slider"') == 3
    rows_with_value_before_slider = re.findall(
        r'<view class="micro-row">\s*'
        r'<view class="micro-heading">.*?class="micro-value".*?</view>\s*'
        r'<slider class="micro-slider"',
        wxml,
        flags=re.DOTALL,
    )
    assert len(rows_with_value_before_slider) == 3


def test_thermometer_clamps_all_four_observation_values_and_blocks_double_save():
    js = (ROOT / "apps/miniprogram/pages/thermometer/index.js").read_text(encoding="utf-8")
    wxml = (ROOT / "apps/miniprogram/pages/thermometer/index.wxml").read_text(encoding="utf-8")

    assert js.count("this.clampIntensity(event.detail.value)") == 3
    assert 'disabled="{{saving}}"' in wxml
