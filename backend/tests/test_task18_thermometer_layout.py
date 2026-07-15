from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_supplemental_observation_values_are_outside_slider_tracks():
    wxml = (ROOT / "apps/miniprogram/pages/thermometer/index.wxml").read_text(encoding="utf-8")
    wxss = (ROOT / "apps/miniprogram/pages/thermometer/index.wxss").read_text(encoding="utf-8")

    assert wxml.count('class="micro-value"') == 3
    assert wxml.count('class="micro-slider"') == 3
    assert "grid-template-columns: minmax(0, 1fr) auto" in wxss
    assert "grid-column: 1 / -1" in wxss
    assert ".micro-value" in wxss


def test_thermometer_clamps_all_four_observation_values_and_blocks_double_save():
    js = (ROOT / "apps/miniprogram/pages/thermometer/index.js").read_text(encoding="utf-8")
    wxml = (ROOT / "apps/miniprogram/pages/thermometer/index.wxml").read_text(encoding="utf-8")

    assert js.count("this.clampIntensity(event.detail.value)") == 3
    assert 'disabled="{{saving}}"' in wxml
