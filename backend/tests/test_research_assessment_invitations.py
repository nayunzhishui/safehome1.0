"""Researchers see participants' scales and send scale invitations; synthetic accounts only."""

import importlib
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = PROJECT_ROOT / "backend"
OWNER_CODE = "synthetic-owner-claim-0002"
WORKSPACE = {"X-SafeHome-Researcher-Workspace": "1"}


def _fresh_app(tmp_path, monkeypatch):
    sys.path.insert(0, str(BACKEND_ROOT))
    for name in list(sys.modules):
        if name in {"app", "config", "database", "models"} or name.startswith("routes.") or name.startswith("services."):
            sys.modules.pop(name, None)
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.delenv("WECHAT_APPID", raising=False)
    monkeypatch.delenv("WECHAT_SECRET", raising=False)
    monkeypatch.setenv("OWNER_CLAIM_CODE", OWNER_CODE)
    monkeypatch.setenv("RESEARCH_PARTICIPANT_SCOPE", "all")
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "research-invitations.sqlite3"))
    monkeypatch.setenv("CONTENT_DIR", str(PROJECT_ROOT / "content"))
    return importlib.import_module("app").app


def _wechat_login(client, code):
    response = client.post("/api/auth/wechat-login", json={"code": code, "nickname": f"合成-{code}"})
    assert response.status_code == 200, response.get_json()
    data = response.get_json()["data"]
    return data["user"], {"Authorization": f"Bearer {data['token']}"}


def test_researcher_sends_a_catalog_scale_and_reads_the_answers(tmp_path, monkeypatch):
    client = _fresh_app(tmp_path, monkeypatch).test_client()
    _, owner_headers = _wechat_login(client, "invite-owner")
    claim = client.post("/api/auth/owner-claim", headers=owner_headers, json={"code": OWNER_CODE})
    owner = {"Authorization": f"Bearer {claim.get_json()['data']['token']}", **WORKSPACE}
    participant, participant_headers = _wechat_login(client, "invite-participant")
    _, bystander_headers = _wechat_login(client, "invite-bystander")

    # The sendable list is the same list 测一测 shows participants.
    catalog = client.get("/api/research/assessment-catalog", headers=owner).get_json()["data"]["items"]
    offered = client.get("/api/assessments", headers=participant_headers).get_json()["data"]["items"]
    assert [item["id"] for item in catalog] == [item["id"] for item in offered]
    worksheet_id = min(catalog, key=lambda item: item["question_count"])["id"]

    # A brand-new account has no records but is still found by search.
    found = client.get("/api/research/participants?q=invite-participant", headers=owner).get_json()["data"]["items"]
    assert [item["user_id"] for item in found] == [participant["id"]]

    invitations = f"/api/research/participants/{participant['id']}/assessment-invitations"
    showcase_only = client.post(invitations, headers={**bystander_headers, **WORKSPACE}, json={"worksheet_id": worksheet_id})
    assert showcase_only.status_code == 403
    assert showcase_only.get_json()["error"]["code"] == "formal_role_required"
    assert client.post(invitations, headers=owner, json={"worksheet_id": "not-in-catalog"}).status_code == 400

    sent = client.post(invitations, headers=owner, json={"worksheet_id": worksheet_id})
    assert sent.status_code == 201, sent.get_json()
    message = sent.get_json()["data"]
    assert (message["message_type"], message["source_type"], message["source_id"]) == ("assessment_invitation", "assessment_worksheet", worksheet_id)
    again = client.post(invitations, headers=owner, json={"worksheet_id": worksheet_id})
    assert again.status_code == 409
    assert again.get_json()["error"]["code"] == "assessment_invitation_pending"
    assert client.get(f"/api/messages/{message['id']}", headers=participant_headers).get_json()["data"]["source_id"] == worksheet_id

    worksheet = client.get(f"/api/assessments/{worksheet_id}", headers=participant_headers).get_json()["data"]
    answers = [
        {"question_id": question["id"], "value": question["options"][0]["value"] if question.get("options") else "合成回答"}
        for question in worksheet["questions"]
    ]
    submitted = client.post("/api/assessment-results", headers=participant_headers, json={"worksheet_id": worksheet_id, "answers": answers})
    assert submitted.status_code == 201, submitted.get_json()

    state = client.get(invitations, headers=owner).get_json()["data"]["items"][0]
    assert state["state"] == "completed" and state["result_id"]
    detail = client.get(f"/api/research/participants/{participant['id']}/assessments/{state['result_id']}", headers=owner).get_json()["data"]
    assert len(detail["answers"]) == len(worksheet["questions"])
    assert all(item["prompt"] and item["answer"] for item in detail["answers"])

    filtered = client.get(f"/api/research/participants?worksheet_id={worksheet_id}", headers=owner).get_json()["data"]["items"]
    assert [item["user_id"] for item in filtered] == [participant["id"]]
    other = next(item["id"] for item in catalog if item["id"] != worksheet_id)
    assert client.get(f"/api/research/participants?worksheet_id={other}", headers=owner).get_json()["data"]["items"] == []

    # Exports carry every question with its answer and score; typed answers stay out.
    open_sheet = next(item for item in offered if item["id"] == "attribution_style_student_36")
    open_questions = client.get(f"/api/assessments/{open_sheet['id']}", headers=participant_headers).get_json()["data"]["questions"]
    secret = "合成私密原因-不应导出"
    open_answers = [
        {"question_id": question["id"], "value": question["options"][0]["value"] if question.get("options") else secret}
        for question in open_questions
    ]
    assert client.post("/api/assessment-results", headers=participant_headers, json={"worksheet_id": open_sheet["id"], "answers": open_answers}).status_code == 201

    items_csv = client.get("/api/admin/export?type=assessment_items", headers=owner).get_data(as_text=True)
    lines = items_csv.lstrip("﻿").splitlines()
    assert lines[0].startswith("result_id,anonymous_id,worksheet_id,worksheet_title,question_no,question_id,question_text")
    assert len(lines) - 1 == len(worksheet["questions"]) + len(open_questions)
    assert worksheet["questions"][0]["prompt"] in items_csv
    assert secret not in items_csv and participant["id"] not in items_csv

    wide_csv = client.get(f"/api/admin/export?type=assessment_wide&worksheet_id={worksheet_id}", headers=owner).get_data(as_text=True)
    wide_lines = wide_csv.lstrip("﻿").splitlines()
    assert wide_lines[0].startswith("result_id,anonymous_id,created_at,total_score") and "Q1 " in wide_lines[0]
    assert len(wide_lines) == 2
    assert client.get("/api/admin/export?type=assessment_wide", headers=owner).status_code == 400
