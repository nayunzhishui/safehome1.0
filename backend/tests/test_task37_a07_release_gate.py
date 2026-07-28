import hashlib
import importlib
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
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "a07.sqlite3"))
    monkeypatch.setenv("CONTENT_DIR", str(content_dir))
    monkeypatch.setenv("OFFLINE_BENCHMARK_ENABLED", "1")
    return importlib.import_module("app").app


def _headers(app):
    specs = [
        ("admin-a", "admin"),
        ("supervisor-a", "supervisor"),
        ("researcher-a", "researcher"),
        ("participant-a", "participant"),
    ]
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


def test_release_gate_builds_blocked_evidence_package_without_activation(
    tmp_path, monkeypatch
):
    app = _app(tmp_path, monkeypatch)
    headers = _headers(app)
    client = app.test_client()
    response = client.post(
        "/api/research/benchmarks/release-gate/packages",
        headers=headers["supervisor-a"],
    )
    assert response.status_code == 200
    gate = response.get_json()["data"]
    assert gate["status"] == "blocked_external_gates"
    assert gate["runtime_activation_allowed"] is False
    assert gate["production_release_approved"] is False
    assert gate["temporary_showcase_privilege_counts_as_approval"] is False
    assert gate["simulated_agent_counts_as_human_signoff"] is False
    assert "test_cloud_shadow" in gate["blockers"]
    assert "accountable_owner_approval" in gate["blockers"]
    machine = {item["gate_id"]: item for item in gate["checks"]}
    assert machine["abstention_review_and_rollback"]["passed"] is True
    assert machine["non_diagnostic_output_boundary"]["passed"] is True


def test_simulated_or_incomplete_signoff_is_rejected(tmp_path, monkeypatch):
    app = _app(tmp_path, monkeypatch)
    headers = _headers(app)
    client = app.test_client()
    evidence_hash = hashlib.sha256(b"test-cloud-report").hexdigest()
    simulated = client.post(
        "/api/research/benchmarks/release-gate/evidence",
        headers=headers["admin-a"],
        json={
            "gate_id": "test_cloud_shadow",
            "evidence_hash": evidence_hash,
            "evidence_type": "test_cloud_report",
            "signer_name": "模拟Agent",
            "source_environment": "synthetic",
            "simulated_agent": True,
        },
    )
    assert simulated.status_code == 400
    assert simulated.get_json()["error"]["code"] == "simulated_signoff_forbidden"
    invalid_hash = client.post(
        "/api/research/benchmarks/release-gate/evidence",
        headers=headers["admin-a"],
        json={
            "gate_id": "test_cloud_shadow",
            "evidence_hash": "not-a-hash",
            "evidence_type": "test_cloud_report",
            "signer_name": "负责人",
            "source_environment": "test-cloud",
            "simulated_agent": False,
        },
    )
    assert invalid_hash.status_code == 400
    assert invalid_hash.get_json()["error"]["code"] == "evidence_hash_invalid"


def test_real_evidence_is_audited_but_does_not_approve_production(
    tmp_path, monkeypatch
):
    app = _app(tmp_path, monkeypatch)
    headers = _headers(app)
    client = app.test_client()
    evidence_hash = hashlib.sha256(b"test-cloud-report").hexdigest()
    response = client.post(
        "/api/research/benchmarks/release-gate/evidence",
        headers=headers["admin-a"],
        json={
            "gate_id": "test_cloud_shadow",
            "evidence_hash": evidence_hash,
            "evidence_type": "test_cloud_report",
            "signer_name": "测试负责人",
            "source_environment": "test-cloud",
            "simulated_agent": False,
        },
    )
    assert response.status_code == 200
    assert response.get_json()["data"]["production_release_approved"] is False
    package = client.post(
        "/api/research/benchmarks/release-gate/packages",
        headers=headers["admin-a"],
    ).get_json()["data"]
    check = {item["gate_id"]: item for item in package["checks"]}
    assert check["test_cloud_shadow"]["passed"] is True
    assert package["production_release_approved"] is False
    with app.app_context():
        database = importlib.import_module("database")
        with database.get_connection() as conn:
            audit = conn.execute(
                "SELECT metadata_json FROM audit_logs "
                "WHERE action = 'offline_model_release_evidence_recorded'"
            ).fetchone()
        assert evidence_hash in audit["metadata_json"]


def test_release_gate_permissions_are_restricted(tmp_path, monkeypatch):
    app = _app(tmp_path, monkeypatch)
    headers = _headers(app)
    client = app.test_client()
    assert (
        client.get(
            "/api/research/benchmarks/release-gate",
            headers=headers["participant-a"],
        ).status_code
        == 403
    )
    assert (
        client.post(
            "/api/research/benchmarks/release-gate/packages",
            headers=headers["researcher-a"],
        ).status_code
        == 403
    )
