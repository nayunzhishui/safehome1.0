import importlib
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = PROJECT_ROOT / "backend"
MINIPROGRAM_ROOT = PROJECT_ROOT / "apps" / "miniprogram"


def _fresh_app(tmp_path, monkeypatch):
    sys.path.insert(0, str(BACKEND_ROOT))
    for name in list(sys.modules):
        if name in {"app", "config", "database", "models"} or name.startswith("routes.") or name.startswith("services."):
            sys.modules.pop(name, None)
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.delenv("WECHAT_APPID", raising=False)
    monkeypatch.delenv("WECHAT_SECRET", raising=False)
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "safehome-test.sqlite3"))
    monkeypatch.setenv("CONTENT_DIR", str(PROJECT_ROOT / "content"))
    module = importlib.import_module("app")
    return module.app


def test_wechat_login_dev_fallback_creates_parent_user(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()

    response = client.post("/api/auth/wechat-login", json={"code": "dev-code-1", "nickname": "微信家长"})

    assert response.status_code == 200
    data = response.get_json()["data"]
    assert data["token"]
    assert data["dev_fallback"] is True
    assert data["user"]["role"] == "parent"
    assert data["user"]["nickname"] == "微信家长"


def test_profile_stats_and_messages_flow(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()

    from database import get_connection
    from services.message_service import create_message

    with get_connection() as conn:
        message = create_message(conn, "demo-parent", title="老师补充反馈已更新", body="请查看补充说明。")
        conn.commit()

    stats_response = client.get("/api/profile/stats?user_id=demo-parent")
    assert stats_response.status_code == 200
    stats = stats_response.get_json()["data"]
    assert stats["unread_message_count"] == 1
    assert "诊断" in stats["boundary_notice"]

    anonymous_response = client.get("/api/messages?user_id=demo-parent")
    assert anonymous_response.status_code == 401

    login_response = client.post("/api/auth/wechat-login", json={"code": "message-owner-code", "nickname": "消息用户"})
    token = login_response.get_json()["data"]["token"]
    user_id = login_response.get_json()["data"]["user"]["id"]
    with get_connection() as conn:
        owner_message = create_message(conn, user_id, title="给登录用户的消息", body="只允许本人查看。")
        conn.commit()

    list_response = client.get(f"/api/messages?user_id={user_id}", headers={"Authorization": f"Bearer {token}"})
    assert list_response.status_code == 200
    listed = list_response.get_json()["data"]
    assert listed["unread_count"] == 1
    assert listed["items"][0]["id"] == owner_message["id"]

    cross_user_response = client.get("/api/messages?user_id=demo-parent", headers={"Authorization": f"Bearer {token}"})
    assert cross_user_response.status_code == 200
    cross_user_data = cross_user_response.get_json()["data"]
    assert [item["id"] for item in cross_user_data["items"]] == [owner_message["id"]]
    assert message["id"] not in {item["id"] for item in cross_user_data["items"]}

    detail_response = client.get(f"/api/messages/{owner_message['id']}?user_id={user_id}", headers={"Authorization": f"Bearer {token}"})
    assert detail_response.status_code == 200
    assert detail_response.get_json()["data"]["status"] == "read"


def test_miniprogram_message_list_uses_cloudbase_safe_page_size_parameter():
    page = (MINIPROGRAM_ROOT / "pages/messages/index.js").read_text(encoding="utf-8")

    assert "page_size: 50" in page
    assert "limit: 50" not in page


def test_admin_worksheet_crud_and_assessment_results_endpoint(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    headers = {"X-Admin-Token": "safehome-local-admin-token"}

    blocked_create = client.post(
        "/api/admin/worksheets",
        headers=headers,
        json={
            "id": "blocked_open_scale",
            "display_title": "不应直接开放的量表",
            "enabled_for_user": True,
        },
    )
    assert blocked_create.status_code == 400
    assert blocked_create.get_json()["error"]["code"] == "review_required"

    create_response = client.post(
        "/api/admin/worksheets",
        headers=headers,
        json={
            "id": "admin_test_scale",
            "display_title": "后台测试量表",
            "source_title": "后台测试量表",
            "category": "支持性测评",
            "enabled_for_user": False,
            "review_status": "pilot_review_required",
            "profile_model_id": "test_profile_model",
            "questions": [],
            "sections": [],
            "recommended_card_ids": ["emotion_naming_parent"],
            "boundary_notice": "只用于支持性自我理解，不用于诊断。",
            "result_disclaimer": "不替代专业咨询。",
        },
    )
    assert create_response.status_code == 201
    created = create_response.get_json()["data"]
    assert created["profile_model_id"] == "test_profile_model"
    assert created["enabled_for_user"] is False

    direct_enable_response = client.put(
        "/api/admin/worksheets/admin_test_scale",
        headers=headers,
        json={"enabled_for_user": True},
    )
    assert direct_enable_response.status_code == 400
    assert direct_enable_response.get_json()["error"]["code"] == "review_required"

    update_response = client.put(
        "/api/admin/worksheets/admin_test_scale",
        headers=headers,
        json={"display_title": "后台测试量表已更新", "enabled_for_user": False},
    )
    assert update_response.status_code == 200
    updated = update_response.get_json()["data"]
    assert updated["display_title"] == "后台测试量表已更新"
    assert updated["enabled_for_user"] is False

    delete_response = client.delete("/api/admin/worksheets/admin_test_scale", headers=headers)
    assert delete_response.status_code == 200
    disabled = delete_response.get_json()["data"]
    assert disabled["enabled_for_user"] is False
    assert disabled["review_status"] == "disabled"

    results_response = client.get("/api/admin/assessment-results", headers=headers)
    assert results_response.status_code == 200
    body = results_response.get_json()["data"]
    assert "items" in body
    assert "count" in body


def test_hidden_admin_worksheet_is_not_visible_or_submittable_to_users(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    headers = {"X-Admin-Token": "safehome-local-admin-token"}

    response = client.post(
        "/api/admin/worksheets",
        headers=headers,
        json={
            "id": "hidden_test_scale",
            "display_title": "隐藏测试量表",
            "source_title": "隐藏测试量表",
            "category": "支持性测评",
            "questions": [{"id": "q1", "prompt": "测试题", "options": [{"value": "1", "score": 1}]}],
            "sections": [],
            "boundary_notice": "只用于测试。",
            "result_disclaimer": "不替代专业咨询。",
        },
    )
    assert response.status_code == 201
    assert response.get_json()["data"]["enabled_for_user"] is False

    list_response = client.get("/api/assessments")
    ids = [item["id"] for item in list_response.get_json()["data"]["items"]]
    assert "hidden_test_scale" not in ids

    detail_response = client.get("/api/assessments/hidden_test_scale")
    assert detail_response.status_code == 404

    login_response = client.post("/api/auth/wechat-login", json={"code": "hidden-submit-user"})
    token = login_response.get_json()["data"]["token"]

    submit_response = client.post(
        "/api/assessment-results",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "user_id": "hidden-submit-user",
            "worksheet_id": "hidden_test_scale",
            "answers": [{"question_id": "q1", "prompt": "测试题", "value": "1", "score": 1}],
        },
    )
    assert submit_response.status_code == 400
    assert submit_response.get_json()["error"]["code"] == "assessment_not_enabled"
