import hashlib
import importlib
import json
import shutil
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
FIXTURE_NAME = "synthetic_affect_benchmark_240.json"
FIXTURE_ID = "safehome_synthetic_affect_240_v1"


def _fresh_app(tmp_path, monkeypatch, content_dir=None):
    sys.path.insert(0, str(BACKEND))
    for name in list(sys.modules):
        if name in {"app", "config", "database", "models"} or name.startswith("routes.") or name.startswith("services."):
            sys.modules.pop(name, None)
    monkeypatch.setenv("APP_ENV", "testing")
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "rc0810-f18.sqlite3"))
    monkeypatch.setenv("CONTENT_DIR", str(content_dir or ROOT / "content"))
    monkeypatch.setenv("RESEARCH_ANALYSIS_JOB_EXECUTION_ENABLED", "1")
    monkeypatch.setenv("SAFEHOME_BUILD_COMMIT", "rc0810-f18-test-commit")
    monkeypatch.setenv("SAFEHOME_EXECUTION_IMAGE_REF", "safehome-test@sha256:f18")
    monkeypatch.setenv("AI_QA_ENABLED", "0")
    monkeypatch.setenv("AI_QA_PROVIDER", "fake")
    return importlib.import_module("app").app


def _seed(app):
    with app.app_context():
        from database import get_connection, now_iso
        from routes.auth_utils import generate_auth_token

        now = now_iso()
        actors = {
            "parent-f18": "parent",
            "other-parent-f18": "parent",
            "researcher-f18": "researcher",
            "admin-f18": "admin",
        }
        with get_connection() as conn:
            for actor_id, role in actors.items():
                conn.execute(
                    "INSERT INTO users (id, nickname, role, status, created_at, updated_at) VALUES (?, ?, ?, 'active', ?, ?)",
                    (actor_id, actor_id, role, now, now),
                )
            for suffix, user_id in (("main", "parent-f18"), ("other", "other-parent-f18")):
                conn.execute(
                    """INSERT INTO relationship_pilot_enrollments
                       (id, user_id, assessment_result_id, worksheet_id, dimensions_json, radar_features_json,
                        profile_json, consent_scope, status, review_status, assigned_researcher_id, created_at, updated_at)
                       VALUES (?, ?, ?, 'regulatory_focus_relationship_18', '[]', '[]', '{}',
                               'relationship_pilot_stage2_v1', 'enrolled', 'pending_review', ?, ?, ?)""",
                    (
                        f"enrollment-f18-{suffix}",
                        user_id,
                        f"result-f18-{suffix}",
                        "researcher-f18" if suffix == "main" else None,
                        now,
                        now,
                    ),
                )
                conn.execute(
                    """INSERT INTO consent_records
                       (id, user_id, consent_type, consent_version, agreed, agreed_at, created_at)
                       VALUES (?, ?, 'research_authorization', 'research-v1', 1, ?, ?)""",
                    (f"consent-f18-{suffix}", user_id, now, now),
                )
            conn.execute(
                """INSERT INTO research_scope_assignments
                   (id, enrollment_id, actor_id, assignment_role, status, version, idempotency_key,
                    assigned_by, expires_at, created_at, updated_at)
                   VALUES ('assignment-f18', 'enrollment-f18-main', 'researcher-f18', 'researcher',
                           'active', 1, 'assignment-f18', 'admin-f18',
                           '2099-01-01T00:00:00+00:00', ?, ?)""",
                (now, now),
            )
            conn.commit()
        return {
            actor_id: {
                "Authorization": f"Bearer {generate_auth_token({'id': actor_id, 'role': role})}"
            }
            for actor_id, role in actors.items()
        }


def _catalog(client, headers):
    response = client.get("/api/research/analysis/catalog", headers=headers["researcher-f18"])
    assert response.status_code == 200
    return response.get_json()["data"]["pipelines"][0]


def _snapshot(
    client,
    headers,
    source_hash,
    *,
    source_type="synthetic_fixture",
    source_id=FIXTURE_ID,
    actor="researcher-f18",
    participant="parent-f18",
    enrollment="enrollment-f18-main",
):
    response = client.post(
        "/api/research/analysis/snapshots",
        headers=headers[actor],
        json={
            "participant_user_id": participant,
            "enrollment_id": enrollment,
            "purpose_code": "affect_research",
            "source_refs": [{
                "source_type": source_type,
                "source_id": source_id,
                "source_version": "v1",
                "source_hash": source_hash,
            }],
        },
    )
    return response


def _job(client, headers, snapshot_id, pipeline, key, *, version=None, resource_hash=None, seed=0):
    response = client.post(
        "/api/research/analysis/jobs",
        headers={**headers["researcher-f18"], "Idempotency-Key": key},
        json={
            "snapshot_id": snapshot_id,
            "analysis_type": pipeline["analysis_type"],
            "analysis_version": version or pipeline["analysis_version"],
            "resource_hash": resource_hash or pipeline["resource_hash"],
            "parameters": {"minimum_count": 5, "synthetic_sample_size": 20, "random_seed": seed},
        },
    )
    assert response.status_code == 201
    return response.get_json()["data"]["id"]


def _setup_job(tmp_path, monkeypatch, *, content_dir=None, key="f18-job", seed=0):
    app = _fresh_app(tmp_path, monkeypatch, content_dir)
    headers = _seed(app)
    client = app.test_client()
    pipeline = _catalog(client, headers)
    source_hash = pipeline["resource_hash"]
    snapshot = _snapshot(client, headers, source_hash)
    assert snapshot.status_code == 201
    job_id = _job(client, headers, snapshot.get_json()["data"]["id"], pipeline, key, seed=seed)
    return app, headers, client, pipeline, snapshot.get_json()["data"]["id"], job_id


def test_f18_policy_schema_and_migration_head_are_frozen(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    policy = json.loads((ROOT / "config" / "rc0810" / "research_execution_manifest_policy.json").read_text(encoding="utf-8"))
    profile = json.loads((ROOT / "config" / "rc0810" / "database_profiles.json").read_text(encoding="utf-8"))
    assert policy["active_source_types"] == ["synthetic_fixture"]
    assert policy["completion"]["public_metrics_completion_allowed"] is False
    assert policy["real_participant_processing_enabled"] is False
    assert profile["profiles"]["production"]["explicit_migration_head"] == "2026_08_25_076"
    with app.app_context():
        from database import get_connection

        with get_connection() as conn:
            tables = {row["name"] for row in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
            manifest_columns = {row["name"] for row in conn.execute("PRAGMA table_info(research_execution_manifests)")}
            artifact_columns = {row["name"] for row in conn.execute("PRAGMA table_info(research_analysis_artifacts)")}
    assert {"research_source_objects", "research_execution_manifests"}.issubset(tables)
    assert {"source_hash", "dependency_hash", "random_seed", "manifest_hash", "reproducibility_key"}.issubset(manifest_columns)
    assert "execution_manifest_id" in artifact_columns


def test_forged_client_hash_is_rejected_against_server_bytes(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    headers = _seed(app)
    client = app.test_client()
    pipeline = _catalog(client, headers)
    snapshot = _snapshot(client, headers, "a" * 64)
    job_id = _job(client, headers, snapshot.get_json()["data"]["id"], pipeline, "f18-forged")
    response = client.post(f"/api/research/analysis/jobs/{job_id}/execute-synthetic", headers=headers["admin-f18"])
    assert response.status_code == 409
    assert response.get_json()["error"]["code"] == "source_hash_mismatch"


def test_source_replacement_after_snapshot_is_detected(tmp_path, monkeypatch):
    content_dir = tmp_path / "content"
    shutil.copytree(ROOT / "content", content_dir)
    app, headers, client, _, _, job_id = _setup_job(tmp_path, monkeypatch, content_dir=content_dir, key="f18-replaced")
    source_path = content_dir / FIXTURE_NAME
    source_path.write_bytes(source_path.read_bytes() + b"\n")
    response = client.post(f"/api/research/analysis/jobs/{job_id}/execute-synthetic", headers=headers["admin-f18"])
    assert response.status_code == 409
    assert response.get_json()["error"]["code"] == "source_hash_mismatch"


def test_wrong_algorithm_version_and_cross_user_selection_are_blocked(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    headers = _seed(app)
    client = app.test_client()
    pipeline = _catalog(client, headers)
    snapshot = _snapshot(client, headers, pipeline["resource_hash"])
    job_id = _job(
        client,
        headers,
        snapshot.get_json()["data"]["id"],
        pipeline,
        "f18-wrong-version",
        version="stale-algorithm",
    )
    rejected = client.post(f"/api/research/analysis/jobs/{job_id}/execute-synthetic", headers=headers["admin-f18"])
    cross_user = _snapshot(
        client,
        headers,
        pipeline["resource_hash"],
        participant="other-parent-f18",
        enrollment="enrollment-f18-other",
    )
    assert rejected.status_code == 409 and rejected.get_json()["error"]["code"] == "analysis_version_mismatch"
    assert cross_user.status_code in {403, 404}


def test_public_complete_rejects_arbitrary_metrics_without_server_proof(tmp_path, monkeypatch):
    app, headers, client, _, _, job_id = _setup_job(tmp_path, monkeypatch, key="f18-public-complete")
    claimed = client.post(f"/api/research/analysis/jobs/{job_id}/claim", headers=headers["admin-f18"], json={})
    assert claimed.status_code == 200
    response = client.post(
        f"/api/research/analysis/jobs/{job_id}/complete",
        headers=headers["admin-f18"],
        json={"metrics": {"coverage_rate": 1, "unknown_rate": 0, "sample_size": 20, "quality_status": "sufficient", "result": {}, "warnings": []}},
    )
    assert response.status_code == 409
    assert response.get_json()["error"]["code"] == "server_execution_proof_required"
    with app.app_context():
        from database import get_connection

        with get_connection() as conn:
            assert conn.execute("SELECT COUNT(*) AS count FROM research_analysis_artifacts").fetchone()["count"] == 0


def test_server_execution_binds_complete_manifest_and_deletable_artifact(tmp_path, monkeypatch):
    app, headers, client, pipeline, _, job_id = _setup_job(tmp_path, monkeypatch, key="f18-success")
    response = client.post(f"/api/research/analysis/jobs/{job_id}/execute-synthetic", headers=headers["admin-f18"])
    assert response.status_code == 200
    artifact_id = response.get_json()["data"]["result_artifact_id"]
    with app.app_context():
        from database import get_connection

        with get_connection() as conn:
            manifest = dict(conn.execute("SELECT * FROM research_execution_manifests WHERE job_id = ?", (job_id,)).fetchone())
            source = dict(conn.execute("SELECT * FROM research_source_objects WHERE id = ?", (manifest["source_object_id"],)).fetchone())
            artifact = dict(conn.execute("SELECT * FROM research_analysis_artifacts WHERE id = ?", (artifact_id,)).fetchone())
    required = json.loads((ROOT / "config" / "rc0810" / "research_execution_manifest_policy.json").read_text(encoding="utf-8"))["required_manifest_fields"]
    assert manifest["status"] == "consumed" and all(manifest[field] not in (None, "") for field in required)
    assert manifest["algorithm_version"] == pipeline["analysis_version"]
    assert source["server_hash"] == pipeline["resource_hash"] and source["storage_path"] == FIXTURE_NAME
    assert hashlib.sha256(bytes(source["payload_blob"])).hexdigest() == source["server_hash"]
    assert len(source["payload_blob"]) == source["size_bytes"]
    assert artifact["execution_manifest_id"] == manifest["id"]
    deleted = client.delete(
        f"/api/research/analysis/artifacts/{artifact_id}",
        headers=headers["admin-f18"],
        json={"reason_code": "participant_withdrawal"},
    )
    assert deleted.status_code == 200 and deleted.get_json()["data"]["derived_data_only"] is True


def test_partial_tampered_wrong_job_and_replayed_proofs_are_rejected(tmp_path, monkeypatch):
    app, headers, client, _, _, job_id = _setup_job(tmp_path, monkeypatch, key="f18-proof")
    client.post(f"/api/research/analysis/jobs/{job_id}/claim", headers=headers["admin-f18"], json={})
    with app.app_context():
        from database import get_connection
        from services.research_execution_manifest_service import (
            ResearchManifestError,
            consume_completion_manifest,
            fail_execution_manifest,
            finalize_execution_manifest,
            prepare_execution_manifest,
            validate_completion_manifest,
        )
        from services.research_online_analysis_service import DICTIONARY_HASH, MODEL_VERSION, THRESHOLDS_HASH, _fixture_path

        valid_metrics = {
            "coverage_rate": 1,
            "unknown_rate": 0,
            "sample_size": 20,
            "quality_status": "sufficient",
            "result": {
                "suppressed": False,
                "categories": [],
                "category_definition": "合成类别",
                "catalog_version": "v1",
                "fixture_id": FIXTURE_ID,
                "data_mode": "project_owned_synthetic_only",
            },
            "warnings": [],
        }
        with get_connection() as conn:
            job = dict(conn.execute("SELECT * FROM research_analysis_jobs WHERE id = ?", (job_id,)).fetchone())
            snapshot = dict(conn.execute("SELECT * FROM research_analysis_snapshots WHERE id = ?", (job["snapshot_id"],)).fetchone())
            first = prepare_execution_manifest(
                conn, actor_id="admin-f18", job=job, snapshot_hash=snapshot["snapshot_hash"],
                source_id=FIXTURE_ID, source_type="synthetic_fixture", source_path=_fixture_path(),
                declared_hash=job["resource_hash"], model_version=MODEL_VERSION,
                dictionary_hash=DICTIONARY_HASH, thresholds_hash=THRESHOLDS_HASH, random_seed=0,
            )
            with pytest.raises(ResearchManifestError, match="完整"):
                finalize_execution_manifest(conn, first["id"], job["analysis_type"], {"result": {}})
            fail_execution_manifest(conn, first["id"], "partial_output_rejected")
            second = prepare_execution_manifest(
                conn, actor_id="admin-f18", job=job, snapshot_hash=snapshot["snapshot_hash"],
                source_id=FIXTURE_ID, source_type="synthetic_fixture", source_path=_fixture_path(),
                declared_hash=job["resource_hash"], model_version=MODEL_VERSION,
                dictionary_hash=DICTIONARY_HASH, thresholds_hash=THRESHOLDS_HASH, random_seed=0,
            )
            finalize_execution_manifest(conn, second["id"], job["analysis_type"], valid_metrics)
            with pytest.raises(ResearchManifestError):
                validate_completion_manifest(conn, job={**job, "id": "other-job"}, manifest_id=second["id"], metrics=valid_metrics)
            with pytest.raises(ResearchManifestError):
                validate_completion_manifest(conn, job=job, manifest_id=second["id"], metrics={**valid_metrics, "sample_size": 19})
            consume_completion_manifest(conn, second["id"], "artifact-f18")
            with pytest.raises(ResearchManifestError) as replay:
                validate_completion_manifest(conn, job=job, manifest_id=second["id"], metrics=valid_metrics)
            conn.commit()
    assert replay.value.code == "manifest_replay_rejected"


def test_algorithm_failure_marks_job_and_manifest_failed_without_partial_artifact(tmp_path, monkeypatch):
    app, headers, client, _, _, job_id = _setup_job(tmp_path, monkeypatch, key="f18-algorithm-failure")
    with app.app_context():
        service = importlib.import_module("services.research_online_analysis_service")
        monkeypatch.setattr(service, "_fixture_cases", lambda: (_ for _ in ()).throw(RuntimeError("synthetic failure")))
        response = client.post(f"/api/research/analysis/jobs/{job_id}/execute-synthetic", headers=headers["admin-f18"])
        from database import get_connection

        with get_connection() as conn:
            job = conn.execute("SELECT status, last_error_code FROM research_analysis_jobs WHERE id = ?", (job_id,)).fetchone()
            manifest = conn.execute("SELECT status, failure_code FROM research_execution_manifests WHERE job_id = ?", (job_id,)).fetchone()
            artifact_count = conn.execute("SELECT COUNT(*) AS count FROM research_analysis_artifacts WHERE job_id = ?", (job_id,)).fetchone()["count"]
    assert response.status_code == 503 and response.get_json()["error"]["code"] == "algorithm_execution_failed"
    assert job["status"] == "failed" and job["last_error_code"] == "algorithm_execution_failed"
    assert manifest["status"] == "failed" and manifest["failure_code"] == "algorithm_execution_failed"
    assert artifact_count == 0


def test_identical_manifest_inputs_reproduce_exact_result_and_seed_changes_key(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    headers = _seed(app)
    client = app.test_client()
    pipeline = _catalog(client, headers)
    snapshot = _snapshot(client, headers, pipeline["resource_hash"])
    snapshot_id = snapshot.get_json()["data"]["id"]
    job_ids = [
        _job(client, headers, snapshot_id, pipeline, "f18-repeat-1", seed=7),
        _job(client, headers, snapshot_id, pipeline, "f18-repeat-2", seed=7),
        _job(client, headers, snapshot_id, pipeline, "f18-repeat-3", seed=8),
    ]
    for job_id in job_ids:
        response = client.post(f"/api/research/analysis/jobs/{job_id}/execute-synthetic", headers=headers["admin-f18"])
        assert response.status_code == 200
    with app.app_context():
        from database import get_connection

        with get_connection() as conn:
            manifests = [
                dict(conn.execute("SELECT * FROM research_execution_manifests WHERE job_id = ?", (job_id,)).fetchone())
                for job_id in job_ids
            ]
    assert [item["reproducibility_status"] for item in manifests] == ["baseline", "match", "baseline"]
    assert manifests[0]["reproducibility_key"] == manifests[1]["reproducibility_key"]
    assert manifests[0]["result_hash"] == manifests[1]["result_hash"]
    assert manifests[2]["reproducibility_key"] != manifests[0]["reproducibility_key"]
