import importlib
import sys
from pathlib import Path
from urllib.error import URLError


PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = PROJECT_ROOT / "backend"


def _fresh_app(tmp_path, monkeypatch, app_env="development"):
    sys.path.insert(0, str(BACKEND_ROOT))
    for name in list(sys.modules):
        if name in {"app", "config", "database", "models"} or name.startswith("routes.") or name.startswith("services."):
            sys.modules.pop(name, None)
    runtime_env = "validation" if app_env == "production" else app_env
    monkeypatch.setenv("APP_ENV", runtime_env)
    monkeypatch.delenv("ADMIN_EXPORT_TOKEN", raising=False)
    monkeypatch.delenv("WECHAT_APPID", raising=False)
    monkeypatch.delenv("WECHAT_SECRET", raising=False)
    if app_env == "production":
        monkeypatch.setenv("DB_PROVIDER", "sqlite")
        monkeypatch.setenv("DATABASE_DATA_WATERMARK", "synthetic_validation_only")
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


def test_admin_can_rotate_existing_researcher_credentials_explicitly(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    headers = {"X-Admin-Token": "safehome-local-admin-token"}
    original = {
        "username": "safehome_researcher_01",
        "password": "initial-password-123",
        "role": "researcher",
        "nickname": "正式研究者",
    }

    created = client.post("/api/auth/admin-create-account", json=original, headers=headers)
    conflict = client.post("/api/auth/admin-create-account", json=original, headers=headers)
    rotated = client.post(
        "/api/auth/admin-create-account",
        json={**original, "password": "rotated-password-456", "rotate_existing": True},
        headers=headers,
    )
    old_login = client.post("/api/auth/login", json={"username": original["username"], "password": original["password"]})
    new_login = client.post("/api/auth/login", json={"username": original["username"], "password": "rotated-password-456"})

    assert created.status_code == 201
    assert conflict.status_code == 409
    assert rotated.status_code == 200
    assert rotated.get_json()["data"]["credentials_rotated"] is True
    assert old_login.status_code == 401
    assert new_login.status_code == 200
    assert new_login.get_json()["data"]["user"]["role"] == "researcher"


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
    monkeypatch.setenv("TRUST_CLOUDBASE_IDENTITY_HEADERS", "1")
    app = _fresh_app(tmp_path, monkeypatch, app_env="production")
    client = app.test_client()

    response = client.post(
        "/api/auth/wechat-login",
        headers={"X-WX-OPENID": "cloudbase-openid-1", "X-WX-SOURCE": "wx_client"},
        json={"nickname": "云托管用户"},
    )

    assert response.status_code == 200
    body = response.get_json()
    assert body["data"]["token"]
    assert body["data"]["dev_fallback"] is False
    assert body["data"]["identity_source"] == "cloudbase_header"


def test_cloudbase_identity_headers_are_ignored_without_explicit_trust(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch, app_env="production")
    client = app.test_client()

    response = client.post(
        "/api/auth/wechat-login",
        headers={"X-WX-OPENID": "spoofed-openid", "X-WX-SOURCE": "wx_client"},
        json={"nickname": "伪造请求"},
    )

    assert response.status_code == 400
    assert response.get_json()["error"]["code"] == "validation_error"

    from database import get_connection

    with get_connection() as conn:
        created = conn.execute(
            "SELECT COUNT(*) AS count FROM users WHERE source = 'wechat'"
        ).fetchone()
    assert created["count"] == 0


def test_wechat_login_reuses_identity_and_rejects_disabled_account(tmp_path, monkeypatch):
    monkeypatch.setenv("TRUST_CLOUDBASE_IDENTITY_HEADERS", "1")
    app = _fresh_app(tmp_path, monkeypatch, app_env="production")
    client = app.test_client()
    headers = {
        "X-WX-OPENID": "cloudbase-repeat-login",
        "X-WX-SOURCE": "wx_devtools",
    }

    first = client.post("/api/auth/wechat-login", headers=headers, json={"nickname": "首次"})
    second = client.post("/api/auth/wechat-login", headers=headers, json={"nickname": "再次"})

    assert first.status_code == 200
    assert second.status_code == 200
    first_user = first.get_json()["data"]["user"]
    second_user = second.get_json()["data"]["user"]
    assert first_user["id"] == second_user["id"]
    assert first_user["role"] == "parent"

    from database import get_connection

    with get_connection() as conn:
        conn.execute(
            "UPDATE users SET status = 'disabled' WHERE id = ?",
            (first_user["id"],),
        )
        conn.commit()

    disabled = client.post("/api/auth/wechat-login", headers=headers, json={})
    assert disabled.status_code == 403
    assert disabled.get_json()["error"]["code"] == "account_inactive"


def test_cloudbase_identity_matching_appid_is_still_rejected_without_explicit_trust(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch, app_env="production")
    monkeypatch.setenv("WECHAT_APPID", "wx-test-appid")
    monkeypatch.setenv("WECHAT_SECRET", "test-secret")
    client = app.test_client()

    response = client.post(
        "/api/auth/wechat-login",
        headers={
            "X-WX-OPENID": "cloudbase-guarded-openid",
            "X-WX-APPID": "wx-test-appid",
            "X-WX-SOURCE": "wx_client",
        },
        json={},
    )

    assert response.status_code == 400
    assert response.get_json()["error"]["code"] == "validation_error"


def test_cloudbase_identity_guarded_mode_rejects_mismatched_appid(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch, app_env="production")
    monkeypatch.setenv("WECHAT_APPID", "wx-test-appid")
    monkeypatch.setenv("WECHAT_SECRET", "test-secret")
    client = app.test_client()

    response = client.post(
        "/api/auth/wechat-login",
        headers={
            "X-WX-OPENID": "cloudbase-guarded-openid",
            "X-WX-APPID": "wx-other-appid",
            "X-WX-SOURCE": "wx_client",
        },
        json={},
    )

    assert response.status_code == 400
    assert response.get_json()["error"]["code"] == "validation_error"


def test_cloudbase_identity_matching_appid_without_source_is_rejected_without_explicit_trust(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch, app_env="production")
    monkeypatch.setenv("WECHAT_APPID", "wx-test-appid")
    monkeypatch.setenv("WECHAT_SECRET", "test-secret")
    client = app.test_client()

    response = client.post(
        "/api/auth/wechat-login",
        headers={
            "X-WX-OPENID": "cloudbase-no-source-openid",
            "X-WX-APPID": "wx-test-appid",
        },
        json={},
    )

    assert response.status_code == 400
    assert response.get_json()["error"]["code"] == "validation_error"


def test_wechat_login_reports_network_failure_without_leaking_credentials(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch, app_env="production")
    monkeypatch.setenv("WECHAT_APPID", "wx-test-appid")
    monkeypatch.setenv("WECHAT_SECRET", "secret-must-not-leak")
    auth_module = importlib.import_module("routes.auth")

    def fail_network(*_args, **_kwargs):
        raise URLError(OSError("network unreachable"))

    monkeypatch.setattr(auth_module, "urlopen", fail_network)
    response = app.test_client().post(
        "/api/auth/wechat-login",
        json={"code": "one-time-code-must-not-leak"},
    )

    assert response.status_code == 502
    body = response.get_json()
    assert body["error"]["code"] == "wechat_network_unavailable"
    assert "secret-must-not-leak" not in str(body)
    assert "one-time-code-must-not-leak" not in str(body)


def test_cloudbase_identity_requires_exact_source_and_valid_openid(tmp_path, monkeypatch):
    monkeypatch.setenv("TRUST_CLOUDBASE_IDENTITY_HEADERS", "1")
    app = _fresh_app(tmp_path, monkeypatch, app_env="production")
    client = app.test_client()

    for headers in [
        {"X-WX-OPENID": "valid-openid-1", "X-WX-SOURCE": "public-http"},
        {"X-WX-OPENID": "valid-openid-1", "X-WX-SOURCE": "wx-cloudbase"},
        {"X-WX-OPENID": "bad openid", "X-WX-SOURCE": "wx_client"},
    ]:
        response = client.post("/api/auth/wechat-login", headers=headers, json={})
        assert response.status_code == 400
        assert response.get_json()["error"]["code"] == "validation_error"


def test_phone_login_creates_and_reuses_verified_phone_without_storing_raw(tmp_path, monkeypatch, caplog):
    monkeypatch.setenv("TRUST_CLOUDBASE_IDENTITY_HEADERS", "1")
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    auth_module = importlib.import_module("routes.auth")
    monkeypatch.setattr(
        auth_module,
        "_wechat_phone_from_code",
        lambda _code: {"phone_number": "13800138000", "pure_phone_number": "13800138000", "country_code": "86"},
    )
    headers = {"X-WX-OPENID": "cloudbase-phone-openid", "X-WX-SOURCE": "wx_client"}

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
    assert "13800138000" not in caplog.text


def test_phone_login_returns_safe_configuration_error_without_token_source(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch, app_env="production")
    client = app.test_client()

    response = client.post("/api/auth/phone-login", json={"code": "phone-code"})

    assert response.status_code == 503
    body = response.get_json()
    assert body["error"]["code"] == "wechat_phone_config_missing"
    assert "WECHAT_SECRET" not in body["error"]["message"]


def test_phone_login_conflict_is_non_destructive_and_redacted(tmp_path, monkeypatch):
    monkeypatch.setenv("TRUST_CLOUDBASE_IDENTITY_HEADERS", "1")
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    auth_module = importlib.import_module("routes.auth")
    monkeypatch.setattr(
        auth_module,
        "_wechat_phone_from_code",
        lambda _code: {
            "phone_number": "13800138000",
            "pure_phone_number": "13800138000",
            "country_code": "86",
        },
    )
    phone_only = client.post("/api/auth/phone-login", json={"code": "first-phone-code"})
    assert phone_only.status_code == 200
    phone_user_id = phone_only.get_json()["data"]["user"]["id"]

    headers = {
        "X-WX-OPENID": "different-wechat-identity",
        "X-WX-SOURCE": "wx_client",
    }
    wechat_only = client.post("/api/auth/wechat-login", headers=headers, json={})
    assert wechat_only.status_code == 200
    wechat_user_id = wechat_only.get_json()["data"]["user"]["id"]
    assert phone_user_id != wechat_user_id

    conflict = client.post(
        "/api/auth/phone-login",
        headers=headers,
        json={"code": "conflict-phone-code"},
    )
    assert conflict.status_code == 409
    body = conflict.get_json()
    assert body["error"]["code"] == "phone_account_conflict"
    assert "13800138000" not in str(body)

    from database import get_connection

    with get_connection() as conn:
        phone_row = conn.execute(
            "SELECT * FROM users WHERE id = ?", (phone_user_id,)
        ).fetchone()
        wechat_row = conn.execute(
            "SELECT * FROM users WHERE id = ?", (wechat_user_id,)
        ).fetchone()
    assert phone_row["phone_hash"]
    assert wechat_row["phone_hash"] is None
    assert "13800138000" not in str(dict(phone_row))
    assert "13800138000" not in str(dict(wechat_row))


def test_phone_login_rejects_disabled_phone_account(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    auth_module = importlib.import_module("routes.auth")
    monkeypatch.setattr(
        auth_module,
        "_wechat_phone_from_code",
        lambda _code: {
            "phone_number": "13900139000",
            "pure_phone_number": "13900139000",
            "country_code": "86",
        },
    )
    first = client.post("/api/auth/phone-login", json={"code": "phone-code-1"})
    assert first.status_code == 200
    user_id = first.get_json()["data"]["user"]["id"]

    from database import get_connection

    with get_connection() as conn:
        conn.execute("UPDATE users SET status = 'disabled' WHERE id = ?", (user_id,))
        conn.commit()

    disabled = client.post("/api/auth/phone-login", json={"code": "phone-code-2"})
    assert disabled.status_code == 403
    assert disabled.get_json()["error"]["code"] == "account_inactive"


def test_auth_capabilities_report_missing_external_configuration_without_secrets(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch, app_env="production")
    client = app.test_client()

    response = client.get("/api/auth/capabilities")

    assert response.status_code == 200
    data = response.get_json()["data"]
    assert data["account_password"]["available"] is True
    assert data["wechat_login"] == {"available": False, "mode": "not_configured"}
    assert data["phone_login"] == {"available": False, "mode": "not_configured"}
    assert "WECHAT_SECRET" not in str(data)
    assert "phone_number" not in data
    assert "access_token" not in data


def test_auth_capabilities_report_cloudbase_identity_when_trust_is_configured(tmp_path, monkeypatch):
    monkeypatch.setenv("TRUST_CLOUDBASE_IDENTITY_HEADERS", "1")
    app = _fresh_app(tmp_path, monkeypatch, app_env="production")
    client = app.test_client()

    response = client.get("/api/auth/capabilities")

    assert response.status_code == 200
    data = response.get_json()["data"]
    assert data["wechat_login"] == {"available": True, "mode": "cloudbase_identity"}


def test_cloudbase_identity_accepts_official_developer_tool_source(tmp_path, monkeypatch):
    monkeypatch.setenv("TRUST_CLOUDBASE_IDENTITY_HEADERS", "1")
    app = _fresh_app(tmp_path, monkeypatch, app_env="production")
    client = app.test_client()

    response = client.post(
        "/api/auth/wechat-login",
        headers={"X-WX-OPENID": "cloudbase-openid-devtools", "X-WX-SOURCE": "wx_devtools"},
        json={},
    )

    assert response.status_code == 200
    assert response.get_json()["data"]["identity_source"] == "cloudbase_header"


def test_auth_capabilities_detect_cloudbase_phone_token_file(tmp_path, monkeypatch):
    token_path = tmp_path / "cloudbase_access_token"
    token_path.write_text("test-token", encoding="utf-8")
    monkeypatch.setenv("CLOUDBASE_ACCESS_TOKEN_PATH", str(token_path))
    app = _fresh_app(tmp_path, monkeypatch, app_env="production")
    client = app.test_client()

    response = client.get("/api/auth/capabilities")

    assert response.status_code == 200
    data = response.get_json()["data"]
    assert data["phone_login"] == {"available": True, "mode": "cloudbase_access_token"}


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
