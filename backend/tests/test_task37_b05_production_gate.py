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
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "b05.sqlite3"))
    monkeypatch.setenv("CONTENT_DIR", str(ROOT / "content"))
    return importlib.import_module("app").app


def _seed(app):
    users = {
        "p-b05": "parent",
        "r-b05": "researcher",
        "s-b05": "supervisor",
        "a-b05": "admin",
    }
    with app.app_context():
        from database import get_connection, now_iso
        from routes.auth_utils import generate_auth_token

        now = now_iso()
        with get_connection() as conn:
            for user_id, role in users.items():
                conn.execute(
                    "INSERT INTO users (id, nickname, role, status, created_at, updated_at) VALUES (?, ?, ?, 'active', ?, ?)",
                    (user_id, user_id, role, now, now),
                )
            conn.commit()
        return {
            user_id: {
                "Authorization": f"Bearer {generate_auth_token({'id': user_id, 'role': role})}"
            }
            for user_id, role in users.items()
        }


def test_schema_049_adds_release_evidence_and_gate_snapshots(tmp_path, monkeypatch):
    app = _app(tmp_path, monkeypatch)
    with app.app_context():
        from database import CURRENT_SCHEMA_NAME, CURRENT_SCHEMA_VERSION, get_connection

        with get_connection() as conn:
            tables = {
                row["name"]
                for row in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table'"
                ).fetchall()
            }
            columns = {
                row["name"]
                for row in conn.execute(
                    "PRAGMA table_info(therapeutic_assessment_release_evidence)"
                ).fetchall()
            }
    assert CURRENT_SCHEMA_VERSION == "2026_07_28_049"
    assert CURRENT_SCHEMA_NAME == "therapeutic_assessment_production_gate"
    assert {
        "therapeutic_assessment_release_evidence",
        "therapeutic_assessment_release_gate_runs",
        "therapeutic_assessment_release_gate_checks",
    }.issubset(tables)
    assert {
        "artifact_sha256",
        "environment",
        "verified_by",
        "verification_idempotency_key",
        "version",
    }.issubset(columns)


def test_gate_is_blocked_until_engineering_and_real_human_evidence_exist(
    tmp_path, monkeypatch
):
    app = _app(tmp_path, monkeypatch)
    headers = _seed(app)
    client = app.test_client()

    denied = client.get(
        "/api/therapeutic-assessment/production-gate",
        headers=headers["p-b05"],
    )
    status = client.get(
        "/api/therapeutic-assessment/production-gate",
        headers=headers["s-b05"],
    )
    data = status.get_json()["data"]
    assert denied.status_code == 403
    assert status.status_code == 200
    assert data["status"] == "blocked"
    assert data["production_release_approved"] is False
    assert data["temporary_showcase_counts_as_permission"] is False
    assert data["simulated_signoffs_counted"] is False
    assert "T38-F13" in data["checks"]["engineering_content"]["missing"]
    assert "human_a0_expert_review" in data["checks"]["human_evidence"]["missing"]
    assert "infra_device" in data["checks"]["infrastructure_release"]["missing"]


def test_evidence_requires_hash_independent_verification_and_production_environment(
    tmp_path, monkeypatch
):
    app = _app(tmp_path, monkeypatch)
    headers = _seed(app)
    client = app.test_client()

    invalid = client.post(
        "/api/therapeutic-assessment/production-gate/evidence",
        headers={**headers["s-b05"], "Idempotency-Key": "b05-invalid"},
        json={
            "evidence_type": "human_a0_expert_review",
            "artifact_ref": "local:a0",
            "artifact_sha256": "bad",
        },
    )
    created = client.post(
        "/api/therapeutic-assessment/production-gate/evidence",
        headers={**headers["s-b05"], "Idempotency-Key": "b05-evidence"},
        json={
            "evidence_type": "human_a0_expert_review",
            "artifact_ref": "local:a0-expert-review",
            "artifact_sha256": "a" * 64,
            "status": "verified",
        },
    )
    replay = client.post(
        "/api/therapeutic-assessment/production-gate/evidence",
        headers={**headers["s-b05"], "Idempotency-Key": "b05-evidence"},
        json={
            "evidence_type": "human_a0_expert_review",
            "artifact_ref": "local:a0-expert-review",
            "artifact_sha256": "a" * 64,
        },
    )
    item = created.get_json()["data"]
    self_review = client.post(
        f"/api/therapeutic-assessment/production-gate/evidence/{item['id']}/verify",
        headers={**headers["s-b05"], "Idempotency-Key": "b05-self-review"},
        json={"decision": "verified", "expected_version": 1},
    )
    verified = client.post(
        f"/api/therapeutic-assessment/production-gate/evidence/{item['id']}/verify",
        headers={**headers["a-b05"], "Idempotency-Key": "b05-review"},
        json={"decision": "verified", "expected_version": 1},
    )
    verify_replay = client.post(
        f"/api/therapeutic-assessment/production-gate/evidence/{item['id']}/verify",
        headers={**headers["a-b05"], "Idempotency-Key": "b05-review"},
        json={"decision": "verified", "expected_version": 1},
    )

    assert invalid.status_code == 422
    assert created.status_code == 201
    assert created.get_json()["data"]["status"] == "pending"
    assert replay.status_code == 200
    assert self_review.status_code == 403
    assert verified.status_code == 200
    assert verify_replay.status_code == 200
    assert verified.get_json()["data"]["environment"] == "testing"
    assert verified.get_json()["data"]["qualifies_for_production"] is False

    status = client.get(
        "/api/therapeutic-assessment/production-gate",
        headers=headers["s-b05"],
    ).get_json()["data"]
    assert "human_a0_expert_review" in status["checks"]["human_evidence"]["missing"]


def test_gate_evaluation_is_versioned_idempotent_and_never_releases(tmp_path, monkeypatch):
    app = _app(tmp_path, monkeypatch)
    headers = _seed(app)
    client = app.test_client()

    first = client.post(
        "/api/therapeutic-assessment/production-gate/evaluate",
        headers={**headers["s-b05"], "Idempotency-Key": "b05-evaluate"},
    )
    replay = client.post(
        "/api/therapeutic-assessment/production-gate/evaluate",
        headers={**headers["s-b05"], "Idempotency-Key": "b05-evaluate"},
    )
    data = first.get_json()["data"]
    assert first.status_code == 201
    assert replay.status_code == 200
    assert data["status"] == "blocked"
    assert data["production_release_approved"] is False
    assert replay.get_json()["data"]["run"]["id"] == data["run"]["id"]
    with app.app_context():
        from database import get_connection

        with get_connection() as conn:
            run = conn.execute(
                "SELECT * FROM therapeutic_assessment_release_gate_runs WHERE id = ?",
                (data["run"]["id"],),
            ).fetchone()
            checks = conn.execute(
                "SELECT COUNT(*) AS count FROM therapeutic_assessment_release_gate_checks WHERE run_id = ?",
                (data["run"]["id"],),
            ).fetchone()
    assert run["production_release_approved"] == 0
    assert checks["count"] == 5


def test_policy_forbids_automated_or_simulated_signoff(tmp_path, monkeypatch):
    _app(tmp_path, monkeypatch)
    policy = __import__("json").loads(
        (ROOT / "content" / "therapeutic_assessment_release_gate_policy.json").read_text(
            encoding="utf-8"
        )
    )
    assert policy["evidence_rules"]["simulation_counts_as_approval"] is False
    assert policy["evidence_rules"]["automated_test_counts_as_human_evidence"] is False
    assert policy["production_release_approved"] is False
    assert policy["temporary_showcase_counts_as_permission"] is False
