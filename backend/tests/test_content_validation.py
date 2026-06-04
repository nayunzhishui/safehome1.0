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
