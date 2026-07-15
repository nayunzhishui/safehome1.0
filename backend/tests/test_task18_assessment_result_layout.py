from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PAGE = ROOT / "apps" / "miniprogram" / "pages" / "assessment-result"


def test_task18_profile_charts_use_numbered_axes_and_external_legends():
    script = (PAGE / "index.js").read_text(encoding="utf-8")
    markup = (PAGE / "index.wxml").read_text(encoding="utf-8")
    styles = (PAGE / "index.wxss").read_text(encoding="utf-8")

    assert '.slice(0, 6)' in script
    assert 'label: compactFeatureLabel(dimension.label || dimension.code)' in script
    assert 'ctx.fillText(point.axisLabel || ""' in script
    assert 'ctx.fillText(item.axisLabel || String(index + 1)' in script
    assert 'ctx.fillText(point.label' not in script
    assert 'class="chart-legend cluster-legend"' in markup
    assert 'class="chart-legend radar-legend"' in markup
    assert '.position-canvas' in styles and 'height: 300rpx;' in styles
    assert '.radar-canvas' in styles and 'height: 360rpx;' in styles


def test_task18_dimension_rows_allow_long_labels_without_covering_scores():
    styles = (PAGE / "index.wxss").read_text(encoding="utf-8")

    assert '.dimension-label' in styles
    assert 'overflow-wrap: anywhere;' in styles
    assert '.dimension-score' in styles
    assert 'flex: 0 0 auto;' in styles
