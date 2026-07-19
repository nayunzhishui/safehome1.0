import importlib
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
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "safehome-test.sqlite3"))
    monkeypatch.setenv("CONTENT_DIR", str(PROJECT_ROOT / "content"))
    return importlib.import_module("app").app


def _login(client, code: str):
    response = client.post("/api/auth/wechat-login", json={"code": code, "nickname": code})
    data = response.get_json()["data"]
    return data["user"]["id"], {"Authorization": f"Bearer {data['token']}"}


def test_growth_overview_empty_state_has_four_separate_sections(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    _user_id, headers = _login(client, "growth-empty")

    response = client.get("/api/growth/overview", headers=headers)

    assert response.status_code == 200
    data = response.get_json()["data"]
    assert set(data["sections"]) == {"activity", "assessments", "relationship", "researcher_feedback"}
    assert data["sections"]["activity"]["record_count"] == 0
    assert data["sections"]["assessments"]["group_count"] == 0
    assert data["sections"]["relationship"]["available"] is False
    assert data["sections"]["researcher_feedback"]["count"] == 0
    assert "growth_score" not in data and "total_score" not in data["summary"]


def test_growth_overview_separates_multi_module_facts_and_scale_groups(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    user_id, headers = _login(client, "growth-multi")

    with app.app_context():
        from database import get_connection, now_iso

        timestamp = now_iso()
        with get_connection() as conn:
            card_id = conn.execute("SELECT id FROM training_cards WHERE enabled = 1 ORDER BY id LIMIT 1").fetchone()["id"]
            conn.execute(
                """
                INSERT INTO emotion_diaries (
                    id, user_id, scene, event_description, parent_emotion,
                    parent_emotion_intensity, created_at, updated_at
                ) VALUES ('growth-diary', ?, '一次沟通', '只用于合成测试', '担心', 5, ?, ?)
                """,
                (user_id, timestamp, timestamp),
            )
            for result_id, worksheet_id, title, score in [
                ("growth-assessment-1", "scale-a", "量表A", 5),
                ("growth-assessment-2", "scale-a", "量表A", 7),
                ("growth-assessment-3", "scale-b", "量表B", 20),
            ]:
                conn.execute(
                    """
                    INSERT INTO assessment_results (
                        id, user_id, worksheet_id, worksheet_title, answers_json,
                        scores_json, total_score, created_at
                    ) VALUES (?, ?, ?, ?, '{}', '{}', ?, ?)
                    """,
                    (result_id, user_id, worksheet_id, title, score, timestamp),
                )
            conn.execute(
                "INSERT INTO checkins (id, user_id, card_id, completed, created_at) VALUES ('growth-checkin', ?, ?, 1, ?)",
                (user_id, card_id, timestamp),
            )
            conn.execute(
                """
                INSERT INTO relationship_pilot_enrollments (
                    id, user_id, assessment_result_id, worksheet_id, dimensions_json,
                    radar_features_json, profile_json, consent_scope, status,
                    review_status, created_at, updated_at
                ) VALUES ('growth-enrollment', ?, 'growth-assessment-1', 'scale-a', '[]', '[]', '{}',
                          'feedback_review', 'enrolled', 'pending_review', ?, ?)
                """,
                (user_id, timestamp, timestamp),
            )
            conn.execute(
                """
                INSERT INTO relationship_pilot_tasks (
                    id, enrollment_id, user_id, task_type, review_status, created_at, updated_at
                ) VALUES ('growth-task', 'growth-enrollment', ?, 'relationship_drawing', 'pending_review', ?, ?)
                """,
                (user_id, timestamp, timestamp),
            )
            conn.execute(
                """
                INSERT INTO messages (
                    id, user_id, sender_role, message_type, title, body, status, created_at
                ) VALUES ('growth-feedback', ?, 'researcher', 'researcher_message',
                          '一条阶段性反馈', '只用于合成测试', 'unread', ?)
                """,
                (user_id, timestamp),
            )
            conn.commit()

    response = client.get("/api/growth/overview", headers=headers)
    data = response.get_json()["data"]

    assert data["sections"]["activity"] == {
        "available": True,
        "record_count": 1,
        "practice_count": 1,
    }
    assert data["sections"]["assessments"]["group_count"] == 2
    assert data["sections"]["assessments"]["repeat_group_count"] == 1
    assert data["sections"]["relationship"]["latest_enrollment_id"] == "growth-enrollment"
    assert data["sections"]["relationship"]["task_count"] == 1
    assert data["sections"]["researcher_feedback"]["count"] == 1
    assert data["sections"]["researcher_feedback"]["unread_count"] == 1
    assert {item["type"] for item in data["timeline"]} >= {
        "diary",
        "checkin",
        "assessment",
        "relationship_task",
        "feedback",
    }


def test_growth_entry_keeps_historical_urls_and_one_profile_entry():
    profile_source = (PROJECT_ROOT / "apps" / "miniprogram" / "pages" / "profile" / "index.js").read_text(encoding="utf-8")
    relationship_source = (PROJECT_ROOT / "apps" / "miniprogram" / "pages" / "relationship-growth" / "index.js").read_text(encoding="utf-8")
    pilot_source = (PROJECT_ROOT / "apps" / "miniprogram" / "pages" / "relationship-pilot" / "index.js").read_text(encoding="utf-8")
    unified_source = (PROJECT_ROOT / "apps" / "miniprogram" / "pages" / "growth-dashboard" / "index.js").read_text(encoding="utf-8")
    unified_markup = (PROJECT_ROOT / "apps" / "miniprogram" / "pages" / "growth-dashboard" / "index.wxml").read_text(encoding="utf-8")

    assert profile_source.count('url: "/pages/growth-dashboard/index"') == 1
    assert 'url: "/pages/relationship-growth/index"' not in profile_source
    assert "/pages/growth-dashboard/index?section=relationship" in relationship_source
    assert "options.detail === \"1\"" in relationship_source
    assert "/pages/growth-dashboard/index?section=relationship" in pilot_source
    assert "/pages/relationship-growth/index?detail=1" in unified_source
    for label in ["记录与练习", "测评变化", "关系探索", "研究者反馈"]:
        assert label in unified_source or label in unified_markup
    assert "不生成单一成长分数" in unified_markup
    assert 'bind:action="loadGrowth"' in unified_markup
