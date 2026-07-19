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
    response = client.post("/api/auth/wechat-login", json={"code": code, "nickname": code})
    assert response.status_code == 200
    data = response.get_json()["data"]
    return data["user"]["id"], data["token"]


def _headers(token: str, key: str | None = None) -> dict:
    headers = {"Authorization": f"Bearer {token}"}
    if key:
        headers["Idempotency-Key"] = key
    return headers


def _insert_feedback(app, user_id: str, feedback_id: str = "feedback-source-1"):
    with app.app_context():
        from database import get_connection, now_iso

        with get_connection() as conn:
            conn.execute(
                """
                INSERT INTO feedback_results (
                    id, user_id, diary_id, tags_json, supportive_feedback,
                    recommended_card_ids_json, risk_level, created_at
                ) VALUES (?, ?, NULL, '[]', '支持性反馈', '[]', 'low', ?)
                """,
                (feedback_id, user_id, now_iso()),
            )
            conn.commit()
    return feedback_id


def _payload(source_id: str, **overrides):
    payload = {
        "source_type": "instant_feedback",
        "source_id": source_id,
        "content_version": "feedback-rules-v1",
        "evaluation": "matches",
    }
    payload.update(overrides)
    return payload


def test_feedback_ledger_enforces_source_ownership(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    owner_id, owner_token = _login(client, "ledger-owner")
    _other_id, other_token = _login(client, "ledger-other")
    source_id = _insert_feedback(app, owner_id)

    created = client.post("/api/feedback-ledger", headers=_headers(owner_token), json=_payload(source_id))
    denied = client.post("/api/feedback-ledger", headers=_headers(other_token), json=_payload(source_id))

    assert created.status_code == 201
    assert created.get_json()["data"]["user_id"] == owner_id
    assert denied.status_code == 404
    assert denied.get_json()["error"]["code"] == "not_found"


def test_feedback_ledger_idempotency_replays_and_rejects_conflict(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    user_id, token = _login(client, "ledger-idempotent")
    source_id = _insert_feedback(app, user_id)

    first = client.post("/api/feedback-ledger", headers=_headers(token, "rating-1"), json=_payload(source_id))
    replay = client.post("/api/feedback-ledger", headers=_headers(token, "rating-1"), json=_payload(source_id))
    conflict = client.post(
        "/api/feedback-ledger",
        headers=_headers(token, "rating-1"),
        json=_payload(source_id, evaluation="does_not_match"),
    )

    assert first.status_code == 201
    assert replay.status_code == 200
    assert replay.get_json()["data"]["id"] == first.get_json()["data"]["id"]
    assert replay.get_json()["data"]["already_recorded"] is True
    assert conflict.status_code == 409
    assert conflict.get_json()["error"]["code"] == "idempotency_conflict"


def test_feedback_ledger_keeps_historical_versions(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    user_id, token = _login(client, "ledger-history")
    source_id = _insert_feedback(app, user_id)

    first = client.post(
        "/api/feedback-ledger",
        headers=_headers(token, "history-v1"),
        json=_payload(source_id, content_version="v1", evaluation="partly_matches"),
    )
    second = client.post(
        "/api/feedback-ledger",
        headers=_headers(token, "history-v2"),
        json=_payload(source_id, content_version="v2", evaluation="does_not_match"),
    )
    listed = client.get(
        f"/api/feedback-ledger?source_type=instant_feedback&source_id={source_id}",
        headers=_headers(token),
    )

    assert first.status_code == 201 and second.status_code == 201
    items = listed.get_json()["data"]["items"]
    assert [item["content_version"] for item in items] == ["v2", "v1"]
    assert items[0]["status"] == "active"
    assert items[1]["status"] == "superseded"


def test_uncomfortable_feedback_creates_review_signal_without_risk_inference(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    user_id, token = _login(client, "ledger-uncomfortable")
    source_id = _insert_feedback(app, user_id)

    response = client.post(
        "/api/feedback-ledger",
        headers=_headers(token, "uncomfortable-1"),
        json=_payload(source_id, evaluation="uncomfortable", reason_code="tone_or_wording"),
    )

    assert response.status_code == 201
    data = response.get_json()["data"]
    assert data["requires_human_review"] is True
    assert data["stop_reinforcement"] is True
    assert data["review_status"] == "pending_review"
    assert "risk_level" not in data


def test_uncomfortable_training_feedback_is_available_to_recommendation_ranking(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    user_id, token = _login(client, "ledger-training")
    with app.app_context():
        from database import get_connection

        with get_connection() as conn:
            card_id = conn.execute("SELECT id FROM training_cards WHERE enabled = 1 ORDER BY id LIMIT 1").fetchone()["id"]

    response = client.post(
        "/api/feedback-ledger",
        headers=_headers(token, "training-uncomfortable"),
        json={
            "source_type": "training_recommendation",
            "source_id": card_id,
            "content_version": "card-v1",
            "evaluation": "uncomfortable",
        },
    )

    assert response.status_code == 201
    with app.app_context():
        from services.training_recommendation_service import _load_card_feedback

        stats = _load_card_feedback(user_id)
    assert stats[card_id]["uncomfortable"] == 1


def test_researcher_summary_is_aggregate_and_assignment_scoped(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    participant_id, participant_token = _login(client, "ledger-participant")
    researcher_id, researcher_token = _login(client, "ledger-researcher")
    other_researcher_id, other_researcher_token = _login(client, "ledger-researcher-other")
    source_id = _insert_feedback(app, participant_id)
    client.post(
        "/api/feedback-ledger",
        headers=_headers(participant_token, "summary-1"),
        json=_payload(source_id, evaluation="uncomfortable", reason_text="这段原因不应出现在研究者摘要"),
    )

    with app.app_context():
        from database import get_connection, now_iso

        with get_connection() as conn:
            conn.execute("UPDATE users SET role = 'researcher' WHERE id IN (?, ?)", (researcher_id, other_researcher_id))
            conn.execute(
                """
                INSERT INTO relationship_pilot_enrollments (
                    id, user_id, assessment_result_id, worksheet_id, dimensions_json,
                    radar_features_json, profile_json, consent_scope, assigned_researcher_id,
                    status, review_status, created_at, updated_at
                ) VALUES ('enrollment-ledger', ?, 'assessment-ledger', 'worksheet-ledger', '[]',
                          '[]', '{}', 'feedback_review', ?, 'enrolled', 'pending_review', ?, ?)
                """,
                (participant_id, researcher_id, now_iso(), now_iso()),
            )
            conn.commit()

    allowed = client.get(f"/api/feedback-ledger/summary?user_id={participant_id}", headers=_headers(researcher_token))
    denied = client.get(f"/api/feedback-ledger/summary?user_id={participant_id}", headers=_headers(other_researcher_token))

    assert allowed.status_code == 200
    summary = allowed.get_json()["data"]
    assert summary["evaluation_counts"]["uncomfortable"] == 1
    assert summary["pending_review_count"] == 1
    assert "这段原因" not in allowed.get_data(as_text=True)
    assert denied.status_code == 403
