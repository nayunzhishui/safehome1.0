import hashlib
import importlib
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"


def _fresh_app(tmp_path, monkeypatch):
    sys.path.insert(0, str(BACKEND))
    for name in list(sys.modules):
        if name in {"app", "config", "database", "models"} or name.startswith("routes.") or name.startswith("services."):
            sys.modules.pop(name, None)
    monkeypatch.setenv("APP_ENV", "testing")
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "task36-f14.sqlite3"))
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
        actors = {"parent-f14": "parent", "researcher-f14": "researcher", "admin-f14": "admin"}
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
                   VALUES ('enrollment-f14', 'parent-f14', 'result-f14', 'regulatory_focus_relationship_18',
                           '[]', '[]', '{}', 'relationship_pilot_stage2_v1', 'enrolled', 'pending_review',
                           'researcher-f14', ?, ?)""",
                (now, now),
            )
            conn.execute(
                """INSERT INTO consent_records
                   (id, user_id, consent_type, consent_version, agreed, agreed_at, created_at)
                   VALUES ('consent-f14', 'parent-f14', 'research_authorization', 'research-v1', 1, ?, ?)""",
                (now, now),
            )
            conn.execute(
                """INSERT INTO research_scope_assignments
                   (id, enrollment_id, actor_id, assignment_role, status, version,
                    idempotency_key, assigned_by, expires_at, created_at, updated_at)
                   VALUES ('assignment-f14', 'enrollment-f14', 'researcher-f14',
                           'researcher', 'active', 1, 'seed-assignment-f14',
                           'admin-f14', '2099-01-01T00:00:00+00:00', ?, ?)""",
                (now, now),
            )
            conn.commit()
        return {
            actor_id: {"Authorization": f"Bearer {generate_auth_token({'id': actor_id, 'role': role})}"}
            for actor_id, role in actors.items()
        }


def _catalog(client, headers):
    response = client.get("/api/research/analysis/catalog", headers=headers["researcher-f14"])
    assert response.status_code == 200
    return response.get_json()["data"]


def _snapshot(client, headers, source_type="synthetic_fixture"):
    fixture_hash = hashlib.sha256((ROOT / "content" / "synthetic_affect_benchmark_240.json").read_bytes()).hexdigest()
    response = client.post(
        "/api/research/analysis/snapshots",
        headers=headers["researcher-f14"],
        json={
            "participant_user_id": "parent-f14",
            "enrollment_id": "enrollment-f14",
            "purpose_code": "affect_research",
            "source_refs": [{
                "source_type": source_type,
                "source_id": "safehome_synthetic_affect_240_v1" if source_type == "synthetic_fixture" else "diary-f14",
                "source_version": "v1",
                "source_hash": fixture_hash,
            }],
        },
    )
    assert response.status_code == 201
    return response.get_json()["data"]["id"]


def _job(client, headers, snapshot_id, pipeline, *, sample_size=240, key="f14-job"):
    response = client.post(
        "/api/research/analysis/jobs",
        headers={**headers["researcher-f14"], "Idempotency-Key": key},
        json={
            "snapshot_id": snapshot_id,
            "analysis_type": pipeline["analysis_type"],
            "analysis_version": pipeline["analysis_version"],
            "resource_hash": pipeline["resource_hash"],
            "parameters": {"minimum_count": 5, "synthetic_sample_size": sample_size},
        },
    )
    assert response.status_code == 201
    return response.get_json()["data"]["id"]


def test_catalog_and_three_synthetic_pipelines_are_versioned_and_non_diagnostic(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    headers = _seed(app)
    client = app.test_client()
    catalog = _catalog(client, headers)
    assert catalog["real_participant_processing_enabled"] is False
    assert catalog["external_datasets_downloaded"] is False
    assert len(catalog["pipelines"]) == 3
    snapshot_id = _snapshot(client, headers)

    for index, pipeline in enumerate(catalog["pipelines"]):
        job_id = _job(client, headers, snapshot_id, pipeline, key=f"f14-{index}")
        executed = client.post(
            f"/api/research/analysis/jobs/{job_id}/execute-synthetic",
            headers=headers["admin-f14"],
        )
        assert executed.status_code == 200
        detail = client.get(
            f"/api/research/analysis/jobs/{job_id}",
            headers=headers["researcher-f14"],
        ).get_json()["data"]
        metrics = detail["artifact"]["metrics"]
        assert detail["status"] == "succeeded"
        assert metrics["sample_size"] == 240
        assert metrics["result"]["data_mode"] == "project_owned_synthetic_only"
        assert "诊断" in detail["artifact"]["boundary_notice"]
        assert detail["raw_text_included"] is False
        assert "我特别害怕" not in str(detail)


def test_small_sample_is_suppressed_and_job_list_contains_quality(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    headers = _seed(app)
    client = app.test_client()
    pipeline = _catalog(client, headers)["pipelines"][1]
    snapshot_id = _snapshot(client, headers)
    job_id = _job(client, headers, snapshot_id, pipeline, sample_size=3, key="f14-small")
    executed = client.post(
        f"/api/research/analysis/jobs/{job_id}/execute-synthetic",
        headers=headers["admin-f14"],
    )
    assert executed.status_code == 200
    listing = client.get("/api/research/analysis/jobs", headers=headers["researcher-f14"]).get_json()["data"]
    item = next(item for item in listing["items"] if item["id"] == job_id)
    assert item["artifact"]["metrics"]["quality_status"] == "insufficient"
    assert item["artifact"]["metrics"]["result"]["suppressed"] is True
    assert item["artifact"]["metrics"]["result"]["nodes"] == []
    assert "small_sample_suppressed" in item["artifact"]["metrics"]["warnings"]


def test_real_source_and_version_drift_are_blocked_before_execution(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    headers = _seed(app)
    client = app.test_client()
    pipeline = _catalog(client, headers)["pipelines"][0]
    real_snapshot = _snapshot(client, headers, "emotion_diary")
    blocked_job = _job(client, headers, real_snapshot, pipeline, key="f14-real")
    blocked = client.post(
        f"/api/research/analysis/jobs/{blocked_job}/execute-synthetic",
        headers=headers["admin-f14"],
    )
    assert blocked.status_code == 409
    assert blocked.get_json()["error"]["code"] == "real_participant_analysis_blocked"

    synthetic_snapshot = _snapshot(client, headers)
    drift = dict(pipeline)
    drift["analysis_version"] = "stale-version"
    drift_job = _job(client, headers, synthetic_snapshot, drift, key="f14-drift")
    rejected = client.post(
        f"/api/research/analysis/jobs/{drift_job}/execute-synthetic",
        headers=headers["admin-f14"],
    )
    assert rejected.status_code == 409
    assert rejected.get_json()["error"]["code"] == "analysis_version_mismatch"
