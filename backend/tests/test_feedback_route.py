import importlib
import json
import os
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = PROJECT_ROOT / "backend"
ADMIN_HEADERS = {"X-Admin-Token": "safehome-local-admin-token"}


def _fresh_app(tmp_path):
    sys.path.insert(0, str(BACKEND_ROOT))
    for name in list(sys.modules):
        if name in {"app", "config", "database", "models"} or name.startswith("routes.") or name.startswith("services."):
            sys.modules.pop(name, None)
    os.environ["DATABASE_PATH"] = str(tmp_path / "safehome-test.sqlite3")
    os.environ["CONTENT_DIR"] = str(PROJECT_ROOT / "content")
    module = importlib.import_module("app")
    return module.app


def _wechat_login(client, code: str):
    response = client.post("/api/auth/wechat-login", json={"code": code, "nickname": code})
    assert response.status_code == 200
    data = response.get_json()["data"]
    return data["user"]["id"], data["token"]


def test_feedback_high_risk_blocks_training_cards_and_common_rules(tmp_path):
    app = _fresh_app(tmp_path)
    client = app.test_client()

    response = client.post(
        "/api/feedback/generate",
        json={
            "user_id": "parent-risk",
            "event_description": "你怎么又这样，我不想活了",
            "automatic_thought": "撑不下去了",
            "behavior": "一直哭",
        },
    )

    assert response.status_code == 201
    data = response.get_json()["data"]
    assert data["risk_level"] == "high"
    assert data["recommended_card_ids"] == []
    assert data["tags"] == []
    assert data["labels"] == []
    assert data["risk"]["allow_auto_feedback"] is False
    assert data["risk"]["allow_recommended_training_cards"] is False
    assert data["supportive_feedback"] == data["risk"]["safe_response"]
    assert data["alternative_response"] == data["risk"]["boundary_notice"]
    assert data["training_recommendation_rules"] == []

    from database import get_connection

    with get_connection() as conn:
        row = conn.execute(
            "SELECT tags_json, recommended_card_ids_json, risk_level FROM feedback_results WHERE id = ?",
            (data["id"],),
        ).fetchone()

    assert json.loads(row["tags_json"]) == []
    assert json.loads(row["recommended_card_ids_json"]) == []
    assert row["risk_level"] == "high"


def test_feedback_low_risk_keeps_existing_rule_flow(tmp_path):
    app = _fresh_app(tmp_path)
    client = app.test_client()

    response = client.post(
        "/api/feedback/generate",
        json={
            "user_id": "parent-low",
            "event_description": "孩子写作业拖延，我说你怎么又这样。",
            "scene": "作业拖延",
            "parent_emotion": "着急",
            "parent_emotion_intensity": 8,
            "automatic_thought": "他是不是不上心",
            "behavior": "忍不住催了很多次",
        },
    )

    assert response.status_code == 201
    data = response.get_json()["data"]
    assert data["risk_level"] == "low"
    assert data["risk"]["allow_auto_feedback"] is True
    assert "judgmental_language" in data["tags"]
    assert data["recommended_card_ids"]
    assert data["training_recommendation_rules"]
    rule = data["training_recommendation_rules"][0]
    assert rule["rule_id"] == "diary_judgmental_language_nonjudgmental_response"
    assert rule["source_type"] == "diary"
    assert rule["today_suggestion"]
    assert rule["long_term_suggestion"] == ""
    assert len(rule["recommended_card_ids"]) <= 3
    assert len(data["training_recommendation_rules"]) == 1
    assert len(data["recommended_card_ids"]) <= 3
    assert data["supportive_feedback"]
    assert data["emotion_overview"]["primary_emotion"] == "着急"
    assert data["emotion_overview"]["intensity_text"] == "较强"
    assert "作业拖延" in data["trigger_summary"]
    assert "忍不住催了很多次" in data["pattern_summary"]


def test_feedback_fields_change_with_the_current_diary_instead_of_using_placeholders(tmp_path):
    app = _fresh_app(tmp_path)
    client = app.test_client()

    worried = client.post(
        "/api/feedback/generate",
        json={
            "user_id": "feedback-difference",
            "scene": "睡前冲突",
            "event_description": "孩子一直没有准备睡觉。",
            "parent_emotion": "担心",
            "parent_emotion_intensity": 7,
            "automatic_thought": "明天会不会起不来",
            "behavior": "反复提醒时间",
        },
    ).get_json()["data"]
    guilty = client.post(
        "/api/feedback/generate",
        json={
            "user_id": "feedback-difference",
            "scene": "亲子沟通",
            "event_description": "刚才说话声音太大。",
            "parent_emotion": "内疚",
            "parent_emotion_intensity": 3,
            "automatic_thought": "我可以重新说明",
            "behavior": "停下来道歉",
        },
    ).get_json()["data"]

    assert worried["emotion_overview"]["primary_emotion"] == "担心"
    assert guilty["emotion_overview"]["primary_emotion"] == "内疚"
    assert worried["emotion_overview"]["intensity_text"] == "中等"
    assert guilty["emotion_overview"]["intensity_text"] == "较轻"
    assert worried["trigger_summary"] != guilty["trigger_summary"]
    assert worried["pattern_summary"] != guilty["pattern_summary"]
    assert "一般情绪记录" not in worried["emotion_overview"]["primary_emotion"]


def test_feedback_diary_id_requires_matching_owner_or_admin(tmp_path):
    app = _fresh_app(tmp_path)
    client = app.test_client()
    owner_id, owner_token = _wechat_login(client, "parent-owner")
    other_id, other_token = _wechat_login(client, "parent-other")

    diary_response = client.post(
        "/api/diaries",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={
            "user_id": owner_id,
            "scene": "作业拖延",
            "event_description": "孩子写作业拖延，我催了很多次。",
            "parent_emotion": "着急",
        },
    )
    assert diary_response.status_code == 201
    diary_id = diary_response.get_json()["data"]["id"]

    wrong_owner = client.post(
        "/api/feedback/generate",
        headers={"Authorization": f"Bearer {other_token}"},
        json={"user_id": other_id, "diary_id": diary_id},
    )
    owner = client.post(
        "/api/feedback/generate",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={"user_id": owner_id, "diary_id": diary_id},
    )
    admin = client.post(
        "/api/feedback/generate",
        json={"diary_id": diary_id},
        headers=ADMIN_HEADERS,
    )

    assert wrong_owner.status_code == 404
    assert owner.status_code == 201
    assert admin.status_code == 201
