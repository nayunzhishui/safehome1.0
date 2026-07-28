import importlib
import shutil
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = PROJECT_ROOT / "backend"
CONTENT_ROOT = PROJECT_ROOT / "content"


def _fresh_app(tmp_path, monkeypatch):
    sys.path.insert(0, str(BACKEND_ROOT))
    for name in list(sys.modules):
        if name in {"app", "config", "database", "models"} or name.startswith(
            ("routes.", "services.")
        ):
            sys.modules.pop(name, None)
    content_dir = tmp_path / "content"
    shutil.copytree(CONTENT_ROOT, content_dir)
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "safehome-test.sqlite3"))
    monkeypatch.setenv("CONTENT_DIR", str(content_dir))
    monkeypatch.setenv("AI_QA_ENABLED", "0")
    monkeypatch.setenv("AI_QA_SANDBOX_ENABLED", "1")
    monkeypatch.setenv("AI_QA_PROVIDER", "fake")
    return importlib.import_module("app").app


def _headers(app, *, actor_id="researcher-c01", role="researcher"):
    with app.app_context():
        database = importlib.import_module("database")
        auth_utils = importlib.import_module("routes.auth_utils")
        with database.get_connection() as conn:
            now = database.now_iso()
            conn.execute(
                """
                INSERT INTO users
                (id, nickname, role, source, status, created_at, updated_at)
                VALUES (?, ?, ?, 'test', 'active', ?, ?)
                """,
                (actor_id, actor_id, role, now, now),
            )
            conn.commit()
        token = auth_utils.generate_auth_token({"id": actor_id, "role": role})
    return {"Authorization": f"Bearer {token}"}


def test_use_case_catalog_freezes_first_research_scope(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    response = app.test_client().get("/api/ai-qa/use-cases")
    assert response.status_code == 200
    data = response.get_json()["data"]
    assert data["policy_version"] == "2026.07-t37-c01-v1"
    assert data["stage"] == "research_synthetic_frozen"
    assert {item["id"] for item in data["allowed_use_cases"]} == {
        "approved_material_organization",
        "question_version_drafting",
        "evidence_gap_check",
        "discussion_checklist",
        "format_spelling_deidentification_terminology_candidate",
    }
    assert set(data["prohibited_categories"]) == {
        "participant_free_qa",
        "mechanism_level_hypothesis",
        "diagnosis",
        "crisis_conclusion",
        "standardized_test_interpretation",
        "automatic_training_card_prescription",
        "automatic_publication",
    }
    assert data["participant_entry"]["current_stage_enabled"] is False
    assert data["write_actions_allowed"] is False
    assert "system_prompt" not in data


def test_schema_050_adds_non_destructive_session_scope_columns(
    tmp_path, monkeypatch
):
    app = _fresh_app(tmp_path, monkeypatch)
    with app.app_context():
        database = importlib.import_module("database")
        with database.get_connection() as conn:
            columns = {
                row["name"]
                for row in conn.execute("PRAGMA table_info(ai_qa_sessions)").fetchall()
            }
    assert database.CURRENT_SCHEMA_VERSION == "2026_07_28_050"
    assert database.CURRENT_SCHEMA_NAME == "ai_use_case_freeze"
    assert {"use_case_id", "use_case_policy_version"}.issubset(columns)


def test_session_requires_known_frozen_use_case_and_persists_scope(
    tmp_path, monkeypatch
):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    headers = _headers(app)
    base = {"synthetic_data": True, "research_use_allowed": False}

    missing = client.post("/api/ai-qa/sessions", json=base, headers=headers)
    unknown = client.post(
        "/api/ai-qa/sessions",
        json={**base, "use_case_id": "participant_free_qa"},
        headers=headers,
    )
    created = client.post(
        "/api/ai-qa/sessions",
        json={**base, "use_case_id": "evidence_gap_check"},
        headers=headers,
    )

    assert missing.status_code == 422
    assert missing.get_json()["error"]["code"] == "ai_qa_use_case_required"
    assert unknown.status_code == 409
    assert unknown.get_json()["error"]["code"] == "ai_qa_use_case_not_allowed"
    assert created.status_code == 200
    data = created.get_json()["data"]
    assert data["use_case_id"] == "evidence_gap_check"
    assert data["use_case_policy_version"] == "2026.07-t37-c01-v1"


def test_message_cannot_change_or_escape_session_use_case(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    headers = _headers(app)
    created = client.post(
        "/api/ai-qa/sessions",
        json={
            "synthetic_data": True,
            "research_use_allowed": False,
            "use_case_id": "discussion_checklist",
        },
        headers=headers,
    ).get_json()["data"]

    changed = client.post(
        f"/api/ai-qa/sessions/{created['id']}/messages",
        json={
            "text": "请整理讨论清单",
            "synthetic_data": True,
            "use_case_id": "automatic_publication",
        },
        headers=headers,
    )
    assert changed.status_code == 409
    assert changed.get_json()["error"]["code"] == "ai_qa_use_case_mismatch"


def test_parent_cannot_create_session_even_with_allowed_use_case(
    tmp_path, monkeypatch
):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    parent_headers = _headers(app, actor_id="parent-c01", role="parent")
    response = client.post(
        "/api/ai-qa/sessions",
        json={
            "synthetic_data": True,
            "research_use_allowed": False,
            "use_case_id": "question_version_drafting",
        },
        headers=parent_headers,
    )
    assert response.status_code == 403


def test_config_exposes_same_frozen_scope_without_secret_fields(
    tmp_path, monkeypatch
):
    app = _fresh_app(tmp_path, monkeypatch)
    data = app.test_client().get("/api/ai-qa/config").get_json()["data"]
    policy = data["use_case_policy"]
    assert policy["policy_version"] == "2026.07-t37-c01-v1"
    assert len(policy["allowed_use_cases"]) == 5
    assert policy["participant_entry"]["current_stage_enabled"] is False
    assert "prompt_template" not in policy
    assert "provider_secret" not in policy
