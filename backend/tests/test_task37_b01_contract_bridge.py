import importlib
import json
import shutil
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
CONTENT = ROOT / "content"


def _app(tmp_path, monkeypatch):
    sys.path.insert(0, str(BACKEND))
    for name in list(sys.modules):
        if name in {"app", "config", "database", "models"} or name.startswith(
            ("routes.", "services.")
        ):
            sys.modules.pop(name, None)
    content_dir = tmp_path / "content"
    shutil.copytree(CONTENT, content_dir)
    monkeypatch.setenv("APP_ENV", "testing")
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "b01.sqlite3"))
    monkeypatch.setenv("CONTENT_DIR", str(content_dir))
    return importlib.import_module("app").app, content_dir


def _headers(app):
    specs = [("admin-b01", "admin"), ("parent-b01", "parent")]
    with app.app_context():
        database = importlib.import_module("database")
        auth_utils = importlib.import_module("routes.auth_utils")
        with database.get_connection() as conn:
            now = database.now_iso()
            for actor_id, role in specs:
                conn.execute(
                    "INSERT INTO users (id, nickname, role, source, status, created_at, updated_at) "
                    "VALUES (?, ?, ?, 'test', 'active', ?, ?)",
                    (actor_id, actor_id, role, now, now),
                )
            conn.commit()
        return {
            actor_id: {
                "Authorization": "Bearer "
                + auth_utils.generate_auth_token({"id": actor_id, "role": role})
            }
            for actor_id, role in specs
        }


def test_contract_exposes_one_versioned_machine_contract(tmp_path, monkeypatch):
    app, _ = _app(tmp_path, monkeypatch)
    headers = _headers(app)
    response = app.test_client().get(
        "/api/therapeutic-assessment/production-contract",
        headers=headers["parent-b01"],
    )
    assert response.status_code == 200
    data = response.get_json()["data"]
    assert data["service_levels"] == ["L0", "L1", "L2", "L3"]
    assert data["competency_levels"] == ["T1", "T2", "T3"]
    assert data["evidence_kinds"] == ["O", "P", "H", "U"]
    assert len(data["five_gates"]) == 5
    assert data["production_release_approved"] is False


def test_unknown_or_missing_dimension_denies_without_cross_substitution(
    tmp_path, monkeypatch
):
    app, _ = _app(tmp_path, monkeypatch)
    headers = _headers(app)
    client = app.test_client()
    valid = client.post(
        "/api/therapeutic-assessment/production-contract/check",
        headers=headers["parent-b01"],
        json={
            "service_level": "L1",
            "competency_level": "T2",
            "evidence_kind": "O",
            "object_permission": True,
            "safety_state": "low_risk",
            "responsible_role": "researcher",
        },
    ).get_json()["data"]
    assert valid["allowed"] is True
    denied = client.post(
        "/api/therapeutic-assessment/production-contract/check",
        headers=headers["parent-b01"],
        json={
            "service_level": "L1",
            "competency_level": "T2",
            "evidence_kind": "O",
            "object_permission": False,
            "safety_state": "low_risk",
            "responsible_role": "researcher",
        },
    ).get_json()["data"]
    assert denied["allowed"] is False
    assert denied["checks"]["competency_level"] is True
    assert denied["checks"]["object_permission"] is False
    assert denied["temporary_showcase_bypass_accepted"] is False


def test_source_contract_drift_fails_closed(tmp_path, monkeypatch):
    app, content_dir = _app(tmp_path, monkeypatch)
    headers = _headers(app)
    path = content_dir / "therapeutic_assessment_service_levels.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["version"] = "unexpected-drift"
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    response = app.test_client().get(
        "/api/therapeutic-assessment/production-contract",
        headers=headers["parent-b01"],
    )
    assert response.status_code == 409
    assert response.get_json()["error"]["code"] == "contract_drift"


def test_snapshot_is_admin_only_idempotent_and_not_release_approval(
    tmp_path, monkeypatch
):
    app, _ = _app(tmp_path, monkeypatch)
    headers = _headers(app)
    client = app.test_client()
    assert client.post(
        "/api/therapeutic-assessment/production-contract/snapshots",
        headers=headers["parent-b01"],
    ).status_code == 403
    first = client.post(
        "/api/therapeutic-assessment/production-contract/snapshots",
        headers=headers["admin-b01"],
    ).get_json()["data"]
    second = client.post(
        "/api/therapeutic-assessment/production-contract/snapshots",
        headers=headers["admin-b01"],
    ).get_json()["data"]
    assert first["id"] == second["id"]
    assert first["production_release_approved"] is False
