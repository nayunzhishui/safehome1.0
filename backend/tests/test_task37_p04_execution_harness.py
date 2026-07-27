import importlib
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
CONTRACT = ROOT / "content" / "task37_execution_harness.json"


def _fresh_app(tmp_path, monkeypatch):
    sys.path.insert(0, str(BACKEND))
    for name in list(sys.modules):
        if name in {"app", "config", "database", "models"} or name.startswith(("routes.", "services.")):
            sys.modules.pop(name, None)
    monkeypatch.setenv("APP_ENV", "testing")
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "task37-p04.sqlite3"))
    monkeypatch.setenv("CONTENT_DIR", str(ROOT / "content"))
    monkeypatch.setenv("RELIABILITY_WORKBENCH_ENABLED", "1")
    monkeypatch.setenv("RELIABILITY_JOB_EXECUTION_ENABLED", "1")
    return importlib.import_module("app").app


def _seed(app):
    with app.app_context():
        from database import get_connection, now_iso
        from routes.auth_utils import generate_auth_token

        now = now_iso()
        with get_connection() as conn:
            for actor_id, role in (("admin-p04", "admin"), ("researcher-p04", "researcher")):
                conn.execute(
                    "INSERT INTO users (id, nickname, role, status, created_at, updated_at) VALUES (?, ?, ?, 'active', ?, ?)",
                    (actor_id, actor_id, role, now, now),
                )
            conn.commit()
        return {
            role: {"Authorization": f"Bearer {generate_auth_token({'id': actor_id, 'role': role})}"}
            for actor_id, role in (("admin-p04", "admin"), ("researcher-p04", "researcher"))
        }


def test_contract_declares_seven_states_limits_metrics_and_independent_kill_switches():
    payload = json.loads(CONTRACT.read_text(encoding="utf-8"))
    assert payload["schema"] == "safehome.task37.execution-harness.v1"
    assert len(payload["job_states"]) == 7
    assert set(payload["error_categories"]) == {"user", "data", "model", "provider", "permission"}
    assert set(payload["metrics"]) >= {
        "throughput",
        "queue_duration_ms",
        "failure_rate",
        "coverage_rate",
        "abstention_rate",
        "cost_microunits",
        "human_backlog",
    }
    assert set(payload["kill_switches"]) == {
        "affective_computing",
        "social_network_analysis",
        "participant_ai_qa",
    }
    assert payload["logging"]["stores_raw_text"] is False


def test_dispatch_is_idempotent_and_rejects_sensitive_payload(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    headers = _seed(app)
    client = app.test_client()
    body = {
        "capability": "affective_computing",
        "source_type": "computation_dataset",
        "source_id": "dataset-p04",
        "idempotency_key": "p04-idempotent",
        "max_attempts": 3,
    }
    first = client.post("/api/reliability/computation-harness/jobs", headers=headers["admin"], json=body)
    replay = client.post("/api/reliability/computation-harness/jobs", headers=headers["admin"], json=body)
    rejected = client.post(
        "/api/reliability/computation-harness/jobs",
        headers=headers["admin"],
        json={**body, "idempotency_key": "p04-unsafe", "raw_text": "不得进入队列"},
    )
    assert first.status_code == 201 and replay.status_code == 200
    assert first.get_json()["data"]["id"] == replay.get_json()["data"]["id"]
    assert rejected.status_code == 400
    assert rejected.get_json()["error"]["code"] == "sensitive_payload_rejected"


def test_cancel_freeze_recover_and_independent_switches(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    headers = _seed(app)
    client = app.test_client()

    def create(key):
        return client.post(
            "/api/reliability/computation-harness/jobs",
            headers=headers["admin"],
            json={
                "capability": "social_network_analysis",
                "source_type": "computation_dataset",
                "source_id": f"dataset-{key}",
                "idempotency_key": key,
            },
        ).get_json()["data"]["id"]

    canceled_id = create("p04-cancel")
    canceled = client.post(
        f"/api/reliability/computation-harness/jobs/{canceled_id}/cancel",
        headers=headers["admin"],
    )
    assert canceled.get_json()["data"]["status"] == "canceled"

    frozen_id = create("p04-freeze")
    frozen = client.post(
        f"/api/reliability/computation-harness/jobs/{frozen_id}/freeze",
        headers=headers["admin"],
        json={"reason_code": "controlled_rollout"},
    )
    resumed = client.post(
        f"/api/reliability/computation-harness/jobs/{frozen_id}/resume",
        headers=headers["admin"],
        json={"reason_code": "manual_dependency_recovered"},
    )
    assert frozen.get_json()["data"]["status"] == "suspended"
    assert resumed.get_json()["data"]["status"] == "pending"

    flags = client.get("/api/reliability/feature-flags", headers=headers["researcher"]).get_json()["data"]["items"]
    relevant = {item["flag_name"]: item["enabled"] for item in flags if item["flag_name"] in {
        "affective_computing",
        "social_network_analysis",
        "participant_ai_qa",
    }}
    assert relevant == {
        "affective_computing": False,
        "social_network_analysis": False,
        "participant_ai_qa": False,
    }


def test_heartbeat_metrics_and_error_categories_are_metadata_only(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    headers = _seed(app)
    client = app.test_client()
    heartbeat = client.post(
        "/api/reliability/computation-harness/heartbeat",
        headers=headers["admin"],
        json={"worker_id": "worker-private-001", "capacity": 2, "active_jobs": 1},
    )
    metrics = client.get(
        "/api/reliability/computation-harness/metrics",
        headers=headers["researcher"],
    )
    categories = client.get(
        "/api/reliability/computation-harness/error-categories",
        headers=headers["researcher"],
    )
    assert heartbeat.status_code == 200
    assert heartbeat.get_json()["data"]["worker_ref"].startswith("worker_")
    assert "worker-private-001" not in json.dumps(heartbeat.get_json(), ensure_ascii=False)
    metric_payload = metrics.get_json()["data"]
    assert set(metric_payload) >= {
        "throughput",
        "queue_duration_ms",
        "failure_rate",
        "coverage_rate",
        "abstention_rate",
        "cost_microunits",
        "human_backlog",
    }
    assert set(categories.get_json()["data"]["items"]) == {"user", "data", "model", "provider", "permission"}

    with app.app_context():
        from database import get_connection

        with get_connection() as conn:
            rows = conn.execute(
                "SELECT request_id, path, error_code FROM observability_events WHERE module = 'computation_worker'"
            ).fetchall()
            assert len(rows) == 1
            assert "worker-private-001" not in json.dumps([dict(row) for row in rows], ensure_ascii=False)
