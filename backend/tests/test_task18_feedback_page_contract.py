from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_feedback_page_uses_backend_emotion_overview_and_does_not_repeat_trigger_card():
    js = (ROOT / "apps/miniprogram/pages/feedback-result/index.js").read_text(encoding="utf-8")

    assert "const overview = feedback.emotion_overview || {};" in js
    assert "mainEmotion: overview.primary_emotion" in js
    assert "intensity: overview.intensity_text" in js
    assert js.count('title: "这次的触发点"') == 0
    assert js.count('title: "可能出现的互动线索"') == 1
    assert js.count('title: "可以练习的位置"') == 1
