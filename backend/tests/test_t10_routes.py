import importlib
import json
import os
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = PROJECT_ROOT / "backend"


def _fresh_app(tmp_path, monkeypatch, app_env: str = "development"):
    sys.path.insert(0, str(BACKEND_ROOT))
    for name in list(sys.modules):
        if name in {"app", "config", "database", "models"} or name.startswith("routes.") or name.startswith("services."):
            sys.modules.pop(name, None)
    monkeypatch.setenv("APP_ENV", app_env)
    monkeypatch.delenv("WECHAT_APPID", raising=False)
    monkeypatch.delenv("WECHAT_SECRET", raising=False)
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "safehome-test.sqlite3"))
    monkeypatch.setenv("CONTENT_DIR", str(PROJECT_ROOT / "content"))
    if app_env == "production":
        monkeypatch.setenv("DB_PROVIDER", "sqlite")
        monkeypatch.setenv("ALLOW_PRODUCTION_SQLITE", "1")
        monkeypatch.setenv("SECRET_KEY", "production-test-secret-key-32-chars")
        monkeypatch.setenv("ADMIN_EXPORT_TOKEN", "production-test-token")
    module = importlib.import_module("app")
    return module.app


def _wechat_login(client, code: str):
    response = client.post("/api/auth/wechat-login", json={"code": code, "nickname": code})
    assert response.status_code == 200
    data = response.get_json()["data"]
    return data["user"]["id"], data["token"]


def test_private_assessment_results_use_token_owner_before_user_id(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()

    owner_id, owner_token = _wechat_login(client, "owner-code")
    other_id, other_token = _wechat_login(client, "other-code")

    create_response = client.post(
        "/api/assessment-results",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={
            "user_id": "spoofed-user-id",
            "worksheet_id": "student_profile_v1",
            "answers": [
                {"question_id": question_id, "value": "1"}
                for question_id in ["test_anxiety", "iu_score", "fear_score", "self_compassion"]
            ],
        },
    )
    assert create_response.status_code == 201
    result = create_response.get_json()["data"]
    assert result["user_id"] == owner_id

    other_list = client.get(
        f"/api/assessment-results?user_id={owner_id}",
        headers={"Authorization": f"Bearer {other_token}"},
    )
    assert other_list.status_code == 200
    assert other_list.get_json()["data"]["items"] == []

    other_position = client.get(
        f"/api/assessment-results/{result['id']}/profile-position?user_id={owner_id}",
        headers={"Authorization": f"Bearer {other_token}"},
    )
    assert other_position.status_code == 404
    assert other_id != owner_id


def test_progress_summary_requires_login_in_production_and_keeps_boundary(tmp_path, monkeypatch):
    production_app = _fresh_app(tmp_path, monkeypatch, "production")
    production_client = production_app.test_client()

    blocked = production_client.get("/api/progress-summary?user_id=someone")
    assert blocked.status_code == 401

    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    user_id, token = _wechat_login(client, "summary-code")
    response = client.get(
        f"/api/progress-summary?user_id={user_id}&range=7d",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.get_json()["data"]
    assert data["user_id"] == user_id
    assert "诊断" in data["boundary_notice"]
    assert data["stability_status"] in {"insufficient", "fluctuating", "converging", "stable", "low_confidence"}


def test_auth_error_response_preserves_validation_error_code(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    auth_utils = importlib.import_module("routes.auth_utils")

    with app.test_request_context("/api/example"):
        response, status = auth_utils.auth_error_response(
            auth_utils.AuthError("后台查询需要指定 user_id", status=400)
        )

    assert status == 400
    assert response.get_json()["error"]["code"] == "validation_error"


def test_emotion_thermometer_accepts_lightweight_dimensions(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    user_id, token = _wechat_login(client, "thermo-code")

    create_response = client.post(
        "/api/emotion-thermometer",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "user_id": "spoofed",
            "intensity_level": 7,
            "valence_level": 3,
            "arousal_level": 8,
            "control_level": 4,
            "emotion_label": "着急",
            "brief_text": "孩子还没开始写作业",
            "created_at": "2026-07-05T09:00:00+00:00",
        },
    )
    assert create_response.status_code == 201
    created = create_response.get_json()["data"]
    assert created["user_id"] == user_id
    assert created["valence_level"] == 3
    assert created["emotion_label"] == "着急"

    day_response = client.get(
        "/api/emotion-thermometer/day?date=2026-07-05",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert day_response.status_code == 200
    summary = day_response.get_json()["data"]["summary"]
    assert summary["valence_avg"] == 3
    assert summary["arousal_avg"] == 8
    assert summary["control_avg"] == 4


def test_weekly_report_includes_assessment_and_thermometer_summary(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    user_id, token = _wechat_login(client, "weekly-code")

    assessment_response = client.post(
        "/api/assessment-results",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "worksheet_id": "self_compassion_scs_cn",
            "created_at": "2026-07-06T08:00:00+00:00",
            "answers": [
                {
                    "question_id": question["id"],
                    "value": next(
                        (
                            option["value"]
                            for option in question["options"]
                            if str(option.get("value")) == "3"
                        ),
                        question["options"][0]["value"],
                    ),
                }
                for question in client.get("/api/assessments/self_compassion_scs_cn").get_json()["data"]["questions"]
            ],
        },
    )
    assert assessment_response.status_code == 201

    for level, created_at in [(8, "2026-07-06T09:00:00+00:00"), (5, "2026-07-06T10:00:00+00:00")]:
        response = client.post(
            "/api/emotion-thermometer",
            headers={"Authorization": f"Bearer {token}"},
            json={"intensity_level": level, "created_at": created_at},
        )
        assert response.status_code == 201

    report_response = client.get(
        f"/api/weekly-report?user_id={user_id}&week_start=2026-07-06",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert report_response.status_code == 200
    report = report_response.get_json()["data"]
    assert report["assessment_trend"]["assessment_count"] == 1
    assert report["assessment_trend"]["worksheet_names"]
    assert report["thermometer_trend"]["record_count"] == 2
    assert "诊断" not in report["thermometer_trend"]["trend_text"]


def test_bind_phone_requires_login_and_reports_missing_wechat_config(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()

    unauthenticated = client.post("/api/auth/bind-phone", json={"code": "phone-code"})
    assert unauthenticated.status_code == 401

    _, token = _wechat_login(client, "phone-bind-code")
    response = client.post(
        "/api/auth/bind-phone",
        headers={"Authorization": f"Bearer {token}"},
        json={"code": "phone-code"},
    )
    assert response.status_code == 503
    body = response.get_json()
    assert body["error"]["code"] == "wechat_phone_config_missing"


def test_program_entry_creates_private_record(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    user_id, token = _wechat_login(client, "program-entry-code")

    response = client.post(
        "/api/programs/self_compassion_exam_anxiety/entries",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "session_no": 1,
            "answers": {"练习前": "我先停一下"},
            "reflection": "今天先做一个小步骤",
            "analysis_consent": True,
        },
    )
    assert response.status_code == 201
    created = response.get_json()["data"]["record"]
    assert created["user_id"] == user_id
    assert created["module_type"] == "program_entry"
    assert created["source_id"] == "self_compassion_exam_anxiety"


def test_checkin_effectiveness_and_progress_endpoints(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    user_id, token = _wechat_login(client, "effectiveness-code")

    response = client.post(
        "/api/checkins",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "user_id": "spoofed",
            "card_id": "three_second_pause",
            "status": "completed",
            "emotion_before": 8,
            "emotion_after": 5,
            "helpfulness_rating": 4,
        },
    )
    assert response.status_code == 201
    created = response.get_json()["data"]
    assert created["user_id"] == user_id
    assert created["helpfulness_rating"] == "4"

    effectiveness = client.get(
        "/api/training-effectiveness?range=30d",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert effectiveness.status_code == 200
    data = effectiveness.get_json()["data"]
    assert data["user_id"] == user_id
    assert data["checkins"]["helpfulness_counts"]
    assert "诊断" in data["boundary_notice"]

    trend = client.get(
        "/api/profile-trend?range=30d",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert trend.status_code == 200
    trend_data = trend.get_json()["data"]
    assert trend_data["user_id"] == user_id
    assert "诊断" in trend_data["boundary_notice"]


def test_training_plan_includes_source_and_empty_state_fields(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    user_id, token = _wechat_login(client, "plan-field-code")

    empty_response = client.get(
        "/api/training-plan",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert empty_response.status_code == 200
    empty_data = empty_response.get_json()["data"]
    assert empty_data["empty_state"]["url"] == "/pages/assessment/index"
    assert empty_data["has_recent_checkin"] is False

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

    plan_response = client.get(
        f"/api/training-plan?user_id={user_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert plan_response.status_code == 200
    plan = plan_response.get_json()["data"]
    assert plan["has_assessment"] is True
    assert plan["plan_items"]
    item = plan["plan_items"][0]
    assert item["source_worksheet_id"] == "student_profile_v1"
    assert item["recommendation_reason"]
    assert item["next_step"]
    assert item["evidence_summary"]


def test_text_analysis_script_outputs_aggregate_without_raw_text(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    user_id, token = _wechat_login(client, "text-code")

    diary_response = client.post(
        "/api/diaries",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "scene": "作业",
            "event_description": "孩子写作业拖延，我非常着急并提醒了几次。",
            "parent_emotion": "着急",
            "parent_emotion_intensity": 8,
            "behavior": "提醒孩子开始写作业",
        },
    )
    assert diary_response.status_code == 201
    supervision_response = client.post(
        "/api/supervision",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "message": "希望老师帮我看一下这次沟通。",
        },
    )
    assert supervision_response.status_code == 201
    supervision_id = supervision_response.get_json()["data"]["id"]
    supervisor_reply = "老师补充 AlphaBeta123🙂：先把任务拆小。"
    reply_response = client.post(
        f"/api/supervision/{supervision_id}/reply",
        headers={"X-Admin-Token": "safehome-local-admin-token"},
        json={"supervisor_reply": supervisor_reply},
    )
    assert reply_response.status_code == 200

    output = tmp_path / "text_summary.json"
    env = os.environ.copy()
    env["DATABASE_PATH"] = str(tmp_path / "safehome-test.sqlite3")
    env["CONTENT_DIR"] = str(PROJECT_ROOT / "content")
    env["APP_ENV"] = "development"
    result = subprocess.run(
        [
            sys.executable,
            str(PROJECT_ROOT / "analysis" / "text_analysis" / "analyze_text_sources.py"),
            "--user-id",
            user_id,
            "--minimum-support",
            "1",
            "--output",
            str(output),
        ],
        cwd=PROJECT_ROOT,
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )
    assert "raw_text_included" in result.stdout
    data = json.loads(output.read_text(encoding="utf-8"))
    serialized = json.dumps(data, ensure_ascii=False)
    assert data["record_count"] >= 1
    assert data["source_counts"]["supervision_requests.supervisor_reply"] == 1
    assert data["raw_text_included"] is False
    assert "孩子写作业拖延" not in serialized
    assert supervisor_reply not in serialized
    assert data["sentiment_summary"]["emotion_keywords"]
    assert data["cooccurrence_network"]["nodes"]
