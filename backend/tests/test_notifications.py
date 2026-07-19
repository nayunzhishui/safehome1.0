import importlib
import os
import sys
from datetime import date
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = PROJECT_ROOT / "backend"


def _fresh_app(tmp_path):
    sys.path.insert(0, str(BACKEND_ROOT))
    for name in list(sys.modules):
        if name in {"app", "config", "database", "models"} or name.startswith("routes.") or name.startswith("services."):
            sys.modules.pop(name, None)
    os.environ["DATABASE_PATH"] = str(tmp_path / "safehome-notification-test.sqlite3")
    os.environ["CONTENT_DIR"] = str(PROJECT_ROOT / "content")
    os.environ.pop("WECHAT_TRAINING_DUE_TEMPLATE_ID", None)
    os.environ.pop("WECHAT_SUBSCRIBE_SEND_ENABLED", None)
    app = importlib.import_module("app").app
    app.config.update(
        WECHAT_TRAINING_DUE_TEMPLATE_ID="tmpl_training_due",
        WECHAT_TRAINING_DUE_TEMPLATE_FIELDS='{"thing1":"title","date2":"time","thing3":"note"}',
        WECHAT_SUBSCRIBE_MODE="once",
        WECHAT_SUBSCRIBE_SEND_ENABLED=False,
        NOTIFICATION_SCHEDULER_TOKEN="scheduler-test-token",
    )
    return app


def _login(client, code):
    response = client.post("/api/auth/wechat-login", json={"code": code, "nickname": code})
    assert response.status_code == 200
    data = response.get_json()["data"]
    return data["user"]["id"], {"Authorization": f"Bearer {data['token']}"}


def _save_due_assignment(client, headers):
    response = client.post(
        "/api/training-plan/assignment",
        headers=headers,
        json={
            "phase": "start",
            "cadence": "daily",
            "status": "active",
            "start_date": date.today().isoformat(),
            "goal_text": "先完成一次小练习",
        },
    )
    assert response.status_code == 200


def _consent(client, headers, decision="accept", template_id="tmpl_training_due"):
    return client.post(
        "/api/notifications/consent",
        headers=headers,
        json={"template_id": template_id, "decision": decision},
    )


def test_subscription_config_and_consent_are_private_and_validated(tmp_path):
    app = _fresh_app(tmp_path)
    client = app.test_client()
    _user_id, headers = _login(client, "notification-owner")

    assert client.get("/api/notifications/config").status_code == 401
    config = client.get("/api/notifications/config", headers=headers).get_json()["data"]
    assert config["available"] is True
    assert config["send_enabled"] is False
    assert config["preference"] is None

    mismatch = _consent(client, headers, template_id="wrong-template")
    assert mismatch.status_code == 400
    assert mismatch.get_json()["error"]["code"] == "subscription_template_mismatch"

    rejected = _consent(client, headers, "reject")
    assert rejected.status_code == 200
    assert rejected.get_json()["data"]["preference"]["consent_status"] == "rejected"


def test_rejected_or_missing_openid_is_not_scheduled(tmp_path):
    app = _fresh_app(tmp_path)
    client = app.test_client()
    user_id, headers = _login(client, "notification-rejected")
    _save_due_assignment(client, headers)
    _consent(client, headers, "reject")

    dry_run = client.post(
        "/api/notifications/run-due",
        headers={"X-Scheduler-Token": "scheduler-test-token"},
        json={"dry_run": True},
    )
    assert dry_run.status_code == 200
    assert dry_run.get_json()["data"]["candidate_count"] == 0

    _consent(client, headers, "accept")
    database = importlib.import_module("database")
    with database.get_connection() as conn:
        conn.execute("UPDATE users SET wechat_openid = NULL WHERE id = ?", (user_id,))
        conn.commit()
    dry_run = client.post(
        "/api/notifications/run-due",
        headers={"X-Scheduler-Token": "scheduler-test-token"},
        json={"dry_run": True},
    )
    assert dry_run.get_json()["data"]["candidate_count"] == 0


def test_once_subscription_is_consumed_and_duplicate_send_is_blocked(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path)
    client = app.test_client()
    _user_id, headers = _login(client, "notification-send")
    _save_due_assignment(client, headers)
    assert _consent(client, headers, "accept").status_code == 200

    unauthorized = client.post("/api/notifications/run-due", json={"dry_run": True})
    assert unauthorized.status_code == 401
    dry_run = client.post(
        "/api/notifications/run-due",
        headers={"X-Scheduler-Token": "scheduler-test-token"},
        json={"dry_run": True},
    ).get_json()["data"]
    assert dry_run["candidate_count"] == 1

    disabled = client.post(
        "/api/notifications/run-due",
        headers={"X-Scheduler-Token": "scheduler-test-token"},
        json={"dry_run": False},
    )
    assert disabled.status_code == 503

    app.config["WECHAT_SUBSCRIBE_SEND_ENABLED"] = True
    service = importlib.import_module("services.notification_service")
    send_calls = []

    def fake_send(candidate):
        send_calls.append(candidate["idempotency_key"])
        return {"errcode": 0, "msgid": "provider-message-1"}

    monkeypatch.setattr(service, "send_wechat_subscription", fake_send)
    sent = client.post(
        "/api/notifications/run-due",
        headers={"X-Scheduler-Token": "scheduler-test-token"},
        json={"dry_run": False},
    ).get_json()["data"]
    assert sent["sent"] == 1
    assert len(send_calls) == 1
    preference = client.get("/api/notifications/config", headers=headers).get_json()["data"]["preference"]
    assert preference["consent_status"] == "consumed"

    # A user may authorize again on the same day; the delivery key still prevents a duplicate send.
    _consent(client, headers, "accept")
    repeated = client.post(
        "/api/notifications/run-due",
        headers={"X-Scheduler-Token": "scheduler-test-token"},
        json={"dry_run": False},
    ).get_json()["data"]
    assert repeated["skipped_duplicate"] == 1
    assert len(send_calls) == 1


def test_transient_provider_failure_retries_without_consuming_consent(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path)
    client = app.test_client()
    user_id, headers = _login(client, "notification-retry")
    _save_due_assignment(client, headers)
    _consent(client, headers, "accept")
    app.config["WECHAT_SUBSCRIBE_SEND_ENABLED"] = True
    service = importlib.import_module("services.notification_service")
    attempts = []

    def flaky_send(candidate):
        attempts.append(candidate["idempotency_key"])
        if len(attempts) == 1:
            raise service.NotificationError("wechat_service_unavailable", "temporary", 502)
        return {"errcode": 0, "msgid": "provider-message-retry"}

    monkeypatch.setattr(service, "send_wechat_subscription", flaky_send)
    first = client.post(
        "/api/notifications/run-due",
        headers={"X-Scheduler-Token": "scheduler-test-token"},
        json={"dry_run": False},
    ).get_json()["data"]
    assert first["failed"] == 1
    assert client.get("/api/notifications/config", headers=headers).get_json()["data"]["preference"]["consent_status"] == "accepted"

    second = client.post(
        "/api/notifications/run-due",
        headers={"X-Scheduler-Token": "scheduler-test-token"},
        json={"dry_run": False},
    ).get_json()["data"]
    assert second["sent"] == 0
    assert second["deferred"] == 1
    assert len(attempts) == 1
    database = importlib.import_module("database")
    with database.get_connection() as conn:
        conn.execute(
            "UPDATE notification_deliveries SET next_attempt_at = '2000-01-01T00:00:00+00:00' WHERE user_id = ?",
            (user_id,),
        )
        conn.commit()
    third = client.post(
        "/api/notifications/run-due",
        headers={"X-Scheduler-Token": "scheduler-test-token"},
        json={"dry_run": False},
    ).get_json()["data"]
    assert third["sent"] == 1
    assert len(attempts) == 2
    with database.get_connection() as conn:
        delivery = conn.execute(
            "SELECT status, attempt_count, next_attempt_at, retry_category FROM notification_deliveries WHERE user_id = ?",
            (user_id,),
        ).fetchone()
    assert delivery["status"] == "sent"
    assert delivery["attempt_count"] == 2
