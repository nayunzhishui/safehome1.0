import importlib
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"


def _fresh_app(tmp_path, monkeypatch):
    sys.path.insert(0, str(BACKEND))
    for name in list(sys.modules):
        if name in {"app", "config", "database", "models"} or name.startswith(("routes.", "services.")):
            sys.modules.pop(name, None)
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("DB_PROVIDER", "sqlite")
    monkeypatch.setenv("ALLOW_PRODUCTION_SQLITE", "1")
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "rc0810-f06.sqlite3"))
    monkeypatch.setenv("CONTENT_DIR", str(ROOT / "content"))
    monkeypatch.setenv("SECRET_KEY", "rc0810-f06-production-secret-key")
    monkeypatch.setenv("ADMIN_EXPORT_TOKEN", "rc0810-f06-admin-token")
    return importlib.import_module("app").app


def _seed_scope(app):
    with app.app_context():
        from database import get_connection, now_iso
        from routes.auth_utils import generate_auth_token

        timestamp = now_iso()
        with get_connection() as conn:
            for actor_id, role in {
                "participant-a": "parent",
                "participant-b": "parent",
                "researcher-a": "researcher",
            }.items():
                conn.execute(
                    "INSERT INTO users (id, nickname, role, status, created_at, updated_at) "
                    "VALUES (?, ?, ?, 'active', ?, ?)",
                    (actor_id, actor_id, role, timestamp, timestamp),
                )
            for suffix, user_id in (("a", "participant-a"), ("b", "participant-b")):
                conn.execute(
                    """
                    INSERT INTO relationship_pilot_enrollments (
                        id, user_id, assessment_result_id, worksheet_id, dimensions_json,
                        radar_features_json, profile_json, consent_scope, status,
                        review_status, created_at, updated_at
                    ) VALUES (?, ?, ?, 'regulatory_focus_relationship_18', '[]', '[]', '{}',
                              'relationship_pilot_stage2_v1', 'enrolled', 'pending_review', ?, ?)
                    """,
                    (f"enrollment-{suffix}", user_id, f"result-{suffix}", timestamp, timestamp),
                )
                conn.execute(
                    """
                    INSERT INTO emotion_diaries (
                        id, user_id, scene, event_description, parent_emotion,
                        parent_emotion_intensity, created_at, updated_at
                    ) VALUES (?, ?, '沟通', ?, '担心', 4, ?, ?)
                    """,
                    (f"diary-{suffix}", user_id, f"{user_id} 的记录", timestamp, timestamp),
                )
            conn.commit()
        token = generate_auth_token({"id": "researcher-a", "role": "researcher"})
        return {"Authorization": f"Bearer {token}"}, timestamp


def _assign(app, timestamp):
    with app.app_context():
        from database import get_connection

        with get_connection() as conn:
            conn.execute(
                """
                INSERT INTO research_scope_assignments (
                    id, enrollment_id, actor_id, assignment_role, status, version,
                    idempotency_key, assigned_by, created_at, updated_at
                ) VALUES ('scope-a', 'enrollment-a', 'researcher-a', 'researcher',
                          'active', 1, 'scope-a', 'admin-a', ?, ?)
                """,
                (timestamp, timestamp),
            )
            conn.commit()


def test_researcher_needs_active_assignment_for_participant_diary_target(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    headers, timestamp = _seed_scope(app)
    client = app.test_client()

    unassigned = client.get("/api/diaries?user_id=participant-a", headers=headers)
    assert unassigned.status_code == 403
    assert unassigned.get_json()["error"]["code"] == "forbidden"

    _assign(app, timestamp)
    assigned = client.get("/api/diaries?user_id=participant-a", headers=headers)
    assert assigned.status_code == 200
    assert [item["id"] for item in assigned.get_json()["data"]["items"]] == ["diary-a"]

    still_unassigned = client.get("/api/diaries?user_id=participant-b", headers=headers)
    assert still_unassigned.status_code == 403
    assert still_unassigned.get_json()["error"]["code"] == "forbidden"


def test_assignment_does_not_allow_researcher_to_impersonate_participant_writes(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    headers, timestamp = _seed_scope(app)
    _assign(app, timestamp)
    client = app.test_client()

    response = client.post(
        "/api/diaries",
        headers=headers,
        json={
            "user_id": "participant-a",
            "scene": "沟通",
            "event_description": "研究者不能代参与者新增日记",
            "parent_emotion": "担心",
        },
    )

    assert response.status_code == 403
    assert response.get_json()["error"]["code"] == "forbidden"
