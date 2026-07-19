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
    assert response.status_code == 200
    return response.get_json()["data"]


def _headers(token: str, *, idempotency_key: str | None = None) -> dict:
    headers = {"Authorization": f"Bearer {token}"}
    if idempotency_key:
        headers["Idempotency-Key"] = idempotency_key
    return headers


def test_participant_can_cancel_own_pending_request_but_not_processing_request(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    owner = _login(client, "privacy-cancel-owner")
    other = _login(client, "privacy-cancel-other")

    created = client.post(
        "/api/privacy/delete-my-data",
        headers=_headers(owner["token"]),
        json={"reason": "停止使用"},
    )
    request_id = created.get_json()["data"]["id"]

    other_denied = client.post(
        f"/api/privacy/requests/{request_id}/cancel",
        headers=_headers(other["token"], idempotency_key="cancel-cross-user-001"),
        json={"reason": "无权操作"},
    )
    cancelled = client.post(
        f"/api/privacy/requests/{request_id}/cancel",
        headers=_headers(owner["token"], idempotency_key="cancel-own-request-001"),
        json={"reason": "决定继续使用"},
    )
    replay = client.post(
        f"/api/privacy/requests/{request_id}/cancel",
        headers=_headers(owner["token"], idempotency_key="cancel-own-request-001"),
        json={"reason": "重复点击"},
    )

    assert other_denied.status_code == 404
    assert cancelled.status_code == 200
    assert cancelled.get_json()["data"]["status"] == "cancelled"
    assert replay.status_code == 200
    assert replay.get_json()["data"]["already_processed"] is True


def test_supervisor_can_review_and_claim_request_while_researcher_is_denied(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    owner = _login(client, "privacy-review-owner")
    supervisor = _login(client, "privacy-review-supervisor")
    researcher = _login(client, "privacy-review-researcher")

    with app.app_context():
        from database import get_connection

        with get_connection() as conn:
            conn.execute("UPDATE users SET role = 'supervisor' WHERE id = ?", (supervisor["user"]["id"],))
            conn.execute("UPDATE users SET role = 'researcher' WHERE id = ?", (researcher["user"]["id"],))
            conn.commit()

    created = client.post(
        "/api/privacy/delete-my-data",
        headers=_headers(owner["token"]),
        json={"reason": "这段原因只允许详情页查看"},
    )
    request_id = created.get_json()["data"]["id"]

    researcher_denied = client.get(
        "/api/privacy/admin/requests",
        headers=_headers(researcher["token"]),
    )
    listed = client.get(
        "/api/privacy/admin/requests?status=pending&page=1&page_size=20",
        headers=_headers(supervisor["token"]),
    )
    detail = client.get(
        f"/api/privacy/admin/requests/{request_id}",
        headers=_headers(supervisor["token"]),
    )
    claimed = client.post(
        f"/api/privacy/admin/requests/{request_id}/transition",
        headers=_headers(supervisor["token"], idempotency_key="privacy-claim-001"),
        json={
            "action": "start_processing",
            "scope": ["participant_records", "feedback_and_training"],
            "note": "先核对保存规则",
        },
    )
    replay = client.post(
        f"/api/privacy/admin/requests/{request_id}/transition",
        headers=_headers(supervisor["token"], idempotency_key="privacy-claim-001"),
        json={
            "action": "start_processing",
            "scope": ["participant_records", "feedback_and_training"],
            "note": "重复点击",
        },
    )

    assert researcher_denied.status_code == 403
    assert listed.status_code == 200
    list_body = listed.get_json()["data"]
    assert list_body["total"] == 1
    assert "reason" not in list_body["items"][0]
    assert "handled_note" not in list_body["items"][0]
    assert detail.status_code == 200
    assert detail.get_json()["data"]["request"]["reason"] == "这段原因只允许详情页查看"
    assert claimed.status_code == 200
    assert claimed.get_json()["data"]["request"]["status"] == "processing"
    assert claimed.get_json()["data"]["request"]["handled_by"] == supervisor["user"]["id"]
    assert replay.status_code == 200
    assert replay.get_json()["data"]["already_processed"] is True

    with app.app_context():
        from database import get_connection

        with get_connection() as conn:
            actions = conn.execute("SELECT * FROM privacy_request_actions WHERE request_id = ?", (request_id,)).fetchall()
            audits = conn.execute(
                "SELECT action FROM audit_logs WHERE target_id = ? OR target_type = 'privacy_request_queue'",
                (request_id,),
            ).fetchall()
    assert len(actions) == 1
    assert actions[0]["idempotency_key"] == "privacy-claim-001"
    assert {row["action"] for row in audits} >= {
        "privacy_request_queue_viewed",
        "privacy_request_detail_viewed",
        "privacy_request_transitioned",
    }


def test_privacy_processing_blocks_cross_handler_and_completion_without_executor(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    owner = _login(client, "privacy-state-owner")
    first = _login(client, "privacy-state-first")
    second = _login(client, "privacy-state-second")

    with app.app_context():
        from database import get_connection

        with get_connection() as conn:
            conn.execute("UPDATE users SET role = 'supervisor' WHERE id IN (?, ?)", (first["user"]["id"], second["user"]["id"]))
            conn.commit()

    created = client.post("/api/privacy/delete-my-data", headers=_headers(owner["token"]), json={})
    request_id = created.get_json()["data"]["id"]
    claimed = client.post(
        f"/api/privacy/admin/requests/{request_id}/transition",
        headers=_headers(first["token"], idempotency_key="privacy-state-claim"),
        json={"action": "start_processing", "scope": ["participant_records"], "note": "核对中"},
    )
    cross_handler = client.post(
        f"/api/privacy/admin/requests/{request_id}/transition",
        headers=_headers(second["token"], idempotency_key="privacy-state-cross"),
        json={"action": "reject", "scope": [], "note": "不能跨处理人关闭"},
    )
    fake_complete = client.post(
        f"/api/privacy/admin/requests/{request_id}/transition",
        headers=_headers(first["token"], idempotency_key="privacy-state-complete"),
        json={"action": "mark_completed", "scope": [], "note": "不能人工冒充删除完成"},
    )
    rejected = client.post(
        f"/api/privacy/admin/requests/{request_id}/transition",
        headers=_headers(first["token"], idempotency_key="privacy-state-reject"),
        json={"action": "reject", "scope": [], "note": "保存规则要求暂不删除"},
    )
    participant_view = client.get("/api/privacy/requests", headers=_headers(owner["token"]))

    assert claimed.status_code == 200
    assert cross_handler.status_code == 409
    assert cross_handler.get_json()["error"]["code"] == "processing_conflict"
    assert fake_complete.status_code == 409
    assert fake_complete.get_json()["error"]["code"] == "execution_required"
    assert rejected.status_code == 200
    assert rejected.get_json()["data"]["request"]["status"] == "rejected"
    participant_item = participant_view.get_json()["data"]["items"][0]
    assert participant_item["status"] == "rejected"
    assert "handled_note" not in participant_item and "reason" not in participant_item


def test_privacy_review_validates_scope_pagination_and_required_note(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    admin = _login(client, "privacy-validation-admin")
    owner = _login(client, "privacy-validation-owner")
    with app.app_context():
        from database import get_connection

        with get_connection() as conn:
            conn.execute("UPDATE users SET role = 'admin' WHERE id = ?", (admin["user"]["id"],))
            conn.commit()
    created = client.post("/api/privacy/delete-my-data", headers=_headers(owner["token"]), json={})
    request_id = created.get_json()["data"]["id"]

    bad_page = client.get("/api/privacy/admin/requests?page=0&page_size=500", headers=_headers(admin["token"]))
    bad_scope = client.post(
        f"/api/privacy/admin/requests/{request_id}/transition",
        headers=_headers(admin["token"], idempotency_key="privacy-bad-scope"),
        json={"action": "start_processing", "scope": ["raw_database"], "note": ""},
    )
    missing_note = client.post(
        f"/api/privacy/admin/requests/{request_id}/transition",
        headers=_headers(admin["token"], idempotency_key="privacy-missing-note"),
        json={"action": "reject", "scope": [], "note": ""},
    )

    assert bad_page.status_code == 400
    assert bad_scope.status_code == 400
    assert missing_note.status_code == 400
