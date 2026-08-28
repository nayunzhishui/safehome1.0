import importlib
import json
import shutil
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
ADMIN_HEADERS = {"X-Admin-Token": "safehome-local-admin-token"}


def _fresh_app(tmp_path, monkeypatch):
    sys.path.insert(0, str(BACKEND))
    for name in list(sys.modules):
        if name in {"app", "config", "database", "models"} or name.startswith("routes.") or name.startswith("services."):
            sys.modules.pop(name, None)
    content_dir = tmp_path / "content"
    shutil.copytree(ROOT / "content", content_dir)
    showcase = json.loads((content_dir / "showcase_access.json").read_text(encoding="utf-8"))
    showcase["researcher_platform_full_access"] = False
    (content_dir / "showcase_access.json").write_text(json.dumps(showcase, ensure_ascii=False), encoding="utf-8")
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "task36-f06.sqlite3"))
    monkeypatch.setenv("CONTENT_DIR", str(content_dir))
    return importlib.import_module("app").app


def _participant(client, username):
    response = client.post(
        "/api/auth/register",
        json={"username": username, "password": "password123", "role": "student", "nickname": username},
    )
    assert response.status_code == 201
    return response.get_json()["data"]


def _enrollment(client, participant):
    worksheet = client.get("/api/assessments/relationship_initiation_intention_action").get_json()["data"]
    answers = [
        {"question_id": item["id"], "prompt": item["prompt"], "value": item["options"][len(item["options"]) // 2]["value"]}
        for item in worksheet["questions"]
    ]
    headers = {"Authorization": f"Bearer {participant['token']}"}
    assessment = client.post(
        "/api/assessment-results",
        headers=headers,
        json={"worksheet_id": worksheet["id"], "answers": answers},
    ).get_json()["data"]
    response = client.post(
        "/api/relationship-pilot/enrollments",
        headers=headers,
        json={"research_consent": True, "assessment_result_id": assessment["id"]},
    )
    assert response.status_code == 201
    return response.get_json()["data"]


def _post(client, path, key, payload=None):
    return client.post(path, headers={**ADMIN_HEADERS, "Idempotency-Key": key}, json=payload or {})


def test_stage_feedback_requires_preview_confirm_then_sends_one_visible_message(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    participant = _participant(client, "f06-participant")
    enrollment = _enrollment(client, participant)
    participant_headers = {"Authorization": f"Bearer {participant['token']}"}

    created = _post(
        client,
        "/api/research/deliveries",
        "f06-create-1",
        {
            "enrollment_id": enrollment["id"],
            "delivery_type": "stage_feedback",
            "title": "本阶段可以一起核对的变化",
            "content": {
                "observation": "这几次记录中，暂停后再表达的次数有所增加。",
                "evidence": "最近两次练习都记录了暂停动作。",
                "next_step": "下次先用一句话说出当下最需要被理解的内容。",
                "open_question": "这段描述与你的体验相符吗？",
            },
        },
    )
    assert created.status_code == 201
    workflow = created.get_json()["data"]
    assert workflow["status"] == "draft"
    assert workflow["version"] == 0

    premature = _post(client, f"/api/research/deliveries/{workflow['id']}/send", "f06-send-premature", {"expected_version": 0})
    assert premature.status_code == 409
    assert premature.get_json()["error"]["code"] == "delivery_not_confirmed"

    previewed = _post(client, f"/api/research/deliveries/{workflow['id']}/preview", "f06-preview-1", {"expected_version": 0})
    assert previewed.status_code == 200
    preview = previewed.get_json()["data"]
    assert preview["status"] == "previewed"
    assert preview["active_version"]["version_no"] == 1
    assert "不构成诊断" in preview["preview"]["boundary_notice"]

    confirmed = _post(client, f"/api/research/deliveries/{workflow['id']}/confirm", "f06-confirm-1", {"expected_version": 1})
    assert confirmed.status_code == 200
    assert confirmed.get_json()["data"]["status"] == "confirmed"

    sent = _post(client, f"/api/research/deliveries/{workflow['id']}/send", "f06-send-1", {"expected_version": 2})
    assert sent.status_code == 201
    receipt = sent.get_json()["data"]
    assert receipt["status"] == "sent"
    assert receipt["message"]["message_type"] == "relationship_stage_feedback"
    assert receipt["report_id"]

    replay = _post(client, f"/api/research/deliveries/{workflow['id']}/send", "f06-send-1", {"expected_version": 2})
    assert replay.status_code == 200
    assert replay.get_json()["data"]["already_sent"] is True
    assert replay.get_json()["data"]["message"]["id"] == receipt["message"]["id"]

    messages = client.get("/api/messages", headers=participant_headers).get_json()["data"]
    assert messages["total"] == 1
    assert messages["items"][0]["delivery_id"] == workflow["id"]
    assert messages["items"][0]["delivery_version"] == 1


def test_sent_delivery_can_be_withdrawn_without_deleting_history(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    participant = _participant(client, "f06-withdraw")
    enrollment = _enrollment(client, participant)
    created = _post(
        client,
        "/api/research/deliveries",
        "f06-withdraw-create",
        {
            "enrollment_id": enrollment["id"],
            "delivery_type": "participant_message",
            "title": "练习提醒",
            "content": {"body": "如果今天方便，可以回看一次上周选择的小练习。"},
        },
    ).get_json()["data"]
    previewed = _post(client, f"/api/research/deliveries/{created['id']}/preview", "f06-withdraw-preview", {"expected_version": 0}).get_json()["data"]
    confirmed = _post(client, f"/api/research/deliveries/{created['id']}/confirm", "f06-withdraw-confirm", {"expected_version": previewed["version"]}).get_json()["data"]
    sent = _post(client, f"/api/research/deliveries/{created['id']}/send", "f06-withdraw-send", {"expected_version": confirmed["version"]}).get_json()["data"]

    withdrawn = _post(client, f"/api/research/deliveries/{created['id']}/withdraw", "f06-withdraw-action", {"expected_version": sent["version"], "reason": "内容需要重新核对"})
    assert withdrawn.status_code == 200
    data = withdrawn.get_json()["data"]
    assert data["status"] == "withdrawn"
    assert data["message"]["status"] == "withdrawn"

    participant_headers = {"Authorization": f"Bearer {participant['token']}"}
    visible = client.get("/api/messages", headers=participant_headers).get_json()["data"]["items"][0]
    assert visible["status"] == "withdrawn"
    assert visible["is_withdrawn"] is True
    assert visible["withdrawn_at"]
    opened = client.get(f"/api/messages/{visible['id']}", headers=participant_headers).get_json()["data"]
    assert opened["status"] == "withdrawn"
    assert opened["is_withdrawn"] is True
    marked = client.post(f"/api/messages/{visible['id']}/read", headers=participant_headers).get_json()["data"]
    assert marked["status"] == "withdrawn"


def test_repreview_creates_immutable_version_and_stale_write_is_rejected(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    participant = _participant(client, "f06-version")
    enrollment = _enrollment(client, participant)
    created = _post(
        client,
        "/api/research/deliveries",
        "f06-version-create",
        {
            "enrollment_id": enrollment["id"],
            "delivery_type": "participant_message",
            "title": "第一次提醒",
            "content": {"body": "先完成一次低负担的小练习。"},
        },
    ).get_json()["data"]
    previewed = _post(
        client,
        f"/api/research/deliveries/{created['id']}/preview",
        "f06-version-preview-1",
        {"expected_version": created["version"]},
    ).get_json()["data"]
    stale = client.patch(
        f"/api/research/deliveries/{created['id']}",
        headers={**ADMIN_HEADERS, "Idempotency-Key": "f06-version-stale"},
        json={"expected_version": 0, "title": "过期编辑", "content": {"body": "不应覆盖。"}},
    )
    assert stale.status_code == 409
    assert stale.get_json()["error"]["code"] == "version_conflict"

    saved = client.patch(
        f"/api/research/deliveries/{created['id']}",
        headers={**ADMIN_HEADERS, "Idempotency-Key": "f06-version-save"},
        json={
            "expected_version": previewed["version"],
            "title": "第二次提醒",
            "content": {"body": "如果方便，可以再完成一次低负担的小练习。"},
        },
    ).get_json()["data"]
    second = _post(
        client,
        f"/api/research/deliveries/{created['id']}/preview",
        "f06-version-preview-2",
        {"expected_version": saved["version"]},
    ).get_json()["data"]
    assert second["active_version"]["version_no"] == 2
    assert second["active_version"]["content"]["body"].startswith("如果方便")

    sys.path.insert(0, str(BACKEND))
    from database import get_connection

    with get_connection() as conn:
        versions = conn.execute(
            "SELECT version_no, title, content_hash FROM research_delivery_versions WHERE workflow_id = ? ORDER BY version_no",
            (created["id"],),
        ).fetchall()
        events = conn.execute(
            "SELECT action FROM research_delivery_events WHERE workflow_id = ? ORDER BY created_at",
            (created["id"],),
        ).fetchall()
    assert [row["version_no"] for row in versions] == [1, 2]
    assert versions[0]["content_hash"] != versions[1]["content_hash"]
    assert [row["action"] for row in events] == ["create", "preview", "save_draft", "preview"]


def test_researcher_high_risk_preview_and_revoked_scope_are_blocked(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    participant = _participant(client, "f06-scope")
    enrollment = _enrollment(client, participant)
    from routes.auth_utils import generate_auth_token
    from database import get_connection, now_iso

    timestamp = now_iso()
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO users (id, nickname, role, status, created_at, updated_at) VALUES ('f06-researcher', '研究者', 'researcher', 'active', ?, ?)",
            (timestamp, timestamp),
        )
        conn.execute(
            """
            INSERT INTO research_scope_assignments (
                id, enrollment_id, actor_id, assignment_role, status, version,
                idempotency_key, assigned_by, created_at, updated_at
            ) VALUES ('scope-f06', ?, 'f06-researcher', 'researcher', 'active', 1,
                      'scope-f06-key', 'admin', ?, ?)
            """,
            (enrollment["id"], timestamp, timestamp),
        )
        conn.commit()
    with app.app_context():
        researcher_token = generate_auth_token({"id": "f06-researcher", "role": "researcher"})
    researcher_headers = {"Authorization": f"Bearer {researcher_token}"}
    created_response = client.post(
        "/api/research/deliveries",
        headers={**researcher_headers, "Idempotency-Key": "f06-risk-create"},
        json={
            "enrollment_id": enrollment["id"],
            "delivery_type": "participant_message",
            "title": "人工核对提醒",
            "content": {"body": "这段记录提到不想活，需要先由督导人工核对。"},
        },
    )
    assert created_response.status_code == 201
    risky = created_response.get_json()["data"]
    blocked = client.post(
        f"/api/research/deliveries/{risky['id']}/preview",
        headers={**researcher_headers, "Idempotency-Key": "f06-risk-preview"},
        json={"expected_version": risky["version"]},
    )
    assert blocked.status_code == 409
    assert blocked.get_json()["error"]["code"] == "delivery_requires_supervisor_review"
    repeated_block = client.post(
        f"/api/research/deliveries/{risky['id']}/preview",
        headers={**researcher_headers, "Idempotency-Key": "f06-risk-preview-again"},
        json={"expected_version": risky["version"]},
    )
    assert repeated_block.status_code == 409
    with get_connection() as conn:
        queued = conn.execute(
            "SELECT COUNT(*) AS count FROM risk_review_records WHERE source_type = 'research_delivery_workflow' AND source_id = ?",
            (risky["id"],),
        ).fetchone()
    assert queued["count"] == 1

    safe = client.post(
        "/api/research/deliveries",
        headers={**researcher_headers, "Idempotency-Key": "f06-scope-create"},
        json={
            "enrollment_id": enrollment["id"],
            "delivery_type": "participant_message",
            "title": "练习提醒",
            "content": {"body": "如果方便，可以回看一次小练习。"},
        },
    ).get_json()["data"]
    preview = client.post(
        f"/api/research/deliveries/{safe['id']}/preview",
        headers={**researcher_headers, "Idempotency-Key": "f06-scope-preview"},
        json={"expected_version": safe["version"]},
    ).get_json()["data"]
    confirmed = client.post(
        f"/api/research/deliveries/{safe['id']}/confirm",
        headers={**researcher_headers, "Idempotency-Key": "f06-scope-confirm"},
        json={"expected_version": preview["version"]},
    ).get_json()["data"]
    with get_connection() as conn:
        conn.execute(
            "UPDATE research_scope_assignments SET status = 'revoked', version = version + 1, revoked_at = ?, updated_at = ? WHERE id = 'scope-f06'",
            (now_iso(), now_iso()),
        )
        conn.commit()
    denied = client.post(
        f"/api/research/deliveries/{safe['id']}/send",
        headers={**researcher_headers, "Idempotency-Key": "f06-scope-send"},
        json={"expected_version": confirmed["version"]},
    )
    assert denied.status_code == 404
    assert denied.get_json()["error"]["code"] == "not_found"
