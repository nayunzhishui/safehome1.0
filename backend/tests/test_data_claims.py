import importlib
import os
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = PROJECT_ROOT / "backend"


def _fresh_app(tmp_path):
    sys.path.insert(0, str(BACKEND_ROOT))
    for name in list(sys.modules):
        if name in {"app", "config", "database", "models"} or name.startswith("routes.") or name.startswith("services."):
            sys.modules.pop(name, None)
    os.environ["DATABASE_PATH"] = str(tmp_path / "safehome-data-claim.sqlite3")
    os.environ["CONTENT_DIR"] = str(PROJECT_ROOT / "content")
    return importlib.import_module("app").app


def _seed_anonymous_records(anonymous_id):
    database = importlib.import_module("database")
    timestamp = database.now_iso()
    with database.get_connection() as conn:
        database.ensure_user(conn, anonymous_id, "本机试用")
        conn.execute(
            """
            INSERT INTO goals (id, user_id, scene, smart_goal, motivation, start_date, status, created_at, updated_at)
            VALUES (?, ?, '沟通', '先暂停三秒', NULL, NULL, 'active', ?, ?)
            """,
            (database.new_id("goal"), anonymous_id, timestamp, timestamp),
        )
        conn.execute(
            """
            INSERT INTO emotion_thermometer (id, user_id, intensity_level, brief_text, created_at, updated_at)
            VALUES (?, ?, 5, 'PRIVATE_TRIAL_TEXT', ?, ?)
            """,
            (database.new_id("thermo"), anonymous_id, timestamp, timestamp),
        )
        conn.commit()


def _register(client, username, anonymous_id):
    response = client.post(
        "/api/auth/register",
        json={"username": username, "password": "password-123", "role": "parent", "anonymous_id": anonymous_id},
    )
    assert response.status_code == 201
    data = response.get_json()["data"]
    return data["user"]["id"], {"Authorization": f"Bearer {data['token']}"}


def test_anonymous_records_require_explicit_confirmation_and_claim_once(tmp_path):
    app = _fresh_app(tmp_path)
    client = app.test_client()
    anonymous_id = "web_user_1760000000000_a1b2c3"
    _seed_anonymous_records(anonymous_id)
    user_id, headers = _register(client, "claim-owner", anonymous_id)

    assert client.get("/api/auth/data-claim-preview").status_code == 401
    preview_response = client.get("/api/auth/data-claim-preview", headers=headers)
    assert preview_response.status_code == 200
    preview = preview_response.get_json()["data"]
    assert preview["available"] is True
    assert preview["total_records"] == 2
    assert "PRIVATE_TRIAL_TEXT" not in str(preview)

    missing_confirmation = client.post(
        "/api/auth/data-claim",
        headers=headers,
        json={"claim_id": preview["claim_id"]},
    )
    assert missing_confirmation.status_code == 400

    claimed = client.post(
        "/api/auth/data-claim",
        headers=headers,
        json={"claim_id": preview["claim_id"], "confirm": True},
    )
    assert claimed.status_code == 200
    result = claimed.get_json()["data"]
    assert result["status"] == "claimed"
    assert result["total_records"] == 2
    assert result["already_completed"] is False

    repeated = client.post(
        "/api/auth/data-claim",
        headers=headers,
        json={"claim_id": preview["claim_id"], "confirm": True},
    ).get_json()["data"]
    assert repeated["already_completed"] is True

    database = importlib.import_module("database")
    with database.get_connection() as conn:
        assert conn.execute("SELECT COUNT(*) AS count FROM goals WHERE user_id = ?", (user_id,)).fetchone()["count"] == 1
        assert conn.execute("SELECT COUNT(*) AS count FROM emotion_thermometer WHERE user_id = ?", (user_id,)).fetchone()["count"] == 1
        assert conn.execute("SELECT status FROM users WHERE id = ?", (anonymous_id,)).fetchone()["status"] == "merged"
        assert conn.execute("SELECT COUNT(*) AS count FROM audit_logs WHERE action = 'anonymous_data_claimed'").fetchone()["count"] == 1


def test_claim_candidate_cannot_be_used_by_another_account(tmp_path):
    app = _fresh_app(tmp_path)
    client = app.test_client()
    first_anonymous = "wx_user_1760000000001_aabbcc"
    second_anonymous = "wx_user_1760000000002_ddeeff"
    _seed_anonymous_records(first_anonymous)
    _seed_anonymous_records(second_anonymous)
    _first_id, first_headers = _register(client, "claim-first", first_anonymous)
    _second_id, second_headers = _register(client, "claim-second", second_anonymous)
    second_claim_id = client.get("/api/auth/data-claim-preview", headers=second_headers).get_json()["data"]["claim_id"]

    forbidden = client.post(
        "/api/auth/data-claim",
        headers=first_headers,
        json={"claim_id": second_claim_id, "confirm": True},
    )
    assert forbidden.status_code == 404
