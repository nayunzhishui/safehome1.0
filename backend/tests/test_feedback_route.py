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
    assert data["supportive_feedback"]


def test_feedback_diary_id_requires_matching_owner_or_admin(tmp_path):
    app = _fresh_app(tmp_path)
    client = app.test_client()

    diary_response = client.post(
        "/api/diaries",
        json={
            "user_id": "parent-owner",
            "scene": "作业拖延",
            "event_description": "孩子写作业拖延，我催了很多次。",
            "parent_emotion": "着急",
        },
    )
    assert diary_response.status_code == 201
    diary_id = diary_response.get_json()["data"]["id"]

    wrong_owner = client.post(
        "/api/feedback/generate",
        json={"user_id": "parent-other", "diary_id": diary_id},
    )
    owner = client.post(
        "/api/feedback/generate",
        json={"user_id": "parent-owner", "diary_id": diary_id},
    )
    admin = client.post(
        "/api/feedback/generate",
        json={"diary_id": diary_id},
        headers=ADMIN_HEADERS,
    )

    assert wrong_owner.status_code == 401
    assert owner.status_code == 201
    assert admin.status_code == 201
