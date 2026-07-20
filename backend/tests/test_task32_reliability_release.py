import importlib
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"


def _fresh_app(tmp_path, monkeypatch, *, drills=True):
    sys.path.insert(0, str(BACKEND))
    for name in list(sys.modules):
        if name in {"app", "config", "database", "models"} or name.startswith("routes.") or name.startswith("services."):
            sys.modules.pop(name, None)
    monkeypatch.setenv("APP_ENV", "testing")
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "task32.sqlite3"))
    monkeypatch.setenv("CONTENT_DIR", str(ROOT / "content"))
    monkeypatch.setenv("RELIABILITY_WORKBENCH_ENABLED", "1")
    monkeypatch.setenv("RELIABILITY_JOB_EXECUTION_ENABLED", "1")
    monkeypatch.setenv("RELIABILITY_FAULT_INJECTION_ENABLED", "1" if drills else "0")
    monkeypatch.setenv("AI_QA_ENABLED", "0")
    monkeypatch.setenv("AI_QA_PROVIDER", "fake")
    return importlib.import_module("app").app


def _actors(app):
    specs = [("participant-t32", "parent"), ("researcher-t32", "researcher"), ("supervisor-t32", "supervisor"), ("admin-t32", "admin")]
    with app.app_context():
        database = importlib.import_module("database")
        auth = importlib.import_module("routes.auth_utils")
        with database.get_connection() as conn:
            now = database.now_iso()
            for actor_id, role in specs:
                conn.execute(
                    "INSERT INTO users (id, nickname, role, source, status, created_at, updated_at) VALUES (?, ?, ?, 'test', 'active', ?, ?)",
                    (actor_id, actor_id, role, now, now),
                )
            conn.commit()
        return {actor_id: {"Authorization": f"Bearer {auth.generate_auth_token({'id': actor_id, 'role': role})}"} for actor_id, role in specs}


def test_public_status_is_minimal_and_workbench_is_internal(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    headers = _actors(app)
    client = app.test_client()
    public = client.get("/api/reliability/public-status")
    denied = client.get("/api/reliability/workbench", headers=headers["participant-t32"])
    internal = client.get("/api/reliability/workbench", headers=headers["researcher-t32"])
    assert public.status_code == 200 and denied.status_code == 403 and internal.status_code == 200
    assert public.get_json()["data"]["production_slo_frozen"] is False
    assert "recent_events" not in public.get_json()["data"]


def test_request_trace_records_allowlisted_fields_and_correlates_request_id(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    headers = _actors(app)
    response = app.test_client().get("/api/reliability/public-status", headers={"X-Request-ID": "task32-trace-001"})
    assert response.headers["X-Request-ID"] == "task32-trace-001"
    workbench = app.test_client().get("/api/reliability/workbench", headers=headers["admin-t32"]).get_json()["data"]
    event = next(item for item in workbench["recent_events"] if item["request_id"] == "task32-trace-001")
    assert set(event) >= {"request_id", "actor_scope", "module", "journey", "outcome", "error_code", "latency_ms", "retry_count", "recovered"}
    assert "body" not in event and "token" not in str(event).lower()


def test_slo_snapshot_uses_local_synthetic_events_without_freezing_thresholds(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    headers = _actors(app)
    client = app.test_client()
    for index in range(4):
        client.get("/api/reliability/public-status", headers={"X-Request-ID": f"task32-slo-{index:03d}"})
    result = client.post("/api/reliability/slo-snapshots", headers=headers["researcher-t32"], json={"environment": "local_synthetic", "window_minutes": 60})
    assert result.status_code == 200
    data = result.get_json()["data"]
    assert data["contains_real_participant_text"] is False
    assert data["production_slo_frozen"] is False
    assert data["status"] == "local_evidence_only"


def test_reliable_job_has_idempotency_lease_backoff_dead_letter_and_recovery(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    headers = _actors(app)
    client = app.test_client()
    payload = {"job_type": "notification_delivery", "source_type": "notification_delivery", "source_id": "synthetic-delivery", "idempotency_key": "job-t32-001", "max_attempts": 2}
    first = client.post("/api/reliability/jobs", headers=headers["admin-t32"], json=payload)
    repeated = client.post("/api/reliability/jobs", headers=headers["admin-t32"], json=payload)
    assert first.status_code == 201 and repeated.status_code == 200
    job_id = first.get_json()["data"]["id"]
    assert repeated.get_json()["data"]["id"] == job_id
    claimed = client.post(f"/api/reliability/jobs/{job_id}/claim", headers=headers["admin-t32"], json={"lease_seconds": 60})
    assert claimed.get_json()["data"]["status"] == "leased"
    failed_once = client.post(f"/api/reliability/jobs/{job_id}/fail", headers=headers["admin-t32"], json={"error_code": "provider_timeout"})
    assert failed_once.get_json()["data"]["status"] == "retrying"
    client.post(f"/api/reliability/jobs/{job_id}/claim", headers=headers["admin-t32"], json={"force_due": True})
    failed_twice = client.post(f"/api/reliability/jobs/{job_id}/fail", headers=headers["admin-t32"], json={"error_code": "provider_timeout"})
    assert failed_twice.get_json()["data"]["status"] == "dead_letter"
    recovered = client.post(f"/api/reliability/jobs/{job_id}/recover", headers=headers["admin-t32"], json={"reason_code": "manual_dependency_recovered"})
    assert recovered.get_json()["data"]["status"] == "pending"


def test_reliable_jobs_are_admin_written_and_do_not_store_payload_text(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    headers = _actors(app)
    client = app.test_client()
    denied = client.post("/api/reliability/jobs", headers=headers["researcher-t32"], json={"job_type": "ai_evaluation", "source_type": "ai_run", "source_id": "synthetic", "idempotency_key": "denied"})
    created = client.post("/api/reliability/jobs", headers=headers["admin-t32"], json={"job_type": "ai_evaluation", "source_type": "ai_run", "source_id": "synthetic", "idempotency_key": "safe", "payload": "参与者原文不应被接受"})
    assert denied.status_code == 403 and created.status_code == 400


def test_feature_flag_change_is_versioned_audited_and_atomically_rolled_back(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    headers = _actors(app)
    client = app.test_client()
    denied = client.patch("/api/reliability/feature-flags/participant_journey", headers=headers["supervisor-t32"], json={"enabled": False, "reason_code": "drill"})
    changed = client.patch("/api/reliability/feature-flags/participant_journey", headers=headers["admin-t32"], json={"enabled": False, "role_scope": ["parent"], "rollout_percent": 25, "reason_code": "controlled_rollout"})
    assert denied.status_code == 403 and changed.status_code == 200
    version = changed.get_json()["data"]["version"]
    assert changed.get_json()["data"]["enabled"] is False
    rolled = client.post("/api/reliability/feature-flags/participant_journey/rollback", headers=headers["admin-t32"], json={"target_version": version - 1, "reason_code": "rollback_test"})
    assert rolled.status_code == 200 and rolled.get_json()["data"]["enabled"] is True


def test_fault_drills_are_fixed_synthetic_and_disabled_without_gate(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    headers = _actors(app)
    client = app.test_client()
    scenarios = ["content_missing", "database_timeout", "provider_failure", "token_invalidated", "duplicate_message", "artifact_corrupted"]
    for scenario in scenarios:
        result = client.post("/api/reliability/drills", headers=headers["admin-t32"], json={"scenario": scenario})
        assert result.status_code == 200
        assert result.get_json()["data"]["contains_real_participant_data"] is False
        assert result.get_json()["data"]["production_approval_inferred"] is False
    disabled_app = _fresh_app(tmp_path / "disabled", monkeypatch, drills=False)
    disabled_headers = _actors(disabled_app)
    blocked = disabled_app.test_client().post("/api/reliability/drills", headers=disabled_headers["admin-t32"], json={"scenario": "content_missing"})
    assert blocked.status_code == 503


def test_evidence_package_has_external_gates_and_no_approval_action(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    headers = _actors(app)
    client = app.test_client()
    denied = client.post("/api/reliability/evidence-packages", headers=headers["researcher-t32"])
    package = client.post("/api/reliability/evidence-packages", headers=headers["supervisor-t32"])
    assert denied.status_code == 403 and package.status_code == 200
    data = package.get_json()["data"]
    assert data["status"] == "draft_for_human_release_review"
    assert data["production_release_approved"] is False
    assert data["external_gates"]
