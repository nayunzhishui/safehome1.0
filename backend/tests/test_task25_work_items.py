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
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "safehome-task25.sqlite3"))
    monkeypatch.setenv("CONTENT_DIR", str(PROJECT_ROOT / "content"))
    app = importlib.import_module("app").app
    app.config["ADMIN_EXPORT_TOKEN"] = "task25-admin-token"
    app.config["RESEARCH_OPERATIONS_WRITE_ENABLED"] = True
    return app


def _login(client, code: str):
    response = client.post("/api/auth/wechat-login", json={"code": code, "nickname": code})
    data = response.get_json()["data"]
    return data["user"]["id"], {"Authorization": f"Bearer {data['token']}"}


def _seed_assigned_supervision(app, researcher_id: str, user_id: str):
    with app.app_context():
        from database import get_connection, now_iso

        with get_connection() as conn:
            timestamp = now_iso()
            conn.execute("UPDATE users SET role = 'researcher' WHERE id = ?", (researcher_id,))
            conn.execute(
                """
                INSERT INTO relationship_pilot_enrollments (
                    id, user_id, assessment_result_id, worksheet_id, dimensions_json,
                    radar_features_json, profile_json, consent_scope, assigned_researcher_id,
                    status, review_status, created_at, updated_at
                ) VALUES ('task25-enrollment', ?, 'task25-assessment', 'relationship_action_style_v1',
                          '[]', '[]', '{}', 'pilot', ?, 'enrolled', 'pending_review', ?, ?)
                """,
                (user_id, researcher_id, timestamp, timestamp),
            )
            conn.execute(
                """
                INSERT INTO supervision_requests (id, user_id, message, risk_level, status, created_at)
                VALUES ('task25-supervision', ?, 'PRIVATE-SUPERVISION-TEXT', 'low', 'pending', ?)
                """,
                (user_id, timestamp),
            )
            conn.commit()


def test_work_item_claim_uses_versioned_lease_and_rejects_stale_claim(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    participant_id, _participant_headers = _login(client, "task25-participant")
    researcher_id, researcher_headers = _login(client, "task25-researcher")
    _seed_assigned_supervision(app, researcher_id, participant_id)

    queue = client.get("/api/research/queues?queue=supervision", headers=researcher_headers)
    assert queue.status_code == 200
    item = queue.get_json()["data"]["items"][0]
    assert item["work_item_id"]
    assert item["version"] == 0
    assert item["assignee_id"] is None
    assert item["priority"] in {"routine", "attention", "urgent"}

    claimed = client.post(
        f"/api/research/work-items/{item['work_item_id']}/actions",
        headers={**researcher_headers, "Idempotency-Key": "task25-claim-1"},
        json={"action": "claim", "expected_version": 0},
    )
    assert claimed.status_code == 200
    claimed_item = claimed.get_json()["data"]["work_item"]
    assert claimed_item["status"] == "claimed"
    assert claimed_item["assignee_id"] == researcher_id
    assert claimed_item["lease_expires_at"]
    assert claimed_item["version"] == 1

    stale = client.post(
        f"/api/research/work-items/{item['work_item_id']}/actions",
        headers={"X-Admin-Token": "task25-admin-token", "Idempotency-Key": "task25-claim-stale"},
        json={"action": "claim", "expected_version": 0},
    )
    assert stale.status_code == 409
    assert stale.get_json()["error"]["code"] == "work_item_conflict"


def test_work_item_notes_participant_message_and_lifecycle_are_separate_from_source(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    participant_id, participant_headers = _login(client, "task25-message-participant")
    researcher_id, researcher_headers = _login(client, "task25-message-researcher")
    _seed_assigned_supervision(app, researcher_id, participant_id)
    item = client.get("/api/research/queues?queue=supervision", headers=researcher_headers).get_json()["data"]["items"][0]

    def act(headers, key, action, version, **payload):
        return client.post(
            f"/api/research/work-items/{item['work_item_id']}/actions",
            headers={**headers, "Idempotency-Key": key},
            json={"action": action, "expected_version": version, **payload},
        )

    claimed = act(researcher_headers, "lifecycle-claim", "claim", 0).get_json()["data"]["work_item"]
    noted = act(researcher_headers, "lifecycle-note", "add_note", 1, note="已核对来源，等待补充。").get_json()["data"]
    assert noted["work_item"]["version"] == 2
    sent = act(
        researcher_headers,
        "lifecycle-message",
        "send_participant_message",
        2,
        title="人工支持进度",
        body="你的请求已进入人工查看，可稍后在消息中心查看更新。",
    )
    assert sent.status_code == 200
    assert sent.get_json()["data"]["message_id"]

    messages = client.get("/api/messages", headers=participant_headers).get_json()["data"]["items"]
    assert any(message["source_id"] == item["work_item_id"] for message in messages)

    completed = act(
        researcher_headers,
        "lifecycle-complete",
        "complete",
        3,
        resolution_code="participant_updated",
        note="已向参与者说明当前进度。",
    )
    assert completed.status_code == 200
    assert completed.get_json()["data"]["work_item"]["status"] == "completed"

    closed = act(
        {"X-Admin-Token": "task25-admin-token"},
        "lifecycle-close",
        "close",
        4,
        resolution_code="handled",
        note="处置闭环。",
    )
    assert closed.status_code == 200
    assert closed.get_json()["data"]["work_item"]["status"] == "closed"

    reopened = act(
        {"X-Admin-Token": "task25-admin-token"},
        "lifecycle-reopen",
        "reopen",
        5,
        note="收到新情况，重新进入队列。",
    )
    assert reopened.status_code == 200
    assert reopened.get_json()["data"]["work_item"]["status"] == "open"

    detail = client.get(f"/api/research/work-items/{item['work_item_id']}", headers=researcher_headers)
    assert detail.status_code == 200
    data = detail.get_json()["data"]
    assert data["source"]["source_id"] == "task25-supervision"
    assert "PRIVATE-SUPERVISION-TEXT" not in detail.get_data(as_text=True)
    assert data["notes"][0]["note_type"] in {"internal", "handling"}

    with app.app_context():
        from database import get_connection

        with get_connection() as conn:
            source = conn.execute("SELECT message, status FROM supervision_requests WHERE id = 'task25-supervision'").fetchone()
            assert source["message"] == "PRIVATE-SUPERVISION-TEXT"
            assert source["status"] == "pending"


def test_notification_failures_distinguish_reauthorization_and_manual_dead_letter_recovery(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    user_id, _user_headers = _login(client, "task25-notify-user")
    researcher_id, researcher_headers = _login(client, "task25-notify-researcher")
    _seed_assigned_supervision(app, researcher_id, user_id)

    with app.app_context():
        from database import get_connection, now_iso

        with get_connection() as conn:
            timestamp = now_iso()
            conn.execute(
                """
                INSERT INTO notification_deliveries (
                    id, user_id, notification_type, template_id, schedule_key, idempotency_key,
                    status, attempt_count, scheduled_for, error_code, error_message,
                    retry_category, max_attempts, dead_lettered_at, created_at, updated_at
                ) VALUES ('notify-reauth', ?, 'training_due', 'template', 'reauth', 'notify-reauth-key',
                          'failed', 1, ?, '43101', 'PRIVATE-PROVIDER-ERROR',
                          'reauthorization_required', 3, NULL, ?, ?)
                """,
                (user_id, timestamp, timestamp, timestamp),
            )
            conn.execute(
                """
                INSERT INTO notification_deliveries (
                    id, user_id, notification_type, template_id, schedule_key, idempotency_key,
                    status, attempt_count, scheduled_for, error_code, error_message,
                    retry_category, max_attempts, dead_lettered_at, created_at, updated_at
                ) VALUES ('notify-dead', ?, 'training_due', 'template', 'dead', 'notify-dead-key',
                          'failed', 3, ?, 'wechat_service_unavailable', 'PRIVATE-PROVIDER-ERROR',
                          'retryable', 3, ?, ?, ?)
                """,
                (user_id, timestamp, timestamp, timestamp, timestamp),
            )
            conn.commit()

    queue = client.get("/api/research/queues?queue=notification_failed&page_size=20", headers=researcher_headers)
    assert queue.status_code == 200
    items = {row["source_id"]: row for row in queue.get_json()["data"]["items"]}
    assert items["notify-reauth"]["retry_category"] == "reauthorization_required"
    assert "PRIVATE-PROVIDER-ERROR" not in queue.get_data(as_text=True)

    reauth_retry = client.post(
        f"/api/research/work-items/{items['notify-reauth']['work_item_id']}/actions",
        headers={"X-Admin-Token": "task25-admin-token", "Idempotency-Key": "notify-reauth-retry"},
        json={"action": "retry_notification", "expected_version": 0},
    )
    assert reauth_retry.status_code == 409
    assert reauth_retry.get_json()["error"]["code"] == "notification_reauthorization_required"

    recovered = client.post(
        f"/api/research/work-items/{items['notify-dead']['work_item_id']}/actions",
        headers={"X-Admin-Token": "task25-admin-token", "Idempotency-Key": "notify-dead-recover"},
        json={"action": "recover_notification", "expected_version": 0, "note": "确认授权仍有效后恢复。"},
    )
    assert recovered.status_code == 200
    assert recovered.get_json()["data"]["work_item"]["status"] == "open"
    with app.app_context():
        from database import get_connection

        with get_connection() as conn:
            delivery = conn.execute(
                "SELECT attempt_count, retry_category, next_attempt_at, dead_lettered_at FROM notification_deliveries WHERE id = 'notify-dead'"
            ).fetchone()
            assert delivery["attempt_count"] == 0
            assert delivery["retry_category"] == "retryable"
            assert delivery["next_attempt_at"]
            assert delivery["dead_lettered_at"] is None


def test_operational_metrics_report_backlog_sla_and_close_reasons_without_quality_scoring(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    participant_id, _participant_headers = _login(client, "task25-metrics-participant")
    researcher_id, researcher_headers = _login(client, "task25-metrics-researcher")
    _seed_assigned_supervision(app, researcher_id, participant_id)
    item = client.get("/api/research/queues?queue=supervision", headers=researcher_headers).get_json()["data"]["items"][0]

    claim = client.post(
        f"/api/research/work-items/{item['work_item_id']}/actions",
        headers={**researcher_headers, "Idempotency-Key": "metrics-claim"},
        json={"action": "claim", "expected_version": 0},
    )
    assert claim.status_code == 200
    complete = client.post(
        f"/api/research/work-items/{item['work_item_id']}/actions",
        headers={**researcher_headers, "Idempotency-Key": "metrics-complete"},
        json={"action": "complete", "expected_version": 1, "resolution_code": "participant_updated"},
    )
    assert complete.status_code == 200
    close = client.post(
        f"/api/research/work-items/{item['work_item_id']}/actions",
        headers={"X-Admin-Token": "task25-admin-token", "Idempotency-Key": "metrics-close"},
        json={"action": "close", "expected_version": 2, "resolution_code": "handled"},
    )
    assert close.status_code == 200

    response = client.get("/api/research/work-items/metrics?window_days=7", headers=researcher_headers)
    assert response.status_code == 200
    metrics = response.get_json()["data"]
    assert metrics["scope"] == "assigned_participants"
    assert metrics["totals"]["closed"] == 1
    assert metrics["close_reasons"] == [{"resolution_code": "handled", "count": 1}]
    assert metrics["trend"]
    assert "quality_score" not in str(metrics)
    assert "不用于评价心理支持质量" in metrics["quality_boundary"]


def test_sensitive_queues_share_work_item_contract_but_keep_role_permissions(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    participant_id, _participant_headers = _login(client, "task25-sensitive-participant")
    researcher_id, researcher_headers = _login(client, "task25-sensitive-researcher")
    _seed_assigned_supervision(app, researcher_id, participant_id)
    with app.app_context():
        from database import get_connection, now_iso

        with get_connection() as conn:
            timestamp = now_iso()
            conn.execute(
                """
                INSERT INTO risk_review_records (
                    id, user_id, source_type, source_id, risk_level, review_status, created_at, updated_at
                ) VALUES ('task25-risk', ?, 'feedback', 'task25-source', 'high', 'pending', ?, ?)
                """,
                (participant_id, timestamp, timestamp),
            )
            conn.execute(
                """
                INSERT INTO privacy_requests (
                    id, user_id, request_type, reason, status, created_at, updated_at
                ) VALUES ('task25-privacy', ?, 'delete_my_data', 'PRIVATE-REASON', 'pending', ?, ?)
                """,
                (participant_id, timestamp, timestamp),
            )
            conn.commit()

    risk = client.get("/api/research/queues?queue=risk_review", headers=researcher_headers)
    assert risk.status_code == 200
    risk_item = risk.get_json()["data"]["items"][0]
    denied = client.post(
        f"/api/research/work-items/{risk_item['work_item_id']}/actions",
        headers={**researcher_headers, "Idempotency-Key": "risk-claim-denied"},
        json={"action": "claim", "expected_version": 0},
    )
    assert denied.status_code == 403
    assert client.get("/api/research/queues?queue=privacy_request", headers=researcher_headers).status_code == 403

    privacy = client.get(
        "/api/research/queues?queue=privacy_request",
        headers={"X-Admin-Token": "task25-admin-token"},
    )
    assert privacy.status_code == 200
    assert "PRIVATE-REASON" not in privacy.get_data(as_text=True)


def test_work_item_renew_return_transfer_and_wait_transitions(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    participant_id, _participant_headers = _login(client, "task25-transfer-participant")
    researcher_id, researcher_headers = _login(client, "task25-transfer-researcher")
    _seed_assigned_supervision(app, researcher_id, participant_id)
    item = client.get("/api/research/queues?queue=supervision", headers=researcher_headers).get_json()["data"]["items"][0]

    def action(headers, key, name, version, **extra):
        response = client.post(
            f"/api/research/work-items/{item['work_item_id']}/actions",
            headers={**headers, "Idempotency-Key": key},
            json={"action": name, "expected_version": version, **extra},
        )
        assert response.status_code == 200, response.get_data(as_text=True)
        return response.get_json()["data"]["work_item"]

    assert action(researcher_headers, "flow-claim", "claim", 0)["version"] == 1
    assert action(researcher_headers, "flow-renew", "renew", 1)["version"] == 2
    assert action(researcher_headers, "flow-return", "return", 2)["status"] == "open"
    assert action({"X-Admin-Token": "task25-admin-token"}, "flow-admin-claim", "claim", 3)["status"] == "claimed"
    transferred = action(
        {"X-Admin-Token": "task25-admin-token"},
        "flow-transfer",
        "transfer",
        4,
        assignee_id=researcher_id,
    )
    assert transferred["assignee_id"] == researcher_id
    assert action(researcher_headers, "flow-processing", "start_processing", 5)["status"] == "processing"
    assert action(researcher_headers, "flow-wait", "wait", 6)["status"] == "waiting"


def test_source_resolution_reconciles_work_item_without_editing_source_content(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    participant_id, _participant_headers = _login(client, "task25-reconcile-participant")
    researcher_id, researcher_headers = _login(client, "task25-reconcile-researcher")
    _seed_assigned_supervision(app, researcher_id, participant_id)
    item = client.get("/api/research/queues?queue=supervision", headers=researcher_headers).get_json()["data"]["items"][0]
    with app.app_context():
        from database import get_connection

        with get_connection() as conn:
            conn.execute("UPDATE supervision_requests SET status = 'replied' WHERE id = 'task25-supervision'")
            conn.commit()

    metrics = client.get("/api/research/work-items/metrics", headers=researcher_headers)
    assert metrics.status_code == 200
    detail = client.get(f"/api/research/work-items/{item['work_item_id']}", headers=researcher_headers)
    data = detail.get_json()["data"]
    assert data["work_item"]["status"] == "completed"
    assert data["work_item"]["resolution_code"] == "source_resolved"
    assert data["actions"][-1]["actor_role"] == "system"
    assert "PRIVATE-SUPERVISION-TEXT" not in detail.get_data(as_text=True)


def test_operations_write_switch_keeps_queue_readable_and_blocks_actions(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    participant_id, _participant_headers = _login(client, "task25-switch-participant")
    researcher_id, researcher_headers = _login(client, "task25-switch-researcher")
    _seed_assigned_supervision(app, researcher_id, participant_id)
    app.config["RESEARCH_OPERATIONS_WRITE_ENABLED"] = False

    queue = client.get("/api/research/queues?queue=supervision", headers=researcher_headers)
    assert queue.status_code == 200
    item = queue.get_json()["data"]["items"][0]
    blocked = client.post(
        f"/api/research/work-items/{item['work_item_id']}/actions",
        headers={**researcher_headers, "Idempotency-Key": "switch-blocked"},
        json={"action": "claim", "expected_version": 0},
    )
    assert blocked.status_code == 503
    assert blocked.get_json()["error"]["code"] == "operations_write_disabled"
