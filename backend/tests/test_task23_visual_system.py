from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _read(relative_path: str) -> str:
    return (PROJECT_ROOT / relative_path).read_text(encoding="utf-8")


def test_shared_participant_state_components_are_accessible_and_touch_safe():
    state_markup = _read("apps/miniprogram/components/page-state/index.wxml")
    state_style = _read("apps/miniprogram/components/page-state/index.wxss")
    status_markup = _read("apps/miniprogram/components/status-pill/index.wxml")
    journey_markup = _read("apps/miniprogram/components/journey-action-card/index.wxml")
    journey_style = _read("apps/miniprogram/components/journey-action-card/index.wxss")

    assert 'aria-live="polite"' in state_markup
    assert 'aria-label="{{actionAriaLabel || actionLabel}}"' in state_markup
    assert "min-height: 88rpx" in state_style
    assert 'role="status"' in status_markup
    assert 'aria-label="{{ariaLabel || label}}"' in status_markup
    assert 'aria-label="{{regionAriaLabel}}"' in journey_markup
    assert 'value: "今天的一小步"' in _read("apps/miniprogram/components/journey-action-card/index.js")
    assert "重新读取" in journey_markup
    assert "min-height: 88rpx" in journey_style


def test_home_uses_one_shared_journey_action_card_in_the_frozen_position():
    markup = _read("apps/miniprogram/pages/home/index.wxml")
    config = _read("apps/miniprogram/pages/home/index.json")

    core_index = markup.index('class="core-actions"')
    journey_index = markup.index("<journey-action-card")
    three_step_index = markup.index('title="三步开始"')
    assert core_index < journey_index < three_step_index
    assert markup.count("<journey-action-card") == 1
    assert 'bind:action="openTodayAction"' in markup
    assert 'bind:retry="retryTodayJourney"' in markup
    assert '"journey-action-card"' in config

    pilot_markup = _read("apps/miniprogram/pages/relationship-pilot/index.wxml")
    pilot_config = _read("apps/miniprogram/pages/relationship-pilot/index.json")
    assert "<journey-action-card" in pilot_markup
    assert 'region-aria-label="关系探索当前步骤"' in pilot_markup
    assert '"journey-action-card"' in pilot_config


def test_growth_and_messages_share_loading_error_empty_and_status_components():
    for page in ["growth-dashboard", "messages"]:
        markup = _read(f"apps/miniprogram/pages/{page}/index.wxml")
        config = _read(f"apps/miniprogram/pages/{page}/index.json")
        assert "<page-state" in markup
        assert '"page-state"' in config

    messages_markup = _read("apps/miniprogram/pages/messages/index.wxml")
    messages_config = _read("apps/miniprogram/pages/messages/index.json")
    assert "<status-pill" in messages_markup
    assert '"status-pill"' in messages_config


def test_feedback_rating_exposes_selected_state_and_save_status():
    markup = _read("apps/miniprogram/components/feedback-rating/index.wxml")
    assert 'aria-pressed="{{value === item.value}}"' in markup
    assert 'role="status"' in markup
    assert "已记录你的核对" in markup


def test_key_participant_pages_keep_bottom_safe_area_and_one_primary_action():
    for page in ["messages", "message-detail", "growth-dashboard"]:
        style = _read(f"apps/miniprogram/pages/{page}/index.wxss")
        assert "env(safe-area-inset-bottom)" in style

    message_markup = _read("apps/miniprogram/pages/message-detail/index.wxml")
    assert message_markup.count('class="safe-primary-button bottom-action"') <= 1
    assert 'class="safe-outline-button bottom-action"' in message_markup


def test_visual_audit_covers_required_viewports_overflow_touch_and_names():
    source = _read("scripts/audit_task23_visual_system.mjs")
    assert "const VIEWPORTS = [375, 430, 768, 1440]" in source
    assert "TASK37_38_MINIPROGRAM_PAGES" in source
    assert "therapeutic-assessment-feedback-check" in source
    assert "researcher-dashboard" in source
    assert "auditActualPageSources" in source
    assert "scrollWidth" in source
    assert "44" in source
    assert "aria-label" in source
    assert "screenshot" in source
    assert "shared-component-rendered-matrix" in source
