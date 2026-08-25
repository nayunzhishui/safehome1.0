import importlib
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
SHA = "a" * 64


def _fresh_app(tmp_path, monkeypatch):
    sys.path.insert(0, str(BACKEND))
    for name in list(sys.modules):
        if name in {"app", "config", "database", "models"} or name.startswith("routes.") or name.startswith("services."):
            sys.modules.pop(name, None)
    monkeypatch.setenv("APP_ENV", "testing")
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "task36-f13.sqlite3"))
    monkeypatch.setenv("CONTENT_DIR", str(ROOT / "content"))
    monkeypatch.setenv("RESEARCH_ANALYSIS_JOB_EXECUTION_ENABLED", "1")
    monkeypatch.setenv("AI_QA_ENABLED", "0")
    monkeypatch.setenv("AI_QA_PROVIDER", "fake")
    return importlib.import_module("app").app


def _seed(app):
    with app.app_context():
        from database import get_connection, now_iso
        from routes.auth_utils import generate_auth_token

        now = now_iso()
        actors = {"parent-f13": "parent", "researcher-f13": "researcher", "admin-f13": "admin"}
        with get_connection() as conn:
            for actor_id, role in actors.items():
                conn.execute(
                    "INSERT INTO users (id, nickname, role, status, created_at, updated_at) VALUES (?, ?, ?, 'active', ?, ?)",
                    (actor_id, actor_id, role, now, now),
                )
            conn.execute(
                """INSERT INTO relationship_pilot_enrollments
                   (id, user_id, assessment_result_id, worksheet_id, dimensions_json, radar_features_json,
                    profile_json, consent_scope, status, review_status, assigned_researcher_id, created_at, updated_at)
                   VALUES ('enrollment-f13', 'parent-f13', 'result-f13', 'regulatory_focus_relationship_18',
                           '[]', '[]', '{}', 'relationship_pilot_stage2_v1', 'enrolled', 'pending_review',
                           'researcher-f13', ?, ?)""",
                (now, now),
            )
            conn.execute(
                """INSERT INTO consent_records
                   (id, user_id, consent_type, consent_version, agreed, agreed_at, created_at)
                   VALUES ('consent-f13', 'parent-f13', 'research_authorization', 'research-v1', 1, ?, ?)""",
                (now, now),
            )
            conn.execute(
                """
                INSERT INTO research_scope_assignments (
                    id, enrollment_id, actor_id, assignment_role, status, version,
                    idempotency_key, assigned_by, expires_at, created_at, updated_at
                ) VALUES ('assignment-f13', 'enrollment-f13', 'researcher-f13',
                          'researcher', 'active', 1, 'seed-assignment-f13',
                          'admin-f13', '2099-01-01T00:00:00+00:00', ?, ?)
                """,
                (now, now),
            )
            conn.commit()
        return {
            actor_id: {"Authorization": f"Bearer {generate_auth_token({'id': actor_id, 'role': role})}"}
            for actor_id, role in actors.items()
        }


def _snapshot(client, headers):
    return client.post(
        "/api/research/analysis/snapshots",
        headers=headers["researcher-f13"],
        json={
            "participant_user_id": "parent-f13",
            "enrollment_id": "enrollment-f13",
            "purpose_code": "affect_research",
            "source_refs": [
                {
                    "source_type": "emotion_diary",
                    "source_id": "diary-f13",
                    "source_version": "v1",
                    "source_hash": SHA,
                }
            ],
        },
    )


def _job(client, headers, snapshot_id, key="analysis-f13"):
    return client.post(
        "/api/research/analysis/jobs",
        headers={**headers["researcher-f13"], "Idempotency-Key": key},
        json={
            "snapshot_id": snapshot_id,
            "analysis_type": "affect_aggregate",
            "analysis_version": "affect-v1",
            "resource_hash": SHA,
            "parameters": {"window_days": 30, "minimum_count": 2, "include_unknown": True},
            "max_attempts": 2,
        },
    )


def test_snapshot_and_job_store_only_references_and_are_idempotent(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    headers = _seed(app)
    client = app.test_client()

    denied = client.post("/api/research/analysis/snapshots", headers=headers["parent-f13"], json={})
    created = _snapshot(client, headers)
    assert denied.status_code == 403 and created.status_code == 201
    snapshot = created.get_json()["data"]
    assert snapshot["raw_text_included"] is False and "participant_user_id" not in snapshot

    first = _job(client, headers, snapshot["id"])
    replay = _job(client, headers, snapshot["id"])
    assert first.status_code == 201 and replay.status_code == 200
    assert first.get_json()["data"]["id"] == replay.get_json()["data"]["id"]
    assert first.get_json()["data"]["shadow_mode"] is True

    rejected = client.post(
        "/api/research/analysis/jobs",
        headers={**headers["researcher-f13"], "Idempotency-Key": "unsafe-f13"},
        json={
            "snapshot_id": snapshot["id"],
            "analysis_type": "affect_aggregate",
            "analysis_version": "v1",
            "resource_hash": SHA,
            "parameters": {"raw_text": "不应进入队列"},
        },
    )
    assert rejected.status_code == 400
    assert rejected.get_json()["error"]["code"] in {"validation_error", "sensitive_payload_rejected"}

    with app.app_context():
        from database import get_connection

        with get_connection() as conn:
            stored = conn.execute("SELECT parameters_json FROM research_analysis_jobs").fetchone()["parameters_json"]
            assert "不应进入队列" not in stored


def test_lease_backoff_dead_letter_recovery_and_unproved_completion_rejected(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    headers = _seed(app)
    client = app.test_client()
    snapshot_id = _snapshot(client, headers).get_json()["data"]["id"]
    job_id = _job(client, headers, snapshot_id).get_json()["data"]["id"]

    claimed = client.post(f"/api/research/analysis/jobs/{job_id}/claim", headers=headers["admin-f13"], json={"lease_seconds": 60})
    assert claimed.status_code == 200 and claimed.get_json()["data"]["status"] == "running"
    failed = client.post(f"/api/research/analysis/jobs/{job_id}/fail", headers=headers["admin-f13"], json={"error_code": "worker_timeout"})
    assert failed.get_json()["data"]["status"] == "failed"
    client.post(f"/api/research/analysis/jobs/{job_id}/claim", headers=headers["admin-f13"], json={"force_due": True})
    dead = client.post(f"/api/research/analysis/jobs/{job_id}/fail", headers=headers["admin-f13"], json={"error_code": "worker_timeout"})
    assert dead.get_json()["data"]["dead_lettered_at"]
    recovered = client.post(
        f"/api/research/analysis/jobs/{job_id}/recover",
        headers=headers["admin-f13"],
        json={"reason_code": "dependency_recovered"},
    )
    assert recovered.get_json()["data"]["status"] == "queued"
    client.post(f"/api/research/analysis/jobs/{job_id}/claim", headers=headers["admin-f13"], json={})
    complete = client.post(
        f"/api/research/analysis/jobs/{job_id}/complete",
        headers=headers["admin-f13"],
        json={"metrics": {"coverage_rate": 0.8, "unknown_rate": 0.2, "sample_size": 10, "quality_status": "limited", "result": {"positive": 4}}},
    )
    assert complete.status_code == 409
    assert complete.get_json()["error"]["code"] == "server_execution_proof_required"
    with app.app_context():
        from database import get_connection

        with get_connection() as conn:
            assert conn.execute(
                "SELECT COUNT(*) AS count FROM research_analysis_artifacts WHERE job_id = ?",
                (job_id,),
            ).fetchone()["count"] == 0


def test_consent_withdrawal_freezes_job_and_artifact_and_preserves_audit(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    headers = _seed(app)
    client = app.test_client()
    snapshot_id = _snapshot(client, headers).get_json()["data"]["id"]
    job_id = _job(client, headers, snapshot_id, "withdraw-f13").get_json()["data"]["id"]
    with app.app_context():
        from database import get_connection, now_iso

        now = now_iso()
        with get_connection() as conn:
            conn.execute(
                """INSERT INTO consent_records
                   (id, user_id, consent_type, consent_version, agreed, agreed_at, revoked_at, created_at)
                   VALUES ('consent-revoked-f13', 'parent-f13', 'research_authorization', 'research-v1', 0, ?, ?, ?)""",
                (now, now, now),
            )
            conn.commit()
    detail = client.get(f"/api/research/analysis/jobs/{job_id}", headers=headers["researcher-f13"])
    assert detail.status_code == 200 and detail.get_json()["data"]["status"] == "suspended"
    with app.app_context():
        from database import get_connection

        with get_connection() as conn:
            snapshot = conn.execute("SELECT authorization_status FROM research_analysis_snapshots WHERE id = ?", (snapshot_id,)).fetchone()
            events = conn.execute("SELECT COUNT(*) AS count FROM audit_logs WHERE target_id IN (?, ?)", (snapshot_id, job_id)).fetchone()
            assert snapshot["authorization_status"] == "suspended"
            assert events["count"] >= 2


def test_cancel_and_forbidden_result_payload(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    headers = _seed(app)
    client = app.test_client()
    snapshot_id = _snapshot(client, headers).get_json()["data"]["id"]
    job_id = _job(client, headers, snapshot_id, "cancel-f13").get_json()["data"]["id"]
    canceled = client.post(f"/api/research/analysis/jobs/{job_id}/cancel", headers=headers["researcher-f13"])
    assert canceled.status_code == 200 and canceled.get_json()["data"]["status"] == "canceled"

    other_id = _job(client, headers, snapshot_id, "unsafe-result-f13").get_json()["data"]["id"]
    client.post(f"/api/research/analysis/jobs/{other_id}/claim", headers=headers["admin-f13"], json={})
    rejected = client.post(
        f"/api/research/analysis/jobs/{other_id}/complete",
        headers=headers["admin-f13"],
        json={"metrics": {"coverage_rate": 1, "unknown_rate": 0, "sample_size": 1, "quality_status": "sufficient", "diagnosis": "禁止"}},
    )
    assert rejected.status_code == 400 and rejected.get_json()["error"]["code"] == "validation_error"
