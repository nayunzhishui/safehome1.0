import copy
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from scripts.validate_content import validate_emotion_annotation_content


def _payloads():
    content = ROOT / "content"
    return (
        json.loads((content / "emotion_annotation_ontology.json").read_text(encoding="utf-8")),
        json.loads((content / "emotion_annotation_examples.json").read_text(encoding="utf-8")),
    )


def test_emotion_annotation_ontology_is_complete_and_non_diagnostic():
    ontology, examples = _payloads()
    assert validate_emotion_annotation_content(ROOT / "content") == []
    codes = [item["code"] for item in ontology["emotion_labels"]]
    assert len(codes) == len(set(codes))
    assert {"anxiety", "fear", "anger", "sadness", "calm", "positive", "unknown"}.issubset(codes)
    assert ontology["annotation_mode"]["maximum_emotion_labels"] == 3
    assert ontology["release_boundary"]["automatic_expert_signoff_allowed"] is False
    assert len(examples["examples"]) >= 12
    assert len(examples["counterexamples"]) >= 8


def test_safety_cue_is_separate_from_emotion_and_never_a_probability():
    ontology, examples = _payloads()
    emotion_codes = {item["code"] for item in ontology["emotion_labels"]}
    assert "crisis_expression" not in emotion_codes
    cue = ontology["safety_cues"][0]
    assert cue["is_emotion_label"] is False
    assert "概率" in cue["rule"]
    safety_example = next(item for item in examples["examples"] if item.get("safety_cues"))
    assert safety_example["needs_human_understanding"] is True


def test_validator_rejects_missing_unknown_and_automatic_expert_signoff(tmp_path):
    ontology, examples = _payloads()
    invalid = copy.deepcopy(ontology)
    invalid["emotion_labels"] = [item for item in invalid["emotion_labels"] if item["code"] != "unknown"]
    invalid["release_boundary"]["automatic_expert_signoff_allowed"] = True
    (tmp_path / "emotion_annotation_ontology.json").write_text(
        json.dumps(invalid, ensure_ascii=False), encoding="utf-8"
    )
    (tmp_path / "emotion_annotation_examples.json").write_text(
        json.dumps(examples, ensure_ascii=False), encoding="utf-8"
    )
    (tmp_path / "offline_annotation_data_policy.json").write_text(
        (ROOT / "content" / "offline_annotation_data_policy.json").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    errors = validate_emotion_annotation_content(tmp_path)
    assert any("unknown" in error for error in errors)
    assert any("自动专家签字" in error for error in errors)


def test_manual_names_boundaries_and_72_word_baseline():
    manual = (ROOT / "docs" / "05_内容与心理边界" / "中文情绪线索标注手册_T37_A01.md").read_text(
        encoding="utf-8"
    )
    assert "不等于诊断、人格、危机概率、关系优劣" in manual
    assert "72词规则表继续作为工程测试基线" in manual
    assert "两名标注者独立工作" in manual
