import importlib
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = PROJECT_ROOT / "backend"


def _fresh_app(tmp_path, monkeypatch, app_env="development"):
    sys.path.insert(0, str(BACKEND_ROOT))
    for name in list(sys.modules):
        if name in {"app", "config", "database", "models"} or name.startswith("routes.") or name.startswith("services."):
            sys.modules.pop(name, None)
    monkeypatch.setenv("APP_ENV", app_env)
    monkeypatch.delenv("ADMIN_EXPORT_TOKEN", raising=False)
    monkeypatch.delenv("WECHAT_APPID", raising=False)
    monkeypatch.delenv("WECHAT_SECRET", raising=False)
    if app_env == "production":
        monkeypatch.setenv("DB_PROVIDER", "sqlite")
        monkeypatch.setenv("ALLOW_PRODUCTION_SQLITE", "1")
        monkeypatch.setenv("SECRET_KEY", "production-test-secret-key-32-characters")
        monkeypatch.setenv("ADMIN_EXPORT_TOKEN", "production-test-admin-token")
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "safehome-test.sqlite3"))
    monkeypatch.setenv("CONTENT_DIR", str(PROJECT_ROOT / "content"))
    module = importlib.import_module("app")
    return module.app


def _register(client, username: str, role: str):
    return client.post(
        "/api/auth/register",
        json={
            "username": username,
            "password": "password123",
            "role": role,
            "nickname": "测试账号",
        },
    )


def test_public_register_allows_parent_and_student(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()

    for role in ["parent", "student"]:
        response = _register(client, f"{role}-user", role)

        assert response.status_code == 201
        body = response.get_json()
        assert body["ok"] is True
        assert body["data"]["token"]
        assert body["data"]["user"]["role"] == role


def test_public_register_rejects_backend_roles_without_token(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()

    for role in ["admin", "researcher", "supervisor"]:
        response = _register(client, f"{role}-user", role)

        assert response.status_code == 400
        body = response.get_json()
        assert body["ok"] is False
        assert body["error"]["code"] == "validation_error"
        assert "data" not in body or not body.get("data", {}).get("token")


def test_public_registered_accounts_cannot_access_admin_export(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()

    for role in ["parent", "student"]:
        register_response = _register(client, f"{role}-export-user", role)
        assert register_response.status_code == 201
        token = register_response.get_json()["data"]["token"]

        export_response = client.get("/api/admin/export?type=diaries", headers={"Authorization": f"Bearer {token}"})

        assert export_response.status_code == 403


def test_admin_create_account_requires_valid_admin_token(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()

    payload = {
        "username": "created-researcher",
        "password": "password123",
        "role": "researcher",
        "nickname": "研究员账号",
    }

    no_token = client.post("/api/auth/admin-create-account", json=payload)
    wrong_token = client.post("/api/auth/admin-create-account", json=payload, headers={"X-Admin-Token": "wrong-token"})
    ok_response = client.post(
        "/api/auth/admin-create-account",
        json=payload,
        headers={"X-Admin-Token": "safehome-local-admin-token"},
    )

    assert no_token.status_code == 401
    assert wrong_token.status_code == 401
    assert ok_response.status_code == 201
    body = ok_response.get_json()
    assert body["ok"] is True
    assert body["data"]["user"]["role"] == "researcher"
    assert "token" not in body["data"]


def test_admin_created_backend_account_can_login_with_role(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()

    create_response = client.post(
        "/api/auth/admin-create-account",
        json={
            "username": "created-supervisor",
            "password": "password123",
            "role": "supervisor",
            "nickname": "督导账号",
        },
        headers={"X-Admin-Token": "safehome-local-admin-token"},
    )
    assert create_response.status_code == 201

    login_response = client.post(
        "/api/auth/login",
        json={"username": "created-supervisor", "password": "password123"},
    )

    assert login_response.status_code == 200
    body = login_response.get_json()
    assert body["ok"] is True
    assert body["data"]["token"]
    assert body["data"]["user"]["role"] == "supervisor"


def test_admin_create_account_rejects_unknown_role(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()

    response = client.post(
        "/api/auth/admin-create-account",
        json={
            "username": "created-unknown",
            "password": "password123",
            "role": "owner",
        },
        headers={"X-Admin-Token": "safehome-local-admin-token"},
    )

    assert response.status_code == 400
    body = response.get_json()
    assert body["ok"] is False
    assert body["error"]["code"] == "validation_error"


def test_production_wechat_login_uses_cloudbase_identity_headers_without_secret(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch, app_env="production")
    client = app.test_client()

    response = client.post(
        "/api/auth/wechat-login",
        headers={"X-WX-OPENID": "cloudbase-openid-1", "X-WX-SOURCE": "wx-cloudbase"},
        json={"nickname": "云托管用户"},
    )

    assert response.status_code == 200
    body = response.get_json()
    assert body["data"]["token"]
    assert body["data"]["dev_fallback"] is False
    assert body["data"]["identity_source"] == "cloudbase_header"


def test_phone_login_creates_and_reuses_verified_phone_without_storing_raw(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    auth_module = importlib.import_module("routes.auth")
    monkeypatch.setattr(
        auth_module,
        "_wechat_phone_from_code",
        lambda _code: {"phone_number": "13800138000", "pure_phone_number": "13800138000", "country_code": "86"},
    )
    headers = {"X-WX-OPENID": "cloudbase-phone-openid", "X-WX-SOURCE": "wx-cloudbase"}

    first = client.post("/api/auth/phone-login", headers=headers, json={"code": "phone-code-1"})
    second = client.post("/api/auth/phone-login", headers=headers, json={"code": "phone-code-2"})

    assert first.status_code == 200
    assert second.status_code == 200
    first_data = first.get_json()["data"]
    second_data = second.get_json()["data"]
    assert first_data["user"]["id"] == second_data["user"]["id"]
    assert first_data["phone_bound"] is True
    assert first_data["phone_masked"] == "138****8000"

    from database import get_connection

    with get_connection() as conn:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (first_data["user"]["id"],)).fetchone()
    assert row["phone_hash"]
    assert row["phone_verified_at"]
    assert row["phone_source"] == "wechat_phone"
    assert row["source"] == "wechat_phone"
    assert row["phone_or_email"] is None
    assert "13800138000" not in str(dict(row))


def test_phone_login_returns_safe_configuration_error_without_token_source(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch, app_env="production")
    client = app.test_client()

    response = client.post("/api/auth/phone-login", json={"code": "phone-code"})

    assert response.status_code == 503
    body = response.get_json()
    assert body["error"]["code"] == "wechat_phone_config_missing"
    assert "WECHAT_SECRET" not in body["error"]["message"]


def test_wechat_phone_exchange_uses_cloudbase_token_file(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    auth_module = importlib.import_module("routes.auth")
    token_path = tmp_path / "cloudbase_access_token"
    token_path.write_text("cloudbase-token", encoding="utf-8")
    monkeypatch.setenv("CLOUDBASE_ACCESS_TOKEN_PATH", str(token_path))
    observed = {}

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self):
            return (
                b'{"errcode":0,"phone_info":{"phoneNumber":"+86 13800138000",'
                b'"purePhoneNumber":"13800138000","countryCode":"86"}}'
            )

    def fake_urlopen(api_request, timeout):
        observed["url"] = api_request.full_url
        observed["body"] = api_request.data
        observed["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setattr(auth_module, "urlopen", fake_urlopen)
    with app.app_context():
        result = auth_module._wechat_phone_from_code("one-time-code")

    assert "cloudbase_access_token=cloudbase-token" in observed["url"]
    assert b'"code": "one-time-code"' in observed["body"]
    assert observed["timeout"] == 8
    assert result["pure_phone_number"] == "13800138000"
