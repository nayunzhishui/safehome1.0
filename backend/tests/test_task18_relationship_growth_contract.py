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
    assert "变化记录，不是疗效证明" in wxml
    assert "不合并成总分" in wxml
    assert "section-nav__item--active" in wxss
