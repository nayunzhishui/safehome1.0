import copy
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
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "content-sync.sqlite3"))
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


def _content(name):
    return json.loads((ROOT / "content" / name).read_text(encoding="utf-8"))


def _worksheet(worksheet_id):
    return next(item for item in _content("assessment_worksheets.json")["worksheets"] if item["id"] == worksheet_id)


PHQ_TRIGGER = {
    "min_score": 1,
    "risk_level": "high",
    "safety_route": "human_review",
    "urgent_min_score": 2,
    "reason_code": "assessment_item_self_harm_thoughts",
    "participant_message": "synthetic item message",
}


def _phq_with_trigger():
    worksheet = copy.deepcopy(_worksheet("phq9_cesd10_depression"))
    for question in worksheet["questions"]:
        if question["id"] == "PHQ09":
            question["safety_trigger"] = dict(PHQ_TRIGGER)
    return worksheet


def _answers(worksheet, item_score):
    answers = []
    for question in worksheet["questions"]:
        value = str(item_score) if question["id"] == "PHQ09" else "0"
        answers.append({"question_id": question["id"], "value": value})
    return answers


def test_item_trigger_levels_and_routes(tmp_path, monkeypatch):
    _app(tmp_path, monkeypatch)
    service = importlib.import_module("services.assessment_item_safety_service")
    worksheet = _phq_with_trigger()
    scored = lambda score: [{"question_id": "PHQ09", "score": score}, {"question_id": "PHQ01", "score": 3}]

    assert service.evaluate_item_safety(worksheet, scored(0)) is None
    several_days = service.evaluate_item_safety(worksheet, scored(1))
    assert several_days["risk_level"] == "high"
    assert several_days["safety_route"] == "human_review"
    assert several_days["allow_recommended_training_cards"] is False
    assert several_days["allow_auto_feedback"] is False
    assert several_days["participant_message"] == "synthetic item message"
    assert several_days["matched_categories"] == [
        {
            "id": "assessment_item:PHQ09",
            "label": "题目级安全提示",
            "reason_code": "assessment_item_self_harm_thoughts",
            "risk_level": "high",
        }
    ]
    assert service.evaluate_item_safety(worksheet, scored(2))["safety_route"] == "urgent_human_review"


def test_medium_item_trigger_keeps_ordinary_feedback_and_merges_protectively(tmp_path, monkeypatch):
    _app(tmp_path, monkeypatch)
    service = importlib.import_module("services.assessment_item_safety_service")
    worksheet = {"questions": [{"id": "EPQ16", "safety_trigger": {"min_score": 1, "risk_level": "medium"}}]}
    medium = service.evaluate_item_safety(worksheet, [{"question_id": "EPQ16", "score": 1}])
    assert medium["risk_level"] == "medium"
    assert medium["requires_review"] is True
    assert medium["allow_auto_feedback"] is True
    assert medium["allow_recommended_training_cards"] is True
    assert service.evaluate_item_safety(worksheet, [{"question_id": "EPQ16", "score": True}]) is None

    text_urgent = {
        "risk_level": "high",
        "safety_route": "urgent_human_review",
        "matched_categories": [{"id": "text"}],
        "requires_review": True,
        "allow_auto_feedback": False,
        "allow_recommended_training_cards": False,
        "safe_response": "text response",
    }
    merged = service.merge_risk_results(text_urgent, medium)
    assert merged["risk_level"] == "high"
    assert merged["safety_route"] == "urgent_human_review"
    assert merged["allow_recommended_training_cards"] is False
    assert [item["id"] for item in merged["matched_categories"]] == ["text", "assessment_item:EPQ16"]
    text_low = {"risk_level": "low", "safety_route": "standard", "requires_review": False, "allow_auto_feedback": True, "allow_recommended_training_cards": True}
    assert service.merge_risk_results(text_low, medium)["risk_level"] == "medium"
    assert service.merge_risk_results(None, None) is None


def test_submitted_assessment_routes_item_trigger_to_review_without_cards(tmp_path, monkeypatch):
    app = _app(tmp_path, monkeypatch)
    _seed_user(app, "synthetic-phq-user", "parent")
    with app.app_context():
        execution = importlib.import_module("services.assessment_execution_service")
        from database import get_connection

        worksheet = _phq_with_trigger()
        result = execution.submit_assessment(worksheet, _answers(worksheet, 2), user_id="synthetic-phq-user")
        risk = result["scores"]["risk"]
        assert risk["risk_level"] == "high"
        assert risk["safety_route"] == "urgent_human_review"
        assert risk["participant_message"] == "synthetic item message"
        assert result["recommended_card_ids"] == []
        with get_connection() as conn:
            review = conn.execute(
                "SELECT safety_route, matched_categories_json FROM risk_review_records WHERE source_id = ?",
                (result["id"],),
            ).fetchone()
        assert review["safety_route"] == "urgent_human_review"
        assert "assessment_item:PHQ09" in review["matched_categories_json"]

        calm = execution.submit_assessment(worksheet, _answers(worksheet, 0), user_id="synthetic-phq-user")
        assert "risk" not in calm["scores"]


def test_summed_dimension_thresholds_scale_with_item_count(tmp_path, monkeypatch):
    _app(tmp_path, monkeypatch)
    service = importlib.import_module("services.training_recommendation_service")
    options = [{"score": score} for score in range(1, 6)]
    worksheet = {
        "dimension_score_method": "sum",
        "dimensions": [{"code": "SUMMED"}],
        "questions": [{"id": f"Q{index}", "dimension": "SUMMED", "options": options} for index in range(5)],
    }
    assert service._threshold_from_worksheet("SUMMED", worksheet, "synthetic") == {"support_below": 15.0, "high_above": 15.0}
    worksheet["dimension_score_method"] = "mean"
    assert service._threshold_from_worksheet("SUMMED", worksheet, "synthetic") == {"support_below": 3.0, "high_above": 3.0}

    condition = {"dimension": "TOTAL", "score_at_least": 10}
    assert service._evaluate_condition(condition, {"TOTAL": 10}, None, worksheet, "synthetic") is True
    assert service._evaluate_condition(condition, {"TOTAL": 9}, None, worksheet, "synthetic") is False
    banded = {"dimension": "TOTAL", "score_at_least": 5, "score_below": 10}
    assert service._evaluate_condition(banded, {"TOTAL": 10}, None, worksheet, "synthetic") is False


def test_content_sync_plan_apply_and_restore_are_admin_only(tmp_path, monkeypatch):
    app = _app(tmp_path, monkeypatch)
    admin = _seed_user(app, "admin-sync", "admin")
    researcher = _seed_user(app, "researcher-sync", "researcher")
    client = app.test_client()
    card_ids = [card["id"] for card in _content("training_cards.json")["cards"]]
    worksheet_ids = [item["id"] for item in _content("assessment_worksheets.json")["worksheets"]]

    assert client.get("/api/admin/content-sync/plan", headers=researcher).status_code == 403
    initial = client.get("/api/admin/content-sync/plan", headers=admin).get_json()["data"]
    assert initial["in_sync"] is True
    assert len(initial["backup"]["training_cards"]) == len(card_ids)
    assert len(initial["backup"]["assessment_worksheets"]) == len(worksheet_ids)

    with app.app_context():
        from database import get_connection

        with get_connection() as conn:
            conn.execute("DELETE FROM training_cards WHERE id = ?", (card_ids[0],))
            conn.execute("UPDATE assessment_worksheets SET display_title = 'stale title' WHERE id = ?", (worksheet_ids[0],))
            conn.commit()
    drifted = client.get("/api/admin/content-sync/plan", headers=admin).get_json()["data"]
    assert drifted["in_sync"] is False
    assert drifted["tables"]["training_cards"]["create"] == [card_ids[0]]
    assert drifted["tables"]["assessment_worksheets"]["update"] == [{"id": worksheet_ids[0], "fields": ["display_title"]}]

    stale = client.post("/api/admin/content-sync/apply", headers=admin, json={"plan_hash": initial["plan_hash"]})
    assert stale.status_code == 409
    assert stale.get_json()["error"]["code"] == "plan_changed"
    assert client.post("/api/admin/content-sync/apply", headers=researcher, json={"plan_hash": drifted["plan_hash"]}).status_code == 403

    applied = client.post("/api/admin/content-sync/apply", headers=admin, json={"plan_hash": drifted["plan_hash"]})
    assert applied.status_code == 200
    assert applied.get_json()["data"]["in_sync"] is True

    missing_confirm = client.post("/api/admin/content-sync/restore", headers=admin, json={"backup": drifted["backup"]})
    assert missing_confirm.get_json()["error"]["code"] == "confirmation_required"
    restored = client.post(
        "/api/admin/content-sync/restore",
        headers=admin,
        json={"backup": drifted["backup"], "confirm": "restore"},
    )
    assert restored.status_code == 200
    restored_data = restored.get_json()["data"]
    assert restored_data["removed_ids"]["training_cards"] == [card_ids[0]]
    assert restored_data["plan_after_restore"]["training_cards"]["create"] == [card_ids[0]]
    assert restored_data["plan_after_restore"]["assessment_worksheets"]["update"] == [
        {"id": worksheet_ids[0], "fields": ["display_title"]}
    ]

    with app.app_context():
        from database import get_connection

        with get_connection() as conn:
            actions = {row["action"] for row in conn.execute("SELECT action FROM audit_logs").fetchall()}
    assert {"content_sync_applied", "content_sync_restored"} <= actions


def test_startup_tolerates_cards_awaiting_sync_and_hides_them_in_production(tmp_path, monkeypatch):
    app = _app(tmp_path, monkeypatch)
    card_ids = [card["id"] for card in _content("training_cards.json")["cards"]]
    with app.app_context():
        database = importlib.import_module("database")
        card_service = importlib.import_module("services.card_service")
        with database.get_connection() as conn:
            conn.execute("DELETE FROM training_cards WHERE id = ?", (card_ids[0],))
            conn.commit()
        health = database.check_database_health()
        assert health["training_cards_pending_sync"] == [card_ids[0]]
        assert health["training_cards_sync_ok"] is False
        assert health["training_cards_startup_ok"] is True

        app.config["APP_ENV"] = "production"
        visible = {card["id"] for card in card_service.list_cards(include_unapproved=True)}
        assert card_ids[0] not in visible
        assert card_ids[1] in visible
        app.config["APP_ENV"] = "testing"

        with database.get_connection() as conn:
            conn.execute(
                "INSERT INTO training_cards (id, type, title, steps_json, tags_json, enabled, version, created_at, updated_at) "
                "VALUES ('retired-card', 'general', 'retired', '[]', '[]', 1, 'old', 'now', 'now')"
            )
            conn.commit()
        blocked = database.check_database_health()
        assert blocked["training_cards_unknown_in_db"] == ["retired-card"]
        assert blocked["training_cards_startup_ok"] is False
        assert blocked["ok"] is False
