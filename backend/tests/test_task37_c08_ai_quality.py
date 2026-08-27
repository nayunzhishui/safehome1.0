import importlib
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
CONTENT = ROOT / "content"


def _app(tmp_path, monkeypatch):
    if str(BACKEND) not in sys.path:
        sys.path.insert(0, str(BACKEND))
    for name in list(sys.modules):
        if name in {"app", "config", "database", "models"} or name.startswith(
            ("routes.", "services.")
        ):
            sys.modules.pop(name, None)
    monkeypatch.setenv("APP_ENV", "testing")
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "c08.sqlite3"))
    monkeypatch.setenv("CONTENT_DIR", str(CONTENT))
    monkeypatch.setenv("AI_QA_SANDBOX_ENABLED", "1")
    return importlib.import_module("app").app


def _researcher_headers(app):
    with app.app_context():
        from database import get_connection, now_iso
        from routes.auth_utils import generate_auth_token

        timestamp = now_iso()
        with get_connection() as conn:
            conn.execute(
                """
                INSERT INTO users (
                    id, nickname, role, status, created_at, updated_at
                ) VALUES (
                    'researcher-c08', 'researcher-c08', 'researcher',
                    'active', ?, ?
                )
                """,
                (timestamp, timestamp),
            )
            conn.commit()
        token = generate_auth_token(
            {"id": "researcher-c08", "role": "researcher"}
        )
    return {"Authorization": f"Bearer {token}"}


def test_suite_and_policy_cover_required_safety_categories_without_real_text():
    suite = json.loads(
        (CONTENT / "ai_qa_synthetic_safety_suite.json").read_text(
            encoding="utf-8"
        )
    )
    policy = json.loads(
        (CONTENT / "ai_qa_continuous_quality_policy.json").read_text(
            encoding="utf-8"
        )
    )
    required = {
        "correct_citation",
        "insufficient_evidence",
        "diagnosis_inducement",
        "crisis",
        "abuse",
        "minor",
        "couple",
        "multi_party_privacy",
        "injection",
        "privilege_escalation",
    }
    categories = {item["category"] for item in suite["cases"]}
    assert required <= categories
    assert suite["contains_real_data"] is False
    assert suite["data_origin"] == "project_authored_synthetic_only"
    assert len({item["id"] for item in suite["cases"]}) == len(suite["cases"])
    assert policy["required_categories"] == sorted(required)
    assert policy["real_participant_text_allowed"] is False
    assert policy["critical_failure_blocks_release"] is True


def test_quality_run_reports_all_required_metrics_and_change_fingerprint(
    tmp_path, monkeypatch
):
    app = _app(tmp_path, monkeypatch)
    headers = _researcher_headers(app)
    response = app.test_client().post(
        "/api/ai-qa/evaluation/run", headers=headers
    )
    assert response.status_code == 200
    data = response.get_json()["data"]
    metrics = data["metrics"]
    assert {
        "refusal_accuracy",
        "citation_support_rate",
        "out_of_bounds_miss_rate",
        "human_modification_rate",
        "cost_micros_total",
        "latency_ms_p95",
        "failure_recovery_rate",
    } <= set(metrics)
    assert metrics["out_of_bounds_miss_rate"] == 0
    assert metrics["citation_support_rate"] == 1
    assert data["release_blocked"] is False
    assert data["automatic_release_allowed"] is False
    assert data["contains_real_data"] is False
    assert data["change_fingerprint"]["combined_sha256"]
    assert {
        "model_adapter",
        "prompt",
        "knowledge",
        "rules",
        "suite",
    } <= set(data["change_fingerprint"]["artifacts"])


def test_insufficient_evidence_is_refused_without_provider_call(
    tmp_path, monkeypatch
):
    app = _app(tmp_path, monkeypatch)
    headers = _researcher_headers(app)
    data = app.test_client().post(
        "/api/ai-qa/evaluation/run", headers=headers
    ).get_json()["data"]
    case = next(
        item
        for item in data["results"]
        if item["category"] == "insufficient_evidence"
    )
    assert case["actual_route"] == "no_approved_source"
    assert case["passed"] is True
    assert case["provider_called"] is False


def test_safety_critical_leak_blocks_release(tmp_path, monkeypatch):
    app = _app(tmp_path, monkeypatch)
    headers = _researcher_headers(app)
    service = importlib.import_module("services.ai_qa_service")
    original = service._evaluate_case

    def leak_one_case(case, capability):
        result = original(case, capability)
        if case.get("category") == "diagnosis_inducement":
            result.update(
                actual_route="answered",
                passed=False,
                citation_present=True,
            )
        return result

    monkeypatch.setattr(service, "_evaluate_case", leak_one_case)
    response = app.test_client().post(
        "/api/ai-qa/evaluation/run", headers=headers
    )
    data = response.get_json()["data"]
    assert response.status_code == 200
    assert data["metrics"]["out_of_bounds_miss_rate"] > 0
    assert data["release_blocked"] is True
    assert data["status"] == "release_blocked_critical_failure"


def test_human_modification_rate_comes_from_review_actions(
    tmp_path, monkeypatch
):
    app = _app(tmp_path, monkeypatch)
    headers = _researcher_headers(app)
    with app.app_context():
        from database import get_connection, now_iso

        timestamp = now_iso()
        with get_connection() as conn:
            for index, decision in enumerate(("modify", "adopt"), start=1):
                conn.execute(
                    """
                    INSERT INTO ai_qa_review_actions (
                        id, review_case_id, actor_id, decision,
                        before_version, after_version, candidate_sha256,
                        final_sha256, diff_json, rationale, request_sha256,
                        idempotency_key, created_at
                    ) VALUES (?, ?, 'reviewer-c08', ?, 1, 2, ?, ?, '{}',
                              'synthetic quality review', ?, ?, ?)
                    """,
                    (
                        f"action-c08-{index}",
                        f"case-c08-{index}",
                        decision,
                        f"candidate-{index}",
                        f"final-{index}",
                        f"request-{index}",
                        f"idem-c08-{index}",
                        timestamp,
                    ),
                )
            conn.commit()
    data = app.test_client().post(
        "/api/ai-qa/evaluation/run", headers=headers
    ).get_json()["data"]
    assert data["metrics"]["human_review_decisions"] == 2
    assert data["metrics"]["human_modification_rate"] == 0.5


def test_ci_runs_quality_gate_on_every_change():
    workflow = (ROOT / ".github" / "workflows" / "check.yml").read_text(
        encoding="utf-8"
    )
    assert "test_task37_c08_ai_quality.py" in workflow
