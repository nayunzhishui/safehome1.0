import importlib
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"


def _fresh_app(tmp_path, monkeypatch):
    sys.path.insert(0, str(BACKEND))
    for name in list(sys.modules):
        if name in {"app", "config", "database", "models"} or name.startswith(
            ("routes.", "services.")
        ):
            sys.modules.pop(name, None)
    monkeypatch.setenv("APP_ENV", "validation")
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "rc0810-f07.sqlite3"))
    monkeypatch.setenv("CONTENT_DIR", str(ROOT / "content"))
    monkeypatch.setenv("DB_PROVIDER", "sqlite")
    monkeypatch.setenv("DATABASE_DATA_WATERMARK", "synthetic_validation_only")
    monkeypatch.setenv("SECRET_KEY", "rc0810-f07-test-secret-key-that-is-long-enough")
    monkeypatch.setenv("ADMIN_EXPORT_TOKEN", "rc0810-f07-admin-token")
    app = importlib.import_module("app").app
    app.config["APP_ENV"] = "production"
    return app


def _seed_actor(app, actor_id, role="parent"):
    with app.app_context():
        from database import get_connection, now_iso
        from routes.auth_utils import generate_auth_token

        timestamp = now_iso()
        with get_connection() as conn:
            conn.execute(
                "INSERT INTO users (id, nickname, role, status, created_at, updated_at) "
                "VALUES (?, ?, ?, 'active', ?, ?)",
                (actor_id, actor_id, role, timestamp, timestamp),
            )
            conn.commit()
        return {
            "Authorization": f"Bearer {generate_auth_token({'id': actor_id, 'role': role})}"
        }


def _create_consent(client, headers, **overrides):
    payload = {
        "consent_type": "privacy_policy",
        "consent_version": "2026.07-consent-v2",
        "purpose": "service_delivery",
        "processor": "safehome",
        "text_hash": "a" * 64,
        "agreed": True,
    }
    payload.update(overrides)
    return client.post("/api/consent", json=payload, headers=headers)


def test_consent_post_is_authenticated_self_only_and_records_provenance(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    owner_headers = _seed_actor(app, "parent-f07")

    assert _create_consent(client, {}).status_code == 401

    impersonation = _create_consent(
        client, owner_headers, user_id="another-participant"
    )
    assert impersonation.status_code == 403
    assert impersonation.get_json()["error"]["code"] == "consent_self_only"

    created_response = _create_consent(client, owner_headers, user_id="parent-f07")
    assert created_response.status_code == 201
    created = created_response.get_json()["data"]
    assert created["user_id"] == "parent-f07"
    assert created["subject_id"] == "parent-f07"
    assert created["actor_id"] == "parent-f07"
    assert created["event_type"] == "self_agreed"
    assert created["source"] == "participant_self"
    assert created["purpose"] == "service_delivery"
    assert created["processor"] == "safehome"
    assert created["text_hash"] == "a" * 64
    assert created["supersedes_id"] is None
    assert created["event_version"] == 1


def test_consent_events_are_idempotent_and_use_latest_event_conflict_guard(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    headers = _seed_actor(app, "parent-cycle-f07")

    first = _create_consent(client, headers)
    first_item = first.get_json()["data"]
    duplicate = _create_consent(client, headers)
    assert duplicate.status_code == 200
    assert duplicate.get_json()["data"]["id"] == first_item["id"]

    conflict = _create_consent(
        client,
        headers,
        agreed=False,
        expected_latest_id="stale-consent-id",
        reason="用户主动撤回",
    )
    assert conflict.status_code == 409
    assert conflict.get_json()["error"]["code"] == "consent_version_conflict"

    withdrawn = _create_consent(
        client,
        headers,
        agreed=False,
        expected_latest_id=first_item["id"],
        reason="用户主动撤回",
    )
    assert withdrawn.status_code == 201
    withdrawn_item = withdrawn.get_json()["data"]
    assert withdrawn_item["event_type"] == "self_withdrawn"
    assert withdrawn_item["supersedes_id"] == first_item["id"]
    assert withdrawn_item["event_version"] == 2
    assert withdrawn_item["revoked_at"]

    reconsent = _create_consent(
        client,
        headers,
        consent_version="2026.08-consent-v3",
        purpose="service_delivery_v2",
        text_hash="b" * 64,
        expected_latest_id=withdrawn_item["id"],
    )
    assert reconsent.status_code == 201
    reconsent_item = reconsent.get_json()["data"]
    assert reconsent_item["supersedes_id"] == withdrawn_item["id"]
    assert reconsent_item["consent_version"] == "2026.08-consent-v3"
    assert reconsent_item["event_version"] == 3

    with app.app_context():
        from database import get_connection
        from services.consent_service import has_active_consent

        with get_connection() as conn:
            assert not has_active_consent(
                conn,
                "parent-cycle-f07",
                "privacy_policy",
                consent_version="2026.07-consent-v2",
                purpose="service_delivery",
                processor="safehome",
            )
            assert has_active_consent(
                conn,
                "parent-cycle-f07",
                "privacy_policy",
                consent_version="2026.08-consent-v3",
                purpose="service_delivery_v2",
                processor="safehome",
            )
            assert not has_active_consent(
                conn,
                "parent-cycle-f07",
                "privacy_policy",
                consent_version="2026.08-consent-v3",
                purpose="service_delivery_v2",
                processor="different-processor",
            )


def test_admin_annotation_is_separate_audited_and_cannot_fake_self_consent(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    participant_headers = _seed_actor(app, "participant-annotation-f07")
    admin_headers = _seed_actor(app, "admin-annotation-f07", "admin")
    researcher_headers = _seed_actor(app, "researcher-annotation-f07", "researcher")
    consent = _create_consent(client, participant_headers).get_json()["data"]

    denied = client.post(
        f"/api/consent/{consent['id']}/annotations",
        headers=researcher_headers,
        json={
            "annotation_type": "error_correction",
            "reason": "纸质材料中的版本号录入有误",
            "evidence_ref": "case-note-7",
        },
    )
    assert denied.status_code == 403

    response = client.post(
        f"/api/consent/{consent['id']}/annotations",
        headers=admin_headers,
        json={
            "annotation_type": "error_correction",
            "reason": "纸质材料中的版本号录入有误",
            "evidence_ref": "case-note-7",
        },
    )
    assert response.status_code == 201
    annotation = response.get_json()["data"]
    assert annotation["actor_id"] == "admin-annotation-f07"
    assert annotation["subject_id"] == "participant-annotation-f07"
    assert annotation["consent_record_id"] == consent["id"]

    with app.app_context():
        from database import get_connection, row_to_dict

        with get_connection() as conn:
            original = row_to_dict(
                conn.execute(
                    "SELECT * FROM consent_records WHERE id = ?", (consent["id"],)
                ).fetchone()
            )
            audit = row_to_dict(
                conn.execute(
                    "SELECT * FROM audit_logs WHERE action = 'consent_annotation_created' "
                    "ORDER BY created_at DESC LIMIT 1"
                ).fetchone()
            )
        assert original["actor_id"] == "participant-annotation-f07"
        assert original["agreed"] == 1
        assert audit["actor_id"] == "admin-annotation-f07"
        assert "participant-annotation-f07" in audit["metadata_json"]


def test_legacy_migration_marks_unknown_provenance_and_can_rollback(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    with app.app_context():
        from database import get_connection, now_iso
        from scripts.migrate_rc0810_f07_consent_provenance import (
            apply_backfill,
            rollback_backfill,
            verify,
        )

        with get_connection() as conn:
            timestamp = now_iso()
            conn.execute(
                "INSERT INTO consent_records "
                "(id, user_id, consent_type, consent_version, agreed, agreed_at, revoked_at, created_at, subject_id) "
                "VALUES ('legacy-consent-f07', 'legacy-user-f07', 'privacy_policy', 'legacy-v1', 1, ?, NULL, ?, NULL)",
                (timestamp, timestamp),
            )
            conn.commit()
            result = apply_backfill(conn)
            migrated = conn.execute(
                "SELECT * FROM consent_records WHERE id = 'legacy-consent-f07'"
            ).fetchone()
            assert result["updated_count"] == 1
            assert migrated["subject_id"] == "legacy-user-f07"
            assert migrated["actor_id"] is None
            assert migrated["source"] == "provenance_unknown"
            assert migrated["event_type"] == "provenance_unknown"
            assert verify(conn)["ok"] is True
            assert rollback_backfill(conn)["restored_count"] == 1
            rolled_back = conn.execute(
                "SELECT * FROM consent_records WHERE id = 'legacy-consent-f07'"
            ).fetchone()
            assert rolled_back["subject_id"] is None


def test_legacy_migration_orders_versions_by_event_time_before_new_append(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    with app.app_context():
        from database import get_connection
        from scripts.migrate_rc0810_f07_consent_provenance import apply_backfill
        from services.consent_service import append_consent_event, latest_consent_event

        with get_connection() as conn:
            for record_id, created_at in [
                ("a-newer-id-f07", "2026-01-02T00:00:00+00:00"),
                ("z-older-id-f07", "2026-01-01T00:00:00+00:00"),
            ]:
                conn.execute(
                    "INSERT INTO consent_records "
                    "(id, user_id, consent_type, consent_version, agreed, agreed_at, created_at) "
                    "VALUES (?, 'legacy-order-f07', 'privacy_policy', 'legacy-v1', 1, ?, ?)",
                    (record_id, created_at, created_at),
                )
            conn.commit()
            assert apply_backfill(conn)["updated_count"] == 2
            versions = {
                row["id"]: row["event_version"]
                for row in conn.execute(
                    "SELECT id, event_version FROM consent_records WHERE user_id = 'legacy-order-f07'"
                ).fetchall()
            }
            assert versions == {"z-older-id-f07": 1, "a-newer-id-f07": 2}
            assert latest_consent_event(conn, "legacy-order-f07", "privacy_policy")["id"] == "a-newer-id-f07"
            created, _ = append_consent_event(
                conn,
                actor_id="legacy-order-f07",
                subject_id="legacy-order-f07",
                consent_type="privacy_policy",
                consent_version="2026.07-consent-v2",
                agreed=True,
                purpose="service_delivery",
                processor="safehome",
                source="participant_self",
            )
            assert created["event_version"] == 3


def test_participant_reconsent_does_not_reuse_unknown_legacy_provenance(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    headers = _seed_actor(app, "legacy-reconsent-f07")

    with app.app_context():
        from database import get_connection, now_iso

        timestamp = now_iso()
        with get_connection() as conn:
            conn.execute(
                "INSERT INTO consent_records "
                "(id, user_id, actor_id, subject_id, consent_type, consent_version, "
                "purpose, processor, text_hash, source, event_type, event_version, agreed, agreed_at, created_at) "
                "VALUES ('legacy-unknown-f07', 'legacy-reconsent-f07', NULL, 'legacy-reconsent-f07', "
                "'privacy_policy', '2026.07-consent-v2', 'service_delivery', 'safehome', ?, "
                "'provenance_unknown', 'provenance_unknown', 1, 1, ?, ?)",
                ("a" * 64, timestamp, timestamp),
            )
            conn.commit()

    response = _create_consent(
        client,
        headers,
        expected_latest_id="legacy-unknown-f07",
    )
    assert response.status_code == 201
    created = response.get_json()["data"]
    assert created["id"] != "legacy-unknown-f07"
    assert created["actor_id"] == "legacy-reconsent-f07"
    assert created["source"] == "participant_self"
    assert created["supersedes_id"] == "legacy-unknown-f07"
    assert created["event_version"] == 2


def test_unknown_research_consent_is_blocked_until_verified_reconsent(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    with app.app_context():
        from database import get_connection, now_iso
        from routes.parent_assessments import _ensure_research_consent
        from services.privacy_request_service import (
            get_participant_consent_status,
            revoked_research_user_ids,
        )

        timestamp = now_iso()
        with get_connection() as conn:
            conn.execute(
                "INSERT INTO consent_records "
                "(id, user_id, actor_id, subject_id, consent_type, consent_version, purpose, processor, "
                "source, event_type, event_version, agreed, agreed_at, created_at) "
                "VALUES ('legacy-research-f07', 'research-user-f07', NULL, 'research-user-f07', "
                "'research_authorization', 'legacy-v1', 'research_authorization', 'safehome', "
                "'provenance_unknown', 'provenance_unknown', 1, 1, ?, ?)",
                (timestamp, timestamp),
            )
            conn.commit()

        status = get_participant_consent_status("research-user-f07")
        research_item = next(
            item for item in status["items"] if item["consent_type"] == "research_authorization"
        )
        assert research_item["agreed"] is False
        assert research_item["verification_status"] == "provenance_unknown"

        with get_connection() as conn:
            assert "research-user-f07" in revoked_research_user_ids(conn)
            reconsent = _ensure_research_consent(
                conn, "research-user-f07", True, "2026.07-consent-v2", timestamp
            )
            conn.commit()
            created = conn.execute(
                "SELECT * FROM consent_records WHERE id = ?", (reconsent["record_id"],)
            ).fetchone()
            assert created["id"] != "legacy-research-f07"
            assert created["source"] == "embedded_parent_assessment"
            assert created["event_version"] == 2

            upgraded = _ensure_research_consent(
                conn, "research-user-f07", True, "2026.08-consent-v3", timestamp
            )
            assert upgraded["record_id"] != created["id"]
            upgraded_row = conn.execute(
                "SELECT * FROM consent_records WHERE id = ?", (upgraded["record_id"],)
            ).fetchone()
            assert upgraded_row["consent_version"] == "2026.08-consent-v3"
            assert upgraded_row["event_version"] == 3


def test_consent_machine_contract_matches_runtime_access_and_scope():
    from scripts.build_api_contract import _access_for, _error_codes, _object_scope

    self_access = _access_for("/api/consent", "POST", "routes.consent", "")
    assert self_access["mode"] == "authenticated"
    assert self_access["legacy_admin_token"] is False
    assert _object_scope("/api/consent", "POST", self_access, "") == "authenticated_self_only_consent_event_history"
    assert "consent_version_conflict" in _error_codes(
        "/api/consent", "POST", "", self_access
    )

    annotation_path = "/api/consent/<consent_record_id>/annotations"
    annotation_access = _access_for(annotation_path, "POST", "routes.consent", "")
    assert annotation_access == {
        "mode": "capability",
        "roles": ["admin"],
        "legacy_admin_token": False,
        "showcase_read_bypass": False,
    }
    assert _object_scope(annotation_path, "POST", annotation_access, "") == "admin_consent_annotation_without_mutating_participant_event"
    annotation_errors = _error_codes(annotation_path, "POST", "", annotation_access)
    assert {"validation_error", "not_found", "annotation_version_conflict"}.issubset(
        annotation_errors
    )


def test_family_binding_rolls_back_when_consent_event_conflicts(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    parent_headers = _seed_actor(app, "family-parent-f07", "parent")
    student_headers = _seed_actor(app, "family-student-f07", "student")
    with app.app_context():
        from database import get_connection

        with get_connection() as conn:
            conn.execute(
                "UPDATE users SET age_band = '14_or_over' WHERE id = 'family-student-f07'"
            )
            conn.commit()
    created = client.post(
        "/api/family/create-bind-code", headers=parent_headers, json={"relation_label": "家长"}
    ).get_json()["data"]

    from routes import family as family_route
    from services.consent_service import ConsentError

    def raise_conflict(*_args, **_kwargs):
        raise ConsentError("consent_version_conflict", "并发冲突", 409)

    monkeypatch.setattr(family_route, "append_consent_event", raise_conflict)
    response = client.post(
        "/api/family/bind-student",
        headers=student_headers,
        json={"bind_code": created["bind_code"]},
    )
    assert response.status_code == 409

    with app.app_context():
        from database import get_connection

        with get_connection() as conn:
            link = conn.execute(
                "SELECT * FROM family_links WHERE id = ?", (created["id"],)
            ).fetchone()
            consent_count = conn.execute(
                "SELECT COUNT(*) AS count FROM consent_records WHERE user_id = 'family-student-f07'"
            ).fetchone()["count"]
        assert link["status"] == "pending"
        assert link["student_user_id"] is None
        assert link["attempt_count"] == 0
        assert consent_count == 0


def test_mysql_adapter_exposes_rollback_for_family_conflict_mapping():
    from database import MySQLConnection

    calls = []

    class RawConnection:
        def rollback(self):
            calls.append("rollback")

    connection = object.__new__(MySQLConnection)
    connection._connection = RawConnection()
    connection.rollback()
    assert calls == ["rollback"]


def test_privacy_summary_and_delete_helpers_include_consent_lineage(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    participant_headers = _seed_actor(app, "privacy-lineage-f07")
    admin_headers = _seed_actor(app, "admin-lineage-f07", "admin")
    consent = _create_consent(client, participant_headers).get_json()["data"]
    client.post(
        f"/api/consent/{consent['id']}/annotations",
        headers=admin_headers,
        json={
            "annotation_type": "administrative_annotation",
            "reason": "核对纸质签署记录",
            "evidence_ref": "paper-archive-1",
        },
    )

    with app.app_context():
        from database import get_connection
        from services.privacy_request_service import (
            _delete_table_rows,
            _table_count,
            export_participant_privacy_summary,
        )

        summary = export_participant_privacy_summary("privacy-lineage-f07")
        assert summary["consent_history"][0]["id"] == consent["id"]
        assert summary["consent_history"][0]["annotations"][0]["evidence_ref"] == "paper-archive-1"

        with get_connection() as conn:
            assert _table_count(
                conn, "consent_record_annotations", "privacy-lineage-f07"
            ) == 1
            assert _delete_table_rows(
                conn, "consent_record_annotations", "privacy-lineage-f07"
            ) == 1
            assert _delete_table_rows(conn, "consent_records", "privacy-lineage-f07") == 1
            conn.commit()
