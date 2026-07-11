import importlib
import os
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = PROJECT_ROOT / "backend"


def _fresh_modules(tmp_path):
    sys.path.insert(0, str(BACKEND_ROOT))
    for name in list(sys.modules):
        if name in {"config", "database"} or name.startswith("services."):
            sys.modules.pop(name, None)
    os.environ["DATABASE_PATH"] = str(tmp_path / "safehome-test.sqlite3")
    os.environ["CONTENT_DIR"] = str(PROJECT_ROOT / "content")
    service = importlib.import_module("services.training_recommendation_service")
    database = importlib.import_module("database")
    return service, database


def test_prfq_low_ic_triggers_curiosity_card(tmp_path):
    service, database = _fresh_modules(tmp_path)
    scores = {
        "dimensions": [
            {"key": "PRFQ_IC", "score": 1.5},
        ]
    }

    rules = service.evaluate_training_rules("parent_reflective_functioning_prfq", database.json_dumps(scores))
    card_ids = service.flatten_card_ids(rules)

    assert "prfq_ic_curiosity" in card_ids


def test_rule_without_dimension_matches_directly(tmp_path):
    service, database = _fresh_modules(tmp_path)
    scores = {"dimensions": []}

    rules = service.evaluate_training_rules("student_profile_v1", database.json_dumps(scores))

    assert any(rule["rule_id"] == "student_profile_pressure_alert_basic_support" for rule in rules)


def test_unmodeled_scale_uses_midpoint_threshold(tmp_path):
    service, database = _fresh_modules(tmp_path)
    scores = {"dimensions": [{"key": "ERQ_ES", "score": 6.5}]}

    rules = service.evaluate_training_rules("emotion_regulation_erq", database.json_dumps(scores))
    card_ids = service.flatten_card_ids(rules)

    assert "erq_suppression_release" in card_ids


def test_high_risk_returns_no_training_rules(tmp_path):
    service, database = _fresh_modules(tmp_path)
    scores = {
        "dimensions": [{"key": "PRFQ_IC", "score": 1}],
        "risk": {"risk_level": "high"},
    }

    rules = service.evaluate_training_rules("parent_reflective_functioning_prfq", database.json_dumps(scores))

    assert rules == []


def test_controlled_card_is_not_released_by_automatic_mapping(tmp_path):
    service, _database = _fresh_modules(tmp_path)
    rules = [{"recommended_card_ids": ["sandplay_expression_01", "student_emotion_naming"]}]

    assert service.flatten_card_ids(rules) == ["student_emotion_naming"]
