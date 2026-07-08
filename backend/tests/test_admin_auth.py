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


def _create_high_risk_feedback(client):
    response = client.post(
        "/api/feedback/generate",
        json={
            "user_id": "parent-admin-auth",
            "event_description": "我不想活了，感觉撑不下去。",
            "behavior": "一直哭",
        },
    )
    assert response.status_code == 201
    return response.get_json()["data"]["id"]


def _create_profile(client):
    response = client.post(
        "/api/profile",
        json={
            "user_id": "student-admin-auth",
            "scores": {
                "test_anxiety": 4.2,
                "iu_score": 4.1,
                "f_score": 2.8,
                "self_compassion": 2.7,
            },
            "free_text": "考试前会担心，但愿意先做一次情绪命名练习。",
        },
    )
    assert response.status_code == 201
    return response.get_json()["data"]["student_profile_id"]


def _wechat_login(client, code: str):
    response = client.post("/api/auth/wechat-login", json={"code": code, "nickname": code})
    assert response.status_code == 200
    data = response.get_json()["data"]
    return data["user"]["id"], data["token"]


def test_risk_review_list_requires_admin_token(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()

    no_token = client.get("/api/risk-review")
    wrong_token = client.get("/api/risk-review", headers={"X-Admin-Token": "wrong-token"})
    ok_response = client.get("/api/risk-review", headers=ADMIN_HEADERS)

    assert no_token.status_code == 401
    assert wrong_token.status_code == 401
    assert ok_response.status_code == 200


def test_risk_review_update_requires_admin_token(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()

    feedback_id = _create_high_risk_feedback(client)
    list_response = client.get("/api/risk-review?status=pending", headers=ADMIN_HEADERS)
    review = next(item for item in list_response.get_json()["data"]["items"] if item["source_id"] == feedback_id)

    no_token = client.post(
        f"/api/risk-review/{review['id']}/review",
        json={"review_status": "reviewed", "review_note": "已查看。"},
    )
    ok_response = client.post(
        f"/api/risk-review/{review['id']}/review",
        json={"review_status": "reviewed", "review_note": "已查看。"},
        headers=ADMIN_HEADERS,
    )

    assert no_token.status_code == 401
    assert ok_response.status_code == 200
    assert ok_response.get_json()["data"]["reviewer_id"] == "admin-token"


def test_profile_results_list_requires_admin_token(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    _create_profile(client)

    no_token = client.get("/api/profile-results")
    ok_response = client.get("/api/profile-results", headers=ADMIN_HEADERS)

    assert no_token.status_code == 401
    assert ok_response.status_code == 200


def test_profile_review_endpoints_require_admin_token(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    profile_id = _create_profile(client)

    no_token_list = client.get(f"/api/profile-results/{profile_id}/reviews")
    ok_list = client.get(f"/api/profile-results/{profile_id}/reviews", headers=ADMIN_HEADERS)
    no_token_post = client.post(
        f"/api/profile-results/{profile_id}/review",
        json={"review_decision": "建议继续观察。"},
    )
    ok_post = client.post(
        f"/api/profile-results/{profile_id}/review",
        json={"review_decision": "建议继续观察。"},
        headers=ADMIN_HEADERS,
    )

    assert no_token_list.status_code == 401
    assert ok_list.status_code == 200
    assert no_token_post.status_code == 401
    assert ok_post.status_code == 201
    assert ok_post.get_json()["data"]["reviewer_id"] == "admin-token"


def test_diary_admin_list_can_read_all_users_without_user_filter(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    owner_a_id, owner_a_token = _wechat_login(client, "parent-a")
    owner_b_id, owner_b_token = _wechat_login(client, "parent-b")

    for user_id, token in [(owner_a_id, owner_a_token), (owner_b_id, owner_b_token)]:
        response = client.post(
            "/api/diaries",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "user_id": user_id,
                "scene": "作业拖延",
                "event_description": f"{user_id} 的记录",
                "parent_emotion": "着急",
            },
        )
        assert response.status_code == 201

    owner_response = client.get(
        f"/api/diaries?user_id={owner_a_id}",
        headers={"Authorization": f"Bearer {owner_a_token}"},
    )
    admin_response = client.get("/api/diaries?limit=10", headers=ADMIN_HEADERS)
    wrong_token = client.get("/api/diaries?limit=10", headers={"X-Admin-Token": "wrong-token"})

    assert owner_response.status_code == 200
    assert len(owner_response.get_json()["data"]["items"]) == 1
    assert admin_response.status_code == 200
    assert len(admin_response.get_json()["data"]["items"]) == 2
    assert wrong_token.status_code == 401

    import database

    with database.get_connection() as conn:
        row = conn.execute(
            """
            SELECT * FROM audit_logs
            WHERE action = 'list_diaries_admin'
            ORDER BY created_at DESC
            LIMIT 1
            """
        ).fetchone()

    assert row is not None
    assert row["actor_id"] == "admin-token"
    metadata = json.loads(row["metadata_json"])
    assert metadata["route"] == "/api/diaries"
    assert metadata["row_count"] == 2
    assert metadata["limit"] == 10
