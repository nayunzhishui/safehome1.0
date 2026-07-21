import importlib
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"


def _fresh_app(tmp_path, monkeypatch):
    sys.path.insert(0, str(BACKEND))
    for name in list(sys.modules):
        if name in {"app", "config", "database", "models"} or name.startswith("routes.") or name.startswith("services."):
            sys.modules.pop(name, None)
    monkeypatch.setenv("APP_ENV", "testing")
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "task33.sqlite3"))
    monkeypatch.setenv("CONTENT_DIR", str(ROOT / "content"))
    monkeypatch.setenv("UX_GOVERNANCE_WORKBENCH_ENABLED", "1")
    monkeypatch.setenv("AI_QA_ENABLED", "0")
    monkeypatch.setenv("AI_QA_PROVIDER", "fake")
    return importlib.import_module("app").app


def _actors(app):
    specs = [("participant-t33", "parent"), ("researcher-t33", "researcher"), ("supervisor-t33", "supervisor"), ("admin-t33", "admin")]
    with app.app_context():
        database = importlib.import_module("database")
        auth = importlib.import_module("routes.auth_utils")
        with database.get_connection() as conn:
            now = database.now_iso()
            for actor_id, role in specs:
                conn.execute("INSERT INTO users (id, nickname, role, source, status, created_at, updated_at) VALUES (?, ?, ?, 'test', 'active', ?, ?)", (actor_id, actor_id, role, now, now))
            conn.commit()
        return {actor_id: {"Authorization": f"Bearer {auth.generate_auth_token({'id': actor_id, 'role': role})}"} for actor_id, role in specs}


def _passed_results():
    names = ["touch_target", "contrast", "focus_visible", "accessible_name", "heading_order", "form_association", "horizontal_overflow", "reduced_motion"]
    return {name: {"status": "passed", "checked": 75, "issues": 0, "artifact": "synthetic-task33"} for name in names}


def test_public_status_is_minimal_and_internal_registry_is_role_protected(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    headers = _actors(app)
    client = app.test_client()
    public = client.get("/api/ux-governance/public-status")
    denied = client.get("/api/ux-governance/registry", headers=headers["participant-t33"])
    allowed = client.get("/api/ux-governance/registry", headers=headers["researcher-t33"])
    assert public.status_code == 200 and denied.status_code == 403 and allowed.status_code == 200
    assert public.get_json()["data"]["miniprogram_page_count"] == 40
    assert public.get_json()["data"]["release_approved"] is False
    assert "pages" not in public.get_json()["data"]


def test_audit_run_is_admin_only_allowlisted_audited_and_never_contains_participant_text(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    headers = _actors(app)
    client = app.test_client()
    payload = {"environment": "local_automated", "platform": "cross_platform", "viewport": "desktop_mobile", "results": _passed_results()}
    denied = client.post("/api/ux-governance/audits", headers=headers["researcher-t33"], json=payload)
    created = client.post("/api/ux-governance/audits", headers=headers["admin-t33"], json=payload)
    rejected = client.post("/api/ux-governance/audits", headers=headers["admin-t33"], json={**payload, "participant_text": "不应保存"})
    assert denied.status_code == 403 and created.status_code == 201 and rejected.status_code == 400
    item = created.get_json()["data"]
    assert item["contains_participant_text"] is False
    assert item["status"] == "local_automated_passed_external_manual_pending"
    with app.app_context():
        database = importlib.import_module("database")
        with database.get_connection() as conn:
            audit = conn.execute("SELECT * FROM audit_logs WHERE action = 'ux_audit_recorded'").fetchone()
            assert audit is not None and "不应保存" not in str(dict(audit))


def test_evidence_package_keeps_human_device_research_and_release_gates_unsigned(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    headers = _actors(app)
    client = app.test_client()
    denied = client.post("/api/ux-governance/evidence-packages", headers=headers["researcher-t33"])
    created = client.post("/api/ux-governance/evidence-packages", headers=headers["supervisor-t33"])
    assert denied.status_code == 403 and created.status_code == 201
    data = created.get_json()["data"]
    assert data["status"] == "draft_for_human_ux_review"
    assert data["human_research_approved"] is False
    assert data["device_acceptance_approved"] is False
    assert data["release_approved"] is False
    assert data["human_signatures"] == []


def test_goal_diary_and_supervision_replay_client_submission_ids_without_duplicate_rows(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    headers = _actors(app)
    client = app.test_client()
    participant = headers["participant-t33"]
    goal = {"scene": "亲子沟通", "smart_goal": "先停三秒", "client_submission_id": "goal-t33-replay"}
    diary = {"scene": "亲子沟通", "event_description": "一次合成事件", "parent_emotion": "着急", "client_submission_id": "diary-t33-replay"}
    supervision = {"message": "请基于这条合成记录补充建议", "client_submission_id": "support-t33-replay"}
    for path, payload in [("/api/goals", goal), ("/api/diaries", diary), ("/api/supervision", supervision)]:
        first = client.post(path, headers={**participant, "Idempotency-Key": payload["client_submission_id"]}, json=payload)
        repeated = client.post(path, headers={**participant, "Idempotency-Key": payload["client_submission_id"]}, json=payload)
        assert first.status_code == 201 and repeated.status_code == 200
        assert first.get_json()["data"]["id"] == repeated.get_json()["data"]["id"]
    with app.app_context():
        database = importlib.import_module("database")
        with database.get_connection() as conn:
            assert conn.execute("SELECT COUNT(*) AS count FROM goals").fetchone()["count"] == 1
            assert conn.execute("SELECT COUNT(*) AS count FROM emotion_diaries").fetchone()["count"] == 1
            assert conn.execute("SELECT COUNT(*) AS count FROM supervision_requests").fetchone()["count"] == 1


def test_checkin_assessment_profile_and_parent_assessment_retries_do_not_duplicate(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    headers = _actors(app)
    client = app.test_client()
    participant = headers["participant-t33"]

    checkin_payload = {"card_id": "pause-three-seconds", "reflection": "合成练习复盘", "client_submission_id": "checkin-t33-replay"}
    for _ in range(2):
        response = client.post("/api/checkins", headers={**participant, "Idempotency-Key": "checkin-t33-replay"}, json=checkin_payload)
        assert response.status_code in {200, 201}

    listing = client.get("/api/assessments").get_json()["data"]["items"]
    worksheet = None
    for candidate in listing:
        detail = client.get(f"/api/assessments/{candidate['id']}").get_json()["data"]
        if detail.get("questions") and all(question.get("options") for question in detail["questions"] if question.get("required", True)):
            worksheet = detail
            break
    assert worksheet is not None
    answers = [
        {"question_id": question["id"], "value": (question.get("options") or [{"value": "合成回答"}])[0]["value"]}
        for question in worksheet["questions"]
    ]
    assessment_payload = {"worksheet_id": worksheet["id"], "answers": answers, "client_submission_id": "assessment-t33-replay"}
    first_assessment = client.post("/api/assessment-results", headers={**participant, "Idempotency-Key": "assessment-t33-replay"}, json=assessment_payload)
    second_assessment = client.post("/api/assessment-results", headers={**participant, "Idempotency-Key": "assessment-t33-replay"}, json=assessment_payload)
    assert first_assessment.status_code == 201 and second_assessment.status_code == 200
    assert first_assessment.get_json()["data"]["id"] == second_assessment.get_json()["data"]["id"]

    profile_payload = {
        "scores": {"test_anxiety": 3, "iu_score": 3, "self_compassion": 3, "fear_score": 3},
        "client_submission_id": "profile-t33-replay",
    }
    first_profile = client.post("/api/profile", headers={**participant, "Idempotency-Key": "profile-t33-replay"}, json=profile_payload)
    second_profile = client.post("/api/profile", headers={**participant, "Idempotency-Key": "profile-t33-replay"}, json=profile_payload)
    assert first_profile.status_code == 201 and second_profile.status_code == 200
    assert first_profile.get_json()["data"]["assessment_result_id"] == second_profile.get_json()["data"]["assessment_result_id"]

    parent_form = client.get("/api/parent-assessment").get_json()["data"]
    parent_answers = {
        item["item_code"]: "3"
        for scale in parent_form["scales"]["scales"]
        for item in scale["items"]
    }
    parent_payload = {"answers": parent_answers, "research_consent": False, "client_submission_id": "parent-t33-replay"}
    first_parent = client.post("/api/parent-assessments", headers={**participant, "Idempotency-Key": "parent-t33-replay"}, json=parent_payload)
    second_parent = client.post("/api/parent-assessments", headers={**participant, "Idempotency-Key": "parent-t33-replay"}, json=parent_payload)
    assert first_parent.status_code == 201 and second_parent.status_code == 200
    assert first_parent.get_json()["data"]["id"] == second_parent.get_json()["data"]["id"]

    with app.app_context():
        database = importlib.import_module("database")
        with database.get_connection() as conn:
            assert conn.execute("SELECT COUNT(*) AS count FROM checkins").fetchone()["count"] == 1
            assert conn.execute("SELECT COUNT(*) AS count FROM assessment_results").fetchone()["count"] == 2
            assert conn.execute("SELECT COUNT(*) AS count FROM parent_assessment_submissions").fetchone()["count"] == 1


def test_reused_submission_id_with_changed_payload_is_rejected(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    headers = _actors(app)
    client = app.test_client()
    request_headers = {**headers["participant-t33"], "Idempotency-Key": "goal-t33-conflict"}
    assert client.post("/api/goals", headers=request_headers, json={"scene": "作业", "smart_goal": "停三秒"}).status_code == 201
    conflict = client.post("/api/goals", headers=request_headers, json={"scene": "睡前", "smart_goal": "换一句话"})
    assert conflict.status_code == 409
    assert conflict.get_json()["error"]["code"] == "idempotency_conflict"


def test_reused_submission_id_rejects_secondary_field_changes(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    headers = _actors(app)
    client = app.test_client()
    participant = headers["participant-t33"]

    cases = [
        (
            "/api/goals",
            "goal-t33-secondary-conflict",
            {"scene": "作业", "smart_goal": "停三秒", "motivation": "减少升级"},
            {"scene": "作业", "smart_goal": "停三秒", "motivation": "换成另一目标"},
        ),
        (
            "/api/diaries",
            "diary-t33-secondary-conflict",
            {
                "scene": "作业",
                "event_description": "一次合成事件",
                "parent_emotion": "着急",
                "parent_emotion_intensity": 5,
                "raw_text": "合成文本甲",
            },
            {
                "scene": "作业",
                "event_description": "一次合成事件",
                "parent_emotion": "着急",
                "parent_emotion_intensity": 7,
                "raw_text": "合成文本乙",
            },
        ),
        (
            "/api/supervision",
            "support-t33-secondary-conflict",
            {"message": "请补充建议", "contact": "站内联系", "risk_hint": "无"},
            {"message": "请补充建议", "contact": "稍后联系", "risk_hint": "需要留意"},
        ),
    ]
    for path, submission_id, original, changed in cases:
        request_headers = {**participant, "Idempotency-Key": submission_id}
        assert client.post(path, headers=request_headers, json=original).status_code == 201
        conflict = client.post(path, headers=request_headers, json=changed)
        assert conflict.status_code == 409
        assert conflict.get_json()["error"]["code"] == "idempotency_conflict"
