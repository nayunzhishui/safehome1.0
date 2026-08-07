import importlib
import json
import os
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = PROJECT_ROOT / "backend"
ADMIN_HEADERS = {"X-Admin-Token": "safehome-local-admin-token"}


def _high_signal() -> str:
    payload = json.loads((PROJECT_ROOT / "content" / "risk_keywords.json").read_text(encoding="utf-8"))
    return str(payload["categories"][0]["keywords"][0])


def _fresh_app(tmp_path):
    sys.path.insert(0, str(BACKEND_ROOT))
    for name in list(sys.modules):
        if name in {"app", "config", "database", "models"} or name.startswith("routes.") or name.startswith("services."):
            sys.modules.pop(name, None)
    os.environ["DATABASE_PATH"] = str(tmp_path / "safehome-test.sqlite3")
    os.environ["CONTENT_DIR"] = str(PROJECT_ROOT / "content")
    os.environ.pop("APP_ENV", None)
    module = importlib.import_module("app")
    return module.app


def _wechat_login(client, code: str):
    response = client.post("/api/auth/wechat-login", json={"code": code, "nickname": code})
    assert response.status_code == 200
    data = response.get_json()["data"]
    return data["user"]["id"], data["token"]


def _risk_review_count() -> int:
    import database

    with database.get_connection() as conn:
        return conn.execute("SELECT COUNT(*) FROM risk_review_records").fetchone()[0]


def _parent_answers() -> dict:
    payload = json.loads((PROJECT_ROOT / "content" / "readfeedback" / "parent_scales.json").read_text(encoding="utf-8"))
    return {
        item["item_code"]: "3"
        for scale in payload["scales"]
        for item in scale["items"]
    }


def test_low_feedback_text_does_not_create_risk_review_record(tmp_path):
    app = _fresh_app(tmp_path)
    client = app.test_client()

    response = client.post(
        "/api/feedback/generate",
        json={
            "user_id": "risk-low-parent",
            "event_description": "今天作业沟通有点着急，我想先记录一下。",
            "automatic_thought": "也许可以慢一点。",
            "behavior": "暂停后重新说。",
        },
    )

    assert response.status_code == 201
    assert response.get_json()["data"]["risk_level"] == "low"
    assert _risk_review_count() == 0


def test_medium_and_high_text_create_risk_review_records(tmp_path):
    app = _fresh_app(tmp_path)
    client = app.test_client()
    signal = _high_signal()

    medium = client.post(
        "/api/feedback/generate",
        json={
            "user_id": "risk-medium-parent",
            "event_description": "最近连续失眠，感觉有点撑不住。",
            "behavior": "先记录下来。",
        },
    )
    high = client.post(
        "/api/feedback/generate",
        json={
            "user_id": "risk-high-parent",
            "event_description": f"当前直接表达：{signal}。",
            "behavior": "需要人工复核。",
        },
    )

    assert medium.status_code == 201
    assert high.status_code == 201
    assert medium.get_json()["data"]["risk_level"] == "medium"
    assert high.get_json()["data"]["risk_level"] == "high"
    assert high.get_json()["data"]["recommended_card_ids"] == []

    reviews = client.get("/api/risk-review", headers=ADMIN_HEADERS).get_json()["data"]["items"]
    levels = {item["risk_level"] for item in reviews}
    assert {"medium", "high"}.issubset(levels)


def test_high_profile_parent_assessment_and_supervision_use_boundary_routing(tmp_path):
    app = _fresh_app(tmp_path)
    client = app.test_client()
    signal = _high_signal()
    supervision_user_id, supervision_token = _wechat_login(client, "risk-high-supervision")

    profile = client.post(
        "/api/profile",
        json={
            "user_id": "risk-high-student",
            "scores": {"test_anxiety": 4.2, "iu_score": 4.0, "f_score": 2.8, "self_compassion": 2.7},
            "free_text": f"当前直接表达：{signal}。需要现实支持。",
        },
    )
    parent = client.post(
        "/api/parent-assessments",
        json={
            "user_id": "risk-high-parent-assessment",
            "answers": _parent_answers(),
            "question_answers": {"open": f"最近撑不住，也出现{signal}相关表达。"},
        },
    )
    supervision = client.post(
        "/api/supervision",
        headers={"Authorization": f"Bearer {supervision_token}"},
        json={"user_id": supervision_user_id, "message": f"当前直接表达：{signal}。需要人工支持。"},
    )

    assert profile.status_code == 201
    assert profile.get_json()["data"]["risk_level"] == "high"
    assert profile.get_json()["data"]["recommended_card_ids"] == []
    assert parent.status_code == 201
    assert parent.get_json()["data"]["report"]["action_title"] == "优先确认现实支持"
    assert supervision.status_code == 201
    assert supervision.get_json()["data"]["risk_level"] == "high"

    reviews = client.get("/api/risk-review", headers=ADMIN_HEADERS).get_json()["data"]["items"]
    source_types = {item["source_type"] for item in reviews}
    assert {"student_profile", "parent_assessment", "supervision"}.issubset(source_types)


def test_multiple_fields_use_highest_risk_and_quoted_or_negated_text_is_conservative(tmp_path):
    app = _fresh_app(tmp_path)
    client = app.test_client()
    signal = _high_signal()

    mixed = client.post(
        "/api/feedback/generate",
        json={
            "user_id": "risk-mixed-parent",
            "event_description": "今天只是普通冲突。",
            "automatic_thought": "最近连续失眠。",
            "raw_text": f"也出现过{signal}相关表达。",
        },
    )
    quoted = client.post("/api/risk/check", json={"text": f"孩子引用同学的话：他说“{signal}”。"})
    negated = client.post("/api/risk/check", json={"text": f"我明确否认该表达：没有{signal}，只是压力很大。"})

    assert mixed.status_code == 201
    assert mixed.get_json()["data"]["risk_level"] == "high"
    assert mixed.get_json()["data"]["recommended_card_ids"] == []
    assert quoted.status_code == 200
    assert negated.status_code == 200
    assert quoted.get_json()["data"]["risk_level"] == "medium"
    assert quoted.get_json()["data"]["safety_route"] == "human_review"
    assert negated.get_json()["data"]["risk_level"] == "medium"
    assert negated.get_json()["data"]["safety_route"] == "human_review"
