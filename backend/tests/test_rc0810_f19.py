import importlib
import json
import shutil
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))


def _fresh_app(tmp_path, monkeypatch):
    for name in list(sys.modules):
        if name in {"app", "config", "database", "models"} or name.startswith(
            ("routes.", "services.")
        ):
            sys.modules.pop(name, None)
    content_dir = tmp_path / "content"
    shutil.copytree(ROOT / "content", content_dir)
    monkeypatch.setenv("APP_ENV", "testing")
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "f19.sqlite3"))
    monkeypatch.setenv("CONTENT_DIR", str(content_dir))
    monkeypatch.setenv("PRODUCTION_FEATURES_UNLOCKED", "1")
    monkeypatch.setenv("AI_QA_ENABLED", "1")
    monkeypatch.setenv("AI_QA_SANDBOX_ENABLED", "1")
    monkeypatch.setenv("AI_QA_PROVIDER", "fake")
    monkeypatch.setenv("AI_QA_REAL_PROVIDER_ENABLED", "0")
    return importlib.import_module("app").app, content_dir


def _headers(app, role="parent"):
    with app.app_context():
        database = importlib.import_module("database")
        auth_utils = importlib.import_module("routes.auth_utils")
        actor_id = f"f19-{role}"
        with database.get_connection() as conn:
            now = database.now_iso()
            conn.execute(
                "INSERT INTO users (id, nickname, role, source, status, created_at, updated_at) VALUES (?, ?, ?, 'test', 'active', ?, ?)",
                (actor_id, actor_id, role, now, now),
            )
            conn.commit()
        token = auth_utils.generate_auth_token({"id": actor_id, "role": role})
    return {"Authorization": f"Bearer {token}"}


def test_production_injection_and_provider_secret_cannot_open_participant_ai(
    tmp_path, monkeypatch
):
    app, _content_dir = _fresh_app(tmp_path, monkeypatch)
    monkeypatch.setenv("OPENAI_API_KEY", "present-but-must-not-enable")
    app.config.update(
        APP_ENV="production",
        AI_QA_ENABLED=True,
        AI_QA_SANDBOX_ENABLED=True,
        AI_QA_PROVIDER="openai",
        AI_QA_REAL_PROVIDER_ENABLED=True,
        AI_QA_DAILY_BUDGET_MICROS=1000,
    )

    data = app.test_client().get("/api/ai-qa/config").get_json()["data"]

    assert data["participant_enabled"] is False
    assert data["sandbox_enabled"] is False
    assert data["participant_entry_visible"] is False
    assert data["capability"]["reason_code"] == "production_ai_fixed_closed"
    assert data["provider_policy"]["external_provider_enabled"] is False


def test_production_direct_api_fails_before_session_or_provider(tmp_path, monkeypatch):
    app, _content_dir = _fresh_app(tmp_path, monkeypatch)
    headers = _headers(app)
    app.config.update(APP_ENV="production", AI_QA_ENABLED=True)
    service = importlib.import_module("services.ai_qa_service")
    monkeypatch.setattr(
        service,
        "get_provider",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("provider called")),
    )

    response = app.test_client().post(
        "/api/ai-qa/sessions",
        json={"use_case_id": "participant_support_navigation"},
        headers=headers,
    )

    assert response.status_code == 409
    assert response.get_json()["error"]["code"] == "ai_qa_production_fixed_closed"
    with app.app_context():
        database = importlib.import_module("database")
        with database.get_connection() as conn:
            assert conn.execute("SELECT COUNT(*) AS count FROM ai_qa_sessions").fetchone()["count"] == 0


def test_only_capability_service_and_provider_factory_can_reach_provider():
    service_source = (BACKEND / "services" / "ai_qa_service.py").read_text(encoding="utf-8")
    route_source = (BACKEND / "routes" / "ai_qa.py").read_text(encoding="utf-8")
    scheduler_source = (BACKEND / "services" / "safety_scheduler_service.py").read_text(encoding="utf-8")

    assert "resolve_ai_capability" in service_source
    assert "resolve_ai_capability" in route_source
    assert "get_provider(" not in scheduler_source
    assert "current_app.config.get(\"AI_QA_ENABLED\"" not in route_source


def test_validation_sandbox_uses_same_resolver_and_keeps_real_adapters_bounded(
    tmp_path, monkeypatch
):
    app, _content_dir = _fresh_app(tmp_path, monkeypatch)
    app.config.update(APP_ENV="validation", AI_QA_PROVIDER="fake")
    with app.app_context():
        capability = importlib.import_module("services.ai_capability_service")
        decision = capability.resolve_ai_capability(
            {"id": "f19-researcher", "role": "researcher"}, "provider_generate"
        )

    assert decision.enabled is True
    assert decision.data_mode == "synthetic_or_explicitly_authorized"
    assert decision.provider == "fake"
    provider_source = (BACKEND / "services" / "ai_qa_provider.py").read_text(encoding="utf-8")
    assert '"openai"' in provider_source and '"deepseek"' in provider_source


def test_governance_drift_closes_capability(tmp_path, monkeypatch):
    app, content_dir = _fresh_app(tmp_path, monkeypatch)
    governance_path = content_dir / "ai_qa_governance.json"
    governance = json.loads(governance_path.read_text(encoding="utf-8"))
    governance["participant_feature_enabled"] = True
    governance_path.write_text(json.dumps(governance, ensure_ascii=False), encoding="utf-8")
    with app.app_context():
        capability = importlib.import_module("services.ai_capability_service")
        decision = capability.resolve_ai_capability(
            {"id": "f19-researcher", "role": "researcher"}, "sandbox"
        )

    assert decision.enabled is False
    assert decision.reason_code == "ai_governance_drift"


def test_future_production_gate_is_human_owned_and_never_auto_passes():
    policy = json.loads((ROOT / "content" / "ai_capability_policy.json").read_text(encoding="utf-8"))
    gate = policy["future_production_gate"]

    assert gate["automatic_approval_allowed"] is False
    assert gate["status"] == "pending_external"
    assert set(gate["required_evidence"]) == {
        "participant_consent",
        "provider_terms",
        "data_region",
        "retention_and_deletion",
        "red_team",
        "human_on_call",
        "budget",
        "rollback_drill",
    }
    validator = importlib.import_module("scripts.validate_content")
    assert validator.validate_ai_capability_policy_content(ROOT / "content") == []


def test_miniprogram_entry_defaults_closed_and_network_failure_does_not_reveal_it():
    source = (ROOT / "apps" / "miniprogram" / "pages" / "profile" / "index.js").read_text(encoding="utf-8")

    assert "participant_entry_visible" in source
    assert "buildSupportEntries(false" in source
    assert "getAiQaConfig().catch(() => null)" in source


def test_fake_and_unavailable_copy_are_not_presented_as_real_ai_answers():
    mini = (ROOT / "apps" / "miniprogram" / "pages" / "support-assistant" / "index.js").read_text(encoding="utf-8")
    web = (ROOT / "apps" / "web" / "src" / "pages" / "AiQaSandboxPage.tsx").read_text(encoding="utf-8")

    assert "合成问答演示" in mini
    assert "fake provider" not in web
    assert "合成模拟器" in web


def test_f19_additive_migration_and_database_head_are_registered():
    migrations = (BACKEND / "services" / "schema_migration_service.py").read_text(encoding="utf-8")
    profile = json.loads((ROOT / "config" / "rc0810" / "database_profiles.json").read_text(encoding="utf-8"))

    assert "2026_08_25_075" in migrations
    assert "ai_capability_decisions" in migrations
    assert profile["profiles"]["production"]["explicit_migration_head"] == "2026_08_25_076"
