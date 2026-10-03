from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _read(relative_path: str) -> str:
    return (PROJECT_ROOT / relative_path).read_text(encoding="utf-8")


def test_today_step_and_core_entries_follow_current_home_order():
    wxml = _read("apps/miniprogram/pages/home/index.wxml")
    core_index = wxml.index('class="home-capture"')
    today_index = wxml.index("<journey-action-card")
    three_step_index = wxml.index('title="如何开始"')
    assert today_index < core_index < three_step_index
    for required_text in ["情绪温度计", "测一测", "情绪日记", "更多", "最近记录", "阶段性反馈"]:
        assert required_text in wxml


def test_home_keeps_journey_failure_distinct_from_empty_state():
    source = _read("apps/miniprogram/pages/home/index.js")
    assert "getTodayJourney" in source
    assert "todayJourneyError" in source
    assert "retryTodayJourney" in source
    assert "openTodayAction" in source
    assert "findLocalDraftAction" in source


def test_journey_endpoint_is_shared_by_clients():
    shared = _read("shared/constants/api.ts")
    miniprogram = _read("apps/miniprogram/services/api.js")
    web = _read("apps/web/src/services/safehomeApi.ts")
    assert 'journeyToday: "/api/journey/today"' in shared
    assert 'journeyToday: "/api/journey/today"' in miniprogram
    assert "getTodayJourney" in miniprogram
    assert "getTodayJourney" in web


def test_today_step_card_has_accessible_action_and_all_states():
    wxml = _read("apps/miniprogram/pages/home/index.wxml")
    component_wxml = _read("apps/miniprogram/components/journey-action-card/index.wxml")
    wxss = _read("apps/miniprogram/components/journey-action-card/index.wxss")
    source = _read("apps/miniprogram/pages/home/index.js")
    assert 'action-aria-label="{{todayJourney ? todayJourney.actionAriaLabel' in wxml
    assert 'aria-label="{{actionAriaLabel}}"' in component_wxml
    assert "min-height: var(--safe-touch, 88rpx)" in wxss
    for state in ["loading", "error", "paused", "completed", "not_due"]:
        assert state in source or state in wxml or state in component_wxml or state in wxss


def test_home_progress_fallback_actions_do_not_clip_button_labels():
    wxml = _read("apps/miniprogram/pages/home/index.wxml")
    wxss = _read("apps/miniprogram/pages/home/index.wxss")

    assert 'action-label="查看说明" expanded wrap-title bind:action="openWeeklyReport"' in wxml
    component = _read("apps/miniprogram/components/entry-row/index.wxss")
    block = component.split(".entry-title--wrap {", 1)[1].split("}", 1)[0]
    assert "white-space: normal" in block
    assert "overflow-wrap: anywhere" in block
    assert "min-width: 0" in component
