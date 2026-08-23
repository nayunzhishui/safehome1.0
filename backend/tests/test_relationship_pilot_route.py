import importlib
import json
import os
import shutil
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = PROJECT_ROOT / "backend"


def _fresh_app(tmp_path):
    sys.path.insert(0, str(BACKEND_ROOT))
    for name in list(sys.modules):
        if name in {"app", "config", "database", "models"} or name.startswith("routes.") or name.startswith("services."):
            sys.modules.pop(name, None)
    os.environ["APP_ENV"] = "development"
    os.environ["DATABASE_PATH"] = str(tmp_path / "safehome-test.sqlite3")
    content_dir = tmp_path / "content"
    shutil.copytree(PROJECT_ROOT / "content", content_dir)
    showcase_path = content_dir / "showcase_access.json"
    showcase = json.loads(showcase_path.read_text(encoding="utf-8"))
    showcase["researcher_platform_full_access"] = False
    showcase["read_only_role_bypass"] = False
    showcase_path.write_text(json.dumps(showcase, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.environ["CONTENT_DIR"] = str(content_dir)
    return importlib.import_module("app").app


def _register(client, username):
    response = client.post(
        "/api/auth/register",
        json={"username": username, "password": "password123", "role": "student", "nickname": username},
    )
    assert response.status_code == 201
    return response.get_json()["data"]


def _researcher(client, username="pilot-researcher"):
    response = client.post(
        "/api/auth/admin-create-account",
        headers={"X-Admin-Token": "safehome-local-admin-token"},
        json={"username": username, "password": "password123", "role": "researcher"},
    )
    assert response.status_code == 201
    login = client.post("/api/auth/login", json={"username": username, "password": "password123"})
    return login.get_json()["data"]


def _submit_relationship_assessment(client, token):
    worksheet = client.get("/api/assessments/relationship_initiation_intention_action").get_json()["data"]
    answers = []
    for question in worksheet["questions"]:
        option = question["options"][len(question["options"]) // 2]
        answers.append({"question_id": question["id"], "prompt": question["prompt"], "value": option["value"]})
    response = client.post(
        "/api/assessment-results",
        headers={"Authorization": f"Bearer {token}"},
        json={"worksheet_id": worksheet["id"], "answers": answers},
    )
    assert response.status_code == 201
    return response.get_json()["data"]


def test_enrollment_requires_consent_and_completed_relationship_assessment(tmp_path):
    app = _fresh_app(tmp_path)
    client = app.test_client()
    student = _register(client, "no-assessment")
    headers = {"Authorization": f"Bearer {student['token']}"}

    no_consent = client.post("/api/relationship-pilot/enrollments", headers=headers, json={})
    no_assessment = client.post(
        "/api/relationship-pilot/enrollments",
        headers=headers,
        json={"research_consent": True},
    )

    assert no_consent.status_code == 400
    assert no_assessment.status_code == 409
    assert no_assessment.get_json()["error"]["code"] == "assessment_required"


def test_showcase_mode_allows_logged_in_parent_to_enter_relationship_pilot(tmp_path):
    app = _fresh_app(tmp_path)
    client = app.test_client()
    response = client.post(
        "/api/auth/register",
        json={"username": "showcase-parent", "password": "password123", "role": "parent", "nickname": "showcase-parent"},
    )
    assert response.status_code == 201
    token = response.get_json()["data"]["token"]

    enrollment = client.post(
        "/api/relationship-pilot/enrollments",
        headers={"Authorization": f"Bearer {token}"},
        json={"research_consent": True},
    )

    assert enrollment.status_code == 409
    assert enrollment.get_json()["error"]["code"] == "assessment_required"


def test_relationship_pilot_full_report_message_task_and_narrative_flow(tmp_path):
    app = _fresh_app(tmp_path)
    client = app.test_client()
    student = _register(client, "pilot-student")
    other = _register(client, "other-student")
    researcher = _researcher(client)
    other_researcher = _researcher(client, "pilot-researcher-2")
    student_headers = {"Authorization": f"Bearer {student['token']}"}
    researcher_headers = {"Authorization": f"Bearer {researcher['token']}"}
    other_researcher_headers = {"Authorization": f"Bearer {other_researcher['token']}"}
    other_headers = {"Authorization": f"Bearer {other['token']}"}
    assessment = _submit_relationship_assessment(client, student["token"])

    enrollment_response = client.post(
        "/api/relationship-pilot/enrollments",
        headers=student_headers,
        json={"research_consent": True, "assessment_result_id": assessment["id"]},
    )
    assert enrollment_response.status_code == 201
    enrollment = enrollment_response.get_json()["data"]
    assert enrollment["assessment_result_id"] == assessment["id"]
    assert enrollment["profile_model_id"].startswith("task12_")
    assert enrollment["dimensions"]
    assert enrollment["radar_features"]

    claimed = client.post(
        f"/api/research/access/enrollments/{enrollment['id']}/claim",
        headers={**researcher_headers, "Idempotency-Key": "pilot-explicit-claim"},
    )
    assert claimed.status_code == 201

    report_response = client.post(
        f"/api/relationship-pilot/enrollments/{enrollment['id']}/report",
        headers=researcher_headers,
    )
    assert report_response.status_code == 201
    report = report_response.get_json()["data"]
    assert report["status"] == "pending_review"
    assert report["report"]["suggested_assessment_questions"]
    assert report["report"]["interpretation_status"] in {"usable", "low_confidence", "outlier"}
    assert "不构成诊断" in report["report"]["boundary_notice"]

    participant_cannot_generate = client.post(
        f"/api/relationship-pilot/enrollments/{enrollment['id']}/report",
        headers=student_headers,
    )
    assert participant_cannot_generate.status_code == 403

    hypothesis_response = client.put(
        f"/api/relationship-pilot/reports/{report['id']}/hypotheses/0",
        headers=student_headers,
        json={"response": "uncertain"},
    )
    assert hypothesis_response.status_code == 409
    assert hypothesis_response.get_json()["error"]["code"] == "report_not_delivered"
    hypothesis_forbidden = client.put(
        f"/api/relationship-pilot/reports/{report['id']}/hypotheses/0",
        headers=other_headers,
        json={"response": "matches"},
    )
    assert hypothesis_forbidden.status_code == 403
    report_detail = client.get(f"/api/relationship-pilot/reports/{report['id']}", headers=student_headers).get_json()["data"]
    assert report_detail["delivery_pending"] is True
    assert "profile_description" not in report_detail["report"]
    assert report_detail["hypothesis_feedback"] == []

    download = client.get(f"/api/relationship-pilot/reports/{report['id']}?download=1", headers=student_headers)
    assert download.status_code == 409
    assert download.get_json()["error"]["code"] == "report_not_delivered"

    forbidden = client.get(f"/api/relationship-pilot/reports/{report['id']}", headers=other_headers)
    assert forbidden.status_code == 404

    drawing = client.post(
        f"/api/relationship-pilot/enrollments/{enrollment['id']}/tasks",
        headers=student_headers,
        json={
            "task_type": "relationship_drawing",
            "drawing_data": {"strokes": [[{"x": 1, "y": 2}, {"x": 3, "y": 4}]]},
            "narration": "这幅画只代表我今天的感受。",
            "material_consent": True,
        },
    )
    sentences = client.post(
        f"/api/relationship-pilot/enrollments/{enrollment['id']}/tasks",
        headers=student_headers,
        json={
            "task_type": "sentence_completion",
            "answers": {"被拒绝": "如果被拒绝，我会先照顾自己的感受。", "边界表达": "如果表达边界，我希望被认真听见。"},
            "material_consent": True,
        },
    )
    assert drawing.status_code == 201
    assert sentences.status_code == 201

    supplement = client.post(
        f"/api/relationship-pilot/enrollments/{enrollment['id']}/longitudinal",
        headers=student_headers,
        json={
            "entry_type": "weekly_supplement",
            "measures": {
                "active_social_count": 2,
                "authentic_expression_count": 1,
                "setback_coping": "先暂停，再和朋友讨论",
                "approach_willingness": 4,
                "worry_intensity": 3,
            },
            "narratives": {
                "achievement": "我主动表达了一次真实想法。",
                "setback": "有一次对话没有得到回应。",
            },
            "event_at": "2026-07-10T10:00:00+08:00",
        },
    )
    assert supplement.status_code == 201
    growth = client.get("/api/relationship-pilot/growth", headers=student_headers)
    assert growth.status_code == 200
    growth_data = growth.get_json()["data"]
    assert growth_data["can_record"] is True
    assert growth_data["latest_enrollment_id"] == enrollment["id"]
    assert any(item["type"] == "weekly_supplement" for item in growth_data["timeline"])
    weekly_timeline = next(item for item in growth_data["timeline"] if item["type"] == "weekly_supplement")
    assert weekly_timeline["summary"] == "已完成本周补充记录"
    assert "主动表达了一次真实想法" not in json.dumps(growth_data["timeline"], ensure_ascii=False)
    assert growth_data["growth_report"]["four_layer_profile"]["basic"]
    assert "不构成疗效证明" in growth_data["growth_report"]["boundary_notice"]
    forbidden_growth = client.get("/api/relationship-pilot/growth", headers=other_headers)
    assert forbidden_growth.status_code == 200
    assert forbidden_growth.get_json()["data"]["timeline"] == []
    claimed = client.post(
        f"/api/research/access/enrollments/{enrollment['id']}/claim",
        headers={**researcher_headers, "Idempotency-Key": "pilot-researcher-claim"},
    )
    assert claimed.status_code in {200, 201}
    dashboard = client.get("/api/relationship-pilot/researcher/dashboard", headers=researcher_headers)
    assert dashboard.status_code == 200
    dossier = dashboard.get_json()["data"]["items"][0]
    assert dossier["tasks_count"] == 2
    assert dossier["report_id"] == report["id"]

    note = client.post(
        f"/api/relationship-pilot/enrollments/{enrollment['id']}/notes",
        headers=researcher_headers,
        json={"note": "访谈时先核对用户希望讨论的问题，不把画像当成定论。"},
    )
    assert note.status_code == 201

    narrative = client.post(
        f"/api/relationship-pilot/enrollments/{enrollment['id']}/narrative",
        headers=researcher_headers,
        json={"next_project_task": "选择一个低压力关系微行动。"},
    )
    assert narrative.status_code == 201
    narrative_id = narrative.get_json()["data"]["id"]
    hidden = client.get(f"/api/relationship-pilot/narratives/{narrative_id}", headers=student_headers)
    assert hidden.status_code == 404
    confirmed = client.post(
        f"/api/relationship-pilot/narratives/{narrative_id}/confirm",
        headers=researcher_headers,
    )
    assert confirmed.status_code == 200
    visible = client.get(f"/api/relationship-pilot/narratives/{narrative_id}", headers=student_headers)
    assert visible.status_code == 200
    assert "researcher_notes" not in visible.get_json()["data"]["draft"]
    assert visible.get_json()["data"]["audience"] == "participant"

    report_confirmed = client.post(
        f"/api/relationship-pilot/reports/{report['id']}/confirm",
        headers=researcher_headers,
    )
    assert report_confirmed.status_code == 200
    assignment_conflict = client.post(
        "/api/messages",
        headers={**other_researcher_headers, "Idempotency-Key": "other-researcher-message"},
        json={"enrollment_id": enrollment["id"], "title": "越权消息", "body": "不应发送成功。"},
    )
    assert assignment_conflict.status_code == 404
    other_researcher_detail = client.get(
        f"/api/relationship-pilot/enrollments/{enrollment['id']}",
        headers=other_researcher_headers,
    )
    assert other_researcher_detail.status_code == 404
    other_researcher_growth = client.get(
        f"/api/relationship-pilot/growth?user_id={student['user']['id']}",
        headers=other_researcher_headers,
    )
    assert other_researcher_growth.status_code == 404
    sent = client.post(
        f"/api/relationship-pilot/reports/{report['id']}/send",
        headers=researcher_headers,
        json={},
    )
    assert sent.status_code == 201
    sent_again = client.post(
        f"/api/relationship-pilot/reports/{report['id']}/send",
        headers=researcher_headers,
        json={},
    )
    assert sent_again.status_code == 200
    assert sent_again.get_json()["data"]["already_sent"] is True
    messages = client.get("/api/messages", headers=student_headers).get_json()["data"]["items"]
    report_messages = [item for item in messages if item["source_type"] == "relationship_screening_report" and item["source_id"] == report["id"]]
    assert len(report_messages) == 1
    assert messages[0]["source_type"] == "relationship_screening_report"
    assert messages[0]["source_id"] == report["id"]
    delivered_report = client.get(f"/api/relationship-pilot/reports/{report['id']}", headers=student_headers).get_json()["data"]
    assert delivered_report["status"] == "sent"
    assert delivered_report["sent_at"]
    hypothesis_response = client.put(
        f"/api/relationship-pilot/reports/{report['id']}/hypotheses/0",
        headers=student_headers,
        json={"response": "uncertain"},
    )
    assert hypothesis_response.status_code == 200
    delivered_report = client.get(f"/api/relationship-pilot/reports/{report['id']}", headers=student_headers).get_json()["data"]
    assert delivered_report["hypothesis_feedback"][0]["response"] == "uncertain"
    download = client.get(f"/api/relationship-pilot/reports/{report['id']}?download=1", headers=student_headers)
    assert download.status_code == 200
    download_payload = json.loads(download.data)
    assert download_payload["title"] == "关系健康初筛报告"
    assert "assessment_result_id" not in download_payload
    assert "worksheet_id" not in download_payload
    assert "model_id" not in download.data.decode("utf-8")
    assert "research_notes" not in download.data.decode("utf-8")

    high_risk_update = client.patch(
        f"/api/relationship-pilot/reports/{report['id']}",
        headers=researcher_headers,
        json={
            "version": "2026.07-relationship-screening-risk",
            "personalized_interpretation": "你应该自杀",
        },
    )
    assert high_risk_update.status_code == 409
    assert high_risk_update.get_json()["error"]["code"] == "report_requires_supervisor_review"

    updated = client.patch(
        f"/api/relationship-pilot/reports/{report['id']}",
        headers=researcher_headers,
        json={
            "version": "2026.07-relationship-screening-v2",
            "personalized_interpretation": "这份更新仍只作为共同讨论线索。",
        },
    )
    assert updated.status_code == 200
    updated_report = updated.get_json()["data"]
    assert updated_report["id"] != report["id"]
    assert updated_report["status"] == "updated"
    original_for_student = client.get(f"/api/relationship-pilot/reports/{report['id']}", headers=student_headers).get_json()["data"]
    assert original_for_student["version"] == report["version"]
    assert original_for_student["report"]["personalized_interpretation"] != "这份更新仍只作为共同讨论线索。"
    updated_for_student = client.get(f"/api/relationship-pilot/reports/{updated_report['id']}", headers=student_headers).get_json()["data"]
    assert updated_for_student["version"] == "2026.07-relationship-screening-v2"
    assert updated_for_student["delivery_pending"] is True
    assert "personalized_interpretation" not in updated_for_student["report"]
    sent_update = client.post(f"/api/relationship-pilot/reports/{updated_report['id']}/send", headers=researcher_headers)
    assert sent_update.status_code == 201
    sent_update_again = client.post(f"/api/relationship-pilot/reports/{updated_report['id']}/send", headers=researcher_headers)
    assert sent_update_again.status_code == 200
    delivered_update = client.get(f"/api/relationship-pilot/reports/{updated_report['id']}", headers=student_headers).get_json()["data"]
    assert delivered_update["report"]["personalized_interpretation"] == "这份更新仍只作为共同讨论线索。"
    updated_messages = client.get("/api/messages", headers=student_headers).get_json()["data"]["items"]
    assert {report["id"], updated_report["id"]} <= {
        item["source_id"] for item in updated_messages if item["source_type"] == "relationship_screening_report"
    }
    stage_feedback_messages = [item for item in updated_messages if item["message_type"] == "relationship_stage_feedback"]
    assert len(stage_feedback_messages) == 1
    assert stage_feedback_messages[0]["sender_role"] == "researcher"
    assert stage_feedback_messages[0]["source_id"] == updated_report["id"]
    assert "sender_id" not in stage_feedback_messages[0]
    assert "idempotency_key" not in stage_feedback_messages[0]
    growth_after_feedback = client.get("/api/relationship-pilot/growth", headers=student_headers).get_json()["data"]
    assert any(item["type"] == "researcher_feedback" for item in growth_after_feedback["timeline"])

    direct_message_headers = {**researcher_headers, "Idempotency-Key": "pilot-message-001"}
    direct_message_payload = {
        "enrollment_id": enrollment["id"],
        "title": "研究者提醒",
        "body": "新的阶段安排已更新，请在方便时查看。",
    }
    direct_message = client.post("/api/messages", headers=direct_message_headers, json=direct_message_payload)
    repeated_direct_message = client.post("/api/messages", headers=direct_message_headers, json=direct_message_payload)
    assert direct_message.status_code == 201
    assert repeated_direct_message.status_code == 200
    assert repeated_direct_message.get_json()["data"]["already_sent"] is True
    idempotency_conflict = client.post(
        "/api/messages",
        headers=direct_message_headers,
        json={**direct_message_payload, "body": "相同幂等键不能改成另一条正文。"},
    )
    assert idempotency_conflict.status_code == 409
    assert idempotency_conflict.get_json()["error"]["code"] == "idempotency_conflict"
    participant_messages = client.get("/api/messages?page=1&page_size=1", headers=student_headers).get_json()["data"]
    assert participant_messages["total"] == 4
    assert participant_messages["has_more"] is True
    assert participant_messages["items"][0]["title"] == "研究者提醒"
    assert "sender_id" not in participant_messages["items"][0]
    assert "idempotency_key" not in participant_messages["items"][0]
    read_all = client.post("/api/messages/read-all", headers=student_headers, json={})
    assert read_all.status_code == 200
    assert read_all.get_json()["data"]["updated_count"] >= 1

    with app.app_context():
        from database import get_connection

        with get_connection() as conn:
            actions = {row[0] for row in conn.execute("SELECT action FROM audit_logs").fetchall()}
            conn.execute("UPDATE relationship_pilot_enrollments SET status = 'withdrawn' WHERE id = ?", (enrollment["id"],))
            conn.commit()
    assert {
        "relationship_enrollment_created",
        "relationship_report_generated",
        "relationship_report_updated",
        "relationship_report_sent",
        "relationship_researcher_assigned",
    } <= actions
    inactive_message = client.post(
        "/api/messages",
        headers={**researcher_headers, "Idempotency-Key": "inactive-enrollment-message"},
        json={"enrollment_id": enrollment["id"], "title": "不应发送", "body": "退出后不应继续收到研究者消息。"},
    )
    assert inactive_message.status_code == 409
    assert inactive_message.get_json()["error"]["code"] == "enrollment_not_active"


def test_relationship_growth_without_enrollment_explicitly_blocks_recording(tmp_path):
    app = _fresh_app(tmp_path)
    client = app.test_client()
    student = _register(client, "growth-no-enrollment")

    response = client.get("/api/relationship-pilot/growth", headers={"Authorization": f"Bearer {student['token']}"})

    assert response.status_code == 200
    data = response.get_json()["data"]
    assert data["can_record"] is False
    assert data["latest_enrollment_id"] is None
    assert data["timeline"] == []


def test_sensitive_relationship_text_enters_risk_review_queue(tmp_path):
    app = _fresh_app(tmp_path)
    client = app.test_client()
    student = _register(client, "risk-pilot-student")
    headers = {"Authorization": f"Bearer {student['token']}"}
    assessment = _submit_relationship_assessment(client, student["token"])
    enrollment = client.post(
        "/api/relationship-pilot/enrollments",
        headers=headers,
        json={"research_consent": True, "assessment_result_id": assessment["id"]},
    ).get_json()["data"]

    response = client.post(
        f"/api/relationship-pilot/enrollments/{enrollment['id']}/longitudinal",
        headers=headers,
        json={
            "entry_type": "key_event",
            "measures": {},
            "narratives": {"event_summary": "我最近不想活"},
        },
    )

    assert response.status_code == 201
    assert response.get_json()["data"]["review_status"] == "priority_review"
    with app.app_context():
        from database import get_connection

        with get_connection() as conn:
            row = conn.execute(
                "SELECT source_type, risk_level FROM risk_review_records WHERE source_id = ?",
                (response.get_json()["data"]["id"],),
            ).fetchone()
    assert row["source_type"] == "relationship_longitudinal_entry"
    assert row["risk_level"] == "high"


def test_relationship_task_and_longitudinal_submissions_are_idempotent(tmp_path):
    app = _fresh_app(tmp_path)
    client = app.test_client()
    student = _register(client, "idempotent-pilot-student")
    headers = {"Authorization": f"Bearer {student['token']}"}
    assessment = _submit_relationship_assessment(client, student["token"])
    enrollment = client.post(
        "/api/relationship-pilot/enrollments",
        headers=headers,
        json={"research_consent": True, "assessment_result_id": assessment["id"]},
    ).get_json()["data"]

    task_headers = {**headers, "Idempotency-Key": "task-retry-001"}
    task_payload = {
        "task_type": "sentence_completion",
        "answers": {"靠近": "我愿意先尝试一个低压力的问候。"},
        "material_consent": True,
    }
    first_task = client.post(f"/api/relationship-pilot/enrollments/{enrollment['id']}/tasks", headers=task_headers, json=task_payload)
    second_task = client.post(f"/api/relationship-pilot/enrollments/{enrollment['id']}/tasks", headers=task_headers, json=task_payload)
    assert first_task.status_code == 201
    assert second_task.status_code == 200
    assert first_task.get_json()["data"]["id"] == second_task.get_json()["data"]["id"]

    entry_headers = {**headers, "Idempotency-Key": "weekly-retry-001"}
    entry_payload = {
        "entry_type": "weekly_supplement",
        "measures": {
            "active_social_count": 1,
            "authentic_expression_count": 1,
            "setback_coping": "先暂停",
            "approach_willingness": 3,
            "worry_intensity": 3,
        },
        "narratives": {"achievement": "完成一次尝试。"},
    }
    first_entry = client.post(f"/api/relationship-pilot/enrollments/{enrollment['id']}/longitudinal", headers=entry_headers, json=entry_payload)
    second_entry = client.post(f"/api/relationship-pilot/enrollments/{enrollment['id']}/longitudinal", headers=entry_headers, json=entry_payload)
    assert first_entry.status_code == 201
    assert second_entry.status_code == 200
    assert first_entry.get_json()["data"]["id"] == second_entry.get_json()["data"]["id"]
