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
        "assessment_worksheets.json",
        "scale_item_drafts.json",
        "assessment_training_map.json",
        "diary_training_map.json",
        "programs.json",
    ]:
        shutil.copy(CONTENT_ROOT / filename, target / filename)


def test_current_content_validation_passes():
    validator = _validator()

    errors = validator.validate_content(CONTENT_ROOT, SCHEMA_ROOT)

    assert errors == []


def test_training_cards_keep_low_load_and_safety_contract():
    payload = json.loads((CONTENT_ROOT / "training_cards.json").read_text(encoding="utf-8"))

    assert len(payload["cards"]) == 42
    for card in payload["cards"]:
        assert 1 <= card["duration_minutes"] <= 10, card["id"]
        assert 2 <= len(card["steps"]) <= 4, card["id"]
        assert card["boundary_notice"], card["id"]
        assert card["completion_criteria"], card["id"]
        assert card["stop_rules"], card["id"]
        assert card["release_policy"] in {"shared_choice_candidate", "manual_context_required"}, card["id"]
        assert card["governance_review_status"] == "manual_review_required", card["id"]


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


def test_program_measurement_plan_rejects_unknown_worksheet(tmp_path):
    validator = _validator()
    content_dir = tmp_path / "content"
    _copy_required_content(content_dir)
    path = content_dir / "programs.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["programs"][0]["measurement_plan"]["baseline_worksheet_ids"] = ["missing_worksheet"]
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    errors = validator.validate_content(content_dir, SCHEMA_ROOT)

    assert any("measurement_plan.baseline_worksheet_ids 包含不存在的 worksheet：missing_worksheet" in error for error in errors)


def _write_profile_model(content_dir: Path, **overrides) -> None:
    profile_dir = content_dir / "profiles"
    profile_dir.mkdir(exist_ok=True)
    model = {
        "schema_version": "2026.06-profile-model-v1",
        "model_id": "test_profile_model",
        "standard_scale_name": "测试画像模型",
        "scale_id": "student_profile_v1",
        "worksheet_id": "student_profile_v1",
        "n_cases": 80,
        "n_features": 2,
        "boundary_notice": "本画像只用于阶段性自我理解，不构成诊断。",
        "features": [
            {
                "feature_id": "test_anxiety",
                "worksheet_question_id": "test_anxiety",
                "mean": 3.0,
                "std": 1.0,
            },
            {
                "feature_id": "iu_total",
                "worksheet_question_id": "iu_total",
                "mean": 3.0,
                "std": 1.0,
            },
        ],
        "clusters": [
            {
                "cluster_id": 0,
                "profile_name": "测试画像",
                "n": 40,
                "percent": 50.0,
                "center_z": {"test_anxiety": 0.1, "iu_total": -0.1},
                "pca_centroid": [0.0, 0.0],
                "supportive_explanation": "这是支持性阶段画像，不代表固定标签，不构成诊断。",
                "recommended_card_ids": ["emotion_naming"],
            }
        ],
    }
    model.update(overrides)
    (profile_dir / "test_profile_model.json").write_text(json.dumps(model, ensure_ascii=False), encoding="utf-8")


def test_profile_model_question_ids_must_link_to_real_worksheet_questions(tmp_path):
    validator = _validator()
    content_dir = tmp_path / "content"
    _copy_required_content(content_dir)
    _write_profile_model(
        content_dir,
        features=[
            {
                "feature_id": "test_anxiety",
                "worksheet_question_id": "missing_question_id",
                "mean": 3.0,
                "std": 1.0,
            },
        ],
    )

    errors = validator.validate_content(content_dir, SCHEMA_ROOT)

    assert any("worksheet_question_id" in error and "missing_question_id" in error for error in errors)


def test_profile_model_recommended_cards_must_exist(tmp_path):
    validator = _validator()
    content_dir = tmp_path / "content"
    _copy_required_content(content_dir)
    _write_profile_model(
        content_dir,
        clusters=[
            {
                "cluster_id": 0,
                "profile_name": "测试画像",
                "n": 40,
                "percent": 50.0,
                "center_z": {"test_anxiety": 0.1, "iu_total": -0.1},
                "pca_centroid": [0.0, 0.0],
                "supportive_explanation": "这是支持性阶段画像，不代表固定标签，不构成诊断。",
                "recommended_card_ids": ["missing_training_card"],
            }
        ],
    )

    errors = validator.validate_content(content_dir, SCHEMA_ROOT)

    assert any("recommended_card_ids" in error and "missing_training_card" in error for error in errors)


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


def test_legacy_self_built_assessment_ids_cannot_return_to_content(tmp_path):
    validator = _validator()
    content_dir = tmp_path / "content"
    _copy_required_content(content_dir)
    path = content_dir / "assessment_worksheets.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["worksheets"].append(
        {
            "id": "worksheet_3_1_anxiety",
            "display_title": "工作表3.1：总体焦虑水平及干扰程度量表",
        }
    )
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    errors = validator.validate_content(content_dir, SCHEMA_ROOT)

    assert any("worksheet_3_1_anxiety" in error and "已下线旧版自建工作表" in error for error in errors)


def test_screening_or_health_scales_require_boundary_when_enabled(tmp_path):
    validator = _validator()
    content_dir = tmp_path / "content"
    _copy_required_content(content_dir)
    path = content_dir / "scales_catalog.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    scale = next(item for item in payload["scales"] if item["id"] == "gad7_anxiety")
    scale["review_status"] = "pilot_review_required"
    scale["enabled"] = True
    scale["first_batch_candidate"] = True
    scale["excluded_from_user_flow"] = False
    scale["recommended_card_ids"] = ["emotion_naming"]
    scale["sensitive_category"] = "screening_or_health"
    scale.pop("boundary_notice", None)
    scale.pop("result_disclaimer", None)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    errors = validator.validate_content(content_dir, SCHEMA_ROOT)

    assert any("gad7_anxiety" in error and "boundary_notice" in error for error in errors)
    assert any("gad7_anxiety" in error and "result_disclaimer" in error for error in errors)

    scale["boundary_notice"] = "本结果只用于自我观察，不构成诊断或筛查结论。"
    scale["result_disclaimer"] = "本结果只用于自我观察，不构成诊断或筛查结论。"
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    errors = validator.validate_content(content_dir, SCHEMA_ROOT)

    assert not any("gad7_anxiety" in error for error in errors)
