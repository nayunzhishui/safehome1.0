import importlib
import json
import subprocess
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
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "rc0810-f06.sqlite3"))
    monkeypatch.setenv("CONTENT_DIR", str(ROOT / "content"))
    monkeypatch.setenv("DB_PROVIDER", "sqlite")
    monkeypatch.setenv("DATABASE_DATA_WATERMARK", "synthetic_validation_only")
    monkeypatch.setenv("SECRET_KEY", "rc0810-f06-test-secret-key-that-is-long-enough")
    monkeypatch.setenv("ADMIN_EXPORT_TOKEN", "rc0810-f06-admin-token")
    app = importlib.import_module("app").app
    app.config["APP_ENV"] = "production"
    return app


def _seed_actor(app, actor_id, role):
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


def _seed_enrollment(app, enrollment_id, participant_user_id, *, assigned_researcher_id=None):
    with app.app_context():
        from database import get_connection, now_iso

        timestamp = now_iso()
        with get_connection() as conn:
            conn.execute(
                """
                INSERT INTO relationship_pilot_enrollments (
                    id, user_id, assessment_result_id, worksheet_id, dimensions_json,
                    radar_features_json, profile_json, consent_scope, status,
                    review_status, assigned_researcher_id, created_at, updated_at
                ) VALUES (?, ?, ?, 'regulatory_focus_relationship_18', '[]', '[]', '{}',
                          'relationship_pilot_stage2_v1', 'enrolled', 'pending_review', ?, ?, ?)
                """,
                (
                    enrollment_id,
                    participant_user_id,
                    f"result-{enrollment_id}",
                    assigned_researcher_id,
                    timestamp,
                    timestamp,
                ),
            )
            conn.commit()


def _seed_assignment(
    app, enrollment_id, actor_id, role, *, status="active", expires_at=None
):
    with app.app_context():
        from database import get_connection, now_iso

        timestamp = now_iso()
        assignment_id = f"assignment-{enrollment_id}-{actor_id}"
        with get_connection() as conn:
            conn.execute(
                """
                INSERT INTO research_scope_assignments (
                    id, enrollment_id, actor_id, assignment_role, status, version,
                    idempotency_key, assigned_by, expires_at, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, 1, ?, 'admin-f06', ?, ?, ?)
                """,
                (
                    assignment_id,
                    enrollment_id,
                    actor_id,
                    role,
                    status,
                    f"seed-{assignment_id}",
                    expires_at,
                    timestamp,
                    timestamp,
                ),
            )
            conn.commit()
        return assignment_id


def _seed_message(app, message_id, user_id):
    with app.app_context():
        from database import get_connection, now_iso

        with get_connection() as conn:
            conn.execute(
                """
                INSERT INTO messages (
                    id, user_id, message_type, title, body, status, created_at
                ) VALUES (?, ?, 'system', '范围消息', '仅目标参与者可见', 'unread', ?)
                """,
                (message_id, user_id, now_iso()),
            )
            conn.commit()


def test_unassigned_researcher_cannot_select_another_participant_diaries(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    participant_headers = _seed_actor(app, "participant-f06", "parent")
    researcher_headers = _seed_actor(app, "researcher-f06", "researcher")
    client = app.test_client()
    created = client.post(
        "/api/diaries",
        headers=participant_headers,
        json={
            "scene": "放学后沟通",
            "event_description": "我先听完，再说明自己的担心。",
            "parent_emotion": "着急",
        },
    )
    assert created.status_code == 201

    existing = client.get(
        "/api/diaries?user_id=participant-f06", headers=researcher_headers
    )
    missing = client.get(
        "/api/diaries?user_id=missing-participant-f06", headers=researcher_headers
    )

    assert existing.status_code == missing.status_code == 404
    assert existing.get_json()["error"]["code"] == "not_found"
    assert missing.get_json()["error"]["code"] == "not_found"
    assert "participant-f06" not in str(existing.get_json())


def test_assigned_researcher_can_read_participant_diaries(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    participant_headers = _seed_actor(app, "participant-assigned-f06", "parent")
    researcher_headers = _seed_actor(app, "researcher-assigned-f06", "researcher")
    _seed_actor(app, "admin-f06", "admin")
    _seed_enrollment(app, "enrollment-assigned-f06", "participant-assigned-f06")
    _seed_assignment(
        app,
        "enrollment-assigned-f06",
        "researcher-assigned-f06",
        "researcher",
    )
    client = app.test_client()
    assert (
        client.post(
            "/api/diaries",
            headers=participant_headers,
            json={"scene": "晚饭后", "event_description": "先暂停", "parent_emotion": "担心"},
        ).status_code
        == 201
    )

    response = client.get(
        "/api/diaries?user_id=participant-assigned-f06",
        headers=researcher_headers,
    )

    assert response.status_code == 200
    assert len(response.get_json()["data"]["items"]) == 1


def test_expired_assignment_cannot_read_participant_diaries(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    participant_headers = _seed_actor(app, "participant-expired-f06", "parent")
    researcher_headers = _seed_actor(app, "researcher-expired-f06", "researcher")
    admin_headers = _seed_actor(app, "admin-f06", "admin")
    _seed_actor(app, "researcher-replacement-f06", "researcher")
    _seed_enrollment(app, "enrollment-expired-f06", "participant-expired-f06")
    _seed_assignment(
        app,
        "enrollment-expired-f06",
        "researcher-expired-f06",
        "researcher",
        expires_at="2000-01-01T00:00:00+00:00",
    )
    with app.app_context():
        from database import get_connection

        with get_connection() as conn:
            conn.execute(
                "UPDATE relationship_pilot_enrollments SET assigned_researcher_id = ? WHERE id = ?",
                ("researcher-expired-f06", "enrollment-expired-f06"),
            )
            conn.commit()
    client = app.test_client()
    assert client.post(
        "/api/diaries",
        headers=participant_headers,
        json={"scene": "晚饭后", "event_description": "先暂停", "parent_emotion": "担心"},
    ).status_code == 201

    response = client.get(
        "/api/diaries?user_id=participant-expired-f06",
        headers=researcher_headers,
    )
    relationship = client.get(
        "/api/relationship-pilot/enrollments/enrollment-expired-f06",
        headers=researcher_headers,
    )

    assert response.status_code == 404
    assert response.get_json()["error"]["code"] == "not_found"
    assert relationship.status_code == 404
    replacement = client.post(
        "/api/research/access/assignments",
        headers={**admin_headers, "Idempotency-Key": "replace-expired-f06"},
        json={
            "enrollment_id": "enrollment-expired-f06",
            "actor_id": "researcher-replacement-f06",
            "assignment_role": "researcher",
        },
    )
    assert replacement.status_code == 201


def test_participant_legacy_user_id_cannot_change_owner(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    participant_headers = _seed_actor(app, "participant-owner-f06", "parent")
    _seed_actor(app, "participant-other-f06", "parent")
    client = app.test_client()

    created = client.post(
        "/api/diaries",
        headers=participant_headers,
        json={
            "user_id": "participant-other-f06",
            "scene": "旧客户端",
            "event_description": "旧字段不能改变归属",
            "parent_emotion": "平静",
        },
    )

    assert created.status_code == 201
    assert created.get_json()["data"]["user_id"] == "participant-owner-f06"


def test_assignment_does_not_authorize_generic_cross_participant_write(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    participant_headers = _seed_actor(app, "participant-write-f06", "parent")
    researcher_headers = _seed_actor(app, "researcher-write-f06", "researcher")
    _seed_actor(app, "admin-f06", "admin")
    _seed_enrollment(app, "enrollment-write-f06", "participant-write-f06")
    _seed_assignment(app, "enrollment-write-f06", "researcher-write-f06", "researcher")

    client = app.test_client()
    diary = client.post(
        "/api/diaries",
        headers=participant_headers,
        json={"scene": "反馈", "event_description": "允许专用反馈命令", "parent_emotion": "平静"},
    ).get_json()["data"]
    response = client.post(
        "/api/diaries",
        headers=researcher_headers,
        json={
            "user_id": "participant-write-f06",
            "scene": "越权写入",
            "event_description": "不应创建",
            "parent_emotion": "平静",
        },
    )

    assert response.status_code == 404
    assert response.get_json()["error"]["code"] == "not_found"
    assert "participant-write-f06" not in str(response.get_json())
    feedback = client.post(
        "/api/feedback/generate",
        headers=researcher_headers,
        json={"diary_id": diary["id"]},
    )
    assert feedback.status_code == 201


def test_supervisor_needs_active_scope_for_participant_diaries(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    participant_headers = _seed_actor(app, "participant-supervisor-f06", "parent")
    supervisor_headers = _seed_actor(app, "supervisor-f06", "supervisor")
    _seed_actor(app, "admin-f06", "admin")
    _seed_enrollment(app, "enrollment-supervisor-f06", "participant-supervisor-f06")
    client = app.test_client()
    assert client.post(
        "/api/diaries",
        headers=participant_headers,
        json={"scene": "范围测试", "event_description": "只供授权查看", "parent_emotion": "平静"},
    ).status_code == 201

    denied = client.get(
        "/api/diaries?user_id=participant-supervisor-f06", headers=supervisor_headers
    )
    _seed_assignment(
        app, "enrollment-supervisor-f06", "supervisor-f06", "supervisor"
    )
    allowed = client.get(
        "/api/diaries?user_id=participant-supervisor-f06", headers=supervisor_headers
    )

    assert denied.status_code == 404
    assert allowed.status_code == 200


def test_admin_cross_participant_read_is_capability_checked_and_audited(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    participant_headers = _seed_actor(app, "participant-admin-f06", "parent")
    admin_headers = _seed_actor(app, "admin-audit-f06", "admin")
    client = app.test_client()
    assert client.post(
        "/api/diaries",
        headers=participant_headers,
        json={"scene": "审计测试", "event_description": "管理员读取留痕", "parent_emotion": "平静"},
    ).status_code == 201

    response = client.get(
        "/api/diaries?user_id=participant-admin-f06", headers=admin_headers
    )

    assert response.status_code == 200
    with app.app_context():
        from database import get_connection

        with get_connection() as conn:
            audit = conn.execute(
                "SELECT * FROM audit_logs WHERE action = 'participant_scope_granted' ORDER BY created_at DESC LIMIT 1"
            ).fetchone()
    assert audit is not None
    assert audit["actor_id"] == "admin-audit-f06"
    assert audit["target_id"] == "participant-admin-f06"


def test_revoked_assignment_immediately_removes_cross_module_scope(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    participant_headers = _seed_actor(app, "participant-revoked-f06", "parent")
    researcher_headers = _seed_actor(app, "researcher-revoked-f06", "researcher")
    _seed_actor(app, "admin-f06", "admin")
    _seed_enrollment(app, "enrollment-revoked-f06", "participant-revoked-f06")
    assignment_id = _seed_assignment(
        app, "enrollment-revoked-f06", "researcher-revoked-f06", "researcher"
    )
    client = app.test_client()
    assert client.post(
        "/api/diaries",
        headers=participant_headers,
        json={"scene": "撤销测试", "event_description": "撤销后不可读", "parent_emotion": "平静"},
    ).status_code == 201
    assert client.get(
        "/api/diaries?user_id=participant-revoked-f06", headers=researcher_headers
    ).status_code == 200
    with app.app_context():
        from database import get_connection, now_iso

        with get_connection() as conn:
            conn.execute(
                "UPDATE research_scope_assignments SET status = 'revoked', revoked_at = ?, updated_at = ? WHERE id = ?",
                (now_iso(), now_iso(), assignment_id),
            )
            conn.commit()

    denied = client.get(
        "/api/diaries?user_id=participant-revoked-f06", headers=researcher_headers
    )
    assert denied.status_code == 404


def test_assigned_researcher_message_read_hides_indirect_bola_id(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    _seed_actor(app, "participant-message-f06", "parent")
    _seed_actor(app, "participant-message-other-f06", "parent")
    researcher_headers = _seed_actor(app, "researcher-message-f06", "researcher")
    _seed_actor(app, "admin-f06", "admin")
    _seed_enrollment(app, "enrollment-message-f06", "participant-message-f06")
    _seed_assignment(app, "enrollment-message-f06", "researcher-message-f06", "researcher")
    _seed_message(app, "message-visible-f06", "participant-message-f06")
    _seed_message(app, "message-hidden-f06", "participant-message-other-f06")
    client = app.test_client()

    listed = client.get(
        "/api/messages?user_id=participant-message-f06", headers=researcher_headers
    )
    hidden = client.get(
        "/api/messages/message-hidden-f06?user_id=participant-message-f06",
        headers=researcher_headers,
    )

    assert listed.status_code == 200
    assert [item["id"] for item in listed.get_json()["data"]["items"]] == [
        "message-visible-f06"
    ]
    assert hidden.status_code == 404
    assert "participant-message-other-f06" not in str(hidden.get_json())


def test_relationship_write_cannot_auto_claim_unassigned_enrollment(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    _seed_actor(app, "participant-claim-f06", "parent")
    researcher_headers = _seed_actor(app, "researcher-claim-f06", "researcher")
    _seed_actor(app, "admin-f06", "admin")
    _seed_enrollment(app, "enrollment-claim-f06", "participant-claim-f06")

    response = app.test_client().post(
        "/api/messages",
        headers={**researcher_headers, "Idempotency-Key": "no-auto-claim-f06"},
        json={
            "enrollment_id": "enrollment-claim-f06",
            "title": "不应自动领取",
            "body": "发送消息前必须已有明确分配。",
        },
    )

    assert response.status_code == 404
    with app.app_context():
        from database import get_connection

        with get_connection() as conn:
            count = conn.execute(
                "SELECT COUNT(*) AS count FROM research_scope_assignments WHERE enrollment_id = ?",
                ("enrollment-claim-f06",),
            ).fetchone()["count"]
    assert count == 0


def test_research_workspace_supervisor_pagination_counts_only_assigned_scope(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    supervisor_headers = _seed_actor(app, "supervisor-workspace-f06", "supervisor")
    _seed_actor(app, "admin-f06", "admin")
    client = app.test_client()
    for suffix in ("visible", "hidden"):
        participant_headers = _seed_actor(app, f"participant-{suffix}-f06", "parent")
        _seed_enrollment(
            app, f"enrollment-{suffix}-f06", f"participant-{suffix}-f06"
        )
        assert client.post(
            "/api/diaries",
            headers=participant_headers,
            json={"scene": suffix, "event_description": suffix, "parent_emotion": "平静"},
        ).status_code == 201
    _seed_assignment(
        app,
        "enrollment-visible-f06",
        "supervisor-workspace-f06",
        "supervisor",
    )

    response = client.get(
        "/api/research/participants?page=1&limit=1", headers=supervisor_headers
    )

    assert response.status_code == 200
    data = response.get_json()["data"]
    assert data["total"] == data["count"] == 1
    assert data["items"][0]["user_id"] == "participant-visible-f06"
    assert data["scope"] == "assigned_participants"


def test_therapeutic_case_supervisor_requires_assigned_queue_scope(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    participant_headers = _seed_actor(app, "participant-ta-f06", "parent")
    _seed_actor(app, "researcher-ta-f06", "researcher")
    supervisor_headers = _seed_actor(app, "supervisor-ta-f06", "supervisor")
    admin_headers = _seed_actor(app, "admin-ta-f06", "admin")
    client = app.test_client()
    created = client.post(
        "/api/therapeutic-assessment/cases",
        headers={**participant_headers, "Idempotency-Key": "ta-case-f06"},
        json={
            "assessment_question": "我想共同理解最近一次沟通。",
            "shared_scope": ["question"],
            "consent": True,
            "assigned_researcher_id": "researcher-ta-f06",
        },
    )
    assert created.status_code == 201
    case_id = created.get_json()["data"]["id"]
    second = client.post(
        "/api/therapeutic-assessment/cases",
        headers={**participant_headers, "Idempotency-Key": "ta-case-f06-second"},
        json={
            "assessment_question": "这是同一研究者的另一条记录。",
            "shared_scope": ["question"],
            "consent": True,
            "assigned_researcher_id": "researcher-ta-f06",
        },
    )
    assert second.status_code == 201
    second_case_id = second.get_json()["data"]["id"]
    hidden_queue = client.post(
        f"/api/therapeutic-assessment/cases/{second_case_id}/work-queue",
        headers={**admin_headers, "Idempotency-Key": "ta-hidden-queue-f06"},
        json={"queue_type": "review"},
    )
    assert hidden_queue.status_code == 201

    denied = client.get(
        f"/api/therapeutic-assessment/cases/{case_id}", headers=supervisor_headers
    )
    missing = client.get(
        "/api/therapeutic-assessment/cases/missing-ta-f06", headers=supervisor_headers
    )
    denied_list = client.get(
        "/api/therapeutic-assessment/cases", headers=supervisor_headers
    )
    denied_queue_list = client.get(
        "/api/therapeutic-assessment/work-queue", headers=supervisor_headers
    )
    denied_assign = client.post(
        f"/api/therapeutic-assessment/cases/{case_id}/assign",
        headers={**supervisor_headers, "Idempotency-Key": "ta-assign-denied-f06"},
        json={"researcher_id": "researcher-ta-f06"},
    )
    denied_readiness = client.post(
        f"/api/therapeutic-assessment/cases/{case_id}/readiness",
        headers={**supervisor_headers, "Idempotency-Key": "ta-readiness-denied-f06"},
        json={
            "qualification_evidence_ref": "evidence:q-f06",
            "supervision_evidence_ref": "evidence:s-f06",
            "ethics_evidence_ref": "evidence:e-f06",
        },
    )
    denied_queue = client.post(
        f"/api/therapeutic-assessment/cases/{case_id}/work-queue",
        headers={**supervisor_headers, "Idempotency-Key": "ta-queue-denied-f06"},
        json={"queue_type": "review"},
    )
    with app.app_context():
        from database import get_connection, now_iso

        timestamp = now_iso()
        with get_connection() as conn:
            conn.execute(
                "UPDATE therapeutic_assessment_cases SET assigned_researcher_id = ? WHERE id IN (?, ?)",
                ("researcher-ta-f06", case_id, second_case_id),
            )
            conn.execute(
                """
                INSERT INTO therapeutic_assessment_authorizations (
                    id, user_id, competency_level, task_code, scope_json,
                    supervisor_user_id, evidence_ref, starts_at, expires_at,
                    status, version, granted_by, created_at, updated_at
                ) VALUES ('auth-ta-f06', 'researcher-ta-f06', 'T3', 'feedback_review', ?,
                          'supervisor-ta-f06', 'evidence:f06', ?, ?,
                          'active', 1, 'supervisor-ta-f06', ?, ?)
                """,
                (
                    json.dumps({"case_ids": [case_id]}, ensure_ascii=False),
                    timestamp,
                    "2099-01-01T00:00:00+00:00",
                    timestamp,
                    timestamp,
                ),
            )
            conn.commit()
    allowed = client.get(
        f"/api/therapeutic-assessment/cases/{case_id}", headers=supervisor_headers
    )
    out_of_scope = client.get(
        f"/api/therapeutic-assessment/cases/{second_case_id}", headers=supervisor_headers
    )
    allowed_list = client.get(
        "/api/therapeutic-assessment/cases", headers=supervisor_headers
    )
    allowed_assign = client.post(
        f"/api/therapeutic-assessment/cases/{case_id}/assign",
        headers={**supervisor_headers, "Idempotency-Key": "ta-assign-allowed-f06"},
        json={"researcher_id": "researcher-ta-f06"},
    )
    allowed_readiness = client.post(
        f"/api/therapeutic-assessment/cases/{case_id}/readiness",
        headers={**supervisor_headers, "Idempotency-Key": "ta-readiness-allowed-f06"},
        json={
            "qualification_evidence_ref": "evidence:q-f06",
            "supervision_evidence_ref": "evidence:s-f06",
            "ethics_evidence_ref": "evidence:e-f06",
        },
    )
    allowed_queue = client.post(
        f"/api/therapeutic-assessment/cases/{case_id}/work-queue",
        headers={**supervisor_headers, "Idempotency-Key": "ta-queue-allowed-f06"},
        json={"queue_type": "review"},
    )
    allowed_queue_list = client.get(
        "/api/therapeutic-assessment/work-queue", headers=supervisor_headers
    )

    assert denied.status_code == missing.status_code == 404
    assert denied_list.status_code == 200
    assert denied_list.get_json()["data"]["count"] == 0
    assert denied_queue_list.status_code == 200
    assert denied_queue_list.get_json()["data"]["count"] == 0
    assert denied_assign.status_code == 404
    assert denied_readiness.status_code == 404
    assert denied_queue.status_code == 404
    assert allowed.status_code == 200
    assert out_of_scope.status_code == 404
    listed_ids = {item["id"] for item in allowed_list.get_json()["data"]["items"]}
    assert listed_ids == {case_id}
    assert allowed_assign.status_code == 200
    assert allowed_readiness.status_code == 200
    assert allowed_queue.status_code == 201
    queue_case_ids = {
        item["case_id"] for item in allowed_queue_list.get_json()["data"]["items"]
    }
    assert queue_case_ids == {case_id}


def test_therapeutic_data_item_hides_unshared_object_existence(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    participant_headers = _seed_actor(app, "participant-data-f06", "parent")
    researcher_headers = _seed_actor(app, "researcher-data-f06", "researcher")
    supervisor_headers = _seed_actor(app, "supervisor-data-f06", "supervisor")
    client = app.test_client()
    created_case = client.post(
        "/api/therapeutic-assessment/cases",
        headers={**participant_headers, "Idempotency-Key": "data-case-f06"},
        json={
            "assessment_question": "我想共享一份资料。",
            "shared_scope": ["question"],
            "consent": True,
        },
    )
    case_id = created_case.get_json()["data"]["id"]
    created_item = client.post(
        f"/api/therapeutic-assessment/cases/{case_id}/data-items",
        headers={**participant_headers, "Idempotency-Key": "data-item-f06"},
        json={
            "subject_user_id": "participant-data-f06",
            "involved_user_ids": [],
            "content_ref": "evidence:data-f06",
            "content_sha256": "a" * 64,
            "purpose": "collaborative_assessment",
            "visibility": "professionals",
            "allowed_viewer_ids": ["researcher-data-f06"],
            "expires_at": "2099-01-01T00:00:00+00:00",
        },
    )
    assert created_case.status_code == 201
    assert created_item.status_code == 201
    item_id = created_item.get_json()["data"]["id"]

    allowed = client.get(
        f"/api/therapeutic-assessment/data-items/{item_id}",
        headers=researcher_headers,
    )
    denied = client.get(
        f"/api/therapeutic-assessment/data-items/{item_id}",
        headers=supervisor_headers,
    )
    missing = client.get(
        "/api/therapeutic-assessment/data-items/missing-data-f06",
        headers=supervisor_headers,
    )

    assert allowed.status_code == 200
    assert denied.status_code == missing.status_code == 404


def test_research_export_requires_admin_capability(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    researcher_headers = _seed_actor(app, "researcher-export-f06", "researcher")
    _seed_actor(app, "participant-export-f06", "parent")
    with app.app_context():
        from database import get_connection, now_iso

        with get_connection() as conn:
            conn.execute(
                """
                INSERT INTO assessment_results (
                    id, user_id, worksheet_id, worksheet_title, category,
                    answers_json, scores_json, result_summary, created_at
                ) VALUES ('assessment-export-f06', 'participant-export-f06',
                          'student_profile_v1', '支持性测评', '画像', '[]', '{}',
                          '仅用于范围测试', ?)
                """,
                (now_iso(),),
            )
            conn.commit()

    response = app.test_client().get(
        "/api/admin/export?type=profile", headers=researcher_headers
    )
    assessments = app.test_client().get(
        "/api/admin/assessment-results", headers=researcher_headers
    )

    assert response.status_code == 403
    assert response.get_json()["error"]["details"]["required_capability"] == "research.export"
    assert assessments.status_code == 200
    assert assessments.get_json()["data"]["count"] == 0


def test_production_showcase_header_cannot_expand_participant_scope(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    researcher_headers = _seed_actor(app, "researcher-showcase-f06", "researcher")
    participant_headers = _seed_actor(app, "participant-showcase-f06", "parent")
    _seed_enrollment(app, "enrollment-showcase-f06", "participant-showcase-f06")
    client = app.test_client()
    assert client.post(
        "/api/diaries",
        headers=participant_headers,
        json={"scene": "展示模式", "event_description": "生产环境不可绕过", "parent_emotion": "平静"},
    ).status_code == 201

    response = client.get(
        "/api/research/participants",
        headers={**researcher_headers, "X-SafeHome-Researcher-Workspace": "1"},
    )

    assert response.status_code == 200
    assert response.get_json()["data"]["total"] == 0


def test_assignment_transfer_revokes_old_scope_and_grants_new_scope_atomically(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    participant_headers = _seed_actor(app, "participant-transfer-f06", "parent")
    old_headers = _seed_actor(app, "researcher-old-f06", "researcher")
    new_headers = _seed_actor(app, "researcher-new-f06", "researcher")
    admin_headers = _seed_actor(app, "admin-transfer-f06", "admin")
    _seed_enrollment(app, "enrollment-transfer-f06", "participant-transfer-f06")
    client = app.test_client()
    assert client.post(
        "/api/diaries",
        headers=participant_headers,
        json={"scene": "转交", "event_description": "仅当前负责人可读", "parent_emotion": "平静"},
    ).status_code == 201
    created = client.post(
        "/api/research/access/assignments",
        headers={**admin_headers, "Idempotency-Key": "assign-transfer-f06"},
        json={
            "enrollment_id": "enrollment-transfer-f06",
            "actor_id": "researcher-old-f06",
            "assignment_role": "researcher",
        },
    ).get_json()["data"]

    transferred = client.patch(
        f"/api/research/access/assignments/{created['id']}",
        headers={**admin_headers, "Idempotency-Key": "transfer-f06"},
        json={
            "action": "transfer",
            "target_actor_id": "researcher-new-f06",
            "expected_version": created["version"],
        },
    )
    old_read = client.get(
        "/api/diaries?user_id=participant-transfer-f06", headers=old_headers
    )
    new_read = client.get(
        "/api/diaries?user_id=participant-transfer-f06", headers=new_headers
    )

    assert transferred.status_code == 200
    assert old_read.status_code == 404
    assert new_read.status_code == 200


def test_authorization_inventory_verifier_and_expiry_migration_are_recoverable(
    tmp_path, monkeypatch
):
    app = _fresh_app(tmp_path, monkeypatch)
    _seed_actor(app, "participant-migration-f06", "parent")
    _seed_actor(app, "researcher-migration-f06", "researcher")
    _seed_actor(app, "admin-f06", "admin")
    _seed_enrollment(app, "enrollment-migration-f06", "participant-migration-f06")
    assignment_id = _seed_assignment(
        app, "enrollment-migration-f06", "researcher-migration-f06", "researcher"
    )
    inventory = json.loads(
        (ROOT / "config" / "rc0810" / "object_authorization_inventory.json").read_text(
            encoding="utf-8"
        )
    )
    assert inventory["schema"] == "safehome.rc0810.object-authorization-inventory.v1"
    assert {item["object_type"] for item in inventory["objects"]} >= {
        "participant_user",
        "message",
        "relationship_enrollment",
        "therapeutic_case",
        "research_analysis",
        "export",
    }
    module_path = BACKEND / "scripts" / "migrate_rc0810_f06_object_scope.py"
    spec = importlib.util.spec_from_file_location("rc0810_f06_migration", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    with app.app_context():
        from database import get_connection

        with get_connection() as conn:
            assert module.build_plan(conn)["pending_expiry_count"] == 1
            assert module.apply_backfill(conn)["updated_count"] == 1
            assert module.verify(conn)["ok"] is True
            assert module.rollback_backfill(conn)["restored_count"] == 1
            row = conn.execute(
                "SELECT expires_at FROM research_scope_assignments WHERE id = ?",
                (assignment_id,),
            ).fetchone()
            assert row["expires_at"] is None
    verified = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "verify_rc0810_f06_authorization.py")],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert verified.returncode == 0, verified.stdout + verified.stderr
