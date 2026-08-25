import importlib
import json
import shutil
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))


def _fresh_app(tmp_path, monkeypatch, *, token="ops-health-test-token"):
    for name in list(sys.modules):
        if name in {"app", "config", "database", "models"} or name.startswith(
            ("routes.", "services.")
        ):
            sys.modules.pop(name, None)
    content_dir = tmp_path / "content"
    shutil.copytree(ROOT / "content", content_dir)
    monkeypatch.setenv("APP_ENV", "testing")
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "f21.sqlite3"))
    monkeypatch.setenv("CONTENT_DIR", str(content_dir))
    monkeypatch.setenv("OPERATIONS_HEALTH_TOKEN", token)
    return importlib.import_module("app").app


def _policy():
    return json.loads(
        (ROOT / "config" / "rc0810" / "operations_reliability_policy.json").read_text(
            encoding="utf-8"
        )
    )


def test_f21_policy_freezes_protected_health_contract():
    policy = _policy()
    contract = policy["health_contract"]
    assert contract["public_fields"] == ["ok", "service", "version"]
    assert contract["protected_paths"] == ["/healthz/deep", "/readyz"]
    assert contract["forwarded_headers_trusted"] is False
    assert set(contract["protected_components"]) == {
        "database", "redis", "queues", "content", "scheduler", "deployment"
    }


def test_f21_public_health_is_minimal(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    response = app.test_client().get("/healthz", environ_base={"REMOTE_ADDR": "198.51.100.8"})
    assert response.status_code == 200
    assert set(response.get_json()) == {"ok", "service", "version"}


def test_f21_external_deep_health_without_token_is_denied(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    for path in ("/healthz/deep", "/readyz"):
        response = client.get(path, environ_base={"REMOTE_ADDR": "198.51.100.8"})
        assert response.status_code == 403
        assert response.get_json()["error"]["code"] == "operations_health_forbidden"


def test_f21_operations_token_allows_protected_health(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    response = app.test_client().get(
        "/readyz",
        headers={"X-Operations-Token": "ops-health-test-token"},
        environ_base={"REMOTE_ADDR": "198.51.100.8"},
    )
    assert response.status_code == 200
    body = response.get_json()
    assert {"database", "redis", "queues", "content", "scheduler", "deployment"} <= set(body)
    assert "ops-health-test-token" not in response.get_data(as_text=True)


def test_f21_internal_source_ignores_forwarded_headers_and_is_allowed(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    response = app.test_client().get(
        "/healthz/deep",
        headers={"X-Forwarded-For": "198.51.100.8"},
        environ_base={"REMOTE_ADDR": "127.0.0.1"},
    )
    assert response.status_code == 200
    assert response.get_json()["ok"] is True
    source = (BACKEND / "services" / "operations_reliability_service.py").read_text(encoding="utf-8")
    assert "apply_pending_schema_migrations" not in source


def test_f21_sli_slo_and_alerts_have_actionable_fields():
    policy = _policy()
    metrics = {item["metric"] for item in policy["sli_slo"]}
    assert {
        "request_success_rate", "request_latency_p95_ms", "http_5xx_rate",
        "authentication_failure_rate", "database_or_redis_unavailable", "queue_backlog",
        "risk_review_sla_breach", "external_message_failure_rate", "scheduler_delay_seconds",
    } <= metrics
    assert all(
        {"id", "level", "threshold", "duration", "notify", "silence", "recovery"} <= set(item)
        for item in policy["alerts"]
    )


def test_f21_three_independent_rollback_runbooks_are_fail_safe():
    runbooks = _policy()["rollback_runbooks"]
    assert set(runbooks) == {"code_version", "database_migration", "content_artifact"}
    assert "do_not_reverse_database_schema_automatically" in runbooks["code_version"]["data_rule"]
    assert "never_drop_schema_automatically" in runbooks["database_migration"]["data_rule"]
    assert "historical_results_keep_original_payload" in runbooks["content_artifact"]["data_rule"]


def test_f21_incident_record_rejects_sensitive_body_and_keeps_timeline():
    service = importlib.import_module("services.operations_reliability_service")
    payload = {
        "impact_code": "affected_delivery_unknown_count",
        "started_at": "2026-08-26T00:00:00+08:00",
        "detected_at": "2026-08-26T00:01:00+08:00",
        "recovered_at": None,
        "evidence_refs": ["audit:event-1"],
        "decisions": ["disable_delivery"],
        "followup_actions": ["reconcile_recipients"],
    }
    assert service.sanitize_incident_record(payload) == payload
    try:
        service.sanitize_incident_record({**payload, "participant_text": "sensitive"})
    except service.OperationsReliabilityError as exc:
        assert exc.code == "incident_sensitive_field_forbidden"
    else:
        raise AssertionError("participant_text must be rejected")


def test_f21_p0_categories_cover_required_stop_notify_repair_and_reconcile():
    categories = _policy()["incident_record"]["p0_categories"]
    assert {item["id"] for item in categories} == {
        "psychological_content_misdelivery", "cross_object_disclosure", "deletion_failure",
        "high_risk_feedback_error", "external_message_misdelivery",
    }
    assert all({"stop", "notify", "repair", "reconcile"} <= set(item) for item in categories)


def test_f21_isolated_drills_detect_and_recover_all_five_scenarios():
    service = importlib.import_module("services.operations_reliability_service")
    report = service.run_isolated_drills(_policy())
    assert report["ok"] is True
    assert {item["scenario"] for item in report["results"]} == {
        "http_5xx", "database_outage", "redis_outage", "queue_backlog", "content_version_error"
    }
    assert all(item["alert_detected"] and item["recovery_verified"] for item in report["results"])
    assert report["production_mutation_executed"] is False


def test_f21_performance_cost_and_account_continuity_are_frozen():
    policy = _policy()
    assert {"p50_ms", "p95_ms", "p99_ms", "error_rate", "concurrency", "db_queries_per_request"} <= set(
        policy["performance_budget"]["core_api"]
    )
    assert policy["performance_budget"]["miniprogram"]["main_package_mb"] == 2
    assert {item["resource"] for item in policy["cost_quota"]} == {
        "cloudbase_requests", "mysql_storage", "logs", "backups", "external_messages",
        "production_ai", "human_review",
    }
    assert all(item["warn_at"] == 0.8 and item["owner"] for item in policy["cost_quota"])
    assert all(item["minimum_admins"] >= 2 and item["single_person_dependency"] is False for item in policy["account_continuity"])


def test_f21_external_operations_and_account_recovery_gates_remain_pending():
    policy = _policy()
    assert policy["external_gates"] == {
        "operations_owner": "pending_external",
        "test_cloud_observation": "pending_external",
        "account_recovery_drill": "pending_external",
    }
    assert policy["production_gate_eligible"] is False
    registry = json.loads((ROOT / "content" / "rc0810_release_candidate_registry.json").read_text(encoding="utf-8"))
    task = next(item for item in registry["tasks"] if item["id"] == "RC0810-F21")
    assert task["change_budget"]["expected_migrations"] == 0
