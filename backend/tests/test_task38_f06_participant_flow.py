import importlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
MINI = ROOT / "apps" / "miniprogram"
STEPS = (
    "boundary",
    "issue",
    "recent-event",
    "resources",
    "sharing",
    "summary",
    "feedback-check",
    "action-review",
)


def _app(tmp_path, monkeypatch):
    sys.path.insert(0, str(BACKEND))
    for name in list(sys.modules):
        if name in {"app", "config", "database", "models"} or name.startswith(("routes.", "services.")):
            sys.modules.pop(name, None)
    monkeypatch.setenv("APP_ENV", "testing")
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "f06.sqlite3"))
    monkeypatch.setenv("CONTENT_DIR", str(ROOT / "content"))
    return importlib.import_module("app").app


def _seed(app):
    with app.app_context():
        from database import get_connection, now_iso
        from routes.auth_utils import generate_auth_token
        now = now_iso()
        with get_connection() as conn:
            for user_id in ("p1-f06", "p2-f06"):
                conn.execute(
                    "INSERT INTO users (id, nickname, role, status, created_at, updated_at) VALUES (?, ?, 'parent', 'active', ?, ?)",
                    (user_id, user_id, now, now),
                )
            conn.commit()
        return {
            user_id: {"Authorization": f"Bearer {generate_auth_token({'id': user_id, 'role': 'parent'})}"}
            for user_id in ("p1-f06", "p2-f06")
        }


def _case(client, headers):
    response = client.post(
        "/api/therapeutic-assessment/cases",
        headers={**headers, "Idempotency-Key": "f06-case"},
        json={"assessment_question": "我想理解一次互动", "shared_scope": ["question"], "consent": True},
    )
    assert response.status_code == 201
    return response.get_json()["data"]


def _save(client, headers, case_id, step_id, version, key, value="草稿"):
    return client.put(
        f"/api/therapeutic-assessment/cases/{case_id}/participant-drafts/{step_id}",
        headers={**headers, "Idempotency-Key": key},
        json={
            "payload": {"value": value, "selected": ""},
            "expected_version": version,
            "status": "active",
            "client_updated_at": "2026-07-27T12:00:00+08:00",
        },
    )


def test_schema_035_and_cross_device_draft_round_trip(tmp_path, monkeypatch):
    app = _app(tmp_path, monkeypatch)
    headers = _seed(app)
    client = app.test_client()
    case = _case(client, headers["p1-f06"])
    saved = _save(client, headers["p1-f06"], case["id"], "recent_event", 0, "f06-save")
    loaded = client.get(
        f"/api/therapeutic-assessment/cases/{case['id']}/participant-drafts/recent_event",
        headers=headers["p1-f06"],
    )
    assert saved.status_code == 200
    assert loaded.status_code == 200
    assert loaded.get_json()["data"]["payload"]["value"] == "草稿"
    with app.app_context():
        from database import CURRENT_SCHEMA_NAME, CURRENT_SCHEMA_VERSION
        assert CURRENT_SCHEMA_VERSION == "2026_07_27_035"
        assert CURRENT_SCHEMA_NAME == "therapeutic_assessment_participant_flow"


def test_draft_scope_version_conflict_and_idempotent_replay(tmp_path, monkeypatch):
    app = _app(tmp_path, monkeypatch)
    headers = _seed(app)
    client = app.test_client()
    case = _case(client, headers["p1-f06"])
    first = _save(client, headers["p1-f06"], case["id"], "resources", 0, "f06-first")
    second = _save(client, headers["p1-f06"], case["id"], "resources", 1, "f06-second", "第二版")
    replay = _save(client, headers["p1-f06"], case["id"], "resources", 0, "f06-first")
    conflict = _save(client, headers["p1-f06"], case["id"], "resources", 0, "f06-conflict", "另一设备")
    denied = client.get(
        f"/api/therapeutic-assessment/cases/{case['id']}/participant-drafts/resources",
        headers=headers["p2-f06"],
    )
    assert first.status_code == 200
    assert second.status_code == 200
    assert replay.status_code == 200
    assert replay.get_json()["data"]["version"] == second.get_json()["data"]["version"]
    assert conflict.status_code == 409
    assert denied.status_code == 403


def test_withdrawn_case_blocks_further_draft_sync(tmp_path, monkeypatch):
    app = _app(tmp_path, monkeypatch)
    headers = _seed(app)
    client = app.test_client()
    case = _case(client, headers["p1-f06"])
    withdrawn = client.post(
        f"/api/therapeutic-assessment/cases/{case['id']}/withdraw",
        headers={**headers["p1-f06"], "Idempotency-Key": "f06-withdraw"},
        json={"note": "主动撤回", "expected_version": case["version"]},
    )
    blocked = _save(client, headers["p1-f06"], case["id"], "summary", 0, "f06-after-withdraw")
    assert withdrawn.status_code == 200
    assert blocked.status_code == 409


def test_eight_participant_pages_and_accessibility_contract():
    app_config = json.loads((MINI / "app.json").read_text(encoding="utf-8"))
    page_paths = set(app_config["pages"])
    for step in STEPS:
        prefix = f"pages/therapeutic-assessment-{step}/index"
        assert prefix in page_paths
        assert (MINI / f"{prefix}.js").exists()
        assert (MINI / f"{prefix}.json").exists()
        assert (MINI / f"{prefix}.wxml").exists()
    component = (MINI / "components/therapeutic-flow-step/index.wxml").read_text(encoding="utf-8")
    styles = (MINI / "components/therapeutic-flow-step/index.wxss").read_text(encoding="utf-8")
    factory = (MINI / "utils/therapeuticAssessmentParticipantFlow.js").read_text(encoding="utf-8")
    assert 'role="radiogroup"' in component
    assert 'aria-checked="' in component
    assert 'aria-live="polite"' in component
    assert "min-height: 88rpx" in styles
    for state in ("offline", "expired", "withdrawn"):
        assert state in factory
