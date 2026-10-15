"""Owner claim, staff role grants and the all-participants research scope; synthetic accounts only."""

import importlib
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = PROJECT_ROOT / "backend"
OWNER_CODE = "synthetic-owner-claim-0001"


def _fresh_app(tmp_path, monkeypatch, *, owner_code=OWNER_CODE):
    sys.path.insert(0, str(BACKEND_ROOT))
    for name in list(sys.modules):
        if name in {"app", "config", "database", "models"} or name.startswith("routes.") or name.startswith("services."):
            sys.modules.pop(name, None)
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.delenv("WECHAT_APPID", raising=False)
    monkeypatch.delenv("WECHAT_SECRET", raising=False)
    monkeypatch.delenv("RESEARCH_PARTICIPANT_SCOPE", raising=False)
    if owner_code:
        monkeypatch.setenv("OWNER_CLAIM_CODE", owner_code)
    else:
        monkeypatch.delenv("OWNER_CLAIM_CODE", raising=False)
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "owner-accounts.sqlite3"))
    monkeypatch.setenv("CONTENT_DIR", str(PROJECT_ROOT / "content"))
    return importlib.import_module("app").app


def _wechat_login(client, code):
    response = client.post("/api/auth/wechat-login", json={"code": code, "nickname": f"合成-{code}"})
    assert response.status_code == 200, response.get_json()
    data = response.get_json()["data"]
    return data["user"], {"Authorization": f"Bearer {data['token']}"}


def _claim_owner(client, headers):
    response = client.post("/api/auth/owner-claim", headers=headers, json={"code": OWNER_CODE})
    assert response.status_code == 200, response.get_json()
    data = response.get_json()["data"]
    return {"Authorization": f"Bearer {data['token']}"}


def _audit_actions(action):
    database = importlib.import_module("database")
    with database.get_connection() as conn:
        rows = conn.execute(
            "SELECT target_id, metadata_json FROM audit_logs WHERE action = ? ORDER BY sequence_no",
            (action,),
        ).fetchall()
    return [(row["target_id"], row["metadata_json"]) for row in rows]


def test_owner_claim_needs_the_console_code_and_works_once(tmp_path, monkeypatch):
    client = _fresh_app(tmp_path, monkeypatch).test_client()
    owner, headers = _wechat_login(client, "owner-claim-owner")

    assert client.get("/api/auth/owner-claim", headers=headers).get_json()["data"] == {"available": True}
    wrong = client.post("/api/auth/owner-claim", headers=headers, json={"code": "不对的认领码-0000"})
    assert wrong.status_code == 403
    assert wrong.get_json()["error"]["code"] == "owner_claim_code_invalid"

    owner_headers = _claim_owner(client, headers)
    assert client.get("/api/auth/me", headers=owner_headers).get_json()["data"]["user"]["role"] == "admin"
    # Claiming signs out the old session; the claim is audited without the code.
    assert client.get("/api/auth/me", headers=headers).status_code == 401
    claims = _audit_actions("owner_claimed")
    assert [target for target, _ in claims] == [owner["id"]]
    assert OWNER_CODE not in claims[0][1]
    assert client.get("/api/auth/owner-claim", headers=owner_headers).get_json()["data"] == {"available": False}

    _, other_headers = _wechat_login(client, "owner-claim-latecomer")
    assert client.get("/api/auth/owner-claim", headers=other_headers).get_json()["data"] == {"available": False}
    late = client.post("/api/auth/owner-claim", headers=other_headers, json={"code": OWNER_CODE})
    assert late.status_code == 409
    assert late.get_json()["error"]["code"] == "owner_already_claimed"

    # The owner's WeChat login keeps working after becoming admin.
    again, _ = _wechat_login(client, "owner-claim-owner")
    assert again["id"] == owner["id"] and again["role"] == "admin"


def test_owner_claim_is_closed_without_a_code_and_rate_limited(tmp_path, monkeypatch):
    client = _fresh_app(tmp_path, monkeypatch, owner_code="").test_client()
    _, headers = _wechat_login(client, "owner-claim-closed")
    assert client.get("/api/auth/owner-claim", headers=headers).get_json()["data"] == {"available": False}
    closed = client.post("/api/auth/owner-claim", headers=headers, json={"code": OWNER_CODE})
    assert closed.status_code == 404

    client = _fresh_app(tmp_path / "limited", monkeypatch).test_client()
    _, headers = _wechat_login(client, "owner-claim-guessing")
    statuses = [
        client.post("/api/auth/owner-claim", headers=headers, json={"code": f"guess-{index:014d}"}).status_code
        for index in range(6)
    ]
    assert statuses == [403] * 5 + [429]
    registered = client.post(
        "/api/auth/register",
        json={"username": "owner-claim-password", "password": "password-123", "role": "parent"},
    ).get_json()["data"]
    password_headers = {"Authorization": f"Bearer {registered['token']}"}
    assert client.get("/api/auth/owner-claim", headers=password_headers).get_json()["data"] == {"available": False}
    assert client.post("/api/auth/owner-claim", headers=password_headers, json={"code": OWNER_CODE}).status_code == 403


def test_owner_grants_and_takes_back_staff_roles_for_wechat_accounts(tmp_path, monkeypatch):
    client = _fresh_app(tmp_path, monkeypatch).test_client()
    _, headers = _wechat_login(client, "roles-owner")
    owner_headers = _claim_owner(client, headers)
    helper, helper_headers = _wechat_login(client, "roles-helper")
    registered = client.post(
        "/api/auth/register",
        json={"username": "roles-password", "password": "password-123", "role": "parent"},
    ).get_json()["data"]

    assert client.get("/api/auth/accounts", headers=helper_headers).status_code == 403
    listing = client.get("/api/auth/accounts", headers=owner_headers, query_string={"q": "roles-helper"})
    assert listing.status_code == 200
    items = listing.get_json()["data"]["items"]
    assert [(item["id"], item["grantable"]) for item in items] == [(helper["id"], True)]
    assert set(items[0]) == {"id", "nickname", "role", "wechat_account", "grantable", "created_at", "last_login_at"}
    everyone = client.get("/api/auth/accounts", headers=owner_headers).get_json()["data"]["items"]
    assert everyone[0]["role"] == "admin" and everyone[0]["grantable"] is False
    assert {item["id"]: item["grantable"] for item in everyone}[registered["user"]["id"]] is False

    granted = client.post(f"/api/auth/accounts/{helper['id']}/role", headers=owner_headers, json={"role": "researcher"})
    assert granted.status_code == 200
    assert granted.get_json()["data"]["account"]["role"] == "researcher"
    assert client.get("/api/auth/me", headers=helper_headers).status_code == 401
    relogin, _ = _wechat_login(client, "roles-helper")
    assert relogin["role"] == "researcher"

    def change(user_id, role):
        return client.post(f"/api/auth/accounts/{user_id}/role", headers=owner_headers, json={"role": role})

    assert change(registered["user"]["id"], "researcher").status_code == 403
    assert change(helper["id"], "admin").status_code == 400
    owner_id = client.get("/api/auth/me", headers=owner_headers).get_json()["data"]["user"]["id"]
    assert change(owner_id, "researcher").status_code == 403
    assert change(helper["id"], "supervisor").get_json()["data"]["account"]["role"] == "supervisor"
    assert change(helper["id"], "parent").get_json()["data"]["changed"] is True
    assert [target for target, _ in _audit_actions("account_role_changed")] == [helper["id"]] * 3


def test_research_scope_switch_lets_staff_see_every_participant(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    database = importlib.import_module("database")
    access = importlib.import_module("services.research_access_service")
    enrollments = importlib.import_module("services.relationship_enrollment_service")
    workspace = importlib.import_module("routes.research_workspace")
    now = database.now_iso()
    with database.get_connection() as conn:
        for user_id, role in (("scope-parent-a", "parent"), ("scope-parent-b", "parent"), ("scope-researcher", "researcher"), ("scope-supervisor", "supervisor")):
            conn.execute(
                "INSERT INTO users (id, nickname, role, status, created_at, updated_at) VALUES (?, ?, ?, 'active', ?, ?)",
                (user_id, user_id, role, now, now),
            )
        for suffix, assigned in (("a", "scope-researcher"), ("b", None)):
            conn.execute(
                """INSERT INTO relationship_pilot_enrollments
                   (id, user_id, assessment_result_id, worksheet_id, dimensions_json, radar_features_json,
                    profile_json, consent_scope, status, review_status, assigned_researcher_id, created_at, updated_at)
                   VALUES (?, ?, ?, 'regulatory_focus_relationship_18', '[]', '[]', '{}',
                           'relationship_pilot_stage2_v1', 'enrolled', 'pending_review', ?, ?, ?)""",
                (f"scope-enrollment-{suffix}", f"scope-parent-{suffix}", f"scope-result-{suffix}", assigned, now, now),
            )
        conn.commit()
    researcher = {"id": "scope-researcher", "role": "researcher"}
    supervisor = {"id": "scope-supervisor", "role": "supervisor"}

    with app.app_context():
        assert app.config["RESEARCH_PARTICIPANT_SCOPE"] == "assigned"
        assert not access.sees_all_participants(researcher)
        assert access.participant_scope_clause(supervisor, "user_id")[0] != "1 = 1"
        assert workspace._scope_label(researcher) == "assigned_participants"
        listed = enrollments.list_enrollments(researcher).data["items"]
        assert {item["id"]: item.get("scope_status") for item in listed} == {
            "scope-enrollment-a": None,
            "scope-enrollment-b": "claimable",
        }
        assert enrollments.list_enrollments(supervisor).data["items"] == []

        app.config["RESEARCH_PARTICIPANT_SCOPE"] = "all"
        assert access.sees_all_participants(researcher) and access.sees_all_participants(supervisor)
        assert not access.sees_all_participants({"id": "scope-parent-a", "role": "parent"})
        assert access.participant_scope_clause(supervisor, "user_id") == ("1 = 1", [])
        assert workspace._scope_label(supervisor) == "all_participants"
        clause, params = workspace._allowed_user_clause(researcher)
        assert params == [] and "research_scope_assignments" not in clause
        for actor in (researcher, supervisor):
            listed = enrollments.list_enrollments(actor).data["items"]
            assert sorted(item["id"] for item in listed) == ["scope-enrollment-a", "scope-enrollment-b"]
            assert all("scope_status" not in item for item in listed)
