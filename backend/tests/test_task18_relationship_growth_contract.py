from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_relationship_growth_page_guards_recording_without_enrollment():
    js = (ROOT / "apps/miniprogram/pages/relationship-growth/index.js").read_text(encoding="utf-8")
    wxml = (ROOT / "apps/miniprogram/pages/relationship-growth/index.wxml").read_text(encoding="utf-8")

    assert "growth.latest_enrollment_id" in js
    assert "requireEnrollment()" in js
    assert "if (this.data.savingWeekly || !this.requireEnrollment()) return;" in js
    assert "if (!this.requireEnrollment()) return;" in js
    assert 'wx:if="{{!canRecord}}"' in wxml
    assert 'bindtap="goRelationshipPilot"' in wxml


def test_relationship_growth_page_displays_slider_values_outside_tracks():
    wxml = (ROOT / "apps/miniprogram/pages/relationship-growth/index.wxml").read_text(encoding="utf-8")
    wxss = (ROOT / "apps/miniprogram/pages/relationship-growth/index.wxss").read_text(encoding="utf-8")

    assert wxml.count('class="value-badge"') == 2
    assert ".slider-heading" in wxss
    assert ".value-badge" in wxss


def test_relationship_growth_page_uses_progressive_disclosure_and_supportive_copy():
    js = (ROOT / "apps/miniprogram/pages/relationship-growth/index.js").read_text(encoding="utf-8")
    wxml = (ROOT / "apps/miniprogram/pages/relationship-growth/index.wxml").read_text(encoding="utf-8")
    wxss = (ROOT / "apps/miniprogram/pages/relationship-growth/index.wxss").read_text(encoding="utf-8")

    for section in ["变化曲线", "成长时间线", "阶段反馈", "补充记录"]:
        assert section in js or section in wxml
    assert 'activeSection: "curve"' in js
    assert 'bindtap="toggleRecordPanel"' in wxml
    assert 'bindtap="openRecordSection"' in wxml
    assert "持续记录，帮助你看见同一指标在不同时间的变化" in wxml
    assert "不合并成总分" in wxml
    assert "section-nav__item--active" in wxss


def test_relationship_growth_page_matches_dashboard_visual_hierarchy():
    js = (ROOT / "apps/miniprogram/pages/relationship-growth/index.js").read_text(encoding="utf-8")
    wxml = (ROOT / "apps/miniprogram/pages/relationship-growth/index.wxml").read_text(encoding="utf-8")
    wxss = (ROOT / "apps/miniprogram/pages/relationship-growth/index.wxss").read_text(encoding="utf-8")
    config = (ROOT / "apps/miniprogram/pages/relationship-growth/index.json").read_text(encoding="utf-8")

    assert wxml.count('class="growth-summary-item"') == 3
    for label in ["累计记录", "指标组", "阶段性反馈"]:
        assert label in wxml
    assert 'role="tablist"' in wxml
    assert 'role="tab"' in wxml
    assert 'aria-selected="{{activeSection === item.key}}"' in wxml
    assert 'wx:if="{{selectedPoints.length >= 2}}" canvas-id="growthChart"' in wxml
    assert "这里不会根据单次记录判断变化" in wxml
    assert "position: sticky" in wxss
    assert "font-variant-numeric: tabular-nums" in wxss
    assert "if (points.length >= 2) this.drawChart" in js
    assert '"navigationBarTitleText": "关系探索成长记录"' in config
