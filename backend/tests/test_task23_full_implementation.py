import importlib
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = PROJECT_ROOT / "backend"


def _fresh_app(tmp_path, monkeypatch):
    sys.path.insert(0, str(BACKEND_ROOT))
    for name in list(sys.modules):
        if name in {"app", "config", "database", "models"} or name.startswith("routes.") or name.startswith("services."):
            sys.modules.pop(name, None)
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "safehome-test.sqlite3"))
    monkeypatch.setenv("CONTENT_DIR", str(PROJECT_ROOT / "content"))
    return importlib.import_module("app").app


def _login(client, code: str):
    data = client.post("/api/auth/wechat-login", json={"code": code, "nickname": code}).get_json()["data"]
    return data["user"]["id"], data["token"]


def _headers(token: str, key: str | None = None):
    headers = {"Authorization": f"Bearer {token}"}
    if key:
        headers["Idempotency-Key"] = key
    return headers


def _feedback_source(app, user_id: str):
    with app.app_context():
        from database import get_connection, now_iso

        with get_connection() as conn:
            conn.execute(
                """
                INSERT INTO feedback_results (
                    id, user_id, diary_id, tags_json, supportive_feedback,
                    recommended_card_ids_json, risk_level, created_at
                ) VALUES ('feedback-t23-full', ?, NULL, '[]', '支持性反馈', '[]', 'low', ?)
                """,
                (user_id, now_iso()),
            )
            conn.commit()
    return "feedback-t23-full"


def _assessment(client, token: str):
    response = client.post(
        "/api/assessment-results",
        headers=_headers(token),
        json={
            "worksheet_id": "student_profile_v1",
            "answers": [
                {"question_id": question_id, "value": "5"}
                for question_id in ["test_anxiety", "iu_score", "fear_score", "self_compassion"]
            ],
        },
    )
    assert response.status_code == 201
    return response.get_json()["data"]["id"]


def test_feedback_can_be_corrected_then_withdrawn_with_idempotent_history(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    user_id, token = _login(client, "t23-ledger-owner")
    _other_id, other_token = _login(client, "t23-ledger-other")
    source_id = _feedback_source(app, user_id)
    created = client.post(
        "/api/feedback-ledger",
        headers=_headers(token, "t23-rating"),
        json={"source_type": "instant_feedback", "source_id": source_id, "content_version": "v1", "evaluation": "matches"},
    ).get_json()["data"]

    corrected_response = client.post(
        f"/api/feedback-ledger/{created['id']}/actions",
        headers=_headers(token, "t23-correct"),
        json={"action": "correct", "replacement": {"content_version": "v2", "evaluation": "partly_matches"}},
    )
    assert corrected_response.status_code == 200
    corrected = corrected_response.get_json()["data"]
    assert corrected["status"] == "active"
    assert corrected["supersedes_id"] == created["id"]

    replay = client.post(
        f"/api/feedback-ledger/{created['id']}/actions",
        headers=_headers(token, "t23-correct"),
        json={"action": "correct", "replacement": {"content_version": "v2", "evaluation": "partly_matches"}},
    )
    assert replay.status_code == 200
    assert replay.get_json()["data"]["already_recorded"] is True

    denied = client.post(
        f"/api/feedback-ledger/{corrected['id']}/actions",
        headers=_headers(other_token, "t23-withdraw-other"),
        json={"action": "withdraw"},
    )
    assert denied.status_code == 404

    withdrawn = client.post(
        f"/api/feedback-ledger/{corrected['id']}/actions",
        headers=_headers(token, "t23-withdraw"),
        json={"action": "withdraw"},
    ).get_json()["data"]
    assert withdrawn["status"] == "withdrawn"
    assert withdrawn["participant_status"] == "withdrawn"
    assert withdrawn["withdrawn_at"]


def test_recommendation_strategy_can_be_replayed_and_snapshot_is_owner_scoped(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    _user_id, token = _login(client, "t23-replay-owner")
    _other_id, other_token = _login(client, "t23-replay-other")
    result_id = _assessment(client, token)

    response = client.post(
        "/api/training-plan/recommendations/replay",
        headers=_headers(token, "t23-replay-legacy"),
        json={"source_result_id": result_id, "strategy_version": "legacy_rule_order_v1"},
    )
    assert response.status_code == 201
    snapshot = response.get_json()["data"]
    assert snapshot["strategy_version"] == "legacy_rule_order_v1"
    assert snapshot["rollback_available"] is False
    assert "诊断" in snapshot["boundary_notice"]

    replay = client.post(
        "/api/training-plan/recommendations/replay",
        headers=_headers(token, "t23-replay-legacy"),
        json={"source_result_id": result_id, "strategy_version": "legacy_rule_order_v1"},
    )
    assert replay.status_code == 200
    assert replay.get_json()["data"]["already_recorded"] is True
    assert client.get(f"/api/training-plan/recommendation-snapshots/{snapshot['id']}", headers=_headers(token)).status_code == 200
    assert client.get(f"/api/training-plan/recommendation-snapshots/{snapshot['id']}", headers=_headers(other_token)).status_code == 404


def test_journey_contract_and_privacy_minimized_events_cover_recovery(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    _user_id, token = _login(client, "t23-events")
    journey = client.get("/api/journey/today", headers=_headers(token)).get_json()["data"]
    assert journey["state_contract"]["failure"]["never_render_as_empty"] is True
    assert journey["state_contract"]["weak_network_recovery"]["deduplicate_submit"] is True
    assert journey["controlled_capabilities"]["therapeutic_assessment"]["enabled"] is False

    payload = {
        "event_name": "journey_action_recovery",
        "client_event_id": "t23-event-recovery",
        "metadata": {
            "action": "start_assessment",
            "stage": "journey",
            "status": "recovered",
            "source": "today_journey",
            "recovery_mode": "manual_retry",
        },
    }
    first = client.post("/api/product-events", headers=_headers(token), json=payload)
    second = client.post("/api/product-events", headers=_headers(token), json=payload)
    assert first.status_code == 202
    assert second.status_code == 200
    assert second.get_json()["data"]["duplicate"] is True


def test_task23_schema_and_clients_include_full_contract(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    with app.app_context():
        from database import CURRENT_SCHEMA_VERSION, get_connection, list_database_columns, list_database_tables

        assert CURRENT_SCHEMA_VERSION == "2026_07_22_025"
        with get_connection() as conn:
            tables = {row["name"] for row in list_database_tables(conn)}
            columns = {row["name"] for row in list_database_columns(conn, "feedback_ledger")}
        assert {"feedback_ledger_actions", "recommendation_snapshots"} <= tables
        assert {"supersedes_id", "participant_status", "withdrawn_at"} <= columns

    shared = (PROJECT_ROOT / "shared" / "types" / "api.ts").read_text(encoding="utf-8")
    web = (PROJECT_ROOT / "apps" / "web" / "src" / "services" / "safehomeApi.ts").read_text(encoding="utf-8")
    mini = (PROJECT_ROOT / "apps" / "miniprogram" / "services" / "api.js").read_text(encoding="utf-8")
    assert "FeedbackLedgerActionInput" in shared
    assert "RecommendationSnapshot" in shared
    assert "applyFeedbackLedgerAction" in web and "replayTrainingRecommendation" in web
    assert "applyFeedbackLedgerAction" in mini and "replayTrainingRecommendation" in mini
