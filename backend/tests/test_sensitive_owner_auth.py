import importlib
import os
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = PROJECT_ROOT / "backend"
ADMIN_HEADERS = {"X-Admin-Token": "safehome-local-admin-token"}


def _fresh_app(tmp_path):
    sys.path.insert(0, str(BACKEND_ROOT))
    for name in list(sys.modules):
        if name in {"app", "config", "database", "models"} or name.startswith("routes.") or name.startswith("services."):
            sys.modules.pop(name, None)
    os.environ["DATABASE_PATH"] = str(tmp_path / "safehome-test.sqlite3")
    os.environ["CONTENT_DIR"] = str(PROJECT_ROOT / "content")
    os.environ.pop("APP_ENV", None)
    os.environ.pop("ADMIN_EXPORT_TOKEN", None)
    module = importlib.import_module("app")
    return module.app


def _create_profile(client, user_id: str = "student-owner-auth") -> str:
    response = client.post(
        "/api/profile",
        json={
            "user_id": user_id,
            "scores": {
                "test_anxiety": 4.2,
                "iu_score": 4.0,
                "f_score": 2.8,
                "self_compassion": 2.9,
            },
            "free_text": "考试前会紧张，但愿意先做一次小练习。",
        },
    )
    assert response.status_code == 201
    return response.get_json()["data"]["student_profile_id"]


def _insert_parent_assessment(user_id: str = "parent-owner-auth") -> str:
    import database

    submission_id = "parent_owner_auth_001"
    with database.get_connection() as conn:
        conn.execute(
            """
            INSERT INTO parent_assessment_submissions (
                id, user_id, anonymous_id, participant_code, research_consent,
                study_batch, source_channel, questionnaire_version, scoring_version,
                answers_json, scores_json, profile_key, report_json,
                started_at, completed_at, duration_seconds, quality_flags_json,
                export_allowed, created_at, updated_at
            )
            VALUES (
                ?, ?, 'anon_parent_owner_auth', 'P001', 1, 'batch', 'web', 'q-v1', 's-v1',
                '{"scale_answers":{}}', '{"scale_scores":{"scales":{}}}', 'support_parent',
                '{"boundary_notice":"本报告不构成诊断。"}',
                NULL, '2026-06-05T00:00:00+00:00', 60, '{"flags":[]}', 1,
                '2026-06-05T00:00:00+00:00', '2026-06-05T00:00:00+00:00'
            )
            """,
            (submission_id, user_id),
        )
        conn.commit()
    return submission_id


def test_profile_detail_and_visuals_require_admin_or_matching_owner(tmp_path):
    app = _fresh_app(tmp_path)
    client = app.test_client()
    profile_id = _create_profile(client)

    no_token = client.get(f"/api/profile-results/{profile_id}")
    wrong_owner = client.get(f"/api/profile-results/{profile_id}?user_id=student-other")
    owner = client.get(f"/api/profile-results/{profile_id}?user_id=student-owner-auth")
    admin = client.get(f"/api/profile-results/{profile_id}", headers=ADMIN_HEADERS)
    visuals_owner = client.get(f"/api/profile-results/{profile_id}/visuals?user_id=student-owner-auth")

    assert no_token.status_code == 401
    assert wrong_owner.status_code == 401
    assert owner.status_code == 200
    assert admin.status_code == 200
    assert visuals_owner.status_code == 200


def test_profile_followup_and_sandplay_require_matching_owner(tmp_path):
    app = _fresh_app(tmp_path)
    client = app.test_client()
    profile_id = _create_profile(client)

    no_owner = client.get(f"/api/profile-results/{profile_id}/followups")
    owner_list = client.get(f"/api/profile-results/{profile_id}/followups?user_id=student-owner-auth")
    wrong_post = client.post(
        f"/api/profile-results/{profile_id}/followups",
        json={"user_id": "student-other", "text": "今天状态还可以。"},
    )
    owner_post = client.post(
        f"/api/profile-results/{profile_id}/followups",
        json={"user_id": "student-owner-auth", "text": "今天状态还可以。"},
    )

    assert no_owner.status_code == 401
    assert owner_list.status_code == 200
    assert wrong_post.status_code == 401
    assert owner_post.status_code == 201

    no_sandplay = client.get(f"/api/profile-results/{profile_id}/sandplay")
    owner_sandplay = client.get(f"/api/profile-results/{profile_id}/sandplay?user_id=student-owner-auth")
    admin_sandplay_post = client.post(
        f"/api/profile-results/{profile_id}/sandplay",
        headers=ADMIN_HEADERS,
        json={
            "scene": {"symbols": [{"type": "bridge", "x": 50, "y": 50}]},
            "reflection_text": "这座桥像一个支持资源。",
        },
    )

    assert no_sandplay.status_code == 401
    assert owner_sandplay.status_code == 200
    assert admin_sandplay_post.status_code == 404
    assert admin_sandplay_post.get_json()["error"]["code"] == "not_found"


def test_parent_assessment_detail_requires_owner_or_explicit_object_scope(tmp_path):
    app = _fresh_app(tmp_path)
    client = app.test_client()
    submission_id = _insert_parent_assessment()

    no_list_token = client.get("/api/parent-assessments")
    admin_list = client.get("/api/parent-assessments", headers=ADMIN_HEADERS)
    no_detail_token = client.get(f"/api/parent-assessments/{submission_id}")
    wrong_owner = client.get(f"/api/parent-assessments/{submission_id}?user_id=parent-other")
    owner = client.get(f"/api/parent-assessments/{submission_id}?user_id=parent-owner-auth")
    admin = client.get(f"/api/parent-assessments/{submission_id}", headers=ADMIN_HEADERS)

    assert no_list_token.status_code == 401
    assert admin_list.status_code == 200
    assert no_detail_token.status_code == 401
    assert wrong_owner.status_code == 401
    assert owner.status_code == 200
    assert admin.status_code == 404
    assert admin.get_json()["error"]["code"] == "not_found"

    no_action_owner = client.post(f"/api/parent-assessments/{submission_id}/actions", json={"action_key": "saved"})
    owner_action = client.post(
        f"/api/parent-assessments/{submission_id}/actions",
        json={"user_id": "parent-owner-auth", "action_key": "saved"},
    )
    assert no_action_owner.status_code == 401
    assert owner_action.status_code == 201
