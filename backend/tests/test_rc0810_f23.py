import importlib
import json
import os
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(ROOT))


def _fresh_app(tmp_path, monkeypatch):
    sys.path.insert(0, str(BACKEND))
    for name in list(sys.modules):
        if name in {"app", "config", "database", "models"} or name.startswith(
            ("routes.", "services.")
        ):
            sys.modules.pop(name, None)
    monkeypatch.setenv("APP_ENV", "validation")
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "rc0810-f23.sqlite3"))
    monkeypatch.setenv("CONTENT_DIR", str(ROOT / "content"))
    monkeypatch.setenv("DB_PROVIDER", "sqlite")
    monkeypatch.setenv("DATABASE_DATA_WATERMARK", "synthetic_validation_only")
    monkeypatch.setenv("SECRET_KEY", "rc0810-f23-test-secret-key-that-is-long-enough")
    monkeypatch.setenv("ADMIN_EXPORT_TOKEN", "rc0810-f23-admin-token")
    monkeypatch.setenv("SAFETY_SCHEDULER_ENABLED", "1")
    monkeypatch.setenv("THERAPEUTIC_ASSESSMENT_LIFECYCLE_ENABLED", "1")
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


def _seed_enrollment(app, enrollment_id, participant_user_id):
    with app.app_context():
        from database import get_connection, now_iso

        timestamp = now_iso()
        with get_connection() as conn:
            conn.execute(
                """
                INSERT INTO relationship_pilot_enrollments (
                    id, user_id, assessment_result_id, worksheet_id, dimensions_json,
                    radar_features_json, profile_json, consent_scope, status,
                    review_status, created_at, updated_at
                ) VALUES (?, ?, ?, 'regulatory_focus_relationship_18', '[]', '[]', '{}',
                          'relationship_pilot_stage2_v1', 'enrolled', 'pending_review', ?, ?)
                """,
                (
                    enrollment_id,
                    participant_user_id,
                    f"result-{enrollment_id}",
                    timestamp,
                    timestamp,
                ),
            )
            conn.commit()


def _seed_message(app, message_id, user_id):
    with app.app_context():
        from database import get_connection, now_iso

        with get_connection() as conn:
            conn.execute(
                """
                INSERT INTO messages (
                    id, user_id, message_type, title, body, status, created_at
                ) VALUES (?, ?, 'system', 'F23范围消息', '仅目标参与者可见', 'unread', ?)
                """,
                (message_id, user_id, now_iso()),
            )
            conn.commit()


def test_seeded_fuzz_cases_are_derived_from_the_current_api_contract():
    from scripts.run_rc0810_f23_fuzz import build_cases

    cases = build_cases(
        ROOT / "shared" / "contracts" / "api-contract.json",
        ROOT / "config" / "rc0810" / "f23_fuzz_seed_corpus.json",
    )

    assert len(cases) == 10
    assert {case["operation_id"] for case in cases} == {
        "consent.create_consent_record.post",
        "diaries.create_diary.post",
        "messages.list_messages.get",
    }
    assert [case["case_id"] for case in cases] == sorted(
        case["case_id"] for case in cases
    )
    assert json.dumps(cases, ensure_ascii=False, sort_keys=True)


def test_seeded_schema_fuzz_cases_fail_closed_or_are_safely_normalized(
    tmp_path, monkeypatch
):
    from scripts.run_rc0810_f23_fuzz import build_cases

    app = _fresh_app(tmp_path, monkeypatch)
    headers = _seed_actor(app, "participant-fuzz-f23")
    client = app.test_client()
    cases = build_cases()
    results = {}
    for case in cases:
        request_headers = dict(headers)
        if case["operation_id"] == "diaries.create_diary.post":
            request_headers["Idempotency-Key"] = f"f23-{case['case_id']}"
            response = client.post(case["path"], headers=request_headers, json=case["input"])
        elif case["operation_id"] == "consent.create_consent_record.post":
            response = client.post(case["path"], headers=request_headers, json=case["input"])
        else:
            response = client.get(case["path"], headers=request_headers, query_string=case["input"])
        assert response.status_code < 500, case["case_id"]
        results[case["case_id"]] = response

    for case_id in {
        "diary-missing-scene",
        "diary-nested-intensity",
        "diary-overlong-scene",
        "consent-invalid-state",
        "consent-missing-agreed",
        "consent-overlong-version",
    }:
        assert results[case_id].status_code == 400, case_id

    unknown = results["diary-unknown-nested"]
    assert unknown.status_code == 201
    assert "_unexpected" not in unknown.get_json()["data"]
    unicode_case = results["diary-unicode-scene"]
    assert unicode_case.status_code == 201
    assert unicode_case.get_json()["data"]["scene"] == "亲子沟通🙂éمرحبا"

    negative_page = results["messages-negative-page"].get_json()["data"]
    oversized_page = results["messages-page-size-overflow"].get_json()["data"]
    assert negative_page["page"] == 1
    assert oversized_page["page_size"] == 100


def test_role_gate_rejects_participant_on_admin_route(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    headers = _seed_actor(app, "participant-role-f23")

    response = app.test_client().get("/api/admin/worksheets", headers=headers)

    assert response.status_code == 403
    assert response.get_json()["error"]["code"] == "forbidden"


def test_assignment_gate_hides_unassigned_subject(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    participant_headers = _seed_actor(app, "participant-assignment-f23")
    researcher_headers = _seed_actor(app, "researcher-assignment-f23", "researcher")
    _seed_enrollment(app, "enrollment-assignment-f23", "participant-assignment-f23")
    client = app.test_client()
    assert client.post(
        "/api/diaries",
        headers=participant_headers,
        json={
            "scene": "分配范围",
            "event_description": "只允许已分配研究者读取。",
            "parent_emotion": "平静",
        },
    ).status_code == 201

    response = client.get(
        "/api/diaries?user_id=participant-assignment-f23",
        headers=researcher_headers,
    )

    assert response.status_code == 404
    assert response.get_json()["error"]["code"] == "not_found"
    assert "participant-assignment-f23" not in str(response.get_json())


def test_consent_self_only_rejects_replaced_subject(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    headers = _seed_actor(app, "participant-consent-f23")
    _seed_actor(app, "participant-consent-other-f23")

    response = app.test_client().post(
        "/api/consent",
        headers=headers,
        json={
            "subject_id": "participant-consent-other-f23",
            "consent_type": "privacy_policy",
            "agreed": True,
            "consent_version": "2026.08-f23",
        },
    )

    assert response.status_code == 403
    assert response.get_json()["error"]["code"] == "consent_self_only"


def test_risk_gate_blocks_ordinary_feedback(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    headers = _seed_actor(app, "participant-risk-f23")

    response = app.test_client().post(
        "/api/feedback/generate",
        headers=headers,
        json={"event_description": "我现在不想活", "parent_emotion": "绝望"},
    )

    assert response.status_code == 201
    data = response.get_json()["data"]
    assert data["risk_level"] == "high"
    assert data["recommended_card_ids"] == []
    assert data["training_recommendation_rules"] == []
    assert data["pattern_summary"] == "此时系统不会继续生成普通互动模式反馈或训练卡建议。"


def test_therapeutic_risk_gate_routes_to_human_support(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    headers = _seed_actor(app, "participant-therapeutic-f23")

    response = app.test_client().post(
        "/api/therapeutic-assessment/cases",
        headers={**headers, "Idempotency-Key": "therapeutic-risk-f23"},
        json={
            "assessment_question": "我现在不想活，需要有人马上帮助我。",
            "shared_scope": ["question"],
            "consent": True,
        },
    )

    assert response.status_code == 201
    data = response.get_json()["data"]
    assert data["status"] == "support_required"
    assert data["support_signal"] == "needs_human_understanding"


def test_idempotency_hash_conflict_is_rejected(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    headers = {
        **_seed_actor(app, "participant-idempotency-f23"),
        "Idempotency-Key": "diary-conflict-f23",
    }
    client = app.test_client()
    first = client.post(
        "/api/diaries",
        headers=headers,
        json={
            "scene": "第一次",
            "event_description": "固定内容一",
            "parent_emotion": "平静",
        },
    )
    conflict = client.post(
        "/api/diaries",
        headers=headers,
        json={
            "scene": "第二次",
            "event_description": "同一键不能绑定另一份内容",
            "parent_emotion": "担心",
        },
    )

    assert first.status_code == 201
    assert conflict.status_code == 409
    assert conflict.get_json()["error"]["code"] == "idempotency_conflict"


def test_bola_idor_sequence_covers_subject_record_task_message_export_and_source_object(
    tmp_path, monkeypatch
):
    app = _fresh_app(tmp_path, monkeypatch)
    owner_headers = _seed_actor(app, "participant-owner-f23")
    attacker_headers = _seed_actor(app, "participant-attacker-f23")
    researcher_headers = _seed_actor(app, "researcher-attacker-f23", "researcher")
    supervisor_headers = _seed_actor(app, "supervisor-attacker-f23", "supervisor")
    _seed_enrollment(app, "enrollment-owner-f23", "participant-owner-f23")
    _seed_message(app, "message-owner-f23", "participant-owner-f23")
    client = app.test_client()

    subject_swap = client.post(
        "/api/diaries",
        headers=attacker_headers,
        json={
            "user_id": "participant-owner-f23",
            "scene": "主体替换",
            "event_description": "归属必须仍是当前登录者。",
            "parent_emotion": "平静",
        },
    )
    owner_diary = client.post(
        "/api/diaries",
        headers=owner_headers,
        json={
            "scene": "对象范围",
            "event_description": "不能被其他参与者读取或生成反馈。",
            "parent_emotion": "平静",
        },
    ).get_json()["data"]
    record_swap = client.post(
        "/api/feedback/generate",
        headers=attacker_headers,
        json={"diary_id": owner_diary["id"]},
    )
    message_swap = client.get(
        "/api/messages/message-owner-f23", headers=attacker_headers
    )
    export_swap = client.get(
        "/api/admin/export?type=records", headers=attacker_headers
    )
    source_swap = client.post(
        "/api/messages",
        headers={**researcher_headers, "Idempotency-Key": "source-swap-f23"},
        json={
            "enrollment_id": "enrollment-owner-f23",
            "title": "不应发送",
            "body": "未分配研究者不能把外部对象作为消息来源。",
        },
    )
    case = client.post(
        "/api/therapeutic-assessment/cases",
        headers={**owner_headers, "Idempotency-Key": "task-owner-f23"},
        json={
            "assessment_question": "这是仅由本人发起的协作记录。",
            "shared_scope": ["question"],
            "consent": True,
        },
    ).get_json()["data"]
    task_swap = client.post(
        f"/api/therapeutic-assessment/cases/{case['id']}/work-queue",
        headers={**supervisor_headers, "Idempotency-Key": "task-swap-f23"},
        json={"queue_type": "review"},
    )

    assert subject_swap.status_code == 201
    assert subject_swap.get_json()["data"]["user_id"] == "participant-attacker-f23"
    for response in (record_swap, message_swap, source_swap, task_swap):
        assert response.status_code == 404
        assert response.get_json()["error"]["code"] == "not_found"
    assert export_swap.status_code == 403


def test_mutation_runner_kills_every_critical_security_mutant():
    if os.environ.get("RC0810_MUTATION_CHILD") == "1":
        return

    from scripts.run_rc0810_f23_mutation import run_mutations

    report = run_mutations()

    assert report["mutant_count"] == 6
    assert report["killed_count"] == 6
    assert report["surviving_count"] == 0
    assert report["invalid_run_count"] == 0
    assert report["all_killed"] is True
