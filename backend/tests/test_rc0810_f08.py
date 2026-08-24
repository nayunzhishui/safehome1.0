import importlib
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"


def _fresh_app(tmp_path, monkeypatch):
    sys.path.insert(0, str(BACKEND))
    for name in list(sys.modules):
        if name in {"app", "config", "database", "models"} or name.startswith(
            ("routes.", "services.")
        ):
            sys.modules.pop(name, None)
    monkeypatch.setenv("APP_ENV", "validation")
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "rc0810-f08.sqlite3"))
    monkeypatch.setenv("CONTENT_DIR", str(ROOT / "content"))
    monkeypatch.setenv("DB_PROVIDER", "sqlite")
    monkeypatch.setenv("DATABASE_DATA_WATERMARK", "synthetic_validation_only")
    monkeypatch.setenv("SECRET_KEY", "rc0810-f08-test-secret-key-that-is-long-enough")
    monkeypatch.setenv("ADMIN_EXPORT_TOKEN", "rc0810-f08-admin-token")
    app = importlib.import_module("app").app
    app.config["APP_ENV"] = "production"
    return app


def _register(client, username):
    response = client.post(
        "/api/auth/register",
        json={"username": username, "password": "password123", "role": "parent"},
    )
    assert response.status_code == 201
    return response.get_json()["data"]


def _login(client, username, **extra):
    return client.post(
        "/api/auth/login",
        json={"username": username, "password": "password123", **extra},
    )


def _headers(token):
    return {"Authorization": f"Bearer {token}"}


def test_logout_is_idempotent_and_revokes_all_tokens_once(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    registered = _register(client, "multi-device-f08")
    second_token = _login(client, "multi-device-f08").get_json()["data"]["token"]

    first = client.post("/api/auth/logout", headers=_headers(registered["token"]))
    assert first.status_code == 200
    assert first.get_json()["data"]["tokens_revoked"] is True

    repeated = client.post("/api/auth/logout", headers=_headers(second_token))
    assert repeated.status_code == 200
    assert repeated.get_json()["data"]["tokens_revoked"] is False
    assert repeated.get_json()["data"]["already_inactive"] is True
    assert client.get("/api/auth/me", headers=_headers(registered["token"])).status_code == 401
    assert client.get("/api/auth/me", headers=_headers(second_token)).status_code == 401

    invalid = client.post("/api/auth/logout", headers=_headers("expired-or-invalid-token"))
    anonymous = client.post("/api/auth/logout")
    assert invalid.status_code == anonymous.status_code == 200
    assert invalid.get_json()["data"]["tokens_revoked"] is False

    with app.app_context():
        from database import get_connection

        with get_connection() as conn:
            user = conn.execute(
                "SELECT auth_epoch FROM users WHERE id = ?", (registered["user"]["id"],)
            ).fetchone()
            audit_count = conn.execute(
                "SELECT COUNT(*) AS count FROM audit_logs WHERE action = 'auth_sessions_revoked'"
            ).fetchone()["count"]
        assert user["auth_epoch"] == 1
        assert audit_count == 1


@pytest.mark.parametrize("username", ["Test1", "wyd"])
def test_pending_logout_rotates_original_historical_account_before_new_token(
    tmp_path, monkeypatch, username
):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    registered = _register(client, username)
    original_id = registered["user"]["id"]
    old_token = registered["token"]

    response = _login(
        client,
        username,
        revoke_previous_sessions=True,
        pending_logout_user_id=original_id,
    )
    assert response.status_code == 200
    data = response.get_json()["data"]
    assert data["user"]["id"] == original_id
    assert data["pending_logout_resolved"] is True
    assert data["pending_logout_user_mismatch"] is False
    assert client.get("/api/auth/me", headers=_headers(old_token)).status_code == 401
    assert client.get("/api/auth/me", headers=_headers(data["token"])).status_code == 200


def test_pending_logout_never_revokes_a_different_account(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    old_account = _register(client, "pending-old-f08")
    other_account = _register(client, "pending-other-f08")

    response = _login(
        client,
        "pending-other-f08",
        revoke_previous_sessions=True,
        pending_logout_user_id=old_account["user"]["id"],
    )
    data = response.get_json()["data"]
    assert data["pending_logout_resolved"] is False
    assert data["pending_logout_user_mismatch"] is True
    assert client.get(
        "/api/auth/me", headers=_headers(other_account["token"])
    ).status_code == 200


def test_clients_call_server_before_local_clear_and_store_no_token_in_pending_marker():
    web_auth = (ROOT / "apps/web/src/services/authState.ts").read_text(encoding="utf-8")
    web_main = (ROOT / "apps/web/src/main.tsx").read_text(encoding="utf-8")
    mini_api = (ROOT / "apps/miniprogram/services/api.js").read_text(encoding="utf-8")
    mini_profile = (ROOT / "apps/miniprogram/pages/profile/index.js").read_text(encoding="utf-8")

    assert "safehome_pending_logout" in web_auth
    assert "auth_token" not in web_auth.split("markPendingLogout", 1)[1].split("}", 1)[0]
    assert web_main.index("await safeHomeApi.logout") < web_main.index("clearAuthSession()")
    logout_block = mini_api.split("logout()", 1)[1].split("createGoal", 1)[0]
    assert logout_block.index("request(API_ENDPOINTS.authLogout") < logout_block.index(
        "clearAuthSession()"
    )
    assert "pending_logout" in logout_block
    assert "await api.logout()" in mini_profile


def test_mini_keeps_account_a_pending_marker_when_account_b_logs_out_successfully():
    script = r"""
const assert = require("assert");
const storage = new Map();
let mode = "fail";
global.getApp = () => ({ globalData: {} });
global.wx = {
  getStorageSync: (key) => storage.get(key),
  setStorageSync: (key, value) => storage.set(key, value),
  removeStorageSync: (key) => storage.delete(key),
  getExtConfigSync: () => ({}),
  getAccountInfoSync: () => ({ miniProgram: { version: "test" } }),
  request: (options) => {
    if (mode === "fail") {
      options.fail({ errCode: "network_error" });
      return;
    }
    const data = options.url.endsWith("/api/auth/login")
      ? { token: "token-b", user: { id: "user-b", auth_epoch: 0 }, pending_logout_resolved: false, pending_logout_user_mismatch: true }
      : { tokens_revoked: true, already_inactive: false, message: "ok" };
    options.success({ statusCode: 200, data: { ok: true, data }, header: {} });
  },
};
const { createSafeHomeApi } = require("./apps/miniprogram/services/api.js");
const api = createSafeHomeApi({ useLocalHttp: true, localHttpBaseUrl: "http://127.0.0.1:5000", defaultUserId: "anonymous-test" });
(async () => {
  storage.set("auth_token", "token-a");
  storage.set("auth_user", { id: "user-a", auth_epoch: 0 });
  const failedLogout = await api.logout();
  assert.strictEqual(failedLogout.pending_logout, true);
  assert.strictEqual(storage.get("safehome_pending_logout").user_id, "user-a");
  assert.strictEqual(JSON.stringify(storage.get("safehome_pending_logout")).includes("token-a"), false);

  mode = "success";
  await api.login({ username: "account-b", password: "password123" });
  assert.strictEqual(storage.get("safehome_pending_logout").user_id, "user-a");
  await api.logout();
  assert.strictEqual(storage.get("safehome_pending_logout").user_id, "user-a");
})().catch((error) => { console.error(error); process.exit(1); });
"""
    completed = subprocess.run(
        ["node", "-e", script], cwd=ROOT, capture_output=True, text=True, check=False
    )
    assert completed.returncode == 0, completed.stderr


def test_web_pending_clear_is_scoped_to_current_logout_user():
    source = (ROOT / "apps/web/src/services/authState.ts").read_text(encoding="utf-8")
    main = (ROOT / "apps/web/src/main.tsx").read_text(encoding="utf-8")
    helper = source.split("export function clearPendingLogoutForUser", 1)[1].split(
        "export function logout", 1
    )[0]
    assert "pending.user_id === userId" in helper
    assert "clearPendingLogoutForUser(authUser.id)" in main
