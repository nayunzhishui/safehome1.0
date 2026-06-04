import importlib
import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = PROJECT_ROOT / "backend"


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

    list_response = client.get("/api/risk-review?status=pending")
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
        },
    )

    assert update_response.status_code == 200
    updated = update_response.get_json()["data"]
    assert updated["review_status"] == "follow_up_needed"
    assert updated["reviewer_id"] == "teacher-1"

    import database

    with database.get_connection() as conn:
        audit = conn.execute(
            "SELECT metadata_json FROM audit_logs WHERE action = 'review_risk' AND target_id = ?",
            (review["id"],),
        ).fetchone()

    assert audit is not None
    assert json.loads(audit["metadata_json"])["source_type"] == "feedback"


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

    list_response = client.get("/api/risk-review?status=pending")
    assert list_response.status_code == 200
    reviews = list_response.get_json()["data"]["items"]
    review = next(item for item in reviews if item["source_id"] == profile_id)
    assert review["source_type"] == "student_profile"
    assert review["risk_level"] == "high"
