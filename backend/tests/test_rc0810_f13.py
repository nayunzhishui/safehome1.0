import importlib
import json
import sys
from concurrent.futures import ThreadPoolExecutor
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
    monkeypatch.delenv("DB_PROVIDER", raising=False)
    monkeypatch.delenv("REDIS_URL", raising=False)
    module = importlib.import_module("app")
    return module.app


def _register(client, username: str, role: str) -> tuple[str, str]:
    response = client.post(
        "/api/auth/register",
        json={"username": username, "password": "password123", "role": role},
    )
    assert response.status_code == 201
    data = response.get_json()["data"]
    return data["user"]["id"], data["token"]


def test_created_code_is_high_entropy_and_never_stored_in_plaintext(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    _, parent_token = _register(client, "f13-parent", "parent")

    response = client.post(
        "/api/family/create-bind-code",
        headers={"Authorization": f"Bearer {parent_token}"},
        json={"relation_label": "家长"},
    )

    assert response.status_code == 200
    created = response.get_json()["data"]
    assert len(created["bind_code"]) == 10
    assert created["bind_code"].isdigit()

    import database

    with database.get_connection() as conn:
        stored = conn.execute(
            "SELECT bind_code, bind_code_hash, bind_code_tail FROM family_links WHERE id = ?",
            (created["id"],),
        ).fetchone()
    assert stored["bind_code"] != created["bind_code"]
    assert stored["bind_code_hash"]
    assert stored["bind_code_tail"] == created["bind_code"][-4:]


def test_code_is_redeemed_once_and_replay_does_not_reveal_state(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    _, parent_token = _register(client, "f13-parent-once", "parent")
    student_id, student_token = _register(client, "f13-student-once", "student")
    _, second_student_token = _register(client, "f13-student-replay", "student")
    created = client.post(
        "/api/family/create-bind-code",
        headers={"Authorization": f"Bearer {parent_token}"},
    ).get_json()["data"]

    redeemed = client.post(
        "/api/family/bind-student",
        headers={"Authorization": f"Bearer {student_token}", "X-Device-Id": "student-device-1"},
        json={"bind_code": created["bind_code"]},
    )
    replay = client.post(
        "/api/family/bind-student",
        headers={"Authorization": f"Bearer {second_student_token}", "X-Device-Id": "student-device-2"},
        json={"bind_code": created["bind_code"]},
    )
    wrong = client.post(
        "/api/family/bind-student",
        headers={"Authorization": f"Bearer {second_student_token}", "X-Device-Id": "student-device-2"},
        json={"bind_code": "0000000000"},
    )

    assert redeemed.status_code == 200
    assert redeemed.get_json()["data"]["student_user_id"] == student_id
    assert redeemed.get_json()["data"]["status"] == "consumed"
    assert replay.status_code == wrong.status_code == 400
    assert replay.get_json()["error"] == wrong.get_json()["error"] == {
        "code": "bind_code_unavailable",
        "message": "绑定码无效或已不可使用，请向家长获取新码。",
    }


def test_wrong_code_flood_is_atomically_limited_without_storing_the_code(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    student_id, student_token = _register(client, "f13-flood-student", "student")
    headers = {
        "Authorization": f"Bearer {student_token}",
        "X-Device-Id": "f13-flood-device",
    }
    wrong_code = "1234567890"

    responses = [
        client.post(
            "/api/family/bind-student",
            headers=headers,
            json={"bind_code": wrong_code},
        )
        for _ in range(6)
    ]

    assert [item.status_code for item in responses[:5]] == [400] * 5
    assert responses[5].status_code == 429
    assert responses[5].get_json()["error"] == {
        "code": "family_binding_rate_limited",
        "message": "请求过于频繁，请稍后再试。",
    }

    import database

    with database.get_connection() as conn:
        rows = conn.execute(
            "SELECT dimension, dimension_hash, attempt_count FROM family_bind_rate_limits"
        ).fetchall()
    assert {row["dimension"] for row in rows} == {"account", "device", "ip", "code"}
    assert all(wrong_code not in str(dict(row)) for row in rows)
    assert any(row["dimension"] == "account" and row["dimension_hash"] and student_id not in row["dimension_hash"] for row in rows)


def test_regeneration_revokes_old_code_and_unavailable_states_share_one_error(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    _, parent_token = _register(client, "f13-parent-regenerate", "parent")
    _, student_token = _register(client, "f13-student-regenerate", "student")
    parent_headers = {"Authorization": f"Bearer {parent_token}"}
    student_headers = {
        "Authorization": f"Bearer {student_token}",
        "X-Device-Id": "f13-regenerate-device",
    }
    first = client.post("/api/family/create-bind-code", headers=parent_headers).get_json()["data"]
    second = client.post("/api/family/create-bind-code", headers=parent_headers).get_json()["data"]

    revoked = client.post(
        "/api/family/bind-student",
        headers=student_headers,
        json={"bind_code": first["bind_code"]},
    )

    import database

    with database.get_connection() as conn:
        conn.execute(
            "UPDATE family_links SET expires_at = '2020-01-01T00:00:00+00:00' WHERE id = ?",
            (second["id"],),
        )
        conn.commit()
    expired = client.post(
        "/api/family/bind-student",
        headers=student_headers,
        json={"bind_code": second["bind_code"]},
    )
    missing = client.post(
        "/api/family/bind-student",
        headers=student_headers,
        json={"bind_code": "9999999999"},
    )

    expected = {
        "code": "bind_code_unavailable",
        "message": "绑定码无效或已不可使用，请向家长获取新码。",
    }
    assert revoked.status_code == expired.status_code == missing.status_code == 400
    assert revoked.get_json()["error"] == expired.get_json()["error"] == missing.get_json()["error"] == expected
    with database.get_connection() as conn:
        states = {
            row["id"]: row["status"]
            for row in conn.execute(
                "SELECT id, status FROM family_links WHERE id IN (?, ?)",
                (first["id"], second["id"]),
            ).fetchall()
        }
    assert states == {first["id"]: "revoked", second["id"]: "expired"}


def test_concurrent_students_cannot_redeem_the_same_code_twice(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    setup_client = app.test_client()
    _, parent_token = _register(setup_client, "f13-parent-race", "parent")
    student_one_id, token_one = _register(setup_client, "f13-student-race-1", "student")
    student_two_id, token_two = _register(setup_client, "f13-student-race-2", "student")
    created = setup_client.post(
        "/api/family/create-bind-code",
        headers={"Authorization": f"Bearer {parent_token}"},
    ).get_json()["data"]

    def redeem(token: str, device: str):
        with app.test_client() as client:
            return client.post(
                "/api/family/bind-student",
                headers={"Authorization": f"Bearer {token}", "X-Device-Id": device},
                json={"bind_code": created["bind_code"]},
            )

    with ThreadPoolExecutor(max_workers=2) as pool:
        responses = list(
            pool.map(
                lambda args: redeem(*args),
                [(token_one, "race-device-1"), (token_two, "race-device-2")],
            )
        )

    assert sorted(item.status_code for item in responses) == [200, 400]
    success = next(item for item in responses if item.status_code == 200)
    failure = next(item for item in responses if item.status_code == 400)
    assert success.get_json()["data"]["student_user_id"] in {student_one_id, student_two_id}
    assert failure.get_json()["error"]["code"] == "bind_code_unavailable"


def test_expired_lock_recovers_before_single_redemption(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    _, parent_token = _register(client, "f13-parent-unlock", "parent")
    student_id, student_token = _register(client, "f13-student-unlock", "student")
    created = client.post(
        "/api/family/create-bind-code",
        headers={"Authorization": f"Bearer {parent_token}"},
    ).get_json()["data"]

    import database

    with database.get_connection() as conn:
        conn.execute(
            """
            UPDATE family_links
            SET status = 'locked', locked_until = '2020-01-01T00:00:00+00:00',
                lock_reason = 'rate_limit', version = version + 1
            WHERE id = ?
            """,
            (created["id"],),
        )
        conn.commit()

    listed = client.get(
        "/api/family/members",
        headers={"Authorization": f"Bearer {parent_token}"},
    )
    assert listed.status_code == 200
    assert listed.get_json()["data"]["items"][0]["status"] == "locked"

    response = client.post(
        "/api/family/bind-student",
        headers={
            "Authorization": f"Bearer {student_token}",
            "X-Device-Id": "f13-unlock-device",
        },
        json={"bind_code": created["bind_code"]},
    )

    assert response.status_code == 200
    data = response.get_json()["data"]
    assert data["status"] == "consumed"
    assert data["student_user_id"] == student_id


def test_downstream_failure_rolls_back_redemption_and_attempt_ledger(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    _, parent_token = _register(client, "f13-parent-rollback", "parent")
    _, student_token = _register(client, "f13-student-rollback", "student")
    created = client.post(
        "/api/family/create-bind-code",
        headers={"Authorization": f"Bearer {parent_token}"},
    ).get_json()["data"]

    from routes import family as family_route
    from services.consent_service import ConsentError

    original = family_route.append_consent_event

    def fail_consent(*_args, **_kwargs):
        raise ConsentError("consent_version_conflict", "并发冲突", 409)

    monkeypatch.setattr(family_route, "append_consent_event", fail_consent)
    failed = client.post(
        "/api/family/bind-student",
        headers={
            "Authorization": f"Bearer {student_token}",
            "X-Device-Id": "f13-rollback-device",
        },
        json={"bind_code": created["bind_code"]},
    )
    assert failed.status_code == 409

    import database

    with database.get_connection() as conn:
        link = conn.execute("SELECT * FROM family_links WHERE id = ?", (created["id"],)).fetchone()
        attempt_rows = conn.execute("SELECT COUNT(*) AS count FROM family_bind_rate_limits").fetchone()["count"]
    assert link["status"] == "pending"
    assert link["student_user_id"] is None
    assert link["attempt_count"] == 0
    assert attempt_rows == 0

    monkeypatch.setattr(family_route, "append_consent_event", original)
    original_attach = family_route.attach_guardian_from_family_link

    def fail_safeguard(*_args, **_kwargs):
        from services.participant_safeguard_service import ParticipantSafeguardError

        raise ParticipantSafeguardError("guardian_link_conflict", "监护关系冲突", 409)

    monkeypatch.setattr(
        family_route, "attach_guardian_from_family_link", fail_safeguard
    )
    safeguard_failed = client.post(
        "/api/family/bind-student",
        headers={
            "Authorization": f"Bearer {student_token}",
            "X-Device-Id": "f13-rollback-device",
        },
        json={"bind_code": created["bind_code"]},
    )
    assert safeguard_failed.status_code == 409
    with database.get_connection() as conn:
        link = conn.execute(
            "SELECT * FROM family_links WHERE id = ?", (created["id"],)
        ).fetchone()
        attempt_rows = conn.execute(
            "SELECT COUNT(*) AS count FROM family_bind_rate_limits"
        ).fetchone()["count"]
    assert link["status"] == "pending"
    assert link["student_user_id"] is None
    assert link["attempt_count"] == 0
    assert attempt_rows == 0

    monkeypatch.setattr(
        family_route, "attach_guardian_from_family_link", original_attach
    )
    retried = client.post(
        "/api/family/bind-student",
        headers={
            "Authorization": f"Bearer {student_token}",
            "X-Device-Id": "f13-rollback-device",
        },
        json={"bind_code": created["bind_code"]},
    )
    assert retried.status_code == 200


def test_configured_redis_failure_blocks_redemption_without_mutation(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    _, parent_token = _register(client, "f13-parent-redis", "parent")
    _, student_token = _register(client, "f13-student-redis", "student")
    created = client.post(
        "/api/family/create-bind-code",
        headers={"Authorization": f"Bearer {parent_token}"},
    ).get_json()["data"]

    from services import family_binding_service

    monkeypatch.setattr(family_binding_service, "redis_settings", lambda: {"enabled": True})
    monkeypatch.setattr(
        family_binding_service,
        "redis_rate_limit",
        lambda *_args, **_kwargs: {"available": False, "allowed": True},
    )
    response = client.post(
        "/api/family/bind-student",
        headers={
            "Authorization": f"Bearer {student_token}",
            "X-Device-Id": "f13-redis-device",
        },
        json={"bind_code": created["bind_code"]},
    )

    assert response.status_code == 503
    assert response.get_json()["error"]["code"] == "family_binding_rate_limit_unavailable"

    import database

    with database.get_connection() as conn:
        link = conn.execute("SELECT * FROM family_links WHERE id = ?", (created["id"],)).fetchone()
        attempt_rows = conn.execute("SELECT COUNT(*) AS count FROM family_bind_rate_limits").fetchone()["count"]
    assert link["status"] == "pending"
    assert link["student_user_id"] is None
    assert attempt_rows == 0


def test_production_without_redis_blocks_redemption_without_mutation(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    _, parent_token = _register(client, "f13-parent-production-redis", "parent")
    _, student_token = _register(client, "f13-student-production-redis", "student")
    created = client.post(
        "/api/family/create-bind-code",
        headers={"Authorization": f"Bearer {parent_token}"},
    ).get_json()["data"]
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.delenv("REDIS_URL", raising=False)

    response = client.post(
        "/api/family/bind-student",
        headers={
            "Authorization": f"Bearer {student_token}",
            "X-Device-Id": "f13-production-redis-device",
        },
        json={"bind_code": created["bind_code"]},
    )

    assert response.status_code == 503
    assert response.get_json()["error"]["code"] == "family_binding_rate_limit_unavailable"

    import database

    with database.get_connection() as conn:
        link = conn.execute("SELECT * FROM family_links WHERE id = ?", (created["id"],)).fetchone()
        attempt_rows = conn.execute("SELECT COUNT(*) AS count FROM family_bind_rate_limits").fetchone()["count"]
    assert link["status"] == "pending"
    assert attempt_rows == 0


def test_full_binding_code_never_enters_audit_or_request_logs(tmp_path, monkeypatch, caplog):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    _, parent_token = _register(client, "f13-parent-logs", "parent")
    _, student_token = _register(client, "f13-student-logs", "student")
    created = client.post(
        "/api/family/create-bind-code",
        headers={"Authorization": f"Bearer {parent_token}"},
    ).get_json()["data"]
    code = created["bind_code"]
    response = client.post(
        "/api/family/bind-student",
        headers={
            "Authorization": f"Bearer {student_token}",
            "X-Device-Id": "f13-log-device",
        },
        json={"bind_code": code},
    )
    assert response.status_code == 200

    import database

    with database.get_connection() as conn:
        audit_text = "\n".join(
            str(dict(row)) for row in conn.execute("SELECT * FROM audit_logs").fetchall()
        )
        rate_text = "\n".join(
            str(dict(row)) for row in conn.execute("SELECT * FROM family_bind_rate_limits").fetchall()
        )
        link = conn.execute("SELECT * FROM family_links WHERE id = ?", (created["id"],)).fetchone()
    assert code not in audit_text
    assert code not in rate_text
    assert code not in caplog.text
    assert link["bind_code"] == f"redacted:{code[-4:]}"
    assert link["bind_code_tail"] == code[-4:]


def test_minor_binding_requires_age_confirmation_and_does_not_imply_guardian_consent(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    from services import participant_safeguard_service

    monkeypatch.setattr(participant_safeguard_service.Config, "MINOR_SAFEGUARDS_ENFORCED", True, raising=False)
    _, parent_token = _register(client, "f13-minor-parent", "parent")
    student_id, student_token = _register(client, "f13-minor-student", "student")
    parent_headers = {"Authorization": f"Bearer {parent_token}"}
    student_headers = {
        "Authorization": f"Bearer {student_token}",
        "X-Device-Id": "f13-minor-device",
    }
    code = client.post("/api/family/create-bind-code", headers=parent_headers).get_json()["data"]["bind_code"]

    blocked = client.post(
        "/api/family/bind-student",
        headers=student_headers,
        json={"bind_code": code},
    )
    assert blocked.status_code == 403
    assert blocked.get_json()["error"]["code"] == "age_verification_required"

    age = client.post(
        "/api/minor-safeguards/age-confirmation",
        headers=student_headers,
        json={"age_band": "under_14"},
    )
    assert age.status_code == 200
    bound = client.post(
        "/api/family/bind-student",
        headers=student_headers,
        json={"bind_code": code},
    )
    assert bound.status_code == 200
    data = bound.get_json()["data"]
    assert data["student_user_id"] == student_id
    assert data["status"] == "consumed"
    assert data["minor_safeguards"]["status"] == "guardian_consent_required"
    assert data["minor_safeguards"]["guardian_consent_status"] == "pending"


def test_migrations_redact_legacy_codes_and_preserve_consumed_relationships(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    legacy_code = "654321"
    with app.app_context():
        import database
        from services.schema_migration_service import apply_pending_schema_migrations, migration_manifest

        with database.get_connection() as conn:
            conn.execute(
                "DELETE FROM explicit_schema_migrations WHERE version IN ('2026_08_24_067', '2026_08_24_068')"
            )
            conn.execute(
                """
                INSERT INTO family_links (
                    id, parent_user_id, student_user_id, bind_code, relation_label,
                    status, expires_at, attempt_count, last_attempt_at,
                    created_at, updated_at, confirmed_at, revoked_at
                ) VALUES (
                    'legacy-family-link', 'legacy-parent', 'legacy-student', ?, '家长',
                    'active', NULL, 1, NULL,
                    '2026-08-01T00:00:00+00:00', '2026-08-01T00:00:00+00:00',
                    '2026-08-01T00:00:00+00:00', NULL
                )
                """,
                (legacy_code,),
            )
            applied = apply_pending_schema_migrations(conn)
            conn.commit()
            migrated = conn.execute(
                "SELECT * FROM family_links WHERE id = 'legacy-family-link'"
            ).fetchone()

    assert applied == ["2026_08_24_067", "2026_08_24_068"]
    assert migrated["bind_code"] == "redacted:4321"
    assert migrated["bind_code_hash"]
    assert migrated["bind_code_tail"] == "4321"
    assert migrated["status"] == "consumed"
    f13_manifest = [
        item for item in migration_manifest() if item["version"] in {"2026_08_24_067", "2026_08_24_068"}
    ]
    assert len(f13_manifest) == 2
    assert all(item["rollback_notes"] for item in f13_manifest)
    assert "plaintext" in " ".join(f13_manifest[1]["rollback_notes"]).lower()


def test_f13_mysql_schema_uses_indexable_types_for_digest_and_rate_limit_keys():
    sys.path.insert(0, str(BACKEND_ROOT))
    from database import mysqlize_schema_statement

    schema_sql = mysqlize_schema_statement(
        """
        CREATE TABLE IF NOT EXISTS family_bind_rate_limits (
            id TEXT PRIMARY KEY,
            dimension TEXT NOT NULL,
            dimension_hash TEXT NOT NULL,
            window_key TEXT NOT NULL,
            UNIQUE(dimension, dimension_hash, window_key)
        )
        """
    )
    digest_definition = mysqlize_schema_statement("bind_code_hash TEXT")

    assert "dimension VARCHAR(191) NOT NULL" in schema_sql
    assert "dimension_hash VARCHAR(191) NOT NULL" in schema_sql
    assert "window_key VARCHAR(191) NOT NULL" in schema_sql
    assert digest_definition == "bind_code_hash VARCHAR(191)"


def test_family_binding_machine_contract_exposes_generic_and_rate_limit_errors():
    contract = json.loads(
        (PROJECT_ROOT / "shared" / "contracts" / "api-contract.json").read_text(
            encoding="utf-8"
        )
    )
    operation = next(
        item
        for item in contract["endpoints"]
        if item["path"] == "/api/family/bind-student" and item["method"] == "POST"
    )

    assert "X-Device-Id" in operation["request"]["headers"]
    assert {
        "bind_code_unavailable",
        "family_binding_rate_limited",
        "family_binding_rate_limit_unavailable",
    } <= set(operation["error_codes"])
