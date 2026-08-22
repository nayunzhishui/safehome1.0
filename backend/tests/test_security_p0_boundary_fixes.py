import importlib
import json
import shutil
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"


def _fresh_app(tmp_path, monkeypatch, *, app_env="production", ai_enabled=False):
    content_dir = tmp_path / "content"
    shutil.copytree(ROOT / "content", content_dir)
    showcase = json.loads((content_dir / "showcase_access.json").read_text(encoding="utf-8"))
    showcase.update(
        {
            "researcher_platform_full_access": False,
            "read_only_role_bypass": False,
        }
    )
    (content_dir / "showcase_access.json").write_text(
        json.dumps(showcase, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    if str(BACKEND) not in sys.path:
        sys.path.insert(0, str(BACKEND))
    for name in list(sys.modules):
        if name in {"app", "config", "database", "models"} or name.startswith(
            ("routes.", "services.")
        ):
            sys.modules.pop(name, None)

    monkeypatch.setenv("APP_ENV", app_env)
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "security-p0.sqlite3"))
    monkeypatch.setenv("CONTENT_DIR", str(content_dir))
    monkeypatch.setenv("DB_PROVIDER", "sqlite")
    monkeypatch.setenv("ALLOW_PRODUCTION_SQLITE", "1")
    monkeypatch.setenv("SECRET_KEY", "security-p0-test-secret-key-that-is-long-enough")
    monkeypatch.setenv("ADMIN_EXPORT_TOKEN", "security-p0-admin-token")
    monkeypatch.setenv("PRODUCTION_FEATURES_UNLOCKED", "1" if ai_enabled else "0")
    monkeypatch.setenv("AI_QA_ENABLED", "1" if ai_enabled else "0")
    monkeypatch.setenv("AI_QA_SANDBOX_ENABLED", "1" if ai_enabled else "0")
    monkeypatch.setenv("AI_QA_PROVIDER", "fake")
    return importlib.import_module("app").app


def _headers_for(app, users):
    with app.app_context():
        from database import get_connection, now_iso
        from routes.auth_utils import generate_auth_token

        timestamp = now_iso()
        with get_connection() as conn:
            for user_id, role in users.items():
                conn.execute(
                    """
                    INSERT INTO users (
                        id, nickname, role, source, status, created_at, updated_at
                    ) VALUES (?, ?, ?, 'test', 'active', ?, ?)
                    """,
                    (user_id, user_id, role, timestamp, timestamp),
                )
            conn.commit()
        return {
            user_id: {
                "Authorization": (
                    "Bearer "
                    + generate_auth_token({"id": user_id, "role": role})
                )
            }
            for user_id, role in users.items()
        }


def _seed_research_subject(app):
    with app.app_context():
        from database import get_connection, json_dumps, now_iso

        timestamp = now_iso()
        with get_connection() as conn:
            conn.execute(
                """
                INSERT INTO relationship_pilot_enrollments (
                    id, user_id, assessment_result_id, worksheet_id, dimensions_json,
                    radar_features_json, profile_json, consent_scope, status,
                    review_status, created_at, updated_at
                ) VALUES (
                    'enrollment-security-p0', 'participant-security-p0',
                    'assessment-security-p0', 'student_profile_v1', '[]', '[]', '{}',
                    'relationship_pilot_stage2_v1', 'enrolled', 'pending_review', ?, ?
                )
                """,
                (timestamp, timestamp),
            )
            conn.execute(
                """
                INSERT INTO assessment_results (
                    id, user_id, worksheet_id, worksheet_title, category,
                    answers_json, scores_json, total_score, result_summary,
                    profile_model_id, profile_cluster_id, profile_confidence,
                    created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    "assessment-security-p0",
                    "participant-security-p0",
                    "student_profile_v1",
                    "学生画像",
                    "profile",
                    json_dumps([{"question_id": "secret-answer", "value": "raw"}]),
                    json_dumps({"secret_score": 99}),
                    99,
                    "最小化摘要",
                    "profile-v1",
                    1,
                    0.9,
                    timestamp,
                ),
            )
            conn.commit()


def _record_research_consent(app, *, agreed):
    with app.app_context():
        from database import get_connection, new_id, now_iso

        timestamp = now_iso()
        with get_connection() as conn:
            conn.execute(
                """
                INSERT INTO consent_records (
                    id, user_id, consent_type, consent_version, agreed,
                    agreed_at, revoked_at, created_at
                ) VALUES (?, 'participant-security-p0', 'research_authorization',
                          'security-p0-v1', ?, ?, ?, ?)
                """,
                (
                    new_id("consent"),
                    1 if agreed else 0,
                    timestamp,
                    None if agreed else timestamp,
                    timestamp,
                ),
            )
            conn.commit()


def test_researcher_legacy_sensitive_reads_are_fail_closed(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    headers = _headers_for(
        app,
        {
            "participant-security-p0": "parent",
            "researcher-security-p0": "researcher",
            "admin-security-p0": "admin",
        },
    )
    _seed_research_subject(app)
    client = app.test_client()

    raw = client.get(
        "/api/admin/assessment-results",
        headers=headers["researcher-security-p0"],
    )
    export = client.get(
        "/api/admin/export?type=profile",
        headers=headers["researcher-security-p0"],
    )
    workspace = client.get(
        "/api/research/participants",
        headers=headers["researcher-security-p0"],
    )

    assert raw.status_code == 403
    assert export.status_code == 403
    assert workspace.status_code == 403
    assert raw.get_json()["error"]["code"] == "researcher_sensitive_read_disabled"
    assert export.get_json()["error"]["code"] == "researcher_sensitive_read_disabled"
    assert workspace.get_json()["error"]["code"] == "researcher_sensitive_read_disabled"


def test_scoped_research_assessment_read_requires_assignment_and_explicit_opt_in(
    tmp_path, monkeypatch
):
    app = _fresh_app(tmp_path, monkeypatch)
    headers = _headers_for(
        app,
        {
            "participant-security-p0": "parent",
            "researcher-security-p0": "researcher",
            "admin-security-p0": "admin",
        },
    )
    _seed_research_subject(app)
    client = app.test_client()

    assigned = client.post(
        "/api/research/access/assignments",
        headers={
            **headers["admin-security-p0"],
            "Idempotency-Key": "security-p0-assignment",
        },
        json={
            "enrollment_id": "enrollment-security-p0",
            "actor_id": "researcher-security-p0",
            "assignment_role": "researcher",
        },
    )
    assert assigned.status_code == 201

    no_consent = client.get(
        "/api/research/access/enrollments/enrollment-security-p0/assessment-summaries",
        headers=headers["researcher-security-p0"],
    )
    assert no_consent.status_code == 403
    assert no_consent.get_json()["error"]["code"] == "research_authorization_required"

    _record_research_consent(app, agreed=True)

    participants = client.get(
        "/api/research/access/participants",
        headers=headers["researcher-security-p0"],
    )
    assert participants.status_code == 200
    participant_data = participants.get_json()["data"]
    assert participant_data["count"] == 1
    assert "user_id" not in participant_data["items"][0]
    assert participant_data["items"][0]["anonymous_id"].startswith("anon_")

    response = client.get(
        "/api/research/access/enrollments/enrollment-security-p0/assessment-summaries",
        headers=headers["researcher-security-p0"],
    )
    assert response.status_code == 200
    data = response.get_json()["data"]
    assert data["count"] == 1
    item = data["items"][0]
    for forbidden in ("answers", "answers_json", "scores", "scores_json", "user_id"):
        assert forbidden not in item
    assert item["result_summary"] == "最小化摘要"

    _record_research_consent(app, agreed=False)
    revoked = client.get(
        "/api/research/access/enrollments/enrollment-security-p0/assessment-summaries",
        headers=headers["researcher-security-p0"],
    )
    assert revoked.status_code == 403
    assert revoked.get_json()["error"]["code"] == "research_authorization_required"


def test_admin_participant_derived_export_requires_subject_and_explicit_opt_in(
    tmp_path, monkeypatch
):
    app = _fresh_app(tmp_path, monkeypatch)
    headers = _headers_for(
        app,
        {
            "participant-security-p0": "parent",
            "admin-security-p0": "admin",
        },
    )
    _seed_research_subject(app)
    client = app.test_client()

    no_subject = client.get(
        "/api/admin/export?type=profile",
        headers=headers["admin-security-p0"],
    )
    assert no_subject.status_code == 400
    assert no_subject.get_json()["error"]["code"] == "research_subject_scope_required"

    no_consent = client.get(
        "/api/admin/export?type=profile&user_id=participant-security-p0",
        headers=headers["admin-security-p0"],
    )
    assert no_consent.status_code == 403
    assert no_consent.get_json()["error"]["code"] == "research_authorization_required"

    bulk_raw = client.get(
        "/api/admin/export?type=raw_wide",
        headers=headers["admin-security-p0"],
    )
    assert bulk_raw.status_code == 403
    assert bulk_raw.get_json()["error"]["code"] == "scoped_research_export_required"


def test_historical_student_ai_candidate_is_withheld_and_upgraded_to_minor_t3(
    tmp_path, monkeypatch
):
    app = _fresh_app(tmp_path, monkeypatch, app_env="testing", ai_enabled=True)
    headers = _headers_for(app, {"student-security-p0": "student"})

    with app.app_context():
        from database import get_connection, json_dumps, now_iso
        from services.ai_qa_review_service import create_review_case

        timestamp = now_iso()
        with get_connection() as conn:
            conn.execute(
                """
                INSERT INTO ai_qa_sessions (
                    id, user_id, mode, status, synthetic_data, context_policy,
                    research_use_allowed, use_case_id, use_case_policy_version,
                    created_at, updated_at
                ) VALUES (
                    'session-security-p0', 'student-security-p0',
                    'participant_support', 'active', 0, 'current_session_only', 0,
                    'participant_support_navigation', 'security-p0-v1', ?, ?
                )
                """,
                (timestamp, timestamp),
            )
            conn.execute(
                """
                INSERT INTO ai_qa_messages (
                    id, session_id, user_id, role, content, citations_json,
                    model_json, safety_json, prompt_version, knowledge_version,
                    token_estimate, cost_micros, created_at
                ) VALUES (
                    'message-security-p0', 'session-security-p0',
                    'student-security-p0', 'assistant', ?, '[]',
                    ?, ?, 'prompt-security-p0', 'knowledge-security-p0', 10, 0, ?
                )
                """,
                (
                    "SECRET_UNREVIEWED_CANDIDATE",
                    json_dumps({"human_verification_required": True}),
                    json_dumps({"precheck": {"severity": "low"}}),
                    timestamp,
                ),
            )
            create_review_case(
                conn,
                message_id="message-security-p0",
                session_id="session-security-p0",
                subject_type="ai_qa_session",
                subject_id="session-security-p0",
                recipient_user_id="student-security-p0",
                draft_author_id="provider:fake",
                candidate_text="SECRET_UNREVIEWED_CANDIDATE",
                citations=[],
                gate_violations=[],
                scope={
                    "object_scope": "individual_adult_low_risk",
                    "risk_level": "low",
                    "involves_minor": False,
                    "multi_party": False,
                    "mechanism_explanation": False,
                },
                publication_candidate_id=None,
            )
            conn.commit()

    client = app.test_client()
    response = client.get(
        "/api/ai-qa/sessions/session-security-p0",
        headers=headers["student-security-p0"],
    )
    assert response.status_code == 200
    data = response.get_json()["data"]
    assistant = next(item for item in data["messages"] if item["role"] == "assistant")
    assert assistant["content"] != "SECRET_UNREVIEWED_CANDIDATE"
    assert "SECRET_UNREVIEWED_CANDIDATE" not in json.dumps(data, ensure_ascii=False)
    assert assistant["delivery_status"] == "pending_human_review"
    assert assistant["model"]["candidate_withheld"] is True

    with app.app_context():
        from database import get_connection, json_loads

        with get_connection() as conn:
            case = conn.execute(
                "SELECT * FROM ai_qa_review_cases WHERE message_id = 'message-security-p0'"
            ).fetchone()
            scope = json_loads(case["scope_json"], {})
            assert case["required_task_code"] == "minor_or_family"
            assert case["required_competency"] == "T3"
            assert scope["involves_minor"] is True
            assert scope["object_scope"] == "individual_student_support"
            conn.execute(
                """
                UPDATE ai_qa_review_cases
                SET status = 'adopted', final_text = 'APPROVED_REVIEWED_TEXT'
                WHERE id = ?
                """,
                (case["id"],),
            )
            conn.commit()

    approved = client.get(
        "/api/ai-qa/sessions/session-security-p0",
        headers=headers["student-security-p0"],
    )
    approved_assistant = next(
        item
        for item in approved.get_json()["data"]["messages"]
        if item["role"] == "assistant"
    )
    assert approved_assistant["content"] == "APPROVED_REVIEWED_TEXT"
    assert approved_assistant["delivery_status"] == "human_review_approved"
