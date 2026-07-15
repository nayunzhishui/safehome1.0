import importlib
import json
import os
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = PROJECT_ROOT / "backend"
MINIPROGRAM_ROOT = PROJECT_ROOT / "apps" / "miniprogram"


def _fresh_app(tmp_path):
    sys.path.insert(0, str(BACKEND_ROOT))
    for name in list(sys.modules):
        if name in {"app", "config", "database", "models"} or name.startswith("routes.") or name.startswith("services."):
            sys.modules.pop(name, None)
    os.environ["DATABASE_PATH"] = str(tmp_path / "safehome-test.sqlite3")
    os.environ["CONTENT_DIR"] = str(PROJECT_ROOT / "content")
    return importlib.import_module("app").app


def _wechat_login(client, code):
    response = client.post("/api/auth/wechat-login", json={"code": code, "nickname": code})
    assert response.status_code == 200
    data = response.get_json()["data"]
    return data["user"]["id"], data["token"]


def _create_student_assessment(client, token):
    response = client.post(
        "/api/assessment-results",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "worksheet_id": "student_profile_v1",
            "answers": [
                {"question_id": question_id, "value": "5"}
                for question_id in ["test_anxiety", "iu_score", "fear_score", "self_compassion"]
            ],
        },
    )
    assert response.status_code == 201


def test_completed_card_is_removed_from_default_training_plan(tmp_path):
    app = _fresh_app(tmp_path)
    client = app.test_client()
    _user_id, token = _wechat_login(client, "task18-training-filter")
    _create_student_assessment(client, token)

    before = client.get("/api/training-plan", headers={"Authorization": f"Bearer {token}"}).get_json()["data"]
    card_id = before["plan_items"][0]["card_ids"][0]

    saved = client.post(
        "/api/checkins",
        headers={"Authorization": f"Bearer {token}"},
        json={"card_id": card_id, "completed": True, "reflection": "完成一次"},
    )
    assert saved.status_code == 201

    after = client.get("/api/training-plan", headers={"Authorization": f"Bearer {token}"}).get_json()["data"]
    remaining_ids = {
        item_card_id
        for item in after["plan_items"]
        for item_card_id in item.get("card_ids", [])
    }
    assert card_id in after["completed_card_ids"]
    assert card_id not in remaining_ids


def test_completed_checkin_history_is_private_paginated_and_enriched(tmp_path):
    app = _fresh_app(tmp_path)
    client = app.test_client()
    _user_id, token = _wechat_login(client, "task18-checkins-owner")
    _other_id, other_token = _wechat_login(client, "task18-checkins-other")

    for index in range(5):
        response = client.post(
            "/api/checkins",
            headers={"Authorization": f"Bearer {token}"},
            json={"card_id": "three_second_pause", "completed": True, "reflection": f"记录 {index}"},
        )
        assert response.status_code == 201
    client.post(
        "/api/checkins",
        headers={"Authorization": f"Bearer {token}"},
        json={"card_id": "emotion_naming", "completed": False, "skip_reason": "本次暂缓"},
    )

    first = client.get(
        "/api/checkins?completed=true&page=1&page_size=2",
        headers={"Authorization": f"Bearer {token}"},
    ).get_json()["data"]
    last = client.get(
        "/api/checkins?completed=true&page=3&page_size=2",
        headers={"Authorization": f"Bearer {token}"},
    ).get_json()["data"]
    other = client.get(
        "/api/checkins?completed=true",
        headers={"Authorization": f"Bearer {other_token}"},
    ).get_json()["data"]

    assert first["total"] == 5
    assert len(first["items"]) == 2
    assert first["has_more"] is True
    assert first["items"][0]["card_title"]
    assert len(last["items"]) == 1
    assert last["has_more"] is False
    assert other["total"] == 0
    assert other["items"] == []


def test_miniprogram_has_independent_training_history_and_repeat_action():
    app_config = json.loads((MINIPROGRAM_ROOT / "app.json").read_text(encoding="utf-8"))
    profile_js = (MINIPROGRAM_ROOT / "pages" / "profile" / "index.js").read_text(encoding="utf-8")
    history_js = (MINIPROGRAM_ROOT / "pages" / "training-history" / "index.js").read_text(encoding="utf-8")
    history_wxml = (MINIPROGRAM_ROOT / "pages" / "training-history" / "index.wxml").read_text(encoding="utf-8")
    plan_wxml = (MINIPROGRAM_ROOT / "pages" / "personalized-plan" / "index.wxml").read_text(encoding="utf-8")

    assert "pages/training-history/index" in app_config["pages"]
    assert 'url: "/pages/training-history/index"' in profile_js
    assert "completed: true" in history_js
    assert "has_more" in history_js
    assert "再次练习" in history_wxml
    assert "openSingleCard" in plan_wxml
