import importlib
import json
import os
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = PROJECT_ROOT / "backend"
ADMIN_HEADERS = {"X-Admin-Token": "safehome-local-admin-token"}


def _fresh_app(tmp_path, content_dir: Path | None = None):
    sys.path.insert(0, str(BACKEND_ROOT))
    for name in list(sys.modules):
        if name in {"app", "config", "database", "models"} or name.startswith("routes.") or name.startswith("services."):
            sys.modules.pop(name, None)
    os.environ["DATABASE_PATH"] = str(tmp_path / "safehome-test.sqlite3")
    if content_dir is None:
        os.environ["CONTENT_DIR"] = str(PROJECT_ROOT / "content")
    else:
        os.environ["CONTENT_DIR"] = str(content_dir)
    module = importlib.import_module("app")
    return module.app


def _profile_payload(user_id: str = "student-test") -> dict:
    return {
        "user_id": user_id,
        "round": 1,
        "scores": {
            "test_anxiety": 4.2,
            "iu_score": 4.1,
            "f_score": 2.8,
            "self_compassion": 2.7,
        },
        "free_text": "考试前会担心，但愿意先做一次情绪命名练习。",
    }


def _high_risk_profile_payload(user_id: str = "student-risk") -> dict:
    payload = _profile_payload(user_id)
    payload["free_text"] = "我最近不想活，需要现实中的可信成年人帮助。"
    return payload


def test_missing_student_profile_rules_returns_content_error(tmp_path):
    content_dir = tmp_path / "content"
    content_dir.mkdir()
    (content_dir / "training_cards.json").write_text(json.dumps({"version": "test", "cards": []}), encoding="utf-8")
    (content_dir / "risk_keywords.json").write_text(json.dumps({"categories": [], "handling_rules": []}), encoding="utf-8")
    app = _fresh_app(tmp_path, content_dir)
    client = app.test_client()

    response = client.post("/api/profile", json=_profile_payload())

    assert response.status_code == 500
    body = response.get_json()
    assert body["ok"] is False
    assert body["error"]["code"] == "content_load_error"
    assert "readfeedback/student_scales.json" in body["error"]["message"]


def test_profile_review_creates_review_and_audit_without_overwriting_profile(tmp_path):
    app = _fresh_app(tmp_path)
    client = app.test_client()

    create_response = client.post("/api/profile", json=_profile_payload("student-review"))
    assert create_response.status_code == 201
    created = create_response.get_json()["data"]
    profile_id = created["student_profile_id"]
    assert created["model_type"] == "readfeedback-kmeans-pca"
    assert created["report"]["sandplay_task"]["title"]

    review_response = client.post(
        f"/api/profile-results/{profile_id}/review",
        json={
            "reviewer_id": "teacher-1",
            "review_status": "reviewed",
            "review_decision": "维持支持性反馈，建议继续观察",
            "note": "学生端报告不修改。",
            "action_summary": "已完成人工复核。",
            "visible_to_student": False,
        },
        headers=ADMIN_HEADERS,
    )

    assert review_response.status_code == 201
    review = review_response.get_json()["data"]
    assert review["profile_id"] == profile_id
    assert review["review_status"] == "reviewed"
    assert review["visible_to_student"] == 0

    detail_response = client.get(f"/api/profile-results/{profile_id}")
    assert detail_response.status_code == 200
    detail = detail_response.get_json()["data"]
    assert detail["id"] == profile_id
    assert detail["latest_review"]["review_decision"] == "维持支持性反馈，建议继续观察"

    from database import get_connection

    with get_connection() as conn:
        profile_count = conn.execute("SELECT COUNT(*) FROM student_profiles WHERE id = ?", (profile_id,)).fetchone()[0]
        review_count = conn.execute("SELECT COUNT(*) FROM profile_reviews WHERE profile_id = ?", (profile_id,)).fetchone()[0]
        audit_count = conn.execute(
            "SELECT COUNT(*) FROM audit_logs WHERE target_id = ? AND action = 'review_profile'",
            (profile_id,),
        ).fetchone()[0]

    assert profile_count == 1
    assert review_count == 1
    assert audit_count == 1


def test_high_risk_profile_and_records_export_requires_confirmation(tmp_path):
    app = _fresh_app(tmp_path)
    client = app.test_client()
    headers = {"X-Admin-Token": "safehome-local-admin-token"}

    create_response = client.post("/api/profile", json=_high_risk_profile_payload("student-risk-export"))
    assert create_response.status_code == 201
    created = create_response.get_json()["data"]
    assert created["risk_level"] == "high"
    assert created["recommended_card_ids"] == []
    assert created["allow_auto_feedback"] is False

    blocked_profile_export = client.get("/api/admin/export?type=profile", headers=headers)
    assert blocked_profile_export.status_code == 409
    assert blocked_profile_export.get_json()["error"]["code"] == "high_risk_export_confirmation_required"

    confirmed_profile_export = client.get("/api/admin/export?type=profile&confirm_high_risk=true", headers=headers)
    assert confirmed_profile_export.status_code == 200
    profile_csv = confirmed_profile_export.get_data(as_text=True)
    assert "anon_" in profile_csv
    assert "student-risk-export" not in profile_csv
    assert "不想活" not in profile_csv

    blocked_records_export = client.get("/api/admin/export?type=records&module_type=student_profile", headers=headers)
    assert blocked_records_export.status_code == 409

    confirmed_records_export = client.get(
        "/api/admin/export?type=records&module_type=student_profile&confirm_high_risk=true",
        headers=headers,
    )
    assert confirmed_records_export.status_code == 200
    records_csv = confirmed_records_export.get_data(as_text=True)
    assert "student_profile" in records_csv
    assert "student-risk-export" not in records_csv
    assert "不想活" not in records_csv

    from database import get_connection

    with get_connection() as conn:
        records_count = conn.execute("SELECT COUNT(*) FROM records WHERE module_type = 'student_profile'").fetchone()[0]
        stored_recommended = conn.execute(
            "SELECT recommended_task_ids_json FROM student_profiles WHERE id = ?",
            (created["student_profile_id"],),
        ).fetchone()[0]
        profile_export_audit = conn.execute(
            """
            SELECT metadata_json FROM audit_logs
            WHERE action = 'export_profile'
            ORDER BY created_at DESC
            LIMIT 1
            """
        ).fetchone()[0]
        records_export_audit = conn.execute(
            """
            SELECT metadata_json FROM audit_logs
            WHERE action = 'export_records'
            ORDER BY created_at DESC
            LIMIT 1
            """
        ).fetchone()[0]

    assert records_count == 1
    assert json.loads(stored_recommended) == []
    assert json.loads(profile_export_audit)["contains_high_risk"] is True
    assert json.loads(profile_export_audit)["confirmed_high_risk_export"] is True
    assert json.loads(records_export_audit)["module_type_filter"] == "student_profile"
    assert json.loads(records_export_audit)["contains_high_risk"] is True


def test_profile_visuals_followup_and_sandplay_flow(tmp_path):
    app = _fresh_app(tmp_path)
    client = app.test_client()

    create_response = client.post("/api/profile", json=_profile_payload("student-visuals"))
    assert create_response.status_code == 201
    profile_id = create_response.get_json()["data"]["student_profile_id"]

    followup_response = client.post(
        f"/api/profile-results/{profile_id}/followups",
        json={"round_no": 1, "fit": "比较像", "task_done": "已尝试", "state_score": 3, "text": "比上次稍微放松一些。"},
    )
    assert followup_response.status_code == 201

    sandplay_response = client.post(
        f"/api/profile-results/{profile_id}/sandplay",
        json={
            "scene": {
                "symbols": [
                    {"type": "stone", "x": 25, "y": 40},
                    {"type": "tree", "x": 70, "y": 45},
                ]
            },
            "reflection_text": "压力旁边也有一点资源。",
        },
    )
    assert sandplay_response.status_code == 201
    assert sandplay_response.get_json()["data"]["summary"]["symbol_count"] == 2

    visuals_response = client.get(f"/api/profile-results/{profile_id}/visuals")
    assert visuals_response.status_code == 200
    visuals = visuals_response.get_json()["data"]
    assert len(visuals["radar"]) == 4
    assert len(visuals["trends"]) == 2


def _parent_answers() -> dict:
    content_path = PROJECT_ROOT / "content" / "readfeedback" / "parent_scales.json"
    payload = json.loads(content_path.read_text(encoding="utf-8"))
    return {
        item["item_code"]: "3"
        for scale in payload["scales"]
        for item in scale["items"]
    }


def test_parent_assessment_report_and_export(tmp_path):
    app = _fresh_app(tmp_path)
    client = app.test_client()

    response = client.post(
        "/api/parent-assessments",
        json={
            "user_id": "parent-flow",
            "participant_code": "P001",
            "research_consent": True,
            "answers": _parent_answers(),
            "question_answers": {"q1": "comfort", "q2": "sometimes", "q3": "early", "q4": "balanced", "q5": "some", "q7": "clear", "q8": "pause"},
        },
    )
    assert response.status_code == 201
    data = response.get_json()["data"]
    assert data["report"]["boundary_notice"]

    detail = client.get(f"/api/parent-assessments/{data['id']}")
    assert detail.status_code == 200
    assert detail.get_json()["data"]["participant_code"] == "P001"

    export_response = client.get(
        "/api/admin/export?type=parent_assessments",
        headers={"X-Admin-Token": "safehome-local-admin-token"},
    )
    assert export_response.status_code == 200
    assert "P001" in export_response.get_data(as_text=True)
