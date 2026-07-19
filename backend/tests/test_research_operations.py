import importlib
import os
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = PROJECT_ROOT / "backend"


def _fresh_app(tmp_path):
    sys.path.insert(0, str(BACKEND_ROOT))
    for name in list(sys.modules):
        if name in {"app", "config", "database", "models"} or name.startswith("routes.") or name.startswith("services."):
            sys.modules.pop(name, None)
    os.environ["DATABASE_PATH"] = str(tmp_path / "safehome-research-operations.sqlite3")
    os.environ["CONTENT_DIR"] = str(PROJECT_ROOT / "content")
    app = importlib.import_module("app").app
    app.config["ADMIN_EXPORT_TOKEN"] = "operations-admin-token"
    return app


def _create_researcher(client):
    response = client.post(
        "/api/auth/admin-create-account",
        headers={"X-Admin-Token": "operations-admin-token"},
        json={"username": "operations-researcher", "password": "password-123", "role": "researcher"},
    )
    assert response.status_code == 201
    researcher_id = response.get_json()["data"]["user"]["id"]
    login = client.post("/api/auth/login", json={"username": "operations-researcher", "password": "password-123"})
    token = login.get_json()["data"]["token"]
    return researcher_id, {"Authorization": f"Bearer {token}"}


def _seed_operations(researcher_id):
    database = importlib.import_module("database")
    timestamp = database.now_iso()
    with database.get_connection() as conn:
        for user_id in ["participant-assigned", "participant-other"]:
            database.ensure_user(conn, user_id, user_id)
        conn.execute(
            """
            INSERT INTO relationship_pilot_enrollments (
                id, user_id, assessment_result_id, worksheet_id, dimensions_json, radar_features_json,
                profile_json, consent_scope, assigned_researcher_id, status, review_status, created_at, updated_at
            ) VALUES ('enroll-assigned', 'participant-assigned', 'assessment-assigned', 'relationship_action_style_v1',
                      '[]', '[]', '{}', 'pilot', ?, 'enrolled', 'pending_review', ?, ?)
            """,
            (researcher_id, timestamp, timestamp),
        )
        for suffix, user_id in [("assigned", "participant-assigned"), ("other", "participant-other")]:
            conn.execute(
                """
                INSERT INTO notification_preferences (
                    id, user_id, channel, notification_type, template_id, subscription_mode,
                    consent_status, created_at, updated_at
                ) VALUES (?, ?, 'wechat_subscribe', 'training_due', 'template-private', 'once', 'accepted', ?, ?)
                """,
                (f"pref-{suffix}", user_id, timestamp, timestamp),
            )
            conn.execute(
                """
                INSERT INTO notification_deliveries (
                    id, user_id, preference_id, notification_type, template_id, schedule_key,
                    idempotency_key, status, attempt_count, scheduled_for, error_code, error_message,
                    created_at, updated_at
                ) VALUES (?, ?, ?, 'training_due', 'template-private', ?, ?, 'failed', 2, ?,
                          'wechat_service_unavailable', 'PRIVATE_PROVIDER_MESSAGE', ?, ?)
                """,
                (f"delivery-{suffix}", user_id, f"pref-{suffix}", suffix, f"delivery-key-{suffix}", timestamp, timestamp, timestamp),
            )
            conn.execute(
                """
                INSERT INTO supervision_requests (
                    id, user_id, message, status, risk_level, created_at
                ) VALUES (?, ?, 'PRIVATE_SUPERVISION_TEXT', 'pending', 'low', ?)
                """,
                (f"supervision-{suffix}", user_id, timestamp),
            )
            conn.execute(
                """
                INSERT INTO risk_review_records (
                    id, user_id, source_type, source_id, risk_level, review_status, created_at, updated_at
                ) VALUES (?, ?, 'feedback', ?, 'medium', 'pending', ?, ?)
                """,
                (f"risk-{suffix}", user_id, f"source-{suffix}", timestamp, timestamp),
            )
        conn.execute(
            """
            INSERT INTO relationship_screening_reports (
                id, enrollment_id, user_id, assessment_result_id, status, version,
                report_json, created_at, updated_at
            ) VALUES ('report-assigned', 'enroll-assigned', 'participant-assigned', 'assessment-assigned',
                      'pending_review', 'v1', '{"raw":"PRIVATE_REPORT_TEXT"}', ?, ?)
            """,
            (timestamp, timestamp),
        )
        conn.commit()


def test_research_operations_are_role_scoped_and_redacted(tmp_path):
    app = _fresh_app(tmp_path)
    client = app.test_client()
    researcher_id, researcher_headers = _create_researcher(client)
    _seed_operations(researcher_id)

    assert client.get("/api/research/operations").status_code == 401
    researcher_response = client.get("/api/research/operations", headers=researcher_headers)
    assert researcher_response.status_code == 200
    data = researcher_response.get_json()["data"]
    assert data["scope"] == "assigned_participants"
    assert data["notification_preferences"]["accepted"] == 1
    assert data["notification_deliveries"]["failed"] == 1
    assert data["backlog"] == {"stage_feedback": 1, "supervision": 1, "risk_review": 1, "privacy_requests": 0}
    assert data["privacy_management_available"] is False
    serialized = str(data)
    assert "PRIVATE_" not in serialized
    assert "template-private" not in serialized
    assert "'openid':" not in serialized.lower()

    admin_data = client.get(
        "/api/research/operations",
        headers={"X-Admin-Token": "operations-admin-token"},
    ).get_json()["data"]
    assert admin_data["scope"] == "all_participants"
    assert admin_data["notification_deliveries"]["failed"] == 2
    assert admin_data["backlog"]["supervision"] == 2
