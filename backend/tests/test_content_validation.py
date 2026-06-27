import importlib
import json
import shutil
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = PROJECT_ROOT / "backend"
CONTENT_ROOT = PROJECT_ROOT / "content"
SCHEMA_ROOT = CONTENT_ROOT / "schemas"


def _validator():
    sys.path.insert(0, str(BACKEND_ROOT))
    return importlib.import_module("scripts.validate_content")


def _copy_required_content(target: Path) -> None:
    target.mkdir()
    for filename in [
        "training_cards.json",
        "feedback_rules.json",
        "risk_keywords.json",
        "student_profile_rules.json",
        "scales_catalog.json",
        "scale_item_drafts.json",
        "assessment_training_map.json",
        "diary_training_map.json",
    ]:
        shutil.copy(CONTENT_ROOT / filename, target / filename)


def test_current_content_validation_passes():
    validator = _validator()

    errors = validator.validate_content(CONTENT_ROOT, SCHEMA_ROOT)

    assert errors == []


def test_missing_training_card_title_reports_specific_field(tmp_path):
    validator = _validator()
    content_dir = tmp_path / "content"
    _copy_required_content(content_dir)
    path = content_dir / "training_cards.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["cards"][0].pop("title")
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    errors = validator.validate_content(content_dir, SCHEMA_ROOT)

    assert any("training_cards.json.cards[emotion_naming].title" in error for error in errors)


def test_missing_risk_keyword_level_reports_specific_field(tmp_path):
    validator = _validator()
    content_dir = tmp_path / "content"
    _copy_required_content(content_dir)
    path = content_dir / "risk_keywords.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["categories"][0].pop("risk_level")
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    errors = validator.validate_content(content_dir, SCHEMA_ROOT)

    assert any("risk_keywords.json.categories[self_harm].risk_level" in error for error in errors)


def test_training_card_requires_at_least_two_reflection_questions(tmp_path):
    validator = _validator()
    content_dir = tmp_path / "content"
    _copy_required_content(content_dir)
    path = content_dir / "training_cards.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["cards"][0]["reflection_questions"] = ["只保留一个问题"]
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    errors = validator.validate_content(content_dir, SCHEMA_ROOT)

    assert any("training_cards.json.cards[emotion_naming].reflection_questions 至少需要 2 项" in error for error in errors)


def test_duplicate_training_card_id_reports_error(tmp_path):
    validator = _validator()
    content_dir = tmp_path / "content"
    _copy_required_content(content_dir)
    path = content_dir / "training_cards.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["cards"].append(dict(payload["cards"][0]))
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    errors = validator.validate_content(content_dir, SCHEMA_ROOT)

    assert any("training_cards.json.cards[emotion_naming].id 重复" in error for error in errors)


def test_unknown_recommended_card_id_reports_error(tmp_path):
    validator = _validator()
    content_dir = tmp_path / "content"
    _copy_required_content(content_dir)
    path = content_dir / "feedback_rules.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["rules"][0]["recommended_card_ids"] = ["missing_card_id"]
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    errors = validator.validate_content(content_dir, SCHEMA_ROOT)

    assert any("feedback_rules.json.rules[judgmental_language].recommended_card_ids 包含不存在的训练卡：missing_card_id" in error for error in errors)


def test_high_risk_feedback_rule_cannot_recommend_regular_cards(tmp_path):
    validator = _validator()
    content_dir = tmp_path / "content"
    _copy_required_content(content_dir)
    path = content_dir / "feedback_rules.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["rules"][0]["risk_level"] = "high"
    payload["rules"][0]["recommended_card_ids"] = ["emotion_naming"]
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    errors = validator.validate_content(content_dir, SCHEMA_ROOT)

    assert any("feedback_rules.json.rules[judgmental_language] high 风险规则不得推荐普通训练卡" in error for error in errors)


def test_legal_non_diagnostic_boundary_text_is_allowed(tmp_path):
    validator = _validator()
    content_dir = tmp_path / "content"
    _copy_required_content(content_dir)
    path = content_dir / "feedback_rules.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["safety_notes"] = ["反馈只用于自我理解和亲子沟通练习，不构成诊断。"]
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    errors = validator.validate_content(content_dir, SCHEMA_ROOT)

    assert not any("feedback_rules.json 风险边界文案" in error for error in errors)


def test_assessment_training_map_high_risk_condition_cannot_recommend_cards(tmp_path):
    validator = _validator()
    content_dir = tmp_path / "content"
    _copy_required_content(content_dir)
    path = content_dir / "assessment_training_map.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["rules"][0]["trigger_condition"]["risk_level"] = "high"
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    errors = validator.validate_content(content_dir, SCHEMA_ROOT)

    assert any("assessment_training_map.json.rules[student_profile_pressure_alert_basic_support] high 风险条件不得推荐普通训练卡" in error for error in errors)


def test_diary_training_map_requires_allowed_review_status(tmp_path):
    validator = _validator()
    content_dir = tmp_path / "content"
    _copy_required_content(content_dir)
    path = content_dir / "diary_training_map.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["rules"][0]["review_status"] = "open_without_review"
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    errors = validator.validate_content(content_dir, SCHEMA_ROOT)

    assert any("diary_training_map.json.rules[diary_judgmental_language_nonjudgmental_response].review_status 不在允许枚举中" in error for error in errors)
