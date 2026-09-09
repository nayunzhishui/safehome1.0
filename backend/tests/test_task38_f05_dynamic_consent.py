import importlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"


def _app(tmp_path, monkeypatch):
    sys.path.insert(0, str(BACKEND))
    for name in list(sys.modules):
        if name in {"app", "config", "database", "models"} or name.startswith(("routes.", "services.")):
            sys.modules.pop(name, None)
    monkeypatch.setenv("APP_ENV", "testing")
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "f05.sqlite3"))
    monkeypatch.setenv("CONTENT_DIR", str(ROOT / "content"))
    return importlib.import_module("app").app


def _seed(app):
    with app.app_context():
        from database import get_connection, now_iso
        from routes.auth_utils import generate_auth_token
        now = now_iso()
        users = {"p1-f05": "parent", "p2-f05": "parent", "r-f05": "researcher", "s-f05": "supervisor"}
        with get_connection() as conn:
            for user_id, role in users.items():
                conn.execute(
                    "INSERT INTO users (id, nickname, role, status, created_at, updated_at) VALUES (?, ?, ?, 'active', ?, ?)",
                    (user_id, user_id, role, now, now),
                )
            conn.commit()
        return {
            key: {"Authorization": f"Bearer {generate_auth_token({'id': key, 'role': role})}"}
            for key, role in users.items()
        }


def _case(client, headers):
    result = client.post(
        "/api/therapeutic-assessment/cases",
        headers={**headers["p1-f05"], "Idempotency-Key": "f05-case"},
        json={"assessment_question": "我想理解一次互动", "shared_scope": ["question"], "consent": True},
    )
    return result.get_json()["data"]


def _create(client, headers, case_id, **overrides):
    payload = {
        "subject_user_id": "p1-f05",
        "involved_user_ids": ["p2-f05"],
        "content_ref": "diary:private-1",
        "content_sha256": "a" * 64,
        "purpose": "collaborative_assessment",
        "visibility": "private",
        "allowed_viewer_ids": [],
        "expires_at": "2099-01-01T00:00:00+00:00",
        **overrides,
    }
    return client.post(
        f"/api/therapeutic-assessment/cases/{case_id}/data-items",
        headers={**headers["p1-f05"], "Idempotency-Key": overrides.get("key", "f05-create")},
        json={key: value for key, value in payload.items() if key != "key"},
    )


def test_schema_034_and_binding_does_not_grant_access(tmp_path, monkeypatch):
    app = _app(tmp_path, monkeypatch)
    headers = _seed(app)
    client = app.test_client()
    case = _case(client, headers)
    created = _create(client, headers, case["id"]).get_json()["data"]
    denied = client.get(f"/api/therapeutic-assessment/data-items/{created['id']}", headers=headers["p2-f05"])
    assert denied.status_code == 404
    with app.app_context():
        from database import CURRENT_SCHEMA_VERSION
        assert CURRENT_SCHEMA_VERSION >= "2026_07_27_038"


def test_named_professional_only_and_no_raw_content(tmp_path, monkeypatch):
    app = _app(tmp_path, monkeypatch)
    headers = _seed(app)
    client = app.test_client()
    case = _case(client, headers)
    raw = _create(client, headers, case["id"], raw_content="不能存", key="f05-raw")
    created = _create(
        client, headers, case["id"], visibility="professionals",
        allowed_viewer_ids=["r-f05"], key="f05-prof",
    ).get_json()["data"]
    allowed = client.get(f"/api/therapeutic-assessment/data-items/{created['id']}", headers=headers["r-f05"])
    denied = client.get(f"/api/therapeutic-assessment/data-items/{created['id']}", headers=headers["s-f05"])
    assert raw.status_code == 400
    assert allowed.status_code == 200
    assert denied.status_code == 404
    assert "raw_content" not in str(allowed.get_json())


def test_withdrawal_revokes_view_but_preserves_legal_hold_metadata(tmp_path, monkeypatch):
    app = _app(tmp_path, monkeypatch)
    headers = _seed(app)
    client = app.test_client()
    case = _case(client, headers)
    item = _create(
        client, headers, case["id"], visibility="professionals",
        allowed_viewer_ids=["r-f05"], key="f05-withdraw-item",
    ).get_json()["data"]
    withdrawn = client.patch(
        f"/api/therapeutic-assessment/data-items/{item['id']}/consent",
        headers={**headers["p1-f05"], "Idempotency-Key": "f05-withdraw"},
        json={"action": "withdraw", "expected_version": item["version"], "legal_hold_reason": "ethics_review"},
    )
    replay = client.patch(
        f"/api/therapeutic-assessment/data-items/{item['id']}/consent",
        headers={**headers["p1-f05"], "Idempotency-Key": "f05-withdraw"},
        json={"action": "withdraw", "expected_version": item["version"], "legal_hold_reason": "ethics_review"},
    )
    denied = client.get(f"/api/therapeutic-assessment/data-items/{item['id']}", headers=headers["r-f05"])
    assert withdrawn.status_code == 200
    assert replay.status_code == 200
    assert replay.get_json()["data"]["version"] == withdrawn.get_json()["data"]["version"]
    assert withdrawn.get_json()["data"]["status"] == "withdrawn"
    assert withdrawn.get_json()["data"]["retained_under_legal_hold"] is True
    assert denied.status_code == 403


def test_expired_item_and_shared_feedback_require_explicit_confirmation(tmp_path, monkeypatch):
    app = _app(tmp_path, monkeypatch)
    headers = _seed(app)
    client = app.test_client()
    case = _case(client, headers)
    expired = _create(
        client, headers, case["id"], visibility="professionals",
        allowed_viewer_ids=["r-f05"], expires_at="2020-01-01T00:00:00+00:00", key="f05-expired",
    ).get_json()["data"]
    shared = _create(
        client, headers, case["id"], visibility="confirmed_shared_feedback",
        allowed_viewer_ids=["p2-f05"], key="f05-shared",
    ).get_json()["data"]
    expired_read = client.get(f"/api/therapeutic-assessment/data-items/{expired['id']}", headers=headers["r-f05"])
    shared_read = client.get(f"/api/therapeutic-assessment/data-items/{shared['id']}", headers=headers["p2-f05"])
    assert expired_read.status_code == 410
    assert shared_read.status_code == 404


def test_notification_preview_is_minimal(tmp_path, monkeypatch):
    app = _app(tmp_path, monkeypatch)
    headers = _seed(app)
    client = app.test_client()
    case = _case(client, headers)
    item = _create(client, headers, case["id"]).get_json()["data"]
    assert item["notification_preview"] == "你有一项协作资料状态更新，请进入小程序查看。"
    assert "diary:private-1" not in item["notification_preview"]
