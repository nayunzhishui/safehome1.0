import importlib
import json
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"


def _app(tmp_path, monkeypatch):
    if str(BACKEND) not in sys.path:
        sys.path.insert(0, str(BACKEND))
    for name in list(sys.modules):
        if name in {"app", "config", "database", "models"} or name.startswith(("routes.", "services.")):
            sys.modules.pop(name, None)
    monkeypatch.setenv("APP_ENV", "testing")
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "supportive-review.sqlite3"))
    monkeypatch.setenv("CONTENT_DIR", str(ROOT / "content"))
    return importlib.import_module("app").app


def _seed_user(app, user_id, role):
    with app.app_context():
        from database import get_connection, now_iso
        from routes.auth_utils import generate_auth_token

        timestamp = now_iso()
        with get_connection() as conn:
            conn.execute(
                "INSERT INTO users (id, nickname, role, status, created_at, updated_at) VALUES (?, ?, ?, 'active', ?, ?)",
                (user_id, user_id, role, timestamp, timestamp),
            )
            conn.commit()
        return {"Authorization": f"Bearer {generate_auth_token({'id': user_id, 'role': role})}"}


def _seed_result(app, user_id, *, risk_level=None, card_ids=(), rules=(), worksheet_id="gad7_anxiety"):
    with app.app_context():
        from database import get_connection, json_dumps, new_id, now_iso

        result_id = new_id("assessment")
        scores = {"total_score": 12, "dimensions": [{"key": "TOTAL", "label": "总分", "score": 12}]}
        if risk_level:
            scores["risk"] = {"risk_level": risk_level}
        snapshot = {"recommendation": {"card_ids": list(card_ids), "rules": list(rules)}}
        with get_connection() as conn:
            conn.execute(
                """
                INSERT INTO assessment_results (
                    id, user_id, worksheet_id, worksheet_title, answers_json, scores_json,
                    content_snapshot_json, result_summary, created_at
                ) VALUES (?, ?, ?, ?, '[]', ?, ?, ?, ?)
                """,
                (result_id, user_id, worksheet_id, "GAD-7 焦虑相关自评量表", json_dumps(scores), json_dumps(snapshot), "合成摘要", now_iso()),
            )
            conn.commit()
        return result_id


def _visible_card_id(app):
    with app.app_context():
        from services.card_service import list_cards

        return list_cards()[0]["id"]


def _create(client, headers, key="key-1", **payload):
    body = {"question": "为什么一件小事也会让我反复担心很久？", "topic_id": "worry_tension", **payload}
    return client.post("/api/supportive-review/reviews", json=body, headers={**headers, "Idempotency-Key": key})


def _patch(client, headers, review, section, data):
    return client.patch(
        f"/api/supportive-review/reviews/{review['id']}",
        json={"section": section, "data": data, "expected_version": review["version"]},
        headers=headers,
    )


def _data(response):
    payload = response.get_json()
    assert payload["ok"] is True, payload
    return payload["data"]


def test_guide_covers_every_worksheet_and_is_participant_only(tmp_path, monkeypatch):
    app = _app(tmp_path, monkeypatch)
    parent = _seed_user(app, "parent_guide", "parent")
    researcher = _seed_user(app, "researcher_guide", "researcher")
    client = app.test_client()

    guide = _data(client.get("/api/supportive-review/guide", headers=parent))
    worksheets = json.loads((ROOT / "content" / "assessment_worksheets.json").read_text(encoding="utf-8"))["worksheets"]
    known = {item["id"] for item in worksheets}
    listed = {worksheet_id for topic in guide["topics"] for worksheet_id in topic["worksheet_ids"]}
    assert listed <= known
    assert listed == known
    assert [step["id"] for step in guide["steps"]][0] == "question"

    assert client.get("/api/supportive-review/guide").status_code == 401
    assert client.get("/api/supportive-review/guide", headers=researcher).status_code == 403
    assert client.get("/api/supportive-review/reviews", headers=researcher).status_code == 403


def test_create_is_idempotent_private_and_owner_scoped(tmp_path, monkeypatch):
    app = _app(tmp_path, monkeypatch)
    parent = _seed_user(app, "parent_owner", "parent")
    other = _seed_user(app, "parent_other", "parent")
    client = app.test_client()

    missing_key = client.post("/api/supportive-review/reviews", json={"question": "我想弄清楚"}, headers=parent)
    assert missing_key.status_code == 400
    assert missing_key.get_json()["error"]["code"] == "missing_idempotency_key"

    created = _create(client, parent)
    assert created.status_code == 201
    review = _data(created)
    assert review["next_step"] == "guess"
    assert review["letter"]["sections"][0]["items"][0]["text"] == "为什么一件小事也会让我反复担心很久？"

    replay = _create(client, parent)
    assert replay.status_code == 200
    assert _data(replay)["id"] == review["id"]
    conflict = _create(client, parent, question="另一个问题")
    assert conflict.status_code == 409

    assert client.get(f"/api/supportive-review/reviews/{review['id']}", headers=other).status_code == 404
    assert _data(client.get("/api/supportive-review/reviews", headers=other))["items"] == []

    with app.app_context():
        from database import get_connection

        with get_connection() as conn:
            row = conn.execute("SELECT module_type, export_allowed FROM records WHERE id = ?", (review["id"],)).fetchone()
            audit = conn.execute("SELECT metadata_json FROM audit_logs WHERE target_id = ?", (review["id"],)).fetchall()
    assert row["module_type"] == "supportive_review"
    assert row["export_allowed"] == 0
    assert audit and all("担心" not in item["metadata_json"] for item in audit)


def test_full_flow_builds_layered_letter_and_followup(tmp_path, monkeypatch):
    app = _app(tmp_path, monkeypatch)
    parent = _seed_user(app, "parent_flow", "parent")
    client = app.test_client()
    card_id = _visible_card_id(app)
    rule = {
        "rule_id": "v4_gad7_moderate",
        "trigger_condition": {"worksheet_id": "gad7_anxiety", "dimension": "TOTAL"},
        "reason": "最近两周焦虑相关的困扰较明显（10分及以上）。这些练习可以帮你管理担心。",
    }
    result_id = _seed_result(app, "parent_flow", card_ids=[card_id], rules=[rule])

    review = _data(_create(client, parent))
    review = _data(_patch(client, parent, review, "guess", {"guess": "可能是我太想把事情做好", "hoped_change": "能早点放下"}))
    review = _data(_patch(client, parent, review, "episode", {
        "situation": "周日晚上在家",
        "body_feeling": "胸口发紧",
        "thought": "又要来不及了",
        "action": "一直刷手机查资料",
        "after": "睡得很晚",
        "intensity": 7,
    }))
    review = _data(_patch(client, parent, review, "exceptions", {"exception": "上周六先散了步", "resources": "和朋友聊几句"}))
    review = _data(_patch(client, parent, review, "scales", {"result_ids": [result_id]}))
    assert review["next_step"] == "inquiry"
    review = _data(_patch(client, parent, review, "inquiry", {"entries": {result_id: {"stood_out": "坐立不安那题", "fit": "担心这点很像"}}}))

    letter = review["letter"]
    sections = {section["id"]: section for section in letter["sections"]}
    assert [sections[key]["level"] for key in ("your_words", "scale_clues", "connections", "other_angles")] == [1, 2, 2, 3]
    clue = sections["scale_clues"]["items"][0]
    assert clue["text"] == "最近两周焦虑相关的困扰较明显（10分及以上）。"
    assert clue["checkable"] is True
    connection_ids = [item["id"] for item in sections["connections"]["items"]]
    assert connection_ids[:3] == ["connection:guess", "connection:thought", "connection:exception"]
    assert sections["other_angles"]["collapsed"] is True
    assert [card["id"] for card in review["card_options"]] == [card_id]

    review = _data(_patch(client, parent, review, "letter_checks", {"checks": {
        clue["id"]: {"fit": "like", "note": "考试前尤其明显"},
        "connection:guess": {"note": "猜对了一半"},
        "unknown:item": {"fit": "like"},
    }}))
    assert set(review["letter_checks"]) == {clue["id"], "connection:guess"}
    assert "fit" not in review["letter_checks"]["connection:guess"]

    early_followup = _patch(client, parent, review, "followup", {"question_now": "clearer", "next": "continue"})
    assert early_followup.status_code == 409
    review = _data(_patch(client, parent, review, "experiment", {
        "own_idea": "每天只在晚饭后担心十分钟",
        "card_id": card_id,
        "stop_condition": "如果明显不舒服就先停下来。",
        "planned_date": "2026-10-09",
    }))
    assert review["followup_due_on"] == "2026-10-16"
    review = _data(_patch(client, parent, review, "followup", {"question_now": "clearer", "next": "continue", "noticed": "第三天忘了"}))
    assert review["status"] == "completed"
    assert review["next_step"] == "done"

    stale = client.patch(
        f"/api/supportive-review/reviews/{review['id']}",
        json={"section": "guess", "data": {"guess": "x"}, "expected_version": 1},
        headers=parent,
    )
    assert stale.status_code == 409
    assert stale.get_json()["error"]["code"] == "version_conflict"


def test_high_risk_text_routes_to_safety_once_and_hides_letter(tmp_path, monkeypatch):
    app = _app(tmp_path, monkeypatch)
    parent = _seed_user(app, "parent_risk", "parent")
    client = app.test_client()
    review = _data(_create(client, parent))
    review = _data(_patch(client, parent, review, "episode", {"thought": "我不想活了"}))

    assert review["risk"]["level"] == "high"
    assert review["risk"]["show_emergency_resources"] is True
    assert review["letter"]["safety_only"] is True
    assert review["card_options"] == []
    review = _data(_patch(client, parent, review, "guess", {"guess": "还是不想活"}))

    with app.app_context():
        from database import get_connection

        with get_connection() as conn:
            rows = conn.execute(
                "SELECT source_type FROM risk_review_records WHERE source_id = ?",
                (review["id"],),
            ).fetchall()
    assert [row["source_type"] for row in rows] == ["supportive_review"]


def test_medium_risk_and_risky_linked_result(tmp_path, monkeypatch):
    app = _app(tmp_path, monkeypatch)
    parent = _seed_user(app, "parent_medium", "parent")
    client = app.test_client()
    review = _data(_create(client, parent))
    review = _data(_patch(client, parent, review, "episode", {"body_feeling": "感觉快撑不住了"}))
    sections = [section["id"] for section in review["letter"]["sections"]]
    assert review["risk"]["level"] == "medium"
    assert "other_angles" not in sections
    assert "support" in sections

    calm = _data(_create(client, parent, key="key-2", question="我怎样才能早点睡？", topic_id="lifestyle_body"))
    risky_result = _seed_result(app, "parent_medium", risk_level="high")
    calm = _data(_patch(client, parent, calm, "scales", {"result_ids": [risky_result]}))
    assert calm["risk"]["level"] == "high"
    assert calm["letter"]["safety_only"] is True


def test_linked_results_must_belong_to_participant_and_delete(tmp_path, monkeypatch):
    app = _app(tmp_path, monkeypatch)
    parent = _seed_user(app, "parent_link", "parent")
    _seed_user(app, "parent_stranger", "parent")
    client = app.test_client()
    foreign = _seed_result(app, "parent_stranger")
    review = _data(_create(client, parent))
    response = _patch(client, parent, review, "scales", {"result_ids": [foreign]})
    assert response.status_code == 404
    too_many = _patch(client, parent, review, "scales", {"result_ids": ["a", "b", "c", "d"]})
    assert too_many.status_code == 400

    deleted = client.delete(f"/api/supportive-review/reviews/{review['id']}", headers=parent)
    assert _data(deleted)["deleted"] is True
    assert client.get(f"/api/supportive-review/reviews/{review['id']}", headers=parent).status_code == 404


def test_human_review_intake_closed_in_production_until_release_flag(tmp_path, monkeypatch):
    app = _app(tmp_path, monkeypatch)
    levels = importlib.import_module("services.therapeutic_assessment_level_service")
    with app.app_context():
        assert levels.human_review_intake_open() is True
        app.config["APP_ENV"] = "production"
        try:
            assert levels.human_review_intake_open() is False
        finally:
            app.config["APP_ENV"] = "testing"

    parent = _seed_user(app, "parent_human", "parent")
    service = importlib.import_module("services.therapeutic_assessment_service")
    monkeypatch.setattr(service, "human_review_intake_open", lambda: False)
    response = app.test_client().post(
        "/api/therapeutic-assessment/cases",
        json={"assessment_question": "想一起理解一次争吵", "shared_scope": ["question"], "consent": True},
        headers={**parent, "Idempotency-Key": "ta-closed-1"},
    )
    assert response.status_code == 409
    assert response.get_json()["error"]["code"] == "human_review_not_open"
    status = app.test_client().get("/api/therapeutic-assessment/service-levels", headers=parent).get_json()["data"]
    assert status["human_review_open"] is True


@pytest.mark.parametrize("section,data", [
    ("question", {"question": ""}),
    ("episode", {"intensity": 11}),
    ("question", {"question": "问题", "topic_id": "unknown"}),
    ("followup_extra", {}),
])
def test_validation_errors(tmp_path, monkeypatch, section, data):
    app = _app(tmp_path, monkeypatch)
    parent = _seed_user(app, "parent_validation", "parent")
    client = app.test_client()
    review = _data(_create(client, parent))
    response = _patch(client, parent, review, section, data)
    assert response.status_code == 400
    assert response.get_json()["error"]["code"] == "validation_error"
