import importlib
import json
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
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "task34.sqlite3"))
    monkeypatch.setenv("CONTENT_DIR", str(ROOT / "content"))
    monkeypatch.setenv("OPERATIONS_GOVERNANCE_WORKBENCH_ENABLED", "1")
    monkeypatch.setenv("OPERATIONS_LOCAL_RELEASE_ENABLED", "1")
    monkeypatch.setenv("OPERATIONS_PRODUCTION_RELEASE_ENABLED", "0")
    monkeypatch.setenv("AI_QA_ENABLED", "0")
    monkeypatch.setenv("AI_QA_PROVIDER", "fake")
    return importlib.import_module("app").app


def _actors(app):
    specs = [
        ("participant-t34", "parent"),
        ("researcher-a-t34", "researcher"),
        ("researcher-b-t34", "researcher"),
        ("supervisor-a-t34", "supervisor"),
        ("supervisor-b-t34", "supervisor"),
        ("admin-a-t34", "admin"),
        ("admin-b-t34", "admin"),
    ]
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
        return {
            actor_id: {"Authorization": f"Bearer {auth.generate_auth_token({'id': actor_id, 'role': role})}"}
            for actor_id, role in specs
        }


def _create_package(client, headers, version="task34-v1", previous_package_id=None, target_environment="local_synthetic"):
    payload = {
        "package_version": version,
        "risk_level": "high",
        "target_environment": target_environment,
    }
    if previous_package_id:
        payload["previous_package_id"] = previous_package_id
    return client.post("/api/operations-governance/packages", headers=headers["researcher-a-t34"], json=payload)


def _approve_and_release(client, headers, package_id):
    assert client.post(
        f"/api/operations-governance/packages/{package_id}/replay",
        headers=headers["admin-a-t34"],
    ).status_code == 200
    assert client.post(
        f"/api/operations-governance/packages/{package_id}/submit",
        headers=headers["researcher-a-t34"],
    ).status_code == 200
    assert client.post(
        f"/api/operations-governance/packages/{package_id}/reviews",
        headers=headers["supervisor-b-t34"],
        json={"decision": "recommended", "evidence_ref": "evidence://task34/review"},
    ).status_code == 200
    approvals = [
        ("researcher-b-t34", "research"),
        ("supervisor-a-t34", "psychology"),
        ("admin-a-t34", "security"),
    ]
    for actor_id, domain in approvals:
        response = client.post(
            f"/api/operations-governance/packages/{package_id}/approvals",
            headers=headers[actor_id],
            json={"domain": domain, "decision": "approved", "evidence_ref": f"evidence://task34/{domain}"},
        )
        assert response.status_code == 200
    return client.post(
        f"/api/operations-governance/packages/{package_id}/release",
        headers=headers["admin-b-t34"],
        json={"confirmation": "LOCAL_SYNTHETIC_RELEASE_ONLY"},
    )


def test_registry_covers_every_machine_contract_operation_and_public_status_is_minimal(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    headers = _actors(app)
    client = app.test_client()
    public = client.get("/api/operations-governance/public-status")
    denied = client.get("/api/operations-governance/registry", headers=headers["participant-t34"])
    internal = client.get("/api/operations-governance/registry", headers=headers["researcher-a-t34"])
    assert public.status_code == 200 and denied.status_code == 403 and internal.status_code == 200
    data = internal.get_json()["data"]
    contract = json.loads((ROOT / "shared/contracts/api-contract.json").read_text(encoding="utf-8"))
    covered = {operation_id for item in data["capabilities"] for operation_id in item["operation_ids"]}
    assert covered == {item["operation_id"] for item in contract["endpoints"]}
    assert public.get_json()["data"]["production_release_approved"] is False
    assert "capabilities" not in public.get_json()["data"]


def test_release_manifest_and_asset_cards_are_complete_content_addressed_and_non_diagnostic():
    manifest = json.loads((ROOT / "content/operations_release_manifest.json").read_text(encoding="utf-8"))
    cards = json.loads((ROOT / "content/operations_asset_cards.json").read_text(encoding="utf-8"))
    assert {item["artifact_type"] for item in manifest["artifacts"]} >= {"content", "rule", "model", "dictionary", "prompt", "knowledge_index"}
    assert all(len(item["sha256"]) == 64 and item["size_bytes"] > 0 for item in manifest["artifacts"])
    assert {item["card_type"] for item in cards["cards"]} >= {"dataset", "rule", "model"}
    required = {"source", "license", "metrics", "bias", "failure_modes", "out_of_domain", "admission_criteria", "disable_criteria"}
    assert all(required <= set(item) for item in cards["cards"])
    assert "参与者或家庭变差" not in json.dumps(cards, ensure_ascii=False)


def test_high_risk_release_requires_independent_review_multi_domain_approval_replay_and_release_actor(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    headers = _actors(app)
    client = app.test_client()
    created = _create_package(client, headers)
    assert created.status_code == 201
    package_id = created.get_json()["data"]["id"]
    assert created.get_json()["data"]["manifest_hash"]
    early = client.post(
        f"/api/operations-governance/packages/{package_id}/release",
        headers=headers["admin-b-t34"],
        json={"confirmation": "LOCAL_SYNTHETIC_RELEASE_ONLY"},
    )
    assert early.status_code == 409
    released = _approve_and_release(client, headers, package_id)
    assert released.status_code == 200
    data = released.get_json()["data"]
    assert data["status"] == "active_local_synthetic"
    assert data["production_release_approved"] is False
    assert len({item["reviewer_id"] for item in data["approvals"]}) == 3
    assert data["released_by"] == "admin-b-t34"


def test_revision_is_new_version_and_atomic_pause_resume_and_rollback_preserve_evidence(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    headers = _actors(app)
    client = app.test_client()
    first = _create_package(client, headers, "task34-v1").get_json()["data"]
    assert _approve_and_release(client, headers, first["id"]).status_code == 200
    duplicate = _create_package(client, headers, "task34-v1")
    assert duplicate.status_code == 409
    second = _create_package(client, headers, "task34-v2", first["id"]).get_json()["data"]
    assert _approve_and_release(client, headers, second["id"]).status_code == 200
    paused = client.post(
        f"/api/operations-governance/packages/{second['id']}/pause",
        headers=headers["admin-a-t34"],
        json={"reason_code": "synthetic_safety_pause"},
    )
    assert paused.status_code == 200 and paused.get_json()["data"]["status"] == "paused"
    assert client.post(
        f"/api/operations-governance/packages/{second['id']}/replay",
        headers=headers["admin-a-t34"],
    ).status_code == 200
    resumed = client.post(
        f"/api/operations-governance/packages/{second['id']}/resume",
        headers=headers["admin-b-t34"],
        json={"reason_code": "synthetic_evidence_rechecked"},
    )
    assert resumed.status_code == 200 and resumed.get_json()["data"]["status"] == "active_local_synthetic"
    rolled = client.post(
        "/api/operations-governance/runtime/rollback",
        headers=headers["admin-b-t34"],
        json={"target_package_id": first["id"], "reason_code": "synthetic_atomic_rollback"},
    )
    assert rolled.status_code == 200
    assert rolled.get_json()["data"]["active_package_id"] == first["id"]
    detail = client.get(f"/api/operations-governance/packages/{second['id']}", headers=headers["researcher-b-t34"]).get_json()["data"]
    assert detail["manifest_hash"] == second["manifest_hash"] and detail["replay_runs"]


def test_high_severity_regression_blocks_submission(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    headers = _actors(app)
    service = importlib.import_module("services.operations_governance_service")
    monkeypatch.setattr(service, "execute_fixed_replay", lambda *_args, **_kwargs: {
        "suite_version": "synthetic-regression",
        "results": [{"case_id": "risk-block", "severity": "critical", "passed": False}],
        "metrics": {"total": 1, "failed": 1, "high_severity_regressions": 1, "wording_diff_count": 0},
        "snapshot_hash": "f" * 64,
    })
    client = app.test_client()
    package = _create_package(client, headers, "task34-regression").get_json()["data"]
    replay = client.post(f"/api/operations-governance/packages/{package['id']}/replay", headers=headers["admin-a-t34"])
    blocked = client.post(f"/api/operations-governance/packages/{package['id']}/submit", headers=headers["researcher-a-t34"])
    assert replay.get_json()["data"]["status"] == "blocked_high_severity_regression"
    assert blocked.status_code == 409


def test_monitoring_drift_only_requests_review_and_never_labels_people_or_families(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    headers = _actors(app)
    with app.app_context():
        database = importlib.import_module("database")
        with database.get_connection() as conn:
            now = database.now_iso()
            for index in range(4):
                conn.execute(
                    "INSERT INTO feedback_ledger (id,user_id,source_type,source_id,content_version,evaluation,status,created_at,updated_at) VALUES (?,?,?,?,?,'uncomfortable','active',?,?)",
                    (f"ledger-{index}", "participant-t34", "synthetic", f"s-{index}", "v1", now, now),
                )
                conn.execute(
                    "INSERT INTO ai_qa_provider_events (id,user_id,provider,model_version,status,error_code,created_at) VALUES (?,?, 'fake','v1','failed','synthetic_error',?)",
                    (f"provider-{index}", "participant-t34", now),
                )
            conn.commit()
    response = app.test_client().post(
        "/api/operations-governance/monitoring/snapshots",
        headers=headers["researcher-a-t34"],
        json={"window_days": 30, "environment": "local_synthetic"},
    )
    assert response.status_code == 201
    data = response.get_json()["data"]
    assert data["review_required"] is True
    assert data["automatic_participant_or_family_judgment"] is False
    serialized = json.dumps(data, ensure_ascii=False)
    assert "诊断" not in serialized and "家庭变差" not in serialized


def test_severe_incident_disables_capability_preserves_evidence_and_queues_notifications(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    headers = _actors(app)
    client = app.test_client()
    capability_id = client.get("/api/operations-governance/registry", headers=headers["admin-a-t34"]).get_json()["data"]["capabilities"][0]["id"]
    payload = {
        "capability_id": capability_id,
        "incident_type": "data_leak",
        "severity": "critical",
        "evidence_refs": ["evidence://synthetic/no-participant-text"],
        "summary_code": "synthetic_leak_drill",
    }
    denied = client.post("/api/operations-governance/incidents", headers=headers["participant-t34"], json=payload)
    created = client.post("/api/operations-governance/incidents", headers=headers["supervisor-a-t34"], json=payload)
    rejected_raw = client.post("/api/operations-governance/incidents", headers=headers["supervisor-a-t34"], json={**payload, "participant_text": "不应保存"})
    assert denied.status_code == 403 and created.status_code == 201 and rejected_raw.status_code == 400
    data = created.get_json()["data"]
    assert data["capability_disabled"] is True
    assert data["evidence_hold_hash"] and len(data["notifications"]) >= 3
    assert all(item["status"] == "queued" for item in data["notifications"])
    postmortem = client.post(
        f"/api/operations-governance/incidents/{data['id']}/postmortem",
        headers=headers["admin-a-t34"],
        json={"root_cause_code": "synthetic_drill", "corrective_actions": ["复核对象授权", "回放固定安全集"]},
    )
    assert postmortem.status_code == 200
    assert postmortem.get_json()["data"]["status"] == "postmortem_recorded_human_close_pending"
    assert postmortem.get_json()["data"]["capability_disabled"] is True


def test_evidence_package_keeps_human_cloud_device_ethics_and_production_gates_unsigned(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    headers = _actors(app)
    client = app.test_client()
    denied = client.post("/api/operations-governance/evidence-packages", headers=headers["researcher-a-t34"])
    package = client.post("/api/operations-governance/evidence-packages", headers=headers["supervisor-a-t34"])
    assert denied.status_code == 403 and package.status_code == 201
    data = package.get_json()["data"]
    assert data["status"] == "draft_for_external_governance_review"
    assert data["human_approved"] is False
    assert data["ethics_approved"] is False
    assert data["cloud_approved"] is False
    assert data["device_approved"] is False
    assert data["production_release_approved"] is False
    assert data["signatures"] == []


def test_package_bundle_is_redacted_from_api_and_manifest_tamper_blocks_replay(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    headers = _actors(app)
    client = app.test_client()
    package = _create_package(client, headers, "task34-tamper").get_json()["data"]
    assert all("bundle_b64" not in artifact for artifact in package["manifest"]["artifacts"])
    with app.app_context():
        database = importlib.import_module("database")
        with database.get_connection() as conn:
            row = conn.execute("SELECT manifest_json FROM operations_release_packages WHERE id = ?", (package["id"],)).fetchone()
            manifest = json.loads(row["manifest_json"])
            manifest["artifacts"][0]["sha256"] = "0" * 64
            conn.execute("UPDATE operations_release_packages SET manifest_json = ? WHERE id = ?", (json.dumps(manifest, ensure_ascii=False), package["id"]))
            conn.commit()
    replay = client.post(f"/api/operations-governance/packages/{package['id']}/replay", headers=headers["admin-a-t34"])
    assert replay.status_code == 409
    assert replay.get_json()["error"]["code"] == "package_integrity_failed"


def test_production_release_is_blocked_even_after_engineering_approval_without_external_gate(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    headers = _actors(app)
    client = app.test_client()
    package = _create_package(
        client,
        headers,
        "task34-production-candidate",
        target_environment="production_candidate",
    ).get_json()["data"]
    released = _approve_and_release(client, headers, package["id"])
    assert released.status_code == 503
    assert released.get_json()["error"]["code"] == "production_release_gate_disabled"
    detail = client.get(
        f"/api/operations-governance/packages/{package['id']}",
        headers=headers["researcher-a-t34"],
    ).get_json()["data"]
    assert detail["status"] == "approved"
    assert detail["production_release_approved"] is False
