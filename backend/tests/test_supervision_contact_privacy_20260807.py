import importlib
import sys
from pathlib import Path

from werkzeug.security import generate_password_hash


ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"


def _fresh_app(tmp_path, monkeypatch):
    sys.path.insert(0, str(BACKEND))
    for name in list(sys.modules):
        if name in {"app", "config", "database", "models"} or name.startswith("routes.") or name.startswith("services."):
            sys.modules.pop(name, None)
    monkeypatch.setenv("APP_ENV", "testing")
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "supervision-contact.sqlite3"))
    monkeypatch.setenv("CONTENT_DIR", str(ROOT / "content"))
    monkeypatch.setenv("DB_PROVIDER", "sqlite")
    monkeypatch.setenv("SECRET_KEY", "supervision-contact-privacy-secret-key")
    monkeypatch.setenv("ADMIN_EXPORT_TOKEN", "legacy-admin-token")
    monkeypatch.setenv("LEGACY_ADMIN_TOKEN_ENABLED", "0")
    return importlib.import_module("app").app


def _register(client, username, role="parent"):
    response = client.post(
        "/api/auth/register",
        json={
            "username": username,
            "password": "StrongPass123!",
            "role": role,
            "nickname": username,
        },
    )
    assert response.status_code == 201, response.get_json()
    return response.get_json()["data"]


def _headers(token):
    return {"Authorization": f"Bearer {token}"}


def _promote(app, user_id, role):
    with app.app_context():
        from database import get_connection

        with get_connection() as conn:
            conn.execute(
                "UPDATE users SET role = ?, password_hash = ? WHERE id = ?",
                (role, generate_password_hash("StrongPass123!"), user_id),
            )
            conn.commit()


def test_state_transitions_do_not_implicitly_disclose_contact(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    participant = _register(client, "contact-participant")
    reviewer = _register(client, "contact-reviewer")
    reviewer_id = reviewer["user"]["id"]
    _promote(app, reviewer_id, "supervisor")

    created = client.post(
        "/api/supervision",
        headers=_headers(participant["token"]),
        json={
            "message": "需要和老师确认后续支持安排。",
            "contact": "13800138000",
        },
    )
    assert created.status_code == 201
    request_id = created.get_json()["data"]["id"]
    reviewer_headers = _headers(reviewer["token"])

    explicit_read = client.get(
        f"/api/supervision/{request_id}/reviewer",
        headers=reviewer_headers,
    )
    assert explicit_read.status_code == 200
    assert explicit_read.get_json()["data"]["contact"] == "13800138000"

    acknowledged = client.post(
        f"/api/supervision/{request_id}/acknowledge",
        headers=reviewer_headers,
        json={},
    )
    assert acknowledged.status_code == 200
    acknowledged_data = acknowledged.get_json()["data"]
    assert "contact" not in acknowledged_data
    assert acknowledged_data["contact_masked"] == "138****8000"

    replied = client.post(
        f"/api/supervision/{request_id}/reply",
        headers=reviewer_headers,
        json={"reply": "已收到，将按支持流程继续处理。"},
    )
    assert replied.status_code == 200
    replied_data = replied.get_json()["data"]
    assert "contact" not in replied_data
    assert replied_data["contact_masked"] == "138****8000"

    resolved = client.post(
        f"/api/supervision/{request_id}/resolve",
        headers=reviewer_headers,
        json={"resolution_code": "support_completed"},
    )
    assert resolved.status_code == 200
    resolved_data = resolved.get_json()["data"]
    assert "contact" not in resolved_data
    assert resolved_data["contact_masked"] == "138****8000"

    with app.app_context():
        from database import get_connection

        with get_connection() as conn:
            raw_contact_reads = conn.execute(
                """
                SELECT COUNT(*) AS count
                FROM audit_logs
                WHERE action = 'supervision_sensitive_contact_viewed'
                  AND target_id = ?
                """,
                (request_id,),
            ).fetchone()["count"]

    assert raw_contact_reads == 1
