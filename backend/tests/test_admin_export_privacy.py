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
    module = importlib.import_module("app")
    return module.app


def _csv(client, export_type: str, query: str = "") -> str:
    response = client.get(f"/api/admin/export?type={export_type}{query}", headers=ADMIN_HEADERS)
    assert response.status_code == 200
    return response.get_data(as_text=True)


def test_diaries_export_uses_lengths_not_original_text(tmp_path):
    app = _fresh_app(tmp_path)
    client = app.test_client()

    response = client.post(
        "/api/diaries",
        json={
            "user_id": "parent-private-diary",
            "scene": "作业沟通",
            "event_description": "PRIVATE_EVENT_TEXT_001",
            "parent_emotion": "着急",
            "parent_emotion_intensity": 7,
            "automatic_thought": "PRIVATE_THOUGHT_001",
            "body_sensation": "PRIVATE_BODY_001",
            "behavior": "PRIVATE_BEHAVIOR_001",
            "raw_text": "PRIVATE_RAW_TEXT_001",
        },
    )
    assert response.status_code == 201

    csv_text = _csv(client, "diaries")

    assert "parent-private-diary" not in csv_text
    assert "PRIVATE_EVENT_TEXT_001" not in csv_text
    assert "PRIVATE_THOUGHT_001" not in csv_text
    assert "PRIVATE_BEHAVIOR_001" not in csv_text
    assert "PRIVATE_RAW_TEXT_001" not in csv_text
    assert "anonymous_id" in csv_text
    assert "event_description_length" in csv_text


def test_feedback_export_uses_feedback_lengths_not_original_feedback(tmp_path):
    app = _fresh_app(tmp_path)
    client = app.test_client()

    import database

    with database.get_connection() as conn:
        conn.execute(
            """
            INSERT INTO feedback_results (
                id, user_id, diary_id, tags_json, trigger_summary,
                pattern_summary, supportive_feedback, alternative_response,
                recommended_card_ids_json, risk_level, created_at
            )
            VALUES (
                'feedback_privacy_001', 'parent-private-feedback', NULL, '["tag"]',
                'PRIVATE_TRIGGER_001', 'PRIVATE_PATTERN_001',
                'PRIVATE_SUPPORTIVE_FEEDBACK_001', 'PRIVATE_ALTERNATIVE_001',
                '["pause_and_notice"]', 'low', '2026-06-05T00:00:00+00:00'
            )
            """
        )
        conn.commit()

    csv_text = _csv(client, "feedback")

    assert "parent-private-feedback" not in csv_text
    assert "PRIVATE_SUPPORTIVE_FEEDBACK_001" not in csv_text
    assert "PRIVATE_ALTERNATIVE_001" not in csv_text
    assert "PRIVATE_TRIGGER_001" not in csv_text
    assert "supportive_feedback_length" in csv_text


def test_supervision_export_uses_lengths_not_message_contact_or_reply(tmp_path):
    app = _fresh_app(tmp_path)
    client = app.test_client()

    import database

    with database.get_connection() as conn:
        conn.execute(
            """
            INSERT INTO supervision_requests (
                id, user_id, diary_id, message, contact, risk_hint,
                risk_level, status, supervisor_reply, created_at, replied_at
            )
            VALUES (
                'supervision_privacy_001', 'parent-private-supervision', NULL,
                'PRIVATE_MESSAGE_001', 'phone-PRIVATE-CONTACT-001',
                'PRIVATE_RISK_HINT_001', 'medium', 'pending',
                'PRIVATE_SUPERVISOR_REPLY_001',
                '2026-06-05T00:00:00+00:00', NULL
            )
            """
        )
        conn.commit()

    csv_text = _csv(client, "supervision")

    assert "parent-private-supervision" not in csv_text
    assert "PRIVATE_MESSAGE_001" not in csv_text
    assert "PRIVATE-CONTACT-001" not in csv_text
    assert "PRIVATE_RISK_HINT_001" not in csv_text
    assert "PRIVATE_SUPERVISOR_REPLY_001" not in csv_text
    assert "message_length" in csv_text
    assert "contact_length" in csv_text


def test_high_risk_profile_and_records_export_confirmed_still_omits_raw_user_and_data_json(tmp_path):
    app = _fresh_app(tmp_path)
    client = app.test_client()

    import database

    with database.get_connection() as conn:
        conn.execute(
            """
            INSERT INTO student_profiles (
                id, user_id, anonymous_id, assessment_result_id, round, source,
                scores_json, text_features_json, profile_code, profile_name,
                confidence, dimensions_json, recommended_task_ids_json,
                risk_level, requires_review, boundary_notice, rules_version,
                report_json, visuals_json, export_allowed, created_at, updated_at
            )
            VALUES (
                'profile_privacy_001', 'student-private-profile', 'anon_profile_privacy',
                NULL, 1, 'test', '{}', '{}', 'support_profile', '阶段性画像',
                0.8, '[]', '[]', 'high', 1, '边界提示', 'test',
                '{"note":"PRIVATE_PROFILE_REPORT_001"}', '{}', 1,
                '2026-06-05T00:00:00+00:00', '2026-06-05T00:00:00+00:00'
            )
            """
        )
        conn.execute(
            """
            INSERT INTO records (
                id, user_id, module_type, source_id, data_json,
                created_at, updated_at, export_allowed
            )
            VALUES (
                'record_privacy_001', 'student-private-profile', 'student_profile',
                'profile_privacy_001',
                '{"anonymous_id":"anon_profile_privacy","risk_level":"high","requires_review":true,"raw_text":"PRIVATE_RECORD_RAW_001","profile_code":"support_profile"}',
                '2026-06-05T00:00:00+00:00', '2026-06-05T00:00:00+00:00', 1
            )
            """
        )
        conn.commit()

    blocked_profile = client.get("/api/admin/export?type=profile", headers=ADMIN_HEADERS)
    assert blocked_profile.status_code == 409
    blocked_records = client.get("/api/admin/export?type=records&module_type=student_profile", headers=ADMIN_HEADERS)
    assert blocked_records.status_code == 409

    profile_csv = _csv(client, "profile", "&confirm_high_risk=true")
    records_csv = _csv(client, "records", "&module_type=student_profile&confirm_high_risk=true")

    combined = profile_csv + records_csv
    assert "student-private-profile" not in combined
    assert "PRIVATE_PROFILE_REPORT_001" not in combined
    assert "PRIVATE_RECORD_RAW_001" not in combined
    assert "data_json" not in records_csv.splitlines()[0]
    assert "anonymous_id" in records_csv
    assert "risk_level" in records_csv


def test_parent_assessments_summary_export_omits_answers_and_report_json(tmp_path):
    app = _fresh_app(tmp_path)
    client = app.test_client()

    import database

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
                'parent_privacy_001', 'parent-private-assessment', 'anon_parent_privacy',
                'P-PRIVATE-001', 1, 'batch-a', 'web', 'q-v1', 's-v1',
                '{"scale_answers":{"item":"PRIVATE_ANSWER_001"},"question_answers":{"open":"PRIVATE_OPEN_001"}}',
                '{"scale_scores":{"scales":{}}}', 'support_parent',
                '{"role":"支持性报告","action":"PRIVATE_REPORT_ACTION_001"}',
                NULL, '2026-06-05T00:00:00+00:00', 60, '{"flags":[]}', 1,
                '2026-06-05T00:00:00+00:00', '2026-06-05T00:00:00+00:00'
            )
            """
        )
        conn.commit()

    csv_text = _csv(client, "parent_assessments")
    header = csv_text.splitlines()[0]

    assert "parent-private-assessment" not in csv_text
    assert "PRIVATE_ANSWER_001" not in csv_text
    assert "PRIVATE_OPEN_001" not in csv_text
    assert "PRIVATE_REPORT_ACTION_001" not in csv_text
    assert "answers_json" not in header
    assert "report_json" not in header

    raw_wide_csv = _csv(client, "raw_wide")
    raw_wide_header = raw_wide_csv.splitlines()[0]
    assert "P-PRIVATE-001" not in raw_wide_csv
    assert "participant_code_hash" in raw_wide_header
