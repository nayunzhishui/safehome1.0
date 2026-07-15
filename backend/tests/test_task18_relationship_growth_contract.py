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
