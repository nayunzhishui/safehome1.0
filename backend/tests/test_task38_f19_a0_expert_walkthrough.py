import importlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
REGISTRY = ROOT / "content" / "therapeutic_assessment_pilot_evidence_registry.json"


def _app(tmp_path, monkeypatch):
    sys.path.insert(0, str(BACKEND))
    for name in list(sys.modules):
        if name in {"app", "config", "database", "models"} or name.startswith(("routes.", "services.")):
            sys.modules.pop(name, None)
    monkeypatch.setenv("APP_ENV", "testing")
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "f19.sqlite3"))
    monkeypatch.setenv("CONTENT_DIR", str(ROOT / "content"))
    return importlib.import_module("app").app


def _headers(app, user_id, role):
    with app.app_context():
        from database import get_connection, now_iso
        from routes.auth_utils import generate_auth_token
        now = now_iso()
        with get_connection() as conn:
            conn.execute("INSERT INTO users (id,nickname,role,status,created_at,updated_at) VALUES (?,?,?,'active',?,?)", (user_id, user_id, role, now, now))
            conn.commit()
        return {"Authorization": f"Bearer {generate_auth_token({'id': user_id, 'role': role})}"}


def test_a0_has_five_roles_questions_evidence_and_human_only_signoff():
    payload = json.loads(REGISTRY.read_text(encoding="utf-8"))
    stage = payload["stages"][0]
    assert stage["id"] == "A0"
    assert len(stage["roles"]) == 5
    assert all(item["questions"] and item["evidence_refs"] for item in stage["roles"])
    assert stage["simulated_role_may_sign"] is False
    assert stage["automatic_test_may_sign"] is False
    assert "disagreements" in stage["required_human_fields"]


def test_a0_package_is_formal_role_only_and_never_prefilled_as_signed(tmp_path, monkeypatch):
    app = _app(tmp_path, monkeypatch)
    client = app.test_client()
    participant = _headers(app, "participant-f19", "parent")
    researcher = _headers(app, "researcher-f19", "researcher")
    assert client.get("/api/therapeutic-assessment/pilot-evidence/A0", headers=participant).status_code == 403
    response = client.get("/api/therapeutic-assessment/pilot-evidence/A0", headers=researcher)
    assert response.status_code == 200
    data = response.get_json()["data"]
    assert data["human_reviews"] == []
    assert data["human_signoff_complete"] is False
    assert data["simulated_signoffs_counted"] is False
    assert len(data["sha256"]) == 64
