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
    return data["user"]["id"], data["token"]


def _headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_delete_request_reuses_active_request_and_owner_can_list_status(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    user_id, token = _login(client, "privacy-status-owner")
    headers = _headers(token)

    first = client.post("/api/privacy/delete-my-data", headers=headers, json={"reason": "不再使用"})
    replay = client.post("/api/privacy/delete-my-data", headers=headers, json={"reason": "再次提交"})
    listed = client.get("/api/privacy/requests?page=1&page_size=10", headers=headers)

    assert first.status_code == 201
    assert replay.status_code == 200
    assert replay.get_json()["data"]["id"] == first.get_json()["data"]["id"]
    assert replay.get_json()["data"]["already_active"] is True
    data = listed.get_json()["data"]
    assert data["page"] == 1 and data["page_size"] == 10
    assert data["total"] == 1 and data["has_more"] is False
    assert data["items"][0]["user_id"] == user_id
    assert data["items"][0]["status"] == "pending"


def test_privacy_request_list_rejects_cross_user_query_with_request_id(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    _owner_id, owner_token = _login(client, "privacy-status-a")
    other_id, _other_token = _login(client, "privacy-status-b")

    response = client.get(
        f"/api/privacy/requests?user_id={other_id}",
        headers={**_headers(owner_token), "X-Request-ID": "privacy-contract-001"},
    )

    assert response.status_code == 403
    body = response.get_json()
    assert body["error"]["code"] == "forbidden"
    assert body["request_id"] == "privacy-contract-001"


def test_research_queue_is_paginated_minimal_and_assignment_scoped(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    assigned_user, _assigned_token = _login(client, "queue-participant-assigned")
    other_user, _other_token = _login(client, "queue-participant-other")
    researcher_id, researcher_token = _login(client, "queue-researcher")
    participant_id, participant_token = _login(client, "queue-plain-participant")

    with app.app_context():
        from database import get_connection, now_iso

        with get_connection() as conn:
            conn.execute("UPDATE users SET role = 'researcher' WHERE id = ?", (researcher_id,))
            conn.execute(
                """
                INSERT INTO relationship_pilot_enrollments (
                    id, user_id, assessment_result_id, worksheet_id, dimensions_json,
                    radar_features_json, profile_json, consent_scope, assigned_researcher_id,
                    status, review_status, created_at, updated_at
                ) VALUES ('queue-enrollment', ?, 'assessment-q', 'worksheet-q', '[]', '[]', '{}',
                          'feedback_review', ?, 'enrolled', 'pending_review', ?, ?)
                """,
                (assigned_user, researcher_id, now_iso(), now_iso()),
            )
            for index, user_id in enumerate([assigned_user, assigned_user, other_user]):
                conn.execute(
                    """
                    INSERT INTO supervision_requests (
                        id, user_id, message, risk_level, status, created_at
                    ) VALUES (?, ?, ?, 'low', 'pending', ?)
                    """,
                    (f"queue-supervision-{index}", user_id, f"PRIVATE-{index}", now_iso()),
                )
            conn.commit()

    first_page = client.get(
        "/api/research/queues?queue=supervision&page=1&page_size=1",
        headers=_headers(researcher_token),
    )
    participant_denied = client.get("/api/research/queues?queue=supervision", headers=_headers(participant_token))

    assert first_page.status_code == 200
    data = first_page.get_json()["data"]
    assert data["total"] == 2 and data["has_more"] is True
    assert len(data["items"]) == 1
    assert data["items"][0]["user_id"] == assigned_user
    assert isinstance(data["items"][0]["wait_minutes"], int)
    assert data["items"][0]["wait_minutes"] >= 0
    body = first_page.get_data(as_text=True)
    assert "PRIVATE" not in body and "message" not in data["items"][0]
    assert participant_denied.status_code == 403
    assert participant_id != researcher_id


def test_research_queue_validates_enum_and_pagination_contract(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    researcher_id, token = _login(client, "queue-contract-researcher")
    with app.app_context():
        from database import get_connection

        with get_connection() as conn:
            conn.execute("UPDATE users SET role = 'researcher' WHERE id = ?", (researcher_id,))
            conn.commit()

    response = client.get("/api/research/queues?queue=unknown&page=0&page_size=500", headers=_headers(token))

    assert response.status_code == 400
    body = response.get_json()
    assert body["error"]["code"] == "validation_error"
    assert body["request_id"]
