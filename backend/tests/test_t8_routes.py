import importlib
import sys
from datetime import date, timedelta
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
    module = importlib.import_module("app")
    return module.app


def _wechat_login(client, code: str):
    response = client.post("/api/auth/wechat-login", json={"code": code, "nickname": code})
    assert response.status_code == 200
    data = response.get_json()["data"]
    return data["user"]["id"], data["token"]


def test_emotion_thermometer_day_returns_sorted_records_and_summary(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    user_id, token = _wechat_login(client, "t8-thermo")

    for level, created_at in [(7, "2026-07-01T09:10:00+00:00"), (3, "2026-07-01T08:10:00+00:00")]:
        response = client.post(
            "/api/emotion-thermometer",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "intensity_level": level,
                "brief_text": "一次温度记录",
                "created_at": created_at,
            },
        )
        assert response.status_code == 201

    response = client.get(
        f"/api/emotion-thermometer/day?user_id={user_id}&date=2026-07-01",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.get_json()["data"]
    assert [item["intensity_level"] for item in data["items"]] == [3, 7]
    assert data["summary"]["count"] == 2
    assert data["summary"]["min"] == 3
    assert data["summary"]["max"] == 7
    assert data["summary"]["avg"] == 5.0
    assert data["summary"]["valence_avg"] is None
    assert data["summary"]["arousal_avg"] is None
    assert data["summary"]["control_avg"] is None
    assert "诊断" in data["boundary_notice"]


def test_programs_endpoints_return_pilot_programs(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()

    list_response = client.get("/api/programs")
    assert list_response.status_code == 200
    items = list_response.get_json()["data"]["items"]
    ids = {item["id"] for item in items}
    assert "self_compassion_exam_anxiety" in ids
    assert "academic_pressure_sleep_health" in ids
    assert all(item["measurement_plan"]["measurement_point_labels"] for item in items)
    assert all(item["measurement_plan"]["requires_manual_review"] is True for item in items)

    detail_response = client.get("/api/programs/self_compassion_exam_anxiety")
    assert detail_response.status_code == 200
    program = detail_response.get_json()["data"]["program"]
    assert program["review_status"] == "pilot_draft"
    assert len(program["sessions"]) >= 3
    assert program["measurement_plan"]["baseline_worksheet_ids"]
    assert program["measurement_plan"]["post_worksheet_ids"]
    assert program["measurement_plan"]["status"] == "draft_requires_research_review"
    assert program["protocol_version"] == "2026.07-task17-v1"
    assert len(program["measurement_plan"]["measurement_points"]) == 4
    assert all(item["status"] == "pending" for item in program["approval"].values())
    assert "不构成诊断" in program["boundary_notice"]


def test_courses_return_structured_units_and_pathway(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()

    list_response = client.get("/api/courses")
    assert list_response.status_code == 200
    data = list_response.get_json()["data"]
    assert len(data["items"]) == 5
    assert len(data["pathways"][0]["nodes"]) == 6
    assert all(item["learning_objectives"] for item in data["items"])

    detail_response = client.get("/api/courses/understand_child_emotion")
    assert detail_response.status_code == 200
    course = detail_response.get_json()["data"]["course"]
    assert course["review_status"] == "draft_requires_psychology_review"
    assert course["knowledge_checks"]
    assert course["guided_practice"]["card_id"] == "emotion_naming"

    pathway_response = client.get("/api/courses/pathways")
    assert pathway_response.status_code == 200
    assert pathway_response.get_json()["data"]["items"][0]["excluded_from_automatic_release"]


def test_course_progress_binds_content_version_and_requires_real_attempt(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    _user_id, token = _wechat_login(client, "course-progress-user")

    response = client.post(
        "/api/courses/understand_child_emotion/progress",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "status": "completed",
            "completed_section_count": 3,
            "knowledge_check_completed_ids": ["emotion_fact_check"],
            "transfer_task_status": "planned",
            "linked_card_id": "emotion_naming",
        },
    )
    assert response.status_code == 201
    progress = response.get_json()["data"]["progress"]
    assert progress["course_version"] == "2026.07-task17-course-v2"
    assert progress["status"] == "completed"
    assert "不代表掌握" in progress["completion_note"]

    restored = client.get(
        "/api/courses/understand_child_emotion/progress",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert restored.status_code == 200
    assert restored.get_json()["data"]["progress"]["linked_card_id"] == "emotion_naming"

    invalid = client.post(
        "/api/courses/understand_child_emotion/progress",
        headers={"Authorization": f"Bearer {token}"},
        json={"status": "completed", "completed_section_count": 3, "knowledge_check_completed_ids": ["missing"]},
    )
    assert invalid.status_code == 400
    assert invalid.get_json()["error"]["code"] == "invalid_knowledge_check"

    malformed = client.post(
        "/api/courses/understand_child_emotion/progress",
        headers={"Authorization": f"Bearer {token}"},
        json={"status": "completed", "completed_section_count": "not-a-number", "knowledge_check_completed_ids": []},
    )
    assert malformed.status_code == 400
    assert malformed.get_json()["error"]["code"] == "invalid_completed_section_count"


def test_training_plan_prompts_when_no_assessment(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    _user_id, token = _wechat_login(client, "no-assessment-user")

    response = client.get("/api/training-plan", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    data = response.get_json()["data"]
    assert data["has_assessment"] is False
    assert data["plan_items"] == []
    assert data["next_action"]["url"] == "/pages/assessment/index"


def test_training_plan_uses_latest_assessment_recommendation(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    user_id, token = _wechat_login(client, "training-plan-user")

    create_response = client.post(
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
    assert create_response.status_code == 201

    response = client.get(
        f"/api/training-plan?user_id={user_id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.get_json()["data"]
    assert data["has_assessment"] is True
    assert data["plan_items"]
    assert data["plan_items"][0]["cards"]
    assert "不构成" in data["boundary_notice"]


def test_training_plan_assignment_persists_and_is_private(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    user_id, token = _wechat_login(client, "training-assignment-user")
    _other_id, other_token = _wechat_login(client, "training-assignment-other")

    saved = client.post(
        "/api/training-plan/assignment",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "phase": "practice",
            "cadence": "every_other_day",
            "status": "active",
            "start_date": "2026-07-11",
            "goal_text": "先稳定完成一张卡，再逐步增加练习。",
        },
    )
    assert saved.status_code == 200
    assignment = saved.get_json()["data"]
    assert assignment["user_id"] == user_id
    assert assignment["phase"] == "practice"
    assert assignment["agreement_status"] == "self_selected"

    plan = client.get("/api/training-plan", headers={"Authorization": f"Bearer {token}"})
    assert plan.status_code == 200
    assert plan.get_json()["data"]["assignment"]["cadence"] == "every_other_day"

    other_plan = client.get("/api/training-plan", headers={"Authorization": f"Bearer {other_token}"})
    assert other_plan.status_code == 200
    assert other_plan.get_json()["data"]["assignment"] is None

    with app.app_context():
        from database import get_connection, json_loads

        with get_connection() as conn:
            row = conn.execute(
                "SELECT metadata_json FROM audit_logs WHERE action = 'training_plan_assignment_saved'"
            ).fetchone()
        metadata = json_loads(row["metadata_json"], {})
        assert metadata["has_goal_text"] is True
        assert "先稳定" not in row["metadata_json"]


def test_training_plan_assignment_drives_due_state_and_next_date(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    _user_id, token = _wechat_login(client, "training-cadence-due")
    from services.training_schedule_service import current_local_day

    today = current_local_day()
    saved = client.post(
        "/api/training-plan/assignment",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "phase": "practice",
            "cadence": "daily",
            "status": "active",
            "start_date": today.isoformat(),
            "goal_text": "",
        },
    )
    assert saved.status_code == 200
    assert saved.get_json()["data"]["is_due_today"] is True

    checkin = client.post(
        "/api/checkins",
        headers={"Authorization": f"Bearer {token}"},
        json={"card_id": "three_second_pause", "status": "completed"},
    )
    assert checkin.status_code == 201

    plan = client.get("/api/training-plan", headers={"Authorization": f"Bearer {token}"})
    assert plan.status_code == 200
    assignment = plan.get_json()["data"]["assignment"]
    assert assignment["is_due_today"] is False
    assert assignment["next_practice_date"] == (today + timedelta(days=1)).isoformat()


def test_training_plan_assignment_rejects_invalid_values_without_writing(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    user_id, token = _wechat_login(client, "training-assignment-invalid")

    response = client.post(
        "/api/training-plan/assignment",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "phase": "diagnostic_phase",
            "cadence": "daily",
            "start_date": "2026-07-11",
        },
    )
    assert response.status_code == 400
    assert response.get_json()["error"]["code"] == "invalid_training_phase"

    with app.app_context():
        from database import get_connection

        with get_connection() as conn:
            row = conn.execute(
                "SELECT COUNT(*) AS count FROM records WHERE user_id = ? AND module_type = 'training_plan_assignment'",
                (user_id,),
            ).fetchone()
    assert row["count"] == 0
