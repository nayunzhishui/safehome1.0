import importlib
import json
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
POLICY = ROOT / "content" / "therapeutic_assessment_stop_recovery_policy.json"


def _app(tmp_path, monkeypatch, name="f24.sqlite3"):
    sys.path.insert(0, str(BACKEND))
    for module_name in list(sys.modules):
        if module_name in {"app", "config", "database", "models"} or module_name.startswith(
            ("routes.", "services.")
        ):
            sys.modules.pop(module_name, None)
    monkeypatch.setenv("APP_ENV", "testing")
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / name))
    monkeypatch.setenv("CONTENT_DIR", str(ROOT / "content"))
    return importlib.import_module("app").app


def _seed(app):
    roles = {
        "participant-f24": "parent",
        "researcher-f24": "researcher",
        "supervisor-f24": "supervisor",
        "admin-f24": "admin",
    }
    with app.app_context():
        from database import get_connection, now_iso
        from routes.auth_utils import generate_auth_token

        now = now_iso()
        with get_connection() as conn:
            for user_id, role in roles.items():
                conn.execute(
                    "INSERT INTO users (id, nickname, role, status, created_at, updated_at) "
                    "VALUES (?, ?, ?, 'active', ?, ?)",
                    (user_id, user_id, role, now, now),
                )
            conn.commit()
        return {
            user_id: {
                "Authorization": f"Bearer {generate_auth_token({'id': user_id, 'role': role})}"
            }
            for user_id, role in roles.items()
        }


def _report(client, headers, key="incident-1", trigger="systemic_privacy_incident"):
    return client.post(
        "/api/therapeutic-assessment/stop-recovery/incidents",
        headers={**headers, "Idempotency-Key": key},
        json={
            "trigger_code": trigger,
            "reason_summary": "内部事件摘要：仅用于计算摘要，不应保存原文。",
            "scopes": ["participant_write", "model_input"],
        },
    )


def test_policy_freezes_seven_stop_triggers_and_human_recovery():
    policy = json.loads(POLICY.read_text(encoding="utf-8"))
    assert policy["schema"] == "safehome.therapeutic-assessment.stop-recovery-policy.v1"
    assert len(policy["immediate_pause_triggers"]) == 7
    assert len(policy["recovery_gates"]) == 7
    assert len(policy["rollback_matrix"]) == 8
    assert policy["pause_behavior"]["fail_closed"] is True
    assert policy["pause_behavior"]["internal_reason_exposed_to_participant"] is False
    assert policy["recovery_rules"]["self_verification_allowed"] is False
    assert policy["recovery_rules"]["simulated_agent_may_approve"] is False
    assert policy["recovery_rules"]["automated_test_counts_as_human_approval"] is False
    assert policy["recovery_rules"]["temporary_showcase_bypass_counts_as_recovery"] is False
    assert policy["production_release_approved"] is False


def test_schema_and_mysql_contract_include_stop_recovery_tables():
    sys.path.insert(0, str(BACKEND))
    from database import CURRENT_SCHEMA_NAME, CURRENT_SCHEMA_VERSION, MYSQL_VARCHAR_COLUMNS
    from models import INDEX_SQL, SCHEMA_SQL

    schema = "\n".join(SCHEMA_SQL)
    indexes = "\n".join(INDEX_SQL)
    assert CURRENT_SCHEMA_VERSION >= "2026_07_29_061"
    assert CURRENT_SCHEMA_NAME in {
        "therapeutic_assessment_stop_recovery",
        "rc0810_f07_consent_provenance",
    }
    assert "therapeutic_assessment_stop_incidents" in schema
    assert "therapeutic_assessment_recovery_evidence" in schema
    assert "idx_therapeutic_recovery_verifier_idempotency" in indexes
    assert {"trigger_code", "incident_id", "evidence_type"} <= MYSQL_VARCHAR_COLUMNS


def test_participant_gets_safe_status_but_cannot_manage_incidents(tmp_path, monkeypatch):
    app = _app(tmp_path, monkeypatch)
    headers = _seed(app)
    client = app.test_client()
    status = client.get(
        "/api/therapeutic-assessment/stop-recovery/status",
        headers=headers["participant-f24"],
    )
    assert status.status_code == 200
    data = status.get_json()["data"]
    assert data["ordinary_flow_enabled"] is True
    assert data["internal_reason_exposed"] is False
    assert "incidents" not in data
    assert "runtime_reason" not in data
    denied = _report(client, headers["participant-f24"])
    assert denied.status_code == 403


def test_reporting_is_fail_closed_idempotent_and_does_not_store_reason_text(
    tmp_path, monkeypatch
):
    app = _app(tmp_path, monkeypatch)
    headers = _seed(app)
    client = app.test_client()
    created = _report(client, headers["researcher-f24"])
    assert created.status_code == 201
    item = created.get_json()["data"]
    assert item["status"] == "open"
    assert item["reason_text_stored"] is False
    assert len(item["reason_digest"]) == 64
    replay = _report(client, headers["researcher-f24"])
    assert replay.status_code == 200
    assert replay.get_json()["data"]["id"] == item["id"]
    conflict = client.post(
        "/api/therapeutic-assessment/stop-recovery/incidents",
        headers={**headers["researcher-f24"], "Idempotency-Key": "incident-1"},
        json={
            "trigger_code": "queue_sla_breach",
            "reason_summary": "另一事件",
        },
    )
    assert conflict.status_code == 409
    scope_conflict = client.post(
        "/api/therapeutic-assessment/stop-recovery/incidents",
        headers={**headers["researcher-f24"], "Idempotency-Key": "incident-1"},
        json={
            "trigger_code": "systemic_privacy_incident",
            "reason_summary": "内部事件摘要：仅用于计算摘要，不应保存原文。",
            "scopes": ["research_export"],
        },
    )
    assert scope_conflict.status_code == 409
    participant = client.get(
        "/api/therapeutic-assessment/stop-recovery/status",
        headers=headers["participant-f24"],
    ).get_json()["data"]
    assert participant["ordinary_flow_enabled"] is False
    assert "privacy" not in participant["participant_message"].lower()
    with app.app_context():
        from database import get_connection

        with get_connection() as conn:
            stored = conn.execute(
                "SELECT reason_digest FROM therapeutic_assessment_stop_incidents WHERE id = ?",
                (item["id"],),
            ).fetchone()
            assert len(stored["reason_digest"]) == 64
            columns = {
                row["name"]
                for row in conn.execute(
                    "PRAGMA table_info(therapeutic_assessment_stop_incidents)"
                ).fetchall()
            }
            assert "reason_summary" not in columns
            assert "reason_text" not in columns
            assert (
                conn.execute(
                    "SELECT COUNT(*) AS n FROM audit_logs "
                    "WHERE action = 'therapeutic_assessment_stop_incident_reported'"
                ).fetchone()["n"]
                == 1
            )


def test_recovery_requires_all_independently_verified_evidence_and_version_lock(
    tmp_path, monkeypatch
):
    app = _app(tmp_path, monkeypatch)
    headers = _seed(app)
    client = app.test_client()
    incident = _report(client, headers["researcher-f24"]).get_json()["data"]
    incomplete = client.post(
        f"/api/therapeutic-assessment/stop-recovery/incidents/{incident['id']}/restore",
        headers={**headers["admin-f24"], "Idempotency-Key": "restore-incomplete"},
        json={"expected_version": 1},
    )
    assert incomplete.status_code == 409
    invalid_hash = client.post(
        f"/api/therapeutic-assessment/stop-recovery/incidents/{incident['id']}/evidence",
        headers={**headers["researcher-f24"], "Idempotency-Key": "bad-hash"},
        json={
            "evidence_type": "impact_scope_assessed",
            "artifact_ref": "evidence://impact",
            "artifact_sha256": "bad",
        },
    )
    assert invalid_hash.status_code == 422

    gates = json.loads(POLICY.read_text(encoding="utf-8"))["recovery_gates"]
    evidence = []
    for index, gate in enumerate(gates):
        response = client.post(
            f"/api/therapeutic-assessment/stop-recovery/incidents/{incident['id']}/evidence",
            headers={
                **headers["researcher-f24"],
                "Idempotency-Key": f"evidence-{index}",
            },
            json={
                "evidence_type": gate,
                "artifact_ref": f"evidence://{gate}",
                "artifact_sha256": f"{index + 1:064x}",
            },
        )
        assert response.status_code == 201
        evidence.append(response.get_json()["data"])

    self_verify = client.post(
        f"/api/therapeutic-assessment/stop-recovery/evidence/{evidence[0]['id']}/verify",
        headers={
            **headers["researcher-f24"],
            "Idempotency-Key": "self-verify",
        },
        json={"decision": "verified", "expected_version": 1},
    )
    assert self_verify.status_code == 403
    stale = client.post(
        f"/api/therapeutic-assessment/stop-recovery/evidence/{evidence[0]['id']}/verify",
        headers={**headers["supervisor-f24"], "Idempotency-Key": "stale"},
        json={"decision": "verified", "expected_version": 99},
    )
    assert stale.status_code == 409
    for index, item in enumerate(evidence):
        verified = client.post(
            f"/api/therapeutic-assessment/stop-recovery/evidence/{item['id']}/verify",
            headers={
                **headers["supervisor-f24"],
                "Idempotency-Key": f"verify-{index}",
            },
            json={"decision": "verified", "expected_version": 1},
        )
        assert verified.status_code == 200
        assert verified.get_json()["data"]["status"] == "verified"
    re_review = client.post(
        f"/api/therapeutic-assessment/stop-recovery/evidence/{evidence[0]['id']}/verify",
        headers={
            **headers["admin-f24"],
            "Idempotency-Key": "second-review",
        },
        json={"decision": "rejected", "expected_version": 2},
    )
    assert re_review.status_code == 409
    assert re_review.get_json()["error"]["code"] == "evidence_already_reviewed"

    restored = client.post(
        f"/api/therapeutic-assessment/stop-recovery/incidents/{incident['id']}/restore",
        headers={**headers["admin-f24"], "Idempotency-Key": "restore-complete"},
        json={"expected_version": 1},
    )
    assert restored.status_code == 200
    restored_item = restored.get_json()["data"]
    assert restored_item["status"] == "restored"
    assert restored_item["version"] == 2
    replay = client.post(
        f"/api/therapeutic-assessment/stop-recovery/incidents/{incident['id']}/restore",
        headers={**headers["admin-f24"], "Idempotency-Key": "restore-complete"},
        json={"expected_version": 1},
    )
    assert replay.status_code == 200
    different_key = client.post(
        f"/api/therapeutic-assessment/stop-recovery/incidents/{incident['id']}/restore",
        headers={**headers["admin-f24"], "Idempotency-Key": "restore-other"},
        json={"expected_version": 2},
    )
    assert different_key.status_code == 409
    status = client.get(
        "/api/therapeutic-assessment/stop-recovery/status",
        headers=headers["supervisor-f24"],
    ).get_json()["data"]
    assert status["ordinary_flow_enabled"] is True
    assert status["production_release_approved"] is False
    assert status["temporary_showcase_counts_as_recovery"] is False


def test_other_open_incident_blocks_global_restore(tmp_path, monkeypatch):
    app = _app(tmp_path, monkeypatch)
    headers = _seed(app)
    client = app.test_client()
    first = _report(client, headers["researcher-f24"], key="first").get_json()["data"]
    _report(
        client,
        headers["researcher-f24"],
        key="second",
        trigger="queue_sla_breach",
    )
    gates = json.loads(POLICY.read_text(encoding="utf-8"))["recovery_gates"]
    for index, gate in enumerate(gates):
        item = client.post(
            f"/api/therapeutic-assessment/stop-recovery/incidents/{first['id']}/evidence",
            headers={
                **headers["researcher-f24"],
                "Idempotency-Key": f"first-evidence-{index}",
            },
            json={
                "evidence_type": gate,
                "artifact_ref": f"evidence://first/{gate}",
                "artifact_sha256": f"{index + 100:064x}",
            },
        ).get_json()["data"]
        assert (
            client.post(
                f"/api/therapeutic-assessment/stop-recovery/evidence/{item['id']}/verify",
                headers={
                    **headers["supervisor-f24"],
                    "Idempotency-Key": f"first-verify-{index}",
                },
                json={"decision": "verified", "expected_version": 1},
            ).status_code
            == 200
        )
    blocked = client.post(
        f"/api/therapeutic-assessment/stop-recovery/incidents/{first['id']}/restore",
        headers={**headers["admin-f24"], "Idempotency-Key": "blocked-restore"},
        json={"expected_version": 1},
    )
    assert blocked.status_code == 409
    assert blocked.get_json()["error"]["code"] == "other_open_incidents"


def test_shared_web_and_miniprogram_use_unified_stop_contract():
    shared = (ROOT / "shared/types/api.ts").read_text(encoding="utf-8")
    web_api = (ROOT / "apps/web/src/services/safehomeApi.ts").read_text(
        encoding="utf-8"
    )
    mini_api = (ROOT / "apps/miniprogram/services/api.js").read_text(
        encoding="utf-8"
    )
    participant_flow = (
        ROOT / "apps/miniprogram/utils/therapeuticAssessmentParticipantFlow.js"
    ).read_text(encoding="utf-8")
    assert "TherapeuticAssessmentStopRecoveryStatus" in shared
    assert "getTherapeuticAssessmentStopRecoveryStatus" in web_api
    assert "getTherapeuticAssessmentStopRecoveryStatus" in mini_api
    assert "getTherapeuticAssessmentStopRecoveryStatus()" in participant_flow
    assert "getTherapeuticAssessmentSafetyStatus()" not in participant_flow


def test_migration_supports_four_non_destructive_actions(tmp_path):
    script = BACKEND / "scripts/migrate_task38_f24_stop_recovery.py"
    database = tmp_path / "f24-migration.sqlite3"
    env = {
        **os.environ,
        "APP_ENV": "testing",
        "CONTENT_DIR": str(ROOT / "content"),
    }
    for action in ("plan", "apply", "verify", "rollback"):
        completed = subprocess.run(
            [
                sys.executable,
                str(script),
                action,
                "--database-path",
                str(database),
            ],
            cwd=ROOT,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        assert completed.returncode == 0, completed.stderr or completed.stdout
        payload = json.loads(completed.stdout)
        assert payload["ok"] is True
        assert payload["production_mutation"] is False
        if action == "rollback":
            assert payload["tables_dropped"] is False
            assert payload["incident_history_deleted"] is False
            assert payload["runtime_reactivated"] is False
