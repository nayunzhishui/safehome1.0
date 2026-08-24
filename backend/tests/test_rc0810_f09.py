import importlib
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier

import pytest


ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"


def _load_idempotency_service():
    sys.path.insert(0, str(BACKEND))
    sys.modules.pop("services.idempotency_service", None)
    return importlib.import_module("services.idempotency_service")


def test_parent_web_retry_persists_one_started_and_completed_time_with_submission_key():
    page = (ROOT / "apps/web/src/pages/ReadFeedbackIntegrationPages.tsx").read_text(encoding="utf-8")
    hook = (ROOT / "apps/web/src/hooks/useResilientDraft.ts").read_text(encoding="utf-8")

    assert "function flush(nextValue: T = value)" in hook
    assert "setStartedAt(saved.startedAt || new Date().toISOString())" in page
    assert "setCompletedAt(saved.completedAt || null)" in page
    assert "const submissionCompletedAt = completedAt || new Date().toISOString()" in page
    assert "completedAt: submissionCompletedAt" in page
    assert "completed_at: submissionCompletedAt" in page


def _fresh_app(tmp_path, monkeypatch):
    sys.path.insert(0, str(BACKEND))
    for name in list(sys.modules):
        if name in {"app", "config", "database", "models"} or name.startswith(
            ("routes.", "services.")
        ):
            sys.modules.pop(name, None)
    monkeypatch.setenv("APP_ENV", "validation")
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "rc0810-f09.sqlite3"))
    monkeypatch.setenv("CONTENT_DIR", str(ROOT / "content"))
    monkeypatch.setenv("DB_PROVIDER", "sqlite")
    monkeypatch.setenv("DATABASE_DATA_WATERMARK", "synthetic_validation_only")
    monkeypatch.setenv("SECRET_KEY", "rc0810-f09-test-secret-key-that-is-long-enough")
    monkeypatch.setenv("ADMIN_EXPORT_TOKEN", "rc0810-f09-admin-token")
    app = importlib.import_module("app").app
    app.config["APP_ENV"] = "production"
    return app


def _register(client, username="parent-f09"):
    response = client.post(
        "/api/auth/register",
        json={"username": username, "password": "password123", "role": "parent"},
    )
    assert response.status_code == 201
    data = response.get_json()["data"]
    return data["user"]["id"], {"Authorization": f"Bearer {data['token']}"}


def _assessment_payload(client):
    listing = client.get("/api/assessments").get_json()["data"]["items"]
    for candidate in listing:
        worksheet = client.get(f"/api/assessments/{candidate['id']}").get_json()["data"]
        questions = worksheet.get("questions") or []
        if questions and all(question.get("options") for question in questions):
            answers = [
                {"question_id": question["id"], "value": question["options"][0]["value"]}
                for question in questions
            ]
            return {"worksheet_id": worksheet["id"], "answers": answers}, worksheet
    raise AssertionError("No option-based assessment worksheet is available")


def test_canonical_request_hash_binds_actor_endpoint_version_and_normalizes_payload():
    service = _load_idempotency_service()
    first = service.canonical_request_hash(
        actor_id="parent-f09",
        endpoint="POST /api/diaries",
        version="v1",
        payload={
            "scene": "home",
            "event_time": "2026-08-24T08:00:00+08:00",
            "optional": None,
            "nested": {"b": 2, "a": 1},
            "client_submission_id": "body-key",
            "nickname": "ignored display name",
        },
    )
    reordered = service.canonical_request_hash(
        actor_id="parent-f09",
        endpoint="POST /api/diaries",
        version="v1",
        payload={
            "nested": {"a": 1, "b": 2},
            "optional": None,
            "event_time": "2026-08-24T00:00:00Z",
            "scene": "home",
        },
    )

    assert first == reordered
    assert first != service.canonical_request_hash(
        actor_id="other-parent",
        endpoint="POST /api/diaries",
        version="v1",
        payload={
            "scene": "home",
            "event_time": "2026-08-24T00:00:00Z",
            "optional": None,
            "nested": {"a": 1, "b": 2},
        },
    )
    assert first != service.canonical_request_hash(
        actor_id="parent-f09",
        endpoint="POST /api/checkins",
        version="v1",
        payload={
            "scene": "home",
            "event_time": "2026-08-24T00:00:00Z",
            "optional": None,
            "nested": {"a": 1, "b": 2},
        },
    )


def test_canonical_request_hash_rejects_oversized_body():
    service = _load_idempotency_service()

    with pytest.raises(service.IdempotencyValidationError) as exc_info:
        service.canonical_request_hash(
            actor_id="parent-f09",
            endpoint="POST /api/diaries",
            version="v1",
            payload={"raw_text": "x" * (service.MAX_CANONICAL_BODY_BYTES + 1)},
        )

    assert exc_info.value.code == "idempotency_payload_too_large"


def test_database_claim_replays_winner_and_rejects_different_hash(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    with app.app_context():
        from database import get_connection
        from services.idempotency_service import (
            IdempotencyConflictError,
            reserve_idempotency,
        )

        with get_connection() as conn:
            first = reserve_idempotency(
                conn,
                actor_id="parent-f09",
                endpoint="POST /api/goals",
                idempotency_key="same-key",
                request_hash="a" * 64,
                resource_type="goal",
                resource_id="goal-winner",
            )
            conn.commit()
        with get_connection() as conn:
            replay = reserve_idempotency(
                conn,
                actor_id="parent-f09",
                endpoint="POST /api/goals",
                idempotency_key="same-key",
                request_hash="a" * 64,
                resource_type="goal",
                resource_id="goal-loser",
            )
            with pytest.raises(IdempotencyConflictError):
                reserve_idempotency(
                    conn,
                    actor_id="parent-f09",
                    endpoint="POST /api/goals",
                    idempotency_key="same-key",
                    request_hash="b" * 64,
                    resource_type="goal",
                    resource_id="goal-conflict",
                )
            count = conn.execute(
                "SELECT COUNT(*) AS count FROM core_idempotency_records"
            ).fetchone()["count"]

    assert first.created is True
    assert replay.created is False
    assert replay.resource_id == "goal-winner"
    assert count == 1


def test_concurrent_database_claim_has_one_winner_and_no_500_window(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    gate = Barrier(2)

    def claim(resource_id):
        with app.app_context():
            from database import get_connection
            from services.idempotency_service import reserve_idempotency

            with get_connection() as conn:
                conn.execute("PRAGMA busy_timeout = 5000")
                gate.wait(timeout=5)
                result = reserve_idempotency(
                    conn,
                    actor_id="parent-concurrent-f09",
                    endpoint="POST /api/goals",
                    idempotency_key="concurrent-key",
                    request_hash="c" * 64,
                    resource_type="goal",
                    resource_id=resource_id,
                )
                conn.commit()
                return result

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(claim, ("goal-one", "goal-two")))

    assert sorted(result.created for result in results) == [False, True]
    assert len({result.resource_id for result in results}) == 1


def test_side_effect_ledger_records_each_effect_once(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    with app.app_context():
        from database import get_connection
        from services.idempotency_service import record_side_effect, reserve_idempotency

        with get_connection() as conn:
            claim = reserve_idempotency(
                conn,
                actor_id="parent-effects-f09",
                endpoint="POST /api/checkins",
                idempotency_key="effect-key",
                request_hash="d" * 64,
                resource_type="checkin",
                resource_id="checkin-f09",
            )
            assert record_side_effect(
                conn,
                idempotency_record_id=claim.id,
                effect_type="audit",
                effect_key="checkin-created",
                status="committed",
            ) is True
            assert record_side_effect(
                conn,
                idempotency_record_id=claim.id,
                effect_type="audit",
                effect_key="checkin-created",
                status="committed",
            ) is False
            count = conn.execute(
                "SELECT COUNT(*) AS count FROM core_side_effect_ledger"
            ).fetchone()["count"]

    assert count == 1


@pytest.mark.parametrize(
    ("endpoint", "payload", "changed_field"),
    (
        (
            "/api/goals",
            {"scene": "home", "smart_goal": "pause before responding"},
            ("smart_goal", "use a different goal"),
        ),
        (
            "/api/diaries",
            {
                "scene": "home",
                "event_description": "homework disagreement",
                "parent_emotion": "worried",
                "parent_emotion_intensity": 6,
            },
            ("event_description", "a different event"),
        ),
        (
            "/api/checkins",
            {"card_id": "pause_and_breathe", "completed": True},
            ("completed", False),
        ),
    ),
)
def test_core_write_routes_replay_same_request_and_conflict_on_changed_payload(
    tmp_path, monkeypatch, endpoint, payload, changed_field
):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    _, headers = _register(client, f"route-{endpoint.rsplit('/', 1)[-1]}-f09")
    headers = {**headers, "Idempotency-Key": "route-key-f09"}

    first = client.post(endpoint, headers=headers, json=payload)
    replay = client.post(endpoint, headers=headers, json=dict(reversed(list(payload.items()))))
    changed = {**payload, changed_field[0]: changed_field[1]}
    conflict = client.post(endpoint, headers=headers, json=changed)

    assert first.status_code == 201, first.get_json()
    assert replay.status_code == 200, replay.get_json()
    assert "request_hash" not in first.get_json()["data"]
    assert "request_hash" not in replay.get_json()["data"]
    assert replay.get_json()["data"]["id"] == first.get_json()["data"]["id"]
    assert replay.get_json()["data"]["idempotency_replayed"] is True
    assert conflict.status_code == 409
    assert conflict.get_json()["error"]["code"] == "idempotency_conflict"


def test_checkin_replay_does_not_duplicate_audit_side_effect(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    user_id, headers = _register(client, "checkin-effects-route-f09")
    headers = {**headers, "Idempotency-Key": "checkin-effects-key"}
    payload = {"card_id": "pause_and_breathe", "completed": True}

    assert client.post("/api/checkins", headers=headers, json=payload).status_code == 201
    assert client.post("/api/checkins", headers=headers, json=payload).status_code == 200

    with app.app_context():
        from database import get_connection

        with get_connection() as conn:
            audit_count = conn.execute(
                """
                SELECT COUNT(*) AS count FROM audit_logs
                WHERE actor_id = ? AND action = 'product_event_journey_action_completed'
                """,
                (user_id,),
            ).fetchone()["count"]
            effect_count = conn.execute(
                """
                SELECT COUNT(*) AS count FROM core_side_effect_ledger
                WHERE effect_type = 'audit'
                """
            ).fetchone()["count"]

    assert audit_count == 1
    assert effect_count == 1


def test_supervision_replay_keeps_primary_events_risk_and_audit_exactly_once(
    tmp_path, monkeypatch
):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    user_id, headers = _register(client, "supervision-effects-f09")
    headers = {**headers, "Idempotency-Key": "supervision-effects-key"}
    payload = {
        "message": "我想自杀",
        "risk_hint": "需要尽快支持",
        "source_title": "支持入口",
    }

    first = client.post("/api/supervision", headers=headers, json=payload)
    replay = client.post("/api/supervision", headers=headers, json=payload)
    conflict = client.post(
        "/api/supervision",
        headers=headers,
        json={**payload, "message": "另一份支持请求"},
    )
    title_conflict = client.post(
        "/api/supervision",
        headers=headers,
        json={**payload, "source_title": "另一入口"},
    )

    assert first.status_code == 201, first.get_json()
    assert replay.status_code == 200, replay.get_json()
    assert replay.get_json()["data"]["id"] == first.get_json()["data"]["id"]
    assert conflict.status_code == 409
    assert title_conflict.status_code == 409

    request_id = first.get_json()["data"]["id"]
    with app.app_context():
        from database import get_connection

        with get_connection() as conn:
            counts = {
                "requests": conn.execute(
                    "SELECT COUNT(*) AS count FROM supervision_requests WHERE id = ?",
                    (request_id,),
                ).fetchone()["count"],
                "events": conn.execute(
                    "SELECT COUNT(*) AS count FROM supervision_request_events WHERE request_id = ?",
                    (request_id,),
                ).fetchone()["count"],
                "risk": conn.execute(
                    "SELECT COUNT(*) AS count FROM risk_review_records WHERE source_type = 'supervision' AND source_id = ?",
                    (request_id,),
                ).fetchone()["count"],
                "audit": conn.execute(
                    "SELECT COUNT(*) AS count FROM audit_logs WHERE actor_id = ? AND action = 'supervision_requested'",
                    (user_id,),
                ).fetchone()["count"],
                "ledger": conn.execute(
                    "SELECT COUNT(*) AS count FROM core_side_effect_ledger WHERE idempotency_record_id = (SELECT id FROM core_idempotency_records WHERE resource_id = ?)",
                    (request_id,),
                ).fetchone()["count"],
            }

    assert counts == {"requests": 1, "events": 1, "risk": 1, "audit": 1, "ledger": 3}

    low = client.post(
        "/api/supervision",
        headers={**headers, "Idempotency-Key": "supervision-low-risk-key"},
        json={"message": "我想聊聊最近的压力"},
    )
    assert low.status_code == 201, low.get_json()
    with app.app_context():
        from database import get_connection

        with get_connection() as conn:
            low_statuses = {
                row["effect_type"]: row["status"]
                for row in conn.execute(
                    """
                    SELECT effect_type, status FROM core_side_effect_ledger
                    WHERE idempotency_record_id = (
                        SELECT id FROM core_idempotency_records WHERE resource_id = ?
                    )
                    """,
                    (low.get_json()["data"]["id"],),
                ).fetchall()
            }
    assert low_statuses["database_event"] == "committed"
    assert low_statuses["risk_task"] == "not_required"


def test_assessment_replays_original_result_and_records_derived_effects_once(
    tmp_path, monkeypatch
):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    _, headers = _register(client, "assessment-effects-f09")
    payload, worksheet = _assessment_payload(client)
    headers = {**headers, "Idempotency-Key": "assessment-effects-key"}

    first = client.post("/api/assessment-results", headers=headers, json=payload)
    replay = client.post("/api/assessment-results", headers=headers, json=payload)
    changed_answers = list(payload["answers"])
    first_question = worksheet["questions"][0]
    changed_answers[0] = {
        "question_id": first_question["id"],
        "value": first_question["options"][-1]["value"],
    }
    conflict = client.post(
        "/api/assessment-results",
        headers=headers,
        json={**payload, "answers": changed_answers},
    )

    assert first.status_code == 201, first.get_json()
    assert replay.status_code == 200, replay.get_json()
    first_data = first.get_json()["data"]
    replay_data = replay.get_json()["data"]
    assert replay_data["id"] == first_data["id"]
    assert replay_data["recommended_card_ids"] == first_data["recommended_card_ids"]
    assert replay_data["scores"] == first_data["scores"]
    assert replay_data["idempotency_replayed"] is True
    assert conflict.status_code == 409

    result_list = client.get("/api/assessment-results", headers=headers)
    result_detail = client.get(
        f"/api/assessment-results/{first_data['id']}",
        headers=headers,
    )
    assert result_list.status_code == 200
    assert result_detail.status_code == 200
    assert "request_hash" not in result_list.get_json()["data"]["items"][0]
    assert "request_hash" not in result_detail.get_json()["data"]

    with app.app_context():
        from database import get_connection

        with get_connection() as conn:
            primary_count = conn.execute(
                "SELECT COUNT(*) AS count FROM assessment_results WHERE id = ?",
                (first_data["id"],),
            ).fetchone()["count"]
            effect_rows = conn.execute(
                """
                SELECT effect_type, effect_key, status FROM core_side_effect_ledger
                WHERE idempotency_record_id = (
                    SELECT id FROM core_idempotency_records WHERE resource_id = ?
                ) ORDER BY effect_type, effect_key
                """,
                (first_data["id"],),
            ).fetchall()

    assert primary_count == 1
    assert {row["effect_type"] for row in effect_rows} == {
        "profile_position",
        "recommendation",
        "risk_task",
    }


def test_parent_assessment_replay_does_not_duplicate_consent_record_or_risk_effects(
    tmp_path, monkeypatch
):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    user_id, headers = _register(client, "parent-assessment-effects-f09")
    form = client.get("/api/parent-assessment").get_json()["data"]
    answers = {
        item["item_code"]: "3"
        for scale in form["scales"]["scales"]
        for item in scale["items"]
    }
    payload = {
        "answers": answers,
        "research_consent": True,
        "participant_code": "pilot-f09",
    }
    headers = {**headers, "Idempotency-Key": "parent-assessment-effects-key"}

    first = client.post("/api/parent-assessments", headers=headers, json=payload)
    replay = client.post("/api/parent-assessments", headers=headers, json=payload)
    conflict = client.post(
        "/api/parent-assessments",
        headers=headers,
        json={**payload, "participant_code": "changed-code"},
    )
    risk_conflict = client.post(
        "/api/parent-assessments",
        headers=headers,
        json={**payload, "free_text": "我想自杀"},
    )
    completed_at_conflict = client.post(
        "/api/parent-assessments",
        headers=headers,
        json={**payload, "completed_at": "2026-08-24T10:00:00+08:00"},
    )

    assert first.status_code == 201, first.get_json()
    assert replay.status_code == 200, replay.get_json()
    first_data = first.get_json()["data"]
    replay_data = replay.get_json()["data"]
    assert replay_data["id"] == first_data["id"]
    assert replay_data["report"] == first_data["report"]
    assert replay_data["idempotency_replayed"] is True
    assert conflict.status_code == 409
    assert risk_conflict.status_code == 409
    assert completed_at_conflict.status_code == 409

    with app.app_context():
        from database import get_connection

        with get_connection() as conn:
            counts = {
                "primary": conn.execute(
                    "SELECT COUNT(*) AS count FROM parent_assessment_submissions WHERE id = ?",
                    (first_data["id"],),
                ).fetchone()["count"],
                "records": conn.execute(
                    "SELECT COUNT(*) AS count FROM records WHERE module_type = 'parent_assessment' AND source_id = ?",
                    (first_data["id"],),
                ).fetchone()["count"],
                "consent": conn.execute(
                    "SELECT COUNT(*) AS count FROM consent_records WHERE user_id = ? AND consent_type = 'research_authorization'",
                    (user_id,),
                ).fetchone()["count"],
                "ledger": conn.execute(
                    "SELECT COUNT(*) AS count FROM core_side_effect_ledger WHERE idempotency_record_id = (SELECT id FROM core_idempotency_records WHERE resource_id = ?)",
                    (first_data["id"],),
                ).fetchone()["count"],
            }

    assert counts == {"primary": 1, "records": 1, "consent": 1, "ledger": 3}


def test_concurrent_goal_requests_return_one_create_and_one_replay(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    _, headers = _register(client, "goal-api-concurrent-f09")
    headers = {**headers, "Idempotency-Key": "goal-api-concurrent-key"}
    payload = {"scene": "home", "smart_goal": "pause before responding"}

    from routes import goals as goals_route

    original_hash = goals_route.canonical_request_hash
    gate = Barrier(2)

    def synchronized_hash(*args, **kwargs):
        gate.wait(timeout=5)
        return original_hash(*args, **kwargs)

    monkeypatch.setattr(goals_route, "canonical_request_hash", synchronized_hash)

    def submit(_index):
        with app.test_client() as thread_client:
            response = thread_client.post("/api/goals", headers=headers, json=payload)
            return response.status_code, response.get_json()

    with ThreadPoolExecutor(max_workers=2) as executor:
        responses = list(executor.map(submit, (1, 2)))

    assert sorted(status for status, _body in responses) == [200, 201]
    assert len({body["data"]["id"] for _status, body in responses}) == 1


def test_failed_checkin_transaction_rolls_back_claim_and_retries_cleanly(
    tmp_path, monkeypatch
):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    _, headers = _register(client, "checkin-rollback-f09")
    headers = {**headers, "Idempotency-Key": "checkin-rollback-key"}
    payload = {"card_id": "pause_and_breathe", "completed": True}

    from routes import checkins as checkins_route

    original_audit = checkins_route.write_audit_log

    def fail_audit(*_args, **_kwargs):
        raise RuntimeError("synthetic audit failure")

    monkeypatch.setattr(checkins_route, "write_audit_log", fail_audit)
    failed = client.post("/api/checkins", headers=headers, json=payload)
    monkeypatch.setattr(checkins_route, "write_audit_log", original_audit)

    assert failed.status_code == 500
    with app.app_context():
        from database import get_connection

        with get_connection() as conn:
            assert conn.execute("SELECT COUNT(*) AS count FROM checkins").fetchone()["count"] == 0
            assert conn.execute("SELECT COUNT(*) AS count FROM core_idempotency_records").fetchone()["count"] == 0
            assert conn.execute("SELECT COUNT(*) AS count FROM core_side_effect_ledger").fetchone()["count"] == 0

    retry = client.post("/api/checkins", headers=headers, json=payload)
    assert retry.status_code == 201, retry.get_json()


def test_legacy_client_without_key_keeps_non_idempotent_create_behavior(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    _, headers = _register(client, "legacy-no-key-f09")
    payload = {"scene": "home", "smart_goal": "pause before responding"}

    first = client.post("/api/goals", headers=headers, json=payload)
    second = client.post("/api/goals", headers=headers, json=payload)

    assert first.status_code == second.status_code == 201
    assert first.get_json()["data"]["id"] != second.get_json()["data"]["id"]
    with app.app_context():
        from database import get_connection

        with get_connection() as conn:
            assert conn.execute("SELECT COUNT(*) AS count FROM goals").fetchone()["count"] == 2
            assert conn.execute("SELECT COUNT(*) AS count FROM core_idempotency_records").fetchone()["count"] == 0


def test_historical_submission_key_backfill_replays_original_resource(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    user_id, headers = _register(client, "legacy-backfill-f09")
    with app.app_context():
        from database import get_connection, now_iso
        from services.schema_migration_service import apply_pending_schema_migrations

        with get_connection() as conn:
            timestamp = now_iso()
            conn.execute(
                """
                INSERT INTO goals (
                    id, user_id, scene, smart_goal, motivation, start_date, status,
                    client_submission_id, request_hash, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, NULL, ?, ?)
                """,
                (
                    "goal-legacy-f09",
                    user_id,
                    "home",
                    "pause before responding",
                    None,
                    None,
                    "active",
                    "legacy-backfill-key",
                    timestamp,
                    timestamp,
                ),
            )
            conn.execute(
                "DELETE FROM core_idempotency_records WHERE resource_id = 'goal-legacy-f09'"
            )
            conn.execute(
                "DELETE FROM explicit_schema_migrations WHERE version = '2026_08_24_065'"
            )
            conn.commit()
        with get_connection() as conn:
            assert apply_pending_schema_migrations(conn) == ["2026_08_24_065"]
            conn.commit()

    response = client.post(
        "/api/goals",
        headers={**headers, "Idempotency-Key": "legacy-backfill-key"},
        json={"scene": "home", "smart_goal": "pause before responding"},
    )
    assert response.status_code == 200, response.get_json()
    assert response.get_json()["data"]["id"] == "goal-legacy-f09"


def test_mysql_duplicate_key_is_reread_as_replay_not_raised():
    service = _load_idempotency_service()
    mysql_integrity_error = type("IntegrityError", (Exception,), {})
    existing = {
        "id": "idem-mysql-f09",
        "actor_id": "parent-mysql-f09",
        "endpoint": "POST /api/goals",
        "idempotency_key": "mysql-key",
        "request_hash": "e" * 64,
        "resource_type": "goal",
        "resource_id": "goal-mysql-f09",
        "response_status": None,
        "response_json": None,
    }

    class Cursor:
        def fetchone(self):
            return existing

    class Connection:
        def execute(self, sql, _params=None):
            if "INSERT INTO core_idempotency_records" in sql:
                raise mysql_integrity_error(1062, "Duplicate entry")
            return Cursor()

    replay = service.reserve_idempotency(
        Connection(),
        actor_id="parent-mysql-f09",
        endpoint="POST /api/goals",
        idempotency_key="mysql-key",
        request_hash="e" * 64,
        resource_type="goal",
        resource_id="goal-loser",
    )

    assert replay.created is False
    assert replay.resource_id == "goal-mysql-f09"


def test_external_side_effect_cannot_escape_compensation_states_after_provider_commit(
    tmp_path, monkeypatch
):
    app = _fresh_app(tmp_path, monkeypatch)
    with app.app_context():
        from database import get_connection
        from services.idempotency_service import (
            IdempotencyValidationError,
            record_side_effect,
            reserve_idempotency,
            update_side_effect_status,
        )

        with get_connection() as conn:
            claim = reserve_idempotency(
                conn,
                actor_id="system-f09",
                endpoint="POST /internal/wechat-delivery",
                idempotency_key="wechat-delivery-key",
                request_hash="f" * 64,
                resource_type="notification_delivery",
                resource_id="delivery-f09",
            )
            assert record_side_effect(
                conn,
                idempotency_record_id=claim.id,
                effect_type="wechat_subscription",
                effect_key="delivery-f09",
                status="pending",
            )
            update_side_effect_status(
                conn,
                idempotency_record_id=claim.id,
                effect_type="wechat_subscription",
                effect_key="delivery-f09",
                status="externally_committed",
                external_reference="provider-message-f09",
            )
            update_side_effect_status(
                conn,
                idempotency_record_id=claim.id,
                effect_type="wechat_subscription",
                effect_key="delivery-f09",
                status="compensation_required",
            )
            with pytest.raises(IdempotencyValidationError):
                update_side_effect_status(
                    conn,
                    idempotency_record_id=claim.id,
                    effect_type="wechat_subscription",
                    effect_key="delivery-f09",
                    status="cancelled",
                )
            row = conn.execute(
                "SELECT * FROM core_side_effect_ledger WHERE idempotency_record_id = ?",
                (claim.id,),
            ).fetchone()

    assert row["status"] == "compensation_required"
    assert row["external_reference"] == "provider-message-f09"


def test_f09_schema_has_three_recoverable_migrations_and_all_six_request_hashes(
    tmp_path, monkeypatch
):
    app = _fresh_app(tmp_path, monkeypatch)
    with app.app_context():
        from database import get_connection
        from services.schema_migration_service import (
            apply_pending_schema_migrations,
            migration_manifest,
        )

        manifest = migration_manifest()
        f09_migrations = [
            item for item in manifest if item["version"].startswith("2026_08_24_06")
        ]
        assert [item["version"] for item in f09_migrations] == [
            "2026_08_24_064",
            "2026_08_24_065",
            "2026_08_24_066",
        ]
        assert all(item["rollback_notes"] for item in f09_migrations)

        with get_connection() as conn:
            for table in (
                "goals",
                "emotion_diaries",
                "checkins",
                "supervision_requests",
                "assessment_results",
                "parent_assessment_submissions",
            ):
                columns = {
                    row["name"] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()
                }
                assert "request_hash" in columns
            tables = {
                row["name"]
                for row in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table'"
                ).fetchall()
            }
            assert {"core_idempotency_records", "core_side_effect_ledger"} <= tables
            assert apply_pending_schema_migrations(conn) == []


def test_f09_mysql_schema_uses_indexable_types_for_unique_ledger_keys():
    sys.path.insert(0, str(BACKEND))
    from services import schema_migration_service as migrations

    statements = []

    class Cursor:
        def fetchone(self):
            return None

        def fetchall(self):
            return []

    class MySQLConnection:
        provider = "mysql"

        def execute(self, sql, _params=None):
            statements.append(sql)
            return Cursor()

    conn = MySQLConnection()
    migrations._apply_2026_08_24_064(conn)
    migrations._apply_2026_08_24_066(conn)
    schema_sql = "\n".join(statements)

    assert "actor_id VARCHAR(191) NOT NULL" in schema_sql
    assert "endpoint VARCHAR(191) NOT NULL" in schema_sql
    assert "idempotency_key VARCHAR(191) NOT NULL" in schema_sql
    assert "idempotency_record_id VARCHAR(191) NOT NULL" in schema_sql
    assert "effect_type VARCHAR(191) NOT NULL" in schema_sql
    assert "effect_key VARCHAR(191) NOT NULL" in schema_sql
    assert "endpoint TEXT NOT NULL" not in schema_sql
    assert "idempotency_record_id TEXT NOT NULL" not in schema_sql
