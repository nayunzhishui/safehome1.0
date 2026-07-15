from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _read(relative_path: str) -> str:
    return (PROJECT_ROOT / relative_path).read_text(encoding="utf-8")


def test_nine_point_scale_uses_compact_grid_layout():
    markup = _read("apps/miniprogram/pages/assessment-detail/index.wxml")
    styles = _read("apps/miniprogram/pages/assessment-detail/index.wxss")

    assert "item.options.length === 9" in markup
    assert ".option-row--nine" in styles
    assert "grid-template-columns: repeat(3" in styles


def test_getting_started_layout_contains_overflow_guards():
    styles = _read("apps/miniprogram/pages/getting-started/index.wxss")
    markup = _read("apps/miniprogram/pages/task-detail/index.wxml")

    assert "overflow-x: hidden" in styles
    assert "min-width: 0" in styles
    assert 'title="练习步骤"' in markup


def test_relationship_pilot_calls_step_four_stage_feedback():
    script = _read("apps/miniprogram/pages/relationship-pilot/index.js")

    assert 'title: "阶段性反馈"' in script
    assert 'reportStatus === "sent"' not in script
