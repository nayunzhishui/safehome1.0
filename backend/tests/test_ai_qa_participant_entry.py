import importlib
import shutil
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"


def _fresh_app(tmp_path, monkeypatch):
    sys.path.insert(0, str(BACKEND))
    for name in list(sys.modules):
        if name in {"app", "config", "database", "models"} or name.startswith(
            ("routes.", "services.")
        ):
            sys.modules.pop(name, None)
    content_dir = tmp_path / "content"
    shutil.copytree(ROOT / "content", content_dir)
    monkeypatch.setenv("APP_ENV", "testing")
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "participant-ai.sqlite3"))
    monkeypatch.setenv("CONTENT_DIR", str(content_dir))
    monkeypatch.setenv("PRODUCTION_FEATURES_UNLOCKED", "1")
    monkeypatch.setenv("AI_QA_ENABLED", "1")
    monkeypatch.setenv("AI_QA_SANDBOX_ENABLED", "1")
    monkeypatch.setenv("AI_QA_PROVIDER", "fake")
    return importlib.import_module("app").app


def _parent_headers(app):
    with app.app_context():
        database = importlib.import_module("database")
        auth_utils = importlib.import_module("routes.auth_utils")
        with database.get_connection() as conn:
            now = database.now_iso()
            conn.execute(
                """
                INSERT INTO users
                (id, nickname, role, source, status, created_at, updated_at)
                VALUES ('parent-participant-ai', '参与者', 'parent', 'test', 'active', ?, ?)
                """,
                (now, now),
            )
            conn.commit()
        token = auth_utils.generate_auth_token(
            {"id": "parent-participant-ai", "role": "parent"}
        )
    return {"Authorization": f"Bearer {token}"}


def test_participant_entry_requires_separate_consent_and_owns_session(
    tmp_path, monkeypatch
):
    app = _fresh_app(tmp_path, monkeypatch)
    headers = _parent_headers(app)
    client = app.test_client()
    payload = {"use_case_id": "participant_support_navigation"}

    blocked = client.post("/api/ai-qa/sessions", json=payload, headers=headers)
    consent = client.post(
        "/api/consent",
        json={
            "consent_type": "ai_assistance",
            "consent_version": "2026.07-consent-v2",
            "agreed": True,
        },
        headers=headers,
    )
    created = client.post("/api/ai-qa/sessions", json=payload, headers=headers)

    assert blocked.status_code == 409
    assert blocked.get_json()["error"]["code"] == "ai_assistance_consent_required"
    assert consent.status_code == 201
    assert created.status_code == 200
    session = created.get_json()["data"]
    assert session["mode"] == "participant_support"
    assert session["synthetic_data"] == 0
    assert session["context_policy"] == "current_session_only"
    assert session["research_use_allowed"] == 0


def test_participant_high_risk_text_uses_fixed_route_without_provider(
    tmp_path, monkeypatch
):
    app = _fresh_app(tmp_path, monkeypatch)
    headers = _parent_headers(app)
    client = app.test_client()
    client.post(
        "/api/consent",
        json={"consent_type": "ai_assistance", "agreed": True},
        headers=headers,
    )
    session = client.post(
        "/api/ai-qa/sessions",
        json={"use_case_id": "participant_support_navigation"},
        headers=headers,
    ).get_json()["data"]

    response = client.post(
        f"/api/ai-qa/sessions/{session['id']}/messages",
        json={"text": "我想自杀"},
        headers=headers,
    )

    assert response.status_code == 200
    data = response.get_json()["data"]
    assert data["route"] == "risk_fixed"
    assert data["fixed_response"] is True
    with app.app_context():
        database = importlib.import_module("database")
        with database.get_connection() as conn:
            provider_count = conn.execute(
                "SELECT COUNT(*) AS count FROM ai_qa_provider_events"
            ).fetchone()["count"]
    assert provider_count == 0


def test_config_exposes_controlled_participant_scope(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    data = app.test_client().get("/api/ai-qa/config").get_json()["data"]
    assert data["participant_enabled"] is True
    assert data["participant_eligible"] is True
    assert data["participant_use_case_policy"]["required_consent_type"] == "ai_assistance"
    assert {
        item["id"]
        for item in data["participant_use_case_policy"]["allowed_use_cases"]
    } == {"participant_support_navigation"}
