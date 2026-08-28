import importlib
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"


def _fresh_app(tmp_path, monkeypatch, *, app_env="production", content_dir=None):
    sys.path.insert(0, str(BACKEND))
    for name in list(sys.modules):
        if name in {"app", "config", "database", "models"} or name.startswith("routes.") or name.startswith("services."):
            sys.modules.pop(name, None)
    # The real production factory performs an external MySQL readiness check;
    # use the validated local app and override only the request-time environment
    # for these route-level fail-closed assertions.
    import_env = "validation" if app_env == "production" else app_env
    monkeypatch.setenv("APP_ENV", import_env)
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / f"f05-{app_env}.sqlite3"))
    monkeypatch.setenv("CONTENT_DIR", str(content_dir or ROOT / "content"))
    monkeypatch.setenv("DB_PROVIDER", "sqlite")
    monkeypatch.setenv("ALLOW_PRODUCTION_SQLITE", "0")
    monkeypatch.setenv("SECRET_KEY", "f05-test-secret-key-that-is-long-enough")
    monkeypatch.setenv("ADMIN_EXPORT_TOKEN", "f05-admin-token")
    module = importlib.import_module("app")
    if app_env == "production":
        app = module.create_app(config_overrides={"APP_ENV": "validation"}, init_database=False)
        app.config["APP_ENV"] = "production"
        return app
    return module.app


def test_production_ignores_enabled_showcase_content(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch, app_env="production")
    response = app.test_client().get("/api/showcase-access")

    assert response.status_code == 200
    data = response.get_json()["data"]
    assert data["enabled"] is False
    assert data["researcher_platform_full_access"] is False
    assert data["notice"] == "Showcase 在当前环境不可用；正式角色与权限保持不变。"


def _register(client, username, role="parent"):
    result = client.post(
        "/api/auth/register",
        json={"username": username, "password": "StrongPass123!", "role": role},
    )
    assert result.status_code == 201
    return result.get_json()["data"]


def test_production_workspace_header_cannot_elevate_participant(tmp_path, monkeypatch):
    monkeypatch.setenv("SHOWCASE_ACCESS_ENABLED", "1")
    monkeypatch.setenv("SHOWCASE_RESEARCHER_PLATFORM_FULL_ACCESS", "1")
    app = _fresh_app(tmp_path, monkeypatch, app_env="production")
    client = app.test_client()
    account = _register(client, "f05-production-parent")
    response = client.post(
        "/api/research/access/assignments",
        headers={
            "Authorization": f"Bearer {account['token']}",
            "X-SafeHome-Researcher-Workspace": "1",
        },
        json={},
    )

    assert response.status_code == 403
    with app.app_context():
        from database import get_connection

        with get_connection() as conn:
            row = conn.execute(
                "SELECT metadata_json FROM audit_logs WHERE action = ? ORDER BY created_at DESC LIMIT 1",
                ("showcase_elevation_blocked",),
            ).fetchone()
    assert row is not None
    metadata = json.loads(row["metadata_json"])
    assert metadata["actor_role"] == "parent"
    assert metadata["request_id"]


def test_validation_requires_header_and_preserves_original_role(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch, app_env="validation")
    actor = {"id": "parent-one", "role": "parent", "source": "auth_token"}
    with app.app_context():
        from routes.auth_utils import elevate_actor_for_showcase_researcher_platform

        with app.test_request_context("/api/research/access/assignments", method="POST"):
            unchanged = elevate_actor_for_showcase_researcher_platform(actor)
        with app.test_request_context(
            "/api/research/access/assignments",
            method="POST",
            headers={"X-SafeHome-Researcher-Workspace": "1", "X-Request-ID": "f05-validation-request"},
        ):
            elevated = elevate_actor_for_showcase_researcher_platform(actor)

    assert unchanged["role"] == "parent"
    assert elevated["role"] == "admin"
    assert elevated["original_role"] == "parent"
    assert elevated["showcase_full_access"] is True
    with app.app_context():
        from database import get_connection

        with get_connection() as conn:
            row = conn.execute(
                "SELECT metadata_json FROM audit_logs WHERE action = ? ORDER BY created_at DESC LIMIT 1",
                ("showcase_elevation_granted",),
            ).fetchone()
    assert row is not None
    assert json.loads(row["metadata_json"])["request_id"] == "f05-validation-request"


def test_validation_capability_summary_matches_header_authorization(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch, app_env="validation")
    client = app.test_client()
    account = _register(client, "f05-validation-capabilities")
    authorization = {"Authorization": f"Bearer {account['token']}"}

    ordinary = client.get("/api/research/access/capabilities", headers=authorization)
    elevated = client.get(
        "/api/research/access/capabilities",
        headers={**authorization, "X-SafeHome-Researcher-Workspace": "1"},
    )

    ordinary_data = ordinary.get_json()["data"]
    elevated_data = elevated.get_json()["data"]
    assert ordinary_data["effective_role"] == "parent"
    assert ordinary_data["development_exception_active"] is False
    assert "research.assignment.manage" not in ordinary_data["capability_ids"]
    assert elevated_data["effective_role"] == "admin"
    assert elevated_data["development_exception_active"] is True
    assert "research.feedback.write" in elevated_data["capability_ids"]


def test_production_preserves_all_formal_and_participant_roles_on_showcase_paths(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch, app_env="production")
    operations = (
        ("POST", "/api/research/access/assignments"),
        ("POST", "/api/research/analysis/jobs"),
        ("POST", "/api/therapeutic-assessment/production-gate/evaluate"),
        ("POST", "/api/ai-qa/release/transition"),
        ("POST", "/api/content-review/versions/example/publish"),
        ("POST", "/api/operations-governance/packages/example/release"),
        ("PATCH", "/api/security/accounts/example/status"),
    )
    with app.app_context():
        from routes.auth_utils import elevate_actor_for_showcase_researcher_platform

        for role in ("parent", "student", "researcher", "admin"):
            actor = {"id": f"f05-{role}", "role": role, "source": "auth_token"}
            for method, path in operations:
                with app.test_request_context(
                    path,
                    method=method,
                    headers={"X-SafeHome-Researcher-Workspace": "1", "X-Request-ID": f"f05-{role}"},
                ):
                    resolved = elevate_actor_for_showcase_researcher_platform(actor)
                assert resolved["role"] == role, (role, method, path, resolved)
                assert "showcase_full_access" not in resolved


def test_production_policy_declares_no_break_glass_shortcut():
    payload = json.loads((ROOT / "content" / "showcase_access.json").read_text(encoding="utf-8"))
    assert "production" not in payload["allowed_profiles"]
    assert payload["break_glass"]["implemented"] is False
    assert payload["break_glass"]["production_available"] is False
    assert payload["break_glass"]["status"] == "pending_external"
    assert payload["break_glass"]["required_controls"] == [
        "strong_authentication",
        "two_person_approval",
        "bounded_duration",
        "reason",
        "scope",
        "automatic_expiry",
        "audit",
    ]
