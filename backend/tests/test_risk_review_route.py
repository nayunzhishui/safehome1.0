import importlib
import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = PROJECT_ROOT / "backend"
ADMIN_HEADERS = {"X-Admin-Token": "safehome-local-admin-token"}


def _fresh_app(tmp_path, monkeypatch):
    sys.path.insert(0, str(BACKEND_ROOT))
    for name in list(sys.modules):
        if name in {"app", "config", "database", "models"} or name.startswith("routes.") or name.startswith("services."):
            sys.modules.pop(name, None)
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.delenv("ADMIN_EXPORT_TOKEN", raising=False)
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "safehome-test.sqlite3"))
    monkeypatch.setenv("CONTENT_DIR", str(PROJECT_ROOT / "content"))
    module = importlib.import_module("app")
    return module.app


def test_high_risk_feedback_creates_pending_risk_review_and_review_audit(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()

    feedback_response = client.post(
        "/api/feedback/generate",
        json={
            "user_id": "parent-risk-review",
            "event_description": "我不想活了，感觉撑不下去。",
            "behavior": "一直哭",
        },
    )

    assert feedback_response.status_code == 201
    feedback_id = feedback_response.get_json()["data"]["id"]

    list_response = client.get("/api/risk-review?status=pending", headers=ADMIN_HEADERS)
    assert list_response.status_code == 200
    reviews = list_response.get_json()["data"]["items"]
    review = next(item for item in reviews if item["source_id"] == feedback_id)
    assert review["source_type"] == "feedback"
    assert review["risk_level"] == "high"
    assert json.loads(review["matched_categories_json"])[0]["id"] == "self_harm"

    update_response = client.post(
        f"/api/risk-review/{review['id']}/review",
        json={
            "reviewer_id": "teacher-1",
            "review_status": "follow_up_needed",
            "review_note": "建议人工进一步确认现实支持资源。",
            "action_taken": "已提醒人工跟进现实支持资源",
            "closed_reason": "暂不关闭",
        },
        headers=ADMIN_HEADERS,
    )

    assert update_response.status_code == 200
    updated = update_response.get_json()["data"]
    assert updated["review_status"] == "follow_up_needed"
    assert updated["reviewer_id"] == "teacher-1"
    assert updated["action_taken"] == "已提醒人工跟进现实支持资源"
    assert updated["closed_reason"] == "暂不关闭"

    import database

    with database.get_connection() as conn:
        audit = conn.execute(
            "SELECT metadata_json FROM audit_logs WHERE action = 'review_risk' AND target_id = ?",
            (review["id"],),
        ).fetchone()

    assert audit is not None
    metadata = json.loads(audit["metadata_json"])
    assert metadata["source_type"] == "feedback"
    assert metadata["action_taken"] == "已提醒人工跟进现实支持资源"
    assert metadata["closed_reason"] == "暂不关闭"


def test_high_risk_profile_creates_pending_risk_review(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()

    profile_response = client.post(
        "/api/profile",
        json={
            "user_id": "student-risk-review",
            "scores": {
                "test_anxiety": 4.2,
                "iu_score": 4.1,
                "f_score": 2.8,
                "self_compassion": 2.7,
            },
            "free_text": "我最近不想活，需要现实中的可信成年人帮助。",
        },
    )

    assert profile_response.status_code == 201
    profile_id = profile_response.get_json()["data"]["student_profile_id"]

    list_response = client.get("/api/risk-review?status=pending", headers=ADMIN_HEADERS)
    assert list_response.status_code == 200
    reviews = list_response.get_json()["data"]["items"]
    review = next(item for item in reviews if item["source_id"] == profile_id)
    assert review["source_type"] == "student_profile"
    assert review["risk_level"] == "high"


def test_followup_and_sandplay_high_risk_text_create_pending_reviews(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()

    profile_response = client.post(
        "/api/profile",
        json={
            "user_id": "student-followup-risk",
            "scores": {
                "test_anxiety": 4.2,
                "iu_score": 4.1,
                "f_score": 2.8,
                "self_compassion": 2.7,
            },
            "free_text": "考试前会担心，但愿意先做一次情绪命名练习。",
        },
    )
    profile_id = profile_response.get_json()["data"]["student_profile_id"]

    followup_response = client.post(
        f"/api/profile-results/{profile_id}/followups",
        json={"user_id": "student-followup-risk", "round_no": 1, "text": "最近又出现不想活的念头，需要现实支持。"},
    )
    sandplay_response = client.post(
        f"/api/profile-results/{profile_id}/sandplay",
        json={
            "user_id": "student-followup-risk",
            "scene": {"symbols": [{"type": "stone", "x": 30, "y": 40}]},
            "reflection_text": "我觉得撑不住，也不想活了。",
        },
    )

    assert followup_response.status_code == 201
    assert followup_response.get_json()["data"]["risk"]["risk_level"] == "high"
    assert sandplay_response.status_code == 201
    assert sandplay_response.get_json()["data"]["risk"]["risk_level"] == "high"

    reviews_response = client.get("/api/risk-review?status=pending", headers=ADMIN_HEADERS)
    reviews = reviews_response.get_json()["data"]["items"]
    source_types = {item["source_type"] for item in reviews}
    assert "student_profile_followup" in source_types
    assert "student_sandplay" in source_types


def test_supervision_high_risk_message_creates_pending_review(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()

    response = client.post(
        "/api/supervision",
        json={"user_id": "parent-supervision-risk", "message": "我不想活了，需要人工支持。"},
    )

    assert response.status_code == 201
    data = response.get_json()["data"]
    assert data["risk_level"] == "high"
    assert data["risk"]["risk_level"] == "high"

    reviews_response = client.get("/api/risk-review?status=pending", headers=ADMIN_HEADERS)
    reviews = reviews_response.get_json()["data"]["items"]
    review = next(item for item in reviews if item["source_id"] == data["id"])
    assert review["source_type"] == "supervision"
    assert review["risk_level"] == "high"


def _parent_answers() -> dict:
    content_path = PROJECT_ROOT / "content" / "readfeedback" / "parent_scales.json"
    payload = json.loads(content_path.read_text(encoding="utf-8"))
    return {
        item["item_code"]: "3"
        for scale in payload["scales"]
        for item in scale["items"]
    }


def test_parent_assessment_open_text_high_risk_creates_pending_review(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()

    response = client.post(
        "/api/parent-assessments",
        json={
            "user_id": "parent-assessment-risk",
            "answers": _parent_answers(),
            "question_answers": {
                "q1": "comfort",
                "q2": "sometimes",
                "q3": "early",
                "q4": "balanced",
                "q5": "some",
                "q6": "最近压力很大，出现过不想活的念头。",
                "q7": "clear",
                "q8": "pause",
            },
        },
    )

    assert response.status_code == 201
    data = response.get_json()["data"]
    assert data["risk"]["risk_level"] == "high"
    assert data["report"]["action_title"] == "优先确认现实支持"

    reviews_response = client.get("/api/risk-review?status=pending", headers=ADMIN_HEADERS)
    reviews = reviews_response.get_json()["data"]["items"]
    review = next(item for item in reviews if item["source_id"] == data["id"])
    assert review["source_type"] == "parent_assessment"
    assert review["risk_level"] == "high"
