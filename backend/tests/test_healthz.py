import importlib
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = PROJECT_ROOT / "backend"


def _fresh_app(tmp_path, monkeypatch):
    sys.path.insert(0, str(BACKEND_ROOT))
    for name in list(sys.modules):
        if name in {"app", "config", "database", "models"} or name.startswith("routes.") or name.startswith("services."):
            sys.modules.pop(name, None)
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "safehome-test.sqlite3"))
    monkeypatch.setenv("CONTENT_DIR", str(PROJECT_ROOT / "content"))
    monkeypatch.setenv("ADMIN_EXPORT_TOKEN", "test-secret-token")
    module = importlib.import_module("app")
    return module.app


def test_healthz_returns_lightweight_status_without_secret(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()

    response = client.get("/healthz")

    assert response.status_code == 200
    data = response.get_json()
    app_module = importlib.import_module("app")
    assert data["ok"] is True
    assert data["service"] == "safehome-backend"
    assert data["version"] == app_module.SERVICE_VERSION
    assert set(data) == {"ok", "service", "version"}
    assert "test-secret-token" not in response.get_data(as_text=True)


def test_deep_healthz_checks_database_and_content(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()

    response = client.get("/healthz/deep")

    assert response.status_code == 200
    data = response.get_json()
    database = importlib.import_module("database")
    assert data["ok"] is True
    assert data["database"]["ok"] is True
    assert data["database"]["expected_schema_version"] == database.CURRENT_SCHEMA_VERSION
    assert data["database"]["current_schema_version"] == database.CURRENT_SCHEMA_VERSION
    assert data["database"]["schema_version_ok"] is True
    assert data["database"]["required_tables_ok"] is True
    assert data["database"]["missing_tables"] == []
    assert data["database"]["database_path_parent_exists"] is True
    assert data["database"]["database_file_exists"] is True
    assert data["database"]["training_cards_count"] > 0
    assert data["database"]["content_training_cards_count"] == data["database"]["training_cards_count"]
    assert data["database"]["training_cards_sync_ok"] is True
    assert data["database"]["assessment_worksheets_count"] > 0
    assert data["database"]["assessment_worksheets_count"] >= data["database"]["content_assessment_worksheets_count"]
    assert data["database"]["worksheets_sync_ok"] is True
    assert data["database"]["identity_uniqueness_ok"] is True
    assert data["database"]["identity_duplicate_groups"] == {"phone_hash": 0, "username": 0, "wechat_openid": 0}
    assert data["database"]["identity_unique_indexes_ok"] is True
    assert data["content"]["ok"] is True
    assert data["content"]["required_files_ok"] is True
    assert data["content"]["missing_files"] == []
    assert data["content"]["content_versions"]["assessment_worksheets.json"]
    assert len(data["content"]["relationship_profile_model_versions"]) == 3
    assert data["content"]["profile_models_ok"] is True
    assert data["content"]["invalid_profile_artifacts"] == []
    assert data["content"]["ungoverned_profile_models"] == []
    assert data["runtime_metrics"]["api_responses_total"] >= 0
    assert data["runtime_metrics"]["api_error_rate"] >= 0
    assert "请求正文" in data["runtime_metrics"]["privacy"]
    assert data["operational_backlog"]["ok"] is True
    assert data["operational_backlog"]["risk_review_pending"] == 0
    assert "test-secret-token" not in response.get_data(as_text=True)


def test_readyz_checks_database_and_content(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()

    response = client.get("/readyz")

    assert response.status_code == 200
    data = response.get_json()
    assert data["ok"] is True
    assert data["database"]["ok"] is True
    assert data["content"]["ok"] is True
    assert "test-secret-token" not in response.get_data(as_text=True)


def test_create_app_accepts_temporary_config_overrides(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    import app as app_module

    override_path = tmp_path / "override.sqlite3"
    override_app = app_module.create_app(
        config_overrides={
            "APP_ENV": "development",
            "DATABASE_PATH": override_path,
            "CONTENT_DIR": PROJECT_ROOT / "content",
            "ADMIN_EXPORT_TOKEN": "override-admin-token",
        },
        init_database=True,
    )

    response = override_app.test_client().get("/readyz")

    assert app.config["DATABASE_PATH"] != override_path
    assert override_app.config["DATABASE_PATH"] == override_path
    assert override_path.exists()
    assert response.status_code == 200


def test_unknown_route_returns_stable_json_error(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()

    response = client.get("/missing-route")
    body = response.get_json()

    assert response.status_code == 404
    assert body["ok"] is False
    assert body["error"] == {"code": "not_found", "message": "没有找到对应接口。"}
    assert body["request_id"] == response.headers["X-Request-ID"]


def test_unhandled_exception_returns_stable_json_error(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)

    @app.get("/boom")
    def boom():
        raise RuntimeError("database password leaked in raw exception")

    response = app.test_client().get("/boom")
    body = response.get_json()

    assert response.status_code == 500
    assert body["ok"] is False
    assert body["error"] == {"code": "internal_error", "message": "服务暂时没有响应，请稍后再试。"}
    assert body["request_id"] == response.headers["X-Request-ID"]
    assert "database password" not in response.get_data(as_text=True)


def test_request_id_is_forwarded_or_replaced_and_added_to_errors(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()

    forwarded = client.get("/healthz", headers={"X-Request-ID": "client-request-123"})
    replaced = client.get("/healthz", headers={"X-Request-ID": "bad request id with spaces"})
    failed = client.get("/missing-route", headers={"X-Request-ID": "client-error-123"})

    assert forwarded.headers["X-Request-ID"] == "client-request-123"
    assert replaced.headers["X-Request-ID"] != "bad request id with spaces"
    assert len(replaced.headers["X-Request-ID"]) == 32
    assert failed.get_json()["request_id"] == "client-error-123"


def test_readiness_does_not_expose_filesystem_or_mysql_connection_details(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    response = app.test_client().get("/readyz")
    body = response.get_json()

    assert "path" not in body["database"]
    assert "mysql" not in body["database"]
    assert "content_dir" not in body["content"]
    assert str(tmp_path) not in response.get_data(as_text=True)
