import importlib
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"


def _production_app(tmp_path, monkeypatch):
    if str(BACKEND) not in sys.path:
        sys.path.insert(0, str(BACKEND))
    for name in list(sys.modules):
        if name in {"app", "config", "database", "models"} or name.startswith(
            ("routes.", "services.")
        ):
            sys.modules.pop(name, None)

    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("DB_PROVIDER", "sqlite")
    monkeypatch.setenv("ALLOW_PRODUCTION_SQLITE", "1")
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "p1-network.sqlite3"))
    monkeypatch.setenv("CONTENT_DIR", str(ROOT / "content"))
    monkeypatch.setenv("SECRET_KEY", "p1-network-security-test-secret-key-32-plus")
    monkeypatch.setenv("ADMIN_EXPORT_TOKEN", "p1-network-admin-token")
    monkeypatch.setenv("INTERNAL_HEALTH_TOKEN", "p1-internal-health-token")
    return importlib.import_module("app").app


def test_production_readyz_is_redacted_for_anonymous_probe(tmp_path, monkeypatch):
    app = _production_app(tmp_path, monkeypatch)
    response = app.test_client().get("/readyz")

    assert response.status_code in {200, 503}
    body = response.get_json()
    assert set(body) == {"ok", "service", "version"}
    assert body["service"] == "safehome-backend"
    text = response.get_data(as_text=True)
    for forbidden in (
        "database",
        "content",
        "runtime_metrics",
        "operational_backlog",
        "deployment",
    ):
        assert forbidden not in text
    assert response.headers["Cache-Control"] == "no-store"


def test_production_deep_health_requires_internal_token(tmp_path, monkeypatch):
    app = _production_app(tmp_path, monkeypatch)
    client = app.test_client()

    anonymous = client.get("/healthz/deep")
    wrong = client.get(
        "/healthz/deep",
        headers={"X-Internal-Health-Token": "wrong"},
    )
    internal = client.get(
        "/healthz/deep",
        headers={"X-Internal-Health-Token": "p1-internal-health-token"},
    )

    assert anonymous.status_code == 404
    assert wrong.status_code == 404
    assert internal.status_code == 200
    internal_body = internal.get_json()
    assert internal_body["ok"] is True
    assert "database" in internal_body
    assert "content" in internal_body


def test_development_health_behavior_remains_diagnostic(tmp_path, monkeypatch):
    if str(BACKEND) not in sys.path:
        sys.path.insert(0, str(BACKEND))
    for name in list(sys.modules):
        if name in {"app", "config", "database", "models"} or name.startswith(
            ("routes.", "services.")
        ):
            sys.modules.pop(name, None)
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "p1-network-dev.sqlite3"))
    monkeypatch.setenv("CONTENT_DIR", str(ROOT / "content"))
    monkeypatch.delenv("INTERNAL_HEALTH_TOKEN", raising=False)
    app = importlib.import_module("app").app
    client = app.test_client()

    deep = client.get("/healthz/deep")
    ready = client.get("/readyz")

    assert deep.status_code == 200
    assert "database" in deep.get_json()
    assert ready.status_code == 200
    assert "database" in ready.get_json()
